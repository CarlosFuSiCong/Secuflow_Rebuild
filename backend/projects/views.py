"""
Projects API Views

This module provides comprehensive CRUD operations for managing software projects 
and their members in the Secuflow system.

API Endpoints:
- GET    /api/projects/projects/           - List all projects
  Query Parameters:
  - q: Search query (name, repo_url, description)
  - repo_type: Filter by repository type (github/gitlab/bitbucket/other)
  - role: Filter by user role (owner/member) - replaces my_projects and joined_projects
  - sort: Sort field (-created_at/name/repo_type)
  - include_deleted: Include soft-deleted projects (true/false)
  - page: Page number
  - page_size: Items per page

- POST   /api/projects/projects/           - Create new project
- GET    /api/projects/projects/{id}/      - Get project details
- PUT    /api/projects/projects/{id}/      - Update project
- DELETE /api/projects/projects/{id}/      - Delete project
- GET    /api/projects/projects/{id}/members/ - Get project members
- POST   /api/projects/projects/{id}/add_member/ - Add member
- DELETE /api/projects/projects/{id}/members/{member_id}/ - Remove member
- PATCH  /api/projects/projects/{id}/members/{member_id}/ - Update member role
- GET    /api/projects/projects/stats/     - Get project statistics

Authentication: All endpoints require JWT authentication
Permissions: 
- List/Create: Any authenticated user
- View Details: Project owner or member
- Update/Delete: Project owner only
- Member Management: Project owner only

Role Hierarchy:
1. owner: Full control over the project
2. maintainer: Can manage project settings and members
3. reviewer: Can review code and manage issues
4. member: Basic access to project resources
"""

import logging
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from accounts.models import User
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError

from .models import Project, ProjectMember, ProjectRole
from .serializers import (
    ProjectSerializer, ProjectCreateSerializer, ProjectListSerializer, ProjectMemberSerializer,
    ProjectMemberCreateSerializer, ProjectStatsSerializer
)
from .services import ProjectService
from common.git_utils import GitPermissionError
from accounts.models import UserProfile
from common.response import ApiResponse

# Initialize logger for projects API
logger = logging.getLogger(__name__)


