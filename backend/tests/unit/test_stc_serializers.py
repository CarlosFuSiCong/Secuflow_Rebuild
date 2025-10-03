"""
Unit tests for STC Analysis serializers.
"""

from django.test import TestCase
from rest_framework.exceptions import ValidationError
from tests.conftest import BaseTestCase
from stc_analysis.models import STCAnalysis
from stc_analysis.serializers import (
    STCAnalysisSerializer,
    STCAnalysisCreateSerializer,
    STCResultSerializer,
    STCAnalysisResultsSerializer,
    STCComparisonSerializer
)


class STCAnalysisSerializerTests(BaseTestCase):
    """Test STCAnalysisSerializer."""
    
    def test_serialize_stc_analysis(self):
        """Test serializing an STC analysis."""
        analysis = STCAnalysis.objects.create(
            project=self.project,
            use_monte_carlo=True,
            monte_carlo_iterations=5000
        )
        
        serializer = STCAnalysisSerializer(analysis)
        data = serializer.data
        
        self.assertEqual(str(data['project']), str(self.project.id))
        self.assertTrue(data['use_monte_carlo'])
        self.assertEqual(data['monte_carlo_iterations'], 5000)
        self.assertFalse(data['is_completed'])
        self.assertIn('analysis_date', data)
    
    def test_serialize_completed_analysis(self):
        """Test serializing a completed STC analysis."""
        analysis = STCAnalysis.objects.create(
            project=self.project,
            use_monte_carlo=False,
            is_completed=True,
            results_file='results/analysis_123.json'
        )
        
        serializer = STCAnalysisSerializer(analysis)
        data = serializer.data
        
        self.assertTrue(data['is_completed'])
        self.assertEqual(data['results_file'], 'results/analysis_123.json')
    
    def test_serialize_failed_analysis(self):
        """Test serializing a failed STC analysis."""
        analysis = STCAnalysis.objects.create(
            project=self.project,
            use_monte_carlo=False,
            error_message='Analysis failed due to missing data'
        )
        
        serializer = STCAnalysisSerializer(analysis)
        data = serializer.data
        
        self.assertEqual(data['error_message'], 'Analysis failed due to missing data')


class STCAnalysisCreateSerializerTests(BaseTestCase):
    """Test STCAnalysisCreateSerializer."""
    
    def test_create_basic_analysis(self):
        """Test creating a basic STC analysis."""
        data = {
            'project': str(self.project.id),
            'use_monte_carlo': False,
            'monte_carlo_iterations': 1000
        }
        
        serializer = STCAnalysisCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        analysis = serializer.save()
        self.assertEqual(analysis.project, self.project)
        self.assertFalse(analysis.use_monte_carlo)
        self.assertEqual(analysis.monte_carlo_iterations, 1000)
    
    def test_create_monte_carlo_analysis(self):
        """Test creating a Monte Carlo STC analysis."""
        data = {
            'project': str(self.project.id),
            'use_monte_carlo': True,
            'monte_carlo_iterations': 5000
        }
        
        serializer = STCAnalysisCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        analysis = serializer.save()
        self.assertTrue(analysis.use_monte_carlo)
        self.assertEqual(analysis.monte_carlo_iterations, 5000)
    
    def test_invalid_project_id(self):
        """Test creating analysis with invalid project ID."""
        data = {
            'project': '00000000-0000-0000-0000-000000000000',
            'use_monte_carlo': False
        }
        
        serializer = STCAnalysisCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('project', serializer.errors)
    
    def test_negative_iterations(self):
        """Test creating analysis with negative iterations."""
        data = {
            'project': str(self.project.id),
            'use_monte_carlo': True,
            'monte_carlo_iterations': -100
        }
        
        serializer = STCAnalysisCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('monte_carlo_iterations', serializer.errors)
    
    def test_zero_iterations_for_monte_carlo(self):
        """Test creating Monte Carlo analysis with zero iterations."""
        data = {
            'project': str(self.project.id),
            'use_monte_carlo': True,
            'monte_carlo_iterations': 0
        }
        
        serializer = STCAnalysisCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('monte_carlo_iterations', serializer.errors)


