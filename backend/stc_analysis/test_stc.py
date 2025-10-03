import numpy as np
from django.test import TestCase
from stc_analysis.services import STCService, MCSTCService

class STCServiceTests(TestCase):
    def setUp(self):
        """Set up test cases"""
        self.service = STCService(project_id="test")
        
        # CR matrices (Collaboration Relations) for testing
        # These represent developer collaboration networks (symmetric matrices)
        
        # Test case 1: Simple path graph (3 nodes)
        # 0 -- 1 -- 2
        self.path_graph = np.array([
            [0, 1, 0],
            [1, 0, 1],
            [0, 1, 0]
        ])
        
        # Test case 2: Simple cycle graph (4 nodes)
        # 0 -- 1
        # |    |
        # 3 -- 2
        self.cycle_graph = np.array([
            [0, 1, 0, 1],
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [1, 0, 1, 0]
        ])
        
        # Test case 3: Star graph (4 nodes)
        # 1
        # |
        # 0 -- 2
        # |
        # 3
        self.star_graph = np.array([
            [0, 1, 1, 1],
            [1, 0, 0, 0],
            [1, 0, 0, 0],
            [1, 0, 0, 0]
        ])
        
        # Test case 4: Weighted graph
        # 0 -2- 1
        # | \   |
        # 1  3  1
        # |   \ |
        # 2 -1- 3
        self.weighted_graph = np.array([
            [0, 2, 1, 3],
            [2, 0, 0, 1],
            [1, 0, 0, 1],
            [3, 1, 1, 0]
        ])
        
        # Sample CA matrix (3 developers × 4 files)
        self.ca_matrix = np.array([
            [5, 3, 0, 2],  # Developer 0's contributions
            [2, 4, 3, 0],  # Developer 1's contributions
            [0, 1, 5, 4]   # Developer 2's contributions
        ])

    def test_kirchhoff_matrix(self):
        """Test Kirchhoff matrix calculation"""
        # Test for path graph
        k_matrix = self.service.calculate_kirchhoff_matrix(self.path_graph)
        expected = np.array([
            [1, -1, 0],
            [-1, 2, -1],
            [0, -1, 1]
        ])
        np.testing.assert_array_almost_equal(k_matrix, expected)
        
        # Test for cycle graph
        k_matrix = self.service.calculate_kirchhoff_matrix(self.cycle_graph)
        expected = np.array([
            [2, -1, 0, -1],
            [-1, 2, -1, 0],
            [0, -1, 2, -1],
            [-1, 0, -1, 2]
        ])
        np.testing.assert_array_almost_equal(k_matrix, expected)

    def test_spanning_tree_count(self):
        """Test spanning tree counting"""
        # Path graph should have exactly 1 spanning tree
        k_matrix = self.service.calculate_kirchhoff_matrix(self.path_graph)
        count = self.service.calculate_spanning_tree_count(k_matrix)
        self.assertAlmostEqual(count, 1.0)
        
        # Cycle graph should have exactly 4 spanning trees
        k_matrix = self.service.calculate_kirchhoff_matrix(self.cycle_graph)
        count = self.service.calculate_spanning_tree_count(k_matrix)
        self.assertAlmostEqual(count, 4.0)
        
        # Star graph should have exactly 3 spanning trees
        k_matrix = self.service.calculate_kirchhoff_matrix(self.star_graph)
        count = self.service.calculate_spanning_tree_count(k_matrix)
        self.assertAlmostEqual(count, 3.0)

    def test_edge_participation(self):
        """Test edge participation calculation"""
        # For path graph, each edge must participate in the only spanning tree
        k_matrix = self.service.calculate_kirchhoff_matrix(self.path_graph)
        participation = self.service.calculate_edge_participation(self.path_graph, k_matrix)
        
        # Check if edges (0,1) and (1,2) have participation = 1
        self.assertAlmostEqual(participation[0,1], 1.0)
        self.assertAlmostEqual(participation[1,2], 1.0)
        
        # Check symmetry
        self.assertAlmostEqual(participation[1,0], participation[0,1])
        self.assertAlmostEqual(participation[2,1], participation[1,2])

    def test_cr_matrix_calculation(self):
        """Test CR matrix calculation from CA matrix"""
        # Calculate CR = CA × CA^T
        cr_matrix = self.service.calculate_cr_matrix(self.ca_matrix)
        
        # Check dimensions (should be m × m, where m = number of developers)
        self.assertEqual(cr_matrix.shape, (3, 3))
        
        # Check symmetry
        self.assertTrue(np.allclose(cr_matrix, cr_matrix.T))
        
        # Check values are non-negative
        self.assertTrue(np.all(cr_matrix >= 0))
        
        # Manually verify one value: CR[0,1] = sum(CA[0,i] * CA[1,i] for all i)
        expected_cr_01 = np.dot(self.ca_matrix[0], self.ca_matrix[1])
        self.assertAlmostEqual(cr_matrix[0,1], expected_cr_01)

    def test_stc_from_cr(self):
        """Test STC calculation from CR matrix"""
        # Test path graph
        stc_values = self.service.calculate_stc_from_cr(self.path_graph)
        
        # In a path graph, middle node should have higher centrality
        self.assertGreater(float(stc_values['1']), float(stc_values['0']))
        self.assertGreater(float(stc_values['1']), float(stc_values['2']))
        
        # Test star graph
        stc_values = self.service.calculate_stc_from_cr(self.star_graph)
        
        # In a star graph, center node (0) should have highest centrality
        center_value = float(stc_values['0'])
        for i in range(1, 4):
            self.assertGreater(center_value, float(stc_values[str(i)]))
            
        # Leaf nodes should have equal centrality
        self.assertAlmostEqual(float(stc_values['1']), float(stc_values['2']))
        self.assertAlmostEqual(float(stc_values['2']), float(stc_values['3']))
    
    def test_stc_from_ca(self):
        """Test STC calculation from CA matrix (full workflow)"""
        # This tests the complete workflow: CA → CR → STC
        stc_values = self.service.calculate_stc_from_ca(self.ca_matrix)
        
        # Check that we get values for all developers
        self.assertEqual(len(stc_values), 3)
        
        # Check all values are non-negative
        for value in stc_values.values():
            self.assertGreaterEqual(float(value), 0.0)

    def test_weighted_graph(self):
        """Test STC calculation for weighted graphs"""
        stc_values = self.service.calculate_stc_from_cr(self.weighted_graph)
        
        # Node 0 should have highest centrality due to high weight connections
        node0_value = float(stc_values['0'])
        for i in range(1, 4):
            self.assertGreater(node0_value, float(stc_values[str(i)]))

    def test_invalid_input(self):
        """Test error handling for invalid inputs"""
        # Test non-symmetric CR matrix
        non_symmetric = np.array([
            [0, 1, 0],
            [0, 0, 1],
            [0, 0, 0]
        ])
        with self.assertRaises(ValueError):
            self.service.calculate_stc_from_cr(non_symmetric)
        
        # Test CR matrix with negative values
        negative_matrix = np.array([
            [0, -1, 0],
            [-1, 0, 1],
            [0, 1, 0]
        ])
        with self.assertRaises(ValueError):
            self.service.calculate_stc_from_cr(negative_matrix)


