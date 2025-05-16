"""
Progress Engine for the Mentora application
Implements automatic task logging, progress metrics, and analytics
"""
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
import os

from app import db
from models import Task, Goal, Category, TimeSlot, Blueprint

logger = logging.getLogger(__name__)

# Ensure the logs directory exists
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)


class TaskStatus(Enum):
    """Enum for task status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    MISSED = "missed"


def log_daily_progress():
    """
    Log daily progress automatically
    Should be called at the end of each day
    """
    today = datetime.utcnow().date()
    log_progress_for_date(today)


def log_progress_for_date(date):
    """
    Log progress for a specific date
    
    Args:
        date: The date to log progress for
    """
    # Convert date to datetime objects for start and end of day
    day_start = datetime.combine(date, datetime.min.time())
    day_end = datetime.combine(date, datetime.max.time())
    
    # Get the blueprint for this day
    day_of_week = day_start.strftime('%A')  # Monday, Tuesday, etc.
    
    # Get blueprint for today
    blueprint = None
    day_blueprint = Blueprint.query.filter_by(
        day_of_week=day_of_week,
        is_active=True
    ).first()
    
    if day_blueprint:
        blueprint = day_blueprint
    else:
        # Fallback to default blueprint
        blueprint = Blueprint.query.filter_by(
            day_of_week=None,
            is_active=True
        ).first()
    
    if not blueprint:
        logger.warning(f"No blueprint found for {day_of_week}. Skipping progress logging.")
        return
    
    # Get time slots for this blueprint
    time_slots = TimeSlot.query.filter_by(blueprint_id=blueprint.id).all()
    
    # If no time slots, nothing to log
    if not time_slots:
        logger.warning(f"No time slots found for blueprint {blueprint.id}. Skipping progress logging.")
        return
    
    # Get tasks that were due on this day
    tasks_due = Task.query.filter(
        Task.deadline.between(day_start, day_end)
    ).all()
    
    # Get tasks that were completed on this day
    tasks_completed = Task.query.filter(
        Task.completion_date.between(day_start, day_end)
    ).all()
    
    # Initialize task status map for all time slots
    task_statuses = []
    
    # Process each time slot
    for slot in time_slots:
        # Try to find a matching task
        matching_task = None
        
        # If slot has an associated goal, look for tasks from that goal
        if slot.goal_id:
            for task in tasks_due:
                if task.goal_id == slot.goal_id:
                    matching_task = task
                    break
        
        # If no matching task found by goal, try to find by category
        if not matching_task:
            category = Category.query.get(slot.category_id)
            
            for task in tasks_due:
                task_goal = Goal.query.get(task.goal_id)
                if task_goal and task_goal.category_id == slot.category_id:
                    matching_task = task
                    break
        
        # Determine the status of this time slot
        status = TaskStatus.NOT_STARTED.value
        
        if matching_task:
            if matching_task.completed:
                status = TaskStatus.COMPLETED.value
            else:
                # If the end time of this slot is in the past, it's missed
                slot_end_time = datetime.combine(date, slot.end_time)
                if datetime.utcnow() > slot_end_time:
                    status = TaskStatus.MISSED.value
                # If the start time is past but end time is not, it's in progress
                elif datetime.utcnow() > datetime.combine(date, slot.start_time):
                    status = TaskStatus.IN_PROGRESS.value
        else:
            # No matching task, but we still need to track the time slot
            slot_end_time = datetime.combine(date, slot.end_time)
            if datetime.utcnow() > slot_end_time:
                status = TaskStatus.MISSED.value
            elif datetime.utcnow() > datetime.combine(date, slot.start_time):
                status = TaskStatus.IN_PROGRESS.value
        
        # Get category
        category = Category.query.get(slot.category_id)
        category_name = category.name if category else "Uncategorized"
        
        # Get goal if associated
        goal = None
        if slot.goal_id:
            goal = Goal.query.get(slot.goal_id)
        
        # Create a log entry
        task_entry = {
            "name": slot.title,
            "category": category_name,
            "status": status,
            "start": slot.start_time.strftime('%H:%M'),
            "end": slot.end_time.strftime('%H:%M'),
            "goal_id": slot.goal_id,
            "goal_title": goal.title if goal else None
        }
        
        task_statuses.append(task_entry)
    
    # Create the daily log
    log_data = {
        "date": date.strftime('%Y-%m-%d'),
        "tasks": task_statuses
    }
    
    # Save to JSON file
    log_file = os.path.join(LOGS_DIR, f"progress_{date.strftime('%Y-%m-%d')}.json")
    with open(log_file, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    logger.info(f"Progress logged for {date.strftime('%Y-%m-%d')} with {len(task_statuses)} tasks")
    
    return log_data


def get_daily_metrics(date=None):
    """
    Get metrics for a specific day
    
    Args:
        date: The date to get metrics for, or today if None
    
    Returns:
        Dictionary with metrics
    """
    if date is None:
        date = datetime.utcnow().date()
    
    # Try to load from log file first
    log_file = os.path.join(LOGS_DIR, f"progress_{date.strftime('%Y-%m-%d')}.json")
    
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            log_data = json.load(f)
    else:
        # Generate log if it doesn't exist
        log_data = log_progress_for_date(date)
        
        if not log_data:
            # If we couldn't generate a log, return empty metrics
            return {
                "date": date.strftime('%Y-%m-%d'),
                "total_tasks": 0,
                "completed_tasks": 0,
                "completion_rate": 0,
                "missed_tasks": 0,
                "in_progress_tasks": 0,
                "not_started_tasks": 0,
                "categories": {},
                "top_category": None
            }
    
    # Process metrics
    tasks = log_data["tasks"]
    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks if task["status"] == TaskStatus.COMPLETED.value)
    missed_tasks = sum(1 for task in tasks if task["status"] == TaskStatus.MISSED.value)
    in_progress_tasks = sum(1 for task in tasks if task["status"] == TaskStatus.IN_PROGRESS.value)
    not_started_tasks = sum(1 for task in tasks if task["status"] == TaskStatus.NOT_STARTED.value)
    
    completion_rate = 0
    if total_tasks > 0:
        completion_rate = (completed_tasks / total_tasks) * 100
    
    # Category-specific metrics
    categories = {}
    for task in tasks:
        category = task["category"]
        
        if category not in categories:
            categories[category] = {
                "total": 0,
                "completed": 0,
                "completion_rate": 0
            }
        
        categories[category]["total"] += 1
        
        if task["status"] == TaskStatus.COMPLETED.value:
            categories[category]["completed"] += 1
    
    # Calculate completion rate for each category
    for category in categories:
        if categories[category]["total"] > 0:
            categories[category]["completion_rate"] = (
                categories[category]["completed"] / categories[category]["total"]
            ) * 100
    
    # Determine top category
    top_category = None
    top_completion_rate = -1
    
    for category, stats in categories.items():
        if stats["completion_rate"] > top_completion_rate and stats["total"] > 0:
            top_completion_rate = stats["completion_rate"]
            top_category = category
    
    return {
        "date": date.strftime('%Y-%m-%d'),
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "completion_rate": completion_rate,
        "missed_tasks": missed_tasks,
        "in_progress_tasks": in_progress_tasks,
        "not_started_tasks": not_started_tasks,
        "categories": categories,
        "top_category": top_category
    }


def get_weekly_metrics(end_date=None, days=7):
    """
    Get metrics for a week
    
    Args:
        end_date: The end date of the week, or today if None
        days: Number of days to include
    
    Returns:
        Dictionary with weekly metrics
    """
    if end_date is None:
        end_date = datetime.utcnow().date()
    
    # Get metrics for each day
    daily_metrics = []
    
    for i in range(days - 1, -1, -1):
        date = end_date - timedelta(days=i)
        metrics = get_daily_metrics(date)
        daily_metrics.append(metrics)
    
    # Calculate weekly totals
    total_tasks = sum(day["total_tasks"] for day in daily_metrics)
    completed_tasks = sum(day["completed_tasks"] for day in daily_metrics)
    missed_tasks = sum(day["missed_tasks"] for day in daily_metrics)
    
    completion_rate = 0
    if total_tasks > 0:
        completion_rate = (completed_tasks / total_tasks) * 100
    
    # Calculate streak (consecutive days with at least one completed task)
    streak = 0
    
    for day in reversed(daily_metrics):
        if day["completed_tasks"] > 0:
            streak += 1
        else:
            break
    
    # Category-specific metrics
    categories = {}
    
    for day in daily_metrics:
        for category, stats in day["categories"].items():
            if category not in categories:
                categories[category] = {
                    "total": 0,
                    "completed": 0,
                    "completion_rate": 0
                }
            
            categories[category]["total"] += stats["total"]
            categories[category]["completed"] += stats["completed"]
    
    # Calculate completion rate for each category
    for category in categories:
        if categories[category]["total"] > 0:
            categories[category]["completion_rate"] = (
                categories[category]["completed"] / categories[category]["total"]
            ) * 100
    
    # Determine best and worst categories
    best_category = None
    best_completion_rate = -1
    worst_category = None
    worst_completion_rate = 101
    
    for category, stats in categories.items():
        if stats["completion_rate"] > best_completion_rate and stats["total"] >= 3:
            best_completion_rate = stats["completion_rate"]
            best_category = category
        
        if stats["completion_rate"] < worst_completion_rate and stats["total"] >= 3:
            worst_completion_rate = stats["completion_rate"]
            worst_category = category
    
    # Calculate consistency score
    consistency_score = completion_rate
    
    # Generate insights
    insights = []
    
    if best_category:
        insights.append(f"Your {best_category} tasks had a {best_completion_rate:.1f}% completion rate this week — excellent!")
    
    if worst_category and worst_completion_rate < 70:
        insights.append(f"{worst_category} tasks had only {worst_completion_rate:.1f}% completion. Let's plan a better schedule or adjust timing?")
    
    if streak >= 3:
        insights.append(f"You're on a {streak}-day streak! Keep it up!")
    
    if completion_rate >= 80:
        insights.append(f"Great job this week with {completion_rate:.1f}% overall completion!")
    elif completion_rate >= 50:
        insights.append(f"Solid effort with {completion_rate:.1f}% completion. Let's push for 80% next week!")
    else:
        insights.append(f"This week was challenging with {completion_rate:.1f}% completion. Let's simplify your schedule for better results.")
    
    return {
        "start_date": (end_date - timedelta(days=days-1)).strftime('%Y-%m-%d'),
        "end_date": end_date.strftime('%Y-%m-%d'),
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "missed_tasks": missed_tasks,
        "completion_rate": completion_rate,
        "streak": streak,
        "consistency_score": consistency_score,
        "categories": categories,
        "best_category": best_category,
        "worst_category": worst_category,
        "daily_metrics": daily_metrics,
        "insights": insights
    }


def get_nudge_for_current_status():
    """
    Generate a smart nudge based on current status
    
    Returns:
        Dictionary with nudge data or None if no nudge needed
    """
    today = datetime.utcnow().date()
    now = datetime.utcnow()
    
    # Get today's blueprint and time slots
    day_of_week = now.strftime('%A')
    
    # Get blueprint for today
    blueprint = None
    day_blueprint = Blueprint.query.filter_by(
        day_of_week=day_of_week,
        is_active=True
    ).first()
    
    if day_blueprint:
        blueprint = day_blueprint
    else:
        # Fallback to default blueprint
        blueprint = Blueprint.query.filter_by(
            day_of_week=None,
            is_active=True
        ).first()
    
    if not blueprint:
        return None
    
    # Get time slots for this blueprint
    time_slots = TimeSlot.query.filter_by(blueprint_id=blueprint.id).all()
    
    if not time_slots:
        return None
    
    # Find current and next time slots
    current_slot = None
    next_slot = None
    
    # Sort time slots by start time
    sorted_slots = sorted(time_slots, key=lambda x: x.start_time)
    
    current_time = now.time()
    
    for i, slot in enumerate(sorted_slots):
        # Check if current time is within this slot
        if slot.start_time <= current_time < slot.end_time:
            current_slot = slot
            
            # Next slot is the next one in the list
            if i < len(sorted_slots) - 1:
                next_slot = sorted_slots[i + 1]
            
            break
        
        # If we haven't found the current slot and this slot starts in the future
        if current_slot is None and current_time < slot.start_time:
            next_slot = slot
            break
    
    # Generate nudge based on current context
    nudge = None
    
    # Get daily metrics
    metrics = get_daily_metrics()
    
    # Case 1: Current slot is ending soon (within 5 minutes)
    if current_slot:
        end_time_dt = datetime.combine(today, current_slot.end_time)
        minutes_left = (end_time_dt - now).total_seconds() / 60
        
        if 0 < minutes_left <= 5:
            category = Category.query.get(current_slot.category_id)
            category_name = category.name if category else "this task"
            
            nudge = {
                "type": "end_task",
                "message": f"Wrapping up {current_slot.title} in {int(minutes_left)} minutes. " +
                          (f"Get ready for {next_slot.title} next!" if next_slot else "You'll have a break after this!"),
                "task": current_slot.title,
                "category": category_name,
                "emoji": "⏰"
            }
    
    # Case 2: Next slot is starting soon (within 5 minutes)
    elif next_slot:
        start_time_dt = datetime.combine(today, next_slot.start_time)
        minutes_until = (start_time_dt - now).total_seconds() / 60
        
        if 0 < minutes_until <= 5:
            category = Category.query.get(next_slot.category_id)
            category_name = category.name if category else "this task"
            
            nudge = {
                "type": "start_task",
                "message": f"{next_slot.title} starts in {int(minutes_until)} minutes. " +
                          f"Get ready for focused {category_name} time!",
                "task": next_slot.title,
                "category": category_name,
                "emoji": "🚀"
            }
    
    # Case 3: Multiple completed tasks today (congratulate)
    elif metrics["completed_tasks"] >= 3 and metrics["completion_rate"] >= 75:
        nudge = {
            "type": "progress",
            "message": f"You've completed {metrics['completed_tasks']} tasks today - that's {metrics['completion_rate']:.1f}% of your schedule! Excellent momentum!",
            "completion_rate": metrics["completion_rate"],
            "emoji": "🔥"
        }
    
    # Case 4: Multiple missed tasks (gentle reminder)
    elif metrics["missed_tasks"] >= 2:
        nudge = {
            "type": "missed",
            "message": f"You've missed {metrics['missed_tasks']} tasks today. Would you like to reschedule or adjust your blueprint?",
            "missed_count": metrics["missed_tasks"],
            "emoji": "🤔"
        }
    
    return nudge


def generate_weekly_report():
    """
    Generate a complete weekly report
    
    Returns:
        String with formatted weekly report
    """
    # Get weekly metrics
    metrics = get_weekly_metrics()
    
    # Format the report
    report = f"""📅 Week Summary: {metrics['start_date']} – {metrics['end_date']}

