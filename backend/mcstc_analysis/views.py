import logging
import os
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.db.models import Avg, Count, Q

from common.response import ApiResponse
from common.pagination import DefaultPagination
from projects.models import Project
from .models import MCSTCAnalysis, MCSTCCoordinationPair
from .serializers import (
    MCSTCAnalysisSerializer, MCSTCAnalysisCreateSerializer,
    MCSTCCoordinationPairSerializer, MCSTCResultSerializer,
    MCSTCStatsSerializer, MCSTCComparisonSerializer
)
from .services import MCSTCAnalysisService

logger = logging.getLogger(__name__)


class MCSTCAnalysisViewSet(viewsets.ModelViewSet):
    """
    ViewSet for MC-STC (Multi-Class Socio-Technical Congruence) analysis.
    
    MC-STC extends traditional STC analysis to consider functional roles and
    measure coordination between different classes of contributors (e.g., developers, security, ops).
    
    Provides endpoints to:
    - Create and manage MC-STC analyses
    - Start MC-STC calculations
    - Retrieve analysis results with role-specific insights
    - Compare coordination across functional roles
    """
    
    queryset = MCSTCAnalysis.objects.select_related('project').all()
    serializer_class = MCSTCAnalysisSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultPagination
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return MCSTCAnalysisCreateSerializer
        return MCSTCAnalysisSerializer
    
    def get_queryset(self):
        """Filter analyses based on query parameters"""
        queryset = MCSTCAnalysis.objects.select_related('project').all()
        
        # Filter by project
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        
        # Filter by completion status
        is_completed = self.request.query_params.get('is_completed')
        if is_completed is not None:
            queryset = queryset.filter(is_completed=is_completed.lower() == 'true')
        
        # Filter by functional roles
        roles = self.request.query_params.get('roles')
        if roles:
            role_list = roles.split(',')
            queryset = queryset.filter(functional_roles_used__overlap=role_list)
        
        return queryset.order_by('-analysis_date')
    
    def list(self, request, *args, **kwargs):
        """List all MC-STC analyses with logging"""
        user_id = request.user.id if request.user else None
        
        logger.info("MC-STC analyses list request", extra={
            'user_id': user_id,
            'query_params': dict(request.query_params)
        })
        
        try:
            queryset = self.get_queryset()
            page = self.paginate_queryset(queryset)
            
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(queryset, many=True)
            return ApiResponse.success(
                data=serializer.data,
                message=f"Retrieved {len(serializer.data)} MC-STC analyses"
            )
        except Exception as e:
            logger.error(f"Failed to list MC-STC analyses: {e}", exc_info=True)
            return ApiResponse.internal_error(
                error_message="Failed to retrieve MC-STC analyses",
                error_code="MCSTC_LIST_ERROR"
            )
    
    def create(self, request, *args, **kwargs):
        """Create a new MC-STC analysis"""
        user_id = request.user.id if request.user else None
        project_id = request.data.get('project')
        
        logger.info(f"Creating MC-STC analysis for project {project_id}", extra={
            'user_id': user_id,
            'project_id': project_id
        })
        
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Create analysis using service layer
            analysis = MCSTCAnalysisService.create_analysis(
                project=serializer.validated_data['project'],
                monte_carlo_iterations=serializer.validated_data.get('monte_carlo_iterations', 1000),
                functional_roles=serializer.validated_data.get('functional_roles_used', ['developer', 'security', 'ops'])
            )
            
            logger.info(f"MC-STC analysis created successfully", extra={
                'user_id': user_id,
                'analysis_id': analysis.id,
                'project_id': project_id
            })
            
            response_serializer = MCSTCAnalysisSerializer(analysis)
            return ApiResponse.created(
                data=response_serializer.data,
                message="MC-STC analysis created successfully"
            )
            
        except ValidationError as e:
            logger.error(f"Failed to create MC-STC analysis: {e}", extra={
                'user_id': user_id,
                'project_id': project_id,
                'validation_errors': e.detail
            })
            
            # Extract detailed validation errors
            error_details = []
            if isinstance(e.detail, dict):
                for field, errors in e.detail.items():
                    if isinstance(errors, list):
                        for error in errors:
                            error_details.append(f"{field}: {error}")
                    else:
                        error_details.append(f"{field}: {errors}")
            else:
                error_details.append(str(e.detail))
            
            return ApiResponse.validation_error(
                error_message=f"Validation failed: {'; '.join(error_details)}",
                error_code="MCSTC_VALIDATION_ERROR"
            )
            
        except Exception as e:
            logger.error(f"Failed to create MC-STC analysis: {e}", exc_info=True, extra={
                'user_id': user_id,
                'project_id': project_id
            })
            return ApiResponse.internal_error(
                error_message=f"Failed to create MC-STC analysis: {str(e)}",
                error_code="MCSTC_CREATION_ERROR"
            )
    
    @action(detail=True, methods=['post'])
    def start_analysis(self, request, pk=None):
        """
        Start MC-STC analysis for a project.
        
        POST /api/mcstc/analyses/{id}/start_analysis/
        Body: {
            "tnm_output_dir": "/path/to/tnm/output" (optional, auto-detected),
            "branch": "main" (optional)
        }
        """
        analysis = self.get_object()
        user_id = request.user.id if request.user else None
        
        logger.info(f"Starting MC-STC analysis {analysis.id}", extra={
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
            
            # Get parameters
            branch = request.data.get('branch', 'main')
            tnm_output_dir = request.data.get('tnm_output_dir')
            
            # Start analysis using service layer
            result = MCSTCAnalysisService.start_analysis(
                analysis=analysis,
                branch=branch,
                tnm_output_dir=tnm_output_dir
            )
            
            if result['success']:
                logger.info(f"MC-STC analysis started successfully", extra={
                    'user_id': user_id,
                    'analysis_id': analysis.id,
                    'mcstc_value': result.get('mcstc_value')
                })
                
                return ApiResponse.success(
                    data={
                        'analysis_id': analysis.id,
                        'mcstc_value': result.get('mcstc_value'),
                        'status': 'completed' if analysis.is_completed else 'running'
                    },
                    message="MC-STC analysis completed successfully"
                )
            else:
                return ApiResponse.error(
                    error_message=result['error'],
                    error_code="MCSTC_ANALYSIS_FAILED"
                )
                
        except Exception as e:
            logger.error(f"Failed to start MC-STC analysis: {e}", exc_info=True)
            return ApiResponse.internal_error(
                error_message="Failed to start MC-STC analysis",
                error_code="MCSTC_START_ERROR"
            )
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """
        Get detailed MC-STC analysis results.
        
        GET /api/mcstc/analyses/{id}/results/
        Query params:
        - top_n: Number of top coordination pairs to return (default: 20)
        - role_filter: Filter coordination pairs by role (developer, security, ops)
        """
        analysis = self.get_object()
        user_id = request.user.id if request.user else None
        
        logger.info(f"Retrieving MC-STC results for analysis {analysis.id}", extra={
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
            
            # Get results using service layer
            results = MCSTCAnalysisService.get_analysis_results(analysis)
            
            # Apply filters
            top_n = int(request.query_params.get('top_n', 20))
            role_filter = request.query_params.get('role_filter')
            
            if role_filter:
                # Filter coordination pairs by role
                filtered_pairs = [
                    pair for pair in results['top_coordination_pairs']
                    if role_filter in pair['contributor1'] or role_filter in pair['contributor2']
                ]
                results['top_coordination_pairs'] = filtered_pairs[:top_n]
            else:
                results['top_coordination_pairs'] = results['top_coordination_pairs'][:top_n]
            
            return ApiResponse.success(
                data=results,
                message="MC-STC results retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Failed to retrieve MC-STC results: {e}", exc_info=True)
            return ApiResponse.internal_error(
                error_message="Failed to retrieve MC-STC results",
                error_code="MCSTC_RESULTS_ERROR"
            )
    
    @action(detail=False, methods=['get'])
    def project_stats(self, request):
        """
        Get MC-STC statistics for all accessible projects.
        
        GET /api/mcstc/analyses/project_stats/
        """
        user_id = request.user.id if request.user else None
        
        logger.info("MC-STC project statistics request", extra={
            'user_id': user_id
        })
        
        try:
            # Get projects user has access to
            user_profile = request.user.profile
            owned_projects = Q(owner_profile=user_profile)
            member_projects = Q(members__profile=user_profile)
            
            projects = Project.objects.filter(
                (owned_projects | member_projects) & Q(deleted_at__isnull=True)
            ).distinct()
            
            stats_data = []
            
            for project in projects:
                analyses = MCSTCAnalysis.objects.filter(project=project)
                
                if not analyses.exists():
                    continue
                
                completed_analyses = analyses.filter(is_completed=True)
                latest_analysis = completed_analyses.order_by('-analysis_date').first()
                
                avg_mcstc = completed_analyses.aggregate(
                    avg_mcstc=Avg('mcstc_value')
                )['avg_mcstc'] or 0.0
                
                stats_data.append({
                    'project_id': project.id,
                    'project_name': project.name,
                    'total_analyses': analyses.count(),
                    'completed_analyses': completed_analyses.count(),
                    'average_mcstc_value': round(avg_mcstc, 3),
                    'latest_mcstc_value': latest_analysis.mcstc_value if latest_analysis else None,
                    'role_distribution': {
                        'developer': latest_analysis.developer_count if latest_analysis else 0,
                        'security': latest_analysis.security_count if latest_analysis else 0,
                        'ops': latest_analysis.ops_count if latest_analysis else 0
                    },
                    'coordination_health': MCSTCAnalysisViewSet._get_coordination_health(avg_mcstc)
                })
            
            return ApiResponse.success(
                data=stats_data,
                message=f"Retrieved MC-STC statistics for {len(stats_data)} projects"
            )
            
        except Exception as e:
            logger.error(f"Failed to get MC-STC project stats: {e}", exc_info=True)
            return ApiResponse.internal_error(
                error_message="Failed to retrieve MC-STC project statistics",
                error_code="MCSTC_STATS_ERROR"
            )
    
    @staticmethod
    def _get_coordination_health(mcstc_value):
        """Determine coordination health based on MC-STC value"""
        if mcstc_value >= 0.8:
            return 'excellent'
        elif mcstc_value >= 0.6:
            return 'good'
        elif mcstc_value >= 0.4:
            return 'fair'
        else:
            return 'poor'


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def project_mcstc_comparison(request, project_id):
    """
    Compare MC-STC values and role coordination for a project.
    
    GET /api/mcstc/projects/{project_id}/comparison/
    Query params:
    - analysis_id: Specific analysis ID (optional, uses latest if not provided)
    - role_focus: Focus on specific role coordination (developer, security, ops)
    - time_period: Compare over time period in days (default: 30)
    """
    user_id = request.user.id if request.user else None
    
    logger.info(f"MC-STC comparison request for project {project_id}", extra={
        'user_id': user_id,
        'project_id': project_id
    })
    
    try:
        # Get project
        project = get_object_or_404(Project, id=project_id)
        
        # Get analysis
        analysis_id = request.query_params.get('analysis_id')
        if analysis_id:
            analysis = get_object_or_404(MCSTCAnalysis, id=analysis_id, project=project)
        else:
            analysis = MCSTCAnalysis.objects.filter(
                project=project,
                is_completed=True
            ).order_by('-analysis_date').first()
            
            if not analysis:
                return ApiResponse.error(
                    error_message="No completed MC-STC analysis found for this project",
                    error_code="NO_MCSTC_ANALYSIS_FOUND",
                    status_code=status.HTTP_404_NOT_FOUND
                )
        
        # Get comparison data
        role_focus = request.query_params.get('role_focus')
        
        comparison_data = {
            'project_id': project_id,
            'project_name': project.name,
            'analysis_date': analysis.analysis_date,
            'mcstc_value': analysis.mcstc_value,
            'role_coordination_scores': {
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
            'top_issues': [],
            'improvement_suggestions': []
        }
        
        # Get top coordination issues
        coordination_pairs = MCSTCCoordinationPair.objects.filter(
            analysis=analysis,
            is_missed_coordination=True
        ).order_by('-impact_score')[:10]
        
        for pair in coordination_pairs:
            comparison_data['top_issues'].append({
                'pair': f"{pair.contributor1_role}:{pair.contributor1_id} <-> {pair.contributor2_role}:{pair.contributor2_id}",
                'impact_score': pair.impact_score,
                'coordination_gap': pair.coordination_gap,
                'is_inter_class': pair.is_inter_class
            })
        
        # Generate improvement suggestions
        if analysis.developer_security_coordination < 0.6:
            comparison_data['improvement_suggestions'].append(
                "Improve developer-security coordination through regular security reviews"
            )
        
        if analysis.security_count == 0:
            comparison_data['improvement_suggestions'].append(
                "Consider adding dedicated security personnel to the team"
            )
        
        return ApiResponse.success(
            data=comparison_data,
            message="MC-STC comparison data retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to get MC-STC comparison: {e}", exc_info=True)
        return ApiResponse.internal_error(
            error_message="Failed to retrieve MC-STC comparison data",
            error_code="MCSTC_COMPARISON_ERROR"
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def coordination_pairs(request, analysis_id):
    """
    Get detailed coordination pairs for an MC-STC analysis.
    
    GET /api/mcstc/analyses/{analysis_id}/coordination_pairs/
    Query params:
    - top_n: Number of pairs to return (default: 50)
    - role_filter: Filter by role (developer, security, ops)
    - status_filter: Filter by status (missed, unnecessary, adequate)
    - inter_class_only: Show only inter-class coordination (true/false)
    """
    user_id = request.user.id if request.user else None
    
    logger.info(f"Coordination pairs request for analysis {analysis_id}", extra={
        'user_id': user_id,
        'analysis_id': analysis_id
    })
    
    try:
        analysis = get_object_or_404(MCSTCAnalysis, id=analysis_id)
        
        queryset = MCSTCCoordinationPair.objects.filter(analysis=analysis)
        
        # Apply filters
        role_filter = request.query_params.get('role_filter')
        if role_filter:
            queryset = queryset.filter(
                Q(contributor1_role=role_filter) | Q(contributor2_role=role_filter)
            )
        
        status_filter = request.query_params.get('status_filter')
        if status_filter == 'missed':
            queryset = queryset.filter(is_missed_coordination=True)
        elif status_filter == 'unnecessary':
            queryset = queryset.filter(is_unnecessary_coordination=True)
        elif status_filter == 'adequate':
            queryset = queryset.filter(
                is_missed_coordination=False,
                is_unnecessary_coordination=False
            )
        
        inter_class_only = request.query_params.get('inter_class_only', '').lower() == 'true'
        if inter_class_only:
            queryset = queryset.filter(is_inter_class=True)
        
        top_n = int(request.query_params.get('top_n', 50))
        queryset = queryset.order_by('-impact_score')[:top_n]
        
        serializer = MCSTCCoordinationPairSerializer(queryset, many=True)
        
        return ApiResponse.success(
            data={
                'analysis_id': analysis_id,
                'coordination_pairs': serializer.data,
                'total_pairs': len(serializer.data)
            },
            message=f"Retrieved {len(serializer.data)} coordination pairs"
        )
        
    except Exception as e:
        logger.error(f"Failed to get coordination pairs: {e}", exc_info=True)
        return ApiResponse.internal_error(
            error_message="Failed to retrieve coordination pairs",
            error_code="COORDINATION_PAIRS_ERROR"
        )
