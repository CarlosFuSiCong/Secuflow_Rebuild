import numpy as np
from typing import Dict, List, Optional, Tuple, Set
from scipy import linalg
from stc_analysis.models import STCAnalysis
import random

class STCService:
    """Service for STC (Spanning Tree Centrality) calculations
    
    STC uses:
    - CA (Contribution Assignment) Matrix: developers × files contribution matrix
    - CR (Collaboration Relations) Matrix: CR = CA × CA^T, represents developer collaboration network
    
    The STC algorithm operates on the CR matrix (developer collaboration network).
    """
    
    def __init__(self, project_id: str):
        self.project_id = project_id
    
    def calculate_cr_matrix(self, ca_matrix: np.ndarray) -> np.ndarray:
        """Calculate CR (Collaboration Relations) matrix from CA matrix
        
        CR = CA × CA^T
        
        Args:
            ca_matrix: Contribution Assignment matrix (m × n), where:
                       m = number of developers
                       n = number of files
        
        Returns:
            CR matrix (m × m), representing collaboration strength between developers
        """
        # Calculate CR = CA × CA^T
        cr_matrix = np.dot(ca_matrix, ca_matrix.T)
        return cr_matrix
        
    def calculate_kirchhoff_matrix(self, adjacency_matrix: np.ndarray) -> np.ndarray:
        """Calculate Kirchhoff matrix (Laplacian matrix) from CR matrix
        
        The Kirchhoff matrix (also known as Laplacian matrix) is calculated as:
        L = D - A, where:
        - D is the degree matrix (diagonal matrix with vertex degrees)
        - A is the adjacency matrix (CR matrix in STC context - collaboration network)
        
        Args:
            adjacency_matrix: CR matrix representing developer collaboration network
        
        Returns:
            Kirchhoff (Laplacian) matrix
        """
        # Calculate degree matrix (sum of each row)
        degrees = np.sum(adjacency_matrix, axis=1)
        degree_matrix = np.diag(degrees)
        
        # Calculate Kirchhoff matrix
        kirchhoff_matrix = degree_matrix - adjacency_matrix
        
        return kirchhoff_matrix
    
    def calculate_cofactor(self, matrix: np.ndarray, i: int, j: int) -> float:
        """Calculate cofactor of matrix element (i,j)"""
        # Remove i-th row and j-th column
        submatrix = np.delete(np.delete(matrix, i, 0), j, 1)
        # Calculate determinant of submatrix
        return linalg.det(submatrix)
    
    def calculate_spanning_tree_count(self, kirchhoff_matrix: np.ndarray) -> float:
        """Calculate the total number of spanning trees using Kirchhoff's theorem
        
        According to Kirchhoff's theorem, the number of spanning trees is equal to
        any cofactor of the Laplacian matrix.
        """
        # We use the (0,0) cofactor by convention
        return self.calculate_cofactor(kirchhoff_matrix, 0, 0)
    
    def calculate_edge_participation(self, adjacency_matrix: np.ndarray, 
                                   kirchhoff_matrix: np.ndarray) -> np.ndarray:
        """Calculate the participation of each edge in spanning trees
        
        Args:
            adjacency_matrix: CR matrix (collaboration network adjacency matrix)
            kirchhoff_matrix: Kirchhoff (Laplacian) matrix
        
        Returns:
            Edge participation matrix
        """
        n = len(adjacency_matrix)
        edge_participation = np.zeros_like(adjacency_matrix, dtype=float)
        
        for i in range(n):
            for j in range(i+1, n):
                if adjacency_matrix[i,j] > 0:
                    # Calculate participation using the formula:
                    # P(e) = w(e) * K(i,i) * K(j,j) - w(e) * K(i,j) * K(j,i)
                    # where K is the Kirchhoff matrix and w(e) is the edge weight
                    weight = adjacency_matrix[i,j]
                    participation = (weight * kirchhoff_matrix[i,i] * kirchhoff_matrix[j,j] - 
                                   weight * kirchhoff_matrix[i,j] * kirchhoff_matrix[j,i])
                    edge_participation[i,j] = participation
                    edge_participation[j,i] = participation
                    
        return edge_participation
        
    def calculate_stc_from_ca(self, ca_matrix: np.ndarray) -> Dict[str, float]:
        """Calculate STC values from CA (Contribution Assignment) matrix
        
        Steps:
        1. Calculate CR matrix (collaboration network) from CA matrix
        2. Calculate STC on the CR matrix
        
        Args:
            ca_matrix: Contribution Assignment matrix (m × n)
        
        Returns:
            Dictionary mapping developer index to STC value
        """
        # Calculate CR matrix (developer collaboration network)
        cr_matrix = self.calculate_cr_matrix(ca_matrix)
        
        # Calculate STC on CR matrix
        return self.calculate_stc_from_cr(cr_matrix)
    
    def calculate_stc_from_cr(self, cr_matrix: np.ndarray) -> Dict[str, float]:
        """Calculate STC values from CR (Collaboration Relations) matrix
        
        Steps:
        1. Calculate Kirchhoff matrix
        2. Calculate total number of spanning trees
        3. Calculate edge participation in spanning trees
        4. Calculate node STC values
        
        Args:
            cr_matrix: Collaboration Relations matrix (m × m), must be symmetric
        
        Returns:
            Dictionary mapping developer index to STC value
        """
        # Ensure matrix is symmetric
        if not np.allclose(cr_matrix, cr_matrix.T):
            raise ValueError("CR matrix must be symmetric")
        
        # Ensure matrix is non-negative
        if np.any(cr_matrix < 0):
            raise ValueError("CR matrix must contain non-negative values")
            
        # Calculate Kirchhoff matrix
        kirchhoff_matrix = self.calculate_kirchhoff_matrix(cr_matrix)
        
        # Calculate total number of spanning trees
        total_trees = self.calculate_spanning_tree_count(kirchhoff_matrix)
        
        if total_trees <= 0:
            # If no spanning trees, return zero STC for all nodes
            n = len(cr_matrix)
            return {str(i): 0.0 for i in range(n)}
        
        # Calculate edge participation
        edge_participation = self.calculate_edge_participation(cr_matrix, kirchhoff_matrix)
        
        # Calculate node STC values
        n = len(cr_matrix)
        stc_values = {}
        
        for i in range(n):
            # STC of a node is the sum of participation ratios of its incident edges
            node_participation = np.sum(edge_participation[i,:])
            stc_values[str(i)] = node_participation / total_trees
            
        return stc_values

