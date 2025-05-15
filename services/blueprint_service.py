"""
Blueprint service for the Mentora application
Handles business logic for schedule blueprint management
"""
import logging
from datetime import datetime, time
import re

from app import db
from models import Blueprint, TimeSlot, Category, Goal

logger = logging.getLogger(__name__)

# Regular expression for time in HH:MM format
TIME_REGEX = re.compile(r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$')

def get_all_blueprints(active_only=False):
    """
    Get all schedule blueprints
    
    Args:
        active_only: Only return active blueprints
    
    Returns:
        List of Blueprint objects
    """
    query = Blueprint.query
    
    if active_only:
        query = query.filter_by(is_active=True)
    
    return query.order_by(Blueprint.name).all()

def get_blueprint_by_id(blueprint_id):
    """
    Get a blueprint by ID
    
    Args:
        blueprint_id: The ID of the blueprint to retrieve
    
    Returns:
        Blueprint object or None if not found
    """
    return Blueprint.query.get(blueprint_id)

def get_blueprint_for_day(day_of_week):
    """
    Get active blueprint for specific day of week
    
    Args:
        day_of_week: The day to retrieve blueprint for (Monday, Tuesday, etc.)
    
    Returns:
        Blueprint object or None if not found
    """
    # First look for a day-specific blueprint
    blueprint = Blueprint.query.filter_by(
        day_of_week=day_of_week,
        is_active=True
    ).first()
    
    # If no day-specific blueprint, look for a default one
    if not blueprint:
        blueprint = Blueprint.query.filter_by(
            day_of_week=None,
            is_active=True
        ).first()
    
    return blueprint

def create_blueprint(name, description=None, day_of_week=None, is_active=True):
    """
    Create a new schedule blueprint
    
    Args:
        name: Blueprint name
        description: Blueprint description
        day_of_week: Specific day of week (Monday, Tuesday, etc.) or None for any day
        is_active: Whether the blueprint is active
    
    Returns:
        Newly created Blueprint object
    """
    blueprint = Blueprint(
        name=name,
        description=description,
        day_of_week=day_of_week,
        is_active=is_active,
        created_at=datetime.utcnow()
    )
    
    db.session.add(blueprint)
    db.session.commit()
    
    logger.info(f"Created new blueprint: {blueprint.id}")
    return blueprint

def update_blueprint(blueprint_id, name=None, description=None, day_of_week=None, is_active=None):
    """
    Update an existing blueprint
    
    Args:
        blueprint_id: ID of the blueprint to update
        name: New name (optional)
        description: New description (optional)
        day_of_week: New day of week (optional)
        is_active: New active status (optional)
    
    Returns:
        Updated Blueprint object, or None if blueprint not found
    """
    blueprint = Blueprint.query.get(blueprint_id)
    
    if not blueprint:
        return None
    
    if name is not None:
        blueprint.name = name
    
    if description is not None:
        blueprint.description = description
    
    if day_of_week is not None:
        blueprint.day_of_week = day_of_week
    
    if is_active is not None:
        blueprint.is_active = is_active
    
    blueprint.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    logger.info(f"Updated blueprint: {blueprint.id}")
    return blueprint

def delete_blueprint(blueprint_id):
    """
    Delete a blueprint and its time slots
    
    Args:
        blueprint_id: ID of the blueprint to delete
    
    Returns:
        True if successful, False if blueprint not found
    """
    blueprint = Blueprint.query.get(blueprint_id)
    
    if not blueprint:
        return False
    
    db.session.delete(blueprint)
    db.session.commit()
    
    logger.info(f"Deleted blueprint: {blueprint_id}")
    return True

def get_time_slots(blueprint_id=None, category_id=None):
    """
    Get time slots with optional filtering
    
    Args:
        blueprint_id: Filter by blueprint ID
        category_id: Filter by category ID
    
    Returns:
        List of TimeSlot objects
    """
    query = TimeSlot.query
    
    if blueprint_id:
        query = query.filter_by(blueprint_id=blueprint_id)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    return query.order_by(TimeSlot.start_time).all()

def _parse_time(time_str):
    """
    Parse a time string in HH:MM format
    
    Args:
        time_str: Time string in HH:MM format
        
    Returns:
        time object or None if invalid format
    """
    if isinstance(time_str, time):
        return time_str
    
    match = TIME_REGEX.match(time_str)
    if not match:
        return None
    
    hour = int(match.group(1))
    minute = int(match.group(2))
    
    return time(hour, minute)

def create_time_slot(blueprint_id, category_id, title, start_time, end_time, description=None, goal_id=None):
    """
    Create a new time slot
    
    Args:
        blueprint_id: Blueprint ID
        category_id: Category ID
        title: Time slot title
        start_time: Start time (Time object or HH:MM string)
        end_time: End time (Time object or HH:MM string)
        description: Time slot description
        goal_id: Associated goal ID (optional)
    
    Returns:
        Newly created TimeSlot object
    """
    # Check if blueprint exists
    blueprint = Blueprint.query.get(blueprint_id)
    if not blueprint:
        raise ValueError(f"Blueprint with ID {blueprint_id} not found")
    
    # Check if category exists
    category = Category.query.get(category_id)
    if not category:
        raise ValueError(f"Category with ID {category_id} not found")
    
    # Check if goal exists (if provided)
    if goal_id:
        goal = Goal.query.get(goal_id)
        if not goal:
            raise ValueError(f"Goal with ID {goal_id} not found")
    
    # Parse times
    start_time_obj = _parse_time(start_time)
    end_time_obj = _parse_time(end_time)
    
    if not start_time_obj:
        raise ValueError(f"Invalid start time format: {start_time}")
    
    if not end_time_obj:
        raise ValueError(f"Invalid end time format: {end_time}")
    
    if start_time_obj >= end_time_obj:
        raise ValueError("End time must be after start time")
    
    # Create time slot
    time_slot = TimeSlot(
        blueprint_id=blueprint_id,
        category_id=category_id,
        title=title,
        description=description,
        start_time=start_time_obj,
        end_time=end_time_obj,
        goal_id=goal_id,
        created_at=datetime.utcnow()
    )
    
    db.session.add(time_slot)
    db.session.commit()
    
    logger.info(f"Created new time slot: {time_slot.id}")
    return time_slot

def update_time_slot(slot_id, title=None, description=None, start_time=None, end_time=None, 
                    category_id=None, goal_id=None):
    """
    Update an existing time slot
    
    Args:
        slot_id: ID of the time slot to update
        title: New title (optional)
        description: New description (optional)
        start_time: New start time (optional)
        end_time: New end time (optional)
        category_id: New category ID (optional)
        goal_id: New goal ID (optional)
    
    Returns:
        Updated TimeSlot object, or None if slot not found
    """
    time_slot = TimeSlot.query.get(slot_id)
    
    if not time_slot:
        return None
    
    if title is not None:
        time_slot.title = title
    
    if description is not None:
        time_slot.description = description
    
    # Update start time if provided
    if start_time is not None:
        start_time_obj = _parse_time(start_time)
        if not start_time_obj:
            raise ValueError(f"Invalid start time format: {start_time}")
        time_slot.start_time = start_time_obj
    
    # Update end time if provided
    if end_time is not None:
        end_time_obj = _parse_time(end_time)
        if not end_time_obj:
            raise ValueError(f"Invalid end time format: {end_time}")
        time_slot.end_time = end_time_obj
    
    # Check that start time is before end time
    if time_slot.start_time >= time_slot.end_time:
        raise ValueError("End time must be after start time")
    
    # Update category if provided
    if category_id is not None:
        category = Category.query.get(category_id)
        if not category:
            raise ValueError(f"Category with ID {category_id} not found")
        time_slot.category_id = category_id
    
    # Update goal if provided
    if goal_id is not None:
        if goal_id == 0:  # Allow removing goal association
            time_slot.goal_id = None
        else:
            goal = Goal.query.get(goal_id)
            if not goal:
                raise ValueError(f"Goal with ID {goal_id} not found")
            time_slot.goal_id = goal_id
    
    db.session.commit()
    
    logger.info(f"Updated time slot: {time_slot.id}")
    return time_slot

def delete_time_slot(slot_id):
    """
    Delete a time slot
    
    Args:
        slot_id: ID of the time slot to delete
    
    Returns:
        True if successful, False if not found
    """
    time_slot = TimeSlot.query.get(slot_id)
    
    if not time_slot:
        return False
    
    db.session.delete(time_slot)
    db.session.commit()
    
    logger.info(f"Deleted time slot: {slot_id}")
    return True

def get_today_schedule():
    """
    Get the schedule for today
    
    Returns:
        Dictionary with schedule details for today
    """
    today = datetime.utcnow()
    day_of_week = today.strftime('%A')  # Monday, Tuesday, etc.
    
    # Get blueprint for today
    blueprint = get_blueprint_for_day(day_of_week)
    
    # If no blueprint, return empty schedule
    if not blueprint:
        return {
            'date': today.strftime('%Y-%m-%d'),
            'day_of_week': day_of_week,
            'has_schedule': False,
            'blueprint_id': None,
            'blueprint_name': None,
            'time_slots': []
        }
    
    # Get time slots for this blueprint
    time_slots = get_time_slots(blueprint_id=blueprint.id)
    
    # Format time slots
    formatted_slots = []
    for slot in time_slots:
        # Get category details
        category = Category.query.get(slot.category_id)
        
        # Get goal details if associated
        goal = None
        if slot.goal_id:
            goal = Goal.query.get(slot.goal_id)
        
        formatted_slots.append({
            'id': slot.id,
            'title': slot.title,
            'description': slot.description,
            'start_time': slot.start_time.strftime('%H:%M'),
            'end_time': slot.end_time.strftime('%H:%M'),
            'category_id': slot.category_id,
            'category_name': category.name if category else None,
            'category_color': category.color if category else None,
            'goal_id': slot.goal_id,
            'goal_title': goal.title if goal else None
        })
    
    return {
        'date': today.strftime('%Y-%m-%d'),
        'day_of_week': day_of_week,
        'has_schedule': True,
        'blueprint_id': blueprint.id,
        'blueprint_name': blueprint.name,
        'time_slots': formatted_slots
    }

def get_default_blueprint():
    """
    Create a default blueprint if none exists
    
    Returns:
        Blueprint object
    """
    # Look for an existing default blueprint
    default = Blueprint.query.filter_by(name='Default Schedule').first()
    
    # If it exists, return it
    if default:
        return default
    
    # Create a new default blueprint
    default = create_blueprint(
        name='Default Schedule',
        description='Default daily schedule',
        day_of_week=None,
        is_active=True
    )
    
    # Create default time slots
    # First, get the Study category (or create it if it doesn't exist)
    study_category = Category.query.filter_by(name='Study').first()
    if not study_category:
        study_category = Category(
            name='Study',
            description='Academic pursuits and learning',
            color='#4a69bd'
        )
        db.session.add(study_category)
        db.session.commit()
    
    # Create some default time slots for a productive day
    create_time_slot(
        blueprint_id=default.id,
        category_id=study_category.id,
        title='Morning Study Session',
        start_time='08:00',
        end_time='10:00',
        description='Focused study time for your most important subject'
    )
    
    create_time_slot(
        blueprint_id=default.id,
        category_id=study_category.id,
        title='Afternoon Study Session',
        start_time='14:00',
        end_time='16:00',
        description='Review and practice exercises'
    )
    
    return default