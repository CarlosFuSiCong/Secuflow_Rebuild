"""
Serializers for accounts app models.
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, UserProfile, GitCredential


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    contact_email = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'date_joined', 'last_login', 'contact_email', 'display_name',
            'avatar'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
    
    def get_contact_email(self, obj):
        """Get user's contact email from profile."""
        return obj.profile.contact_email if hasattr(obj, 'profile') else obj.email
    
    def get_display_name(self, obj):
        """Get user's display name from profile."""
        if hasattr(obj, 'profile') and obj.profile.display_name:
            return obj.profile.display_name
        return obj.get_full_name() or obj.username
    
    def get_avatar(self, obj):
        """Get user's avatar URL from profile."""
        if hasattr(obj, 'profile') and obj.profile.avatar:
            return obj.profile.avatar.url
        return None


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'user', 'contact_email', 'display_name', 'avatar',
            'created_at', 'updated_at', 'selected_project'
        ]
        read_only_fields = ['created_at', 'updated_at']


class GitCredentialSerializer(serializers.ModelSerializer):
    """Serializer for GitCredential model."""
    
    # Don't expose encrypted data in serialization
    class Meta:
        model = GitCredential
        fields = [
            'id', 'credential_type', 'provider', 'username', 
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GitCredentialCreateSerializer(serializers.Serializer):
    """Serializer for creating Git credentials."""
    
    credential_type = serializers.ChoiceField(choices=GitCredential.CredentialType.choices)
    provider = serializers.CharField(max_length=50, default='github')
    
    # For HTTPS token
    token = serializers.CharField(required=False, allow_blank=True, write_only=True)
    
    # For basic auth
    username = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(required=False, allow_blank=True, write_only=True)
    
    # For SSH key
    private_key = serializers.CharField(required=False, allow_blank=True, write_only=True)
    ssh_username = serializers.CharField(required=False, default='git')
    
    def validate(self, data):
        """Validate that required fields are provided based on credential type."""
        credential_type = data.get('credential_type')
        
        if credential_type == GitCredential.CredentialType.HTTPS_TOKEN:
            if not data.get('token'):
                raise serializers.ValidationError("Token is required for HTTPS token authentication")
        elif credential_type == GitCredential.CredentialType.BASIC_AUTH:
            if not data.get('username') or not data.get('password'):
                raise serializers.ValidationError("Username and password are required for basic authentication")
        elif credential_type == GitCredential.CredentialType.SSH_KEY:
            if not data.get('private_key'):
                raise serializers.ValidationError("Private key is required for SSH authentication")
        
        return data
    
    def create(self, validated_data):
        """Create a new Git credential."""
        user_profile = self.context['request'].user.profile
        credential_type = validated_data['credential_type']
        provider = validated_data.get('provider', 'github')
        
        # Remove existing credential of same type and provider
        GitCredential.objects.filter(
            user_profile=user_profile,
            provider=provider,
            credential_type=credential_type
        ).delete()
        
        # Create new credential
        credential = GitCredential(
            user_profile=user_profile,
            credential_type=credential_type,
            provider=provider
        )
        
        if credential_type == GitCredential.CredentialType.HTTPS_TOKEN:
            credential.set_token(validated_data['token'])
        elif credential_type == GitCredential.CredentialType.BASIC_AUTH:
            credential.set_basic_auth(validated_data['username'], validated_data['password'])
        elif credential_type == GitCredential.CredentialType.SSH_KEY:
            credential.set_ssh_key(validated_data['private_key'], validated_data.get('ssh_username', 'git'))
        
        credential.save()
        return credential


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        """Validate user credentials."""
        username = data.get('username')
        password = data.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    data['user'] = user
                else:
                    raise serializers.ValidationError("User account is disabled")
            else:
                raise serializers.ValidationError("Invalid username or password")
        else:
            raise serializers.ValidationError("Username and password are required")
        
        return data


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm', 'first_name', 'last_name']
    
    def validate(self, data):
        """Validate password confirmation and generate username from email."""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match")
        
        email = data.get('email')
        if not email:
            raise serializers.ValidationError("Email is required")
        
        # Get username part from email (before @)
        base_username = email.split('@')[0]
        
        # Try to find a unique username
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Add generated username to data
        data['username'] = username
        
        return data
    
    def create(self, validated_data):
        """Create a new user with profile."""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        
        # Create user profile
        UserProfile.objects.create(user=user)
        
        return user