class MCSTCService(STCService):
    """Service for MC-STC (Monte Carlo Spanning Tree Centrality) calculations
    
    MC-STC uses Monte Carlo sampling to estimate STC values by:
    1. Generating random spanning trees from the collaboration network
    2. Computing node importance in each sampled tree
    3. Averaging across all samples to get final STC estimates
    """
    
    def __init__(self, project_id: str, iterations: int = 1000):
        super().__init__(project_id)
        self.iterations = iterations
        self.random_state = np.random.RandomState()
    
    def _get_edges_from_matrix(self, cr_matrix: np.ndarray) -> List[Tuple[int, int, float]]:
        """Extract edges from CR matrix
        
        Args:
            cr_matrix: Collaboration Relations matrix
            
        Returns:
            List of (node_i, node_j, weight) tuples
        """
        edges = []
        n = len(cr_matrix)
        for i in range(n):
            for j in range(i + 1, n):
                if cr_matrix[i, j] > 0:
                    edges.append((i, j, cr_matrix[i, j]))
        return edges
    
    def _find_parent(self, parent: Dict[int, int], node: int) -> int:
        """Find root parent for Union-Find algorithm"""
        if parent[node] != node:
            parent[node] = self._find_parent(parent, parent[node])
        return parent[node]
    
    def _union(self, parent: Dict[int, int], rank: Dict[int, int], x: int, y: int) -> bool:
        """Union operation for Union-Find algorithm
        
        Returns:
            True if union was performed, False if nodes already in same set
        """
        root_x = self._find_parent(parent, x)
        root_y = self._find_parent(parent, y)
        
        if root_x == root_y:
            return False
        
        # Union by rank
        if rank[root_x] < rank[root_y]:
            parent[root_x] = root_y
        elif rank[root_x] > rank[root_y]:
            parent[root_y] = root_x
        else:
            parent[root_y] = root_x
            rank[root_x] += 1
        
        return True
        
    def generate_random_spanning_tree(self, cr_matrix: np.ndarray) -> np.ndarray:
        """Generate random spanning tree using randomized Kruskal's algorithm
        
        Uses probability sampling based on edge weights to generate
        a random spanning tree from the collaboration network.
        
        Args:
            cr_matrix: Collaboration Relations matrix (m × m)
            
        Returns:
            Adjacency matrix of the random spanning tree
        """
        n = len(cr_matrix)
        edges = self._get_edges_from_matrix(cr_matrix)
        
        if not edges:
            # No edges, return empty tree
            return np.zeros_like(cr_matrix)
        
        # Convert edges to probabilities based on weights
        weights = np.array([w for _, _, w in edges])
        probabilities = weights / weights.sum() if weights.sum() > 0 else np.ones(len(edges)) / len(edges)
        
        # Shuffle edges with probability proportional to weights
        edge_indices = self.random_state.choice(
            len(edges), 
            size=len(edges), 
            replace=False, 
            p=probabilities
        )
        
        # Initialize Union-Find structure
        parent = {i: i for i in range(n)}
        rank = {i: 0 for i in range(n)}
        
        # Build spanning tree using randomized Kruskal's algorithm
        tree_edges = []
        for idx in edge_indices:
            i, j, weight = edges[idx]
            if self._union(parent, rank, i, j):
                tree_edges.append((i, j, weight))
                if len(tree_edges) == n - 1:
                    break
        
        # Convert edges to adjacency matrix
        tree_matrix = np.zeros((n, n))
        for i, j, weight in tree_edges:
            tree_matrix[i, j] = weight
            tree_matrix[j, i] = weight
        
        return tree_matrix
    
    def calculate_node_importance_in_tree(self, tree_matrix: np.ndarray) -> Dict[str, float]:
        """Calculate node importance in a single spanning tree
        
        For MC-STC, node importance in a tree is based on its degree
        (number of connections) weighted by edge weights.
        
        Args:
            tree_matrix: Adjacency matrix of spanning tree
            
        Returns:
            Dictionary mapping node index to importance value
        """
        n = len(tree_matrix)
        importance = {}
        
        for i in range(n):
            # Weighted degree: sum of edge weights
            node_importance = np.sum(tree_matrix[i, :])
            importance[str(i)] = float(node_importance)
        
        # Normalize by total importance
        total_importance = sum(importance.values())
        if total_importance > 0:
            importance = {k: v / total_importance for k, v in importance.items()}
        
        return importance
        
    def calculate_mc_stc_from_ca(self, ca_matrix: np.ndarray) -> Dict[str, float]:
        """Calculate MC-STC from CA matrix using Monte Carlo method
        
        Args:
            ca_matrix: Contribution Assignment matrix (m × n)
            
        Returns:
            Dictionary mapping developer index to MC-STC value
        """
        # Calculate CR matrix first
        cr_matrix = self.calculate_cr_matrix(ca_matrix)
        return self.calculate_mc_stc_from_cr(cr_matrix)
        
    def calculate_mc_stc_from_cr(self, cr_matrix: np.ndarray) -> Dict[str, float]:
        """Calculate MC-STC from CR matrix using Monte Carlo method
        
        Algorithm:
        1. Generate N random spanning trees from the collaboration network
        2. For each tree, calculate node importance
        3. Average importance values across all sampled trees
        
        Args:
            cr_matrix: Collaboration Relations matrix (m × m)
            
        Returns:
            Dictionary mapping developer index to MC-STC value
        """
        # Validate input
        if not np.allclose(cr_matrix, cr_matrix.T):
            raise ValueError("CR matrix must be symmetric")
        
        n = len(cr_matrix)
        
        # Check if graph is connected (has edges)
        if np.sum(cr_matrix) == 0:
            return {str(i): 0.0 for i in range(n)}
        
        # Accumulate importance values across iterations
        cumulative_importance = {str(i): 0.0 for i in range(n)}
        
        # Monte Carlo sampling
        for iteration in range(self.iterations):
            # Generate random spanning tree
            tree = self.generate_random_spanning_tree(cr_matrix)
            
            # Calculate node importance in this tree
            tree_importance = self.calculate_node_importance_in_tree(tree)
            
            # Accumulate
            for node_id, importance in tree_importance.items():
                cumulative_importance[node_id] += importance
        
        # Average across iterations
        mc_stc_values = {
            node_id: importance / self.iterations 
            for node_id, importance in cumulative_importance.items()
        }
        
        return mc_stc_values
