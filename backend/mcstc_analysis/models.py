from django.db import models
from django.conf import settings
import uuid


class MCSTCAnalysis(models.Model):
    """Model for storing MC-STC (Multi-Class Socio-Technical Congruence) analysis results"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='mcstc_analyses')
    analysis_date = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)
    
    # MC-STC specific configuration
    monte_carlo_iterations = models.IntegerField(default=1000)
    functional_roles_used = models.JSONField(
        default=list, 
        help_text="List of functional roles used in this analysis"
    )
    
    # Legacy field for backward compatibility (results now stored in database fields)
    results_file = models.CharField(max_length=255, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    
    # MC-STC specific metrics
    mcstc_value = models.FloatField(
        null=True, 
        blank=True,
        help_text="MC-STC value (0-1, higher means better multi-class coordination)"
    )
    inter_class_coordination_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Inter-class coordination score"
    )
    intra_class_coordination_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Intra-class coordination score"
    )
    
    # Role-specific metrics
    developer_security_coordination = models.FloatField(
        null=True,
        blank=True,
        help_text="Coordination score between developers and security team"
    )
    developer_ops_coordination = models.FloatField(
        null=True,
        blank=True,
        help_text="Coordination score between developers and ops team"
    )
    security_ops_coordination = models.FloatField(
        null=True,
        blank=True,
        help_text="Coordination score between security and ops team"
    )
    
    # Top coordination pairs
    top_coordination_pairs = models.JSONField(
        default=list,
        blank=True,
        help_text="Top coordination pairs with highest MC-STC impact"
    )
    
    # Analysis metadata
    branch_analyzed = models.CharField(
        max_length=100,
        blank=True,
        help_text="Git branch analyzed"
    )
    total_contributors_analyzed = models.IntegerField(
        default=0,
        help_text="Total number of contributors included in analysis"
    )
    developer_count = models.IntegerField(
        default=0,
        help_text="Number of developers in analysis"
    )
    security_count = models.IntegerField(
        default=0,
        help_text="Number of security personnel in analysis"
    )
    ops_count = models.IntegerField(
        default=0,
        help_text="Number of ops personnel in analysis"
    )

    class Meta:
        app_label = 'mcstc_analysis'
        ordering = ['-analysis_date']
        verbose_name = "MC-STC Analysis"
        verbose_name_plural = "MC-STC Analyses"
    
    def __str__(self):
        return f"MC-STC Analysis for {self.project.name} ({self.analysis_date.strftime('%Y-%m-%d')})"


class MCSTCCoordinationPair(models.Model):
    """Model for storing detailed coordination pair information from MC-STC analysis"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analysis = models.ForeignKey(MCSTCAnalysis, on_delete=models.CASCADE, related_name='coordination_pairs')
    
    # Contributor information
    contributor1_id = models.CharField(max_length=100, help_text="First contributor identifier")
    contributor1_role = models.CharField(max_length=20, help_text="First contributor's functional role")
    contributor1_email = models.EmailField(blank=True, help_text="First contributor's email")
    
    contributor2_id = models.CharField(max_length=100, help_text="Second contributor identifier")
    contributor2_role = models.CharField(max_length=20, help_text="Second contributor's functional role")
    contributor2_email = models.EmailField(blank=True, help_text="Second contributor's email")
    
    # Coordination metrics
    coordination_requirement = models.FloatField(
        help_text="Coordination requirement strength (0-1)"
    )
    actual_coordination = models.FloatField(
        help_text="Actual coordination observed (0-1)"
    )
    coordination_gap = models.FloatField(
        help_text="Gap between required and actual coordination"
    )
    impact_score = models.FloatField(
        help_text="Impact score on overall MC-STC"
    )
    
    # Classification
    is_inter_class = models.BooleanField(
        default=False,
        help_text="Whether this is inter-class coordination (different roles)"
    )
    is_missed_coordination = models.BooleanField(
        default=False,
        help_text="Whether this represents missed coordination"
    )
    is_unnecessary_coordination = models.BooleanField(
        default=False,
        help_text="Whether this represents unnecessary coordination"
    )
    
    # File-level details
    shared_files = models.JSONField(
        default=list,
        help_text="List of files both contributors work on"
    )
    coordination_files = models.JSONField(
        default=list,
        help_text="Files where coordination is most critical"
    )

    class Meta:
        app_label = 'mcstc_analysis'
        ordering = ['-impact_score']
        unique_together = ['analysis', 'contributor1_id', 'contributor2_id']
        verbose_name = "MC-STC Coordination Pair"
        verbose_name_plural = "MC-STC Coordination Pairs"
    
    def __str__(self):
        return f"{self.contributor1_id} <-> {self.contributor2_id} (Impact: {self.impact_score:.2f})"