✅ Tasks Completed: {metrics['completed_tasks']} / {metrics['total_tasks']} ({metrics['completion_rate']:.1f}%)
🔁 Missed Tasks: {metrics['missed_tasks']}"""
    
    if metrics['best_category']:
        best_rate = metrics['categories'][metrics['best_category']]['completion_rate']
        report += f"\n🧠 Best Focused Area: {metrics['best_category']} ({best_rate:.1f}% completion)"
    
    if metrics['worst_category']:
        worst_rate = metrics['categories'][metrics['worst_category']]['completion_rate']
        report += f"\n⚠️ Attention Needed: {metrics['worst_category']} ({worst_rate:.1f}% completion)"
    
    # Add insights
    report += "\n\n"
    
    # Pick one insight
    if metrics['insights']:
        report += f"🌟 {metrics['insights'][0]}"
    
    # Add a motivational quote
    quotes = [
        "'Success is the sum of small efforts, repeated daily.' — James Clear",
        "'The only way to do great work is to love what you do.' — Steve Jobs",
        "'It's not about having time, it's about making time.' — Unknown",
        "'Progress is impossible without change.' — George Bernard Shaw",
        "'The secret to getting ahead is getting started.' — Mark Twain"
    ]
    
    import random
    report += f"\n\n{random.choice(quotes)}"
    
    return report