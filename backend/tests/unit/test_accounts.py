"""
Unit tests for accounts module.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from accounts.models import UserProfile
from tests.conftest import BaseTestCase

User = get_user_model()


class UserModelTests(BaseTestCase):
    """Test User model functionality."""
    
    def test_create_user(self):
        """Test creating a regular user."""
        user = User.objects.create_user(
            username='newuser',
            email='newuser@example.com',
            password='testpass123'
        )
        
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_create_superuser(self):
        """Test creating a superuser."""
        user = User.objects.create_superuser(
            username='superuser',
            email='super@example.com',
            password='testpass123'
        )
        
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
    
    def test_user_string_representation(self):
        """Test user string representation."""
        self.assertEqual(str(self.user), 'testuser')


class UserProfileModelTests(BaseTestCase):
    """Test UserProfile model functionality."""
    
    def test_create_user_profile(self):
        """Test creating a user profile."""
        # Create a new user for this test to avoid conflicts
        new_user = User.objects.create_user(
            username='newuser',
            email='newuser@example.com',
            password='testpass123'
        )
        
        profile = UserProfile.objects.create(
            user=new_user,
            display_name='Test Display Name'
        )
        
        self.assertEqual(profile.user, new_user)
        self.assertEqual(profile.display_name, 'Test Display Name')
    
    def test_user_profile_string_representation(self):
        """Test user profile string representation."""
        expected_str = f"UserProfile(user_id={self.user_profile.user_id}, display_name={self.user_profile.display_name})"
        self.assertEqual(str(self.user_profile), expected_str)
    
    def test_user_profile_one_to_one_relationship(self):
        """Test that user profile has one-to-one relationship with user."""
        self.assertEqual(self.user.profile, self.user_profile)
        self.assertEqual(self.user_profile.user, self.user)
