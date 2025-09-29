"""
Projects API Models

This module provides models for Project and ProjectMember.
"""

import uuid
import re
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils import timezone


class ProjectRole(models.TextChoices):
    """Project role choices."""
    OWNER = 'owner', 'Owner'
    MAINTAINER = 'maintainer', 'Maintainer'
    REVIEWER = 'reviewer', 'Reviewer'


class RepositoryType(models.TextChoices):
    """Repository type choices."""
    GITHUB = 'github', 'GitHub'
    GITLAB = 'gitlab', 'GitLab'
    BITBUCKET = 'bitbucket', 'Bitbucket'
    OTHER = 'other', 'Other'


class Project(models.Model):
    """
    Project model representing a software project with repository information.
    
    Fields:
    - id: UUID primary key
    - name: Project name (max 200 chars, indexed)
    - description: Project description (optional)
    - repo_url: Repository URL (unique, validated)
    - repo_type: Repository type (github/gitlab/bitbucket/other)
    - default_branch: Default branch name
    - owner_profile: Foreign key to UserProfile (project owner)
    - created_at: Creation timestamp
    - updated_at: Last update timestamp
    - deleted_at: Soft deletion timestamp
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField(blank=True, null=True, help_text="Project description")
    repo_url = models.URLField(
        max_length=255, 
        unique=True,
        validators=[URLValidator(schemes=['http', 'https', 'git', 'ssh'])]
    )
    repo_type = models.CharField(
        max_length=20,
        choices=RepositoryType.choices,
        default=RepositoryType.GITHUB,
        help_text="Repository type"
    )
    default_branch = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Default branch name"
    )
    owner_profile = models.ForeignKey(
        "accounts.UserProfile", 
        on_delete=models.PROTECT, 
        related_name="owned_projects"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    # Risk assessment fields
    last_risk_check_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Last risk assessment timestamp"
    )
    stc_risk_score = models.FloatField(
        default=0.0,
        help_text="STC risk score (0-1, higher means more risky)"
    )
    mcstc_risk_score = models.FloatField(
        default=0.0,
        help_text="MC-STC risk score (0-1, higher means more risky)"
    )

    class Meta:
        indexes = [
            models.Index(fields=['repo_type']),
            models.Index(fields=['deleted_at']),
            models.Index(fields=['stc_risk_score']),
            models.Index(fields=['mcstc_risk_score']),
            models.Index(fields=['last_risk_check_at']),
            # Composite indexes for common queries
            models.Index(fields=['owner_profile', 'deleted_at']),
            models.Index(fields=['repo_type', 'deleted_at']),
        ]
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"Project({self.name})"
    
    def soft_delete(self):
        """Soft delete the project by setting deleted_at timestamp."""
        self.deleted_at = timezone.now()
        self.save()
    
    def restore(self):
        """Restore a soft-deleted project."""
        self.deleted_at = None
        self.save()
    
    def save(self, *args, **kwargs):
        """Save the project instance."""
        super().save(*args, **kwargs)
    
    @property
    def is_deleted(self):
        """Check if the project is soft-deleted."""
        return self.deleted_at is not None
    
    def needs_risk_assessment(self, max_age_days: int = 7) -> bool:
        """
        Check if the project needs a new risk assessment.
        
        A project needs risk assessment if:
        1. Never been assessed before
        2. Has updates after last assessment
        3. Last assessment is older than max_age_days
        
        Args:
            max_age_days: Maximum age of risk assessment in days
        
        Returns:
            bool: True if needs new assessment, False otherwise
        """
        if not self.last_risk_check_at:
            return True
            
        # Check for updates
        if self.updated_at and self.updated_at > self.last_risk_check_at:
            return True
            
        # Check if assessment is expired
        age = timezone.now() - self.last_risk_check_at
        return age.days >= max_age_days
    
    def update_risk_scores(self, stc_score: float, mcstc_score: float):
        """
        Update project risk scores for both STC and MC-STC methods.
        
        Args:
            stc_score: STC risk score between 0 and 1 (higher means more risky)
            mcstc_score: MC-STC risk score between 0 and 1 (higher means more risky)
        """
        if not 0 <= stc_score <= 1:
            raise ValueError("STC risk score must be between 0 and 1")
        if not 0 <= mcstc_score <= 1:
            raise ValueError("MC-STC risk score must be between 0 and 1")
            
        self.stc_risk_score = stc_score
        self.mcstc_risk_score = mcstc_score
        self.last_risk_check_at = timezone.now()
        self.save()


class ProjectMember(models.Model):
    """Membership of a profile in a project with a specific role."""

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="members")
    profile = models.ForeignKey("accounts.UserProfile", on_delete=models.CASCADE, related_name="project_memberships")
    role = models.CharField(
        max_length=20,
        choices=ProjectRole.choices,
        default=ProjectRole.REVIEWER,
        help_text="Member role in the project"
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['project', 'profile']
        indexes = [
            models.Index(fields=['project', 'role']),
        ]

    def __str__(self) -> str:
        return f"ProjectMember({self.project.name}:{self.profile.user.username})"

    def clean(self):
        """Validate that a user cannot have multiple roles in the same project."""
        if self.pk:  # Only check for existing instances
            existing = ProjectMember.objects.filter(
                project=self.project, profile=self.profile
            ).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError("User already has a role in this project.")