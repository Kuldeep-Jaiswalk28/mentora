"""
Reminder scheduler for the Mentora application
Schedules and triggers reminders for tasks
"""
import logging
from datetime import datetime, timedelta
from models import Reminder, Task

logger = logging.getLogger(__name__)

def initialize_reminders(scheduler):
    """
    Initialize the reminder system with the APScheduler
    Sets up jobs to check for reminders and handle recurring tasks
    """
    # Add job to check reminders every minute
    scheduler.add_job(
        check_reminders,
        'interval',
        minutes=1,
        id='check_reminders',
        replace_existing=True
    )
    
    # Add job to handle recurring tasks daily
    scheduler.add_job(
        handle_recurring_tasks,
        'cron',
        hour=0,
        minute=0,
        id='handle_recurring_tasks',
        replace_existing=True
    )
    
    logger.info("Reminder scheduler initialized")

def check_reminders():
    """
    Check for pending reminders and trigger them
    This function is called by the scheduler every minute
    """
    from app import db, app
    
    # Use application context to avoid "working outside of application context" error
    with app.app_context():
        now = datetime.utcnow()
        five_minutes_ago = now - timedelta(minutes=5)
        
        # Find pending reminders that should be triggered
        pending_reminders = Reminder.query.filter(
            Reminder.reminder_time <= now,
            Reminder.reminder_time >= five_minutes_ago,
            Reminder.triggered == False
        ).all()
        
        for reminder in pending_reminders:
            # Handle the reminder notification
            # In a desktop app, this would trigger a system notification
            logger.info(f"REMINDER: {reminder.message} for task '{reminder.task.title}'")
            
            # Mark reminder as triggered
            reminder.triggered = True
            db.session.add(reminder)
        
        if pending_reminders:
            db.session.commit()
            logger.info(f"Triggered {len(pending_reminders)} reminders")

def handle_recurring_tasks():
    """
    Create new task instances for recurring tasks
    This function is called by the scheduler daily at midnight
    """
    from app import db, app
    
    # Use application context to avoid "working outside of application context" error
    with app.app_context():
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Find completed tasks with recurrence settings
        completed_recurrings = Task.query.filter(
            Task.completed == True,
            Task.recurrence_type.isnot(None),
            Task.recurrence_value.isnot(None)
        ).all()
        
        new_tasks_count = 0
        
        for task in completed_recurrings:
            if should_create_recurrence(task, today):
                # Create a new task instance
                new_task = Task(
                    title=task.title,
                    description=task.description,
                    goal_id=task.goal_id,
                    priority=task.priority,
                    recurrence_type=task.recurrence_type,
                    recurrence_value=task.recurrence_value,
                    parent_task_id=task.id
                )
                
                # Set new deadline based on recurrence type
                if task.deadline:
                    new_task.deadline = calculate_next_deadline(task)
                
                db.session.add(new_task)
                new_tasks_count += 1
        
        if new_tasks_count > 0:
            db.session.commit()
            logger.info(f"Created {new_tasks_count} new recurring tasks")

def should_create_recurrence(task, today):
    """
    Determine if a recurring task should create a new instance
    """
    if not task.completion_date:
        return False
    
    # Calculate next occurrence based on completion date
    next_date = calculate_next_date(task.completion_date, task.recurrence_type, task.recurrence_value)
    
    # If next date is today or earlier, create a new instance
    return next_date <= today

def calculate_next_date(base_date, recurrence_type, recurrence_value):
    """Calculate the next occurrence date based on recurrence settings"""
    if recurrence_type == 'daily':
        return base_date + timedelta(days=recurrence_value)
    elif recurrence_type == 'weekly':
        return base_date + timedelta(weeks=recurrence_value)
    elif recurrence_type == 'monthly':
        # Simple approximation: add 30 days per month
        return base_date + timedelta(days=30 * recurrence_value)
    elif recurrence_type == 'yearly':
        # Simple approximation: add 365 days per year
        return base_date + timedelta(days=365 * recurrence_value)
    else:
        # Default to daily
        return base_date + timedelta(days=recurrence_value)

def calculate_next_deadline(task):
    """Calculate the next deadline based on the previous one"""
    return calculate_next_date(task.deadline, task.recurrence_type, task.recurrence_value)

def create_reminder(task_id, reminder_time, message=None):
    """
    Create a new reminder for a task
    """
    from app import db
    
    # Generate default message if none provided
    if not message:
        task = Task.query.get(task_id)
        if not task:
            logger.error(f"Cannot create reminder: Task {task_id} not found")
            return None
        
        message = f"Reminder for task: {task.title}"
    
    # Create and save the reminder
    reminder = Reminder(
        task_id=task_id,
        reminder_time=reminder_time,
        message=message
    )
    
    db.session.add(reminder)
    db.session.commit()
    logger.info(f"Created reminder for task {task_id} at {reminder_time}")
    
    return reminder

def create_default_reminders(task):
    """
    Create default reminders for a task based on its deadline
    """
    if not task.deadline:
        return
    
    # Create a reminder for 1 day before deadline
    one_day_before = task.deadline - timedelta(days=1)
    if one_day_before > datetime.utcnow():
        create_reminder(
            task.id, 
            one_day_before, 
            f"Task '{task.title}' is due tomorrow!"
        )
    
    # Create a reminder for 1 hour before deadline
    one_hour_before = task.deadline - timedelta(hours=1)
    if one_hour_before > datetime.utcnow():
        create_reminder(
            task.id, 
            one_hour_before, 
            f"Task '{task.title}' is due in 1 hour!"
        )
