"""
API tests for Project Monitoring endpoints.
"""

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from tests.conftest import BaseTestCase
from tests.utils.test_helpers import APITestMixin
from projects.models import ProjectMember, ProjectRole
from project_monitoring.models import ProjectMonitoring, ProjectMonitoringSubscription, AnalysisType, AnalysisStatus


class ProjectMonitoringAPITests(BaseTestCase, APITestCase, APITestMixin):
    """Test cases for Project Monitoring API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        
        # Set up API clients with authentication
        self.owner_client = self.get_authenticated_client(self.user)
        self.member_client = self.get_authenticated_client(self.other_user)
        
        # Add other_user as member to project
        ProjectMember.objects.create(
            project=self.project,
            profile=self.other_profile,
            role=ProjectRole.REVIEWER
        )
        
        # Create some monitoring records
        self.monitoring1 = ProjectMonitoring.objects.create(
            project=self.project,
            analysis_type=AnalysisType.STC,
            status=AnalysisStatus.COMPLETED,
            stc_value=0.75
        )
        
        self.monitoring2 = ProjectMonitoring.objects.create(
            project=self.project,
            analysis_type=AnalysisType.MC_STC,
            status=AnalysisStatus.PENDING
        )
    
    def test_list_monitoring_records_as_owner(self):
        """Test listing monitoring records as project owner."""
        response = self.owner_client.get('/api/project-monitoring/monitoring/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['results']), 2)
    
    def test_list_monitoring_records_as_member(self):
        """Test listing monitoring records as project member."""
        response = self.member_client.get('/api/project-monitoring/monitoring/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['results']), 2)
    
    def test_list_monitoring_records_as_non_member(self):
        """Test that non-members cannot see monitoring records."""
        # Create another user who is not a member
        non_member_client = self.get_authenticated_client(self.admin_user)
        
        response = non_member_client.get('/api/project-monitoring/monitoring/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['results']), 0)
    
    def test_filter_by_project_id(self):
        """Test filtering monitoring records by project ID."""
        response = self.owner_client.get(
            f'/api/project-monitoring/monitoring/?project_id={self.project.id}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['results']), 2)
    
    def test_filter_by_analysis_type(self):
        """Test filtering monitoring records by analysis type."""
        response = self.owner_client.get(
            '/api/project-monitoring/monitoring/?analysis_type=stc'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['results']), 1)
        self.assertEqual(response.json()['results'][0]['analysis_type'], 'stc')
    
    def test_get_project_stats(self):
        """Test getting project statistics."""
        response = self.owner_client.get('/api/project-monitoring/monitoring/project_stats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 1)
        
        stats = response.json()['data'][0]
        self.assertEqual(stats['project_name'], 'Test Project')
        self.assertEqual(stats['total_analyses'], 2)
        self.assertEqual(stats['completed_analyses'], 1)
    
    def test_get_project_trends(self):
        """Test getting project trend data."""
        response = self.owner_client.get(
            f'/api/project-monitoring/monitoring/project_trends/?project_id={self.project.id}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['project_name'], 'Test Project')
    
    def test_check_project_access_as_owner(self):
        """Test checking project access as owner."""
        response = self.owner_client.get(
            f'/api/project-monitoring/check-access/?project_id={self.project.id}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertTrue(data['has_access'])
        self.assertEqual(data['role'], 'owner')
    
    def test_check_project_access_as_member(self):
        """Test checking project access as member."""
        response = self.member_client.get(
            f'/api/project-monitoring/check-access/?project_id={self.project.id}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertTrue(data['has_access'])
        self.assertEqual(data['role'], 'member')
    
    def test_check_project_access_as_non_member(self):
        """Test checking project access as non-member."""
        non_member_client = self.get_authenticated_client(self.admin_user)
        
        response = non_member_client.get(
            f'/api/project-monitoring/check-access/?project_id={self.project.id}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertFalse(data['has_access'])
    
    def test_create_monitoring_analysis(self):
        """Test creating a new monitoring analysis."""
        data = {
            'project_id': str(self.project.id),
            'analysis_type': 'stc',
            'branch_analyzed': 'main'
        }
        
        response = self.owner_client.post('/api/project-monitoring/create-analysis/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['data']['analysis_type'], 'stc')
        self.assertEqual(response.json()['data']['branch_analyzed'], 'main')
    
    def test_create_monitoring_analysis_unauthorized(self):
        """Test that unauthorized users cannot create monitoring analysis."""
        data = {
            'project_id': str(self.project.id),
            'analysis_type': 'stc'
        }
        
        # Remove authentication
        self.client.credentials()
        response = self.client.post('/api/project-monitoring/create-analysis/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TopCoordinationPairsAPITests(BaseTestCase, APITestCase, APITestMixin):
    """Test cases for top coordination pairs API."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        
        self.client = self.get_authenticated_client(self.user)
        
        # Create a completed MC-STC monitoring record with coordination pairs
        self.monitoring = ProjectMonitoring.objects.create(
            project=self.project,
            analysis_type=AnalysisType.MC_STC,
            status=AnalysisStatus.COMPLETED,
            stc_value=0.65,
            top_coordination_pairs=[
                {
                    'developer_id': 'dev1',
                    'developer_info': 'developer1@example.com',
                    'security_id': 'sec1',
                    'security_info': 'security1@example.com',
                    'required_coordination': 5.0,
                    'actual_coordination': 2.0,
                    'coordination_gap': 3.0,
                    'is_missed_coordination': True,
                    'impact_score': 10.0,
                    'pair_name': 'developer1@example.com ↔ security1@example.com'
                },
                {
                    'developer_id': 'dev2',
                    'developer_info': 'developer2@example.com',
                    'security_id': 'sec2',
                    'security_info': 'security2@example.com',
                    'required_coordination': 3.0,
                    'actual_coordination': 3.0,
                    'coordination_gap': 0.0,
                    'is_missed_coordination': False,
                    'impact_score': 3.0,
                    'pair_name': 'developer2@example.com ↔ security2@example.com'
                }
            ]
        )
    
    def test_get_top_coordination_pairs_success(self):
        """Test successfully getting top coordination pairs."""
        response = self.client.get(
            f'/api/project-monitoring/monitoring/top_coordination_pairs/?project_id={self.project.id}'
        )
        
        self.assert_api_success(response)
        data = response.json()['data']
        
        self.assertEqual(data['project_id'], str(self.project.id))
        self.assertEqual(data['project_name'], 'Test Project')
        self.assertEqual(data['stc_value'], 0.65)
        self.assertEqual(len(data['coordination_pairs']), 2)
        
        # Check first pair (highest impact)
        first_pair = data['coordination_pairs'][0]
        self.assertEqual(first_pair['developer_info'], 'developer1@example.com')
        self.assertEqual(first_pair['security_info'], 'security1@example.com')
        self.assertTrue(first_pair['is_missed_coordination'])
        self.assertEqual(first_pair['impact_score'], 10.0)
    
    def test_get_top_coordination_pairs_missing_project_id(self):
        """Test getting coordination pairs without project_id parameter."""
        response = self.client.get('/api/project-monitoring/monitoring/top_coordination_pairs/')
        
        self.assert_api_error(response, status.HTTP_400_BAD_REQUEST)
    
    def test_get_top_coordination_pairs_project_not_found(self):
        """Test getting coordination pairs for non-existent project."""
        response = self.client.get(
            '/api/project-monitoring/monitoring/top_coordination_pairs/?project_id=00000000-0000-0000-0000-000000000000'
        )
        
        self.assert_api_error(response, status.HTTP_404_NOT_FOUND)
    
    def test_get_top_coordination_pairs_no_access(self):
        """Test getting coordination pairs without project access."""
        # Create another user without access to the project
        no_access_client = self.get_authenticated_client(self.admin_user)
        
        response = no_access_client.get(
            f'/api/project-monitoring/monitoring/top_coordination_pairs/?project_id={self.project.id}'
        )
        
        self.assert_api_error(response, status.HTTP_403_FORBIDDEN)
    
    def test_get_top_coordination_pairs_no_mc_stc_analysis(self):
        """Test getting coordination pairs when no MC-STC analysis exists."""
        # Delete the MC-STC monitoring record
        self.monitoring.delete()
        
        response = self.client.get(
            f'/api/project-monitoring/monitoring/top_coordination_pairs/?project_id={self.project.id}'
        )
        
        self.assert_api_error(response, status.HTTP_404_NOT_FOUND)
    
    def test_get_top_coordination_pairs_with_limit(self):
        """Test getting coordination pairs with top_n limit."""
        response = self.client.get(
            f'/api/project-monitoring/monitoring/top_coordination_pairs/?project_id={self.project.id}&top_n=1'
        )
        
        self.assert_api_success(response)
        data = response.json()['data']
        self.assertEqual(len(data['coordination_pairs']), 1)
