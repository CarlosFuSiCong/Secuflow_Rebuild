from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and register viewsets
router = DefaultRouter()
# Removed contributors list endpoint per requirement
router.register(r'project-contributors', views.ProjectContributorViewSet)

# URL patterns
urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Additional function-based views
    path('projects/<int:project_id>/analysis/', views.project_contributor_analysis, name='project-contributor-analysis'),
    
    # TNM Analysis and Classification APIs
    path('projects/<uuid:project_id>/analyze_tnm/', views.analyze_tnm_contributors, name='analyze-tnm-contributors'),
    path('projects/<uuid:project_id>/classification/', views.project_contributors_classification, name='project-contributors-classification'),
    path('functional-role-choices/', views.functional_role_choices, name='functional-role-choices'),
]
