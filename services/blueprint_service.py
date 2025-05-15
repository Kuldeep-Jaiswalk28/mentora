"""
Blueprint service for the Mentora application
Handles business logic for schedule blueprint management
"""
import logging
from datetime import datetime, time
from app import db
from models import Blueprint, TimeSlot, Category, Goal

logger = logging.getLogger(__name__)

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
    
    return query.all()

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
    # First, try to find a specific blueprint for this day
    blueprint = Blueprint.query.filter_by(day_of_week=day_of_week, is_active=True).first()
    
    # If no specific day blueprint, return the default (day_of_week=None) blueprint
    if not blueprint:
        blueprint = Blueprint.query.filter_by(day_of_week=None, is_active=True).first()
    
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
        is_active=is_active
    )
    
    db.session.add(blueprint)
    db.session.commit()
    
    logger.info(f"Created new blueprint: {blueprint.id} - {blueprint.name}")
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
        logger.warning(f"Attempted to update non-existent blueprint with ID: {blueprint_id}")
        return None
    
    # Update fields if provided
    if name is not None:
        blueprint.name = name
    
    if description is not None:
        blueprint.description = description
    
    if day_of_week is not None:
        blueprint.day_of_week = day_of_week
    
    if is_active is not None:
        blueprint.is_active = is_active
    
    blueprint.updated_at = datetime.utcnow()
    
    db.session.add(blueprint)
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
        logger.warning(f"Attempted to delete non-existent blueprint with ID: {blueprint_id}")
        return False
    
    # Blueprint deletion will cascade to time slots due to relationship setup
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
    
    if blueprint_id is not None:
        query = query.filter_by(blueprint_id=blueprint_id)
    
    if category_id is not None:
        query = query.filter_by(category_id=category_id)
    
    return query.order_by(TimeSlot.start_time).all()

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
    # Ensure blueprint exists
    blueprint = Blueprint.query.get(blueprint_id)
    if not blueprint:
        logger.error(f"Cannot create time slot: Blueprint {blueprint_id} not found")
        return None
    
    # Ensure category exists
    category = Category.query.get(category_id)
    if not category:
        logger.error(f"Cannot create time slot: Category {category_id} not found")
        return None
    
    # If goal_id provided, ensure it exists
    if goal_id is not None:
        goal = Goal.query.get(goal_id)
        if not goal:
            logger.warning(f"Goal {goal_id} not found, creating time slot without goal association")
            goal_id = None
    
    # Convert string times to time objects
    if isinstance(start_time, str):
        hour, minute = map(int, start_time.split(':'))
        start_time = time(hour, minute)
    
    if isinstance(end_time, str):
        hour, minute = map(int, end_time.split(':'))
        end_time = time(hour, minute)
    
    # Create time slot
    time_slot = TimeSlot(
        blueprint_id=blueprint_id,
        category_id=category_id,
        title=title,
        description=description,
        start_time=start_time,
        end_time=end_time,
        goal_id=goal_id
    )
    
    db.session.add(time_slot)
    db.session.commit()
    
    logger.info(f"Created new time slot: {time_slot.id} - {time_slot.title}")
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
        logger.warning(f"Attempted to update non-existent time slot with ID: {slot_id}")
        return None
    
    # Update fields if provided
    if title is not None:
        time_slot.title = title
    
    if description is not None:
        time_slot.description = description
    
    if start_time is not None:
        if isinstance(start_time, str):
            hour, minute = map(int, start_time.split(':'))
            start_time = time(hour, minute)
        time_slot.start_time = start_time
    
    if end_time is not None:
        if isinstance(end_time, str):
            hour, minute = map(int, end_time.split(':'))
            end_time = time(hour, minute)
        time_slot.end_time = end_time
    
    if category_id is not None:
        # Ensure category exists
        if Category.query.get(category_id):
            time_slot.category_id = category_id
        else:
            logger.warning(f"Cannot update time slot: Category {category_id} not found")
    
    if goal_id is not None:
        # Handle null case specially
        if goal_id == 0:
            time_slot.goal_id = None
        # Ensure goal exists if not null
        elif Goal.query.get(goal_id):
            time_slot.goal_id = goal_id
        else:
            logger.warning(f"Cannot update time slot: Goal {goal_id} not found")
    
    db.session.add(time_slot)
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
        logger.warning(f"Attempted to delete non-existent time slot with ID: {slot_id}")
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
    day_name = today.strftime('%A')  # e.g., Monday, Tuesday
    
    # Get blueprint for today
    blueprint = get_blueprint_for_day(day_name)
    
    if not blueprint:
        return {
            'date': today.strftime('%Y-%m-%d'),
            'day_of_week': day_name,
            'has_schedule': False,
            'message': 'No schedule blueprint defined for today',
            'time_slots': []
        }
    
    # Get time slots ordered by start time
    time_slots = get_time_slots(blueprint_id=blueprint.id)
    
    return {
        'date': today.strftime('%Y-%m-%d'),
        'day_of_week': day_name,
        'has_schedule': True,
        'blueprint_id': blueprint.id,
        'blueprint_name': blueprint.name,
        'blueprint_description': blueprint.description,
        'time_slots': [slot.to_dict() for slot in time_slots]
    }

def get_default_blueprint():
    """
    Create a default blueprint if none exists
    
    Returns:
        Blueprint object
    """
    # Check if there's already a default blueprint
    default = Blueprint.query.filter_by(day_of_week=None, is_active=True).first()
    
    if default:
        return default
    
    # Create a new default blueprint
    default = create_blueprint(
        name="Default Daily Schedule",
        description="Default schedule for a balanced productive day",
        day_of_week=None,
        is_active=True
    )
    
    # Get categories
    from services.category_service import get_all_categories, get_default_categories
    categories = get_all_categories()
    
    if not categories:
        categories = get_default_categories()
    
    # Map of category names to objects
    category_map = {category.name: category for category in categories}
    
    # Add default time slots
    if 'Study' in category_map:
        create_time_slot(
            blueprint_id=default.id,
            category_id=category_map['Study'].id,
            title="Morning Study Session",
            description="Focus on the most challenging subjects",
            start_time="08:00",
            end_time="10:00"
        )
        
        create_time_slot(
            blueprint_id=default.id,
            category_id=category_map['Study'].id,
            title="Afternoon Review",
            description="Review and practice problems",
            start_time="14:00",
            end_time="15:30"
        )
    
    if 'Freelancing' in category_map:
        create_time_slot(
            blueprint_id=default.id,
            category_id=category_map['Freelancing'].id,
            title="Freelance Work",
            description="Focus on client projects",
            start_time="10:30",
            end_time="12:30"
        )
    
    if 'AI Tools' in category_map:
        create_time_slot(
            blueprint_id=default.id,
            category_id=category_map['AI Tools'].id,
            title="AI Practice Session",
            description="Practice using AI tools and learning new techniques",
            start_time="16:00",
            end_time="17:30"
        )
    
    if 'Certifications' in category_map:
        create_time_slot(
            blueprint_id=default.id,
            category_id=category_map['Certifications'].id,
            title="Certification Prep",
            description="Study for upcoming certifications",
            start_time="19:00",
            end_time="20:30"
        )
    
    logger.info(f"Created default blueprint with {default.time_slots.count()} time slots")
    return default