"""
Simple tests for Project Monitoring module.
"""

from django.test import TestCase
from accounts.models import User, UserProfile
from projects.models import Project
from .models import ProjectMonitoring, AnalysisType, AnalysisStatus


class ProjectMonitoringSimpleTests(TestCase):
    """Simple test cases for ProjectMonitoring model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user_profile = UserProfile.objects.create(user=self.user)
        
        self.project = Project.objects.create(
            name='Test Project',
            repo_url='https://github.com/test/repo',
            owner_profile=self.user_profile
        )
    
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
