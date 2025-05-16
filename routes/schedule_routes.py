from flask import Blueprint, jsonify, request
from services.schedule_engine import (
    get_daily_schedule,
    regenerate_schedule,
    mark_slot_complete,
    snooze_task,
    handle_missed_task
)
from services.blueprint_import_service import (
    load_blueprint_file,
    import_blueprint_to_database
)

schedule_bp = Blueprint('schedule', __name__, url_prefix='/api/schedule')

@schedule_bp.route('/today', methods=['GET'])
def get_schedule_for_today():
    """Get the schedule for today"""
    schedule = get_daily_schedule()
    return jsonify(schedule)

@schedule_bp.route('/day/<day>', methods=['GET'])
def get_schedule_for_day(day):
    """Get the schedule for a specific day"""
    schedule = get_daily_schedule(day)
    return jsonify(schedule)

@schedule_bp.route('/regenerate', methods=['POST'])
def regenerate_weekly_schedule():
    """Regenerate the weekly schedule"""
    success = regenerate_schedule()
    return jsonify({
        "success": success,
        "message": "Weekly schedule regenerated successfully" if success else "Failed to regenerate schedule"
    })

@schedule_bp.route('/complete/<int:slot_id>', methods=['POST'])
def complete_slot(slot_id):
    """Mark a time slot's task as completed"""
    success = mark_slot_complete(slot_id)
    return jsonify({
        "success": success,
        "message": "Task marked as completed" if success else "Failed to mark task as completed"
    })

@schedule_bp.route('/snooze/<int:slot_id>', methods=['POST'])
def snooze_slot(slot_id):
    """Snooze a task for later"""
    success = snooze_task(slot_id)
    return jsonify({
        "success": success,
        "message": "Task snoozed successfully" if success else "Failed to snooze task"
    })

@schedule_bp.route('/missed/<int:task_id>', methods=['POST'])
def report_missed_task(task_id):
    """Handle a missed task"""
    success = handle_missed_task(task_id)
    return jsonify({
        "success": success,
        "message": "Missed task handled successfully" if success else "Failed to handle missed task"
    })

@schedule_bp.route('/import', methods=['POST'])
def import_blueprint():
    """Import blueprint from file and generate schedule"""
    # Load blueprint file
    blueprint_data = load_blueprint_file()
    if not blueprint_data:
        return jsonify({
            "success": False,
            "message": "Failed to load blueprint file"
        }), 500
    
    # Import to database
    success = import_blueprint_to_database(blueprint_data)
    if not success:
        return jsonify({
            "success": False,
            "message": "Failed to import blueprint to database"
        }), 500
    
    # Generate schedule
    success = regenerate_schedule()
    
    return jsonify({
        "success": success,
        "message": "Blueprint imported and schedule generated successfully" if success else "Failed to generate schedule"
    })