class ProjectPagination(PageNumberPagination):
    """Custom pagination for project list."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing projects.
    
    Provides CRUD operations for projects with proper permissions.
    Only project owners and members can access project details.
    """
    
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    pagination_class = ProjectPagination
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ProjectListSerializer
        elif self.action == 'create':
            return ProjectCreateSerializer
        return ProjectSerializer
    
    def get_queryset(self):
        """Filter projects based on user permissions using service layer."""
        user = self.request.user
        user_profile = getattr(user, 'profile', None)
        
        if not user_profile:
            return Project.objects.none()
        
        # For detail actions, return an unsliced queryset to avoid DRF filtering on a sliced QS
        # which raises: "Cannot filter a query once a slice has been taken."
        if getattr(self, 'action', None) and self.action != 'list':
            return Project.objects.all()
        
        # List action: use service-layer search (may apply slicing for manual pagination)
        query = self.request.query_params.get('q')
        repo_type = self.request.query_params.get('repo_type')
        role = self.request.query_params.get('role')
        sort_by = self.request.query_params.get('sort', '-created_at')
        include_deleted = self.request.query_params.get('include_deleted', '').lower() == 'true'
        
        # Validate sort field
        valid_sort_fields = ['created_at', '-created_at', 'name', '-name', 'repo_type', '-repo_type']
        if sort_by not in valid_sort_fields:
            sort_by = '-created_at'
        
        # Return all objects for list action here because we override list() method
        # to handle pagination manually via service layer.
        return Project.objects.none()

    def list(self, request, *args, **kwargs):
        """
        List projects using service layer search.
        Overrides default list to avoid double pagination issues with sliced querysets.
        """
        user_profile = getattr(request.user, 'profile', None)
        if not user_profile:
             return ApiResponse.success(data={
                'results': [],
                'count': 0,
                'next': None,
                'previous': None
            })

        query = request.query_params.get('q')
        repo_type = request.query_params.get('repo_type')
        role = request.query_params.get('role')
        sort_by = request.query_params.get('sort', '-created_at')
        include_deleted = request.query_params.get('include_deleted', '').lower() == 'true'
        
        # Validate sort field
        valid_sort_fields = ['created_at', '-created_at', 'name', '-name', 'repo_type', '-repo_type']
        if sort_by not in valid_sort_fields:
            sort_by = '-created_at'

        # Parse pagination
        try:
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
        except ValueError:
            page = 1
            page_size = 20

        # Use service layer to get paginated results
        result = ProjectService.search_projects(
            user_profile=user_profile,
            query=query,
            repo_type=repo_type,
            role=role,
            sort_by=sort_by,
            include_deleted=include_deleted,
            page=page,
            page_size=page_size
        )

        serializer = ProjectListSerializer(result['projects'], many=True)
        
        # Manually construct paginated response
        base_url = request.build_absolute_uri().split('?')[0]
        
        next_link = None
        if page < result['total_pages']:
            params = request.query_params.copy()
            params['page'] = page + 1
            next_link = f"{base_url}?{params.urlencode()}"
            
        previous_link = None
        if page > 1:
            params = request.query_params.copy()
            params['page'] = page - 1
            previous_link = f"{base_url}?{params.urlencode()}"

        return ApiResponse.success(data={
            'results': serializer.data,
            'count': result['count'],
            'next': next_link,
            'previous': previous_link
        })

    
    def create(self, request, *args, **kwargs):
        """Create a new project using service layer."""
        user_id = request.user.id if request.user else None
        project_name = request.data.get('name', '')
        
        logger.info("Creating new project", extra={
            'user_id': user_id,
            'project_name': project_name
        })
        
        try:
            user_profile = request.user.profile
            
            # Use service layer to create project
            result = ProjectService.create_project(request.data, user_profile)
            
            logger.info("Project created successfully", extra={
                'user_id': user_id,
                'project_name': project_name,
                'project_id': result['project'].id
            })
            
            serializer = self.get_serializer(result['project'])
            return ApiResponse.created(
                data=serializer.data,
                message=result.get('message', 'Project created successfully')
            )
            
        except GitPermissionError as e:
            logger.warning("Project creation failed - Git permission error", extra={
                'user_id': user_id,
                'project_name': project_name,
                'error_type': e.error_type,
                'error': str(e)
            })
            return ApiResponse.error(
                error_message=e.message,
                error_code=f"GIT_{e.error_type}",
                status_code=status.HTTP_403_FORBIDDEN,
                data={
                    'error_type': e.error_type,
                    'solution': e.solution,
                    'stderr': e.stderr
                }
            )
        except ValidationError as e:
            logger.warning("Project creation failed - validation error", extra={
                'user_id': user_id,
                'project_name': project_name,
                'error': str(e)
            })
            return ApiResponse.error(
                error_message=str(e),
                error_code="PROJECT_CREATION_ERROR"
            )
        except Exception as e:
            logger.error("Project creation failed - system error", extra={
                'user_id': user_id,
                'project_name': project_name,
                'error': str(e)
            }, exc_info=True)
            return ApiResponse.internal_error(
                error_message="Project creation failed",
                error_code="PROJECT_CREATION_ERROR"
            )
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'create']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve project details using service layer."""
        try:
            project = self.get_object()
            user_profile = request.user.profile
            
            # Use service layer to check access
            if not ProjectService.check_project_access(project, user_profile):
                return ApiResponse.forbidden(
                    error_message="You do not have permission to view this project",
                    error_code="ACCESS_DENIED"
                )
            
            serializer = self.get_serializer(project)
            return ApiResponse.success(
                data=serializer.data,
                message="Project retrieved successfully"
            )
            
        except Exception as e:
            return ApiResponse.internal_error(
                error_message="Failed to retrieve project",
                error_code="PROJECT_RETRIEVAL_ERROR"
            )
    
    def update(self, request, *args, **kwargs):
        """Update project using service layer."""
        try:
            project = self.get_object()
            user_profile = request.user.profile
            
            # Use service layer to update project
            result = ProjectService.update_project(project, request.data, user_profile)
            
            serializer = self.get_serializer(result['project'])
            return ApiResponse.success(
                data=serializer.data,
                message=result.get('message', 'Project updated successfully')
            )
            
        except ValidationError as e:
            return ApiResponse.error(
                error_message=str(e),
                error_code="PROJECT_UPDATE_ERROR"
            )
        except Exception as e:
            return ApiResponse.internal_error(
                error_message="Project update failed",
                error_code="PROJECT_UPDATE_ERROR"
            )
    
    def destroy(self, request, *args, **kwargs):
        """Delete project using service layer."""
        try:
            project = self.get_object()
            user_profile = request.user.profile
            
            # Use service layer to delete project
            result = ProjectService.delete_project(project, user_profile)
            
            return ApiResponse.success(
                message=result['message']
            )
            
        except ValidationError as e:
            return ApiResponse.error(
                error_message=str(e),
                error_code="PROJECT_DELETION_ERROR"
            )
        except Exception as e:
            logger.error("Project deletion failed", extra={
                'user_id': request.user.id if request and request.user else None,
                'project_id': locals().get('project').id if 'project' in locals() else None,
                'error': str(e)
            }, exc_info=True)
            return ApiResponse.internal_error(
                error_message=f"Project deletion failed: {str(e)}",
                error_code="PROJECT_DELETION_ERROR"
            )
    
    @action(detail=True, methods=['get'])
    def members(self, request, id=None):
        """Get all members of a project using service layer."""
        try:
            project = self.get_object()
            user_profile = request.user.profile
            
            # Use service layer to get project members
            result = ProjectService.get_project_members(project, user_profile)
            
            serializer = ProjectMemberSerializer(result['members'], many=True)
            return ApiResponse.success(
                data=serializer.data,
                message=result.get('message', 'Project members retrieved successfully')
            )
            
        except ValidationError as e:
            return ApiResponse.forbidden(
                error_message=str(e),
                error_code="ACCESS_DENIED"
            )
        except Exception as e:
            return ApiResponse.internal_error(
                error_message="Failed to get project members",
                error_code="MEMBERS_RETRIEVAL_ERROR"
            )
    
    @action(detail=True, methods=['post'])
    def add_member(self, request, id=None):
        """Add a new member to the project using service layer."""
        try:
            project = self.get_object()
            user_profile = request.user.profile
            
            user_id = request.data.get('user_id')
            role_id = request.data.get('role_id', 3)  # Default to reviewer (ID: 3)
            
            if not user_id:
                return ApiResponse.error(
                    error_message="user_id is required",
                    error_code="MISSING_USER_ID"
                )
            
            if not role_id:
                return ApiResponse.error(
                    error_message="role_id is required",
                    error_code="MISSING_ROLE_ID"
                )
            
            # Use service layer to add member
            result = ProjectService.add_project_member_by_user_id(project, user_id, role_id, user_profile)
            
            serializer = ProjectMemberSerializer(result['member'])
            return ApiResponse.created(
                data=serializer.data,
                message=result.get('message', 'Member added successfully')
            )
            
        except ValidationError as e:
            return ApiResponse.error(
                error_message=str(e),
                error_code="MEMBER_ADDITION_ERROR"
            )
        except Exception as e:
            return ApiResponse.internal_error(
                error_message="Failed to add member",
                error_code="MEMBER_ADDITION_ERROR"
            )
    
    
    
    @action(detail=True, methods=['delete'], url_path='members/by-user/(?P<user_id>[^/.]+)')
    def remove_member_by_user(self, request, id=None, user_id=None):
        """Remove a member by user UUID using service layer."""
        try:
            project = self.get_object()
            user_profile = request.user.profile
            result = ProjectService.remove_project_member_by_user_id(project, user_id, user_profile)
            return ApiResponse.success(
                message=result['message']
            )
        except ValidationError as e:
            return ApiResponse.error(
                error_message=str(e),
                error_code="MEMBER_REMOVAL_ERROR"
            )
        except Exception:
            return ApiResponse.internal_error(
                error_message="Failed to remove member",
                error_code="MEMBER_REMOVAL_ERROR"
            )

    

    @action(detail=True, methods=['patch'], url_path='members/by-user/(?P<user_id>[^/.]+)')
    def update_member_role_by_user(self, request, id=None, user_id=None):
        """Update a member's role by user UUID using service layer."""
        try:
            project = self.get_object()
            user_profile = request.user.profile
            new_role = request.data.get('role')
            if not new_role:
                return ApiResponse.error(
                    error_message="Role is required",
                    error_code="MISSING_ROLE"
                )
            result = ProjectService.update_member_role_by_user_id(project, user_id, new_role, user_profile)
            serializer = ProjectMemberSerializer(result['member'])
            return ApiResponse.success(
                data=serializer.data,
                message=result.get('message', 'Member role updated successfully')
            )
        except ValidationError as e:
            return ApiResponse.error(
                error_message=str(e),
                error_code="MEMBER_ROLE_UPDATE_ERROR"
            )
        except Exception:
            return ApiResponse.internal_error(
                error_message="Failed to update member role",
                error_code="MEMBER_ROLE_UPDATE_ERROR"
            )
    
    
    @action(detail=False, methods=['get'])
    def selectable_projects(self, request):
        """Get projects that user can select for TNM analysis (owned or maintainer role)."""
        try:
            user_profile = request.user.profile
            
            # Get projects where user is owner or maintainer (can run TNM)
            user_projects = Project.objects.filter(
                Q(owner_profile=user_profile) | 
                Q(members__profile=user_profile, members__role__in=[ProjectRole.OWNER, ProjectRole.MAINTAINER])
            ).distinct().order_by('-created_at')
            
            # Filter projects that have repositories
            projects_with_repos = user_projects.filter(repo_url__isnull=False).exclude(repo_url='')
            
            page = self.paginate_queryset(projects_with_repos)
            if page is not None:
                serializer = ProjectListSerializer(page, many=True)
                # Build paginated response manually using ApiResponse to avoid rendering issues
                paginator = self.paginator
                return ApiResponse.success(data={
                    'results': serializer.data,
                    'count': paginator.page.paginator.count,
                    'next': paginator.get_next_link(),
                    'previous': paginator.get_previous_link()
                })
            
            serializer = ProjectListSerializer(projects_with_repos, many=True)
            return ApiResponse.success(
                data={
                    'projects': serializer.data,
                    'count': projects_with_repos.count()
                },
                message='Projects available for TNM analysis'
            )
            
        except Exception as e:
            return ApiResponse.internal_error(
                error_message="Failed to get selectable projects",
                error_code="SELECTABLE_PROJECTS_ERROR"
            )

    @action(detail=False, methods=['post'])
    def select_project(self, request):
        """Persist user's selected project for quick TNM operations.
        Body: { "project_uid": "<uuid>" }
        """
        try:
            user_profile = request.user.profile
            project_uid = request.data.get('project_uid')
            if not project_uid:
                return ApiResponse.error('project_uid is required', error_code='MISSING_PROJECT_UID', status_code=status.HTTP_400_BAD_REQUEST)
            project = Project.objects.filter(id=project_uid).first()
            if not project:
                return ApiResponse.not_found('Project not found')
            # Only owner or maintainer can select for TNM
            membership = project.members.filter(profile=user_profile).first()
            if not (project.owner_profile == user_profile or (membership and membership.role in [ProjectRole.OWNER, ProjectRole.MAINTAINER])):
                return ApiResponse.forbidden('Only project owner or maintainer can select this project')
            user_profile.selected_project = project
            user_profile.save(update_fields=['selected_project'])
            return ApiResponse.success(data={'project_uid': str(project.id), 'project_name': project.name}, message='Selected project updated')
        except Exception:
            return ApiResponse.internal_error('Failed to select project', error_code='SELECT_PROJECT_ERROR')
    
    @action(detail=False, methods=['get'])
    def roles(self, request):
        """Get all available project roles."""
        try:
            roles = ProjectRole.get_all_roles()
            return ApiResponse.success(
                data=roles,
                message="Project roles retrieved successfully"
            )
        except Exception as e:
            return ApiResponse.internal_error(
                error_message="Failed to get project roles",
                error_code="ROLES_RETRIEVAL_ERROR"
            )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get project statistics for the current user using service layer."""
        try:
            user_profile = request.user.profile
            
            # Use service layer to get project statistics
            result = ProjectService.get_project_stats(user_profile)
            
            serializer = ProjectStatsSerializer(result)
            return ApiResponse.success(data=serializer.data)
            
        except ValidationError as e:
            return ApiResponse.error(
                error_message=str(e),
                error_code="PROJECT_STATS_ERROR",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return ApiResponse.internal_error(
                error_message="Failed to get project statistics",
                error_code="PROJECT_STATS_ERROR"
            )
    
    @action(detail=True, methods=['patch'])
    def update_branch(self, request, id=None):
        """Update project's default branch using service layer."""
        try:
            project = self.get_object()
            user_profile = request.user.profile
            
            new_branch = request.data.get('branch')
            if not new_branch:
                return ApiResponse.error('Branch name is required', error_code='MISSING_BRANCH', status_code=status.HTTP_400_BAD_REQUEST)
            
            # Use service layer to update branch
            result = ProjectService.update_project_branch(project, new_branch, user_profile)
            
            serializer = self.get_serializer(result['project'])
            return ApiResponse.success(data={'project': serializer.data}, message=result['message'])
            
        except ValidationError as e:
            error_message = str(e)
            if "permission" in error_message.lower() or "owner" in error_message.lower() or "maintainer" in error_message.lower():
                return ApiResponse.forbidden(error_message='Permission denied', error_code='PERMISSION_DENIED')
            else:
                return ApiResponse.error(
                    error_message=str(e),
                    error_code='UPDATE_BRANCH_ERROR',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return ApiResponse.internal_error(
                error_message=str(e),
                error_code='UPDATE_BRANCH_ERROR'
            )
    
    @action(detail=True, methods=['get'])
    def branches(self, request, id=None):
        """Get all branches for a project's repository using service layer."""
        try:
            project = self.get_object()
            user_profile = request.user.profile
            
            # Check if user has access to the project
            if not ProjectService.check_project_access(project, user_profile):
                return ApiResponse.forbidden(
                    error_message="You do not have permission to view this project",
                    error_code="ACCESS_DENIED"
                )
            
            # Use service layer to get branches
            result = ProjectService.get_project_branches(project)
            
            return ApiResponse.success(
                data={
                    'branches': result['branches'],
                    'current_branch': result['current_branch'],
                    'repository_path': result['repository_path']
                },
                message="Project branches retrieved successfully"
            )
            
        except ValidationError as e:
            return ApiResponse.error(
                error_message=str(e),
                error_code="BRANCHES_RETRIEVAL_ERROR"
            )
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error("Error in branches", extra={
                'error': str(e),
                'traceback': error_details
            })
            return ApiResponse.internal_error(
                error_message="Failed to get branches",
                error_code="BRANCHES_RETRIEVAL_ERROR"
            )
    
    @action(detail=True, methods=['post'])
    def switch_branch(self, request, id=None):
        """Switch to a different branch in the project's repository using service layer."""
        try:
            project = self.get_object()
            user_profile = request.user.profile
            
            # Check if user has permission to update project settings
            user_membership = project.members.filter(profile=user_profile).first()
            if not (project.owner_profile == user_profile or 
                    (user_membership and user_membership.role in [ProjectRole.OWNER, ProjectRole.MAINTAINER])):
                return ApiResponse.forbidden(
                    error_message="Only project owner or maintainer can switch branches",
                    error_code="ACCESS_DENIED"
                )
            
            branch_id = request.data.get('branch_id')
            
            if not branch_id:
                return ApiResponse.error(
                    error_message="branch_id is required",
                    error_code="MISSING_BRANCH_ID"
                )
            
            # Get all branches to find the one with matching branch_id
            branches_result = ProjectService.get_project_branches(project)
            target_branch = None
            for branch in branches_result['branches']:
                if branch['branch_id'] == branch_id:
                    target_branch = branch
                    break
            
            if not target_branch:
                return ApiResponse.error(
                    error_message=f"Branch with ID {branch_id} not found",
                    error_code="BRANCH_NOT_FOUND"
                )
            
            branch_name = target_branch['name']
            
            # Use service layer to switch branch
            result = ProjectService.switch_project_branch(project, branch_name)
            
            serializer = self.get_serializer(result['project'])
            return ApiResponse.success(
                data={
                    'project': serializer.data,
                    'current_branch': result['current_branch']
                },
                message=result['message']
            )
            
        except ValidationError as e:
            return ApiResponse.error(
                error_message=str(e),
                error_code="BRANCH_SWITCH_ERROR"
            )
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error("Error in switch_branch", extra={
                'error': str(e),
                'traceback': error_details
            })
            return ApiResponse.internal_error(
                error_message="Failed to switch branch",
                error_code="BRANCH_SWITCH_ERROR"
            )
    
    @action(detail=False, methods=['post'])
    def validate_repository(self, request):
        """Validate a repository URL and get its branches using service layer."""
        try:
            user_profile = request.user.profile
            repo_url = request.data.get('repo_url')
            
            if not repo_url:
                return ApiResponse.error('Repository URL is required', error_code='MISSING_REPO_URL', status_code=status.HTTP_400_BAD_REQUEST)
            
            # Use service layer to validate repository
            result = ProjectService.validate_and_clone_repository(repo_url, user_profile)
            
            return ApiResponse.success(
                data={
                    'valid': True,
                    'branches': result['branches'],
                    'default_branch': result['default_branch'],
                    'repo_url': result['repo_url']
                },
                message=result['message']
            )
            
        except GitPermissionError as e:
            return ApiResponse.error(
                error_message=e.message,
                error_code=f'GIT_{e.error_type}',
                status_code=status.HTTP_403_FORBIDDEN,
                data={
                    'valid': False,
                    'error_type': e.error_type,
                    'solution': e.solution,
                    'stderr': e.stderr
                }
            )
        except ValidationError as e:
            return ApiResponse.error(
                error_message=str(e),
                error_code='REPO_VALIDATION_ERROR',
                status_code=status.HTTP_400_BAD_REQUEST,
                data={'valid': False}
            )
        except Exception as e:
            return ApiResponse.internal_error(
                error_message='Repository validation failed',
                error_code='REPO_VALIDATION_ERROR'
            )
    
    @action(detail=True, methods=['post'])
    def retry_repository_access(self, request, id=None):
        """Retry repository access after fixing authentication issues."""
        try:
            project = self.get_object()
            user_profile = request.user.profile
            
            # Check if user has permission to update project
            if not ProjectService.check_project_access(project, user_profile):
                return ApiResponse.forbidden(
                    error_message="You do not have permission to access this project",
                    error_code="ACCESS_DENIED"
                )
            
            if not project.repo_url:
                return ApiResponse.error(
                    error_message="Project has no repository URL configured",
                    error_code="NO_REPOSITORY_URL"
                )
            
            logger.info("Retrying repository access", extra={
                'user_id': request.user.id,
                'project_id': project.id,
                'repo_url': project.repo_url
            })
            
            # Try to validate repository access again
            try:
                validation_result = ProjectService.validate_and_clone_repository(project.repo_url, user_profile)
                
                # Try to clone/update the repository if validation succeeds
                try:
                    clone_result = ProjectService.clone_repository_for_project(project, project.repo_url)
                    
                    logger.info("Repository retry successful - cloned", extra={
                        'user_id': request.user.id,
                        'project_id': project.id,
                        'used_authentication': clone_result.get('used_authentication', False)
                    })
                    
                    return ApiResponse.success(
                        data={
                            'status': 'success',
                            'action': 'cloned',
                            'repository_info': {
                                'branches': clone_result.get('branches', []),
                                'current_branch': clone_result.get('current_branch'),
                                'used_authentication': clone_result.get('used_authentication', False)
                            }
                        },
                        message="Repository access restored and repository cloned successfully"
                    )
                    
                except Exception as clone_error:
                    # If cloning fails but validation succeeded, still report partial success
                    logger.warning("Repository retry partially successful - validation only", extra={
                        'user_id': request.user.id,
                        'project_id': project.id,
                        'clone_error': str(clone_error)
                    })
                    
                    return ApiResponse.success(
                        data={
                            'status': 'partial_success',
                            'action': 'validated',
                            'validation_info': {
                                'branches': validation_result.get('branches', []),
                                'default_branch': validation_result.get('default_branch'),
                                'used_authentication': validation_result.get('used_authentication', False)
                            },
                            'warning': f"Repository is accessible but cloning failed: {str(clone_error)}"
                        },
                        message="Repository access restored but cloning failed"
                    )
                    
            except GitPermissionError as e:
                logger.warning("Repository retry failed - still permission issues", extra={
                    'user_id': request.user.id,
                    'project_id': project.id,
                    'error_type': e.error_type,
                    'error': str(e)
                })
                
                return ApiResponse.error(
                    error_message=f"Repository access still failed: {e.message}",
                    error_code=f"GIT_{e.error_type}",
                    status_code=status.HTTP_403_FORBIDDEN,
                    data={
                        'status': 'failed',
                        'error_type': e.error_type,
                        'solution': e.solution,
                        'stderr': e.stderr
                    }
                )
                
        except Exception as e:
            logger.error("Repository retry failed - system error", extra={
                'user_id': request.user.id,
                'project_id': project.id if 'project' in locals() else None,
                'error': str(e)
            }, exc_info=True)
            return ApiResponse.internal_error(
                error_message="Failed to retry repository access",
                error_code="REPOSITORY_RETRY_ERROR"
            )


class ProjectMemberViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing project members.
    
    Provides CRUD operations for project members with proper permissions.
    """
    
    queryset = ProjectMember.objects.all()
    serializer_class = ProjectMemberSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter project members based on user permissions."""
        user_profile = self.request.user.profile
        
        # Return members of projects where user is owner or member
        return ProjectMember.objects.filter(
            Q(project__owner_profile=user_profile) | 
            Q(project__members__profile=user_profile)
        ).distinct().order_by('-joined_at')
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def create(self, request, *args, **kwargs):
        """Create a new project member with owner permission check."""
        project_id = request.data.get('project')
        if not project_id:
            return Response(
                {'error': 'Project ID is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {'error': 'Project not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        user_profile = request.user.profile
        
        # Only owner can add members
        if project.owner_profile != user_profile:
            return Response(
                {'error': 'Only project owner can add members.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ProjectMemberCreateSerializer(data=request.data)
        if serializer.is_valid():
            member = serializer.save()
            response_serializer = ProjectMemberSerializer(member)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """Update project member with owner permission check."""
        member = self.get_object()
        user_profile = request.user.profile
        
        # Only owner can update members
        if member.project.owner_profile != user_profile:
            return Response(
                {'error': 'Only project owner can update member details.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Prevent changing owner role
        if member.role == ProjectRole.OWNER:
            return Response(
                {'error': 'Cannot change project owner role.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete project member with owner permission check."""
        member = self.get_object()
        user_profile = request.user.profile
        
        # Only owner can remove members
        if member.project.owner_profile != user_profile:
            return Response(
                {'error': 'Only project owner can remove members.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Prevent removing the owner
        if member.role == ProjectRole.OWNER:
            return Response(
                {'error': 'Cannot remove project owner.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().destroy(request, *args, **kwargs)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cleanup_tnm_data(request, project_id=None):
    """
    Clean up TNM output and repository data.
    
    POST /api/projects/cleanup-tnm-data/                    # Clean all data (admin only)
    POST /api/projects/projects/{project_id}/cleanup-tnm/  # Clean specific project data
    
    Body: {
        "cleanup_type": "output" | "repositories" | "all",  # What to clean
        "confirm": true,                                     # Confirmation flag
        "older_than_days": 7                                # Optional: only clean files older than N days
    }
    """
    import os
    import shutil
    from datetime import datetime, timedelta
    from django.conf import settings
    
    try:
        # Parse request data
        cleanup_type = request.data.get('cleanup_type', 'all')
        confirm = request.data.get('confirm', False)
        older_than_days = request.data.get('older_than_days')
        
        if not confirm:
            return ApiResponse.error(
                error_message="Cleanup requires confirmation. Set 'confirm': true in request body.",
                error_code="CONFIRMATION_REQUIRED"
            )
        
        # Check permissions
        if project_id:
            # Project-specific cleanup - check project access
            try:
                project = Project.objects.get(id=project_id, deleted_at__isnull=True)
                user_profile = request.user.profile
                
                if not (project.owner_profile == user_profile or 
                        project.members.filter(profile=user_profile).exists()):
                    return ApiResponse.forbidden("You don't have access to this project")
                    
            except Project.DoesNotExist:
                return ApiResponse.not_found("Project not found")
        else:
            # Global cleanup - admin only
            if not request.user.is_staff:
                return ApiResponse.forbidden("Only administrators can perform global cleanup")
        
        # Define paths
        tnm_output_dir = getattr(settings, 'TNM_OUTPUT_DIR', '/app/tnm_output')
        tnm_repos_dir = getattr(settings, 'TNM_REPOSITORIES_DIR', '/app/tnm_repositories')
        
        # If running locally, use backend paths
        if not os.path.exists(tnm_output_dir):
            tnm_output_dir = os.path.join(os.path.dirname(settings.BASE_DIR), 'tnm_output')
        if not os.path.exists(tnm_repos_dir):
            tnm_repos_dir = os.path.join(os.path.dirname(settings.BASE_DIR), 'tnm_repositories')
        
        cleanup_results = {
            'output_cleaned': False,
            'repositories_cleaned': False,
            'files_removed': 0,
            'directories_removed': 0,
            'total_size_freed_mb': 0
        }
        
        # Calculate cutoff time if older_than_days is specified
        cutoff_time = None
        if older_than_days:
            cutoff_time = datetime.now() - timedelta(days=older_than_days)
        
        # Helper function to check if path should be cleaned
        def should_clean_path(path):
            if not cutoff_time:
                return True
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(path))
                return mtime < cutoff_time
            except:
                return True
        
        # Helper function to calculate directory size
        def get_dir_size(path):
            total_size = 0
            try:
                for dirpath, dirnames, filenames in os.walk(path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        if os.path.exists(filepath):
                            total_size += os.path.getsize(filepath)
            except:
                pass
            return total_size
        
        # Clean TNM output
        if cleanup_type in ['output', 'all']:
            if project_id:
                # Clean specific project output
                project_pattern = f"project_{project_id}_*"
                output_path = tnm_output_dir
                
                if os.path.exists(output_path):
                    for item in os.listdir(output_path):
                        item_path = os.path.join(output_path, item)
                        if (item.startswith(f"project_{project_id}_") and 
                            should_clean_path(item_path)):
                            
                            if os.path.isdir(item_path):
                                size_before = get_dir_size(item_path)
                                shutil.rmtree(item_path)
                                cleanup_results['directories_removed'] += 1
                                cleanup_results['total_size_freed_mb'] += size_before / (1024 * 1024)
                            else:
                                size_before = os.path.getsize(item_path)
                                os.remove(item_path)
                                cleanup_results['files_removed'] += 1
                                cleanup_results['total_size_freed_mb'] += size_before / (1024 * 1024)
            else:
                # Clean all output
                if os.path.exists(tnm_output_dir):
                    for item in os.listdir(tnm_output_dir):
                        if item in ['.', '..', 'README.md']:
                            continue
                            
                        item_path = os.path.join(tnm_output_dir, item)
                        if should_clean_path(item_path):
                            if os.path.isdir(item_path):
                                size_before = get_dir_size(item_path)
                                shutil.rmtree(item_path)
                                cleanup_results['directories_removed'] += 1
                                cleanup_results['total_size_freed_mb'] += size_before / (1024 * 1024)
                            else:
                                size_before = os.path.getsize(item_path)
                                os.remove(item_path)
                                cleanup_results['files_removed'] += 1
                                cleanup_results['total_size_freed_mb'] += size_before / (1024 * 1024)
            
            cleanup_results['output_cleaned'] = True
        
        # Clean TNM repositories
        if cleanup_type in ['repositories', 'all']:
            if project_id:
                # Clean specific project repository
                repo_path = os.path.join(tnm_repos_dir, f"project_{project_id}")
                if os.path.exists(repo_path) and should_clean_path(repo_path):
                    size_before = get_dir_size(repo_path)
                    shutil.rmtree(repo_path)
                    cleanup_results['directories_removed'] += 1
                    cleanup_results['total_size_freed_mb'] += size_before / (1024 * 1024)
            else:
                # Clean all repositories
                if os.path.exists(tnm_repos_dir):
                    for item in os.listdir(tnm_repos_dir):
                        if item in ['.', '..', 'README.md']:
                            continue
                            
                        item_path = os.path.join(tnm_repos_dir, item)
                        if should_clean_path(item_path):
                            if os.path.isdir(item_path):
                                size_before = get_dir_size(item_path)
                                shutil.rmtree(item_path)
                                cleanup_results['directories_removed'] += 1
                                cleanup_results['total_size_freed_mb'] += size_before / (1024 * 1024)
                            else:
                                size_before = os.path.getsize(item_path)
                                os.remove(item_path)
                                cleanup_results['files_removed'] += 1
                                cleanup_results['total_size_freed_mb'] += size_before / (1024 * 1024)
            
            cleanup_results['repositories_cleaned'] = True
        
        # Round the size
        cleanup_results['total_size_freed_mb'] = round(cleanup_results['total_size_freed_mb'], 2)
        
        logger.info(f"TNM cleanup completed", extra={
            'user_id': request.user.id,
            'project_id': project_id,
            'cleanup_type': cleanup_type,
            'results': cleanup_results
        })
        
        message = f"Cleanup completed. Removed {cleanup_results['files_removed']} files and {cleanup_results['directories_removed']} directories, freed {cleanup_results['total_size_freed_mb']} MB"
        
        return ApiResponse.success(
            data=cleanup_results,
            message=message
        )
        
    except Exception as e:
        logger.error(f"TNM cleanup failed: {e}", extra={
            'user_id': request.user.id,
            'project_id': project_id
        }, exc_info=True)
        return ApiResponse.internal_error(
            error_message="Failed to cleanup TNM data",
            error_code="CLEANUP_ERROR"
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def auto_cleanup_tnm_data(request):
    """
    Automatic cleanup of old TNM data based on configurable rules.
    
    POST /api/projects/auto-cleanup-tnm/
    
    Body: {
        "dry_run": false,                    # If true, only report what would be cleaned
        "output_retention_days": 30,        # Keep output files for N days
        "repository_retention_days": 7,     # Keep repository clones for N days
        "max_total_size_gb": 10             # Clean oldest files if total size exceeds N GB
    }
    """
    import os
    import shutil
    from datetime import datetime, timedelta
    from django.conf import settings
    
    try:
        # Parse request data
        dry_run = request.data.get('dry_run', False)
        output_retention_days = request.data.get('output_retention_days', 30)
        repository_retention_days = request.data.get('repository_retention_days', 7)
        max_total_size_gb = request.data.get('max_total_size_gb', 10)
        
        # Only admins can run auto cleanup
        if not request.user.is_staff:
            return ApiResponse.forbidden("Only administrators can run auto cleanup")
        
        # Define paths
        tnm_output_dir = getattr(settings, 'TNM_OUTPUT_DIR', '/app/tnm_output')
        tnm_repos_dir = getattr(settings, 'TNM_REPOSITORIES_DIR', '/app/tnm_repositories')
        
        # If running locally, use backend paths
        if not os.path.exists(tnm_output_dir):
            tnm_output_dir = os.path.join(os.path.dirname(settings.BASE_DIR), 'tnm_output')
        if not os.path.exists(tnm_repos_dir):
            tnm_repos_dir = os.path.join(os.path.dirname(settings.BASE_DIR), 'tnm_repositories')
        
        cleanup_plan = {
            'output_files_to_clean': [],
            'repository_dirs_to_clean': [],
            'total_size_to_free_mb': 0,
            'current_total_size_gb': 0
        }
        
        # Helper functions
        def get_dir_size(path):
            total_size = 0
            try:
                for dirpath, dirnames, filenames in os.walk(path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        if os.path.exists(filepath):
                            total_size += os.path.getsize(filepath)
            except:
                pass
            return total_size
        
        def get_path_info(path):
            try:
                stat = os.stat(path)
                return {
                    'path': path,
                    'size_mb': (stat.st_size if os.path.isfile(path) else get_dir_size(path)) / (1024 * 1024),
                    'modified_time': datetime.fromtimestamp(stat.st_mtime),
                    'age_days': (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days
                }
            except:
                return None
        
        # Calculate current total size
        total_size = 0
        if os.path.exists(tnm_output_dir):
            total_size += get_dir_size(tnm_output_dir)
        if os.path.exists(tnm_repos_dir):
            total_size += get_dir_size(tnm_repos_dir)
        
        cleanup_plan['current_total_size_gb'] = round(total_size / (1024 * 1024 * 1024), 2)
        
        # Find old output files
        output_cutoff = datetime.now() - timedelta(days=output_retention_days)
        if os.path.exists(tnm_output_dir):
            for item in os.listdir(tnm_output_dir):
                if item in ['.', '..', 'README.md']:
                    continue
                    
                item_path = os.path.join(tnm_output_dir, item)
                info = get_path_info(item_path)
                
                if info and info['modified_time'] < output_cutoff:
                    cleanup_plan['output_files_to_clean'].append(info)
                    cleanup_plan['total_size_to_free_mb'] += info['size_mb']
        
        # Find old repository directories
        repo_cutoff = datetime.now() - timedelta(days=repository_retention_days)
        if os.path.exists(tnm_repos_dir):
            for item in os.listdir(tnm_repos_dir):
                if item in ['.', '..', 'README.md']:
                    continue
                    
                item_path = os.path.join(tnm_repos_dir, item)
                info = get_path_info(item_path)
                
                if info and info['modified_time'] < repo_cutoff:
                    cleanup_plan['repository_dirs_to_clean'].append(info)
                    cleanup_plan['total_size_to_free_mb'] += info['size_mb']
        
        # If total size exceeds limit, add more files to cleanup (oldest first)
        if cleanup_plan['current_total_size_gb'] > max_total_size_gb:
            # Collect all files with their info
            all_files = []
            
            # Add remaining output files
            if os.path.exists(tnm_output_dir):
                for item in os.listdir(tnm_output_dir):
                    if item in ['.', '..', 'README.md']:
                        continue
                    item_path = os.path.join(tnm_output_dir, item)
                    info = get_path_info(item_path)
                    if info and info not in cleanup_plan['output_files_to_clean']:
                        all_files.append(('output', info))
            
            # Add remaining repository directories
            if os.path.exists(tnm_repos_dir):
                for item in os.listdir(tnm_repos_dir):
                    if item in ['.', '..', 'README.md']:
                        continue
                    item_path = os.path.join(tnm_repos_dir, item)
                    info = get_path_info(item_path)
                    if info and info not in cleanup_plan['repository_dirs_to_clean']:
                        all_files.append(('repository', info))
            
            # Sort by age (oldest first)
            all_files.sort(key=lambda x: x[1]['modified_time'])
            
            # Add files until we're under the size limit
            target_size_gb = max_total_size_gb * 0.8  # Clean to 80% of limit
            current_size_gb = cleanup_plan['current_total_size_gb']
            
            for file_type, info in all_files:
                if current_size_gb <= target_size_gb:
                    break
                
                if file_type == 'output':
                    cleanup_plan['output_files_to_clean'].append(info)
                else:
                    cleanup_plan['repository_dirs_to_clean'].append(info)
                
                cleanup_plan['total_size_to_free_mb'] += info['size_mb']
                current_size_gb -= info['size_mb'] / 1024
        
        # Round the size
        cleanup_plan['total_size_to_free_mb'] = round(cleanup_plan['total_size_to_free_mb'], 2)
        
        # Execute cleanup if not dry run
        if not dry_run and (cleanup_plan['output_files_to_clean'] or cleanup_plan['repository_dirs_to_clean']):
            files_removed = 0
            directories_removed = 0
            
            # Clean output files
            for info in cleanup_plan['output_files_to_clean']:
                try:
                    if os.path.isdir(info['path']):
                        shutil.rmtree(info['path'])
                        directories_removed += 1
                    else:
                        os.remove(info['path'])
                        files_removed += 1
                except Exception as e:
                    logger.warning(f"Failed to remove {info['path']}: {e}")
            
            # Clean repository directories
            for info in cleanup_plan['repository_dirs_to_clean']:
                try:
                    if os.path.isdir(info['path']):
                        shutil.rmtree(info['path'])
                        directories_removed += 1
                    else:
                        os.remove(info['path'])
                        files_removed += 1
                except Exception as e:
                    logger.warning(f"Failed to remove {info['path']}: {e}")
            
            cleanup_plan['files_removed'] = files_removed
            cleanup_plan['directories_removed'] = directories_removed
        
        logger.info(f"Auto cleanup {'planned' if dry_run else 'completed'}", extra={
            'user_id': request.user.id,
            'dry_run': dry_run,
            'plan': cleanup_plan
        })
        
        message = f"Auto cleanup {'plan' if dry_run else 'completed'}. Would {'free' if dry_run else 'Freed'} {cleanup_plan['total_size_to_free_mb']} MB"
        
        return ApiResponse.success(
            data=cleanup_plan,
            message=message
        )
        
    except Exception as e:
        logger.error(f"Auto cleanup failed: {e}", extra={
            'user_id': request.user.id
        }, exc_info=True)
        return ApiResponse.internal_error(
            error_message="Failed to run auto cleanup",
            error_code="AUTO_CLEANUP_ERROR"
        )
