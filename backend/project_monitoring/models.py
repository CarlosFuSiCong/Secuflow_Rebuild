"""
Project Monitoring Models

This module defines models for tracking STC and MC-STC analysis results over time.
"""

import uuid
from django.db import models
from django.utils import timezone
from projects.models import Project
from accounts.models import UserProfile


class AnalysisType(models.TextChoices):
    """Analysis type choices."""
    STC = 'stc', 'STC (Socio-Technical Congruence)'
    MC_STC = 'mc_stc', 'MC-STC (Multi-Class STC)'


class AnalysisStatus(models.TextChoices):
    """Analysis status choices."""
    PENDING = 'pending', 'Pending'
    RUNNING = 'running', 'Running'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'


class ProjectMonitoring(models.Model):
    """
    Model for tracking periodic STC/MC-STC analysis results for projects.
    
    This model stores historical analysis data to help project owners and members
    monitor coordination health and risk trends over time.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project, 
        on_delete=models.CASCADE, 
        related_name='monitoring_records'
    )
    analysis_type = models.CharField(
        max_length=10,
        choices=AnalysisType.choices,
        help_text="Type of analysis performed"
    )
    status = models.CharField(
        max_length=10,
        choices=AnalysisStatus.choices,
        default=AnalysisStatus.PENDING,
        help_text="Current status of the analysis"
    )
    
    # Analysis Results
    stc_value = models.FloatField(
        null=True, 
        blank=True,
        help_text="STC value (0-1, higher means better coordination)"
    )
    risk_score = models.FloatField(
        null=True,
        blank=True, 
        help_text="Risk score (0-1, higher means more risky)"
    )
    
    # Coordination Metrics
    total_required_edges = models.IntegerField(
        default=0,
        help_text="Total coordination requirements"
    )
    satisfied_edges = models.IntegerField(
        default=0,
        help_text="Satisfied coordination requirements"
    )
    missed_coordination_count = models.IntegerField(
        default=0,
        help_text="Number of missed coordination opportunities"
    )
    unnecessary_coordination_count = models.IntegerField(
        default=0,
        help_text="Number of unnecessary coordination activities"
    )
    
    # Team Metrics (for MC-STC)
    total_contributors = models.IntegerField(
        default=0,
        help_text="Total number of contributors analyzed"
    )
    developer_count = models.IntegerField(
        default=0,
        help_text="Number of developers in the analysis"
    )
    security_count = models.IntegerField(
        default=0,
        help_text="Number of security team members"
    )
    ops_count = models.IntegerField(
        default=0,
        help_text="Number of ops team members"
    )
    
    # Analysis Metadata
    branch_analyzed = models.CharField(
        max_length=100,
        blank=True,
        help_text="Git branch analyzed"
    )
    tnm_analysis_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="Related TNM analysis ID"
    )
    stc_analysis_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="Related STC analysis ID"
    )
    mcstc_analysis_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="Related MC-STC analysis ID"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Top Coordination Pairs (JSON field)
    top_coordination_pairs = models.JSONField(
        default=list,
        blank=True,
        help_text="Top 10 coordination pairs with highest MC-STC impact"
    )
    
    # Error Information
    error_message = models.TextField(
        blank=True,
        help_text="Error message if analysis failed"
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['project', 'analysis_type']),
            models.Index(fields=['project', 'created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['stc_value']),
            models.Index(fields=['risk_score']),
            models.Index(fields=['completed_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"ProjectMonitoring({self.project.name}:{self.analysis_type}:{self.created_at.date()})"
    
    def start_analysis(self):
        """Mark analysis as started."""
        self.status = AnalysisStatus.RUNNING
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])
    
    def complete_analysis(self, results: dict):
        """
        Mark analysis as completed and store results.
        
        Args:
            results: Dictionary containing analysis results
        """
        self.status = AnalysisStatus.COMPLETED
        self.completed_at = timezone.now()
        
        # Store main metrics
        self.stc_value = results.get('stc_value')
        self.risk_score = results.get('risk_score', 1.0 - (results.get('stc_value', 0)))
        
        # Store coordination metrics
        self.total_required_edges = results.get('total_required_edges', 0)
        self.satisfied_edges = results.get('satisfied_edges', 0)
        self.missed_coordination_count = results.get('missed_coordination_count', 0)
        self.unnecessary_coordination_count = results.get('unnecessary_coordination_count', 0)
        
        # Store team metrics
        self.total_contributors = results.get('total_contributors', 0)
        self.developer_count = results.get('developer_count', 0)
        self.security_count = results.get('security_count', 0)
        self.ops_count = results.get('ops_count', 0)
        
        self.save()
    
    def fail_analysis(self, error_message: str):
        """Mark analysis as failed with error message."""
        self.status = AnalysisStatus.FAILED
        self.completed_at = timezone.now()
        self.error_message = error_message
        self.save(update_fields=['status', 'completed_at', 'error_message'])
    
    @property
    def duration(self):
        """Get analysis duration if completed."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    @property
    def coordination_efficiency(self):
        """Calculate coordination efficiency percentage."""
        if self.total_required_edges > 0:
            return (self.satisfied_edges / self.total_required_edges) * 100
        return 0.0


