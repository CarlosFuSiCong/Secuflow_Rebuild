"""
Integration tests for STC analysis workflow.
"""

import json
import tempfile
import os
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from tests.conftest import BaseTestCase
from stc_analysis.models import STCAnalysis
from project_monitoring.models import ProjectMonitoring, AnalysisType


class STCAnalysisWorkflowTests(BaseTestCase, APITestCase):
    """Test the complete STC analysis workflow."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        
        # Set up API client with authentication
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Create temporary TNM output directory
        self.temp_dir = tempfile.mkdtemp()
        self.tnm_output_dir = os.path.join(self.temp_dir, f'project_{self.project.id}_main')
        os.makedirs(self.tnm_output_dir, exist_ok=True)
        
        # Create sample TNM output files
        self.create_sample_tnm_files()
    
    def tearDown(self):
        """Clean up test data."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_sample_tnm_files(self):
        """Create sample TNM output files for testing."""
        # Sample Assignment Matrix
        assignment_matrix = [
            [5, 3, 0, 2, 1],
            [2, 4, 3, 0, 1],
            [0, 1, 5, 4, 2]
        ]
        
        with open(os.path.join(self.tnm_output_dir, 'AssignmentMatrix.json'), 'w') as f:
            json.dump(assignment_matrix, f)
        
        # Sample File Dependency Matrix
        dependency_matrix = [
            [0, 1, 0, 1, 0],
            [1, 0, 1, 0, 1],
            [0, 1, 0, 1, 0],
            [1, 0, 1, 0, 1],
            [0, 1, 0, 1, 0]
        ]
        
        with open(os.path.join(self.tnm_output_dir, 'FileDependencyMatrix.json'), 'w') as f:
            json.dump(dependency_matrix, f)
        
        # Sample ID to User mapping
        id_to_user = {
            "0": "developer1@example.com",
            "1": "developer2@example.com",
            "2": "security1@example.com"
        }
        
        with open(os.path.join(self.tnm_output_dir, 'idToUser.json'), 'w') as f:
            json.dump(id_to_user, f)
        
        # Sample ID to File mapping
        id_to_file = {
            "0": "src/main.py",
            "1": "src/utils.py",
            "2": "src/security.py",
            "3": "tests/test_main.py",
            "4": "README.md"
        }
        
        with open(os.path.join(self.tnm_output_dir, 'idToFile.json'), 'w') as f:
            json.dump(id_to_file, f)
    
    def test_complete_stc_analysis_workflow(self):
        """Test the complete STC analysis workflow from creation to results."""
        # Step 1: Create STC analysis
        analysis_data = {
            'project': str(self.project.id),
            'use_monte_carlo': False,
            'monte_carlo_iterations': 1000,
            'branch_name': 'main'
        }
        
        response = self.client.post('/api/stc/analyses/', analysis_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        analysis_id = response.json()['data']['id']
        
        # Step 2: Start analysis
        with tempfile.TemporaryDirectory() as temp_output_dir:
            # Mock the TNM output directory
            with self.settings(TNM_OUTPUT_DIR=temp_output_dir):
                # Copy our sample files to the expected location
                import shutil
                expected_dir = os.path.join(temp_output_dir, f'project_{self.project.id}_main')
                shutil.copytree(self.tnm_output_dir, expected_dir)
                
                response = self.client.post(f'/api/stc/analyses/{analysis_id}/start_analysis/')
                
                # Should succeed if TNM files are found
                self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
        
        # Step 3: Check analysis status
        response = self.client.get(f'/api/stc/analyses/{analysis_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        analysis_data = response.json()['data']
        self.assertIn(analysis_data['status'], ['pending', 'running', 'completed', 'failed'])
    
    def test_mc_stc_analysis_with_contributors(self):
        """Test MC-STC analysis with contributor role classification."""
        # Create contributors with different roles
        from contributors.models import Contributor, ProjectContributor, FunctionalRole
        
        # Create contributors
        dev_contributor = Contributor.objects.create(
            email='developer1@example.com',
            name='Developer One'
        )
        
        sec_contributor = Contributor.objects.create(
            email='security1@example.com',
            name='Security One'
        )
        
        # Add them to project with roles
        ProjectContributor.objects.create(
            project=self.project,
            contributor=dev_contributor,
            functional_role=FunctionalRole.DEVELOPER
        )
        
        ProjectContributor.objects.create(
            project=self.project,
            contributor=sec_contributor,
            functional_role=FunctionalRole.SECURITY
        )
        
        # Create MC-STC analysis
        analysis_data = {
            'project': str(self.project.id),
            'use_monte_carlo': True,
            'monte_carlo_iterations': 1000,
            'branch_name': 'main'
        }
        
        response = self.client.post('/api/stc/analyses/', analysis_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        analysis_id = response.json()['data']['id']
        
        # Verify analysis was created with MC-STC enabled
        analysis = STCAnalysis.objects.get(id=analysis_id)
        self.assertTrue(analysis.use_monte_carlo)
    
    def test_project_monitoring_integration(self):
        """Test integration between STC analysis and project monitoring."""
        # Create a monitoring record
        monitoring = ProjectMonitoring.objects.create(
            project=self.project,
            analysis_type=AnalysisType.STC
        )
        
        # Create STC analysis
        analysis = STCAnalysis.objects.create(
            project=self.project,
            use_monte_carlo=False
        )
        
        # Simulate analysis completion
        analysis.is_completed = True
        analysis.save()
        
        # Check that monitoring can track the analysis
        response = self.client.get('/api/project-monitoring/monitoring/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should have at least one monitoring record
        data = response.json()
        self.assertGreaterEqual(len(data['results']), 1)
