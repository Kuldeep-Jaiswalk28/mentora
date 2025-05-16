"""
Progress Engine for Mentora application
Analyzes user progress patterns and provides intelligent insights
"""
import logging
from datetime import datetime, timedelta

from app import db
from models import Task, Goal, Category, TimeSlot

logger = logging.getLogger(__name__)

# Progress log cache
daily_progress_logs = []

def log_daily_progress():
    """
    Log progress data for today
    This is called automatically at the end of each day
    """
    today = datetime.utcnow().date()
    metrics = get_daily_metrics(today)
    
    # Add to progress logs
    daily_progress_logs.append({
        "date": today.isoformat(),
        "metrics": metrics
    })
    
    logger.info(f"Daily progress logged for {today.isoformat()}")
    return metrics

def get_daily_metrics(date=None):
    """
    Get metrics for a specific day
    
    Args:
        date: The date to get metrics for, defaults to today
    
    Returns:
        Dictionary of metrics
    """
    if date is None:
        date = datetime.utcnow().date()
    
    day_start = datetime.combine(date, datetime.min.time())
    day_end = datetime.combine(date, datetime.max.time())
    
    # Get task metrics
    total_tasks = Task.query.filter(
        Task.deadline.between(day_start, day_end)
    ).count()
    
    completed_tasks = Task.query.filter(
        Task.deadline.between(day_start, day_end),
        Task.completed == True
    ).count()
    
    completed_today = Task.query.filter(
        Task.completion_date.between(day_start, day_end)
    ).count()
    
    # Get goal metrics
    active_goals = Goal.query.filter_by(completed=False).count()
    completed_goals = Goal.query.filter(
        Goal.updated_at.between(day_start, day_end),
        Goal.completed == True
    ).count()
    
    # Calculate time spent (based on time slots)
    time_spent = 0
    time_slots = TimeSlot.query.all()
    for slot in time_slots:
        # Convert time objects to datetime for calculation
        start = datetime.combine(date, slot.start_time)
        end = datetime.combine(date, slot.end_time)
        duration = (end - start).seconds / 3600  # in hours
        time_spent += duration
    
    # Calculate completion rate
    completion_rate = 0
    if total_tasks > 0:
        completion_rate = (completed_tasks / total_tasks) * 100
    
    # Get time spent by category
    time_by_category = {}
    categories = Category.query.all()
    
    for category in categories:
        category_slots = TimeSlot.query.filter_by(category_id=category.id).all()
        category_time = 0
        
        for slot in category_slots:
            start = datetime.combine(date, slot.start_time)
            end = datetime.combine(date, slot.end_time)
            duration = (end - start).seconds / 3600  # in hours
            category_time += duration
        
        time_by_category[category.name] = category_time
    
    # Gather overdue tasks
    overdue_tasks = Task.query.filter(
        Task.deadline < day_start,
        Task.completed == False
    ).count()
    
    # Create metrics dictionary
    metrics = {
        "date": date.isoformat(),
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "completed_today": completed_today,
        "completion_rate": round(completion_rate, 1),
        "active_goals": active_goals,
        "completed_goals": completed_goals,
        "time_spent": round(time_spent, 1),
        "time_by_category": time_by_category,
        "overdue_tasks": overdue_tasks
    }
    
    return metrics

def get_weekly_metrics(end_date=None, days=7):
    """
    Get metrics for a week
    
    Args:
        end_date: The end date of the week, defaults to today
        days: Number of days to include, defaults to 7
    
    Returns:
        Dictionary of weekly metrics
    """
    if end_date is None:
        end_date = datetime.utcnow().date()
    
    start_date = end_date - timedelta(days=days-1)
    
    # Initialize metrics
    weekly_metrics = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily_metrics": [],
        "total_tasks": 0,
        "completed_tasks": 0,
        "completion_rate": 0,
        "completed_goals": 0,
        "total_time_spent": 0,
        "most_productive_day": None,
        "least_productive_day": None,
        "time_by_category": {},
        "streak": get_current_streak()
    }
    
    # Get daily metrics for each day
    current_date = start_date
    most_completed = 0
    least_completed = float('inf')
    
    while current_date <= end_date:
        daily_metrics = get_daily_metrics(current_date)
        weekly_metrics["daily_metrics"].append(daily_metrics)
        
        # Update weekly totals
        weekly_metrics["total_tasks"] += daily_metrics["total_tasks"]
        weekly_metrics["completed_tasks"] += daily_metrics["completed_tasks"]
        weekly_metrics["completed_goals"] += daily_metrics["completed_goals"]
        weekly_metrics["total_time_spent"] += daily_metrics["time_spent"]
        
        # Update time by category
        for category, time in daily_metrics["time_by_category"].items():
            if category in weekly_metrics["time_by_category"]:
                weekly_metrics["time_by_category"][category] += time
            else:
                weekly_metrics["time_by_category"][category] = time
        
        # Check for most/least productive day
        if daily_metrics["completed_tasks"] > most_completed:
            most_completed = daily_metrics["completed_tasks"]
            weekly_metrics["most_productive_day"] = daily_metrics["date"]
        
        if daily_metrics["total_tasks"] > 0 and daily_metrics["completed_tasks"] < least_completed:
            least_completed = daily_metrics["completed_tasks"]
            weekly_metrics["least_productive_day"] = daily_metrics["date"]
        
        current_date += timedelta(days=1)
    
    # Calculate weekly completion rate
    if weekly_metrics["total_tasks"] > 0:
        weekly_metrics["completion_rate"] = round(
            (weekly_metrics["completed_tasks"] / weekly_metrics["total_tasks"]) * 100, 1
        )
    
    # Round time spent
    weekly_metrics["total_time_spent"] = round(weekly_metrics["total_time_spent"], 1)
    
    # Round time by category
    for category in weekly_metrics["time_by_category"]:
        weekly_metrics["time_by_category"][category] = round(
            weekly_metrics["time_by_category"][category], 1
        )
    
    return weekly_metrics

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

