"""
Reward System for Mentora application
Implements badges and achievements to gamify the task completion experience
"""
import logging
from datetime import datetime, timedelta

from app import db
from models import Task, Goal, Category

logger = logging.getLogger(__name__)

# Define badge types
BADGES = {
    # Streak badges
    "streak_3": {
        "id": "streak_3",
        "name": "3-Day Streak",
        "description": "Completed at least one task for 3 consecutive days",
        "icon": "🔥",
        "category": "streak"
    },
    "streak_5": {
        "id": "streak_5",
        "name": "5-Day Streak Master",
        "description": "Completed at least one task for 5 consecutive days",
        "icon": "🔥",
        "category": "streak"
    },
    "streak_7": {
        "id": "streak_7",
        "name": "Week Warrior",
        "description": "Completed at least one task every day for a full week",
        "icon": "🔥",
        "category": "streak"
    },
    
    # Completion badges
    "tasks_10": {
        "id": "tasks_10",
        "name": "10 Tasks Completed",
        "description": "Completed 10 tasks",
        "icon": "🎯",
        "category": "completion"
    },
    "tasks_50": {
        "id": "tasks_50",
        "name": "50 Tasks Completed",
        "description": "Completed 50 tasks",
        "icon": "🎯",
        "category": "completion"
    },
    "tasks_100": {
        "id": "tasks_100",
        "name": "100 Tasks Completed",
        "description": "Completed 100 tasks",
        "icon": "🎯",
        "category": "completion"
    },
    
    # Perfect day badges
    "perfect_day": {
        "id": "perfect_day",
        "name": "Perfect Day",
        "description": "Completed all scheduled tasks in a single day",
        "icon": "⭐",
        "category": "perfection"
    },
    "perfect_week": {
        "id": "perfect_week",
        "name": "Perfect Week",
        "description": "Completed all scheduled tasks for a full week",
        "icon": "🌟",
        "category": "perfection"
    },
    
    # Category-specific badges
    "category_master": {
        "id": "category_master",
        "name": "Category Master",
        "description": "Achieved 100% completion rate in a category for a week",
        "icon": "🏆",
        "category": "category"
    },
    
    # Special badges
    "early_bird": {
        "id": "early_bird",
        "name": "Early Bird",
        "description": "Completed a task before 8:00 AM",
        "icon": "🐦",
        "category": "special"
    },
    "night_owl": {
        "id": "night_owl",
        "name": "Night Owl",
        "description": "Completed a task after 10:00 PM",
        "icon": "🦉",
        "category": "special"
    },
    "weekend_warrior": {
        "id": "weekend_warrior",
        "name": "Weekend Warrior",
        "description": "Completed tasks on both Saturday and Sunday",
        "icon": "💪",
        "category": "special"
    }
}

# Cache for user badges
user_badges = []

def check_for_new_badges():
    """
    Check if the user has earned any new badges
    
    Returns:
        List of newly earned badges
    """
    new_badges = []
    
    # Check for streak badges
    streak = get_current_streak()
    
    if streak >= 3:
        badge = BADGES["streak_3"]
        if badge not in user_badges:
            user_badges.append(badge)
            new_badges.append(badge)
    
    if streak >= 5:
        badge = BADGES["streak_5"]
        if badge not in user_badges:
            user_badges.append(badge)
            new_badges.append(badge)
    
    if streak >= 7:
        badge = BADGES["streak_7"]
        if badge not in user_badges:
            user_badges.append(badge)
            new_badges.append(badge)
    
    # Check for completion badges
    total_completed = Task.query.filter_by(completed=True).count()
    
    if total_completed >= 10:
        badge = BADGES["tasks_10"]
        if badge not in user_badges:
            user_badges.append(badge)
            new_badges.append(badge)
    
    if total_completed >= 50:
        badge = BADGES["tasks_50"]
        if badge not in user_badges:
            user_badges.append(badge)
            new_badges.append(badge)
    
    if total_completed >= 100:
        badge = BADGES["tasks_100"]
        if badge not in user_badges:
            user_badges.append(badge)
            new_badges.append(badge)
    
    # Check for perfect day badge
    if has_perfect_day():
        badge = BADGES["perfect_day"]
        if badge not in user_badges:
            user_badges.append(badge)
            new_badges.append(badge)
    
    # Check for perfect week badge
    if has_perfect_week():
        badge = BADGES["perfect_week"]
        if badge not in user_badges:
            user_badges.append(badge)
            new_badges.append(badge)
    
    # Check for category master badge
    if has_category_mastery():
        badge = BADGES["category_master"]
        if badge not in user_badges:
            user_badges.append(badge)
            new_badges.append(badge)
    
    # Check for early bird badge
    if is_early_bird():
        badge = BADGES["early_bird"]
        if badge not in user_badges:
            user_badges.append(badge)
            new_badges.append(badge)
    
    # Check for night owl badge
    if is_night_owl():
        badge = BADGES["night_owl"]
        if badge not in user_badges:
            user_badges.append(badge)
            new_badges.append(badge)
    
    # Check for weekend warrior badge
    if is_weekend_warrior():
        badge = BADGES["weekend_warrior"]
        if badge not in user_badges:
            user_badges.append(badge)
            new_badges.append(badge)
    
    return new_badges

