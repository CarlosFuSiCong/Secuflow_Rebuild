"""
Project Monitoring URLs

URL configuration for project monitoring API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for viewsets
router = DefaultRouter()
router.register(r'monitoring', views.ProjectMonitoringViewSet, basename='monitoring')
router.register(r'subscriptions', views.ProjectMonitoringSubscriptionViewSet, basename='subscriptions')

app_name = 'project_monitoring'

urlpatterns = [
    # ViewSet routes
    path('', include(router.urls)),
    
    # Function-based view routes
    path('create-analysis/', views.create_monitoring_analysis, name='create-analysis'),
]
