from flask import Blueprint, jsonify, request
from werkzeug.exceptions import NotFound

from app import db
from models import Blueprint as BlueprintModel, TimeSlot
from services.blueprint_service import (
    get_all_blueprints, get_blueprint_by_id, 
    create_blueprint, update_blueprint, delete_blueprint,
    get_time_slots, create_time_slot, update_time_slot, 
    delete_time_slot, get_today_schedule, get_default_blueprint
)
from utils.data_validator import validate_blueprint_data, validate_time_slot_data

blueprint_bp = Blueprint('blueprints', __name__, url_prefix='/api/blueprints')

@blueprint_bp.route('', methods=['GET'])
def list_blueprints():
    """Get all blueprints"""
    active_only = request.args.get('active_only', 'false').lower() == 'true'
    blueprints = get_all_blueprints(active_only)
    
    return jsonify({
        'blueprints': [blueprint.to_dict() for blueprint in blueprints]
    })

@blueprint_bp.route('/<int:blueprint_id>', methods=['GET'])
def get_blueprint(blueprint_id):
    """Get a specific blueprint by ID"""
    blueprint = get_blueprint_by_id(blueprint_id)
    
    if not blueprint:
        return jsonify({"error": "Blueprint not found"}), 404
    
    return jsonify({
        'blueprint': blueprint.to_dict()
    })

@blueprint_bp.route('', methods=['POST'])
def add_blueprint():
    """Create a new blueprint"""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    # Validate the data
    validation = validate_blueprint_data(data)
    if not validation['valid']:
        return jsonify({"error": "Invalid data", "details": validation['errors']}), 400
    
    # Create the blueprint
    try:
        blueprint = create_blueprint(
            name=data['name'],
            description=data.get('description'),
            day_of_week=data.get('day_of_week'),
            is_active=data.get('is_active', True)
        )
        
        return jsonify({
            'message': "Blueprint created successfully",
            'blueprint': blueprint.to_dict()
        }), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@blueprint_bp.route('/<int:blueprint_id>', methods=['PUT'])
def modify_blueprint(blueprint_id):
    """Update an existing blueprint"""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    # Validate the data
    validation = validate_blueprint_data(data, required=False)
    if not validation['valid']:
        return jsonify({"error": "Invalid data", "details": validation['errors']}), 400
    
    # Update the blueprint
    blueprint = update_blueprint(
        blueprint_id=blueprint_id,
        name=data.get('name'),
        description=data.get('description'),
        day_of_week=data.get('day_of_week'),
        is_active=data.get('is_active')
    )
    
    if not blueprint:
        return jsonify({"error": "Blueprint not found"}), 404
    
    return jsonify({
        'message': "Blueprint updated successfully",
        'blueprint': blueprint.to_dict()
    })

@blueprint_bp.route('/<int:blueprint_id>', methods=['DELETE'])
def remove_blueprint(blueprint_id):
    """Delete a blueprint"""
    success = delete_blueprint(blueprint_id)
    
    if not success:
        return jsonify({"error": "Blueprint not found"}), 404
    
    return jsonify({
        'message': "Blueprint deleted successfully"
    })

@blueprint_bp.route('/<int:blueprint_id>/time_slots', methods=['GET'])
def list_time_slots(blueprint_id):
    """Get all time slots for a blueprint"""
    slots = get_time_slots(blueprint_id=blueprint_id)
    
    return jsonify({
        'time_slots': [slot.to_dict() for slot in slots]
    })

@blueprint_bp.route('/<int:blueprint_id>/time_slots', methods=['POST'])
def add_time_slot(blueprint_id):
    """Create a new time slot for a blueprint"""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    # Validate the data
    validation = validate_time_slot_data(data)
    if not validation['valid']:
        return jsonify({"error": "Invalid data", "details": validation['errors']}), 400
    
    # Create the time slot
    try:
        slot = create_time_slot(
            blueprint_id=blueprint_id,
            category_id=data['category_id'],
            title=data['title'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            description=data.get('description'),
            goal_id=data.get('goal_id')
        )
        
        return jsonify({
            'message': "Time slot created successfully",
            'time_slot': slot.to_dict()
        }), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@blueprint_bp.route('/time_slots/<int:slot_id>', methods=['PUT'])
def modify_time_slot(slot_id):
    """Update an existing time slot"""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    # Validate the data
    validation = validate_time_slot_data(data, required=False)
    if not validation['valid']:
        return jsonify({"error": "Invalid data", "details": validation['errors']}), 400
    
    # Update the time slot
    slot = update_time_slot(
        slot_id=slot_id,
        title=data.get('title'),
        description=data.get('description'),
        start_time=data.get('start_time'),
        end_time=data.get('end_time'),
        category_id=data.get('category_id'),
        goal_id=data.get('goal_id')
    )
    
    if not slot:
        return jsonify({"error": "Time slot not found"}), 404
    
    return jsonify({
        'message': "Time slot updated successfully",
        'time_slot': slot.to_dict()
    })

@blueprint_bp.route('/time_slots/<int:slot_id>', methods=['DELETE'])
def remove_time_slot(slot_id):
    """Delete a time slot"""
    success = delete_time_slot(slot_id)
    
    if not success:
        return jsonify({"error": "Time slot not found"}), 404
    
    return jsonify({
        'message': "Time slot deleted successfully"
    })

@blueprint_bp.route('/today_schedule', methods=['GET'])
def get_schedule_for_today():
    """Get the schedule for today"""
    schedule = get_today_schedule()
    
    return jsonify(schedule)

@blueprint_bp.route('/default', methods=['GET'])
def create_default():
    """Create or get default blueprint"""
    blueprint = get_default_blueprint()
    
    return jsonify({
        'message': "Default blueprint retrieved or created",
        'blueprint': blueprint.to_dict()
    })