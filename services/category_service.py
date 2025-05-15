"""
Category service for the Mentora application
Handles business logic for category management
"""
import logging
from app import db
from models import Category
from config import DEFAULT_CATEGORIES

logger = logging.getLogger(__name__)

def get_all_categories():
    """
    Get all categories
    
    Returns:
        List of Category objects
    """
    return Category.query.all()

def get_category_by_id(category_id):
    """
    Get a category by ID
    
    Args:
        category_id: The ID of the category to retrieve
    
    Returns:
        Category object or None if not found
    """
    return Category.query.get(category_id)

def get_category_by_name(name):
    """
    Get a category by name
    
    Args:
        name: The name of the category to retrieve
    
    Returns:
        Category object or None if not found
    """
    return Category.query.filter_by(name=name).first()

def create_category(name, description=None, color=None):
    """
    Create a new category
    
    Args:
        name: Category name
        description: Category description
        color: Category color (hex code)
    
    Returns:
        Newly created Category object
    """
    # Check if category with this name already exists
    existing = get_category_by_name(name)
    if existing:
        logger.warning(f"Category with name '{name}' already exists")
        return existing
    
    category = Category(
        name=name,
        description=description,
        color=color
    )
    
    db.session.add(category)
    db.session.commit()
    
    logger.info(f"Created new category: {category.id} - {category.name}")
    return category

def update_category(category_id, name=None, description=None, color=None):
    """
    Update an existing category
    
    Args:
        category_id: ID of the category to update
        name: New name (optional)
        description: New description (optional)
        color: New color (optional)
    
    Returns:
        Updated Category object, or None if category not found
    """
    category = Category.query.get(category_id)
    
    if not category:
        logger.warning(f"Attempted to update non-existent category with ID: {category_id}")
        return None
    
    # Update fields if provided
    if name is not None:
        # Check if another category already has this name
        existing = get_category_by_name(name)
        if existing and existing.id != category_id:
            logger.warning(f"Another category with name '{name}' already exists")
        else:
            category.name = name
    
    if description is not None:
        category.description = description
    
    if color is not None:
        category.color = color
    
    db.session.add(category)
    db.session.commit()
    
    logger.info(f"Updated category: {category.id}")
    return category

def delete_category(category_id):
    """
    Delete a category and all associated goals/tasks
    
    Args:
        category_id: ID of the category to delete
    
    Returns:
        True if successful, False if category not found
    """
    category = Category.query.get(category_id)
    
    if not category:
        logger.warning(f"Attempted to delete non-existent category with ID: {category_id}")
        return False
    
    # Category deletion will cascade to goals and tasks due to relationship setup
    db.session.delete(category)
    db.session.commit()
    
    logger.info(f"Deleted category: {category_id}")
    return True

def get_default_categories():
    """
    Create default categories if they don't exist
    
    Returns:
        List of created or existing default Category objects
    """
    result = []
    
    for category_data in DEFAULT_CATEGORIES:
        # Check if category already exists
        existing = get_category_by_name(category_data['name'])
        
        if existing:
            # Update existing category
            update_category(
                existing.id,
                description=category_data.get('description'),
                color=category_data.get('color')
            )
            result.append(existing)
        else:
            # Create new category
            category = create_category(
                name=category_data['name'],
                description=category_data.get('description'),
                color=category_data.get('color')
            )
            result.append(category)
    
    logger.info(f"Created/updated {len(result)} default categories")
    return result
