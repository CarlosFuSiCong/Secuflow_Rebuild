import numpy as np
from typing import Dict, List, Optional, Tuple, Set
from stc_analysis.models import STCAnalysis


class STCService:
    """Service for STC (Socio-Technical Congruence) calculations
    
    STC measures the alignment between coordination requirements and actual coordination:
    
    Variables:
    - CR (Coordination Requirements): m × m matrix representing who needs to coordinate
      (derived from technical dependencies: CR = Assignment @ Dependency @ Assignment^T)
    - CA (Coordination Actuals): m × m matrix representing who actually coordinates
      (derived from communication/collaboration data, e.g., co-editing files)
    
    Formula:
    STC = |CR ∩ CA| / |CR|
    
    Where:
    - |CR ∩ CA| = number of edges where coordination is both required and actual
    - |CR| = total number of edges where coordination is required
    - Range: [0, 1], higher means better socio-technical alignment
    """
    
    def __init__(self, project_id: str, threshold: float = 0):
        """
        Args:
            project_id: Project identifier
            threshold: Threshold for filtering weak connections (default: 0)
        """
        self.project_id = project_id
        self.threshold = threshold
    
    def calculate_cr_from_assignment_dependency(
        self, 
        assignment_matrix: np.ndarray, 
        dependency_matrix: np.ndarray
    ) -> np.ndarray:
        """Calculate CR (Coordination Requirements) from assignment and dependency matrices
        
        Formula: CR = Assignment @ Dependency @ Assignment^T
        
        Args:
            assignment_matrix: m × n matrix (developers × files)
            dependency_matrix: n × n matrix (file dependencies)
        
        Returns:
            CR matrix (m × m) representing coordination requirements
        """
        # Calculate coordination requirement
        cr_matrix = assignment_matrix @ dependency_matrix @ assignment_matrix.T
        
        # Apply threshold
        if self.threshold > 0:
            cr_matrix = np.where(cr_matrix > self.threshold, 1, 0)
        else:
            # Binary threshold: > 0 means coordination is required
            cr_matrix = np.where(cr_matrix > 0, 1, 0)
        
        # Remove self-loops (diagonal)
        np.fill_diagonal(cr_matrix, 0)
        
        return cr_matrix
    
    def calculate_ca_from_file_modifiers(
        self, 
        file_modifiers: Dict[str, Set[str]], 
        all_users: List[str]
    ) -> np.ndarray:
        """Calculate CA (Coordination Actuals) from file modifier data
        
        If two developers modify the same file, they have actual coordination.
        
        Args:
            file_modifiers: Dictionary mapping file_id to set of user_ids who modified it
            all_users: List of all user IDs
        
        Returns:
            CA matrix (m × m) representing actual coordination
        """
        n = len(all_users)
        ca_matrix = np.zeros((n, n))
        
        # Create user index mapping
        user_indices = {user_id: idx for idx, user_id in enumerate(all_users)}
        
        # For each file, mark coordination between all pairs of modifiers
        for modifiers in file_modifiers.values():
            indices = [user_indices[user_id] for user_id in modifiers if user_id in user_indices]
            for i in indices:
                for j in indices:
                    if i != j:
                        ca_matrix[i][j] = 1
        
        # Remove self-loops (diagonal)
        np.fill_diagonal(ca_matrix, 0)
        
        return ca_matrix
    
    def calculate_stc(self, cr_matrix: np.ndarray, ca_matrix: np.ndarray) -> float:
        """Calculate STC (Socio-Technical Congruence)
        
        Formula: STC = |CR ∩ CA| / |CR|
        
        Args:
            cr_matrix: Coordination Requirements matrix (m × m)
            ca_matrix: Coordination Actuals matrix (m × m)
        
        Returns:
            STC value in range [0, 1]
        """
        # Ensure matrices have the same shape
        if cr_matrix.shape != ca_matrix.shape:
            raise ValueError("CR and CA matrices must have the same shape")
        
        # Remove diagonal (no self-coordination)
        mask_no_diagonal = ~np.eye(len(cr_matrix), dtype=bool)
        
        # Calculate intersection: edges that are in both CR and CA
        intersection_mask = (cr_matrix > 0) & (ca_matrix > 0) & mask_no_diagonal
        intersection_count = np.sum(intersection_mask)
        
        # Calculate total required coordination edges
        required_mask = (cr_matrix > 0) & mask_no_diagonal
        required_count = np.sum(required_mask)
        
        # Calculate STC
        if required_count == 0:
            return 0.0
        
        stc = intersection_count / required_count
        return float(stc)
    
    def get_missed_coordination(
        self, 
        cr_matrix: np.ndarray, 
        ca_matrix: np.ndarray
    ) -> np.ndarray:
        """Get edges where coordination is required but not actual
        
        Returns:
            Matrix of missed coordination edges (CR - CA intersection)
        """
        mask_no_diagonal = ~np.eye(len(cr_matrix), dtype=bool)
        missed = (cr_matrix > 0) & (ca_matrix == 0) & mask_no_diagonal
        return missed.astype(int)
    
    def get_unnecessary_coordination(
        self, 
        cr_matrix: np.ndarray, 
        ca_matrix: np.ndarray
    ) -> np.ndarray:
        """Get edges where coordination is actual but not required
        
        Returns:
            Matrix of unnecessary coordination edges (CA - CR intersection)
        """
        mask_no_diagonal = ~np.eye(len(cr_matrix), dtype=bool)
        unnecessary = (cr_matrix == 0) & (ca_matrix > 0) & mask_no_diagonal
        return unnecessary.astype(int)


