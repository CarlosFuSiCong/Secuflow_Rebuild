"""
Project Monitoring Views

This module provides API endpoints for project monitoring functionality.
Users can only access monitoring data for projects they own or are members of.
"""

import logging
from datetime import datetime, timedelta
from django.db.models import Q, Count, Avg, Max, Min
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from common.response import ApiResponse
from common.pagination import DefaultPagination
from projects.models import Project, ProjectMember
from .models import ProjectMonitoring, ProjectMonitoringSubscription, AnalysisType, AnalysisStatus
from .serializers import (
    ProjectMonitoringSerializer, ProjectMonitoringListSerializer,
    ProjectMonitoringStatsSerializer, ProjectMonitoringTrendSerializer,
    ProjectMonitoringSubscriptionSerializer, CreateMonitoringAnalysisSerializer
)

logger = logging.getLogger(__name__)


class ProjectMonitoringViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing project monitoring records.
    
    Users can only access monitoring data for projects they own or are members of.
    """
    
    serializer_class = ProjectMonitoringSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultPagination
    
    def get_queryset(self):
        """
        Get monitoring records for projects the user has access to.
        """
        user_profile = self.request.user.profile
        
        # Get projects user owns or is a member of
        owned_projects = Q(project__owner_profile=user_profile)
        member_projects = Q(project__members__profile=user_profile)
        
        queryset = ProjectMonitoring.objects.filter(
            owned_projects | member_projects
        ).select_related('project', 'project__owner_profile__user').distinct()
        
        # Apply filters
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        
        analysis_type = self.request.query_params.get('analysis_type')
        if analysis_type:
            queryset = queryset.filter(analysis_type=analysis_type)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Date range filtering
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            try:
                date_from = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                queryset = queryset.filter(created_at__gte=date_from)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                queryset = queryset.filter(created_at__lte=date_to)
            except ValueError:
                pass
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def project_history(self, request):
        """
        Get complete analysis history for a specific project.
        
        Query params:
        - project_id: Required project ID
        - analysis_type: Filter by analysis type (stc, mc_stc)
        - date_from: Start date (ISO format)
        - date_to: End date (ISO format)
        - limit: Number of records to return (default: 50)
        """
        try:
            project_id = request.query_params.get('project_id')
            if not project_id:
                return ApiResponse.validation_error(
                    error_message="project_id parameter is required",
                    error_code="MISSING_PROJECT_ID"
                )
            
            # Check project access
            user_profile = request.user.profile
            try:
                project = Project.objects.get(
                    id=project_id,
                    deleted_at__isnull=True
                )
                
                # Check if user has access to this project
                has_access = (
                    project.owner_profile == user_profile or
                    ProjectMember.objects.filter(
                        project=project,
                        profile=user_profile
                    ).exists()
                )
                
                if not has_access:
                    return ApiResponse.forbidden(
                        error_message="You don't have access to this project",
                        error_code="PROJECT_ACCESS_DENIED"
                    )
                    
            except Project.DoesNotExist:
                return ApiResponse.not_found(
                    error_message="Project not found",
                    error_code="PROJECT_NOT_FOUND"
                )
            
            # Build queryset
            queryset = ProjectMonitoring.objects.filter(project=project)
            
            # Apply filters
            analysis_type = request.query_params.get('analysis_type')
            if analysis_type:
                queryset = queryset.filter(analysis_type=analysis_type)
            
            # Date range filtering
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')
            
            if date_from:
                try:
                    date_from = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                    queryset = queryset.filter(created_at__gte=date_from)
                except ValueError:
                    pass
            
            if date_to:
                try:
                    date_to = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                    queryset = queryset.filter(created_at__lte=date_to)
                except ValueError:
                    pass
            
            # Limit results
            limit = int(request.query_params.get('limit', 50))
            queryset = queryset.order_by('-created_at')[:limit]
            
            # Serialize data
            from .serializers import ProjectMonitoringListSerializer
            serializer = ProjectMonitoringListSerializer(queryset, many=True)
            
            # Calculate summary statistics
            completed_analyses = queryset.filter(status='completed')
            avg_stc = completed_analyses.aggregate(Avg('stc_value'))['stc_value__avg']
            avg_risk = completed_analyses.aggregate(Avg('risk_score'))['risk_score__avg']
            
            return ApiResponse.success(
                data={
                    'project_id': project_id,
                    'project_name': project.name,
                    'total_analyses': queryset.count(),
                    'completed_analyses': completed_analyses.count(),
                    'average_stc_value': round(avg_stc, 3) if avg_stc else None,
                    'average_risk_score': round(avg_risk, 3) if avg_risk else None,
                    'analyses': serializer.data
                },
                message=f"Retrieved {queryset.count()} analysis records"
            )
            
        except Exception as e:
            logger.error(f"Failed to get project history: {e}", exc_info=True)
            return ApiResponse.internal_error(
                error_message="Failed to retrieve project history",
                error_code="PROJECT_HISTORY_ERROR"
            )
    
    @action(detail=False, methods=['get'])
    def trend_analysis(self, request):
        """
        Get trend analysis for a project's STC/MC-STC values over time.
        
        Query params:
        - project_id: Required project ID
        - analysis_type: Filter by analysis type (stc, mc_stc)
        - period: Time period (7d, 30d, 90d, 1y) - default: 30d
        - metric: Metric to analyze (stc_value, risk_score, coordination_efficiency)
        """
        try:
            project_id = request.query_params.get('project_id')
            if not project_id:
                return ApiResponse.validation_error(
                    error_message="project_id parameter is required",
                    error_code="MISSING_PROJECT_ID"
                )
            
            # Check project access (reuse logic from project_history)
            user_profile = request.user.profile
            try:
                project = Project.objects.get(
                    id=project_id,
                    deleted_at__isnull=True
                )
                
                has_access = (
                    project.owner_profile == user_profile or
                    ProjectMember.objects.filter(
                        project=project,
                        profile=user_profile
                    ).exists()
                )
                
                if not has_access:
                    return ApiResponse.forbidden(
                        error_message="You don't have access to this project",
                        error_code="PROJECT_ACCESS_DENIED"
                    )
                    
            except Project.DoesNotExist:
                return ApiResponse.not_found(
                    error_message="Project not found",
                    error_code="PROJECT_NOT_FOUND"
                )
            
            # Parse parameters
            analysis_type = request.query_params.get('analysis_type', 'mc_stc')
            period = request.query_params.get('period', '30d')
            metric = request.query_params.get('metric', 'stc_value')
            
            # Calculate date range
            now = timezone.now()
            if period == '7d':
                date_from = now - timedelta(days=7)
            elif period == '30d':
                date_from = now - timedelta(days=30)
            elif period == '90d':
                date_from = now - timedelta(days=90)
            elif period == '1y':
                date_from = now - timedelta(days=365)
            else:
                date_from = now - timedelta(days=30)  # default
            
            # Get trend data
            queryset = ProjectMonitoring.objects.filter(
                project=project,
                analysis_type=analysis_type,
                status='completed',
                completed_at__gte=date_from,
                completed_at__isnull=False
            ).order_by('completed_at')
            
            # Prepare trend data
            trend_data = []
            for record in queryset:
                if metric == 'stc_value':
                    value = record.stc_value
                elif metric == 'risk_score':
                    value = record.risk_score
                elif metric == 'coordination_efficiency':
                    value = record.coordination_efficiency
                else:
                    value = record.stc_value
                
                trend_data.append({
                    'date': record.completed_at.isoformat(),
                    'value': value,
                    'analysis_id': str(record.id)
                })
            
            # Calculate statistics
            values = [item['value'] for item in trend_data if item['value'] is not None]
            if values:
                avg_value = sum(values) / len(values)
                min_value = min(values)
                max_value = max(values)
                
                # Calculate trend (simple linear regression slope)
                if len(values) > 1:
                    x_values = list(range(len(values)))
                    n = len(values)
                    sum_x = sum(x_values)
                    sum_y = sum(values)
                    sum_xy = sum(x * y for x, y in zip(x_values, values))
                    sum_x2 = sum(x * x for x in x_values)
                    
                    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                    trend_direction = 'improving' if slope > 0.01 else 'declining' if slope < -0.01 else 'stable'
                else:
                    slope = 0
                    trend_direction = 'insufficient_data'
            else:
                avg_value = min_value = max_value = slope = None
                trend_direction = 'no_data'
            
            return ApiResponse.success(
                data={
                    'project_id': project_id,
                    'project_name': project.name,
                    'analysis_type': analysis_type,
                    'metric': metric,
                    'period': period,
                    'date_from': date_from.isoformat(),
                    'date_to': now.isoformat(),
                    'data_points': len(trend_data),
                    'trend_data': trend_data,
                    'statistics': {
                        'average': round(avg_value, 3) if avg_value is not None else None,
                        'minimum': round(min_value, 3) if min_value is not None else None,
                        'maximum': round(max_value, 3) if max_value is not None else None,
                        'trend_slope': round(slope, 4) if slope is not None else None,
                        'trend_direction': trend_direction
                    }
                },
                message=f"Retrieved trend analysis for {len(trend_data)} data points"
            )
            
        except Exception as e:
            logger.error(f"Failed to get trend analysis: {e}", exc_info=True)
            return ApiResponse.internal_error(
                error_message="Failed to retrieve trend analysis",
                error_code="TREND_ANALYSIS_ERROR"
            )
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ProjectMonitoringListSerializer
        return ProjectMonitoringSerializer
    
    def list(self, request, *args, **kwargs):
        """List monitoring records with enhanced response."""
        try:
            queryset = self.get_queryset()
            page = self.paginate_queryset(queryset)
            
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(queryset, many=True)
            return ApiResponse.success(
                data=serializer.data,
                message=f"Retrieved {len(serializer.data)} monitoring records"
            )
        except Exception as e:
            logger.error(f"Failed to list monitoring records: {e}", exc_info=True)
            return ApiResponse.internal_error(
                error_message="Failed to retrieve monitoring records",
                error_code="MONITORING_LIST_ERROR"
            )
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single monitoring record."""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return ApiResponse.success(
                data=serializer.data,
                message="Monitoring record retrieved successfully"
            )
        except Exception as e:
            logger.error(f"Failed to retrieve monitoring record: {e}", exc_info=True)
            return ApiResponse.internal_error(
                error_message="Failed to retrieve monitoring record",
                error_code="MONITORING_RETRIEVE_ERROR"
            )
    
    @action(detail=False, methods=['get'])
    def project_stats(self, request):
        """
        Get monitoring statistics for all accessible projects.
        
        Returns aggregated statistics for each project the user has access to.
        """
        try:
            user_profile = request.user.profile
            
            # Get projects user has access to
            owned_projects = Q(owner_profile=user_profile)
            member_projects = Q(members__profile=user_profile)
            
            projects = Project.objects.filter(
                (owned_projects | member_projects) & Q(deleted_at__isnull=True)
            ).distinct()
            
            stats_data = []
            
            for project in projects:
                # Get monitoring records for this project
                monitoring_records = ProjectMonitoring.objects.filter(project=project)
                
                if not monitoring_records.exists():
                    continue
                
                # Calculate statistics
                total_analyses = monitoring_records.count()
                completed_analyses = monitoring_records.filter(status=AnalysisStatus.COMPLETED).count()
                failed_analyses = monitoring_records.filter(status=AnalysisStatus.FAILED).count()
                
                # Get latest and average values
                completed_records = monitoring_records.filter(
                    status=AnalysisStatus.COMPLETED,
                    stc_value__isnull=False
                )
                
                latest_record = completed_records.order_by('-completed_at').first()
                
                latest_stc_value = latest_record.stc_value if latest_record else None
                latest_risk_score = latest_record.risk_score if latest_record else None
                
                # Calculate averages
                avg_stats = completed_records.aggregate(
                    avg_stc=Avg('stc_value'),
                    avg_risk=Avg('risk_score')
                )
                
                # Determine trend (compare last 2 records)
                recent_records = completed_records.order_by('-completed_at')[:2]
                trend_direction = 'stable'
                
                if len(recent_records) >= 2:
                    latest_stc = recent_records[0].stc_value or 0
                    previous_stc = recent_records[1].stc_value or 0
                    
                    if latest_stc > previous_stc + 0.05:  # 5% improvement
                        trend_direction = 'improving'
                    elif latest_stc < previous_stc - 0.05:  # 5% decline
                        trend_direction = 'declining'
                
                stats_data.append({
                    'project_id': project.id,
                    'project_name': project.name,
                    'total_analyses': total_analyses,
                    'completed_analyses': completed_analyses,
                    'failed_analyses': failed_analyses,
                    'latest_stc_value': latest_stc_value,
                    'latest_risk_score': latest_risk_score,
                    'avg_stc_value': avg_stats['avg_stc'],
                    'avg_risk_score': avg_stats['avg_risk'],
                    'trend_direction': trend_direction,
                    'last_analysis_date': latest_record.completed_at if latest_record else None
                })
            
            serializer = ProjectMonitoringStatsSerializer(stats_data, many=True)
            
            return ApiResponse.success(
                data=serializer.data,
                message=f"Retrieved statistics for {len(stats_data)} projects"
            )
            
        except Exception as e:
            logger.error(f"Failed to get project stats: {e}", exc_info=True)
            return ApiResponse.internal_error(
                error_message="Failed to retrieve project statistics",
                error_code="PROJECT_STATS_ERROR"
            )
    
    @action(detail=False, methods=['get'])
    def project_trends(self, request):
        """
        Get trend data for a specific project.
        
        Query params:
        - project_id: Required project ID
        - days: Number of days to look back (default: 30)
        """
        try:
            project_id = request.query_params.get('project_id')
            if not project_id:
                return ApiResponse.error(
                    error_message="project_id parameter is required",
                    error_code="MISSING_PROJECT_ID"
                )
            
            days = int(request.query_params.get('days', 30))
            
            # Check project access
            user_profile = request.user.profile
            try:
                project = Project.objects.get(
                    id=project_id,
                    deleted_at__isnull=True
                )
                
                # Verify access
                if not (project.owner_profile == user_profile or 
                        project.members.filter(profile=user_profile).exists()):
                    return ApiResponse.forbidden("You don't have access to this project")
                
            except Project.DoesNotExist:
                return ApiResponse.not_found("Project not found")
            
            # Get trend data
            start_date = timezone.now() - timedelta(days=days)
            
            monitoring_records = ProjectMonitoring.objects.filter(
                project=project,
                status=AnalysisStatus.COMPLETED,
                completed_at__gte=start_date,
                stc_value__isnull=False
            ).order_by('completed_at')
            
            trend_data = []
            for record in monitoring_records:
                trend_data.append({
                    'date': record.completed_at.date(),
                    'stc_value': record.stc_value,
                    'risk_score': record.risk_score,
                    'coordination_efficiency': record.coordination_efficiency,
                    'total_contributors': record.total_contributors
                })
            
            serializer = ProjectMonitoringTrendSerializer(trend_data, many=True)
            
            return ApiResponse.success(
                data={
                    'project_id': project_id,
                    'project_name': project.name,
                    'trend_data': serializer.data,
                    'period_days': days
                },
                message=f"Retrieved trend data for {len(trend_data)} analysis points"
            )
            
        except Exception as e:
            logger.error(f"Failed to get project trends: {e}", exc_info=True)
            return ApiResponse.internal_error(
                error_message="Failed to retrieve project trends",
                error_code="PROJECT_TRENDS_ERROR"
            )
    
    @action(detail=False, methods=['get'])
    def top_coordination_pairs(self, request):
        """
        Get top coordination pairs for a specific project's latest MC-STC analysis.
        
        Query params:
        - project_id: Required project ID
        - analysis_id: Optional specific analysis ID (uses latest if not provided)
        - top_n: Number of top pairs to return (default: 10)
        """
        try:
            project_id = request.query_params.get('project_id')
            if not project_id:
                return ApiResponse.error(
                    error_message="project_id parameter is required",
                    error_code="MISSING_PROJECT_ID"
                )
            
            analysis_id = request.query_params.get('analysis_id')
            top_n = int(request.query_params.get('top_n', 10))
            
            # Check project access
            user_profile = request.user.profile
            try:
                project = Project.objects.get(
                    id=project_id,
                    deleted_at__isnull=True
                )
                
                # Verify access
                if not (project.owner_profile == user_profile or 
                        project.members.filter(profile=user_profile).exists()):
                    return ApiResponse.forbidden("You don't have access to this project")
                
            except Project.DoesNotExist:
                return ApiResponse.not_found("Project not found")
            
            # Get monitoring record
            if analysis_id:
                try:
                    monitoring = ProjectMonitoring.objects.get(
                        id=analysis_id,
                        project=project,
                        status=AnalysisStatus.COMPLETED
                    )
                except ProjectMonitoring.DoesNotExist:
                    return ApiResponse.not_found("Analysis not found")
            else:
                # Get latest completed MC-STC analysis
                monitoring = ProjectMonitoring.objects.filter(
                    project=project,
                    analysis_type=AnalysisType.MC_STC,
                    status=AnalysisStatus.COMPLETED,
                    top_coordination_pairs__isnull=False
                ).order_by('-completed_at').first()
                
                if not monitoring:
                    return ApiResponse.not_found(
                        "No completed MC-STC analysis found for this project"
                    )
            
            # Get coordination pairs directly from MC-STC table
            coordination_pairs_queryset = monitoring.get_mcstc_coordination_pairs(
                top_n=top_n,
                role_filter=request.query_params.get('role_filter'),
                status_filter=request.query_params.get('status_filter'),
                inter_class_only=request.query_params.get('inter_class_only', '').lower() == 'true'
            )
            
            if coordination_pairs_queryset is not None:
                # Use MC-STC table data (preferred)
                from mcstc_analysis.serializers import MCSTCCoordinationPairSerializer
                serializer = MCSTCCoordinationPairSerializer(coordination_pairs_queryset, many=True)
                coordination_pairs = serializer.data
            else:
                # Fallback to JSON field data
                coordination_pairs = monitoring.top_coordination_pairs or []
                if len(coordination_pairs) > top_n:
                    coordination_pairs = coordination_pairs[:top_n]
            
            return ApiResponse.success(
                data={
                    'project_id': project_id,
                    'project_name': project.name,
                    'analysis_id': monitoring.id,
                    'analysis_date': monitoring.completed_at,
                    'stc_value': monitoring.stc_value,
                    'total_pairs': len(coordination_pairs),
                    'coordination_pairs': coordination_pairs
                },
                message=f"Retrieved top {len(coordination_pairs)} coordination pairs"
            )
            
        except Exception as e:
            logger.error(f"Failed to get top coordination pairs: {e}", exc_info=True)
            return ApiResponse.internal_error(
                error_message="Failed to retrieve coordination pairs",
                error_code="COORDINATION_PAIRS_ERROR"
            )


class ProjectMonitoringSubscriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing project monitoring subscriptions."""
    
    serializer_class = ProjectMonitoringSubscriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get subscriptions for the current user."""
        return ProjectMonitoringSubscription.objects.filter(
            user_profile=self.request.user.profile
        ).select_related('project', 'user_profile__user')
    
    def perform_create(self, serializer):
        """Create subscription for current user."""
        serializer.save(user_profile=self.request.user.profile)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_monitoring_analysis(request):
    """
    Create a new monitoring analysis for a project.
    
    POST /api/project-monitoring/create-analysis/
    Body: {
        "project_id": "uuid",
        "analysis_type": "stc" | "mc_stc",
        "branch": "main",  // optional
        "force_rerun": false  // optional
    }
    """
    try:
        serializer = CreateMonitoringAnalysisSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return ApiResponse.error(
                error_message="Invalid request data",
                error_code="VALIDATION_ERROR",
                status_code=status.HTTP_400_BAD_REQUEST,
                data=serializer.errors
            )
        
        data = serializer.validated_data
        project = Project.objects.get(id=data['project_id'])
        
        # Cancel existing running analyses if force_rerun is True
        if data.get('force_rerun', False):
            ProjectMonitoring.objects.filter(
                project=project,
                analysis_type=data['analysis_type'],
                status__in=[AnalysisStatus.PENDING, AnalysisStatus.RUNNING]
            ).update(
                status=AnalysisStatus.FAILED,
                error_message="Cancelled by force rerun",
                completed_at=timezone.now()
            )
        
        # Create new monitoring record
        monitoring = ProjectMonitoring.objects.create(
            project=project,
            analysis_type=data['analysis_type'],
            branch_analyzed=data.get('branch', 'main'),
            status=AnalysisStatus.PENDING
        )
        
        # TODO: Trigger actual analysis (integrate with STC analysis service)
        # For now, we just create the record
        
        logger.info(f"Created monitoring analysis {monitoring.id} for project {project.name}")
        
        serializer = ProjectMonitoringSerializer(monitoring)
        return ApiResponse.success(
            data=serializer.data,
            message="Monitoring analysis created successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to create monitoring analysis: {e}", exc_info=True)
        return ApiResponse.internal_error(
            error_message="Failed to create monitoring analysis",
            error_code="CREATE_ANALYSIS_ERROR"
        )


