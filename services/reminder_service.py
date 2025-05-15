"""
Reminder service for the Mentora application
Handles business logic for reminder management
"""
import logging
from datetime import datetime, timedelta
from app import db
from models import Reminder, Task

logger = logging.getLogger(__name__)

def get_all_reminders(triggered=None):
    """
    Get all reminders with optional filtering
    
    Args:
        triggered: Filter by triggered status
    
    Returns:
        List of Reminder objects
    """
    query = Reminder.query
    
    if triggered is not None:
        query = query.filter_by(triggered=triggered)
    
    return query.all()

def get_reminder_by_id(reminder_id):
    """
    Get a reminder by ID
    
    Args:
        reminder_id: The ID of the reminder to retrieve
    
    Returns:
        Reminder object or None if not found
    """
    return Reminder.query.get(reminder_id)

def get_reminders_by_task(task_id, triggered=None):
    """
    Get all reminders for a specific task
    
    Args:
        task_id: Task ID to filter by
        triggered: Filter by triggered status
    
    Returns:
        List of Reminder objects
    """
    query = Reminder.query.filter_by(task_id=task_id)
    
    if triggered is not None:
        query = query.filter_by(triggered=triggered)
    
    return query.all()

def create_reminder(task_id, reminder_time, message=None):
    """
    Create a new reminder
    
    Args:
        task_id: Associated task ID
        reminder_time: Time to trigger reminder (ISO format string or datetime)
        message: Reminder message
    
    Returns:
        Newly created Reminder object
    """
    # Ensure task exists
    task = Task.query.get(task_id)
    if not task:
        logger.error(f"Cannot create reminder: Task {task_id} not found")
        return None
    
    # Convert string date to datetime if necessary
    if isinstance(reminder_time, str):
        reminder_time = datetime.fromisoformat(reminder_time.replace('Z', '+00:00'))
    
    # Generate default message if none provided
    if not message:
        message = f"Reminder for task: {task.title}"
    
    # Create reminder
    reminder = Reminder(
        task_id=task_id,
        reminder_time=reminder_time,
        message=message
    )
    
    db.session.add(reminder)
    db.session.commit()
    
    logger.info(f"Created new reminder: {reminder.id} for task {task_id}")
    return reminder

def update_reminder(reminder_id, task_id=None, reminder_time=None, message=None, triggered=None):
    """
    Update an existing reminder
    
    Args:
        reminder_id: ID of the reminder to update
        task_id: New task ID (optional)
        reminder_time: New reminder time (optional, ISO format string or datetime)
        message: New message (optional)
        triggered: New triggered status (optional)
    
    Returns:
        Updated Reminder object, or None if reminder not found
    """
    reminder = Reminder.query.get(reminder_id)
    
    if not reminder:
        logger.warning(f"Attempted to update non-existent reminder with ID: {reminder_id}")
        return None
    
    # Update fields if provided
    if task_id is not None:
        # Ensure task exists
        if Task.query.get(task_id):
            reminder.task_id = task_id
        else:
            logger.warning(f"Cannot update reminder: Task {task_id} not found")
    
    if reminder_time is not None:
        if isinstance(reminder_time, str):
            reminder_time = datetime.fromisoformat(reminder_time.replace('Z', '+00:00'))
        reminder.reminder_time = reminder_time
    
    if message is not None:
        reminder.message = message
    
    if triggered is not None:
        reminder.triggered = triggered
    
    db.session.add(reminder)
    db.session.commit()
    
    logger.info(f"Updated reminder: {reminder.id}")
    return reminder

def delete_reminder(reminder_id):
    """
    Delete a reminder
    
    Args:
        reminder_id: ID of the reminder to delete
    
    Returns:
        True if successful, False if reminder not found
    """
    reminder = Reminder.query.get(reminder_id)
    
    if not reminder:
        logger.warning(f"Attempted to delete non-existent reminder with ID: {reminder_id}")
        return False
    
    db.session.delete(reminder)
    db.session.commit()
    
    logger.info(f"Deleted reminder: {reminder_id}")
    return True

def create_default_reminders_for_task(task_id):
    """
    Create default reminders for a task based on its deadline
    
    Args:
        task_id: ID of the task to create reminders for
    
    Returns:
        List of created Reminder objects, or None if task not found or has no deadline
    """
    task = Task.query.get(task_id)
    
    if not task or not task.deadline:
        logger.warning(f"Cannot create default reminders: Task {task_id} not found or has no deadline")
        return None
    
    created_reminders = []
    
    # Create a reminder for 1 day before deadline
    one_day_before = task.deadline - timedelta(days=1)
    if one_day_before > datetime.utcnow():
        reminder = create_reminder(
            task_id, 
            one_day_before, 
            f"Task '{task.title}' is due tomorrow!"
        )
        created_reminders.append(reminder)
    
    # Create a reminder for 1 hour before deadline
    one_hour_before = task.deadline - timedelta(hours=1)
    if one_hour_before > datetime.utcnow():
        reminder = create_reminder(
            task_id, 
            one_hour_before, 
            f"Task '{task.title}' is due in 1 hour!"
        )
        created_reminders.append(reminder)
    
    logger.info(f"Created {len(created_reminders)} default reminders for task {task_id}")
    return created_reminders
