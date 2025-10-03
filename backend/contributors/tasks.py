import threading
import logging
from django.utils import timezone
from django.db import transaction
from .models import Contributor, ProjectContributor
from .services import TNMDataAnalysisService
from projects.models import Project

logger = logging.getLogger(__name__)


class AsyncTaskStatus:
    """Task status constants"""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'


class AsyncTaskManager:
    """Manager for async tasks using threading"""
    
    _tasks = {}  # In-memory task storage
    
    @classmethod
    def create_task(cls, task_id: str, task_type: str, project_id: str, user_id: str):
        """Create a new task"""
        cls._tasks[task_id] = {
            'id': task_id,
            'type': task_type,
            'project_id': project_id,
            'user_id': user_id,
            'status': AsyncTaskStatus.PENDING,
            'created_at': timezone.now(),
            'started_at': None,
            'completed_at': None,
            'result': None,
            'error': None,
            'progress': 0
        }
        return cls._tasks[task_id]
    
    @classmethod
    def get_task(cls, task_id: str):
        """Get task by ID"""
        return cls._tasks.get(task_id)
    
    @classmethod
    def update_task(cls, task_id: str, **kwargs):
        """Update task status"""
        if task_id in cls._tasks:
            cls._tasks[task_id].update(kwargs)
    
    @classmethod
    def start_task(cls, task_id: str):
        """Mark task as started"""
        cls.update_task(task_id, 
                       status=AsyncTaskStatus.RUNNING, 
                       started_at=timezone.now())
    
    @classmethod
    def complete_task(cls, task_id: str, result=None):
        """Mark task as completed"""
        cls.update_task(task_id, 
                       status=AsyncTaskStatus.COMPLETED, 
                       completed_at=timezone.now(),
                       result=result,
                       progress=100)
    
    @classmethod
    def fail_task(cls, task_id: str, error: str):
        """Mark task as failed"""
        cls.update_task(task_id, 
                       status=AsyncTaskStatus.FAILED, 
                       completed_at=timezone.now(),
                       error=error)


def analyze_tnm_contributors_async(task_id: str, project_id: str, tnm_output_dir: str, branch: str = None):
    """
    Asynchronous TNM contributor analysis task.
    
    Args:
        task_id: Unique task identifier
        project_id: Project UUID
        tnm_output_dir: Path to TNM output directory
        branch: Git branch name
    """
    try:
        # Mark task as started
        AsyncTaskManager.start_task(task_id)
        logger.info(f"Starting async TNM contributor analysis for project {project_id}")
        
        # Get project
        project = Project.objects.get(id=project_id)
        
        # Update progress
        AsyncTaskManager.update_task(task_id, progress=10)
        
        # Analyze TNM data
        analysis_result = TNMDataAnalysisService.analyze_assignment_matrix(
            project, tnm_output_dir, branch
        )
        
        # Update progress
        AsyncTaskManager.update_task(task_id, progress=90)
        
        # Complete task
        AsyncTaskManager.complete_task(task_id, analysis_result)
        
        logger.info(f"Async TNM contributor analysis completed for project {project_id}", extra={
            'task_id': task_id,
            'project_id': project_id,
            'contributors_processed': analysis_result['total_contributors']
        })
        
    except Project.DoesNotExist:
        error_msg = f"Project {project_id} not found"
        logger.error(error_msg, extra={'task_id': task_id})
        AsyncTaskManager.fail_task(task_id, error_msg)
        
    except Exception as e:
        error_msg = f"TNM contributor analysis failed: {str(e)}"
        logger.error(error_msg, extra={'task_id': task_id, 'project_id': project_id}, exc_info=True)
        AsyncTaskManager.fail_task(task_id, error_msg)


def start_tnm_contributor_analysis_async(project_id: str, tnm_output_dir: str, branch: str = None, user_id: str = None):
    """
    Start asynchronous TNM contributor analysis.
    
    Args:
        project_id: Project UUID
        tnm_output_dir: Path to TNM output directory
        branch: Git branch name
        user_id: User who initiated the task
        
    Returns:
        dict: Task information with task_id
    """
    import uuid
    
    # Generate unique task ID
    task_id = str(uuid.uuid4())
    
    # Create task record
    task = AsyncTaskManager.create_task(
        task_id=task_id,
        task_type='tnm_contributor_analysis',
        project_id=project_id,
        user_id=user_id or 'system'
    )
    
    # Start task in background thread
    thread = threading.Thread(
        target=analyze_tnm_contributors_async,
        args=(task_id, project_id, tnm_output_dir, branch),
        daemon=True
    )
    thread.start()
    
    logger.info(f"Started async TNM contributor analysis task {task_id} for project {project_id}")
    
    return {
        'task_id': task_id,
        'status': task['status'],
        'created_at': task['created_at'],
        'message': 'TNM contributor analysis started in background'
    }


def get_task_status(task_id: str):
    """
    Get the status of an async task.
    
    Args:
        task_id: Task identifier
        
    Returns:
        dict: Task status information
    """
    task = AsyncTaskManager.get_task(task_id)
    if not task:
        return None
    
    return {
        'task_id': task['id'],
        'type': task['type'],
        'status': task['status'],
        'progress': task['progress'],
        'created_at': task['created_at'],
        'started_at': task['started_at'],
        'completed_at': task['completed_at'],
        'result': task['result'],
        'error': task['error']
    }
