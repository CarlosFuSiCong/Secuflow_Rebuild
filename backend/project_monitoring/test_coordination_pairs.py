"""
Tests for Top Coordination Pairs functionality.
"""

from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User, UserProfile
from projects.models import Project, ProjectMember, ProjectRole
from .models import ProjectMonitoring, AnalysisType, AnalysisStatus


class TopCoordinationPairsTests(TestCase):
    """Test cases for top coordination pairs functionality."""
    
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
    
    def test_store_top_coordination_pairs(self):
        """Test storing top coordination pairs in monitoring record."""
        # Sample coordination pairs data
        coordination_pairs = [
            {
                'developer_id': '1',
                'developer_info': 'alice@dev.com',
                'security_id': '2',
                'security_info': 'bob@security.com',
                'required_coordination': 5.0,
                'actual_coordination': 2.0,
                'coordination_gap': 3.0,
                'is_missed_coordination': False,
                'impact_score': 8.0,
                'pair_name': 'alice@dev.com ↔ bob@security.com'
            },
            {
                'developer_id': '3',
                'developer_info': 'charlie@dev.com',
                'security_id': '4',
                'security_info': 'diana@security.com',
                'required_coordination': 4.0,
                'actual_coordination': 0.0,
                'coordination_gap': 4.0,
                'is_missed_coordination': True,
                'impact_score': 8.0,
                'pair_name': 'charlie@dev.com ↔ diana@security.com'
            }
        ]
        
        monitoring = ProjectMonitoring.objects.create(
            project=self.project,
            analysis_type=AnalysisType.MC_STC,
            status=AnalysisStatus.COMPLETED,
            stc_value=0.6,
            top_coordination_pairs=coordination_pairs
        )
        
        self.assertEqual(len(monitoring.top_coordination_pairs), 2)
        self.assertEqual(monitoring.top_coordination_pairs[0]['developer_info'], 'alice@dev.com')
        self.assertEqual(monitoring.top_coordination_pairs[0]['security_info'], 'bob@security.com')
        self.assertEqual(monitoring.top_coordination_pairs[0]['impact_score'], 8.0)
        self.assertTrue(monitoring.top_coordination_pairs[1]['is_missed_coordination'])


class TopCoordinationPairsAPITests(APITestCase):
    """Test cases for top coordination pairs API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        # Create users
        self.owner_user = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='testpass123'
        )
        self.owner_profile = UserProfile.objects.create(user=self.owner_user)
        
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
        
        # Create monitoring record with coordination pairs
        self.coordination_pairs = [
            {
                'developer_id': '1',
                'developer_info': 'alice@dev.com',
                'security_id': '2', 
                'security_info': 'bob@security.com',
                'required_coordination': 5.0,
                'actual_coordination': 2.0,
                'coordination_gap': 3.0,
                'is_missed_coordination': False,
                'impact_score': 8.0,
                'pair_name': 'alice@dev.com ↔ bob@security.com'
            },
            {
                'developer_id': '3',
                'developer_info': 'charlie@dev.com',
                'security_id': '4',
                'security_info': 'diana@security.com',
                'required_coordination': 4.0,
                'actual_coordination': 0.0,
                'coordination_gap': 4.0,
                'is_missed_coordination': True,
                'impact_score': 8.0,
                'pair_name': 'charlie@dev.com ↔ diana@security.com'
            }
        ]
        
        self.monitoring = ProjectMonitoring.objects.create(
            project=self.project,
            analysis_type=AnalysisType.MC_STC,
            status=AnalysisStatus.COMPLETED,
            stc_value=0.6,
            top_coordination_pairs=self.coordination_pairs
        )
    
    def test_get_top_coordination_pairs_as_owner(self):
        """Test getting top coordination pairs as project owner."""
        self.client.force_authenticate(user=self.owner_user)
        
        response = self.client.get(
            f'/api/project-monitoring/monitoring/top_coordination_pairs/?project_id={self.project.id}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        self.assertEqual(response_data['data']['project_name'], 'Test Project')
        self.assertEqual(response_data['data']['total_pairs'], 2)
        self.assertEqual(len(response_data['data']['coordination_pairs']), 2)
        
        # Check first pair
        first_pair = response_data['data']['coordination_pairs'][0]
        self.assertEqual(first_pair['developer_info'], 'alice@dev.com')
        self.assertEqual(first_pair['security_info'], 'bob@security.com')
        self.assertEqual(first_pair['impact_score'], 8.0)
    
    def test_get_top_coordination_pairs_unauthorized(self):
        """Test that unauthorized users cannot get coordination pairs."""
        self.client.force_authenticate(user=self.other_user)
        
        response = self.client.get(
            f'/api/project-monitoring/monitoring/top_coordination_pairs/?project_id={self.project.id}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_get_top_coordination_pairs_with_top_n(self):
        """Test limiting coordination pairs with top_n parameter."""
        self.client.force_authenticate(user=self.owner_user)
        
        response = self.client.get(
            f'/api/project-monitoring/monitoring/top_coordination_pairs/?project_id={self.project.id}&top_n=1'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        self.assertEqual(len(response_data['data']['coordination_pairs']), 1)
    
    def test_get_top_coordination_pairs_missing_project_id(self):
        """Test error when project_id is missing."""
        self.client.force_authenticate(user=self.owner_user)
        
        response = self.client.get('/api/project-monitoring/monitoring/top_coordination_pairs/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertEqual(response_data['errorCode'], 'MISSING_PROJECT_ID')
    
    def test_get_top_coordination_pairs_no_analysis(self):
        """Test error when no MC-STC analysis exists."""
        # Create project without MC-STC analysis
        project2 = Project.objects.create(
            name='Project Without Analysis',
            repo_url='https://github.com/test/no-analysis',
            owner_profile=self.owner_profile
        )
        
        self.client.force_authenticate(user=self.owner_user)
        
        response = self.client.get(
            f'/api/project-monitoring/monitoring/top_coordination_pairs/?project_id={project2.id}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response_data = response.json()
        self.assertIn('No completed MC-STC analysis found', response_data['errorMessage'])
