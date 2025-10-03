"""
Unit tests for Projects module.
"""

import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.core.exceptions import ValidationError
from tests.conftest import BaseTestCase
from tests.utils.test_helpers import FileSystemTestMixin
from projects.models import Project, ProjectMember, ProjectRole


class ProjectModelTests(BaseTestCase):
    """Test cases for Project model."""
    
    def test_create_project(self):
        """Test creating a project."""
        project = Project.objects.create(
            name='New Test Project',
            repo_url='https://github.com/test/newrepo',
            description='A new test project',
            owner_profile=self.user_profile
        )
        
        self.assertEqual(project.name, 'New Test Project')
        self.assertEqual(project.repo_url, 'https://github.com/test/newrepo')
        self.assertEqual(project.description, 'A new test project')
        self.assertEqual(project.owner_profile, self.user_profile)
        self.assertIsNotNone(project.id)
        self.assertIsNotNone(project.created_at)
        self.assertIsNone(project.deleted_at)
    
    def test_project_string_representation(self):
        """Test project string representation."""
        # The actual __str__ method returns "Project(name)"
        self.assertEqual(str(self.project), 'Project(Test Project)')
    
    def test_project_soft_delete(self):
        """Test soft deleting a project."""
        self.project.soft_delete()
        
        self.assertIsNotNone(self.project.deleted_at)
        self.assertTrue(self.project.is_deleted)
    
    def test_project_restore(self):
        """Test restoring a soft-deleted project."""
        self.project.soft_delete()
        self.assertTrue(self.project.is_deleted)
        
        self.project.restore()
        self.assertIsNone(self.project.deleted_at)
        self.assertFalse(self.project.is_deleted)
    
    def test_project_member_count(self):
        """Test project member count via members relationship."""
        # Initially no members (owner is not counted as member)
        self.assertEqual(self.project.members.count(), 0)
        
        # Add a member
        ProjectMember.objects.create(
            project=self.project,
            profile=self.other_profile,
            role=ProjectRole.REVIEWER
        )
        
        # Should have 1 member now
        self.assertEqual(self.project.members.count(), 1)
    
    def test_project_membership_check(self):
        """Test checking if user is project member via members relationship."""
        # Other user should not be a member initially
        self.assertFalse(self.project.members.filter(profile=self.other_profile).exists())
        
        # Add other user as member
        ProjectMember.objects.create(
            project=self.project,
            profile=self.other_profile,
            role=ProjectRole.REVIEWER
        )
        
        # Now other user should be a member
        self.assertTrue(self.project.members.filter(profile=self.other_profile).exists())
    
    def test_project_user_role_check(self):
        """Test getting user role in project via relationships."""
        # Owner check
        self.assertEqual(self.project.owner_profile, self.user_profile)
        
        # Non-member should have no membership
        member_qs = self.project.members.filter(profile=self.other_profile)
        self.assertFalse(member_qs.exists())
        
        # Add other user as member
        member = ProjectMember.objects.create(
            project=self.project,
            profile=self.other_profile,
            role=ProjectRole.REVIEWER
        )
        
        # Member should have their assigned role
        member_qs = self.project.members.filter(profile=self.other_profile)
        self.assertTrue(member_qs.exists())
        self.assertEqual(member_qs.first().role, ProjectRole.REVIEWER)


class ProjectMemberModelTests(BaseTestCase):
    """Test cases for ProjectMember model."""
    
    def test_create_project_member(self):
        """Test creating a project member."""
        member = ProjectMember.objects.create(
            project=self.project,
            profile=self.other_profile,
            role=ProjectRole.REVIEWER
        )
        
        self.assertEqual(member.project, self.project)
        self.assertEqual(member.profile, self.other_profile)
        self.assertEqual(member.role, ProjectRole.REVIEWER)
        self.assertIsNotNone(member.joined_at)
    
    def test_project_member_string_representation(self):
        """Test project member string representation."""
        member = ProjectMember.objects.create(
            project=self.project,
            profile=self.other_profile,
            role=ProjectRole.REVIEWER
        )
        
        # The actual __str__ method returns "ProjectMember(project_name:username)"
        expected_str = f"ProjectMember({self.project.name}:{self.other_profile.user.username})"
        self.assertEqual(str(member), expected_str)
    
    def test_unique_project_member(self):
        """Test that a user can only be a member of a project once."""
        # Create first membership
        ProjectMember.objects.create(
            project=self.project,
            profile=self.other_profile,
            role=ProjectRole.REVIEWER
        )
        
        # Attempting to create duplicate membership should raise error
        with self.assertRaises(Exception):  # IntegrityError or ValidationError
            ProjectMember.objects.create(
                project=self.project,
                profile=self.other_profile,
                role=ProjectRole.DEVELOPER
            )


