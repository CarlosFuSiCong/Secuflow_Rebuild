import logging
import json
import os
from datetime import datetime
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.conf import settings

from .models import STCAnalysis
from .serializers import (
    STCAnalysisSerializer, STCAnalysisCreateSerializer, 
    STCAnalysisResultsSerializer, STCComparisonSerializer
)
from .services import STCService, MCSTCService
from projects.models import Project
from contributors.models import ProjectContributor
from common.response import ApiResponse
from common.pagination import DefaultPagination
import numpy as np
from rest_framework.exceptions import ValidationError as DRFValidationError

# Initialize logger
logger = logging.getLogger(__name__)


class STCAnalysisViewSet(viewsets.ModelViewSet):
    """
    ViewSet for STC (Socio-Technical Congruence) analysis.
    
    STC measures the alignment between coordination requirements and actual coordination:
    - CR (Coordination Requirements): who needs to coordinate (from technical dependencies)
    - CA (Coordination Actuals): who actually coordinates (from communication data)
    - STC = |CR ∩ CA| / |CR|
    
    Provides endpoints to:
    - Create and manage STC analyses
    - Start STC calculations
    - Retrieve analysis results
    - Compare contributor coordination
    """
    
    queryset = STCAnalysis.objects.select_related('project').all()
    serializer_class = STCAnalysisSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultPagination
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return STCAnalysisCreateSerializer
        return STCAnalysisSerializer
    
    def get_queryset(self):
        """Filter analyses based on query parameters"""
        queryset = STCAnalysis.objects.select_related('project').all()
        
        # Filter by project
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        
        # Filter by completion status
        is_completed = self.request.query_params.get('is_completed')
        if is_completed is not None:
            queryset = queryset.filter(is_completed=is_completed.lower() == 'true')
        
        return queryset.order_by('-analysis_date')
    
    def list(self, request, *args, **kwargs):
        """List all STC analyses with logging"""
        user_id = request.user.id if request.user else None
        logger.info("STC analyses list request", extra={'user_id': user_id})
        
        try:
            queryset = self.filter_queryset(self.get_queryset())
            
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                paginated_data = self.get_paginated_response(serializer.data).data
                
                return ApiResponse.success(
                    data=paginated_data,
                    message="STC analyses retrieved successfully"
                )
            
            serializer = self.get_serializer(queryset, many=True)
            return ApiResponse.success(
                data={'results': serializer.data, 'count': queryset.count()},
                message="STC analyses retrieved successfully"
            )
        except Exception as e:
            logger.error(f"Failed to list STC analyses: {e}", extra={'user_id': user_id}, exc_info=True)
            return ApiResponse.internal_error(
                error_message="Failed to retrieve STC analyses",
                error_code="STC_LIST_ERROR"
            )
    
    def create(self, request, *args, **kwargs):
        """Create a new STC analysis"""
        user_id = request.user.id if request.user else None
        project_id = request.data.get('project')
        
        logger.info("Creating new STC analysis", extra={
            'user_id': user_id,
            'project_id': project_id
        })
        
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            return ApiResponse.success(
                data=STCAnalysisSerializer(serializer.instance).data,
                message="STC analysis created successfully",
                status_code=status.HTTP_201_CREATED
            )
        except DRFValidationError as e:
            logger.warning(f"Validation error creating STC analysis: {e}", extra={
                'user_id': user_id,
                'project_id': project_id
            })
            return ApiResponse.error(
                error_message="Validation error",
                error_code="VALIDATION_ERROR",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Failed to create STC analysis: {e}", extra={
                'user_id': user_id,
                'project_id': project_id
            }, exc_info=True)
            return ApiResponse.internal_error(
                error_message="Failed to create STC analysis",
                error_code="STC_CREATE_ERROR"
            )
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single STC analysis"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return ApiResponse.success(
                data=serializer.data,
                message="STC analysis retrieved successfully"
            )
        except Exception as e:
            logger.error(f"Failed to retrieve STC analysis: {e}", exc_info=True)
            return ApiResponse.internal_error(
                error_message="Failed to retrieve analysis",
                error_code="STC_RETRIEVE_ERROR"
            )
    
    def _load_sparse_matrix(self, json_data: dict, num_rows: int, num_cols: int) -> np.ndarray:
        """Convert sparse JSON format to dense numpy matrix"""
        matrix = np.zeros((num_rows, num_cols))
        for row_id, row_data in json_data.items():
            i = int(row_id)
            if i >= num_rows:
                continue
            for col_id, value in row_data.items():
                j = int(col_id)
                if j < num_cols:
                    matrix[i, j] = float(value)
        return matrix
    
    @action(detail=True, methods=['post'])
    def start_analysis(self, request, pk=None):
        """
        Start STC analysis for a project.
        
        POST /api/stc/analyses/{id}/start_analysis/
        Body: {
            "tnm_output_dir": "/path/to/tnm/output" (optional, auto-detected),
            "branch": "main" (optional)
        }
        """
        analysis = self.get_object()
        user_id = request.user.id if request.user else None
        
        logger.info(f"Starting STC analysis {analysis.id}", extra={
            'user_id': user_id,
            'analysis_id': analysis.id,
            'project_id': analysis.project.id
        })
        
        try:
            # Check if already completed
            if analysis.is_completed:
                return ApiResponse.error(
                    error_message="Analysis already completed",
                    error_code="ANALYSIS_ALREADY_COMPLETED",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Get TNM output directory
            branch = request.data.get('branch', 'main')
            tnm_output_dir = request.data.get('tnm_output_dir')
            
            if not tnm_output_dir:
                repos_root = getattr(settings, 'TNM_OUTPUT_DIR', '/app/tnm_output')
                tnm_output_dir = f"{repos_root}/project_{analysis.project.id}_{branch.replace('/', '_')}"
            
            # Check if TNM data exists
            assignment_path = os.path.join(tnm_output_dir, 'AssignmentMatrix.json')
            dependency_path = os.path.join(tnm_output_dir, 'FileDependencyMatrix.json')
            id_to_user_path = os.path.join(tnm_output_dir, 'idToUser.json')
            
            if not os.path.exists(assignment_path):
                analysis.error_message = f"TNM output not found: {assignment_path}"
                analysis.save()
                return ApiResponse.error(
                    error_message="TNM analysis data not found. Please run TNM analysis first.",
                    error_code="TNM_DATA_NOT_FOUND",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Load TNM output data
            with open(assignment_path, 'r') as f:
                assignment_data = json.load(f)
            
            with open(dependency_path, 'r') as f:
                dependency_data = json.load(f)
            
            with open(id_to_user_path, 'r') as f:
                id_to_user = json.load(f)
            
            # Determine matrix dimensions
            all_user_ids = set(assignment_data.keys())
            all_file_ids = set()
            for user_files in assignment_data.values():
                all_file_ids.update(user_files.keys())
            for file_deps in dependency_data.values():
                all_file_ids.update(file_deps.keys())
                all_file_ids.add(int(list(dependency_data.keys())[0]) if dependency_data else 0)
            
            num_users = len(all_user_ids)
            num_files = len(all_file_ids)
            
            logger.info(f"Matrix dimensions: {num_users} users × {num_files} files", extra={
                'analysis_id': analysis.id,
                'num_users': num_users,
                'num_files': num_files
            })
            
            # Convert sparse matrices to dense numpy arrays
            assignment_matrix = self._load_sparse_matrix(assignment_data, num_users, num_files)
            dependency_matrix = self._load_sparse_matrix(dependency_data, num_files, num_files)
            
            # Create ordered user list for indexing
            all_users = sorted([str(uid) for uid in all_user_ids], key=lambda x: int(x))
            
            # Initialize service
            threshold = 0  # Binary threshold: >0 means coordination required
            
            if analysis.use_monte_carlo:
                service = MCSTCService(
                    project_id=str(analysis.project.id),
                    threshold=threshold
                )
            else:
                service = STCService(
                    project_id=str(analysis.project.id),
                    threshold=threshold
                )
            
            # Calculate CR (Coordination Requirements) from Assignment and Dependency
            cr_matrix = service.calculate_cr_from_assignment_dependency(
                assignment_matrix, 
                dependency_matrix
            )
            
            # Calculate CA (Coordination Actuals) from file modifiers
            # If two developers modify the same file, they have actual coordination
            file_modifiers = {}
            for user_id, files in assignment_data.items():
                for file_id, count in files.items():
                    if count > 0:
                        if file_id not in file_modifiers:
                            file_modifiers[file_id] = set()
                        file_modifiers[file_id].add(str(user_id))
            
            ca_matrix = service.calculate_ca_from_file_modifiers(
                file_modifiers,
                all_users
            )
            
            logger.info(f"Matrices calculated", extra={
                'analysis_id': analysis.id,
                'cr_edges': int(np.sum(cr_matrix > 0) / 2),  # Undirected edges
                'ca_edges': int(np.sum(ca_matrix > 0) / 2)
            })
            
            # Calculate STC or MC-STC
            if analysis.use_monte_carlo:
                # For MC-STC, identify developer roles from contributor data
                from contributors.models import ProjectContributor
                from contributors.enums import FunctionalRole
                
                # Get contributor role assignments
                contributors = ProjectContributor.objects.filter(
                    project=analysis.project
                ).select_related('contributor')
                
                # Build user role mapping
                security_users = set()
                developer_users = set()
                
                for pc in contributors:
                    user_id = pc.tnm_user_id
                    if not user_id:
                        # Try to match by github_login
                        login = pc.contributor.github_login
                        # Find user_id in id_to_user mapping
                        for uid, email_or_login in id_to_user.items():
                            if login in email_or_login or email_or_login in login:
                                user_id = uid
                                break
                    
                    if user_id and user_id in all_users:
                        if pc.functional_role == FunctionalRole.SECURITY:
                            security_users.add(user_id)
                        elif pc.functional_role == FunctionalRole.DEVELOPER:
                            developer_users.add(user_id)
                        # Note: OPS users can be added to developer_users or handled separately
                        elif pc.functional_role == FunctionalRole.OPS:
                            developer_users.add(user_id)  # Treat OPS as developers for 2C-STC
                
                # Calculate 2C-STC (Dev-Sec)
                if security_users and developer_users:
                    stc_value, mc_cr, mc_ca = service.calculate_2c_stc(
                        cr_matrix, ca_matrix, all_users,
                        security_users, developer_users
                    )
                    
                    logger.info(f"MC-STC calculated with role distribution", extra={
                        'analysis_id': analysis.id,
                        'security_count': len(security_users),
                        'developer_count': len(developer_users)
                    })
                else:
                    logger.warning(f"Insufficient role data for MC-STC, using standard STC", extra={
                        'analysis_id': analysis.id,
                        'security_count': len(security_users),
                        'developer_count': len(developer_users)
                    })
                    stc_value = service.calculate_stc(cr_matrix, ca_matrix)
            else:
                stc_value = service.calculate_stc(cr_matrix, ca_matrix)
            
            # Get missed coordination for each developer
            missed_coord = service.get_missed_coordination(cr_matrix, ca_matrix)
            missed_counts = {}
            for i, user_id in enumerate(all_users):
                missed_counts[user_id] = int(np.sum(missed_coord[i, :]))
            
            # Prepare results with contributor info
            results_data = {
                'stc_value': float(stc_value),
                'total_required_edges': int(np.sum(cr_matrix > 0) / 2),
                'total_actual_edges': int(np.sum(ca_matrix > 0) / 2),
                'satisfied_edges': int(np.sum((cr_matrix > 0) & (ca_matrix > 0)) / 2),
                'developers': []
            }
            
            for user_id in sorted(missed_counts.keys(), key=lambda x: missed_counts[x], reverse=True):
                contributor_login = id_to_user.get(user_id, f"Unknown_{user_id}")
                results_data['developers'].append({
                    'user_id': user_id,
                    'contributor_login': contributor_login,
                    'missed_coordination_count': missed_counts[user_id],
                    'required_coordination': int(np.sum(cr_matrix[int(user_id), :] > 0)),
                    'actual_coordination': int(np.sum(ca_matrix[int(user_id), :] > 0))
                })
            
            # Save results to file
            results_filename = f"stc_results_{analysis.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            results_path = os.path.join(tnm_output_dir, results_filename)
            
            os.makedirs(os.path.dirname(results_path), exist_ok=True)
            with open(results_path, 'w') as f:
                json.dump({
                    'analysis_id': analysis.id,
                    'project_id': str(analysis.project.id),
                    'analysis_date': datetime.now().isoformat(),
                    'use_monte_carlo': analysis.use_monte_carlo,
                    'results': results_data
                }, f, indent=2)
            
            # Update analysis record
            analysis.results_file = results_path
            analysis.is_completed = True
            analysis.error_message = None
            analysis.save()
            
            logger.info(f"STC analysis {analysis.id} completed successfully", extra={
                'user_id': user_id,
                'analysis_id': analysis.id,
                'stc_value': stc_value
            })
            
            return ApiResponse.success(
                data={
                    'analysis_id': analysis.id,
                    'stc_value': float(stc_value),
                    'results_file': results_filename,
                    'top_missed_coordination': results_data['developers'][:10]
                },
                message="STC analysis completed successfully"
            )
            
        except ValueError as e:
            analysis.error_message = str(e)
            analysis.save()
            logger.error(f"STC analysis validation error: {e}", extra={
                'user_id': user_id,
                'analysis_id': analysis.id
            }, exc_info=True)
            return ApiResponse.error(
                error_message=f"Invalid data: {str(e)}",
                error_code="INVALID_DATA",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            analysis.error_message = str(e)
            analysis.save()
            logger.error(f"STC analysis failed: {e}", extra={
                'user_id': user_id,
                'analysis_id': analysis.id
            }, exc_info=True)
            return ApiResponse.internal_error(
                error_message="Failed to complete STC analysis",
                error_code="STC_ANALYSIS_ERROR"
            )
        
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """
        Get STC analysis results.
        
        GET /api/stc/analyses/{id}/results/
        Query params: top_n (default: all)
        """
        analysis = self.get_object()
        user_id = request.user.id if request.user else None
        
        logger.info(f"Retrieving STC analysis results {analysis.id}", extra={
            'user_id': user_id,
            'analysis_id': analysis.id
        })
        
        try:
            if not analysis.is_completed:
                return ApiResponse.error(
                    error_message="Analysis not completed yet",
                    error_code="ANALYSIS_NOT_COMPLETED",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            if not analysis.results_file or not os.path.exists(analysis.results_file):
                return ApiResponse.error(
                    error_message="Results file not found",
                    error_code="RESULTS_NOT_FOUND",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Load results
            with open(analysis.results_file, 'r') as f:
                results_data = json.load(f)
            
            # Apply top_n filter if specified
            top_n = request.query_params.get('top_n')
            if top_n and 'results' in results_data and 'developers' in results_data['results']:
                try:
                    top_n = int(top_n)
                    results_data['results']['developers'] = results_data['results']['developers'][:top_n]
                except ValueError:
                    pass
            
            return ApiResponse.success(
                data=results_data,
                message="STC analysis results retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Failed to retrieve STC results: {e}", extra={
                'user_id': user_id,
                'analysis_id': analysis.id
            }, exc_info=True)
            return ApiResponse.internal_error(
                error_message="Failed to retrieve analysis results",
                error_code="RESULTS_RETRIEVAL_ERROR"
            )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def project_stc_comparison(request, project_id):
    """
    Compare STC values with contributor statistics for a project.
    
    GET /api/stc/projects/{project_id}/comparison/
    Query params:
    - analysis_id: Specific analysis ID (optional, uses latest if not provided)
    - role: Filter by functional role
    - top_n: Return only top N contributors
    """
    user_id = request.user.id if request.user else None
    
    logger.info(f"STC comparison request for project {project_id}", extra={
        'user_id': user_id,
        'project_id': project_id
    })
    
    try:
        # Get project
        project = get_object_or_404(Project, id=project_id)
        
        # Get analysis
        analysis_id = request.query_params.get('analysis_id')
        if analysis_id:
            analysis = get_object_or_404(STCAnalysis, id=analysis_id, project=project)
        else:
            analysis = STCAnalysis.objects.filter(
                project=project,
                is_completed=True
            ).order_by('-analysis_date').first()
            
            if not analysis:
                return ApiResponse.error(
                    error_message="No completed STC analysis found for this project",
                    error_code="NO_ANALYSIS_FOUND",
                    status_code=status.HTTP_404_NOT_FOUND
                )
        
        # Load results
        if not analysis.results_file or not os.path.exists(analysis.results_file):
            return ApiResponse.error(
                error_message="Analysis results not found",
                error_code="RESULTS_NOT_FOUND",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        with open(analysis.results_file, 'r') as f:
            results_data = json.load(f)
        
        # Get contributor statistics
        contributors = ProjectContributor.objects.filter(project=project).select_related('contributor')
        
        # Build contributor mapping
        contributor_map = {}
        for pc in contributors:
            contributor_map[pc.contributor.github_login] = {
                'id': pc.contributor.id,
                'total_modifications': pc.total_modifications,
                'files_modified': pc.files_modified,
                'functional_role': pc.functional_role,
                'is_core_contributor': pc.is_core_contributor
            }
        
        # Combine STC results with contributor data
        comparison_data = []
        if 'results' in results_data and 'developers' in results_data['results']:
            for dev_result in results_data['results']['developers']:
                login = dev_result.get('contributor_login')
                if login and login in contributor_map:
                    contrib_data = contributor_map[login]
                    comparison_data.append({
                        'contributor_login': login,
                        'contributor_id': contrib_data['id'],
                        'missed_coordination_count': dev_result['missed_coordination_count'],
                        'required_coordination': dev_result['required_coordination'],
                        'actual_coordination': dev_result['actual_coordination'],
                        'total_modifications': contrib_data['total_modifications'],
                        'files_modified': contrib_data['files_modified'],
                        'functional_role': contrib_data['functional_role'],
                        'is_core_contributor': contrib_data['is_core_contributor']
                    })
        
        # Apply filters
        role_filter = request.query_params.get('role')
        if role_filter:
            comparison_data = [c for c in comparison_data if c['functional_role'] == role_filter]
        
        top_n = request.query_params.get('top_n')
        if top_n:
            try:
                comparison_data = comparison_data[:int(top_n)]
            except ValueError:
                pass
        
        logger.info(f"STC comparison completed for project {project_id}", extra={
            'user_id': user_id,
            'project_id': project_id,
            'contributors_count': len(comparison_data)
        })
        
        # Extract STC value from results
        stc_value = 0
        if 'results' in results_data:
            if isinstance(results_data['results'], dict):
                stc_value = results_data['results'].get('stc_value', 0)
        
        return ApiResponse.success(
            data={
                'analysis_id': analysis.id,
                'project_id': str(project.id),
                'project_name': project.name,
                'analysis_date': analysis.analysis_date.isoformat(),
                'stc_value': stc_value,
                'total_contributors': len(comparison_data),
                'contributors': comparison_data
            },
            message="STC comparison data retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"STC comparison failed: {e}", extra={
            'user_id': user_id,
            'project_id': project_id
        }, exc_info=True)
        return ApiResponse.internal_error(
            error_message="Failed to retrieve STC comparison data",
            error_code="STC_COMPARISON_ERROR"
        )
