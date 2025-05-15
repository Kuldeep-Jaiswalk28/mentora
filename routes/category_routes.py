from flask import Blueprint, jsonify, request
from utils.data_validator import validate_request, category_schema
from services.category_service import (
    get_all_categories,
    get_category_by_id,
    create_category,
    update_category,
    delete_category,
    get_default_categories
)

categories_bp = Blueprint('categories', __name__, url_prefix='/api/categories')

@categories_bp.route('/', methods=['GET'])
def list_categories():
    """Get all categories"""
    categories = get_all_categories()
    return jsonify([category.to_dict() for category in categories])

@categories_bp.route('/<int:category_id>', methods=['GET'])
def get_category(category_id):
    """Get a specific category by ID"""
    category = get_category_by_id(category_id)
    
    if not category:
        return jsonify({"error": "Category not found"}), 404
    
    return jsonify(category.to_dict())

@categories_bp.route('/', methods=['POST'])
@validate_request(category_schema)
def add_category():
    """Create a new category"""
    data = request.get_json()
    
    category = create_category(
        name=data['name'],
        description=data.get('description'),
        color=data.get('color')
    )
    
    return jsonify(category.to_dict()), 201

@categories_bp.route('/<int:category_id>', methods=['PUT'])
@validate_request(category_schema)
def modify_category(category_id):
    """Update an existing category"""
    data = request.get_json()
    
    category = update_category(
        category_id=category_id,
        name=data.get('name'),
        description=data.get('description'),
        color=data.get('color')
    )
    
    if not category:
        return jsonify({"error": "Category not found"}), 404
    
    return jsonify(category.to_dict())

@categories_bp.route('/<int:category_id>', methods=['DELETE'])
def remove_category(category_id):
    """Delete a category"""
    success = delete_category(category_id)
    
    if not success:
        return jsonify({"error": "Category not found"}), 404
    
    return jsonify({"message": "Category deleted successfully"}), 200

@categories_bp.route('/defaults', methods=['POST'])
def reset_default_categories():
    """Reset to default categories"""
    created_categories = get_default_categories()
    return jsonify([category.to_dict() for category in created_categories]), 201
