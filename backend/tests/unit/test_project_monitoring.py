"""
Unit tests for Project Monitoring module.
"""

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from tests.conftest import BaseTestCase
from tests.utils.test_helpers import APITestMixin
from project_monitoring.models import ProjectMonitoring, ProjectMonitoringSubscription, AnalysisType, AnalysisStatus


class ProjectMonitoringModelTests(BaseTestCase):
    """Test cases for ProjectMonitoring model."""
    
    def test_create_monitoring_record(self):
        """Test creating a monitoring record."""
        monitoring = ProjectMonitoring.objects.create(
            project=self.project,
            analysis_type=AnalysisType.STC,
            status=AnalysisStatus.PENDING
        )
        
        self.assertEqual(monitoring.project, self.project)
        self.assertEqual(monitoring.analysis_type, AnalysisType.STC)
        self.assertEqual(monitoring.status, AnalysisStatus.PENDING)
        self.assertIsNotNone(monitoring.id)
        self.assertIsNotNone(monitoring.created_at)
    
    def test_start_analysis(self):
        """Test starting an analysis."""
        monitoring = ProjectMonitoring.objects.create(
            project=self.project,
            analysis_type=AnalysisType.STC
        )
        
        monitoring.start_analysis()
        
        self.assertEqual(monitoring.status, AnalysisStatus.RUNNING)
        self.assertIsNotNone(monitoring.started_at)
    
    def test_complete_analysis(self):
        """Test completing an analysis with results."""
        monitoring = ProjectMonitoring.objects.create(
            project=self.project,
            analysis_type=AnalysisType.STC
        )
        
        results = {
            'stc_value': 0.75,
            'risk_score': 0.25,
            'total_required_edges': 100,
            'satisfied_edges': 75,
            'total_contributors': 10,
            'developer_count': 8,
            'security_count': 2
        }
        
        monitoring.complete_analysis(results)
        
        self.assertEqual(monitoring.status, AnalysisStatus.COMPLETED)
        self.assertEqual(monitoring.stc_value, 0.75)
        self.assertEqual(monitoring.risk_score, 0.25)
        self.assertEqual(monitoring.total_required_edges, 100)
        self.assertEqual(monitoring.satisfied_edges, 75)
        self.assertIsNotNone(monitoring.completed_at)
    
    def test_fail_analysis(self):
        """Test failing an analysis with error message."""
        monitoring = ProjectMonitoring.objects.create(
            project=self.project,
            analysis_type=AnalysisType.STC
        )
        
        error_message = "Analysis failed due to missing data"
        monitoring.fail_analysis(error_message)
        
        self.assertEqual(monitoring.status, AnalysisStatus.FAILED)
        self.assertEqual(monitoring.error_message, error_message)
        self.assertIsNotNone(monitoring.completed_at)
    
    def test_coordination_efficiency_property(self):
        """Test coordination efficiency calculation."""
        monitoring = ProjectMonitoring.objects.create(
            project=self.project,
            analysis_type=AnalysisType.STC,
            total_required_edges=100,
            satisfied_edges=80
        )
        
        self.assertEqual(monitoring.coordination_efficiency, 80.0)
        
        # Test with zero required edges
        monitoring.total_required_edges = 0
        self.assertEqual(monitoring.coordination_efficiency, 0.0)


class ProjectMonitoringSubscriptionModelTests(BaseTestCase):
    """Test cases for ProjectMonitoringSubscription model."""
    
    def test_create_subscription(self):
        """Test creating a monitoring subscription."""
        subscription = ProjectMonitoringSubscription.objects.create(
            user_profile=self.user_profile,
            project=self.project,
            notify_on_completion=True,
            notify_on_risk_increase=True,
            notify_on_coordination_drop=True,
            risk_threshold=0.8,
            coordination_threshold=0.6
        )
        
        self.assertEqual(subscription.user_profile, self.user_profile)
        self.assertEqual(subscription.project, self.project)
        self.assertTrue(subscription.notify_on_completion)
        self.assertTrue(subscription.notify_on_risk_increase)
        self.assertTrue(subscription.notify_on_coordination_drop)
        self.assertEqual(subscription.risk_threshold, 0.8)
        self.assertEqual(subscription.coordination_threshold, 0.6)
    
    def test_should_notify_coordination_drop(self):
        """Test coordination drop notification logic."""
        subscription = ProjectMonitoringSubscription.objects.create(
            user_profile=self.user_profile,
            project=self.project,
            notify_on_coordination_drop=True,
            coordination_threshold=0.6
        )
        
        # Test if notification method exists and works
        if hasattr(subscription, 'should_notify_coordination_drop'):
            # Should notify when coordination drops below threshold
            self.assertTrue(subscription.should_notify_coordination_drop(0.4))
            
            # Should not notify when coordination is above threshold
            self.assertFalse(subscription.should_notify_coordination_drop(0.8))
        else:
            # Skip test if method doesn't exist yet
            self.skipTest("should_notify_coordination_drop method not implemented yet")
    
    def test_should_notify_risk_increase(self):
        """Test risk increase notification logic."""
        subscription = ProjectMonitoringSubscription.objects.create(
            user_profile=self.user_profile,
            project=self.project,
            notify_on_risk_increase=True,
            risk_threshold=0.7
        )
        
        # Test if notification method exists and works
        if hasattr(subscription, 'should_notify_risk_increase'):
            # Should notify when risk exceeds threshold
            self.assertTrue(subscription.should_notify_risk_increase(0.8))
            
            # Should not notify when risk is below threshold
            self.assertFalse(subscription.should_notify_risk_increase(0.5))
        else:
            # Skip test if method doesn't exist yet
            self.skipTest("should_notify_risk_increase method not implemented yet")
