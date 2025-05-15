"""
Priority Engine for the Mentora application
Implements a rule-based system for task prioritization
"""
import logging
from datetime import datetime, timedelta
from models import Task, Goal

logger = logging.getLogger(__name__)

def calculate_task_priority(task):
    """
    Calculate priority score for a task based on multiple factors:
    - Deadline proximity
    - Goal importance
    - Dependencies
    - Completion status
    - User-defined priority
    
    Returns a priority score (lower is higher priority)
    """
    if task.completed:
        return 1000  # Completed tasks have lowest priority
    
    # Start with user-defined priority as base score
    base_score = task.priority * 100
    
    # Factor 1: Deadline proximity
    deadline_score = _calculate_deadline_score(task)
    
    # Factor 2: Goal importance (based on category)
    goal_score = _calculate_goal_importance(task)
    
    # Factor 3: Dependencies - tasks blocking others get higher priority
    dependency_score = _calculate_dependency_score(task)
    
    # Calculate final score (lower is higher priority)
    final_score = base_score - deadline_score - goal_score - dependency_score
    
    logger.debug(f"Priority calculation for task {task.id}: {final_score}")
    
    return final_score

def _calculate_deadline_score(task):
    """Calculate score based on deadline proximity"""
    if not task.deadline:
        return 0
    
    now = datetime.utcnow()
    days_until_deadline = (task.deadline - now).days
    
    if days_until_deadline < 0:  # Overdue
        return 200  # High urgency
    elif days_until_deadline == 0:  # Due today
        return 150
    elif days_until_deadline <= 2:  # Due in 1-2 days
        return 100
    elif days_until_deadline <= 7:  # Due this week
        return 50
    else:
        return max(0, 30 - days_until_deadline // 7 * 5)  # Gradually decreases

def _calculate_goal_importance(task):
    """Calculate score based on goal category and progress"""
    goal = task.goal
    
    # Category-based importance (could be expanded with user preferences)
    category_map = {
        'Certifications': 40,
        'Career Planning': 35,
        'Freelancing': 30,
        'AI Tools': 25,
        'Study': 20
    }
    
    category_score = category_map.get(goal.category.name, 0)
    
    # Goals closer to completion get higher priority to encourage finishing
    progress_bonus = 0
    if goal.progress >= 75:
        progress_bonus = 30  # Almost complete
    elif goal.progress >= 50:
        progress_bonus = 15  # Half complete
    
    return category_score + progress_bonus

def _calculate_dependency_score(task):
    """Calculate score based on task dependencies"""
    # Tasks that are blocking other tasks get higher priority
    dependency_count = task.subtasks.count()
    return dependency_count * 20  # Each dependent task adds 20 points of priority

def prioritize_tasks(tasks):
    """
    Sort tasks by calculated priority
    Returns a list of tasks sorted by priority (highest first)
    """
    task_priorities = [(task, calculate_task_priority(task)) for task in tasks]
    sorted_tasks = [task for task, _ in sorted(task_priorities, key=lambda x: x[1])]
    return sorted_tasks

def get_daily_priorities(limit=10):
    """
    Get prioritized tasks for today
    Returns top priority tasks for the day
    """
    from app import db
    
    # Get incomplete tasks
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    
    # Tasks due today or overdue
    due_today_or_overdue = db.session.query(Task).filter(
        (Task.deadline < tomorrow) & 
        (Task.completed == False)
    ).all()
    
    # Add other important tasks (might not have deadlines but are high priority)
    high_priority = db.session.query(Task).filter(
        (Task.priority == 1) &
        (Task.completed == False) &
        ((Task.deadline == None) | (Task.deadline >= tomorrow))
    ).all()
    
    # Combine and prioritize
    all_candidate_tasks = due_today_or_overdue + high_priority
    prioritized_tasks = prioritize_tasks(all_candidate_tasks)
    
    return prioritized_tasks[:limit]

def suggest_next_task():
    """
    Suggest the next task the user should work on
    Returns the highest priority task
    """
    priorities = get_daily_priorities(limit=1)
    if priorities:
        return priorities[0]
    return None
