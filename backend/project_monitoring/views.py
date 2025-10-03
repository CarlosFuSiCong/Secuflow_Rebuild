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
    ProjectMonitoringSubscriptionSerializer, CreateMonitoringAnalysisSerializer,
    ProjectAccessSerializer
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
            
            # Get top coordination pairs
            coordination_pairs = monitoring.top_coordination_pairs or []
            
            # Limit to requested number
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_project_access(request, project_id):
    """
    Check if user has access to a project.
    
    GET /api/project-monitoring/check-access/{project_id}/
    """
    try:
        user_profile = request.user.profile
        
        try:
            project = Project.objects.get(id=project_id, deleted_at__isnull=True)
        except Project.DoesNotExist:
            return ApiResponse.not_found("Project not found")
        
        # Check access
        is_owner = project.owner_profile == user_profile
        is_member = project.members.filter(profile=user_profile).exists()
        has_access = is_owner or is_member
        
        # Get role if member
        role = None
        if is_owner:
            role = 'owner'
        elif is_member:
            member = project.members.filter(profile=user_profile).first()
            role = member.role if member else None
        
        data = {
            'project_id': project_id,
            'has_access': has_access,
            'role': role,
            'is_owner': is_owner,
            'is_member': is_member
        }
        
        serializer = ProjectAccessSerializer(data)
        return ApiResponse.success(
            data=serializer.data,
            message="Project access checked successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to check project access: {e}", exc_info=True)
        return ApiResponse.internal_error(
            error_message="Failed to check project access",
            error_code="CHECK_ACCESS_ERROR"
        )