class MCSTCService(STCService):
    """Service for MC-STC (Multi-Class Socio-Technical Congruence) calculations
    
    MC-STC extends STC to measure alignment between different functional classes.
    
    Formula:
    MC-STC = |(CR ∩ CA)^inter| / |CR^inter|
    
    Where:
    - ^inter means only inter-class edges (between different classes)
    - Intra-class edges (within same class) are excluded
    
    For 2-class (Dev vs Sec):
    2C-STC = |(CR ∩ CA)^{Dev-Sec}| / |CR^{Dev-Sec}|
    """
    
    def __init__(self, project_id: str, threshold: float = 0):
        super().__init__(project_id, threshold)
    
    def filter_inter_class_edges(
        self,
        matrix: np.ndarray,
        all_users: List[str],
        class_assignments: Dict[str, str]
    ) -> np.ndarray:
        """Filter matrix to keep only inter-class edges
        
        Args:
            matrix: Input matrix (CR or CA)
            all_users: List of all user IDs
            class_assignments: Dict mapping user_id to class_name (e.g., 'dev', 'sec')
        
        Returns:
            Matrix with only inter-class edges
        """
        n = len(all_users)
        filtered_matrix = matrix.copy()
        
        # Group users by class
        classes = {}
        for user_id in all_users:
            class_name = class_assignments.get(user_id, 'unknown')
            if class_name not in classes:
                classes[class_name] = []
            classes[class_name].append(user_id)
        
        # Create user index mapping
        user_indices = {user_id: idx for idx, user_id in enumerate(all_users)}
        
        # Zero out intra-class edges
        for class_name, users in classes.items():
            indices = [user_indices[user_id] for user_id in users if user_id in user_indices]
            # Set all intra-class edges to 0
            for i in indices:
                for j in indices:
                    filtered_matrix[i, j] = 0
        
        return filtered_matrix
    
    def calculate_mc_stc(
        self,
        cr_matrix: np.ndarray,
        ca_matrix: np.ndarray,
        all_users: List[str],
        class_assignments: Dict[str, str]
    ) -> float:
        """Calculate MC-STC (Multi-Class Socio-Technical Congruence)
        
        Args:
            cr_matrix: Coordination Requirements matrix
            ca_matrix: Coordination Actuals matrix
            all_users: List of all user IDs
            class_assignments: Dict mapping user_id to class_name
        
        Returns:
            MC-STC value in range [0, 1]
        """
        # Filter to keep only inter-class edges
        mc_cr = self.filter_inter_class_edges(cr_matrix, all_users, class_assignments)
        mc_ca = self.filter_inter_class_edges(ca_matrix, all_users, class_assignments)
        
        # Calculate STC on filtered matrices
        mc_stc = self.calculate_stc(mc_cr, mc_ca)
        
        return mc_stc
    
    def calculate_2c_stc(
        self,
        cr_matrix: np.ndarray,
        ca_matrix: np.ndarray,
        all_users: List[str],
        security_users: Set[str],
        developer_users: Set[str]
    ) -> Tuple[float, np.ndarray, np.ndarray]:
        """Calculate 2C-STC (Two-Class STC) for Dev-Sec coordination
        
        Args:
            cr_matrix: Coordination Requirements matrix
            ca_matrix: Coordination Actuals matrix
            all_users: List of all user IDs
            security_users: Set of security user IDs
            developer_users: Set of developer user IDs
        
        Returns:
            Tuple of (2C-STC value, filtered CR matrix, filtered CA matrix)
        """
        # Create class assignments
        class_assignments = {}
        for user_id in all_users:
            if user_id in security_users:
                class_assignments[user_id] = 'security'
            elif user_id in developer_users:
                class_assignments[user_id] = 'developer'
            else:
                class_assignments[user_id] = 'unknown'
        
        # Filter to keep only inter-class edges
        mc_cr = self.filter_inter_class_edges(cr_matrix, all_users, class_assignments)
        mc_ca = self.filter_inter_class_edges(ca_matrix, all_users, class_assignments)
        
        # Calculate 2C-STC
        two_c_stc = self.calculate_stc(mc_cr, mc_ca)
        
        return two_c_stc, mc_cr, mc_ca
    
    def get_missed_dev_sec_coordination(
        self,
        cr_matrix: np.ndarray,
        ca_matrix: np.ndarray,
        all_users: List[str],
        security_users: Set[str],
        developer_users: Set[str]
    ) -> Dict[str, int]:
        """Calculate missed Dev-Sec coordination count for each developer
        
        Returns:
            Dictionary mapping developer_id to count of missed coordination with security
        """
        _, mc_cr, mc_ca = self.calculate_2c_stc(
            cr_matrix, ca_matrix, all_users, 
            security_users, developer_users
        )
        
        missed_coordination = {}
        user_indices = {user_id: idx for idx, user_id in enumerate(all_users)}
        
        for dev_id in developer_users:
            if dev_id not in user_indices:
                continue
            
            dev_idx = user_indices[dev_id]
            
            # Count edges where coordination with security is required but not actual
            missed_count = 0
            for sec_id in security_users:
                if sec_id not in user_indices:
                    continue
                sec_idx = user_indices[sec_id]
                
                if mc_cr[dev_idx, sec_idx] > 0 and mc_ca[dev_idx, sec_idx] == 0:
                    missed_count += 1
            
            missed_coordination[dev_id] = missed_count
        
        return missed_coordination
