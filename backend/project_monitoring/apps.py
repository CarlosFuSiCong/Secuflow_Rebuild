from django.apps import AppConfig


class ProjectMonitoringConfig(AppConfig):
    """Configuration for the project monitoring application."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'project_monitoring'
    verbose_name = 'Project Monitoring'
    
    def ready(self):
        """Initialize the app when Django starts."""
        pass