class MCSTCServiceTests(TestCase):
    """Test suite for MC-STC (Monte Carlo Spanning Tree Centrality) service"""
    
    def setUp(self):
        """Set up test data"""
        self.service = MCSTCService(project_id="test", iterations=100)
        
        # CR matrices for testing
        self.path_graph = np.array([
            [0, 1, 0],
            [1, 0, 1],
            [0, 1, 0]
        ])
        
        self.complete_graph = np.array([
            [0, 1, 1, 1],
            [1, 0, 1, 1],
            [1, 1, 0, 1],
            [1, 1, 1, 0]
        ])
        
        self.star_graph = np.array([
            [0, 1, 1, 1],
            [1, 0, 0, 0],
            [1, 0, 0, 0],
            [1, 0, 0, 0]
        ])
        
        # Sample CA matrix
        self.ca_matrix = np.array([
            [5, 3, 0, 2],
            [2, 4, 3, 0],
            [0, 1, 5, 4]
        ])
    
    def test_get_edges_from_matrix(self):
        """Test edge extraction from CR matrix"""
        edges = self.service._get_edges_from_matrix(self.path_graph)
        
        # Path graph should have 2 edges
        self.assertEqual(len(edges), 2)
        
        # Check edges
        edge_pairs = {(e[0], e[1]) for e in edges}
        self.assertIn((0, 1), edge_pairs)
        self.assertIn((1, 2), edge_pairs)
    
    def test_union_find(self):
        """Test Union-Find data structure"""
        parent = {0: 0, 1: 1, 2: 2}
        rank = {0: 0, 1: 0, 2: 0}
        
        # Union nodes 0 and 1
        result = self.service._union(parent, rank, 0, 1)
        self.assertTrue(result)
        
        # Find parents
        root_0 = self.service._find_parent(parent, 0)
        root_1 = self.service._find_parent(parent, 1)
        self.assertEqual(root_0, root_1)
        
        # Try to union again (should fail)
        result = self.service._union(parent, rank, 0, 1)
        self.assertFalse(result)
    
    def test_generate_random_spanning_tree(self):
        """Test random spanning tree generation"""
        tree = self.service.generate_random_spanning_tree(self.complete_graph)
        
        # Check tree properties
        self.assertEqual(tree.shape, (4, 4))
        self.assertTrue(np.allclose(tree, tree.T))  # Symmetric
        
        # A spanning tree of 4 nodes should have 3 edges
        edge_count = np.sum(tree > 0) / 2  # Divide by 2 for undirected graph
        self.assertEqual(edge_count, 3)
    
    def test_generate_spanning_tree_empty_graph(self):
        """Test spanning tree generation for graph with no edges"""
        empty_graph = np.zeros((3, 3))
        tree = self.service.generate_random_spanning_tree(empty_graph)
        
        # Should return empty tree
        self.assertTrue(np.allclose(tree, np.zeros((3, 3))))
    
    def test_calculate_node_importance_in_tree(self):
        """Test node importance calculation in a tree"""
        # Use path graph as a simple tree
        importance = self.service.calculate_node_importance_in_tree(self.path_graph)
        
        # Should have 3 nodes
        self.assertEqual(len(importance), 3)
        
        # All importance values should sum to 1 (normalized)
        total = sum(importance.values())
        self.assertAlmostEqual(total, 1.0, places=7)
        
        # Middle node (1) should have higher importance
        self.assertGreater(float(importance['1']), float(importance['0']))
        self.assertGreater(float(importance['1']), float(importance['2']))
    
    def test_mc_stc_from_cr(self):
        """Test MC-STC calculation from CR matrix"""
        mc_stc_values = self.service.calculate_mc_stc_from_cr(self.star_graph)
        
        # Should have 4 nodes
        self.assertEqual(len(mc_stc_values), 4)
        
        # All values should be non-negative
        for value in mc_stc_values.values():
            self.assertGreaterEqual(float(value), 0.0)
        
        # Center node (0) should have highest centrality
        center_value = float(mc_stc_values['0'])
        for i in range(1, 4):
            self.assertGreater(center_value, float(mc_stc_values[str(i)]))
    
    def test_mc_stc_from_ca(self):
        """Test MC-STC calculation from CA matrix"""
        mc_stc_values = self.service.calculate_mc_stc_from_ca(self.ca_matrix)
        
        # Should have 3 developers
        self.assertEqual(len(mc_stc_values), 3)
        
        # All values should be non-negative
        for value in mc_stc_values.values():
            self.assertGreaterEqual(float(value), 0.0)
    
    def test_mc_stc_consistency(self):
        """Test that MC-STC values are consistent across runs"""
        # Run MC-STC twice with the same seed
        service1 = MCSTCService(project_id="test", iterations=50)
        service1.random_state = np.random.RandomState(42)
        result1 = service1.calculate_mc_stc_from_cr(self.complete_graph)
        
        service2 = MCSTCService(project_id="test", iterations=50)
        service2.random_state = np.random.RandomState(42)
        result2 = service2.calculate_mc_stc_from_cr(self.complete_graph)
        
        # Results should be identical with same seed
        for key in result1:
            self.assertAlmostEqual(result1[key], result2[key], places=7)
    
    def test_mc_stc_empty_graph(self):
        """Test MC-STC on graph with no edges"""
        empty_graph = np.zeros((3, 3))
        mc_stc_values = self.service.calculate_mc_stc_from_cr(empty_graph)
        
        # All values should be zero
        for value in mc_stc_values.values():
            self.assertEqual(float(value), 0.0)
    
    def test_mc_stc_invalid_input(self):
        """Test error handling for invalid inputs"""
        # Test non-symmetric CR matrix
        non_symmetric = np.array([
            [0, 1, 0],
            [0, 0, 1],
            [0, 0, 0]
        ])
        with self.assertRaises(ValueError):
            self.service.calculate_mc_stc_from_cr(non_symmetric)
