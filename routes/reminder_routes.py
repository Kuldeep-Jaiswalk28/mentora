from flask import Blueprint, jsonify, request
from utils.data_validator import validate_request, reminder_schema
from services.reminder_service import (
    get_all_reminders,
    get_reminder_by_id,
    create_reminder,
    update_reminder,
    delete_reminder,
    get_reminders_by_task,
    create_default_reminders_for_task
)

reminders_bp = Blueprint('reminders', __name__, url_prefix='/api/reminders')

@reminders_bp.route('/', methods=['GET'])
def list_reminders():
    """Get all reminders with optional filtering"""
    task_id = request.args.get('task_id', type=int)
    triggered = request.args.get('triggered', type=lambda v: v.lower() == 'true')
    
    if task_id:
        reminders = get_reminders_by_task(task_id, triggered=triggered)
    else:
        reminders = get_all_reminders(triggered=triggered)
    
    return jsonify([reminder.to_dict() for reminder in reminders])

@reminders_bp.route('/<int:reminder_id>', methods=['GET'])
def get_reminder(reminder_id):
    """Get a specific reminder by ID"""
    reminder = get_reminder_by_id(reminder_id)
    
    if not reminder:
        return jsonify({"error": "Reminder not found"}), 404
    
    return jsonify(reminder.to_dict())

@reminders_bp.route('/', methods=['POST'])
@validate_request(reminder_schema)
def add_reminder():
    """Create a new reminder"""
    data = request.get_json()
    
    reminder = create_reminder(
        task_id=data['task_id'],
        reminder_time=data['reminder_time'],
        message=data.get('message')
    )
    
    if not reminder:
        return jsonify({"error": "Task not found"}), 404
    
    return jsonify(reminder.to_dict()), 201

@reminders_bp.route('/<int:reminder_id>', methods=['PUT'])
@validate_request(reminder_schema)
def modify_reminder(reminder_id):
    """Update an existing reminder"""
    data = request.get_json()
    
    reminder = update_reminder(
        reminder_id=reminder_id,
        task_id=data.get('task_id'),
        reminder_time=data.get('reminder_time'),
        message=data.get('message'),
        triggered=data.get('triggered')
    )
    
    if not reminder:
        return jsonify({"error": "Reminder not found"}), 404
    
    return jsonify(reminder.to_dict())

@reminders_bp.route('/<int:reminder_id>', methods=['DELETE'])
def remove_reminder(reminder_id):
    """Delete a reminder"""
    success = delete_reminder(reminder_id)
    
    if not success:
        return jsonify({"error": "Reminder not found"}), 404
    
    return jsonify({"message": "Reminder deleted successfully"}), 200

@reminders_bp.route('/task/<int:task_id>/defaults', methods=['POST'])
def add_default_reminders(task_id):
    """Create default reminders for a task"""
    reminders = create_default_reminders_for_task(task_id)
    
    if not reminders:
        return jsonify({"error": "Task not found or has no deadline"}), 404
    
    return jsonify([reminder.to_dict() for reminder in reminders]), 201
