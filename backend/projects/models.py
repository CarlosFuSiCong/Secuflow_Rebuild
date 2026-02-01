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
    repository_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Local path to cloned repository"
    )
    auto_run_stc = models.BooleanField(
        default=False,
        help_text="Automatically run STC analysis after TNM completion"
    )
    auto_run_mcstc = models.BooleanField(
        default=False,
        help_text="Automatically run MC-STC analysis after TNM completion"
    )
    owner_profile = models.ForeignKey(
        "accounts.UserProfile", 
        on_delete=models.PROTECT, 
        related_name="owned_projects"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    # Risk assessment fields (legacy - now computed from analysis results)
    last_risk_check_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Last risk assessment timestamp (legacy field)"
    )

    class Meta:
        indexes = [
            models.Index(fields=['repo_type']),
            models.Index(fields=['deleted_at']),
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
    
    @property
    def stc_risk_score(self):
        """
        Calculate STC risk score based on latest STC analysis for current branch.
        Risk score = 1 - STC value (higher STC means lower risk)
        """
        try:
            current_branch = self.default_branch or 'main'
            latest_stc = self.stc_analyses.filter(
                is_completed=True,
                branch_analyzed=current_branch
            ).first()
            if latest_stc and latest_stc.stc_value is not None:
                return round(1.0 - latest_stc.stc_value, 3)
        except Exception:
            pass
        return None  # No analysis for current branch
    
    @property
    def mcstc_risk_score(self):
        """
        Calculate MC-STC risk score based on latest MC-STC analysis for current branch.
        Risk score = 1 - MC-STC value (higher MC-STC means lower risk)
        """
        try:
            current_branch = self.default_branch or 'main'
            latest_mcstc = self.mcstc_analyses.filter(
                is_completed=True,
                branch_analyzed=current_branch
            ).first()
            if latest_mcstc and latest_mcstc.mcstc_value is not None:
                return round(1.0 - latest_mcstc.mcstc_value, 3)
        except Exception:
            pass
        return None  # No analysis for current branch
    
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
    
    def update_risk_assessment_timestamp(self):
        """
        Update the last risk assessment timestamp.
        Risk scores are now computed from analysis results.
        """
        self.last_risk_check_at = timezone.now()
        self.save(update_fields=['last_risk_check_at'])


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