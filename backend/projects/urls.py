from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'projects', views.ProjectViewSet, basename='project')
router.register(r'members', views.ProjectMemberViewSet, basename='projectmember')

urlpatterns = [
    # Project management API routes
    path('', include(router.urls)),
    
    # TNM data cleanup endpoints
    path('cleanup-tnm-data/', views.cleanup_tnm_data, name='cleanup-tnm-data'),
    path('projects/<uuid:project_id>/cleanup-tnm/', views.cleanup_tnm_data, name='cleanup-project-tnm'),
    path('auto-cleanup-tnm/', views.auto_cleanup_tnm_data, name='auto-cleanup-tnm'),
]

