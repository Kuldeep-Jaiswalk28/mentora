from flask import Blueprint, jsonify, request
from utils.data_validator import validate_request, goal_schema
from services.goal_service import (
    get_all_goals, 
    get_goal_by_id, 
    create_goal, 
    update_goal, 
    delete_goal,
    get_goal_progress
)

goals_bp = Blueprint('goals', __name__, url_prefix='/api/goals')

@goals_bp.route('/', methods=['GET'])
def list_goals():
    """Get all goals"""
    category_id = request.args.get('category_id', type=int)
    completed = request.args.get('completed', type=lambda v: v.lower() == 'true')
    
    goals = get_all_goals(category_id=category_id, completed=completed)
    return jsonify([goal.to_dict() for goal in goals])

@goals_bp.route('/<int:goal_id>', methods=['GET'])
def get_goal(goal_id):
    """Get a specific goal by ID"""
    goal = get_goal_by_id(goal_id)
    
    if not goal:
        return jsonify({"error": "Goal not found"}), 404
    
    return jsonify(goal.to_dict())

@goals_bp.route('/', methods=['POST'])
@validate_request(goal_schema)
def add_goal():
    """Create a new goal"""
    data = request.get_json()
    
    goal = create_goal(
        title=data['title'],
        description=data.get('description'),
        category_id=data['category_id'],
        start_date=data.get('start_date'),
        end_date=data.get('end_date'),
        completed=data.get('completed', False)
    )
    
    return jsonify(goal.to_dict()), 201

@goals_bp.route('/<int:goal_id>', methods=['PUT'])
@validate_request(goal_schema)
def modify_goal(goal_id):
    """Update an existing goal"""
    data = request.get_json()
    
    goal = update_goal(
        goal_id=goal_id,
        title=data.get('title'),
        description=data.get('description'),
        category_id=data.get('category_id'),
        start_date=data.get('start_date'),
        end_date=data.get('end_date'),
        completed=data.get('completed')
    )
    
    if not goal:
        return jsonify({"error": "Goal not found"}), 404
    
    return jsonify(goal.to_dict())

@goals_bp.route('/<int:goal_id>', methods=['DELETE'])
def remove_goal(goal_id):
    """Delete a goal"""
    success = delete_goal(goal_id)
    
    if not success:
        return jsonify({"error": "Goal not found"}), 404
    
    return jsonify({"message": "Goal deleted successfully"}), 200

@goals_bp.route('/<int:goal_id>/progress', methods=['GET'])
def get_progress(goal_id):
    """Get progress details for a goal"""
    progress_data = get_goal_progress(goal_id)
    
    if not progress_data:
        return jsonify({"error": "Goal not found"}), 404
    
    return jsonify(progress_data)

@goals_bp.route('/<int:goal_id>/complete', methods=['POST'])
def mark_goal_complete(goal_id):
    """Mark a goal as complete"""
    goal = update_goal(goal_id=goal_id, completed=True)
    
    if not goal:
        return jsonify({"error": "Goal not found"}), 404
    
    return jsonify(goal.to_dict())

@goals_bp.route('/<int:goal_id>/incomplete', methods=['POST'])
def mark_goal_incomplete(goal_id):
    """Mark a goal as incomplete"""
    goal = update_goal(goal_id=goal_id, completed=False)
    
    if not goal:
        return jsonify({"error": "Goal not found"}), 404
    
    return jsonify(goal.to_dict())
