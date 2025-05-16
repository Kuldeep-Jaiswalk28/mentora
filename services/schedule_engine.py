"""
Schedule Engine for Mentora application
Handles intelligent time-block allocation and task scheduling based on blueprint data
"""
import logging
import json
from datetime import datetime, timedelta, time
from app import db
from models import Category, Goal, Task, Blueprint, TimeSlot

logger = logging.getLogger(__name__)

# Define time block ranges with more granular slots
MORNING_SLOTS = [
    {"start": "06:00", "end": "06:50"},
    {"start": "07:00", "end": "07:50"},
    {"start": "08:00", "end": "08:50"},
    {"start": "09:00", "end": "09:50"},
    {"start": "10:00", "end": "10:50"},
    {"start": "11:00", "end": "11:50"}
]

AFTERNOON_SLOTS = [
    {"start": "12:00", "end": "12:50"},
    {"start": "13:00", "end": "13:50"},
    {"start": "14:00", "end": "14:50"},
    {"start": "15:00", "end": "15:50"},
    {"start": "16:00", "end": "16:50"}
]

EVENING_SLOTS = [
    {"start": "17:00", "end": "17:50"},
    {"start": "18:00", "end": "18:50"},
    {"start": "19:00", "end": "19:50"},
    {"start": "20:00", "end": "20:50"},
    {"start": "21:00", "end": "21:50"}
]

# Desired category balance (in percentage)
CATEGORY_BALANCE = {
    "Class 11": 40,
    "Certifications": 20,
    "Freelancing": 20,
    "AI Tools": 10,
    "Career Planning": 10
}

def generate_weekly_schedule():
    """
    Generate a complete weekly schedule based on tasks in the database
    
    Returns:
        Boolean indicating success
    """
    try:
        # Clear existing blueprints and time slots
        TimeSlot.query.delete()
        Blueprint.query.delete()
        
        # Create blueprints for each day of the week
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_blueprints = {}
        
        for day in days:
            blueprint = Blueprint()
            blueprint.name = f"{day} Schedule"
            blueprint.description = f"Auto-generated schedule for {day}"
            blueprint.day_of_week = day
            blueprint.is_active = True
            db.session.add(blueprint)
            db.session.flush()  # Get ID without committing
            day_blueprints[day] = blueprint
        
        # Get all tasks that are not completed
        active_tasks = Task.query.filter_by(completed=False).all()
        
        # Group tasks by category
        tasks_by_category = {}
        for task in active_tasks:
            # Get category for this task
            goal = Goal.query.get(task.goal_id)
            if not goal:
                continue
                
            category = Category.query.get(goal.category_id)
            if not category:
                continue
                
            if category.name not in tasks_by_category:
                tasks_by_category[category.name] = []
                
            tasks_by_category[category.name].append({
                "id": task.id,
                "title": task.title,
                "priority": task.priority,
                "deadline": task.deadline,
                "goal_id": task.goal_id,
                "category": category.name,
                "category_id": category.id
            })
        
        # Sort tasks by priority (1=High, 2=Medium, 3=Low)
        for category, tasks in tasks_by_category.items():
            tasks.sort(key=lambda x: (x["priority"], x["deadline"] if x["deadline"] else datetime.max))
        
        # Schedule tasks for each day
        schedule = {}
        for day in days:
            schedule[day] = []
            
            # Get eligible tasks for this day
            day_tasks = []
            for category, tasks in tasks_by_category.items():
                for task in tasks:
                    if is_task_eligible_for_day(task, day):
                        day_tasks.append(task)
            
            # Balance tasks according to CATEGORY_BALANCE
            balanced_tasks = balance_day_tasks(day_tasks)
            
            # Allocate time slots
            schedule[day] = allocate_time_slots(balanced_tasks, day_blueprints[day])
        
        # Commit changes to database
        db.session.commit()
        
        logger.info("Successfully generated weekly schedule")
        return True
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error generating weekly schedule: {str(e)}")
        return False

def is_task_eligible_for_day(task, day):
    """
    Check if a task should be scheduled on a particular day
    
    Args:
        task: Dictionary with task information
        day: Day of the week (e.g., "Monday")
        
    Returns:
        Boolean indicating eligibility
    """
    # Check deadline
    if task["deadline"]:
        # If today or tomorrow is the deadline, task is eligible for today
        now = datetime.utcnow()
        today = now.date()
        tomorrow = today + timedelta(days=1)
        
        if task["deadline"].date() <= tomorrow:
            return True
    
    # Check preferred days (based on category pattern)
    day_preferences = {
        "Class 11": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "AI Tools": ["Monday", "Wednesday", "Friday"],
        "Freelancing": ["Tuesday", "Thursday", "Saturday"],
        "Certifications": ["Monday", "Wednesday", "Friday"],
        "Career Planning": ["Saturday", "Sunday"]
    }
    
    # Default to all days if category not found
    all_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    return day in day_preferences.get(task["category"], all_days)

