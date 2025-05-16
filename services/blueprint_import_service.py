"""
Blueprint Import Service for Mentora application
Handles importing and parsing of structured blueprint files for automated task scheduling
"""
import json
import logging
import os
from datetime import datetime, timedelta
from app import db
from models import Category, Goal, Task, Blueprint, TimeSlot

logger = logging.getLogger(__name__)

# Define time block ranges
TIME_BLOCKS = {
    "morning": {"start": "06:00", "end": "12:00"},
    "afternoon": {"start": "12:00", "end": "17:00"},
    "evening": {"start": "17:00", "end": "22:00"}
}

# Define day of week mapping
DAY_MAP = {
    "Mon": "Monday",
    "Tue": "Tuesday",
    "Wed": "Wednesday",
    "Thu": "Thursday",
    "Fri": "Friday",
    "Sat": "Saturday",
    "Sun": "Sunday"
}

# Priority mapping (importance to priority value)
PRIORITY_MAP = {
    "high": 1,
    "medium": 2,
    "low": 3
}

def load_blueprint_file(filepath="blueprints/blueprint.json"):
    """
    Load and parse a blueprint JSON file
    
    Args:
        filepath: Path to the blueprint file
        
    Returns:
        Dictionary containing parsed blueprint data or None if error
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # If file doesn't exist, create a sample blueprint
        if not os.path.exists(filepath):
            logger.info(f"Blueprint file not found at {filepath}, creating sample blueprint")
            create_sample_blueprint(filepath)
        
        with open(filepath, 'r') as file:
            blueprint_data = json.load(file)
            
        logger.info(f"Successfully loaded blueprint from {filepath}")
        return blueprint_data
    
    except Exception as e:
        logger.error(f"Error loading blueprint file: {str(e)}")
        return None

def create_sample_blueprint(filepath):
    """
    Create a sample blueprint file with example tasks
    
    Args:
        filepath: Path where to save the sample blueprint
    """
    sample_blueprint = {
        "Class 11": [
            {
                "name": "Physics Ch1 - Laws of Motion",
                "duration": 50,
                "preferred_time": "morning",
                "days": ["Mon", "Wed", "Fri"],
                "importance": "high",
                "depends_on": []
            },
            {
                "name": "Maths - Trigonometry",
                "duration": 60,
                "preferred_time": "afternoon",
                "days": ["Tue", "Thu"],
                "importance": "medium",
                "depends_on": []
            },
            {
                "name": "Chemistry - Periodic Table",
                "duration": 45,
                "preferred_time": "morning",
                "days": ["Mon", "Thu"],
                "importance": "high",
                "depends_on": []
            }
        ],
        "AI Tools": [
            {
                "name": "Explore Replit Agents",
                "duration": 45,
                "preferred_time": "evening",
                "days": ["Mon", "Thu"],
                "importance": "medium",
                "depends_on": []
            },
            {
                "name": "Learn Cursor AI Features",
                "duration": 60,
                "preferred_time": "morning",
                "days": ["Tue", "Fri"],
                "importance": "medium",
                "depends_on": []
            }
        ],
        "Freelancing": [
            {
                "name": "Portfolio Website Update",
                "duration": 90,
                "preferred_time": "afternoon",
                "days": ["Wed", "Sat"],
                "importance": "high",
                "depends_on": []
            },
            {
                "name": "Client Meeting Prep",
                "duration": 30,
                "preferred_time": "evening",
                "days": ["Tue"],
                "importance": "high",
                "depends_on": []
            }
        ],
        "Certifications": [
            {
                "name": "AWS Cloud Practitioner Study",
                "duration": 60,
                "preferred_time": "afternoon",
                "days": ["Mon", "Wed", "Fri"],
                "importance": "medium",
                "depends_on": []
            }
        ],
        "Career Planning": [
            {
                "name": "Research University Options",
                "duration": 45,
                "preferred_time": "evening",
                "days": ["Sun"],
                "importance": "medium",
                "depends_on": []
            },
            {
                "name": "Update 5-Year Plan Document",
                "duration": 60,
                "preferred_time": "evening",
                "days": ["Sat"],
                "importance": "low",
                "depends_on": ["Research University Options"]
            }
        ]
    }
    
    # Save to file
    try:
        with open(filepath, 'w') as file:
            json.dump(sample_blueprint, file, indent=2)
        logger.info(f"Created sample blueprint at {filepath}")
    except Exception as e:
        logger.error(f"Error creating sample blueprint: {str(e)}")

def import_blueprint_to_database(blueprint_data):
    """
    Import blueprint data into the database
    
    Args:
        blueprint_data: Dictionary containing blueprint tasks and categories
        
    Returns:
        Boolean indicating success
    """
    try:
        # Process each category
        for category_name, tasks in blueprint_data.items():
            # Get or create category
            category = Category.query.filter_by(name=category_name).first()
            if not category:
                category = Category()
                category.name = category_name
                category.description = f"Tasks related to {category_name}"
                category.color = get_color_for_category(category_name)
                db.session.add(category)
                db.session.flush()  # Flush to get the ID without committing
            
            # Create a goal for this category if it doesn't exist
            goal_name = f"{category_name} Master Plan"
            goal = Goal.query.filter_by(title=goal_name, category_id=category.id).first()
            if not goal:
                goal = Goal()
                goal.title = goal_name
                goal.description = f"Master plan for {category_name} tasks"
                goal.category_id = category.id
                goal.start_date = datetime.utcnow()
                goal.end_date = datetime.utcnow() + timedelta(days=90)  # 3-month goal
                db.session.add(goal)
                db.session.flush()  # Flush to get the ID without committing
            
            # Process tasks
            for task_data in tasks:
                # Check if task already exists
                existing_task = Task.query.filter_by(
                    title=task_data["name"],
                    goal_id=goal.id
                ).first()
                
                if not existing_task:
                    # Calculate deadline based on current date and task preferences
                    deadline = calculate_deadline(task_data)
                    
                    # Create new task
                    task = Task()
                    task.title = task_data["name"]
                    task.description = f"Auto-generated task from blueprint"
                    task.goal_id = goal.id
                    task.deadline = deadline
                    task.priority = PRIORITY_MAP.get(task_data["importance"], 2)
                    task.completed = False
                    db.session.add(task)
        
        # Commit all changes
        db.session.commit()
        logger.info("Successfully imported blueprint to database")
        return True
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error importing blueprint to database: {str(e)}")
        return False

def get_color_for_category(category_name):
    """
    Get a sensible color for a category based on its name
    
    Args:
        category_name: Name of the category
        
    Returns:
        Color hex code
    """
    category_colors = {
        "Class 11": "#4285F4",  # Blue
        "AI Tools": "#0F9D58",  # Green
        "Freelancing": "#F4B400",  # Yellow
        "Certifications": "#DB4437",  # Red
        "Career Planning": "#9C27B0"  # Purple
    }
    
    return category_colors.get(category_name, "#6c757d")  # Default gray

def calculate_deadline(task_data):
    """
    Calculate a reasonable deadline for a task based on its preferences
    
    Args:
        task_data: Dictionary with task data
        
    Returns:
        DateTime object representing the deadline
    """
    now = datetime.utcnow()
    days_ahead = 0
    
    # Get preferred days
    preferred_days = task_data.get("days", [])
    if preferred_days:
        # Map day abbreviations to day numbers (0=Monday, 6=Sunday)
        day_to_num = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}
        preferred_day_nums = [day_to_num.get(day) for day in preferred_days if day in day_to_num]
        
        if preferred_day_nums:
            # Find the next preferred day
            current_day = now.weekday()
            for days in range(1, 8):  # Check up to 7 days ahead
                check_day = (current_day + days) % 7
                if check_day in preferred_day_nums:
                    days_ahead = days
                    break
    
    if days_ahead == 0:
        # If no valid preferred day, set deadline to 3 days ahead
        days_ahead = 3
    
    # Calculate the deadline date
    deadline_date = now + timedelta(days=days_ahead)
    
    # Set time based on preferred_time
    preferred_time = task_data.get("preferred_time", "afternoon")
    time_block = TIME_BLOCKS.get(preferred_time, TIME_BLOCKS["afternoon"])
    
    # Use the end time of the block as the deadline
    hours, minutes = map(int, time_block["end"].split(":"))
    
    deadline = deadline_date.replace(hour=hours, minute=minutes, second=0, microsecond=0)
    
    return deadline