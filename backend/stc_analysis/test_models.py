"""
Tests for STC Analysis models
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from projects.models import Project
from accounts.models import User, UserProfile
from stc_analysis.models import STCAnalysis


class STCAnalysisModelTest(TestCase):
    """Test STCAnalysis model"""
    
    def setUp(self):
        """Set up test data"""
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            display_name='Test User'
        )
        
        # Create project
        self.project = Project.objects.create(
            name='Test Project',
            repo_url='https://github.com/test/repo',
            owner_profile=self.profile
        )
    
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
    
    def test_analysis_ordering(self):
        """Test that analyses are ordered by date descending"""
        # Create multiple analyses
        analysis1 = STCAnalysis.objects.create(project=self.project)
        analysis2 = STCAnalysis.objects.create(project=self.project)
        analysis3 = STCAnalysis.objects.create(project=self.project)
        
        # Get all analyses
        analyses = STCAnalysis.objects.all()
        
        # Should be ordered newest first
        self.assertEqual(analyses[0].id, analysis3.id)
        self.assertEqual(analyses[1].id, analysis2.id)
        self.assertEqual(analyses[2].id, analysis1.id)
    
    def test_completed_analysis(self):
        """Test marking analysis as completed"""
        analysis = STCAnalysis.objects.create(project=self.project)
        
        # Initially not completed
        self.assertFalse(analysis.is_completed)
        
        # Mark as completed with results
        analysis.is_completed = True
        analysis.results_file = '/path/to/results.json'
        analysis.save()
        
        # Reload from database
        analysis.refresh_from_db()
        
        self.assertTrue(analysis.is_completed)
        self.assertEqual(analysis.results_file, '/path/to/results.json')
    
    def test_analysis_with_error(self):
        """Test analysis with error message"""
        analysis = STCAnalysis.objects.create(
            project=self.project,
            error_message='TNM data not found'
        )
        
        self.assertEqual(analysis.error_message, 'TNM data not found')
        self.assertFalse(analysis.is_completed)
    
    def test_project_cascade_delete(self):
        """Test that analyses are deleted when project is deleted"""
        # Create analyses
        analysis1 = STCAnalysis.objects.create(project=self.project)
        analysis2 = STCAnalysis.objects.create(project=self.project)
        
        # Verify they exist
        self.assertEqual(STCAnalysis.objects.filter(project=self.project).count(), 2)
        
        # Delete project
        project_id = self.project.id
        self.project.delete()
        
        # Analyses should be deleted
        self.assertEqual(STCAnalysis.objects.filter(project_id=project_id).count(), 0)
    
    def test_default_values(self):
        """Test default field values"""
        analysis = STCAnalysis.objects.create(project=self.project)
        
        self.assertFalse(analysis.is_completed)
        self.assertFalse(analysis.use_monte_carlo)
        self.assertEqual(analysis.monte_carlo_iterations, 1000)
        self.assertIsNone(analysis.results_file)
        self.assertIsNone(analysis.error_message)
        self.assertIsNotNone(analysis.analysis_date)
    
    def test_string_representation(self):
        """Test model string representation"""
        analysis = STCAnalysis.objects.create(project=self.project)
        
        # Should contain project name and analysis date
        str_repr = str(analysis)
        self.assertIn('Test Project', str_repr)

