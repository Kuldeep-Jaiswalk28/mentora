"""
Progress service for the Mentora application
Handles tracking and reporting of user progress towards goals
"""
import logging
from datetime import datetime, timedelta

from app import db
from models import Goal, Task, Category

logger = logging.getLogger(__name__)

def get_overall_progress():
    """
    Get overall progress statistics across all goals
    
    Returns:
        Dictionary with progress statistics
    """
    # Get all goals
    goals = Goal.query.all()
    
    # Get all tasks
    tasks = Task.query.all()
    
    # Get today's tasks
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    today_tasks = Task.query.filter(
        (Task.deadline >= today_start) & (Task.deadline <= today_end)
    ).all()
    
    # Calculate completion rate for today
    today_completed = len([t for t in today_tasks if t.completed])
    today_total = len(today_tasks)
    today_completion_rate = (today_completed / today_total) * 100 if today_total > 0 else 0
    
    # Calculate overall completion rate
    completed_tasks = len([t for t in tasks if t.completed])
    total_tasks = len(tasks)
    task_completion_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
    
    # Calculate goal progress
    completed_goals = len([g for g in goals if g.completed])
    total_goals = len(goals)
    goal_completion_rate = (completed_goals / total_goals) * 100 if total_goals > 0 else 0
    
    # Calculate streak (consecutive days with completed tasks)
    streak = calculate_streak()
    
    # Get category breakdown
    categories = Category.query.all()
    category_stats = []
    
    for category in categories:
        category_tasks = Task.query.join(Goal).filter(Goal.category_id == category.id).all()
        completed = len([t for t in category_tasks if t.completed])
        total = len(category_tasks)
        completion_rate = (completed / total) * 100 if total > 0 else 0
        
        category_stats.append({
            'id': category.id,
            'name': category.name,
            'color': category.color,
            'completed_tasks': completed,
            'total_tasks': total,
            'completion_rate': completion_rate
        })
    
    # Get recent progress (last 7 days)
    recent_progress = get_recent_progress(7)
    
    return {
        'today_completed_tasks': today_completed,
        'today_total_tasks': today_total,
        'today_completion_rate': today_completion_rate,
        'completed_tasks': completed_tasks,
        'total_tasks': total_tasks,
        'task_completion_rate': task_completion_rate,
        'completed_goals': completed_goals,
        'total_goals': total_goals,
        'goal_completion_rate': goal_completion_rate,
        'streak': streak,
        'category_stats': category_stats,
        'recent_progress': recent_progress
    }

def get_goal_progress(goal_id):
    """
    Get progress statistics for a specific goal
    
    Args:
        goal_id: ID of the goal
        
    Returns:
        Dictionary with progress statistics or None if goal not found
    """
    goal = Goal.query.get(goal_id)
    
    if not goal:
        return None
    
    # Get all tasks for this goal
    tasks = Task.query.filter_by(goal_id=goal_id).all()
    
    # Calculate completion rate
    completed_tasks = len([t for t in tasks if t.completed])
    total_tasks = len(tasks)
    completion_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
    
    # Get recent progress (last 7 days)
    recent_progress = get_recent_progress(7, goal_id=goal_id)
    
    return {
        'goal_id': goal.id,
        'goal_title': goal.title,
        'completed_tasks': completed_tasks,
        'total_tasks': total_tasks,
        'completion_rate': completion_rate,
        'is_completed': goal.completed,
        'recent_progress': recent_progress
    }

def calculate_streak():
    """
    Calculate the current streak (consecutive days with completed tasks)
    
    Returns:
        Integer representing streak days
    """
    streak = 0
    current_date = datetime.utcnow().date()
    
    # Check backwards from yesterday
    check_date = current_date - timedelta(days=1)
    
    while True:
        day_start = datetime.combine(check_date, datetime.min.time())
        day_end = datetime.combine(check_date, datetime.max.time())
        
        # Get tasks completed on this day
        completed_tasks = Task.query.filter(
            Task.completion_date.between(day_start, day_end)
        ).count()
        
        if completed_tasks > 0:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break
    
    # Add today if there are completed tasks
    today_start = datetime.combine(current_date, datetime.min.time())
    today_end = datetime.combine(current_date, datetime.max.time())
    
    today_completed = Task.query.filter(
        Task.completion_date.between(today_start, today_end)
    ).count()
    
    if today_completed > 0:
        streak += 1
    
    return streak

def get_recent_progress(days, goal_id=None):
    """
    Get task completion stats for recent days
    
    Args:
        days: Number of days to include
        goal_id: Optional goal ID to filter by
        
    Returns:
        List of daily stats
    """
    result = []
    current_date = datetime.utcnow().date()
    
    for i in range(days - 1, -1, -1):
        check_date = current_date - timedelta(days=i)
        day_start = datetime.combine(check_date, datetime.min.time())
        day_end = datetime.combine(check_date, datetime.max.time())
        
        # Query for tasks due on this day
        tasks_query = Task.query
        if goal_id:
            tasks_query = tasks_query.filter_by(goal_id=goal_id)
        
        day_tasks = tasks_query.filter(
            Task.deadline.between(day_start, day_end)
        ).all()
        
        # Calculate completion stats
        completed = len([t for t in day_tasks if t.completed])
        total = len(day_tasks)
        completion_rate = (completed / total) * 100 if total > 0 else 0
        
        result.append({
            'date': check_date.strftime('%Y-%m-%d'),
            'day': check_date.strftime('%a'),
            'completed_tasks': completed,
            'total_tasks': total,
            'completion_rate': completion_rate
        })
    
    return result