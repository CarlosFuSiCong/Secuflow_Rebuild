"""
Tests for STC Analysis serializers
"""
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from projects.models import Project
from accounts.models import User, UserProfile
from stc_analysis.models import STCAnalysis
from stc_analysis.serializers import (
    STCAnalysisSerializer,
    STCAnalysisCreateSerializer,
    STCResultSerializer,
    STCAnalysisResultsSerializer,
    STCComparisonSerializer
)


class STCAnalysisSerializerTest(TestCase):
    """Test STCAnalysisSerializer"""
    
    def setUp(self):
        """Set up test data"""
        # Create user and profile
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
        
        # Create analysis
        self.analysis = STCAnalysis.objects.create(
            project=self.project,
            use_monte_carlo=False,
            monte_carlo_iterations=1000
        )
    
    def test_serialize_analysis(self):
        """Test serializing an STC analysis"""
        serializer = STCAnalysisSerializer(self.analysis)
        data = serializer.data
        
        self.assertEqual(data['id'], self.analysis.id)
        # Check project ID (could be UUID object or string)
        project_id = data['project']
        self.assertTrue(str(project_id) == str(self.project.id))
        self.assertEqual(data['project_name'], 'Test Project')
        self.assertEqual(data['project_repo_url'], 'https://github.com/test/repo')
        self.assertFalse(data['is_completed'])
        self.assertFalse(data['use_monte_carlo'])
        self.assertEqual(data['monte_carlo_iterations'], 1000)
    
    def test_serialize_completed_analysis(self):
        """Test serializing a completed analysis"""
        self.analysis.is_completed = True
        self.analysis.results_file = '/path/to/results.json'
        self.analysis.save()
        
        serializer = STCAnalysisSerializer(self.analysis)
        data = serializer.data
        
        self.assertTrue(data['is_completed'])
        self.assertEqual(data['results_file'], '/path/to/results.json')
    
    def test_serialize_analysis_with_error(self):
        """Test serializing an analysis with error"""
        self.analysis.error_message = 'Test error'
        self.analysis.save()
        
        serializer = STCAnalysisSerializer(self.analysis)
        data = serializer.data
        
        self.assertEqual(data['error_message'], 'Test error')


class STCAnalysisCreateSerializerTest(TestCase):
    """Test STCAnalysisCreateSerializer"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            display_name='Test User'
        )
        
        self.project = Project.objects.create(
            name='Test Project',
            repo_url='https://github.com/test/repo',
            owner_profile=self.profile
        )
    
    def test_valid_create_data(self):
        """Test creating analysis with valid data"""
        data = {
            'project': self.project.id,
            'use_monte_carlo': False,
            'monte_carlo_iterations': 1000
        }
        
        serializer = STCAnalysisCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        analysis = serializer.save()
        self.assertEqual(analysis.project, self.project)
        self.assertFalse(analysis.use_monte_carlo)
        self.assertEqual(analysis.monte_carlo_iterations, 1000)
    
    def test_monte_carlo_iterations_too_low(self):
        """Test validation for iterations below minimum"""
        data = {
            'project': self.project.id,
            'use_monte_carlo': True,
            'monte_carlo_iterations': 50  # Too low
        }
        
        serializer = STCAnalysisCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('monte_carlo_iterations', serializer.errors)
    
    def test_monte_carlo_iterations_too_high(self):
        """Test validation for iterations above maximum"""
        data = {
            'project': self.project.id,
            'use_monte_carlo': True,
            'monte_carlo_iterations': 15000  # Too high
        }
        
        serializer = STCAnalysisCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('monte_carlo_iterations', serializer.errors)
    
    def test_invalid_project(self):
        """Test validation with non-existent project"""
        data = {
            'project': '00000000-0000-0000-0000-000000000000',
            'use_monte_carlo': False
        }
        
        serializer = STCAnalysisCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())


class STCResultSerializerTest(TestCase):
    """Test STCResultSerializer"""
    
    def test_serialize_result(self):
        """Test serializing a single STC result"""
        data = {
            'node_id': '0',
            'contributor_login': 'john_doe',
            'stc_value': 0.85,
            'rank': 1
        }
        
        serializer = STCResultSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        validated = serializer.validated_data
        self.assertEqual(validated['node_id'], '0')
        self.assertEqual(validated['contributor_login'], 'john_doe')
        self.assertEqual(validated['stc_value'], 0.85)
        self.assertEqual(validated['rank'], 1)
    
    def test_result_without_contributor(self):
        """Test result without contributor login"""
        data = {
            'node_id': '0',
            'stc_value': 0.85,
            'rank': 1
        }
        
        serializer = STCResultSerializer(data=data)
        self.assertTrue(serializer.is_valid())


class STCAnalysisResultsSerializerTest(TestCase):
    """Test STCAnalysisResultsSerializer"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            display_name='Test User'
        )
        
        self.project = Project.objects.create(
            name='Test Project',
            repo_url='https://github.com/test/repo',
            owner_profile=self.profile
        )
    
    def test_serialize_complete_results(self):
        """Test serializing complete analysis results"""
        data = {
            'analysis_id': 1,
            'project_id': str(self.project.id),
            'project_name': 'Test Project',
            'analysis_date': '2025-10-03T10:00:00Z',
            'use_monte_carlo': False,
            'total_nodes': 3,
            'total_spanning_trees': 5.0,
            'results': [
                {
                    'node_id': '0',
                    'contributor_login': 'john_doe',
                    'stc_value': 0.85,
                    'rank': 1
                },
                {
                    'node_id': '1',
                    'contributor_login': 'jane_smith',
                    'stc_value': 0.72,
                    'rank': 2
                }
            ]
        }
        
        serializer = STCAnalysisResultsSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        
        validated = serializer.validated_data
        self.assertEqual(validated['analysis_id'], 1)
        self.assertEqual(validated['total_nodes'], 3)
        self.assertEqual(len(validated['results']), 2)


class STCComparisonSerializerTest(TestCase):
    """Test STCComparisonSerializer"""
    
    def test_serialize_comparison(self):
        """Test serializing comparison data"""
        data = {
            'contributor_login': 'john_doe',
            'contributor_id': 1,
            'stc_value': 0.85,
            'total_modifications': 5000,
            'files_modified': 150,
            'functional_role': 'coder',
            'is_core_contributor': True
        }
        
        serializer = STCComparisonSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        validated = serializer.validated_data
        self.assertEqual(validated['contributor_login'], 'john_doe')
        self.assertEqual(validated['stc_value'], 0.85)
        self.assertTrue(validated['is_core_contributor'])

