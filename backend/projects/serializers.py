"""
Projects API Serializers

This module provides serializers for Project and ProjectMember models.

Models:
- Project: name, repo_url, default_branch, owner_profile, created_at, updated_at
- ProjectMember: project, profile, role, joined_at

Validation Rules:
- Project names are required and limited to 200 characters
- Repository URLs must be valid HTTP/HTTPS or Git SSH URLs
- Each user can only have one role per project
- Project owners cannot be removed or have their role changed
- Repository URLs must be unique across all projects

Role Hierarchy:
1. owner: Full control over the project
2. maintainer: Can manage project settings and members
3. reviewer: Can review code and manage issues
4. member: Basic access to project resources
"""

from rest_framework import serializers
from .models import Project, ProjectMember
from accounts.models import UserProfile


class ProjectCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new projects."""
    
    available_branches = serializers.ListField(
        child=serializers.CharField(),
        read_only=True,
        help_text="List of available branches from the repository"
    )
    
    class Meta:
        model = Project
        fields = ['name', 'repo_url', 'available_branches']
    
    def validate_repo_url(self, value):
        """Validate repository URL format."""
        if not value.startswith(('http://', 'https://', 'git@')):
            raise serializers.ValidationError("Repository URL must be a valid HTTP/HTTPS URL or Git SSH URL.")
        return value
        
    def to_representation(self, instance):
        """Add available branches to the response."""
        from .services import ProjectService
        data = super().to_representation(instance)
        
        # Get available branches from the repository
        try:
            result = ProjectService.get_project_branches(instance)
            branch_names = [b.get('name') for b in result.get('branches', []) if isinstance(b, dict) and b.get('name')]
            data['available_branches'] = branch_names
            
            # Suggest default branch based on common conventions
            if 'main' in branch_names:
                data['suggested_default_branch'] = 'main'
            elif 'master' in branch_names:
                data['suggested_default_branch'] = 'master'
        except Exception as e:
            data['available_branches'] = []
            data['error'] = str(e)
            
        return data


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for Project model with owner information."""
    
    owner_id = serializers.UUIDField(source='owner_profile.user.id', read_only=True)
    owner_username = serializers.CharField(source='owner_profile.user.username', read_only=True)
    owner_email = serializers.EmailField(source='owner_profile.user.email', read_only=True)
    members_count = serializers.SerializerMethodField()
    is_deleted = serializers.BooleanField(read_only=True)
    
    # Latest analysis results
    latest_stc_result = serializers.SerializerMethodField()
    latest_mcstc_result = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'repo_url', 'repo_type', 'default_branch',
            'repository_path', 'auto_run_stc', 'auto_run_mcstc',
            'owner_profile', 'owner_id', 'owner_username', 'owner_email',
            'members_count', 'created_at', 'updated_at', 'is_deleted',
            'stc_risk_score', 'mcstc_risk_score', 'last_risk_check_at',
            'latest_stc_result', 'latest_mcstc_result'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'is_deleted', 'repository_path',
            'stc_risk_score', 'mcstc_risk_score', 'last_risk_check_at',
            'latest_stc_result', 'latest_mcstc_result'
        ]
    
    def get_members_count(self, obj):
        """Get the number of contributors in the project (from TNM analysis)."""
        from contributors.models import ProjectContributor
        return ProjectContributor.objects.filter(project=obj).count()
    
    def get_latest_stc_result(self, obj):
        """Get the latest STC analysis result for this project."""
        try:
            latest_stc = obj.stc_analyses.filter(is_completed=True).first()
            if latest_stc:
                return {
                    'id': str(latest_stc.id),
                    'stc_value': latest_stc.stc_value,
                    'analysis_date': latest_stc.analysis_date.isoformat(),
                    'branch_analyzed': latest_stc.branch_analyzed,
                    'contributors_count': latest_stc.contributors_count,
                    'coordination_efficiency': (
                        latest_stc.coordination_actuals_total / latest_stc.coordination_requirements_total
                        if latest_stc.coordination_requirements_total and latest_stc.coordination_requirements_total > 0
                        else 0
                    )
                }
        except Exception:
            pass
        return None
    
    def get_latest_mcstc_result(self, obj):
        """Get the latest MC-STC analysis result for this project."""
        try:
            latest_mcstc = obj.mcstc_analyses.filter(is_completed=True).first()
            if latest_mcstc:
                return {
                    'id': str(latest_mcstc.id),
                    'mcstc_value': latest_mcstc.mcstc_value,
                    'analysis_date': latest_mcstc.analysis_date.isoformat(),
                    'branch_analyzed': latest_mcstc.branch_analyzed,
                    'total_contributors_analyzed': latest_mcstc.total_contributors_analyzed,
                    'developer_count': latest_mcstc.developer_count,
                    'security_count': latest_mcstc.security_count,
                    'ops_count': latest_mcstc.ops_count,
                    'inter_class_coordination_score': latest_mcstc.inter_class_coordination_score,
                    'intra_class_coordination_score': latest_mcstc.intra_class_coordination_score
                }
        except Exception:
            pass
        return None
    
    def validate_repo_url(self, value):
        """Validate repository URL format."""
        if not value.startswith(('http://', 'https://', 'git@')):
            raise serializers.ValidationError("Repository URL must be a valid HTTP/HTTPS URL or Git SSH URL.")
        return value
    
    def create(self, validated_data):
        """Create a new project using service layer."""
        from .services import ProjectService
        
        # Use service layer to create project
        result = ProjectService.create_project(validated_data, validated_data['owner_profile'])
        return result['project']


