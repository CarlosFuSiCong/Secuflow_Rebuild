"""
API tests for projects endpoints.
"""

import json
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from tests.conftest import BaseTestCase


class ProjectsAPITests(BaseTestCase, APITestCase):
    """Test cases for Projects API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        
        # Set up API client with authentication
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Admin client
        admin_refresh = RefreshToken.for_user(self.admin_user)
        self.admin_client = self.client_class()
        self.admin_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_refresh.access_token}')
    
    def test_list_projects(self):
        """Test listing projects."""
        response = self.client.get('/api/projects/projects/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('results', data)
        self.assertGreaterEqual(len(data['results']), 1)
    
    def test_create_project(self):
        """Test creating a new project."""
        project_data = {
            'name': 'New Test Project',
            'repo_url': 'https://github.com/test/newrepo',
            'description': 'A new test project',
            'repo_type': 'github'
        }
        
        response = self.client.post('/api/projects/projects/', project_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data['data']['name'], 'New Test Project')
        self.assertEqual(data['data']['repo_url'], 'https://github.com/test/newrepo')
    
    def test_get_project_detail(self):
        """Test getting project details."""
        response = self.client.get(f'/api/projects/projects/{self.project.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['data']['name'], self.project.name)
        self.assertEqual(data['data']['repo_url'], self.project.repo_url)
    
    def test_update_project(self):
        """Test updating a project."""
        update_data = {
            'name': 'Updated Project Name',
            'description': 'Updated description'
        }
        
        response = self.client.patch(
            f'/api/projects/projects/{self.project.id}/',
            update_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['data']['name'], 'Updated Project Name')
    
    def test_delete_project(self):
        """Test soft deleting a project."""
        response = self.client.delete(f'/api/projects/projects/{self.project.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify project is soft deleted
        self.project.refresh_from_db()
        self.assertIsNotNone(self.project.deleted_at)
    
    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access projects."""
        self.client.credentials()  # Remove authentication
        
        response = self.client.get('/api/projects/projects/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_project_permissions(self):
        """Test that users can only access their own projects."""
        # Create another user's project
        other_project = self.project.__class__.objects.create(
            name='Other User Project',
            repo_url='https://github.com/other/repo',
            owner_profile=self.other_profile
        )
        
        # Try to access other user's project
        response = self.client.get(f'/api/projects/projects/{other_project.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TNMCleanupAPITests(BaseTestCase, APITestCase):
    """Test cases for TNM cleanup API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        
        # Set up API client with authentication
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Admin client
        admin_refresh = RefreshToken.for_user(self.admin_user)
        self.admin_client = self.client_class()
        self.admin_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_refresh.access_token}')
    
    def test_project_cleanup_requires_confirmation(self):
        """Test that project cleanup requires confirmation."""
        data = {
            'cleanup_type': 'all',
            'confirm': False
        }
        
        response = self.client.post(
            f'/api/projects/projects/{self.project.id}/cleanup-tnm/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertEqual(response_data['errorCode'], 'CONFIRMATION_REQUIRED')
    
    def test_global_cleanup_requires_admin(self):
        """Test that global cleanup requires admin privileges."""
        data = {
            'cleanup_type': 'all',
            'confirm': True
        }
        
        response = self.client.post('/api/projects/cleanup-tnm-data/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_auto_cleanup_requires_admin(self):
        """Test that auto cleanup requires admin privileges."""
        data = {
            'dry_run': True
        }
        
        response = self.client.post('/api/projects/auto-cleanup-tnm/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
