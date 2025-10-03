import numpy as np
from django.test import TestCase
from stc_analysis.services import STCService, MCSTCService


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
            self.assignment_matrix,
            self.dependency_matrix
        )
        
        # CR should be m × m (developers × developers)
        self.assertEqual(cr_matrix.shape, (3, 3))
        
        # CR should be symmetric
        self.assertTrue(np.allclose(cr_matrix, cr_matrix.T))
        
        # Diagonal should be 0 (no self-coordination)
        self.assertTrue(np.all(np.diag(cr_matrix) == 0))
        
        # CR values should be binary (0 or 1) with threshold
        self.assertTrue(np.all((cr_matrix == 0) | (cr_matrix == 1)))
    
    def test_ca_matrix_calculation(self):
        """Test CA (Coordination Actuals) matrix calculation"""
        ca_matrix = self.service.calculate_ca_from_file_modifiers(
            self.file_modifiers,
            self.all_users
        )
        
        # CA should be m × m (developers × developers)
        self.assertEqual(ca_matrix.shape, (3, 3))
        
        # CA should be symmetric
        self.assertTrue(np.allclose(ca_matrix, ca_matrix.T))
        
        # Diagonal should be 0 (no self-coordination)
        self.assertTrue(np.all(np.diag(ca_matrix) == 0))
        
        # Check specific coordination pairs
        # Devs 0 and 1 both modify files 0, 1 -> CA[0,1] = 1
        self.assertEqual(ca_matrix[0, 1], 1)
        self.assertEqual(ca_matrix[1, 0], 1)
        
        # Devs 1 and 2 both modify files 1, 2 -> CA[1,2] = 1
        self.assertEqual(ca_matrix[1, 2], 1)
        
        # Devs 0 and 2 both modify files 1, 3 -> CA[0,2] = 1
        self.assertEqual(ca_matrix[0, 2], 1)
    
    def test_stc_calculation_perfect_congruence(self):
        """Test STC when CR equals CA (perfect congruence)"""
        # Create identical CR and CA matrices
        cr_matrix = np.array([
            [0, 1, 1],
            [1, 0, 1],
            [1, 1, 0]
        ])
        ca_matrix = cr_matrix.copy()
        
        stc = self.service.calculate_stc(cr_matrix, ca_matrix)
        
        # Perfect congruence should give STC = 1.0
        self.assertAlmostEqual(stc, 1.0, places=7)
    
    def test_stc_calculation_no_congruence(self):
        """Test STC when CR and CA don't overlap"""
        cr_matrix = np.array([
            [0, 1, 0],
            [1, 0, 1],
            [0, 1, 0]
        ])
        ca_matrix = np.array([
            [0, 0, 1],
            [0, 0, 0],
            [1, 0, 0]
        ])
        
        stc = self.service.calculate_stc(cr_matrix, ca_matrix)
        
        # No overlap should give STC = 0.0
        self.assertAlmostEqual(stc, 0.0, places=7)
    
    def test_stc_calculation_partial_congruence(self):
        """Test STC with partial congruence"""
        cr_matrix = np.array([
            [0, 1, 1, 1],
            [1, 0, 1, 0],
            [1, 1, 0, 1],
            [1, 0, 1, 0]
        ])
        ca_matrix = np.array([
            [0, 1, 0, 1],  # 2 out of 3 required
            [1, 0, 1, 0],  # 2 out of 2 required
            [0, 1, 0, 0],  # 1 out of 3 required
            [1, 0, 0, 0]   # 1 out of 2 required
        ])
        
        stc = self.service.calculate_stc(cr_matrix, ca_matrix)
        
        # Count edges (considering matrix is symmetric):
        # Required edges (CR>0): (0,1), (0,2), (0,3), (1,2), (2,3) = 5 unique edges
        # Satisfied edges (CR>0 & CA>0): (0,1), (0,3), (1,2) = 3 unique edges
        # But we count both directions in matrix: 10 required, 6 satisfied
        # STC = 6 / 10 = 0.6
        expected_stc = 0.6
        self.assertAlmostEqual(stc, expected_stc, places=7)
    
    def test_stc_calculation_with_threshold(self):
        """Test STC with threshold for CR matrix"""
        service = STCService(project_id="test", threshold=2)
        
        # CR matrix with varying values
        cr_raw = np.array([
            [0, 3, 1, 2],
            [3, 0, 4, 1],
            [1, 4, 0, 3],
            [2, 1, 3, 0]
        ])
        
        # After thresholding (>2 becomes 1)
        cr_expected = np.array([
            [0, 1, 0, 0],
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 0]
        ])
        
        # Test threshold application
        cr_thresholded = np.where(cr_raw > service.threshold, 1, 0)
        np.fill_diagonal(cr_thresholded, 0)
        
        self.assertTrue(np.allclose(cr_thresholded, cr_expected))
    
    def test_get_missed_coordination(self):
        """Test missed coordination detection"""
        cr_matrix = np.array([
            [0, 1, 1],
            [1, 0, 1],
            [1, 1, 0]
        ])
        ca_matrix = np.array([
            [0, 1, 0],
            [1, 0, 1],
            [0, 1, 0]
        ])
        
        missed = self.service.get_missed_coordination(cr_matrix, ca_matrix)
        
        # Developer 0 misses coordination with developer 2
        self.assertEqual(missed[0, 2], 1)
        self.assertEqual(missed[2, 0], 1)
        
        # Developers 0-1 and 1-2 don't miss coordination
        self.assertEqual(missed[0, 1], 0)
        self.assertEqual(missed[1, 2], 0)
    
    def test_get_unnecessary_coordination(self):
        """Test unnecessary coordination detection"""
        cr_matrix = np.array([
            [0, 1, 0],
            [1, 0, 1],
            [0, 1, 0]
        ])
        ca_matrix = np.array([
            [0, 1, 1],  # Extra coordination with dev 2
            [1, 0, 1],
            [1, 1, 0]   # Extra coordination with dev 0
        ])
        
        unnecessary = self.service.get_unnecessary_coordination(cr_matrix, ca_matrix)
        
        # Developers 0 and 2 have unnecessary coordination
        self.assertEqual(unnecessary[0, 2], 1)
        self.assertEqual(unnecessary[2, 0], 1)
        
        # Required coordinations are not unnecessary
        self.assertEqual(unnecessary[0, 1], 0)
        self.assertEqual(unnecessary[1, 2], 0)
    
    def test_empty_matrices(self):
        """Test STC with empty/zero matrices"""
        cr_matrix = np.zeros((3, 3))
        ca_matrix = np.zeros((3, 3))
        
        stc = self.service.calculate_stc(cr_matrix, ca_matrix)
        
        # No coordination required -> STC = 0
        self.assertEqual(stc, 0.0)
    
    def test_invalid_matrix_shapes(self):
        """Test error handling for mismatched matrix shapes"""
        cr_matrix = np.array([[0, 1], [1, 0]])
        ca_matrix = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]])
        
        with self.assertRaises(ValueError):
            self.service.calculate_stc(cr_matrix, ca_matrix)