class ProjectListSerializer(serializers.ModelSerializer):
    """Simplified serializer for project list views."""
    
    owner_id = serializers.UUIDField(source='owner_profile.user.id', read_only=True)
    owner_username = serializers.CharField(source='owner_profile.user.username', read_only=True)
    members_count = serializers.SerializerMethodField()
    is_deleted = serializers.BooleanField(read_only=True)
    
    # Latest analysis results
    latest_stc_result = serializers.SerializerMethodField()
    latest_mcstc_result = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'repo_url', 'repo_type',
            'repository_path', 'auto_run_stc', 'auto_run_mcstc',
            'owner_id', 'owner_username', 'members_count',
            'stc_risk_score', 'mcstc_risk_score',
            'latest_stc_result', 'latest_mcstc_result',
            'is_deleted', 'created_at'
        ]
    
    def get_members_count(self, obj):
        """Get the number of contributors in the project (from TNM analysis)."""
        from contributors.models import ProjectContributor
        return ProjectContributor.objects.filter(project=obj).count()
    
    def get_latest_stc_result(self, obj):
        """Get the latest STC analysis result for this project."""
        try:
            latest_stc = obj.stc_analyses.filter(is_completed=True).first()
            if latest_stc:
                return {
                    'id': str(latest_stc.id),
                    'stc_value': latest_stc.stc_value,
                    'analysis_date': latest_stc.analysis_date.isoformat(),
                    'branch_analyzed': latest_stc.branch_analyzed,
                    'contributors_count': latest_stc.contributors_count,
                    'coordination_efficiency': (
                        latest_stc.coordination_actuals_total / latest_stc.coordination_requirements_total
                        if latest_stc.coordination_requirements_total and latest_stc.coordination_requirements_total > 0
                        else 0
                    )
                }
        except Exception:
            pass
        return None
    
    def get_latest_mcstc_result(self, obj):
        """Get the latest MC-STC analysis result for this project."""
        try:
            latest_mcstc = obj.mcstc_analyses.filter(is_completed=True).first()
            if latest_mcstc:
                return {
                    'id': str(latest_mcstc.id),
                    'mcstc_value': latest_mcstc.mcstc_value,
                    'analysis_date': latest_mcstc.analysis_date.isoformat(),
                    'branch_analyzed': latest_mcstc.branch_analyzed,
                    'total_contributors_analyzed': latest_mcstc.total_contributors_analyzed,
                    'developer_count': latest_mcstc.developer_count,
                    'security_count': latest_mcstc.security_count,
                    'ops_count': latest_mcstc.ops_count,
                    'inter_class_coordination_score': latest_mcstc.inter_class_coordination_score,
                    'intra_class_coordination_score': latest_mcstc.intra_class_coordination_score
                }
        except Exception:
            pass
        return None


class ProjectMemberSerializer(serializers.ModelSerializer):
    """Serializer for ProjectMember model."""
    
    username = serializers.CharField(source='profile.user.username', read_only=True)
    email = serializers.EmailField(source='profile.user.email', read_only=True)
    first_name = serializers.CharField(source='profile.first_name', read_only=True)
    last_name = serializers.CharField(source='profile.last_name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    
    class Meta:
        model = ProjectMember
        fields = [
            'id', 'project', 'project_name', 'profile', 'username', 
            'email', 'first_name', 'last_name', 'role', 'joined_at'
        ]
        read_only_fields = ['id', 'joined_at']
    
    def validate(self, data):
        """Validate that a user can only have one role per project."""
        project = data.get('project')
        profile = data.get('profile')
        
        if project and profile:
            existing_member = ProjectMember.objects.filter(
                project=project, 
                profile=profile
            ).exclude(id=self.instance.id if self.instance else None)
            
            if existing_member.exists():
                raise serializers.ValidationError(
                    "This user is already a member of this project."
                )
        
        return data


class ProjectMemberCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new project members."""
    
    username = serializers.CharField(write_only=True)
    
    class Meta:
        model = ProjectMember
        fields = ['project', 'username', 'role']
    
    def validate_username(self, value):
        """Validate that the username exists."""
        try:
            from accounts.models import User
            user = User.objects.get(username=value)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this username does not exist.")
    
    def create(self, validated_data):
        """Create a new project member using service layer."""
        from .services import ProjectService
        
        project = validated_data['project']
        username = validated_data.pop('username')
        role = validated_data['role']
        
        # Use service layer to add member (we need a user_profile for permission check)
        # This will be handled in the view where we have access to request.user
        from accounts.models import User
        user = User.objects.get(username=username)
        profile = user.profile
        
        return ProjectMember.objects.create(
            project=project,
            profile=profile,
            role=role
        )


class ProjectStatsSerializer(serializers.Serializer):
    """Serializer for project statistics."""
    
    total_projects = serializers.IntegerField()
    total_members = serializers.IntegerField()
    projects_by_owner = serializers.DictField()
    recent_projects = ProjectListSerializer(many=True)