def get_current_streak():
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

def has_perfect_day(date=None):
    """
    Check if all tasks for a day were completed
    
    Args:
        date: The date to check, or today if None
        
    Returns:
        Boolean indicating if the day was perfect
    """
    if date is None:
        date = datetime.utcnow().date()
    
    day_start = datetime.combine(date, datetime.min.time())
    day_end = datetime.combine(date, datetime.max.time())
    
    # Get all tasks due on this day
    total_tasks = Task.query.filter(
        Task.deadline.between(day_start, day_end)
    ).count()
    
    # If no tasks, it's not a perfect day
    if total_tasks == 0:
        return False
    
    # Get completed tasks
    completed_tasks = Task.query.filter(
        Task.deadline.between(day_start, day_end),
        Task.completed == True
    ).count()
    
    return total_tasks > 0 and completed_tasks == total_tasks

def has_perfect_week():
    """
    Check if all tasks for the past week were completed
    
    Returns:
        Boolean indicating if the week was perfect
    """
    # Get the start of the week (past 7 days)
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=6)
    
    # Check each day
    current_date = start_date
    while current_date <= end_date:
        if not has_perfect_day(current_date):
            return False
        current_date += timedelta(days=1)
    
    return True

def has_category_mastery():
    """
    Check if any category has 100% completion rate for the past week
    
    Returns:
        Boolean indicating if there's a mastered category
    """
    # Get all categories
    categories = Category.query.all()
    
    # Get the start of the week (past 7 days)
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=6)
    
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    for category in categories:
        # Get all goals in this category
        goals = Goal.query.filter_by(category_id=category.id).all()
        
        if not goals:
            continue
        
        # Get all tasks for these goals
        total_tasks = 0
        completed_tasks = 0
        
        for goal in goals:
            # Get tasks due during this week
            tasks = Task.query.filter(
                Task.goal_id == goal.id,
                Task.deadline.between(start_datetime, end_datetime)
            ).all()
            
            total_tasks += len(tasks)
            completed_tasks += sum(1 for task in tasks if task.completed)
        
        # Check if there are tasks and all are completed
        if total_tasks >= 5 and completed_tasks == total_tasks:
            return True
    
    return False

def is_early_bird():
    """
    Check if any task was completed before 8:00 AM
    
    Returns:
        Boolean indicating if the user is an early bird
    """
    # Get tasks completed in the past week
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=6)
    
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    # Find any task completed before 8:00 AM
    completed_tasks = Task.query.filter(
        Task.completion_date.between(start_datetime, end_datetime),
        Task.completed == True
    ).all()
    
    for task in completed_tasks:
        if task.completion_date.hour < 8:
            return True
    
    return False

def is_night_owl():
    """
    Check if any task was completed after 10:00 PM
    
    Returns:
        Boolean indicating if the user is a night owl
    """
    # Get tasks completed in the past week
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=6)
    
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    # Find any task completed after 10:00 PM
    completed_tasks = Task.query.filter(
        Task.completion_date.between(start_datetime, end_datetime),
        Task.completed == True
    ).all()
    
    for task in completed_tasks:
        if task.completion_date.hour >= 22:
            return True
    
    return False

def is_weekend_warrior():
    """
    Check if tasks were completed on both Saturday and Sunday
    
    Returns:
        Boolean indicating if the user is a weekend warrior
    """
    # Get the most recent weekend
    today = datetime.utcnow().date()
    days_since_sunday = today.weekday() + 1 if today.weekday() != 6 else 0
    
    sunday = today - timedelta(days=days_since_sunday)
    saturday = sunday - timedelta(days=1)
    
    # Check Saturday
    saturday_start = datetime.combine(saturday, datetime.min.time())
    saturday_end = datetime.combine(saturday, datetime.max.time())
    
    saturday_completed = Task.query.filter(
        Task.completion_date.between(saturday_start, saturday_end),
        Task.completed == True
    ).count()
    
    # Check Sunday
    sunday_start = datetime.combine(sunday, datetime.min.time())
    sunday_end = datetime.combine(sunday, datetime.max.time())
    
    sunday_completed = Task.query.filter(
        Task.completion_date.between(sunday_start, sunday_end),
        Task.completed == True
    ).count()
    
    return saturday_completed > 0 and sunday_completed > 0

def get_all_badges():
    """
    Get all badges including user earned status
    
    Returns:
        Dictionary with badge categories and badges
    """
    # Make sure we have the latest badges
    check_for_new_badges()
    
    # Organize badges by category
    result = {}
    
    for badge_id, badge in BADGES.items():
        category = badge["category"]
        
        if category not in result:
            result[category] = []
        
        # Add earned status
        badge_copy = badge.copy()
        badge_copy["earned"] = "true" if badge in user_badges else "false"
        
        result[category].append(badge_copy)
    
    return result

def get_earned_badges():
    """
    Get badges earned by the user
    
    Returns:
        List of earned badges
    """
    # Make sure we have the latest badges
    check_for_new_badges()
    
    return user_badges.copy()