def balance_day_tasks(day_tasks):
    """
    Balance tasks according to category ratios
    
    Args:
        day_tasks: List of tasks eligible for the day
        
    Returns:
        List of balanced tasks
    """
    # Group by category
    by_category = {}
    for task in day_tasks:
        if task["category"] not in by_category:
            by_category[task["category"]] = []
        by_category[task["category"]].append(task)
    
    # Calculate max tasks to include per category (based on CATEGORY_BALANCE)
    total_tasks = min(len(day_tasks), 8)  # Cap at 8 tasks per day
    category_limits = {}
    
    for category, percentage in CATEGORY_BALANCE.items():
        category_limits[category] = max(1, int(total_tasks * percentage / 100))
    
    # Select tasks respecting limits
    balanced_tasks = []
    
    # First, add high priority tasks
    for category, tasks in by_category.items():
        high_priority = [t for t in tasks if t["priority"] == 1]
        for task in high_priority[:category_limits.get(category, 1)]:
            balanced_tasks.append(task)
            
            # Decrement limit for this category
            if category in category_limits:
                category_limits[category] -= 1
    
    # Then add medium priority tasks
    for category, tasks in by_category.items():
        medium_priority = [t for t in tasks if t["priority"] == 2]
        for task in medium_priority[:category_limits.get(category, 0)]:
            balanced_tasks.append(task)
            
            # Decrement limit for this category
            if category in category_limits:
                category_limits[category] -= 1
    
    # Finally add low priority tasks
    for category, tasks in by_category.items():
        low_priority = [t for t in tasks if t["priority"] == 3]
        for task in low_priority[:category_limits.get(category, 0)]:
            balanced_tasks.append(task)
    
    return balanced_tasks

def allocate_time_slots(tasks, blueprint):
    """
    Allocate tasks to time slots in the day
    
    Args:
        tasks: List of tasks to allocate
        blueprint: Blueprint object for the day
        
    Returns:
        List of allocated time slots
    """
    # Create a list of available slots
    available_slots = MORNING_SLOTS + AFTERNOON_SLOTS + EVENING_SLOTS
    
    # Assign time slots based on task category preferences
    category_time_preferences = {
        "Class 11": MORNING_SLOTS,
        "AI Tools": MORNING_SLOTS + AFTERNOON_SLOTS,
        "Freelancing": AFTERNOON_SLOTS + EVENING_SLOTS,
        "Certifications": AFTERNOON_SLOTS,
        "Career Planning": EVENING_SLOTS
    }
    
    # Sort tasks by priority
    tasks.sort(key=lambda x: x["priority"])
    
    # Track allocated slots
    allocated_slots = []
    used_slots = set()
    
    for task in tasks:
        # Get preferred slots for this category
        preferred_slots = category_time_preferences.get(task["category"], available_slots)
        
        # Find an available slot
        allocated = False
        for slot in preferred_slots:
            # Skip if slot is already used
            slot_id = f"{slot['start']}-{slot['end']}"
            if slot_id in used_slots:
                continue
            
            # Create time slot
            time_slot = TimeSlot()
            time_slot.blueprint_id = blueprint.id
            time_slot.category_id = task["category_id"]
            time_slot.title = task["title"]
            time_slot.description = f"Auto-scheduled task"
            time_slot.start_time = datetime.strptime(slot["start"], "%H:%M").time()
            time_slot.end_time = datetime.strptime(slot["end"], "%H:%M").time()
            time_slot.goal_id = task["goal_id"]
            
            db.session.add(time_slot)
            allocated_slots.append(time_slot)
            used_slots.add(slot_id)
            allocated = True
            break
        
        if not allocated:
            # If no preferred slot is available, try any slot
            for slot in available_slots:
                slot_id = f"{slot['start']}-{slot['end']}"
                if slot_id in used_slots:
                    continue
                
                # Create time slot
                time_slot = TimeSlot()
                time_slot.blueprint_id = blueprint.id
                time_slot.category_id = task["category_id"]
                time_slot.title = task["title"]
                time_slot.description = f"Auto-scheduled task"
                time_slot.start_time = datetime.strptime(slot["start"], "%H:%M").time()
                time_slot.end_time = datetime.strptime(slot["end"], "%H:%M").time()
                time_slot.goal_id = task["goal_id"]
                
                db.session.add(time_slot)
                allocated_slots.append(time_slot)
                used_slots.add(slot_id)
                break
    
    return allocated_slots

