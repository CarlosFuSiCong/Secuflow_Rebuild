"""
API tests for STC Analysis endpoints.
"""

import json
import os
import tempfile
from unittest.mock import patch, MagicMock
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from tests.conftest import BaseTestCase
from tests.utils.test_helpers import APITestMixin, MockTNMOutputMixin
from tests.fixtures.sample_data import SampleDataMixin
from contributors.models import Contributor, ProjectContributor
from contributors.enums import FunctionalRole
from stc_analysis.models import STCAnalysis
import numpy as np


class STCAnalysisAPITests(BaseTestCase, APITestCase, APITestMixin):
    """Test STC Analysis API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        
        self.client = self.get_authenticated_client(self.user)
    
    def test_list_analyses(self):
        """Test listing STC analyses."""
        # Create some analyses
        STCAnalysis.objects.create(project=self.project)
        STCAnalysis.objects.create(project=self.project, use_monte_carlo=True)
        
        response = self.client.get('/api/stc/analyses/')
        
        self.assert_api_success(response)
        data = response.json()['data']
        self.assertEqual(data['count'], 2)
    
    def test_list_analyses_filter_by_project(self):
        """Test filtering analyses by project."""
        # Create analyses for different projects
        STCAnalysis.objects.create(project=self.project)
        
        other_project = self.project.__class__.objects.create(
            name='Other Project',
            repo_url='https://github.com/other/repo',
            owner_profile=self.other_profile
        )
        STCAnalysis.objects.create(project=other_project)
        
        response = self.client.get(f'/api/stc/analyses/?project={self.project.id}')
        
        self.assert_api_success(response)
        data = response.json()['data']
        self.assertEqual(data['count'], 1)
    
    def test_create_analysis(self):
        """Test creating a new STC analysis."""
        data = {
            'project': str(self.project.id),
            'use_monte_carlo': False,
            'monte_carlo_iterations': 1000
        }
        
        response = self.client.post('/api/stc/analyses/', data, format='json')
        
        self.assert_api_success(response, status.HTTP_201_CREATED)
        response_data = response.json()['data']
        self.assertEqual(response_data['project'], str(self.project.id))
        self.assertFalse(response_data['use_monte_carlo'])
    
    def test_create_monte_carlo_analysis(self):
        """Test creating a Monte Carlo STC analysis."""
        data = {
            'project': str(self.project.id),
            'use_monte_carlo': True,
            'monte_carlo_iterations': 5000
        }
        
        response = self.client.post('/api/stc/analyses/', data, format='json')
        
        self.assert_api_success(response, status.HTTP_201_CREATED)
        response_data = response.json()['data']
        self.assertTrue(response_data['use_monte_carlo'])
        self.assertEqual(response_data['monte_carlo_iterations'], 5000)
    
    def test_create_analysis_invalid_project(self):
        """Test creating analysis with invalid project ID."""
        data = {
            'project': '00000000-0000-0000-0000-000000000000',
            'use_monte_carlo': False
        }
        
        response = self.client.post('/api/stc/analyses/', data, format='json')
        
        self.assert_api_error(response, status.HTTP_400_BAD_REQUEST)
    
    def test_get_analysis_detail(self):
        """Test getting analysis details."""
        analysis = STCAnalysis.objects.create(
            project=self.project,
            use_monte_carlo=True,
            monte_carlo_iterations=2000
        )
        
        response = self.client.get(f'/api/stc/analyses/{analysis.id}/')
        
        self.assert_api_success(response)
        data = response.json()['data']
        self.assertEqual(data['id'], str(analysis.id))
        self.assertTrue(data['use_monte_carlo'])
        self.assertEqual(data['monte_carlo_iterations'], 2000)
    
    def test_delete_analysis(self):
        """Test deleting an analysis."""
        analysis = STCAnalysis.objects.create(project=self.project)
        
        response = self.client.delete(f'/api/stc/analyses/{analysis.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify analysis was deleted
        with self.assertRaises(STCAnalysis.DoesNotExist):
            STCAnalysis.objects.get(id=analysis.id)
    
    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access analyses."""
        # Remove authentication
        self.client.credentials()
        
        response = self.client.get('/api/stc/analyses/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class STCAnalysisExecutionAPITests(BaseTestCase, APITestCase, APITestMixin, MockTNMOutputMixin):
    """Test STC Analysis execution API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        
        self.client = self.get_authenticated_client(self.user)
        
        # Create analysis
        self.analysis = STCAnalysis.objects.create(
            project=self.project,
            use_monte_carlo=False
        )
        
        # Create contributors for MC-STC testing
        self.create_test_contributors()
    
    def create_test_contributors(self):
        """Create test contributors with different roles."""
        # Create developer contributors
        dev_contributor1 = Contributor.objects.create(
            email='developer1@example.com',
            github_login='dev1'
        )
        ProjectContributor.objects.create(
            project=self.project,
            contributor=dev_contributor1,
            functional_role=FunctionalRole.DEVELOPER
        )
        
        dev_contributor2 = Contributor.objects.create(
            email='developer2@example.com',
            github_login='dev2'
        )
        ProjectContributor.objects.create(
            project=self.project,
            contributor=dev_contributor2,
            functional_role=FunctionalRole.DEVELOPER
        )
        
        # Create security contributors
        sec_contributor1 = Contributor.objects.create(
            email='security1@example.com',
            github_login='sec1'
        )
        ProjectContributor.objects.create(
            project=self.project,
            contributor=sec_contributor1,
            functional_role=FunctionalRole.SECURITY
        )
    
    @patch('stc_analysis.views.os.path.exists')
    @patch('stc_analysis.views.json.load')
    @patch('builtins.open')
    def test_start_analysis_success(self, mock_open, mock_json_load, mock_exists):
        """Test successfully starting an STC analysis."""
        # Mock TNM files exist
        mock_exists.return_value = True
        
        # Mock TNM file contents
        mock_json_load.side_effect = [
            # AssignmentMatrix.json
            [[5, 3, 0], [2, 4, 3], [0, 1, 5]],
            # FileDependencyMatrix.json  
            [[0, 1, 0], [1, 0, 1], [0, 1, 0]],
            # idToUser.json
            {"0": "developer1@example.com", "1": "developer2@example.com", "2": "security1@example.com"},
            # idToFile.json
            {"0": "src/main.py", "1": "src/utils.py", "2": "src/security.py"}
        ]
        
        response = self.client.post(f'/api/stc/analyses/{self.analysis.id}/start_analysis/')
        
        self.assert_api_success(response)
        
        # Verify analysis was updated
        self.analysis.refresh_from_db()
        self.assertTrue(self.analysis.is_completed)
    
    @patch('stc_analysis.views.os.path.exists')
    def test_start_analysis_missing_tnm_files(self, mock_exists):
        """Test starting analysis with missing TNM files."""
        # Mock TNM files don't exist
        mock_exists.return_value = False
        
        response = self.client.post(f'/api/stc/analyses/{self.analysis.id}/start_analysis/')
        
        self.assert_api_error(response, status.HTTP_400_BAD_REQUEST)
        
        # Verify analysis was not completed
        self.analysis.refresh_from_db()
        self.assertFalse(self.analysis.is_completed)
        self.assertIsNotNone(self.analysis.error_message)
    
    def test_start_analysis_already_completed(self):
        """Test starting an already completed analysis."""
        # Mark analysis as completed
        self.analysis.is_completed = True
        self.analysis.save()
        
        response = self.client.post(f'/api/stc/analyses/{self.analysis.id}/start_analysis/')
        
        self.assert_api_error(response, status.HTTP_400_BAD_REQUEST)
    
    def test_start_analysis_not_found(self):
        """Test starting analysis that doesn't exist."""
        response = self.client.post('/api/stc/analyses/00000000-0000-0000-0000-000000000000/start_analysis/')
        
        self.assert_api_error(response, status.HTTP_404_NOT_FOUND)
    
    @patch('stc_analysis.views.os.path.exists')
    @patch('stc_analysis.views.json.load')
    @patch('builtins.open')
    def test_start_mc_stc_analysis(self, mock_open, mock_json_load, mock_exists):
        """Test starting MC-STC analysis with contributors."""
        # Create MC-STC analysis
        mc_analysis = STCAnalysis.objects.create(
            project=self.project,
            use_monte_carlo=True,
            monte_carlo_iterations=1000
        )
        
        # Mock TNM files exist
        mock_exists.return_value = True
        
        # Mock TNM file contents
        mock_json_load.side_effect = [
            # AssignmentMatrix.json
            [[5, 3, 0], [2, 4, 3], [0, 1, 5]],
            # FileDependencyMatrix.json
            [[0, 1, 0], [1, 0, 1], [0, 1, 0]],
            # idToUser.json
            {"0": "developer1@example.com", "1": "developer2@example.com", "2": "security1@example.com"},
            # idToFile.json
            {"0": "src/main.py", "1": "src/utils.py", "2": "src/security.py"}
        ]
        
        response = self.client.post(f'/api/stc/analyses/{mc_analysis.id}/start_analysis/')
        
        self.assert_api_success(response)
        
        # Verify MC-STC analysis was completed
        mc_analysis.refresh_from_db()
        self.assertTrue(mc_analysis.is_completed)


class STCAnalysisResultsAPITests(BaseTestCase, APITestCase, APITestMixin):
    """Test STC Analysis results API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        
        self.client = self.get_authenticated_client(self.user)
        
        # Create completed analysis with results
        self.analysis = STCAnalysis.objects.create(
            project=self.project,
            use_monte_carlo=False,
            is_completed=True,
            results_file='results/test_analysis.json'
        )
    
    @patch('stc_analysis.views.os.path.exists')
    @patch('stc_analysis.views.json.load')
    @patch('builtins.open')
    def test_get_analysis_results(self, mock_open, mock_json_load, mock_exists):
        """Test getting analysis results."""
        # Mock results file exists
        mock_exists.return_value = True
        
        # Mock results file content
        mock_results = {
            'stc_value': 0.75,
            'total_required_edges': 100,
            'satisfied_edges': 75,
            'coordination_efficiency': 75.0,
            'analysis_metadata': {
                'analysis_date': '2023-10-01T10:00:00Z',
                'branch_analyzed': 'main'
            }
        }
        mock_json_load.return_value = mock_results
        
        response = self.client.get(f'/api/stc/analyses/{self.analysis.id}/results/')
        
        self.assert_api_success(response)
        data = response.json()['data']
        self.assertEqual(data['stc_value'], 0.75)
        self.assertEqual(data['coordination_efficiency'], 75.0)
    
    def test_get_results_analysis_not_completed(self):
        """Test getting results for incomplete analysis."""
        # Create incomplete analysis
        incomplete_analysis = STCAnalysis.objects.create(
            project=self.project,
            use_monte_carlo=False,
            is_completed=False
        )
        
        response = self.client.get(f'/api/stc/analyses/{incomplete_analysis.id}/results/')
        
        self.assert_api_error(response, status.HTTP_400_BAD_REQUEST)
    
    @patch('stc_analysis.views.os.path.exists')
    def test_get_results_file_not_found(self, mock_exists):
        """Test getting results when results file doesn't exist."""
        # Mock results file doesn't exist
        mock_exists.return_value = False
        
        response = self.client.get(f'/api/stc/analyses/{self.analysis.id}/results/')
        
        self.assert_api_error(response, status.HTTP_404_NOT_FOUND)


class STCAnalysisPermissionTests(BaseTestCase, APITestCase, APITestMixin):
    """Test STC Analysis permission controls."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        
        # Create analysis owned by user
        self.analysis = STCAnalysis.objects.create(project=self.project)
        
        # Create another user and project
        self.other_analysis = STCAnalysis.objects.create(
            project=self.project.__class__.objects.create(
                name='Other Project',
                repo_url='https://github.com/other/repo',
                owner_profile=self.other_profile
            )
        )
    
    def test_owner_can_access_analysis(self):
        """Test that project owner can access their analyses."""
        client = self.get_authenticated_client(self.user)
        
        response = client.get(f'/api/stc/analyses/{self.analysis.id}/')
        
        self.assert_api_success(response)
    
    def test_non_owner_cannot_access_analysis(self):
        """Test that non-owners cannot access other's analyses."""
        client = self.get_authenticated_client(self.other_user)
        
        response = client.get(f'/api/stc/analyses/{self.analysis.id}/')
        
        self.assert_api_error(response, status.HTTP_404_NOT_FOUND)
    
    def test_owner_can_delete_analysis(self):
        """Test that project owner can delete their analyses."""
        client = self.get_authenticated_client(self.user)
        
        response = client.delete(f'/api/stc/analyses/{self.analysis.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_non_owner_cannot_delete_analysis(self):
        """Test that non-owners cannot delete other's analyses."""
        client = self.get_authenticated_client(self.other_user)
        
        response = client.delete(f'/api/stc/analyses/{self.analysis.id}/')
        
        self.assert_api_error(response, status.HTTP_404_NOT_FOUND)
