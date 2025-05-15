"""
Goal service for the Mentora application
Handles business logic for goal management
"""
import logging
from datetime import datetime
from app import db
from models import Goal, Task

logger = logging.getLogger(__name__)

def get_all_goals(category_id=None, completed=None):
    """
    Get all goals with optional filtering
    
    Args:
        category_id: Filter by category ID
        completed: Filter by completion status
    
    Returns:
        List of Goal objects
    """
    query = Goal.query
    
    if category_id is not None:
        query = query.filter_by(category_id=category_id)
    
    if completed is not None:
        query = query.filter_by(completed=completed)
    
    return query.all()

def get_goal_by_id(goal_id):
    """
    Get a goal by ID
    
    Args:
        goal_id: The ID of the goal to retrieve
    
    Returns:
        Goal object or None if not found
    """
    return Goal.query.get(goal_id)

def create_goal(title, category_id, description=None, start_date=None, end_date=None, completed=False):
    """
    Create a new goal
    
    Args:
        title: Goal title
        category_id: Category ID
        description: Goal description
        start_date: Start date (ISO format string or datetime)
        end_date: End date (ISO format string or datetime)
        completed: Whether the goal is completed
    
    Returns:
        Newly created Goal object
    """
    # Convert string dates to datetime objects if necessary
    if isinstance(start_date, str):
        start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    
    if isinstance(end_date, str):
        end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    
    goal = Goal(
        title=title,
        description=description,
        category_id=category_id,
        start_date=start_date or datetime.utcnow(),
        end_date=end_date,
        completed=completed
    )
    
    db.session.add(goal)
    db.session.commit()
    
    logger.info(f"Created new goal: {goal.id} - {goal.title}")
    return goal

def update_goal(goal_id, title=None, description=None, category_id=None, 
                start_date=None, end_date=None, completed=None):
    """
    Update an existing goal
    
    Args:
        goal_id: ID of the goal to update
        title: New title (optional)
        description: New description (optional)
        category_id: New category ID (optional)
        start_date: New start date (optional, ISO format string or datetime)
        end_date: New end date (optional, ISO format string or datetime)
        completed: New completion status (optional)
    
    Returns:
        Updated Goal object, or None if goal not found
    """
    goal = Goal.query.get(goal_id)
    
    if not goal:
        logger.warning(f"Attempted to update non-existent goal with ID: {goal_id}")
        return None
    
    # Update fields if provided
    if title is not None:
        goal.title = title
    
    if description is not None:
        goal.description = description
    
    if category_id is not None:
        goal.category_id = category_id
    
    if start_date is not None:
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        goal.start_date = start_date
    
    if end_date is not None:
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        goal.end_date = end_date
    
    if completed is not None:
        goal.completed = completed
        
        # If marking as completed, check if all tasks are completed
        if completed and goal.tasks.count() > 0:
            incomplete_tasks = goal.tasks.filter_by(completed=False).count()
            if incomplete_tasks > 0:
                logger.info(f"Marking goal {goal_id} as complete with {incomplete_tasks} incomplete tasks")
    
    goal.updated_at = datetime.utcnow()
    
    db.session.add(goal)
    db.session.commit()
    
    logger.info(f"Updated goal: {goal.id}")
    return goal

def delete_goal(goal_id):
    """
    Delete a goal and all associated tasks
    
    Args:
        goal_id: ID of the goal to delete
    
    Returns:
        True if successful, False if goal not found
    """
    goal = Goal.query.get(goal_id)
    
    if not goal:
        logger.warning(f"Attempted to delete non-existent goal with ID: {goal_id}")
        return False
    
    # Goal deletion will cascade to tasks due to relationship setup
    db.session.delete(goal)
    db.session.commit()
    
    logger.info(f"Deleted goal: {goal_id}")
    return True

def get_goal_progress(goal_id):
    """
    Get detailed progress information for a goal
    
    Args:
        goal_id: ID of the goal
    
    Returns:
        Dictionary with progress details, or None if goal not found
    """
    goal = Goal.query.get(goal_id)
    
    if not goal:
        return None
    
    # Get task statistics
    total_tasks = goal.tasks.count()
    completed_tasks = goal.tasks.filter_by(completed=True).count()
    
    # Calculate days left until end date
    days_left = None
    if goal.end_date:
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        days_left = (goal.end_date - today).days
    
    # Calculate progress percentage
    progress_percentage = 0
    if total_tasks > 0:
        progress_percentage = int((completed_tasks / total_tasks) * 100)
    
    # Get high priority incomplete tasks
    high_priority_tasks = goal.tasks.filter_by(completed=False, priority=1).all()
    
    # Get overdue tasks
    now = datetime.utcnow()
    overdue_tasks = [task for task in goal.tasks.filter_by(completed=False).all() 
                     if task.deadline and task.deadline < now]
    
    return {
        'goal_id': goal.id,
        'title': goal.title,
        'progress_percentage': progress_percentage,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'days_left': days_left,
        'start_date': goal.start_date.isoformat() if goal.start_date else None,
        'end_date': goal.end_date.isoformat() if goal.end_date else None,
        'high_priority_tasks': [task.to_dict() for task in high_priority_tasks],
        'overdue_tasks': [task.to_dict() for task in overdue_tasks],
        'is_completed': goal.completed
    }
