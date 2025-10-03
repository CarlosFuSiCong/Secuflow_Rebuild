"""
Tests for STC Analysis API views
"""
import json
import os
import tempfile
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from projects.models import Project
from accounts.models import User, UserProfile
from contributors.models import Contributor, ProjectContributor
from stc_analysis.models import STCAnalysis
import numpy as np


class STCAnalysisAPITest(TestCase):
    """Test STC Analysis API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            display_name='Test User'
        )
        
        # Create project
        self.project = Project.objects.create(
            name='Test Project',
            repo_url='https://github.com/test/repo',
            owner_profile=self.profile
        )
        
        # Create API client with authentication
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_list_analyses(self):
        """Test listing STC analyses"""
        # Create some analyses
        STCAnalysis.objects.create(project=self.project)
        STCAnalysis.objects.create(project=self.project, use_monte_carlo=True)
        
        url = reverse('stc-analysis-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(data['data']['count'], 2)
    
    def test_list_analyses_filter_by_project(self):
        """Test filtering analyses by project"""
        # Create another project
        project2 = Project.objects.create(
            name='Project 2',
            repo_url='https://github.com/test/repo2',
            owner_profile=self.profile
        )
        
        # Create analyses for both projects
        STCAnalysis.objects.create(project=self.project)
        STCAnalysis.objects.create(project=self.project)
        STCAnalysis.objects.create(project=project2)
        
        url = reverse('stc-analysis-list')
        response = self.client.get(url, {'project_id': str(self.project.id)})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(data['data']['count'], 2)
    
    def test_create_analysis(self):
        """Test creating an STC analysis"""
        url = reverse('stc-analysis-list')
        data = {
            'project': str(self.project.id),
            'use_monte_carlo': False,
            'monte_carlo_iterations': 1000
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(STCAnalysis.objects.count(), 1)
        
        analysis = STCAnalysis.objects.first()
        self.assertEqual(analysis.project, self.project)
        self.assertFalse(analysis.use_monte_carlo)
    
    def test_create_analysis_invalid_iterations(self):
        """Test creating analysis with invalid iterations"""
        url = reverse('stc-analysis-list')
        data = {
            'project': str(self.project.id),
            'use_monte_carlo': True,
            'monte_carlo_iterations': 50  # Too low
        }
        
        response = self.client.post(url, data, format='json')
        
        # Should return 400 for validation errors
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(STCAnalysis.objects.count(), 0)
    
    def test_get_analysis_detail(self):
        """Test retrieving analysis details"""
        analysis = STCAnalysis.objects.create(project=self.project)
        
        url = reverse('stc-analysis-detail', kwargs={'pk': analysis.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(data['data']['id'], analysis.id)
        self.assertEqual(data['data']['project_name'], 'Test Project')
    
    def test_update_analysis(self):
        """Test updating an analysis"""
        analysis = STCAnalysis.objects.create(project=self.project)
        
        url = reverse('stc-analysis-detail', kwargs={'pk': analysis.id})
        data = {
            'use_monte_carlo': True,
            'monte_carlo_iterations': 2000
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        analysis.refresh_from_db()
        self.assertTrue(analysis.use_monte_carlo)
        self.assertEqual(analysis.monte_carlo_iterations, 2000)
    
    def test_delete_analysis(self):
        """Test deleting an analysis"""
        analysis = STCAnalysis.objects.create(project=self.project)
        
        url = reverse('stc-analysis-detail', kwargs={'pk': analysis.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(STCAnalysis.objects.count(), 0)
    
    def test_unauthenticated_request(self):
        """Test that unauthenticated requests are rejected"""
        # Remove credentials
        self.client.credentials()
        
        url = reverse('stc-analysis-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class STCAnalysisStartTest(TestCase):
    """Test starting STC analysis"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            display_name='Test User'
        )
        
        self.project = Project.objects.create(
            name='Test Project',
            repo_url='https://github.com/test/repo',
            owner_profile=self.profile
        )
        
        self.analysis = STCAnalysis.objects.create(project=self.project)
        
        # Create API client with authentication
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Create temporary directory for TNM output
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary files"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_start_analysis_no_tnm_data(self):
        """Test starting analysis without TNM data"""
        url = reverse('stc-analysis-start-analysis', kwargs={'pk': self.analysis.id})
        data = {'branch': 'main'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response_data = json.loads(response.content)
        self.assertIn('TNM', response_data['errorMessage'])
    
    @override_settings(TNM_OUTPUT_DIR=None)
    def test_start_analysis_with_tnm_data(self):
        """Test starting analysis with TNM data"""
        # Create mock TNM output files
        tnm_dir = os.path.join(self.temp_dir, f'project_{self.project.id}_main')
        os.makedirs(tnm_dir, exist_ok=True)
        
        # Create CA matrix (Contribution Assignment: 3 developers × 4 files)
        # This is what TNM actually outputs - developers' contributions to files
        ca_matrix = [
            [5, 3, 0, 2],  # Developer 0's contributions to files 0-3
            [2, 4, 3, 0],  # Developer 1's contributions to files 0-3
            [0, 1, 5, 4]   # Developer 2's contributions to files 0-3
        ]
        with open(os.path.join(tnm_dir, 'AssignmentMatrix.json'), 'w') as f:
            json.dump(ca_matrix, f)
        
        # Create user mapping
        user_mapping = {'0': 'user1', '1': 'user2', '2': 'user3'}
        with open(os.path.join(tnm_dir, 'idToUser.json'), 'w') as f:
            json.dump(user_mapping, f)
        
        url = reverse('stc-analysis-start-analysis', kwargs={'pk': self.analysis.id})
        data = {
            'branch': 'main',
            'tnm_output_dir': tnm_dir
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        self.assertIn('total_nodes', response_data['data'])
        
        # Check analysis was updated
        self.analysis.refresh_from_db()
        self.assertTrue(self.analysis.is_completed)
        self.assertIsNotNone(self.analysis.results_file)
    
    def test_start_already_completed_analysis(self):
        """Test starting an already completed analysis"""
        self.analysis.is_completed = True
        self.analysis.save()
        
        url = reverse('stc-analysis-start-analysis', kwargs={'pk': self.analysis.id})
        data = {'branch': 'main'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class STCAnalysisResultsTest(TestCase):
    """Test retrieving STC analysis results"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            display_name='Test User'
        )
        
        self.project = Project.objects.create(
            name='Test Project',
            repo_url='https://github.com/test/repo',
            owner_profile=self.profile
        )
        
        self.analysis = STCAnalysis.objects.create(
            project=self.project,
            is_completed=True
        )
        
        # Create API client with authentication
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Create temporary results file
        self.temp_dir = tempfile.mkdtemp()
        self.results_file = os.path.join(self.temp_dir, 'results.json')
        
        results_data = {
            'analysis_id': self.analysis.id,
            'project_id': str(self.project.id),
            'analysis_date': '2025-10-03T10:00:00Z',
            'use_monte_carlo': False,
            'total_nodes': 3,
            'results': [
                {'node_id': '0', 'contributor_login': 'user1', 'stc_value': 0.85, 'rank': 1},
                {'node_id': '1', 'contributor_login': 'user2', 'stc_value': 0.72, 'rank': 2},
                {'node_id': '2', 'contributor_login': 'user3', 'stc_value': 0.65, 'rank': 3}
            ]
        }
        
        with open(self.results_file, 'w') as f:
            json.dump(results_data, f)
        
        self.analysis.results_file = self.results_file
        self.analysis.save()
    
    def tearDown(self):
        """Clean up temporary files"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_get_results(self):
        """Test retrieving analysis results"""
        url = reverse('stc-analysis-results', kwargs={'pk': self.analysis.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(data['data']['total_nodes'], 3)
        self.assertEqual(len(data['data']['results']), 3)
    
    def test_get_results_top_n(self):
        """Test retrieving top N results"""
        url = reverse('stc-analysis-results', kwargs={'pk': self.analysis.id})
        response = self.client.get(url, {'top_n': 2})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(len(data['data']['results']), 2)
    
    def test_get_results_not_completed(self):
        """Test getting results for incomplete analysis"""
        self.analysis.is_completed = False
        self.analysis.save()
        
        url = reverse('stc-analysis-results', kwargs={'pk': self.analysis.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class STCComparisonTest(TestCase):
    """Test STC comparison endpoint"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            display_name='Test User'
        )
        
        self.project = Project.objects.create(
            name='Test Project',
            repo_url='https://github.com/test/repo',
            owner_profile=self.profile
        )
        
        # Create contributors
        self.contributor1 = Contributor.objects.create(github_login='user1')
        self.contributor2 = Contributor.objects.create(github_login='user2')
        
        # Create project contributors
        ProjectContributor.objects.create(
            project=self.project,
            contributor=self.contributor1,
            total_modifications=5000,
            files_modified=150,
            functional_role='coder',
            is_core_contributor=True
        )
        ProjectContributor.objects.create(
            project=self.project,
            contributor=self.contributor2,
            total_modifications=2000,
            files_modified=80,
            functional_role='reviewer',
            is_core_contributor=False
        )
        
        # Create analysis with results
        self.analysis = STCAnalysis.objects.create(
            project=self.project,
            is_completed=True
        )
        
        # Create API client with authentication
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Create temporary results file
        self.temp_dir = tempfile.mkdtemp()
        self.results_file = os.path.join(self.temp_dir, 'results.json')
        
        results_data = {
            'analysis_id': self.analysis.id,
            'project_id': str(self.project.id),
            'results': [
                {'node_id': '0', 'contributor_login': 'user1', 'stc_value': 0.85, 'rank': 1},
                {'node_id': '1', 'contributor_login': 'user2', 'stc_value': 0.72, 'rank': 2}
            ]
        }
        
        with open(self.results_file, 'w') as f:
            json.dump(results_data, f)
        
        self.analysis.results_file = self.results_file
        self.analysis.save()
    
    def tearDown(self):
        """Clean up temporary files"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_get_comparison(self):
        """Test getting STC comparison data"""
        url = reverse('project-stc-comparison', kwargs={'project_id': self.project.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(data['data']['total_contributors'], 2)
        self.assertEqual(len(data['data']['contributors']), 2)
        
        # Check first contributor data
        contrib = data['data']['contributors'][0]
        self.assertEqual(contrib['contributor_login'], 'user1')
        self.assertEqual(contrib['stc_value'], 0.85)
        self.assertEqual(contrib['total_modifications'], 5000)
    
    def test_comparison_filter_by_role(self):
        """Test filtering comparison by role"""
        url = reverse('project-stc-comparison', kwargs={'project_id': self.project.id})
        response = self.client.get(url, {'role': 'coder'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(data['data']['total_contributors'], 1)
        self.assertEqual(data['data']['contributors'][0]['functional_role'], 'coder')
    
    def test_comparison_top_n(self):
        """Test limiting comparison results"""
        url = reverse('project-stc-comparison', kwargs={'project_id': self.project.id})
        response = self.client.get(url, {'top_n': 1})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(len(data['data']['contributors']), 1)
    
    def test_comparison_no_analysis(self):
        """Test comparison when no analysis exists"""
        # Delete the analysis
        self.analysis.delete()
        
        url = reverse('project-stc-comparison', kwargs={'project_id': self.project.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

