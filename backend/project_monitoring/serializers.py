"""
Project Monitoring Serializers

This module provides serializers for project monitoring API endpoints.
"""

from rest_framework import serializers
from django.utils import timezone
from .models import ProjectMonitoring, ProjectMonitoringSubscription, AnalysisType
from projects.models import Project


class ProjectMonitoringSerializer(serializers.ModelSerializer):
    """Serializer for ProjectMonitoring model."""
    
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_owner = serializers.CharField(source='project.owner_profile.user.username', read_only=True)
    analysis_type_display = serializers.CharField(source='get_analysis_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration_seconds = serializers.SerializerMethodField()
    coordination_efficiency = serializers.ReadOnlyField()
    
    class Meta:
        model = ProjectMonitoring
        fields = [
            'id', 'project', 'project_name', 'project_owner',
            'analysis_type', 'analysis_type_display', 'status', 'status_display',
            'stc_value', 'risk_score', 'coordination_efficiency',
            'total_required_edges', 'satisfied_edges', 
            'missed_coordination_count', 'unnecessary_coordination_count',
            'total_contributors', 'developer_count', 'security_count', 'ops_count',
            'branch_analyzed', 'top_coordination_pairs', 'created_at', 'started_at', 'completed_at',
            'duration_seconds', 'error_message'
        ]
        read_only_fields = [
            'id', 'project_name', 'project_owner', 'analysis_type_display', 
            'status_display', 'coordination_efficiency', 'duration_seconds',
            'created_at', 'started_at', 'completed_at'
        ]
    
    def get_duration_seconds(self, obj):
        """Get analysis duration in seconds."""
        if obj.duration:
            return obj.duration.total_seconds()
        return None


class ProjectMonitoringListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing project monitoring records."""
    
    project_name = serializers.CharField(source='project.name', read_only=True)
    analysis_type_display = serializers.CharField(source='get_analysis_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    coordination_efficiency = serializers.ReadOnlyField()
    
    class Meta:
        model = ProjectMonitoring
        fields = [
            'id', 'project', 'project_name', 'analysis_type', 'analysis_type_display',
            'status', 'status_display', 'stc_value', 'risk_score', 
            'coordination_efficiency', 'total_contributors', 'created_at', 'completed_at'
        ]


class ProjectMonitoringStatsSerializer(serializers.Serializer):
    """Serializer for project monitoring statistics."""
    
    project_id = serializers.UUIDField()
    project_name = serializers.CharField()
    total_analyses = serializers.IntegerField()
    completed_analyses = serializers.IntegerField()
    failed_analyses = serializers.IntegerField()
    latest_stc_value = serializers.FloatField(allow_null=True)
    latest_risk_score = serializers.FloatField(allow_null=True)
    avg_stc_value = serializers.FloatField(allow_null=True)
    avg_risk_score = serializers.FloatField(allow_null=True)
    trend_direction = serializers.CharField()  # 'improving', 'declining', 'stable'
    last_analysis_date = serializers.DateTimeField(allow_null=True)


class ProjectMonitoringTrendSerializer(serializers.Serializer):
    """Serializer for project monitoring trend data."""
    
    date = serializers.DateField()
    stc_value = serializers.FloatField(allow_null=True)
    risk_score = serializers.FloatField(allow_null=True)
    coordination_efficiency = serializers.FloatField(allow_null=True)
    total_contributors = serializers.IntegerField()


class ProjectMonitoringSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for ProjectMonitoringSubscription model."""
    
    project_name = serializers.CharField(source='project.name', read_only=True)
    user_name = serializers.CharField(source='user_profile.user.username', read_only=True)
    
    class Meta:
        model = ProjectMonitoringSubscription
        fields = [
            'id', 'project', 'project_name', 'user_name',
            'notify_on_completion', 'notify_on_risk_increase', 'notify_on_coordination_drop',
            'risk_threshold', 'coordination_threshold',
            'created_at', 'updated_at', 'last_notification_at'
        ]
        read_only_fields = ['id', 'project_name', 'user_name', 'created_at', 'updated_at']


class CreateMonitoringAnalysisSerializer(serializers.Serializer):
    """Serializer for creating new monitoring analysis."""
    
    project_id = serializers.UUIDField()
    analysis_type = serializers.ChoiceField(choices=AnalysisType.choices)
    branch = serializers.CharField(max_length=100, required=False, default='main')
    force_rerun = serializers.BooleanField(default=False)
    
    def validate_project_id(self, value):
        """Validate that project exists and user has access."""
        try:
            project = Project.objects.get(id=value, deleted_at__isnull=True)
        except Project.DoesNotExist:
            raise serializers.ValidationError("Project not found or has been deleted.")
        
        # Check if user has access to this project
        user_profile = self.context['request'].user.profile
        if not (project.owner_profile == user_profile or 
                project.members.filter(profile=user_profile).exists()):
            raise serializers.ValidationError("You don't have access to this project.")
        
        return value
    
    def validate(self, data):
        """Validate that analysis is not already running."""
        if not data.get('force_rerun', False):
            # Check for existing running analysis
            existing = ProjectMonitoring.objects.filter(
                project_id=data['project_id'],
                analysis_type=data['analysis_type'],
                status__in=['pending', 'running']
            ).exists()
            
            if existing:
                raise serializers.ValidationError(
                    "Analysis is already running for this project. Use force_rerun=true to override."
                )
        
        return data


class ProjectAccessSerializer(serializers.Serializer):
    """Serializer for checking project access."""
    
    project_id = serializers.UUIDField()
    has_access = serializers.BooleanField()
    role = serializers.CharField(allow_null=True)
    is_owner = serializers.BooleanField()
    is_member = serializers.BooleanField()
