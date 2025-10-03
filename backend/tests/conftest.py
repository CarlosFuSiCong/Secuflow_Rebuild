"""
Shared fixtures and configuration for the test suite.
"""

import tempfile
import shutil
from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import UserProfile
from projects.models import Project, ProjectMember, ProjectRole
from stc_analysis.models import STCAnalysis
from project_monitoring.models import ProjectMonitoring, AnalysisType, AnalysisStatus

User = get_user_model()

# Pytest fixtures (only if pytest is available)
try:
    import pytest
    
    @pytest.fixture
    def temp_directory():
        """Create a temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def admin_user():
        """Create an admin user for tests."""
        return User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )

    @pytest.fixture
    def regular_user():
        """Create a regular user for tests."""
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def user_profile(regular_user):
        """Create a user profile for tests."""
        return UserProfile.objects.create(
            user=regular_user,
            display_name='Test User'
        )

    @pytest.fixture
    def admin_profile(admin_user):
        """Create an admin user profile for tests."""
        return UserProfile.objects.create(
            user=admin_user,
            display_name='Admin User'
        )

    @pytest.fixture
    def test_project(user_profile):
        """Create a test project."""
        return Project.objects.create(
            name='Test Project',
            repo_url='https://github.com/test/repo',
            description='A test project for unit testing',
            owner_profile=user_profile
        )

    @pytest.fixture
    def stc_analysis(test_project):
        """Create a test STC analysis."""
        return STCAnalysis.objects.create(
            project=test_project,
            use_monte_carlo=False,
            monte_carlo_iterations=1000
        )

    @pytest.fixture
    def monitoring_record(test_project):
        """Create a test monitoring record."""
        return ProjectMonitoring.objects.create(
            project=test_project,
            analysis_type=AnalysisType.STC,
            status=AnalysisStatus.PENDING
        )

except ImportError:
    # Pytest not available, skip fixtures
    pass


class BaseTestCase(TestCase):
    """Base test case with common setup for all tests."""
    
    def setUp(self):
        """Set up common test data."""
        # Create users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        self.admin_profile = UserProfile.objects.create(
            user=self.admin_user,
            display_name='Admin User'
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            display_name='Test User'
        )
        
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        self.other_profile = UserProfile.objects.create(
            user=self.other_user,
            display_name='Other User'
        )
        
        # Create test project
        self.project = Project.objects.create(
            name='Test Project',
            repo_url='https://github.com/test/repo',
            description='A test project for unit testing',
            owner_profile=self.user_profile
        )
    
    def tearDown(self):
        """Clean up after tests."""
        # Clean up any temporary files or data
        pass
