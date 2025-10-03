"""
Sample data and fixtures for testing.
"""

import json
import numpy as np
from django.contrib.auth import get_user_model
from accounts.models import UserProfile
from projects.models import Project
from contributors.models import Contributor, ProjectContributor, FunctionalRole

User = get_user_model()


class SampleDataMixin:
    """Mixin providing sample data for tests."""
    
    @staticmethod
    def create_sample_users():
        """Create sample users for testing."""
        users = []
        
        # Admin user
        admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        admin_profile = UserProfile.objects.create(
            user=admin,
            display_name='Admin User'
        )
        users.append((admin, admin_profile))
        
        # Regular users
        for i in range(3):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='testpass123'
            )
            profile = UserProfile.objects.create(
                user=user,
                display_name=f'User {i}'
            )
            users.append((user, profile))
        
        return users
    
    @staticmethod
    def create_sample_projects(owner_profile, count=3):
        """Create sample projects for testing."""
        projects = []
        
        for i in range(count):
            project = Project.objects.create(
                name=f'Test Project {i}',
                repo_url=f'https://github.com/test/repo{i}',
                description=f'Test project {i} description',
                owner_profile=owner_profile
            )
            projects.append(project)
        
        return projects
    
    @staticmethod
    def create_sample_contributors(project):
        """Create sample contributors for a project."""
        contributors = []
        
        # Developer contributors
        for i in range(2):
            contributor = Contributor.objects.create(
                email=f'developer{i}@example.com',
                name=f'Developer {i}'
            )
            
            ProjectContributor.objects.create(
                project=project,
                contributor=contributor,
                functional_role=FunctionalRole.DEVELOPER
            )
            contributors.append(contributor)
        
        # Security contributors
        for i in range(2):
            contributor = Contributor.objects.create(
                email=f'security{i}@example.com',
                name=f'Security {i}'
            )
            
            ProjectContributor.objects.create(
                project=project,
                contributor=contributor,
                functional_role=FunctionalRole.SECURITY
            )
            contributors.append(contributor)
        
        return contributors
    
    @staticmethod
    def get_sample_assignment_matrix():
        """Get a sample assignment matrix for testing."""
        return np.array([
            [5, 3, 0, 2, 1],  # Developer 0
            [2, 4, 3, 0, 1],  # Developer 1
            [0, 1, 5, 4, 2],  # Developer 2
            [1, 0, 2, 3, 4]   # Developer 3
        ])
    
    @staticmethod
    def get_sample_dependency_matrix():
        """Get a sample file dependency matrix for testing."""
        return np.array([
            [0, 1, 0, 1, 0],  # File 0
            [1, 0, 1, 0, 1],  # File 1
            [0, 1, 0, 1, 0],  # File 2
            [1, 0, 1, 0, 1],  # File 3
            [0, 1, 0, 1, 0]   # File 4
        ])
    
    @staticmethod
    def get_sample_file_modifiers():
        """Get sample file modifiers data for testing."""
        return {
            '0': {'0', '1'},       # File 0 modified by devs 0, 1
            '1': {'0', '1', '2'},  # File 1 modified by devs 0, 1, 2
            '2': {'1', '2'},       # File 2 modified by devs 1, 2
            '3': {'0', '2', '3'},  # File 3 modified by devs 0, 2, 3
            '4': {'1', '3'}        # File 4 modified by devs 1, 3
        }
    
    @staticmethod
    def get_sample_tnm_files():
        """Get sample TNM output files as dictionaries."""
        return {
            'AssignmentMatrix.json': SampleDataMixin.get_sample_assignment_matrix().tolist(),
            'FileDependencyMatrix.json': SampleDataMixin.get_sample_dependency_matrix().tolist(),
            'idToUser.json': {
                "0": "developer0@example.com",
                "1": "developer1@example.com",
                "2": "security0@example.com",
                "3": "security1@example.com"
            },
            'idToFile.json': {
                "0": "src/main.py",
                "1": "src/utils.py",
                "2": "src/security.py",
                "3": "tests/test_main.py",
                "4": "README.md"
            }
        }
    
    @staticmethod
    def create_tnm_files_in_directory(directory):
        """Create TNM files in the specified directory."""
        import os
        
        tnm_files = SampleDataMixin.get_sample_tnm_files()
        
        for filename, content in tnm_files.items():
            filepath = os.path.join(directory, filename)
            with open(filepath, 'w') as f:
                json.dump(content, f)
        
        return list(tnm_files.keys())
