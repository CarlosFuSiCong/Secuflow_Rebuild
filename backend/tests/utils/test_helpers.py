"""
Test utilities and helper functions.
"""

import json
import tempfile
import os
import shutil
from unittest.mock import patch, MagicMock
from django.test import override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


class APITestMixin:
    """Mixin providing API testing utilities."""
    
    def get_authenticated_client(self, user):
        """Get an authenticated API client for the given user."""
        client = APIClient()
        refresh = RefreshToken.for_user(user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        return client
    
    def assert_api_success(self, response, expected_status=200):
        """Assert that an API response is successful."""
        self.assertEqual(response.status_code, expected_status)
        
        if response.content:
            data = response.json()
            if 'succeed' in data:
                self.assertTrue(data['succeed'])
    
    def assert_api_error(self, response, expected_status=400, expected_error_code=None):
        """Assert that an API response contains an error."""
        self.assertEqual(response.status_code, expected_status)
        
        if response.content:
            data = response.json()
            if 'succeed' in data:
                self.assertFalse(data['succeed'])
            
            if expected_error_code and 'errorCode' in data:
                self.assertEqual(data['errorCode'], expected_error_code)


class FileSystemTestMixin:
    """Mixin providing file system testing utilities."""
    
    def setUp(self):
        """Set up temporary directories for testing."""
        super().setUp()
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(self.cleanup_temp_dir)
    
    def cleanup_temp_dir(self):
        """Clean up temporary directory."""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_temp_file(self, filename, content):
        """Create a temporary file with the given content."""
        filepath = os.path.join(self.temp_dir, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        if isinstance(content, (dict, list)):
            with open(filepath, 'w') as f:
                json.dump(content, f)
        else:
            with open(filepath, 'w') as f:
                f.write(content)
        
        return filepath
    
    def create_temp_directory(self, dirname):
        """Create a temporary directory."""
        dirpath = os.path.join(self.temp_dir, dirname)
        os.makedirs(dirpath, exist_ok=True)
        return dirpath


class MockTNMOutputMixin:
    """Mixin providing TNM output mocking utilities."""
    
    def mock_tnm_output_directory(self, project_id, branch='main'):
        """Mock TNM output directory with sample files."""
        temp_dir = tempfile.mkdtemp()
        output_dir = os.path.join(temp_dir, f'project_{project_id}_{branch}')
        os.makedirs(output_dir, exist_ok=True)
        
        # Create sample TNM files
        from tests.fixtures.sample_data import SampleDataMixin
        SampleDataMixin.create_tnm_files_in_directory(output_dir)
        
        return temp_dir, output_dir
    
    def patch_tnm_settings(self, output_dir, repos_dir=None):
        """Patch TNM-related settings for testing."""
        if repos_dir is None:
            repos_dir = tempfile.mkdtemp()
        
        return patch.multiple(
            'django.conf.settings',
            TNM_OUTPUT_DIR=output_dir,
            TNM_REPOSITORIES_DIR=repos_dir
        )


class DatabaseTestMixin:
    """Mixin providing database testing utilities."""
    
    def assert_model_exists(self, model_class, **kwargs):
        """Assert that a model instance exists with the given criteria."""
        self.assertTrue(
            model_class.objects.filter(**kwargs).exists(),
            f"{model_class.__name__} with {kwargs} does not exist"
        )
    
    def assert_model_count(self, model_class, expected_count, **kwargs):
        """Assert the count of model instances matching the given criteria."""
        actual_count = model_class.objects.filter(**kwargs).count()
        self.assertEqual(
            actual_count, expected_count,
            f"Expected {expected_count} {model_class.__name__} instances, got {actual_count}"
        )
    
    def get_or_create_test_instance(self, model_class, defaults=None, **kwargs):
        """Get or create a test instance of the given model."""
        if defaults is None:
            defaults = {}
        
        instance, created = model_class.objects.get_or_create(
            defaults=defaults, **kwargs
        )
        return instance, created


class AssertionHelpers:
    """Helper methods for common test assertions."""
    
    def assert_dict_contains(self, container, subset):
        """Assert that a dictionary contains all key-value pairs from subset."""
        for key, value in subset.items():
            self.assertIn(key, container, f"Key '{key}' not found in container")
            self.assertEqual(
                container[key], value,
                f"Value for key '{key}' does not match. Expected: {value}, Got: {container[key]}"
            )
    
    def assert_list_contains_dict(self, list_of_dicts, expected_dict):
        """Assert that a list contains a dictionary with the expected key-value pairs."""
        found = False
        for item in list_of_dicts:
            if all(item.get(k) == v for k, v in expected_dict.items()):
                found = True
                break
        
        self.assertTrue(
            found,
            f"List does not contain a dictionary with {expected_dict}"
        )
    
    def assert_response_has_keys(self, response, expected_keys):
        """Assert that a response JSON contains the expected keys."""
        data = response.json()
        for key in expected_keys:
            self.assertIn(key, data, f"Response missing key: {key}")
    
    def assert_pagination_response(self, response, expected_count=None):
        """Assert that a response has proper pagination structure."""
        data = response.json()
        
        # Check pagination keys
        pagination_keys = ['results', 'count', 'next', 'previous']
        for key in pagination_keys:
            self.assertIn(key, data, f"Pagination response missing key: {key}")
        
        # Check expected count if provided
        if expected_count is not None:
            self.assertEqual(data['count'], expected_count)
        
        # Results should be a list
        self.assertIsInstance(data['results'], list)
