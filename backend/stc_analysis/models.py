from django.db import models
from django.conf import settings
import uuid

class STCAnalysis(models.Model):
    """Model for storing STC analysis results"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='stc_analyses')
    analysis_date = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)
    
    # Analysis configuration
    use_monte_carlo = models.BooleanField(default=False)
    monte_carlo_iterations = models.IntegerField(default=1000)
    
    # STC Results - stored directly in database
    stc_value = models.FloatField(
        null=True, 
        blank=True,
        help_text="STC value (0-1, higher means better coordination)"
    )
    coordination_requirements_total = models.IntegerField(
        default=0,
        help_text="Total coordination requirements"
    )
    coordination_actuals_total = models.IntegerField(
        default=0,
        help_text="Total actual coordination activities"
    )
    missed_coordination_count = models.IntegerField(
        default=0,
        help_text="Number of missed coordination opportunities"
    )
    unnecessary_coordination_count = models.IntegerField(
        default=0,
        help_text="Number of unnecessary coordination activities"
    )
    
    # Matrix dimensions
    contributors_count = models.IntegerField(
        default=0,
        help_text="Number of contributors analyzed"
    )
    files_count = models.IntegerField(
        default=0,
        help_text="Number of files analyzed"
    )
    
    # Analysis metadata
    branch_analyzed = models.CharField(
        max_length=100,
        blank=True,
        help_text="Git branch analyzed"
    )
    tnm_output_dir = models.CharField(
        max_length=500,
        blank=True,
        help_text="TNM output directory used"
    )
    
    # Legacy field for backward compatibility
    results_file = models.CharField(max_length=255, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-analysis_date']
    
    def __str__(self):
        return f"STC Analysis for {self.project.name} ({self.analysis_date.strftime('%Y-%m-%d')})"