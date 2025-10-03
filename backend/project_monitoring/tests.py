"""
Tests for Project Monitoring module.
"""

from django.test import TestCase
from accounts.models import User
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import UserProfile
from projects.models import Project, ProjectMember, ProjectRole
from .models import ProjectMonitoring, ProjectMonitoringSubscription, AnalysisType, AnalysisStatus


class ProjectMonitoringModelTests(TestCase):
    """Test cases for ProjectMonitoring model."""
    
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
        
        error_message = "TNM analysis failed"
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


class ProjectMonitoringSubscriptionModelTests(TestCase):
    """Test cases for ProjectMonitoringSubscription model."""
    
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
    
    def test_create_subscription(self):
        """Test creating a monitoring subscription."""
        subscription = ProjectMonitoringSubscription.objects.create(
            user_profile=self.user_profile,
            project=self.project
        )
        
        self.assertEqual(subscription.user_profile, self.user_profile)
        self.assertEqual(subscription.project, self.project)
        self.assertTrue(subscription.notify_on_completion)
        self.assertTrue(subscription.notify_on_risk_increase)
        self.assertEqual(subscription.risk_threshold, 0.7)
    
    def test_should_notify_risk_increase(self):
        """Test risk increase notification logic."""
        subscription = ProjectMonitoringSubscription.objects.create(
            user_profile=self.user_profile,
            project=self.project,
            risk_threshold=0.6
        )
        
        self.assertTrue(subscription.should_notify_risk_increase(0.8))
        self.assertFalse(subscription.should_notify_risk_increase(0.5))
    
    def test_should_notify_coordination_drop(self):
        """Test coordination drop notification logic."""
        subscription = ProjectMonitoringSubscription.objects.create(
            user_profile=self.user_profile,
            project=self.project,
            coordination_threshold=0.6
        )
        
        self.assertTrue(subscription.should_notify_coordination_drop(0.4))
        self.assertFalse(subscription.should_notify_coordination_drop(0.8))


class ProjectMonitoringAPITests(APITestCase):
    """Test cases for Project Monitoring API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        # Create users
        self.owner_user = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='testpass123'
        )
        self.owner_profile = UserProfile.objects.create(user=self.owner_user)
        
        self.member_user = User.objects.create_user(
            username='member',
            email='member@example.com',
            password='testpass123'
        )
        self.member_profile = UserProfile.objects.create(user=self.member_user)
        
        self.other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        self.other_profile = UserProfile.objects.create(user=self.other_user)
        
        # Create project
        self.project = Project.objects.create(
            name='Test Project',
            repo_url='https://github.com/test/repo',
            owner_profile=self.owner_profile
        )
        
        # Add member to project
        ProjectMember.objects.create(
            project=self.project,
            profile=self.member_profile,
            role=ProjectRole.REVIEWER
        )
        
        # Create monitoring records
        self.monitoring1 = ProjectMonitoring.objects.create(
            project=self.project,
            analysis_type=AnalysisType.STC,
            status=AnalysisStatus.COMPLETED,
            stc_value=0.8,
            risk_score=0.2,
            total_contributors=10
        )
        
        self.monitoring2 = ProjectMonitoring.objects.create(
            project=self.project,
            analysis_type=AnalysisType.MC_STC,
            status=AnalysisStatus.RUNNING
        )
    
    def test_list_monitoring_records_as_owner(self):
        """Test listing monitoring records as project owner."""
        self.client.force_authenticate(user=self.owner_user)
        
        response = self.client.get('/api/project-monitoring/monitoring/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_list_monitoring_records_as_member(self):
        """Test listing monitoring records as project member."""
        self.client.force_authenticate(user=self.member_user)
        
        response = self.client.get('/api/project-monitoring/monitoring/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_list_monitoring_records_as_non_member(self):
        """Test that non-members cannot see monitoring records."""
        self.client.force_authenticate(user=self.other_user)
        
        response = self.client.get('/api/project-monitoring/monitoring/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
    
    def test_filter_by_project_id(self):
        """Test filtering monitoring records by project ID."""
        self.client.force_authenticate(user=self.owner_user)
        
        response = self.client.get(
            f'/api/project-monitoring/monitoring/?project_id={self.project.id}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_filter_by_analysis_type(self):
        """Test filtering monitoring records by analysis type."""
        self.client.force_authenticate(user=self.owner_user)
        
        response = self.client.get(
            '/api/project-monitoring/monitoring/?analysis_type=stc'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['analysis_type'], 'stc')
    
    def test_get_project_stats(self):
        """Test getting project statistics."""
        self.client.force_authenticate(user=self.owner_user)
        
        response = self.client.get('/api/project-monitoring/monitoring/project_stats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)
        
        stats = response.data['data'][0]
        self.assertEqual(stats['project_name'], 'Test Project')
        self.assertEqual(stats['total_analyses'], 2)
        self.assertEqual(stats['completed_analyses'], 1)
    
    def test_get_project_trends(self):
        """Test getting project trend data."""
        self.client.force_authenticate(user=self.owner_user)
        
        response = self.client.get(
            f'/api/project-monitoring/monitoring/project_trends/?project_id={self.project.id}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['project_name'], 'Test Project')
    
    def test_check_project_access_as_owner(self):
        """Test checking project access as owner."""
        self.client.force_authenticate(user=self.owner_user)
        
        response = self.client.get(
            f'/api/project-monitoring/check-access/{self.project.id}/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['data']
        self.assertTrue(data['has_access'])
        self.assertTrue(data['is_owner'])
        self.assertEqual(data['role'], 'owner')
    
    def test_check_project_access_as_member(self):
        """Test checking project access as member."""
        self.client.force_authenticate(user=self.member_user)
        
        response = self.client.get(
            f'/api/project-monitoring/check-access/{self.project.id}/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['data']
        self.assertTrue(data['has_access'])
        self.assertFalse(data['is_owner'])
        self.assertTrue(data['is_member'])
        self.assertEqual(data['role'], 'reviewer')
    
    def test_check_project_access_as_non_member(self):
        """Test checking project access as non-member."""
        self.client.force_authenticate(user=self.other_user)
        
        response = self.client.get(
            f'/api/project-monitoring/check-access/{self.project.id}/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['data']
        self.assertFalse(data['has_access'])
        self.assertFalse(data['is_owner'])
        self.assertFalse(data['is_member'])
        self.assertIsNone(data['role'])
    
    def test_create_monitoring_analysis(self):
        """Test creating a new monitoring analysis."""
        self.client.force_authenticate(user=self.owner_user)
        
        data = {
            'project_id': str(self.project.id),
            'analysis_type': 'stc',
            'branch': 'main'
        }
        
        response = self.client.post('/api/project-monitoring/create-analysis/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['analysis_type'], 'stc')
        self.assertEqual(response.data['data']['branch_analyzed'], 'main')
    
    def test_create_monitoring_analysis_unauthorized(self):
        """Test that unauthorized users cannot create monitoring analysis."""
        self.client.force_authenticate(user=self.other_user)
        
        data = {
            'project_id': str(self.project.id),
            'analysis_type': 'stc'
        }
        
        response = self.client.post('/api/project-monitoring/create-analysis/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
