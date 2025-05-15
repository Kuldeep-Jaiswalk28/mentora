"""
Task service for the Mentora application
Handles business logic for task management
"""
import logging
from datetime import datetime
from app import db
from models import Task, Goal
from utils.priority_engine import get_daily_priorities
from utils.reminder_scheduler import create_default_reminders

logger = logging.getLogger(__name__)

def get_all_tasks(completed=None):
    """
    Get all tasks with optional filtering
    
    Args:
        completed: Filter by completion status
    
    Returns:
        List of Task objects
    """
    query = Task.query
    
    if completed is not None:
        query = query.filter_by(completed=completed)
    
    return query.all()

def get_task_by_id(task_id):
    """
    Get a task by ID
    
    Args:
        task_id: The ID of the task to retrieve
    
    Returns:
        Task object or None if not found
    """
    return Task.query.get(task_id)

def get_tasks_by_goal(goal_id, completed=None):
    """
    Get all tasks for a specific goal
    
    Args:
        goal_id: Goal ID to filter by
        completed: Filter by completion status
    
    Returns:
        List of Task objects
    """
    query = Task.query.filter_by(goal_id=goal_id)
    
    if completed is not None:
        query = query.filter_by(completed=completed)
    
    return query.all()

def create_task(title, goal_id, description=None, deadline=None, priority=2,
                recurrence_type=None, recurrence_value=None, parent_task_id=None):
    """
    Create a new task
    
    Args:
        title: Task title
        goal_id: Associated goal ID
        description: Task description
        deadline: Deadline (ISO format string or datetime)
        priority: Priority level (1=High, 2=Medium, 3=Low)
        recurrence_type: Type of recurrence (daily, weekly, etc.)
        recurrence_value: Value for recurrence
        parent_task_id: ID of parent task if this is a subtask
    
    Returns:
        Newly created Task object
    """
    # Ensure goal exists
    goal = Goal.query.get(goal_id)
    if not goal:
        logger.error(f"Cannot create task: Goal {goal_id} not found")
        return None
    
    # Convert string date to datetime if necessary
    if isinstance(deadline, str):
        deadline = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
    
    # Create task
    task = Task(
        title=title,
        description=description,
        goal_id=goal_id,
        deadline=deadline,
        priority=priority,
        recurrence_type=recurrence_type,
        recurrence_value=recurrence_value,
        parent_task_id=parent_task_id
    )
    
    db.session.add(task)
    db.session.commit()
    
    logger.info(f"Created new task: {task.id} - {task.title}")
    
    # Create default reminders if deadline is set
    if deadline:
        create_default_reminders(task)
    
    return task

def update_task(task_id, title=None, description=None, goal_id=None,
                deadline=None, priority=None, completed=None,
                recurrence_type=None, recurrence_value=None, parent_task_id=None):
    """
    Update an existing task
    
    Args:
        task_id: ID of the task to update
        title: New title (optional)
        description: New description (optional)
        goal_id: New goal ID (optional)
        deadline: New deadline (optional, ISO format string or datetime)
        priority: New priority level (optional)
        completed: New completion status (optional)
        recurrence_type: New recurrence type (optional)
        recurrence_value: New recurrence value (optional)
        parent_task_id: New parent task ID (optional)
    
    Returns:
        Updated Task object, or None if task not found
    """
    task = Task.query.get(task_id)
    
    if not task:
        logger.warning(f"Attempted to update non-existent task with ID: {task_id}")
        return None
    
    # Update fields if provided
    if title is not None:
        task.title = title
    
    if description is not None:
        task.description = description
    
    if goal_id is not None:
        # Ensure goal exists
        if Goal.query.get(goal_id):
            task.goal_id = goal_id
        else:
            logger.warning(f"Cannot update task: Goal {goal_id} not found")
    
    old_deadline = task.deadline
    if deadline is not None:
        if isinstance(deadline, str):
            deadline = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
        task.deadline = deadline
        
        # If deadline changed, update reminders
        if deadline != old_deadline:
            # Delete existing reminders
            for reminder in task.reminders:
                db.session.delete(reminder)
            
            # Create new reminders
            if deadline:
                create_default_reminders(task)
    
    if priority is not None:
        task.priority = priority
    
    if completed is not None:
        old_completed = task.completed
        task.completed = completed
        
        # If completing the task, set completion date
        if completed and not old_completed:
            task.completion_date = datetime.utcnow()
        elif not completed and old_completed:
            task.completion_date = None
    
    if recurrence_type is not None:
        task.recurrence_type = recurrence_type
    
    if recurrence_value is not None:
        task.recurrence_value = recurrence_value
    
    if parent_task_id is not None:
        # Check if creating circular dependency
        if parent_task_id == task_id:
            logger.warning(f"Cannot set parent_task_id to itself: {task_id}")
        else:
            task.parent_task_id = parent_task_id
    
    task.updated_at = datetime.utcnow()
    
    db.session.add(task)
    db.session.commit()
    
    logger.info(f"Updated task: {task.id}")
    return task

def delete_task(task_id):
    """
    Delete a task and its reminders
    
    Args:
        task_id: ID of the task to delete
    
    Returns:
        True if successful, False if task not found
    """
    task = Task.query.get(task_id)
    
    if not task:
        logger.warning(f"Attempted to delete non-existent task with ID: {task_id}")
        return False
    
    # Task deletion will cascade to reminders due to relationship setup
    db.session.delete(task)
    db.session.commit()
    
    logger.info(f"Deleted task: {task_id}")
    return True

def mark_task_completed(task_id):
    """
    Mark a task as completed
    
    Args:
        task_id: ID of the task to mark as completed
    
    Returns:
        Updated Task object, or None if task not found
    """
    return update_task(task_id, completed=True)

def mark_task_incomplete(task_id):
    """
    Mark a task as incomplete
    
    Args:
        task_id: ID of the task to mark as incomplete
    
    Returns:
        Updated Task object, or None if task not found
    """
    return update_task(task_id, completed=False)

def get_daily_tasks(limit=10):
    """
    Get prioritized tasks for today
    
    Args:
        limit: Maximum number of tasks to return
        
    Returns:
        List of prioritized Task objects
    """
    return get_daily_priorities(limit)
