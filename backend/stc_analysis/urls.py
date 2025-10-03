from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'analyses', views.STCAnalysisViewSet, basename='stc-analysis')

# URL patterns
urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Additional function-based views
    path('projects/<uuid:project_id>/comparison/', views.project_stc_comparison, name='project-stc-comparison'),
]