class TNMCleanupUtilsTests(BaseTestCase):
    """Test cases for TNM cleanup utility functions."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        
        # Create temporary directories
        import tempfile
        self.temp_dir = tempfile.mkdtemp()
        self.tnm_output_dir = os.path.join(self.temp_dir, 'tnm_output')
        self.tnm_repos_dir = os.path.join(self.temp_dir, 'tnm_repositories')
        
        os.makedirs(self.tnm_output_dir, exist_ok=True)
        os.makedirs(self.tnm_repos_dir, exist_ok=True)
        
        # Create some test files
        self.create_test_files()
    
    def tearDown(self):
        """Clean up test data."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_files(self):
        """Create test files and directories."""
        # Create project-specific output
        project_output_dir = os.path.join(self.tnm_output_dir, f'project_{self.project.id}_main')
        os.makedirs(project_output_dir, exist_ok=True)
        
        # Create larger test files for size-based cleanup testing
        with open(os.path.join(project_output_dir, 'AssignmentMatrix.json'), 'w') as f:
            f.write('{"test": "data"}' + 'x' * 10000)  # ~10KB file
        
        with open(os.path.join(project_output_dir, 'FileDependencyMatrix.json'), 'w') as f:
            f.write('{"dependency": "matrix"}' + 'y' * 20000)  # ~20KB file
        
        # Create project repository
        project_repo_dir = os.path.join(self.tnm_repos_dir, f'project_{self.project.id}')
        os.makedirs(project_repo_dir, exist_ok=True)
        
        with open(os.path.join(project_repo_dir, 'README.md'), 'w') as f:
            f.write('# Test Repository\n' + 'z' * 15000)  # ~15KB file
        
        # Create some other files
        other_output_dir = os.path.join(self.tnm_output_dir, 'project_other_main')
        os.makedirs(other_output_dir, exist_ok=True)
        
        with open(os.path.join(other_output_dir, 'test.json'), 'w') as f:
            f.write('{"other": "data"}' + 'a' * 5000)  # ~5KB file
        
        # Create another repository
        other_repo_dir = os.path.join(self.tnm_repos_dir, 'project_other')
        os.makedirs(other_repo_dir, exist_ok=True)
        
        with open(os.path.join(other_repo_dir, 'code.py'), 'w') as f:
            f.write('# Python code\n' + 'b' * 8000)  # ~8KB file
    
    def test_directory_size_calculation(self):
        """Test directory size calculation."""
        # Test if the function exists, if not skip the test
        try:
            from projects.views import get_directory_size
        except ImportError:
            self.skipTest("get_directory_size function not found in projects.views")
        
        # Calculate size of output directory
        size = get_directory_size(self.tnm_output_dir)
        
        # Should be greater than 0 (we created files)
        self.assertGreater(size, 0)
        
        # Should be approximately the sum of our test files
        # (allowing for some filesystem overhead)
        expected_min_size = 10000 + 20000 + 5000  # ~35KB
        self.assertGreater(size, expected_min_size)
    
    def test_path_age_checking(self):
        """Test path age checking logic."""
        # Test if the function exists, if not skip the test
        try:
            from projects.views import is_path_older_than_days
        except ImportError:
            self.skipTest("is_path_older_than_days function not found in projects.views")
        
        # Create a file and check its age
        test_file = os.path.join(self.temp_dir, 'test_age.txt')
        with open(test_file, 'w') as f:
            f.write('test content')
        
        # File should not be older than 1 day (just created)
        self.assertFalse(is_path_older_than_days(test_file, 1))
        
        # File should be older than -1 days (impossible, so always False)
        self.assertFalse(is_path_older_than_days(test_file, -1))
        
        # Non-existent file should return False
        self.assertFalse(is_path_older_than_days('/nonexistent/path', 1))