class ProjectMonitoringSubscription(models.Model):
    """
    Model for user subscriptions to project monitoring.
    
    Users can subscribe to get notifications about their projects' analysis results.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='monitoring_subscriptions'
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='monitoring_subscriptions'
    )
    
    # Notification Preferences
    notify_on_completion = models.BooleanField(
        default=True,
        help_text="Send notification when analysis completes"
    )
    notify_on_risk_increase = models.BooleanField(
        default=True,
        help_text="Send notification when risk score increases significantly"
    )
    notify_on_coordination_drop = models.BooleanField(
        default=True,
        help_text="Send notification when coordination efficiency drops"
    )
    
    # Thresholds
    risk_threshold = models.FloatField(
        default=0.7,
        help_text="Risk score threshold for notifications (0-1)"
    )
    coordination_threshold = models.FloatField(
        default=0.5,
        help_text="Coordination efficiency threshold for notifications (0-1)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_notification_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user_profile', 'project']
        indexes = [
            models.Index(fields=['user_profile']),
            models.Index(fields=['project']),
        ]
    
    def __str__(self):
        return f"Subscription({self.user_profile.user.username}:{self.project.name})"
    
    def should_notify_risk_increase(self, new_risk_score: float) -> bool:
        """Check if user should be notified about risk increase."""
        return (self.notify_on_risk_increase and 
                new_risk_score >= self.risk_threshold)
    
    def should_notify_coordination_drop(self, coordination_efficiency: float) -> bool:
        """Check if user should be notified about coordination drop."""
        return (self.notify_on_coordination_drop and 
                coordination_efficiency <= self.coordination_threshold)
    
    def get_mcstc_coordination_pairs(self, top_n=20, **filters):
        """
        Get coordination pairs directly from MC-STC analysis table.
        
        Args:
            top_n: Number of top pairs to return
            **filters: Additional filters (role_filter, status_filter, etc.)
            
        Returns:
            QuerySet of MCSTCCoordinationPair objects
        """
        if not self.mcstc_analysis_id:
            return None
            
        from mcstc_analysis.models import MCSTCCoordinationPair
        from django.db.models import Q
        
        queryset = MCSTCCoordinationPair.objects.filter(
            analysis_id=self.mcstc_analysis_id
        )
        
        # Apply filters
        role_filter = filters.get('role_filter')
        if role_filter:
            queryset = queryset.filter(
                Q(contributor1_role=role_filter) | Q(contributor2_role=role_filter)
            )
        
        status_filter = filters.get('status_filter')
        if status_filter == 'missed':
            queryset = queryset.filter(is_missed_coordination=True)
        elif status_filter == 'unnecessary':
            queryset = queryset.filter(is_unnecessary_coordination=True)
        elif status_filter == 'adequate':
            queryset = queryset.filter(
                is_missed_coordination=False,
                is_unnecessary_coordination=False
            )
        
        inter_class_only = filters.get('inter_class_only', False)
        if inter_class_only:
            queryset = queryset.filter(is_inter_class=True)
        
        return queryset.order_by('-impact_score')[:top_n]