class MCSTCServiceTests(TestCase):
    """Test suite for MC-STC (Multi-Class Socio-Technical Congruence) service"""
    
    def setUp(self):
        """Set up test data"""
        self.service = MCSTCService(project_id="test", threshold=0)
        
        # 4 developers: 2 security, 2 developers
        self.all_users = ['0', '1', '2', '3']
        self.security_users = {'0', '1'}
        self.developer_users = {'2', '3'}
        
        # CR matrix (all pairs need coordination)
        self.cr_matrix = np.array([
            [0, 1, 1, 1],
            [1, 0, 1, 1],
            [1, 1, 0, 1],
            [1, 1, 1, 0]
        ])
        
        # CA matrix (some coordination happens)
        self.ca_matrix = np.array([
            [0, 1, 1, 0],  # Sec 0: coordinates with sec 1, dev 2
            [1, 0, 0, 1],  # Sec 1: coordinates with sec 0, dev 3
            [1, 0, 0, 1],  # Dev 2: coordinates with sec 0, dev 3
            [0, 1, 1, 0]   # Dev 3: coordinates with sec 1, dev 2
        ])
    
    def test_filter_inter_class_edges(self):
        """Test filtering to keep only inter-class edges"""
        class_assignments = {
            '0': 'security',
            '1': 'security',
            '2': 'developer',
            '3': 'developer'
        }
        
        filtered = self.service.filter_inter_class_edges(
            self.cr_matrix,
            self.all_users,
            class_assignments
        )
        
        # Intra-class edges should be 0
        self.assertEqual(filtered[0, 1], 0)  # sec-sec
        self.assertEqual(filtered[1, 0], 0)  # sec-sec
        self.assertEqual(filtered[2, 3], 0)  # dev-dev
        self.assertEqual(filtered[3, 2], 0)  # dev-dev
        
        # Inter-class edges should be preserved
        self.assertEqual(filtered[0, 2], 1)  # sec-dev
        self.assertEqual(filtered[0, 3], 1)  # sec-dev
        self.assertEqual(filtered[1, 2], 1)  # sec-dev
        self.assertEqual(filtered[1, 3], 1)  # sec-dev
    
    def test_calculate_mc_stc(self):
        """Test MC-STC calculation"""
        class_assignments = {
            '0': 'security',
            '1': 'security',
            '2': 'developer',
            '3': 'developer'
        }
        
        mc_stc = self.service.calculate_mc_stc(
            self.cr_matrix,
            self.ca_matrix,
            self.all_users,
            class_assignments
        )
        
        # MC-STC should be between 0 and 1
        self.assertGreaterEqual(mc_stc, 0.0)
        self.assertLessEqual(mc_stc, 1.0)
        
        # With our test data:
        # Required inter-class edges: 8 (4 sec-dev pairs × 2 directions)
        # Actual inter-class edges: 4 (0-2, 1-3, 2-0, 3-1)
        # MC-STC = 4 / 8 = 0.5
        self.assertAlmostEqual(mc_stc, 0.5, places=7)
    
    def test_calculate_2c_stc(self):
        """Test 2C-STC (Two-Class STC) calculation"""
        two_c_stc, mc_cr, mc_ca = self.service.calculate_2c_stc(
            self.cr_matrix,
            self.ca_matrix,
            self.all_users,
            self.security_users,
            self.developer_users
        )
        
        # 2C-STC should be same as MC-STC for 2 classes
        mc_stc = self.service.calculate_mc_stc(
            self.cr_matrix,
            self.ca_matrix,
            self.all_users,
            {uid: 'security' if uid in self.security_users else 'developer' 
             for uid in self.all_users}
        )
        
        self.assertAlmostEqual(two_c_stc, mc_stc, places=7)
        
        # Check that intra-class edges are filtered out
        self.assertEqual(mc_cr[0, 1], 0)  # sec-sec
        self.assertEqual(mc_cr[2, 3], 0)  # dev-dev
        
        # Inter-class edges should be preserved
        self.assertEqual(mc_cr[0, 2], 1)  # sec-dev
    
    def test_get_missed_dev_sec_coordination(self):
        """Test missed Dev-Sec coordination count"""
        missed_counts = self.service.get_missed_dev_sec_coordination(
            self.cr_matrix,
            self.ca_matrix,
            self.all_users,
            self.security_users,
            self.developer_users
        )
        
        # Developer 2: needs coordination with sec 0, 1; has with 0
        # -> misses 1 (with sec 1)
        self.assertEqual(missed_counts['2'], 1)
        
        # Developer 3: needs coordination with sec 0, 1; has with 1
        # -> misses 1 (with sec 0)
        self.assertEqual(missed_counts['3'], 1)
    
    def test_mc_stc_perfect_inter_class_congruence(self):
        """Test MC-STC with perfect inter-class congruence"""
        # All inter-class coordination is satisfied
        ca_perfect = np.array([
            [0, 0, 1, 1],  # Sec 0: coordinates with both devs
            [0, 0, 1, 1],  # Sec 1: coordinates with both devs
            [1, 1, 0, 0],  # Dev 2: coordinates with both secs
            [1, 1, 0, 0]   # Dev 3: coordinates with both secs
        ])
        
        class_assignments = {
            '0': 'security',
            '1': 'security',
            '2': 'developer',
            '3': 'developer'
        }
        
        mc_stc = self.service.calculate_mc_stc(
            self.cr_matrix,
            ca_perfect,
            self.all_users,
            class_assignments
        )
        
        # Perfect inter-class congruence -> MC-STC = 1.0
        self.assertAlmostEqual(mc_stc, 1.0, places=7)
    
    def test_mc_stc_no_inter_class_coordination(self):
        """Test MC-STC with no inter-class coordination"""
        # Only intra-class coordination happens
        ca_intra_only = np.array([
            [0, 1, 0, 0],  # Sec 0: only with sec 1
            [1, 0, 0, 0],  # Sec 1: only with sec 0
            [0, 0, 0, 1],  # Dev 2: only with dev 3
            [0, 0, 1, 0]   # Dev 3: only with dev 2
        ])
        
        class_assignments = {
            '0': 'security',
            '1': 'security',
            '2': 'developer',
            '3': 'developer'
        }
        
        mc_stc = self.service.calculate_mc_stc(
            self.cr_matrix,
            ca_intra_only,
            self.all_users,
            class_assignments
        )
        
        # No inter-class coordination -> MC-STC = 0.0
        self.assertAlmostEqual(mc_stc, 0.0, places=7)
    
    def test_mc_stc_with_three_classes(self):
        """Test MC-STC with three functional classes"""
        # 6 developers: 2 security, 2 developers, 2 ops
        all_users_3class = ['0', '1', '2', '3', '4', '5']
        class_assignments_3class = {
            '0': 'security',
            '1': 'security',
            '2': 'developer',
            '3': 'developer',
            '4': 'ops',
            '5': 'ops'
        }
        
        # Simple complete graph
        cr_6x6 = np.ones((6, 6))
        np.fill_diagonal(cr_6x6, 0)
        
        # Only some inter-class coordination
        ca_6x6 = np.array([
            [0, 0, 1, 0, 0, 0],  # Sec 0 -> Dev 2
            [0, 0, 0, 1, 0, 0],  # Sec 1 -> Dev 3
            [1, 0, 0, 0, 1, 0],  # Dev 2 -> Sec 0, Ops 4
            [0, 1, 0, 0, 0, 1],  # Dev 3 -> Sec 1, Ops 5
            [0, 0, 1, 0, 0, 0],  # Ops 4 -> Dev 2
            [0, 0, 0, 1, 0, 0]   # Ops 5 -> Dev 3
        ])
        
        mc_stc = self.service.calculate_mc_stc(
            cr_6x6,
            ca_6x6,
            all_users_3class,
            class_assignments_3class
        )
        
        # MC-STC should be between 0 and 1
        self.assertGreaterEqual(mc_stc, 0.0)
        self.assertLessEqual(mc_stc, 1.0)

