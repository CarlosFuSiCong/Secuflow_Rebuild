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
    ViewSet for STC (Spanning Tree Centrality) analysis.
    
    Provides endpoints to:
    - Create and manage STC analyses
    - Start STC calculations
    - Retrieve analysis results
    - Compare contributor centrality
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
            assignment_matrix_path = os.path.join(tnm_output_dir, 'AssignmentMatrix.json')
            if not os.path.exists(assignment_matrix_path):
                analysis.error_message = f"TNM output not found: {assignment_matrix_path}"
                analysis.save()
                return ApiResponse.error(
                    error_message="TNM analysis data not found. Please run TNM analysis first.",
                    error_code="TNM_DATA_NOT_FOUND",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Load CA (Contribution Assignment) matrix
            with open(assignment_matrix_path, 'r') as f:
                ca_data = json.load(f)
            
            # Convert to numpy array
            ca_matrix = np.array(ca_data)
            
            # Validate CA matrix
            if ca_matrix.ndim != 2:
                analysis.error_message = "Invalid CA matrix: must be 2-dimensional"
                analysis.save()
                return ApiResponse.error(
                    error_message="Invalid CA matrix format",
                    error_code="INVALID_DATA",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            logger.info(f"CA matrix shape: {ca_matrix.shape} (developers × files)", extra={
                'analysis_id': analysis.id,
                'developers': ca_matrix.shape[0],
                'files': ca_matrix.shape[1]
            })
            
            # Initialize service
            if analysis.use_monte_carlo:
                service = MCSTCService(
                    project_id=str(analysis.project.id),
                    iterations=analysis.monte_carlo_iterations
                )
            else:
                service = STCService(project_id=str(analysis.project.id))
            
            # Calculate STC from CA matrix
            # Service will automatically compute CR = CA × CA^T
            if analysis.use_monte_carlo:
                stc_values = service.calculate_mc_stc_from_ca(ca_matrix)
            else:
                stc_values = service.calculate_stc_from_ca(ca_matrix)
            
            # Save results
            results_filename = f"stc_results_{analysis.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            results_path = os.path.join(tnm_output_dir, results_filename)
            
            # Load user ID mapping
            id_to_user_path = os.path.join(tnm_output_dir, 'idToUser.json')
            user_mapping = {}
            if os.path.exists(id_to_user_path):
                with open(id_to_user_path, 'r') as f:
                    user_mapping = json.load(f)
            
            # Prepare results with contributor info
            results_with_info = []
            for node_id, stc_value in stc_values.items():
                contributor_login = user_mapping.get(node_id, f"Unknown_{node_id}")
                results_with_info.append({
                    'node_id': node_id,
                    'contributor_login': contributor_login,
                    'stc_value': float(stc_value)
                })
            
            # Sort by STC value descending
            results_with_info.sort(key=lambda x: x['stc_value'], reverse=True)
            
            # Add ranks
            for rank, result in enumerate(results_with_info, 1):
                result['rank'] = rank
            
            # Save results to file
            os.makedirs(os.path.dirname(results_path), exist_ok=True)
            with open(results_path, 'w') as f:
                json.dump({
                    'analysis_id': analysis.id,
                    'project_id': str(analysis.project.id),
                    'analysis_date': datetime.now().isoformat(),
                    'use_monte_carlo': analysis.use_monte_carlo,
                    'total_nodes': len(stc_values),
                    'results': results_with_info
                }, f, indent=2)
            
            # Update analysis record
            analysis.results_file = results_path
            analysis.is_completed = True
            analysis.error_message = None
            analysis.save()
            
            logger.info(f"STC analysis {analysis.id} completed successfully", extra={
                'user_id': user_id,
                'analysis_id': analysis.id,
                'total_nodes': len(stc_values)
            })
            
            return ApiResponse.success(
                data={
                    'analysis_id': analysis.id,
                    'total_nodes': len(stc_values),
                    'results_file': results_filename,
                    'top_contributors': results_with_info[:10]
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
            if top_n:
                try:
                    top_n = int(top_n)
                    results_data['results'] = results_data['results'][:top_n]
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
        for result in results_data.get('results', []):
            login = result.get('contributor_login')
            if login and login in contributor_map:
                contrib_data = contributor_map[login]
                comparison_data.append({
                    'contributor_login': login,
                    'contributor_id': contrib_data['id'],
                    'stc_value': result['stc_value'],
                    'stc_rank': result['rank'],
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
        
        return ApiResponse.success(
            data={
                'analysis_id': analysis.id,
                'project_id': str(project.id),
                'project_name': project.name,
                'analysis_date': analysis.analysis_date.isoformat(),
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
