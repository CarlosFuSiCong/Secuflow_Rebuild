import numpy as np
from django.test import TestCase
from stc_analysis.services import STCService

class STCServiceTests(TestCase):
    def setUp(self):
        """Set up test cases"""
        self.service = STCService(project_id="test")
        
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

    def test_stc_calculation(self):
        """Test overall STC calculation"""
        # Test path graph
        stc_values = self.service.calculate_stc(self.path_graph)
        
        # In a path graph, middle node should have higher centrality
        self.assertGreater(float(stc_values['1']), float(stc_values['0']))
        self.assertGreater(float(stc_values['1']), float(stc_values['2']))
        
        # Test star graph
        stc_values = self.service.calculate_stc(self.star_graph)
        
        # In a star graph, center node (0) should have highest centrality
        center_value = float(stc_values['0'])
        for i in range(1, 4):
            self.assertGreater(center_value, float(stc_values[str(i)]))
            
        # Leaf nodes should have equal centrality
        self.assertAlmostEqual(float(stc_values['1']), float(stc_values['2']))
        self.assertAlmostEqual(float(stc_values['2']), float(stc_values['3']))

    def test_weighted_graph(self):
        """Test STC calculation for weighted graphs"""
        stc_values = self.service.calculate_stc(self.weighted_graph)
        
        # Node 0 should have highest centrality due to high weight connections
        node0_value = float(stc_values['0'])
        for i in range(1, 4):
            self.assertGreater(node0_value, float(stc_values[str(i)]))

    def test_invalid_input(self):
        """Test error handling for invalid inputs"""
        # Test non-symmetric matrix
        non_symmetric = np.array([
            [0, 1, 0],
            [0, 0, 1],
            [0, 0, 0]
        ])
        with self.assertRaises(ValueError):
            self.service.calculate_stc(non_symmetric)
            
        # Test empty matrix
        empty_matrix = np.array([])
        with self.assertRaises(ValueError):
            self.service.calculate_stc(empty_matrix)
