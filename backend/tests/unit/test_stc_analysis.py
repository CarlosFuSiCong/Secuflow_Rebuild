"""
Unit tests for STC analysis services and models.
"""

import numpy as np
from django.test import TestCase
from stc_analysis.services import STCService, MCSTCService
from stc_analysis.models import STCAnalysis
from tests.conftest import BaseTestCase


class STCServiceTests(TestCase):
    """Test suite for STC (Socio-Technical Congruence) service"""
    
    def setUp(self):
        """Set up test cases"""
        self.service = STCService(project_id="test", threshold=0)
        
        # Sample matrices for testing
        # 3 developers × 4 files
        self.assignment_matrix = np.array([
            [5, 3, 0, 2],  # Developer 0
            [2, 4, 3, 0],  # Developer 1
            [0, 1, 5, 4]   # Developer 2
        ])
        
        # 4 files × 4 files dependency
        self.dependency_matrix = np.array([
            [0, 1, 0, 1],  # File 0 depends on files 1, 3
            [1, 0, 1, 0],  # File 1 depends on files 0, 2
            [0, 1, 0, 1],  # File 2 depends on files 1, 3
            [1, 0, 1, 0]   # File 3 depends on files 0, 2
        ])
        
        # File modifiers for CA matrix calculation
        self.file_modifiers = {
            '0': {'0', '1'},       # File 0 modified by devs 0, 1
            '1': {'0', '1', '2'},  # File 1 modified by all
            '2': {'1', '2'},       # File 2 modified by devs 1, 2
            '3': {'0', '2'}        # File 3 modified by devs 0, 2
        }
        
        self.all_users = ['0', '1', '2']
    
    def test_cr_matrix_calculation(self):
        """Test CR (Coordination Requirements) matrix calculation"""
        cr_matrix = self.service.calculate_cr_from_assignment_dependency(
            self.assignment_matrix, self.dependency_matrix
        )
        
        # Verify matrix shape
        self.assertEqual(cr_matrix.shape, (3, 3))
        
        # Verify matrix is symmetric
        np.testing.assert_array_equal(cr_matrix, cr_matrix.T)
        
        # Verify diagonal is zero (no self-coordination)
        np.testing.assert_array_equal(np.diag(cr_matrix), np.zeros(3))
    
    def test_ca_matrix_calculation(self):
        """Test CA (Coordination Actuals) matrix calculation"""
        ca_matrix = self.service.calculate_ca_from_file_modifiers(
            self.file_modifiers, self.all_users
        )
        
        # Verify matrix shape
        self.assertEqual(ca_matrix.shape, (3, 3))
        
        # Verify matrix is symmetric
        np.testing.assert_array_equal(ca_matrix, ca_matrix.T)
        
        # Verify diagonal is zero (no self-coordination)
        np.testing.assert_array_equal(np.diag(ca_matrix), np.zeros(3))
    
    def test_stc_calculation(self):
        """Test STC value calculation"""
        cr_matrix = np.array([
            [0, 2, 1],
            [2, 0, 3],
            [1, 3, 0]
        ])
        
        ca_matrix = np.array([
            [0, 1, 1],
            [1, 0, 2],
            [1, 2, 0]
        ])
        
        stc_value = self.service.calculate_stc(cr_matrix, ca_matrix)
        
        # STC = |CR ∩ CA| / |CR|
        # Count actual intersections and requirements
        mask_no_diagonal = ~np.eye(len(cr_matrix), dtype=bool)
        intersection_count = np.sum((cr_matrix > 0) & (ca_matrix > 0) & mask_no_diagonal)
        required_count = np.sum((cr_matrix > 0) & mask_no_diagonal)
        expected_stc = intersection_count / required_count if required_count > 0 else 0.0
        self.assertAlmostEqual(stc_value, expected_stc, places=3)


class MCSTCServiceTests(TestCase):
    """Test suite for MC-STC (Multi-Class STC) service"""
    
    def setUp(self):
        """Set up test cases"""
        self.service = MCSTCService(project_id="test", threshold=0)
        
        # Sample data for MC-STC testing
        self.all_users = ['dev1', 'dev2', 'sec1', 'sec2']
        self.security_users = {'sec1', 'sec2'}
        self.developer_users = {'dev1', 'dev2'}
        
        # Sample CR and CA matrices
        self.cr_matrix = np.array([
            [0, 1, 2, 1],  # dev1
            [1, 0, 1, 2],  # dev2
            [2, 1, 0, 1],  # sec1
            [1, 2, 1, 0]   # sec2
        ])
        
        self.ca_matrix = np.array([
            [0, 1, 1, 0],  # dev1
            [1, 0, 0, 1],  # dev2
            [1, 0, 0, 1],  # sec1
            [0, 1, 1, 0]   # sec2
        ])
    
    def test_filter_inter_class_edges(self):
        """Test filtering inter-class coordination edges"""
        # Create class assignments
        class_assignments = {
            'dev1': 'developer',
            'dev2': 'developer', 
            'sec1': 'security',
            'sec2': 'security'
        }
        
        inter_cr = self.service.filter_inter_class_edges(
            self.cr_matrix, self.all_users, class_assignments
        )
        
        # Verify that intra-class edges are zeroed out
        # dev1-dev2 should be 0
        self.assertEqual(inter_cr[0, 1], 0)
        self.assertEqual(inter_cr[1, 0], 0)
        # sec1-sec2 should be 0  
        self.assertEqual(inter_cr[2, 3], 0)
        self.assertEqual(inter_cr[3, 2], 0)
    
    def test_calculate_2c_stc(self):
        """Test 2C-STC calculation"""
        stc_value, filtered_cr, filtered_ca = self.service.calculate_2c_stc(
            self.cr_matrix, self.ca_matrix, self.all_users,
            self.security_users, self.developer_users
        )
        
        # Should return a value between 0 and 1
        self.assertGreaterEqual(stc_value, 0.0)
        self.assertLessEqual(stc_value, 1.0)
        
        # Filtered matrices should have same shape as original
        self.assertEqual(filtered_cr.shape, self.cr_matrix.shape)
        self.assertEqual(filtered_ca.shape, self.ca_matrix.shape)


class STCAnalysisModelTests(BaseTestCase):
    """Test STCAnalysis model"""
    
    def test_create_stc_analysis(self):
        """Test creating an STC analysis"""
        analysis = STCAnalysis.objects.create(
            project=self.project,
            use_monte_carlo=False,
            monte_carlo_iterations=1000
        )
        
        self.assertEqual(analysis.project, self.project)
        self.assertFalse(analysis.is_completed)
        self.assertFalse(analysis.use_monte_carlo)
        self.assertEqual(analysis.monte_carlo_iterations, 1000)
        self.assertIsNone(analysis.results_file)
        self.assertIsNone(analysis.error_message)
    
    def test_create_monte_carlo_analysis(self):
        """Test creating a Monte Carlo STC analysis"""
        analysis = STCAnalysis.objects.create(
            project=self.project,
            use_monte_carlo=True,
            monte_carlo_iterations=5000
        )
        
        self.assertTrue(analysis.use_monte_carlo)
        self.assertEqual(analysis.monte_carlo_iterations, 5000)
    
    def test_analysis_string_representation(self):
        """Test analysis string representation"""
        analysis = STCAnalysis.objects.create(
            project=self.project,
            use_monte_carlo=False
        )
        
        # String representation includes date, so just check it contains project name
        analysis_str = str(analysis)
        self.assertIn(self.project.name, analysis_str)
        self.assertIn("STC Analysis for", analysis_str)
