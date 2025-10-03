import json
import os
from django.utils import timezone
from django.db import transaction
from .models import Contributor, ProjectContributor
from .enums import FunctionalRole
from projects.models import Project
import logging

logger = logging.getLogger(__name__)


class TNMDataAnalysisService:
    """Service for analyzing TNM output data and storing contributor information."""
    
    @staticmethod
    def analyze_assignment_matrix(project: Project, tnm_output_dir: str, branch: str = None):
        """
        Analyze TNM AssignmentMatrix and idToUser data to extract contributor information.
        
        Args:
            project: Project instance
            tnm_output_dir: Directory containing TNM output files
            branch: Git branch analyzed (for metadata)
        
        Returns:
            dict: Analysis results with contributor count and statistics
        """
        try:
            # Load TNM output files
            id_to_user_path = os.path.join(tnm_output_dir, 'idToUser.json')
            id_to_file_path = os.path.join(tnm_output_dir, 'idToFile.json')
            assignment_matrix_path = os.path.join(tnm_output_dir, 'AssignmentMatrix.json')
            
            if not all(os.path.exists(p) for p in [id_to_user_path, assignment_matrix_path]):
                raise FileNotFoundError("Required TNM output files not found")
            
            # Load data
            with open(id_to_user_path, 'r', encoding='utf-8') as f:
                id_to_user = json.load(f)
            
            with open(assignment_matrix_path, 'r', encoding='utf-8') as f:
                assignment_matrix = json.load(f)
            
            # Optional: load file mapping for additional statistics
            id_to_file = {}
            if os.path.exists(id_to_file_path):
                with open(id_to_file_path, 'r', encoding='utf-8') as f:
                    id_to_file = json.load(f)
            
            return TNMDataAnalysisService._process_contributor_data(
                project, id_to_user, assignment_matrix, id_to_file, branch
            )
            
        except Exception as e:
            logger.error(f"Error analyzing TNM data for project {project.id}: {e}")
            raise
    
    @staticmethod
    def _process_contributor_data(project, id_to_user, assignment_matrix, id_to_file, branch):
        """Process and store contributor data from TNM analysis."""
        
        analysis_time = timezone.now()
        contributors_created = 0
        contributors_updated = 0
        
        with transaction.atomic():
            for user_id, email in id_to_user.items():
                try:
                    # Get or create Contributor
                    github_login = TNMDataAnalysisService._extract_username(email)
                    contributor, created = Contributor.objects.get_or_create(
                        github_login=github_login,
                        defaults={'email': email}
                    )
                    
                    if created:
                        contributors_created += 1
                    elif not contributor.email:
                        contributor.email = email
                        contributor.save()
                    
                    # Calculate statistics from assignment matrix
                    user_stats = TNMDataAnalysisService._calculate_user_statistics(
                        user_id, assignment_matrix, id_to_file
                    )
                    
                    # Suggest functional role based on activity patterns
                    suggested_role = TNMDataAnalysisService._suggest_functional_role(user_stats)
                    
                    # Update or create ProjectContributor
                    project_contributor, pc_created = ProjectContributor.objects.update_or_create(
                        project=project,
                        contributor=contributor,
                        defaults={
                            'tnm_user_id': user_id,
                            # TNM AssignmentMatrix does not contain true commit counts.
                            # Use total_modifications as a proxy for commits_count for now.
                            'commits_count': user_stats['total_modifications'],
                            'files_modified': user_stats['files_count'],
                            'total_modifications': user_stats['total_modifications'],
                            'avg_modifications_per_file': user_stats['avg_modifications_per_file'],
                            'functional_role': suggested_role['role'],
                            'is_core_contributor': user_stats['total_modifications'] >= 100,
                            'role_confidence': suggested_role['confidence'],
                            'last_tnm_analysis': analysis_time,
                            'tnm_branch': branch or 'unknown',
                        }
                    )
                    
                    if not pc_created:
                        contributors_updated += 1
                        
                except Exception as e:
                    logger.error(f"Error processing contributor {email}: {e}")
                    continue
        
        return {
            'total_contributors': len(id_to_user),
            'contributors_created': contributors_created,
            'contributors_updated': contributors_updated,
            'analysis_time': analysis_time,
            'branch': branch,
        }
    
    @staticmethod
    def _extract_username(email):
        """Extract username from email address."""
        if '@' in email:
            username = email.split('@')[0]
            # Handle GitHub noreply emails
            if 'users.noreply.github.com' in email:
                # Extract actual username from noreply format
                parts = username.split('+')
                if len(parts) > 1:
                    return parts[1]  # Return the actual username part
                else:
                    return parts[0]  # Return the number part if no username
            return username
        return email
    
    @staticmethod
    def _calculate_user_statistics(user_id, assignment_matrix, id_to_file):
        """Calculate statistics for a user from assignment matrix."""
        user_data = assignment_matrix.get(user_id, {})
        
        files_count = len(user_data)
        total_modifications = sum(user_data.values())
        avg_modifications_per_file = total_modifications / files_count if files_count > 0 else 0
        
        # Calculate file type distribution with path analysis
        file_types = {}
        for file_id, modifications in user_data.items():
            file_path = id_to_file.get(file_id, '')
            
            # Analyze both extension and path for role indicators
            file_indicator = TNMDataAnalysisService._analyze_file_path(file_path)
            file_types[file_indicator] = file_types.get(file_indicator, 0) + modifications
        
        return {
            'files_count': files_count,
            'total_modifications': total_modifications,
            'avg_modifications_per_file': round(avg_modifications_per_file, 2),
            'file_types': file_types,
        }
    
    @staticmethod
    def _analyze_file_path(file_path):
        """
        Analyze file path to extract role indicators.
        
        Returns a key that represents the file's role category.
        Checks both path components and extension for security/ops keywords.
        """
        if not file_path:
            return 'unknown'
        
        path_lower = file_path.lower()
        
        # Security indicators in path
        security_keywords = [
            'security', 'auth', 'authenticate', 'authorization', 'permission',
            'crypto', 'encryption', 'ssl', 'tls', 'cert', 'oauth', 'jwt',
            'acl', 'rbac', 'policy', 'vulnerability', 'cve', 'sanitize',
            'xss', 'csrf', 'sqli', 'injection'
        ]
        
        # Ops/Infrastructure indicators in path
        ops_keywords = [
            'docker', 'compose', 'kubernetes', 'k8s', 'helm', 'terraform',
            'ansible', 'jenkins', 'gitlab-ci', 'github/workflows',
            'deploy', 'deployment', 'infrastructure', 'infra', 'ops',
            'ci', 'cd', 'pipeline', 'build', 'makefile'
        ]
        
        # Check path for security keywords
        for keyword in security_keywords:
            if keyword in path_lower:
                ext = TNMDataAnalysisService._get_file_extension(file_path)
                return f'security_{ext}' if ext != 'no_ext' else 'security'
        
        # Check path for ops keywords
        for keyword in ops_keywords:
            if keyword in path_lower:
                ext = TNMDataAnalysisService._get_file_extension(file_path)
                return f'ops_{ext}' if ext != 'no_ext' else 'ops'
        
        # Check file extension for ops files
        ext = TNMDataAnalysisService._get_file_extension(file_path)
        ops_extensions = {'yml', 'yaml', 'dockerfile', 'sh', 'bash', 'ps1', 'tf', 'tfvars'}
        
        if ext in ops_extensions:
            return f'ops_{ext}'
        
        # Return regular extension
        return ext
    
    @staticmethod
    def _get_file_extension(file_path):
        """Get file extension from path."""
        if '.' in file_path:
            return file_path.split('.')[-1].lower()
        return 'no_ext'
    
    @staticmethod
    def _suggest_functional_role(user_stats):
        """
        Suggest functional role based on user statistics and file patterns.
        
        Classifies contributors into functional teams for MC-STC analysis:
        - SECURITY: Works on security-related files/features
        - OPS: Works on infrastructure, deployment, CI/CD
        - DEVELOPER: Regular development (default)
        - UNCLASSIFIED: Insufficient data
        
        Args:
            user_stats: Dict containing modification statistics and file types
            
        Returns:
            Dict with 'role' and 'confidence' (0-1 scale)
        """
        total_mods = user_stats['total_modifications']
        files_count = user_stats['files_count']
        file_types = user_stats.get('file_types', {})
        
        # Insufficient data
        if total_mods < 5:
            return {'role': FunctionalRole.UNCLASSIFIED, 'confidence': 0.2}
        
        # Analyze file type patterns to determine role
        role_indicators = TNMDataAnalysisService._analyze_file_patterns(file_types)
        
        # Security role: High proportion of security-related work
        if role_indicators['security_score'] > 0.3 and total_mods >= 10:
            confidence = min(0.9, 0.6 + role_indicators['security_score'] * 0.3)
            return {'role': FunctionalRole.SECURITY, 'confidence': confidence}
        
        # Ops role: High proportion of infrastructure work
        if role_indicators['ops_score'] > 0.3 and total_mods >= 10:
            confidence = min(0.9, 0.6 + role_indicators['ops_score'] * 0.3)
            return {'role': FunctionalRole.OPS, 'confidence': confidence}
        
        # Developer role (default for active contributors)
        if total_mods >= 10:
            # Higher confidence for more active contributors
            if total_mods >= 100 and files_count >= 10:
                confidence = 0.8
            elif total_mods >= 50:
                confidence = 0.7
            else:
                confidence = 0.6
            return {'role': FunctionalRole.DEVELOPER, 'confidence': confidence}
        
        # Low activity - likely developer but low confidence
        else:
            return {'role': FunctionalRole.DEVELOPER, 'confidence': 0.4}
    
    @staticmethod
    def _analyze_file_patterns(file_types):
        """
        Analyze file type distribution to determine role indicators.
        
        Returns scores for different functional roles based on file patterns.
        """
        # Security-related file extensions and keywords
        security_extensions = {
            'security', 'auth', 'authentication', 'authorization',
            'crypto', 'encryption', 'ssl', 'tls', 'cert', 'key',
            'acl', 'permission', 'policy', 'vuln', 'cve'
        }
        
        # Ops-related file extensions and keywords
        ops_extensions = {
            'yml', 'yaml', 'dockerfile', 'sh', 'bash', 'ps1',
            'terraform', 'tf', 'ansible', 'helm', 'k8s',
            'docker', 'compose', 'ci', 'cd', 'jenkins',
            'makefile', 'build', 'deploy', 'infrastructure'
        }
        
        # Development-related extensions (for normalization)
        dev_extensions = {
            'py', 'js', 'jsx', 'ts', 'tsx', 'java', 'kt', 'kts',
            'go', 'rs', 'rb', 'php', 'cs', 'cpp', 'c', 'h',
            'swift', 'scala', 'clj', 'ex', 'elm'
        }
        
        total_mods = sum(file_types.values())
        if total_mods == 0:
            return {'security_score': 0.0, 'ops_score': 0.0, 'dev_score': 0.0}
        
        security_mods = 0
        ops_mods = 0
        dev_mods = 0
        
        for file_ext, mods in file_types.items():
            ext_lower = file_ext.lower()
            
            # Check if extension matches any security keyword
            if any(sec_key in ext_lower for sec_key in security_extensions):
                security_mods += mods
            
            # Check if extension matches any ops keyword
            if any(ops_key in ext_lower for ops_key in ops_extensions):
                ops_mods += mods
            
            # Check if it's a development file
            if ext_lower in dev_extensions:
                dev_mods += mods
        
        return {
            'security_score': security_mods / total_mods,
            'ops_score': ops_mods / total_mods,
            'dev_score': dev_mods / total_mods
        }
