import json
import os
import numpy as np
import logging
import threading
from typing import Dict, List, Optional, Tuple, Set
from django.conf import settings
from django.utils import timezone
from django.db import transaction

from .models import MCSTCAnalysis, MCSTCCoordinationPair
from stc_analysis.services import MCSTCService as BaseMCSTCService
from contributors.models import ProjectContributor
from contributors.enums import FunctionalRole

logger = logging.getLogger(__name__)


class MCSTCAnalysisService:
    """Service for MC-STC analysis operations"""
    
    @staticmethod
    def _convert_tnm_matrix_to_numpy(matrix_data, matrix_name):
        """Convert TNM matrix format to numpy array
        
        TNM outputs matrices in different formats:
        1. Nested dict format: {"0": {"0": value, "1": value}, "1": {...}}
        2. List of lists format: [[value, value], [value, value]]
        3. Dense array format: [value, value, value, ...]
        
        Args:
            matrix_data: Matrix data from TNM JSON file
            matrix_name: Name of the matrix for error messages
            
        Returns:
            numpy.ndarray: 2D numpy array
        """
        if matrix_data is None:
            raise ValueError(f"{matrix_name} matrix data is None")
        
        # Case 1: Nested dictionary format (sparse matrix)
        if isinstance(matrix_data, dict):
            # Find matrix dimensions
            max_row = max(int(k) for k in matrix_data.keys()) if matrix_data else 0
            max_col = 0
            for row_data in matrix_data.values():
                if isinstance(row_data, dict):
                    if row_data:
                        max_col = max(max_col, max(int(k) for k in row_data.keys()))
                else:
                    raise ValueError(f"{matrix_name} matrix has invalid row format: {type(row_data)}")
            
            # Create dense matrix
            rows, cols = max_row + 1, max_col + 1
            dense_matrix = np.zeros((rows, cols), dtype=float)
            
            for row_idx, row_data in matrix_data.items():
                row_i = int(row_idx)
                for col_idx, value in row_data.items():
                    col_j = int(col_idx)
                    dense_matrix[row_i, col_j] = float(value)
            
            return dense_matrix
        
        # Case 2: List of lists format
        elif isinstance(matrix_data, list):
            if not matrix_data:
                raise ValueError(f"{matrix_name} matrix is empty list")
            
            # Check if it's a list of lists (2D)
            if isinstance(matrix_data[0], list):
                return np.array(matrix_data, dtype=float)
            
            # Check if it's a flat list that needs reshaping
            else:
                # This case would need additional dimension information
                # For now, assume it's a square matrix
                size = int(np.sqrt(len(matrix_data)))
                if size * size != len(matrix_data):
                    raise ValueError(f"{matrix_name} matrix flat list length {len(matrix_data)} is not a perfect square")
                return np.array(matrix_data, dtype=float).reshape(size, size)
        
        else:
            raise ValueError(f"{matrix_name} matrix has unsupported format: {type(matrix_data)}")
    
    @staticmethod
    def _align_matrix_dimensions(assignment_matrix, dependency_matrix, assign_name, dep_name):
        """Align matrix dimensions for compatibility
        
        TNM may output matrices with slightly different dimensions due to:
        - Different file indexing ranges
        - Missing files in one matrix but not the other
        
        Args:
            assignment_matrix: numpy array (users × files)
            dependency_matrix: numpy array (files × files)
            assign_name: Name for error messages
            dep_name: Name for error messages
            
        Returns:
            Tuple of aligned matrices (assignment, dependency)
        """
        assign_rows, assign_cols = assignment_matrix.shape
        dep_rows, dep_cols = dependency_matrix.shape
        
        logger.info(f"Matrix alignment needed: {assign_name} {assignment_matrix.shape}, {dep_name} {dependency_matrix.shape}")
        
        # The number of files should match: assignment columns = dependency rows
        max_files = max(assign_cols, dep_rows)
        min_files = min(assign_cols, dep_rows)
        
        # If dimensions are close (within 5), try to align them
        if abs(assign_cols - dep_rows) <= 5:
            # Pad the smaller matrix with zeros
            if assign_cols < max_files:
                # Pad assignment matrix columns
                padding = max_files - assign_cols
                assignment_matrix = np.pad(assignment_matrix, ((0, 0), (0, padding)), mode='constant', constant_values=0)
                logger.info(f"Padded {assign_name} matrix columns: {assignment_matrix.shape}")
            
            if dep_rows < max_files:
                # Pad dependency matrix rows
                padding = max_files - dep_rows
                dependency_matrix = np.pad(dependency_matrix, ((0, padding), (0, 0)), mode='constant', constant_values=0)
                logger.info(f"Padded {dep_name} matrix rows: {dependency_matrix.shape}")
            
            # Also align dependency matrix columns to match rows (square matrix)
            if dependency_matrix.shape[0] != dependency_matrix.shape[1]:
                dep_size = dependency_matrix.shape[0]
                if dependency_matrix.shape[1] < dep_size:
                    padding = dep_size - dependency_matrix.shape[1]
                    dependency_matrix = np.pad(dependency_matrix, ((0, 0), (0, padding)), mode='constant', constant_values=0)
                elif dependency_matrix.shape[1] > dep_size:
                    dependency_matrix = dependency_matrix[:, :dep_size]
                logger.info(f"Aligned {dep_name} matrix to square: {dependency_matrix.shape}")
            
            return assignment_matrix, dependency_matrix
        
        else:
            raise ValueError(
                f"Matrix dimensions too different to align: "
                f"{assign_name} has {assign_cols} files, {dep_name} has {dep_rows} files. "
                f"Difference of {abs(assign_cols - dep_rows)} is too large (max 5 allowed)."
            )
    
    @staticmethod
    @transaction.atomic
    def create_analysis(project, monte_carlo_iterations=1000, functional_roles=None):
        """Create a new MC-STC analysis"""
        
        if functional_roles is None:
            functional_roles = ['developer', 'security', 'ops']
        
        analysis = MCSTCAnalysis.objects.create(
            project=project,
            monte_carlo_iterations=monte_carlo_iterations,
            functional_roles_used=functional_roles
        )
        
        return analysis
    
    @staticmethod
    def start_analysis(analysis, branch='main', tnm_output_dir=None):
        """Start MC-STC analysis execution"""
        
        try:
            # Clear any existing coordination pairs for this analysis to avoid duplicates
            MCSTCCoordinationPair.objects.filter(analysis=analysis).delete()
            
            # Get TNM output directory
            if not tnm_output_dir:
                repos_root = getattr(settings, 'TNM_OUTPUT_DIR', '/app/tnm_output')
                tnm_output_dir = f"{repos_root}/project_{analysis.project.id}_{branch.replace('/', '_')}"
            
            # Check if TNM data exists
            assignment_path = os.path.join(tnm_output_dir, 'AssignmentMatrix.json')
            dependency_path = os.path.join(tnm_output_dir, 'FileDependencyMatrix.json')
            id_to_user_path = os.path.join(tnm_output_dir, 'idToUser.json')
            id_to_file_path = os.path.join(tnm_output_dir, 'idToFile.json')
            
            required_files = [assignment_path, dependency_path, id_to_user_path]
            missing_files = [f for f in required_files if not os.path.exists(f)]
            
            if missing_files:
                analysis.error_message = f"Missing TNM files: {', '.join(missing_files)}"
                analysis.save()
                return {
                    'success': False,
                    'error': analysis.error_message
                }
            
            # Load TNM data
            with open(assignment_path, 'r') as f:
                assignment_matrix = json.load(f)
            
            with open(dependency_path, 'r') as f:
                dependency_matrix = json.load(f)
            
            with open(id_to_user_path, 'r') as f:
                id_to_user = json.load(f)
            
            id_to_file = {}
            if os.path.exists(id_to_file_path):
                with open(id_to_file_path, 'r') as f:
                    id_to_file = json.load(f)
            
            # Get contributor role classifications
            contributors = ProjectContributor.objects.filter(project=analysis.project)
            role_mapping = {}
            role_counts = {'developer': 0, 'security': 0, 'ops': 0, 'unclassified': 0}
            
            for contrib in contributors:
                if contrib.tnm_user_id and contrib.tnm_user_id in id_to_user:
                    role_mapping[contrib.tnm_user_id] = contrib.functional_role
                    role_counts[contrib.functional_role] += 1
            
            # Update analysis with role counts
            analysis.developer_count = role_counts['developer']
            analysis.security_count = role_counts['security']
            analysis.ops_count = role_counts['ops']
            analysis.total_contributors_analyzed = len(role_mapping)
            analysis.branch_analyzed = branch
            
            # Perform MC-STC calculation
            service = BaseMCSTCService(project_id=str(analysis.project.id))
            
            # Convert matrices to numpy arrays with error handling
            try:
                # Handle different matrix formats from TNM
                assignment_np = MCSTCAnalysisService._convert_tnm_matrix_to_numpy(assignment_matrix, "Assignment")
                dependency_np = MCSTCAnalysisService._convert_tnm_matrix_to_numpy(dependency_matrix, "Dependency")
                
                # Validate matrix dimensions
                if assignment_np.ndim != 2:
                    raise ValueError(f"Assignment matrix must be 2D, got {assignment_np.ndim}D")
                if dependency_np.ndim != 2:
                    raise ValueError(f"Dependency matrix must be 2D, got {dependency_np.ndim}D")
                
                # Ensure matrices are compatible - align dimensions if needed
                needs_alignment = (
                    assignment_np.shape[1] != dependency_np.shape[0] or  # Column-row mismatch
                    dependency_np.shape[0] != dependency_np.shape[1]     # Dependency not square
                )
                
                if needs_alignment:
                    # Try to align matrix dimensions
                    assignment_np, dependency_np = MCSTCAnalysisService._align_matrix_dimensions(
                        assignment_np, dependency_np, "Assignment", "Dependency"
                    )
                
            except (ValueError, TypeError) as e:
                analysis.error_message = f"Matrix conversion error: {str(e)}"
                analysis.save()
                return {
                    'success': False,
                    'error': analysis.error_message
                }
            
            # Calculate coordination matrices
            logger.info(f"Starting coordination matrix calculation for matrices: Assignment {assignment_np.shape}, Dependency {dependency_np.shape}")
            
            # For large matrices, this might take a while
            try:
                cr_matrix = service.calculate_cr_from_assignment_dependency(assignment_np, dependency_np)
                logger.info(f"CR matrix calculated: {cr_matrix.shape}")
            except Exception as e:
                logger.error(f"CR matrix calculation failed: {str(e)}")
                analysis.error_message = f"CR matrix calculation failed: {str(e)}"
                analysis.save()
                return {'success': False, 'error': str(e)}
            
            try:
                ca_matrix = assignment_np @ assignment_np.T  # Simple CA calculation
                logger.info(f"CA matrix calculated: {ca_matrix.shape}")
            except Exception as e:
                logger.error(f"CA matrix calculation failed: {str(e)}")
                analysis.error_message = f"CA matrix calculation failed: {str(e)}"
                analysis.save()
                return {'success': False, 'error': str(e)}
            
            # Identify role groups
            logger.info("Identifying role groups...")
            all_users = list(id_to_user.keys())
            developer_users = set()
            security_users = set()
            ops_users = set()
            
            for user_id in all_users:
                role = role_mapping.get(user_id, 'unclassified')
                if role == 'developer':
                    developer_users.add(user_id)
                elif role == 'security':
                    security_users.add(user_id)
                elif role == 'ops':
                    ops_users.add(user_id)
            
            logger.info(f"Role groups identified - Developers: {len(developer_users)}, Security: {len(security_users)}, Ops: {len(ops_users)}")
            
            # Calculate MC-STC
            if len(security_users) > 0 and len(developer_users) > 0:
                try:
                    logger.info("Starting MC-STC calculation...")
                    mcstc_value, mc_cr, mc_ca = service.calculate_2c_stc(
                        cr_matrix, ca_matrix, all_users,
                        security_users, developer_users
                    )
                    logger.info(f"MC-STC calculation completed: {mcstc_value}")
                    
                    # Ensure mcstc_value is a scalar number, not a dict or array
                    if isinstance(mcstc_value, (dict, list, np.ndarray)):
                        raise ValueError(f"MC-STC value should be a scalar, got {type(mcstc_value)}: {mcstc_value}")
                    
                    # Calculate role-specific coordination scores
                    dev_sec_score = MCSTCAnalysisService._calculate_role_coordination(
                        cr_matrix, ca_matrix, all_users, developer_users, security_users
                    )
                    dev_ops_score = MCSTCAnalysisService._calculate_role_coordination(
                        cr_matrix, ca_matrix, all_users, developer_users, ops_users
                    ) if ops_users else 0.0
                    sec_ops_score = MCSTCAnalysisService._calculate_role_coordination(
                        cr_matrix, ca_matrix, all_users, security_users, ops_users
                    ) if ops_users else 0.0
                    
                    # Validate all scores are scalars
                    for score_name, score_value in [
                        ('dev_sec_score', dev_sec_score),
                        ('dev_ops_score', dev_ops_score),
                        ('sec_ops_score', sec_ops_score)
                    ]:
                        if isinstance(score_value, (dict, list, np.ndarray)):
                            raise ValueError(f"{score_name} should be a scalar, got {type(score_value)}: {score_value}")
                    
                    # Calculate inter-class and intra-class scores
                    inter_class_score = dev_sec_score
                    intra_class_score = service.calculate_stc(cr_matrix, ca_matrix)
                    
                    # Validate intra_class_score
                    if isinstance(intra_class_score, (dict, list, np.ndarray)):
                        raise ValueError(f"Intra-class score should be a scalar, got {type(intra_class_score)}: {intra_class_score}")
                        
                except Exception as calc_error:
                    analysis.error_message = f"MC-STC calculation error: {str(calc_error)}"
                    analysis.save()
                    return {
                        'success': False,
                        'error': analysis.error_message
                    }
                
                # Update analysis results - ensure all values are floats
                analysis.mcstc_value = float(mcstc_value) if mcstc_value is not None else None
                analysis.inter_class_coordination_score = float(inter_class_score) if inter_class_score is not None else None
                analysis.intra_class_coordination_score = float(intra_class_score) if intra_class_score is not None else None
                analysis.developer_security_coordination = float(dev_sec_score) if dev_sec_score is not None else None
                analysis.developer_ops_coordination = float(dev_ops_score) if dev_ops_score is not None else None
                analysis.security_ops_coordination = float(sec_ops_score) if sec_ops_score is not None else None
                
                # Generate coordination pairs
                coordination_pairs = MCSTCAnalysisService._generate_coordination_pairs(
                    analysis, cr_matrix, ca_matrix, all_users, role_mapping, id_to_user, id_to_file
                )
                
                # Store top coordination pairs
                analysis.top_coordination_pairs = coordination_pairs[:10]
                analysis.is_completed = True
                
            else:
                analysis.error_message = "Insufficient role data for MC-STC analysis"
            
            analysis.save()
            
            return {
                'success': True,
                'mcstc_value': analysis.mcstc_value,
                'analysis_id': analysis.id
            }
            
        except Exception as e:
            analysis.error_message = str(e)
            analysis.save()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def _calculate_role_coordination(cr_matrix, ca_matrix, all_users, role1_users, role2_users):
        """Calculate coordination score between two role groups"""
        if not role1_users or not role2_users:
            return 0.0
        
        user_to_index = {user: i for i, user in enumerate(all_users)}
        
        total_cr = 0
        total_ca = 0
        
        for user1 in role1_users:
            for user2 in role2_users:
                if user1 in user_to_index and user2 in user_to_index:
                    i, j = user_to_index[user1], user_to_index[user2]
                    total_cr += cr_matrix[i, j]
                    total_ca += ca_matrix[i, j]
        
        return total_ca / total_cr if total_cr > 0 else 0.0
    
    @staticmethod
    def _generate_coordination_pairs(analysis, cr_matrix, ca_matrix, all_users, role_mapping, id_to_user, id_to_file):
        """Generate detailed coordination pair analysis"""
        
        pairs = []
        user_to_index = {user: i for i, user in enumerate(all_users)}
        
        for i, user1 in enumerate(all_users):
            for j, user2 in enumerate(all_users):
                if i >= j:  # Avoid duplicates
                    continue
                
                cr_value = cr_matrix[i, j]
                ca_value = ca_matrix[i, j]
                
                if cr_value > 0:  # Only consider pairs with coordination requirements
                    role1 = role_mapping.get(user1, 'unclassified')
                    role2 = role_mapping.get(user2, 'unclassified')
                    
                    coordination_gap = cr_value - ca_value
                    impact_score = abs(coordination_gap) * cr_value
                    
                    is_inter_class = role1 != role2
                    is_missed = coordination_gap > 0.1
                    is_unnecessary = coordination_gap < -0.1
                    
                    pair_data = {
                        'contributor1_id': user1,
                        'contributor1_role': role1,
                        'contributor1_email': id_to_user.get(user1, ''),
                        'contributor2_id': user2,
                        'contributor2_role': role2,
                        'contributor2_email': id_to_user.get(user2, ''),
                        'coordination_requirement': float(cr_value),
                        'actual_coordination': float(ca_value),
                        'coordination_gap': float(coordination_gap),
                        'impact_score': float(impact_score),
                        'is_inter_class': bool(is_inter_class),  # Convert to Python bool
                        'is_missed_coordination': bool(is_missed),  # Convert to Python bool
                        'is_unnecessary_coordination': bool(is_unnecessary),  # Convert to Python bool
                        'shared_files': [],  # Would need additional logic to determine
                        'coordination_files': []
                    }
                    
                    pairs.append(pair_data)
        
        # Sort by impact score
        pairs.sort(key=lambda x: x['impact_score'], reverse=True)
        
        # Create coordination pairs asynchronously in batches
        if pairs:
            threading.Thread(
                target=MCSTCAnalysisService._create_coordination_pairs_async,
                args=(analysis.id, pairs),
                daemon=True
            ).start()
            logger.info(f"Started async creation of {len(pairs)} coordination pairs")
        
        return pairs
    
    @staticmethod
    def _create_coordination_pairs_async(analysis_id, pairs_data):
        """Asynchronously create coordination pairs in batches"""
        try:
            from django.db import connection
            
            # Get analysis object
            analysis = MCSTCAnalysis.objects.get(id=analysis_id)
            
            # Create coordination pairs in batches to avoid memory issues
            batch_size = 1000
            total_pairs = len(pairs_data)
            
            logger.info(f"Creating {total_pairs} coordination pairs in batches of {batch_size}")
            
            for i in range(0, total_pairs, batch_size):
                batch = pairs_data[i:i + batch_size]
                coordination_pairs = []
                
                for pair_data in batch:
                    coordination_pairs.append(MCSTCCoordinationPair(
                        analysis=analysis,
                        **pair_data
                    ))
                
                # Bulk create this batch
                MCSTCCoordinationPair.objects.bulk_create(
                    coordination_pairs, 
                    batch_size=batch_size,
                    ignore_conflicts=True
                )
                
                logger.info(f"Created batch {i//batch_size + 1}/{(total_pairs-1)//batch_size + 1} "
                           f"({len(batch)} pairs)")
            
            # Close database connection to avoid connection leaks
            connection.close()
            
            logger.info(f"Successfully created all {total_pairs} coordination pairs for analysis {analysis_id}")
            
        except Exception as e:
            logger.error(f"Failed to create coordination pairs asynchronously: {e}", exc_info=True)
    
    @staticmethod
    def get_analysis_results(analysis):
        """Get comprehensive MC-STC analysis results"""
        
        if not analysis.is_completed:
            return {
                'error': 'Analysis not completed',
                'status': 'pending'
            }
        
        coordination_pairs = MCSTCCoordinationPair.objects.filter(
            analysis=analysis
        ).order_by('-impact_score')[:20]
        
        return {
            'mcstc_value': analysis.mcstc_value,
            'inter_class_score': analysis.inter_class_coordination_score,
            'intra_class_score': analysis.intra_class_coordination_score,
            'role_coordination': {
                'developer_security': analysis.developer_security_coordination,
                'developer_ops': analysis.developer_ops_coordination,
                'security_ops': analysis.security_ops_coordination
            },
            'role_distribution': {
                'developer': analysis.developer_count,
                'security': analysis.security_count,
                'ops': analysis.ops_count,
                'total': analysis.total_contributors_analyzed
            },
            'top_coordination_pairs': [
                {
                    'contributor1': f"{pair.contributor1_role}:{pair.contributor1_id}",
                    'contributor2': f"{pair.contributor2_role}:{pair.contributor2_id}",
                    'impact_score': pair.impact_score,
                    'coordination_gap': pair.coordination_gap,
                    'is_inter_class': pair.is_inter_class,
                    'status': 'missed' if pair.is_missed_coordination else 'adequate'
                }
                for pair in coordination_pairs
            ],
            'recommendations': MCSTCAnalysisService._generate_recommendations(analysis)
        }
    
    @staticmethod
    def _generate_recommendations(analysis):
        """Generate recommendations based on MC-STC results"""
        
        recommendations = []
        
        if analysis.mcstc_value < 0.5:
            recommendations.append("Overall MC-STC score is low. Consider improving cross-functional coordination.")
        
        if analysis.developer_security_coordination < 0.6:
            recommendations.append("Developer-Security coordination needs improvement. Consider regular security reviews.")
        
        if analysis.developer_ops_coordination < 0.6:
            recommendations.append("Developer-Ops coordination could be enhanced. Implement DevOps practices.")
        
        if analysis.security_count == 0:
            recommendations.append("No security personnel identified. Consider adding security expertise to the team.")
        
        if analysis.ops_count == 0:
            recommendations.append("No ops personnel identified. Consider adding operations expertise.")
        
        missed_pairs = MCSTCCoordinationPair.objects.filter(
            analysis=analysis,
            is_missed_coordination=True
        ).count()
        
        if missed_pairs > 5:
            recommendations.append(f"High number of missed coordination opportunities ({missed_pairs}). Review communication channels.")
        
        return recommendations
