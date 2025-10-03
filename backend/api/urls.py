from django.urls import include, path

urlpatterns = [
    # Authentication and user management
    path('', include('accounts.urls')),
    
    # Core functionality
    path('projects/', include('projects.urls')),
    path('tnm/', include('tnm_integration.urls')),
    
    # Analysis modules
    path('contributors/', include('contributors.urls')),
    path('stc/', include('stc_analysis.urls')),
    path('mcstc/', include('mcstc_analysis.urls')),
    path('project-monitoring/', include('project_monitoring.urls')),
]


