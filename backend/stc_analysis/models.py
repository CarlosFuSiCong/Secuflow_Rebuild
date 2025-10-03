from django.db import models
from django.conf import settings

class STCAnalysis(models.Model):
    """Model for storing STC analysis results"""
    
    
    
    
    
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='stc_analyses')
    analysis_date = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)
    
    # Analysis configuration
    use_monte_carlo = models.BooleanField(default=False)
    monte_carlo_iterations = models.IntegerField(default=1000)
    
    # Analysis results storage
    results_file = models.CharField(max_length=255, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-analysis_date']
    
    def __str__(self):
        return f"STC Analysis for {self.project.name} ({self.analysis_date.strftime('%Y-%m-%d')})"