class STCResultSerializerTests(TestCase):
    """Test STCResultSerializer."""
    
    def test_serialize_stc_result(self):
        """Test serializing STC result data."""
        result_data = {
            'node_id': '0',
            'contributor_login': 'john_doe',
            'stc_value': 0.75,
            'rank': 1
        }
        
        serializer = STCResultSerializer(data=result_data)
        self.assertTrue(serializer.is_valid())
        
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['node_id'], '0')
        self.assertEqual(validated_data['stc_value'], 0.75)
        self.assertEqual(validated_data['rank'], 1)
    
    def test_missing_required_fields(self):
        """Test STC result with missing required fields."""
        result_data = {
            'stc_value': 0.75,
            # Missing node_id and rank
        }
        
        serializer = STCResultSerializer(data=result_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('node_id', serializer.errors)
        self.assertIn('rank', serializer.errors)
    
    def test_optional_contributor_login(self):
        """Test STC result with optional contributor login."""
        result_data = {
            'node_id': '0',
            'stc_value': 0.75,
            'rank': 1
            # contributor_login is optional
        }
        
        serializer = STCResultSerializer(data=result_data)
        self.assertTrue(serializer.is_valid())
        
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['node_id'], '0')
        self.assertNotIn('contributor_login', validated_data)


class STCAnalysisResultsSerializerTests(BaseTestCase):
    """Test STCAnalysisResultsSerializer."""
    
    def test_serialize_analysis_results(self):
        """Test serializing complete analysis results."""
        analysis = STCAnalysis.objects.create(
            project=self.project,
            use_monte_carlo=True,
            is_completed=True
        )
        
        results_data = {
            'analysis_id': analysis.id,
            'project_id': str(self.project.id),
            'project_name': 'Test Project',
            'analysis_date': '2025-10-03T10:00:00Z',
            'use_monte_carlo': True,
            'total_nodes': 15,
            'total_spanning_trees': 120.5,
            'results': [
                {
                    'node_id': '0',
                    'contributor_login': 'developer1',
                    'stc_value': 0.85,
                    'rank': 1
                },
                {
                    'node_id': '1', 
                    'contributor_login': 'developer2',
                    'stc_value': 0.72,
                    'rank': 2
                }
            ]
        }
        
        serializer = STCAnalysisResultsSerializer(data=results_data)
        self.assertTrue(serializer.is_valid())
        
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['analysis_id'], analysis.id)
        self.assertEqual(validated_data['project_name'], 'Test Project')
        self.assertEqual(validated_data['total_nodes'], 15)
        self.assertEqual(len(validated_data['results']), 2)


class STCComparisonSerializerTests(BaseTestCase):
    """Test STCComparisonSerializer."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        
        # Create two analyses for comparison
        self.analysis1 = STCAnalysis.objects.create(
            project=self.project,
            use_monte_carlo=False,
            is_completed=True
        )
        
        self.analysis2 = STCAnalysis.objects.create(
            project=self.project,
            use_monte_carlo=True,
            is_completed=True
        )
    
    def test_serialize_comparison(self):
        """Test serializing STC analysis comparison."""
        comparison_data = {
            'contributor_login': 'john_doe',
            'contributor_id': 1,
            'stc_value': 0.85,
            'total_modifications': 150,
            'files_modified': 25,
            'functional_role': 'developer',
            'is_core_contributor': True
        }
        
        serializer = STCComparisonSerializer(data=comparison_data)
        self.assertTrue(serializer.is_valid())
        
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['contributor_login'], 'john_doe')
        self.assertEqual(validated_data['contributor_id'], 1)
        self.assertEqual(validated_data['stc_value'], 0.85)
        self.assertEqual(validated_data['total_modifications'], 150)
        self.assertTrue(validated_data['is_core_contributor'])
    
    def test_missing_required_fields(self):
        """Test comparison with missing required fields."""
        comparison_data = {
            'contributor_login': 'john_doe',
            # Missing other required fields
        }
        
        serializer = STCComparisonSerializer(data=comparison_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('contributor_id', serializer.errors)
        self.assertIn('stc_value', serializer.errors)
    
    def test_invalid_data_types(self):
        """Test comparison with invalid data types."""
        comparison_data = {
            'contributor_login': 'john_doe',
            'contributor_id': 'not_an_integer',  # Should be integer
            'stc_value': 0.85,
            'total_modifications': 150,
            'files_modified': 25,
            'functional_role': 'developer',
            'is_core_contributor': True
        }
        
        serializer = STCComparisonSerializer(data=comparison_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('contributor_id', serializer.errors)