def get_daily_schedule(day=None):
    """
    Get schedule for a specific day or today
    
    Args:
        day: Day of week, or None for today
        
    Returns:
        Dictionary with schedule information
    """
    if day is None:
        # Get current day of week
        day = datetime.utcnow().strftime("%A")
    
    # Find blueprint for this day
    blueprint = Blueprint.query.filter_by(day_of_week=day).first()
    
    if not blueprint:
        return {
            "day": day,
            "has_schedule": False,
            "time_slots": []
        }
    
    # Get time slots for this blueprint
    time_slots = TimeSlot.query.filter_by(blueprint_id=blueprint.id).all()
    
    formatted_slots = []
    for slot in time_slots:
        # Get category
        category = Category.query.get(slot.category_id)
        
        # Format times
        start_time = slot.start_time.strftime("%H:%M")
        end_time = slot.end_time.strftime("%H:%M")
        
        formatted_slots.append({
            "id": slot.id,
            "title": slot.title,
            "description": slot.description,
            "start_time": start_time,
            "end_time": end_time,
            "category": category.name if category else "Uncategorized",
            "category_color": category.color if category else "#6c757d",
            "goal_id": slot.goal_id
        })
    
    # Sort by start time
    formatted_slots.sort(key=lambda x: x["start_time"])
    
    return {
        "day": day,
        "has_schedule": True,
        "blueprint_id": blueprint.id,
        "time_slots": formatted_slots
    }

def regenerate_schedule():
    """
    Regenerate the entire weekly schedule
    
    Returns:
        Boolean indicating success
    """
    return generate_weekly_schedule()

def mark_slot_complete(slot_id):
    """
    Mark a time slot's task as completed
    
    Args:
        slot_id: ID of the TimeSlot
        
    Returns:
        Boolean indicating success
    """
    try:
        # Get the time slot
        time_slot = TimeSlot.query.get(slot_id)
        if not time_slot:
            return False
        
        # Get the associated task (if any)
        task = Task.query.filter_by(
            goal_id=time_slot.goal_id,
            title=time_slot.title
        ).first()
        
        if task:
            # Mark task as completed
            task.completed = True
            task.completion_date = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Marked task '{task.title}' as completed")
            
        return True
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error marking slot complete: {str(e)}")
        return False

def handle_missed_task(task_id):
    """
    Handle a missed task by rescheduling it
    
    Args:
        task_id: ID of the missed task
        
    Returns:
        Boolean indicating success
    """
    try:
        # Get the task
        task = Task.query.get(task_id)
        if not task:
            return False
        
        # Extend deadline if it's in the past
        now = datetime.utcnow()
        if task.deadline and task.deadline < now:
            # Set new deadline to tomorrow
            tomorrow = now.date() + timedelta(days=1)
            task.deadline = datetime.combine(tomorrow, time(hour=17, minute=0))
            
            # Log the missed task
            # In a real system, we would have a MissedTask model
            logger.info(f"Rescheduled missed task: {task.title}")
            
            db.session.commit()
        
        # Regenerate schedule to fit the task
        regenerate_schedule()
        
        return True
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error handling missed task: {str(e)}")
        return False

def snooze_task(slot_id):
    """
    Snooze a task by moving it to next available slot
    
    Args:
        slot_id: ID of the TimeSlot to snooze
        
    Returns:
        Boolean indicating success
    """
    try:
        # Get the time slot
        time_slot = TimeSlot.query.get(slot_id)
        if not time_slot:
            return False
        
        # Get the task
        task = Task.query.filter_by(
            goal_id=time_slot.goal_id,
            title=time_slot.title
        ).first()
        
        if task:
            # Push deadline one day if it's today or earlier
            now = datetime.utcnow()
            today = now.date()
            
            if task.deadline and task.deadline.date() <= today:
                tomorrow = today + timedelta(days=1)
                task.deadline = datetime.combine(tomorrow, time(hour=17, minute=0))
                db.session.commit()
        
        # Delete the time slot
        db.session.delete(time_slot)
        db.session.commit()
        
        # Regenerate schedule
        regenerate_schedule()
        
        return True
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error snoozing task: {str(e)}")
        return False