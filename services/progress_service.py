"""
Progress tracking service for the Mentora application
Provides analytics and insights on goal progress
"""
import logging
from datetime import datetime, timedelta
from app import db
from models import Goal, Task, Category
from sqlalchemy import func

logger = logging.getLogger(__name__)

def get_overall_progress():
    """
    Get overall progress stats across all goals
    
    Returns:
        Dictionary with progress statistics
    """
    # Get total counts
    total_goals = Goal.query.count()
    completed_goals = Goal.query.filter_by(completed=True).count()
    
    total_tasks = Task.query.count()
    completed_tasks = Task.query.filter_by(completed=True).count()
    
    # Calculate percentages
    goal_completion_rate = 0
    if total_goals > 0:
        goal_completion_rate = int((completed_goals / total_goals) * 100)
    
    task_completion_rate = 0
    if total_tasks > 0:
        task_completion_rate = int((completed_tasks / total_tasks) * 100)
    
    # Get overdue tasks
    now = datetime.utcnow()
    overdue_count = Task.query.filter(
        Task.deadline < now, 
        Task.completed == False
    ).count()
    
    return {
        'total_goals': total_goals,
        'completed_goals': completed_goals,
        'goal_completion_rate': goal_completion_rate,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'task_completion_rate': task_completion_rate,
        'overdue_tasks': overdue_count,
        'timestamp': now.isoformat()
    }

def get_progress_by_category():
    """
    Get progress statistics broken down by category
    
    Returns:
        List of dictionaries with category progress data
    """
    results = []
    categories = Category.query.all()
    
    for category in categories:
        # Get goals for this category
        goals = Goal.query.filter_by(category_id=category.id).all()
        total_goals = len(goals)
        completed_goals = sum(1 for goal in goals if goal.completed)
        
        # Get tasks for all goals in this category
        total_tasks = 0
        completed_tasks = 0
        
        for goal in goals:
            tasks = Task.query.filter_by(goal_id=goal.id).all()
            total_tasks += len(tasks)
            completed_tasks += sum(1 for task in tasks if task.completed)
        
        # Calculate completion rates
        goal_completion_rate = 0
        if total_goals > 0:
            goal_completion_rate = int((completed_goals / total_goals) * 100)
        
        task_completion_rate = 0
        if total_tasks > 0:
            task_completion_rate = int((completed_tasks / total_tasks) * 100)
        
        # Add to results
        results.append({
            'category_id': category.id,
            'category_name': category.name,
            'category_color': category.color,
            'total_goals': total_goals,
            'completed_goals': completed_goals,
            'goal_completion_rate': goal_completion_rate,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'task_completion_rate': task_completion_rate
        })
    
    return results

def get_recent_activity(days=7):
    """
    Get recent activity stats
    
    Args:
        days: Number of days to look back
    
    Returns:
        Dictionary with recent activity data
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get recently completed tasks
    completed_tasks = Task.query.filter(
        Task.completion_date >= start_date
    ).order_by(Task.completion_date.desc()).all()
    
    # Get recently created goals
    new_goals = Goal.query.filter(
        Goal.created_at >= start_date
    ).order_by(Goal.created_at.desc()).all()
    
    # Get recently completed goals
    completed_goals = Goal.query.filter(
        Goal.completed == True,
        Goal.updated_at >= start_date
    ).order_by(Goal.updated_at.desc()).all()
    
    return {
        'period_days': days,
        'completed_tasks': [task.to_dict() for task in completed_tasks],
        'completed_tasks_count': len(completed_tasks),
        'new_goals': [goal.to_dict() for goal in new_goals],
        'new_goals_count': len(new_goals),
        'completed_goals': [goal.to_dict() for goal in completed_goals],
        'completed_goals_count': len(completed_goals)
    }

def get_daily_completion_stats(days=30):
    """
    Get daily task completion statistics
    
    Args:
        days: Number of days to look back
    
    Returns:
        List of daily completion counts
    """
    result = []
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    for day_offset in range(days, -1, -1):
        day = today - timedelta(days=day_offset)
        next_day = day + timedelta(days=1)
        
        # Count tasks completed on this day
        completed_count = Task.query.filter(
            Task.completion_date >= day,
            Task.completion_date < next_day
        ).count()
        
        # Count tasks created on this day
        created_count = Task.query.filter(
            Task.created_at >= day,
            Task.created_at < next_day
        ).count()
        
        result.append({
            'date': day.strftime('%Y-%m-%d'),
            'completed_tasks': completed_count,
            'created_tasks': created_count
        })
    
    return result

def get_user_productivity_score():
    """
    Calculate a productivity score based on task completion rate, timeliness, etc.
    
    Returns:
        Dictionary with productivity score and factors
    """
    # Base score out of 100
    base_score = 70
    
    # Factor 1: Task completion rate (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    recent_tasks = Task.query.filter(
        Task.created_at >= thirty_days_ago
    ).count()
    
    recent_completed = Task.query.filter(
        Task.created_at >= thirty_days_ago,
        Task.completed == True
    ).count()
    
    completion_score = 0
    if recent_tasks > 0:
        completion_rate = recent_completed / recent_tasks
        completion_score = int(completion_rate * 15)  # Max 15 points
    
    # Factor 2: Timeliness - tasks completed before deadline
    on_time_tasks = 0
    late_tasks = 0
    
    for task in Task.query.filter(
        Task.completed == True,
        Task.completion_date >= thirty_days_ago,
        Task.deadline.isnot(None)
    ).all():
        if task.completion_date <= task.deadline:
            on_time_tasks += 1
        else:
            late_tasks += 1
    
    timeliness_score = 0
    total_deadline_tasks = on_time_tasks + late_tasks
    if total_deadline_tasks > 0:
        on_time_rate = on_time_tasks / total_deadline_tasks
        timeliness_score = int(on_time_rate * 25)  # Max 25 points
    
    # Factor 3: High priority task completion
    high_priority_completed = Task.query.filter(
        Task.completed == True,
        Task.completion_date >= thirty_days_ago,
        Task.priority == 1
    ).count()
    
    high_priority_score = min(high_priority_completed, 10)  # Max 10 points
    
    # Calculate final score
    final_score = base_score + completion_score + timeliness_score + high_priority_score
    final_score = min(final_score, 100)  # Cap at 100
    
    return {
        'productivity_score': final_score,
        'factors': {
            'completion_rate': f"{completion_score}/15",
            'timeliness': f"{timeliness_score}/25",
            'high_priority_completion': f"{high_priority_score}/10",
            'base_score': base_score
        },
        'recent_tasks': recent_tasks,
        'recent_completed': recent_completed,
        'on_time_tasks': on_time_tasks,
        'late_tasks': late_tasks,
        'high_priority_completed': high_priority_completed
    }
