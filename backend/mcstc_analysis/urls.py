from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'analyses', views.MCSTCAnalysisViewSet, basename='mcstc-analysis')

urlpatterns = [
    # ViewSet routes
    path('', include(router.urls)),
    
    # Additional endpoints
    path('projects/<uuid:project_id>/comparison/', 
         views.project_mcstc_comparison, 
         name='project-mcstc-comparison'),
    
    path('analyses/<uuid:analysis_id>/coordination_pairs/', 
         views.coordination_pairs, 
         name='coordination-pairs'),
]