def get_nudge_for_current_status():
    """
    Generate a smart nudge based on the user's current progress status
    
    Returns:
        String containing the nudge message
    """
    # Get today's metrics
    today = datetime.utcnow().date()
    today_metrics = get_daily_metrics(today)
    
    # Get yesterday's metrics
    yesterday = today - timedelta(days=1)
    yesterday_metrics = get_daily_metrics(yesterday)
    
    # Check for idle pattern (no tasks completed today)
    if today_metrics["completed_today"] == 0:
        # If we have overdue tasks, nudge about those
        if today_metrics["overdue_tasks"] > 0:
            return (f"You have {today_metrics['overdue_tasks']} overdue task{'s' if today_metrics['overdue_tasks'] > 1 else ''}. "
                    f"Let's tackle at least one of them today!")
        # Otherwise, encourage starting a task
        elif today_metrics["total_tasks"] > 0:
            return "You haven't completed any tasks today. Can you start with a small one to build momentum?"
        else:
            return "No tasks for today. This might be a good time to plan ahead or work on a bigger goal."
    
    # Check for procrastination pattern (many tasks due soon)
    due_soon = Task.query.filter(
        Task.deadline < datetime.utcnow() + timedelta(days=2),
        Task.completed == False
    ).count()
    
    if due_soon > 3:
        return (f"You have {due_soon} tasks due in the next 48 hours. "
                f"Consider prioritizing the most important ones.")
    
    # Check for burnout risk (high activity for several days)
    if today_metrics["completed_today"] > 5 and yesterday_metrics["completed_tasks"] > 5:
        return "You've been extremely productive lately. Remember to take breaks to avoid burnout."
    
    # Check for strong momentum (increasing completion rate)
    if (today_metrics["completion_rate"] > 70 and 
        today_metrics["completion_rate"] > yesterday_metrics["completion_rate"] + 10):
        return "Great momentum today! You're making excellent progress on your tasks."
    
    # Check for streak milestone
    streak = get_current_streak()
    if streak > 0 and streak % 3 == 0:
        return f"You're on a {streak}-day streak! Keep it up to build consistency."
    
    # Default encouragement based on completion rate
    if today_metrics["completion_rate"] < 30:
        return "You still have several tasks remaining today. Which one feels most doable right now?"
    elif today_metrics["completion_rate"] < 70:
        return "You're making good progress today. What's your next priority?"
    else:
        return "You've completed most of your tasks for today. Great job staying on track!"

def generate_weekly_report():
    """
    Generate a comprehensive weekly report
    
    Returns:
        String containing the report
    """
    # Get weekly metrics
    end_date = datetime.utcnow().date()
    weekly_metrics = get_weekly_metrics(end_date)
    
    # Format dates
    start_date = datetime.strptime(weekly_metrics["start_date"], "%Y-%m-%d").strftime("%B %d")
    end_date_str = datetime.strptime(weekly_metrics["end_date"], "%Y-%m-%d").strftime("%B %d, %Y")
    
    # Build the report
    report = f"# Weekly Progress Report: {start_date} - {end_date_str}\n\n"
    
    # Overall stats
    report += "## Overall Progress\n"
    report += f"* Completed {weekly_metrics['completed_tasks']} of {weekly_metrics['total_tasks']} tasks "
    report += f"({weekly_metrics['completion_rate']}% completion rate)\n"
    report += f"* Achieved {weekly_metrics['completed_goals']} goals\n"
    report += f"* Current streak: {weekly_metrics['streak']} days\n"
    report += f"* Total time invested: {weekly_metrics['total_time_spent']} hours\n\n"
    
    # Most productive day
    if weekly_metrics["most_productive_day"]:
        most_productive = datetime.strptime(weekly_metrics["most_productive_day"], "%Y-%m-%d").strftime("%A")
        report += f"## Most Productive Day: {most_productive}\n\n"
    
    # Time distribution
    report += "## Time Distribution by Category\n"
    for category, time in sorted(weekly_metrics["time_by_category"].items(), key=lambda x: x[1], reverse=True):
        if time > 0:
            report += f"* {category}: {time} hours\n"
    report += "\n"
    
    # Areas for improvement
    report += "## Areas for Improvement\n"
    if weekly_metrics["completion_rate"] < 70:
        report += "* Task completion rate is below target (70%)\n"
    
    if weekly_metrics["total_tasks"] == 0:
        report += "* No tasks were scheduled this week\n"
    
    overdue = sum(day["overdue_tasks"] for day in weekly_metrics["daily_metrics"])
    if overdue > 0:
        report += f"* {overdue} tasks are currently overdue\n"
    
    report += "\n"
    
    # Recommendations
    report += "## Recommendations\n"
    
    if weekly_metrics["completion_rate"] < 50:
        report += "* Consider reducing the number of daily tasks to make your goals more achievable\n"
    
    if weekly_metrics["streak"] > 0:
        report += f"* Maintain your {weekly_metrics['streak']}-day streak for consistent progress\n"
    else:
        report += "* Try to complete at least one task every day to build momentum\n"
    
    low_categories = []
    for category, time in weekly_metrics["time_by_category"].items():
        if time < 2:  # Less than 2 hours per week
            low_categories.append(category)
    
    if low_categories:
        categories_str = ", ".join(low_categories)
        report += f"* Allocate more time to underserved categories: {categories_str}\n"
    
    return report