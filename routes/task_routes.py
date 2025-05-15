from flask import Blueprint, jsonify, request
from datetime import datetime
from utils.data_validator import validate_request, task_schema
from services.task_service import (
    get_all_tasks,
    get_task_by_id,
    create_task,
    update_task,
    delete_task,
    get_tasks_by_goal,
    mark_task_completed,
    mark_task_incomplete,
    get_daily_tasks
)
from utils.priority_engine import suggest_next_task

tasks_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')

@tasks_bp.route('/', methods=['GET'])
def list_tasks():
    """Get all tasks with optional filtering"""
    goal_id = request.args.get('goal_id', type=int)
    completed = request.args.get('completed', type=lambda v: v.lower() == 'true')
    
    if goal_id:
        tasks = get_tasks_by_goal(goal_id, completed=completed)
    else:
        tasks = get_all_tasks(completed=completed)
    
    return jsonify([task.to_dict() for task in tasks])

@tasks_bp.route('/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """Get a specific task by ID"""
    task = get_task_by_id(task_id)
    
    if not task:
        return jsonify({"error": "Task not found"}), 404
    
    return jsonify(task.to_dict())

@tasks_bp.route('/', methods=['POST'])
@validate_request(task_schema)
def add_task():
    """Create a new task"""
    data = request.get_json()
    
    task = create_task(
        title=data['title'],
        description=data.get('description'),
        goal_id=data['goal_id'],
        deadline=data.get('deadline'),
        priority=data.get('priority', 2),
        recurrence_type=data.get('recurrence_type'),
        recurrence_value=data.get('recurrence_value'),
        parent_task_id=data.get('parent_task_id')
    )
    
    return jsonify(task.to_dict()), 201

@tasks_bp.route('/<int:task_id>', methods=['PUT'])
@validate_request(task_schema)
def modify_task(task_id):
    """Update an existing task"""
    data = request.get_json()
    
    task = update_task(
        task_id=task_id,
        title=data.get('title'),
        description=data.get('description'),
        goal_id=data.get('goal_id'),
        deadline=data.get('deadline'),
        priority=data.get('priority'),
        recurrence_type=data.get('recurrence_type'),
        recurrence_value=data.get('recurrence_value'),
        parent_task_id=data.get('parent_task_id')
    )
    
    if not task:
        return jsonify({"error": "Task not found"}), 404
    
    return jsonify(task.to_dict())

@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
def remove_task(task_id):
    """Delete a task"""
    success = delete_task(task_id)
    
    if not success:
        return jsonify({"error": "Task not found"}), 404
    
    return jsonify({"message": "Task deleted successfully"}), 200

@tasks_bp.route('/<int:task_id>/complete', methods=['POST'])
def complete_task(task_id):
    """Mark a task as completed"""
    task = mark_task_completed(task_id)
    
    if not task:
        return jsonify({"error": "Task not found"}), 404
    
    return jsonify(task.to_dict())

@tasks_bp.route('/<int:task_id>/incomplete', methods=['POST'])
def incomplete_task(task_id):
    """Mark a task as incomplete"""
    task = mark_task_incomplete(task_id)
    
    if not task:
        return jsonify({"error": "Task not found"}), 404
    
    return jsonify(task.to_dict())

@tasks_bp.route('/daily', methods=['GET'])
def get_daily_priority_tasks():
    """Get prioritized tasks for today"""
    tasks = get_daily_tasks()
    return jsonify([task.to_dict() for task in tasks])

@tasks_bp.route('/next', methods=['GET'])
def get_next_task():
    """Get the suggested next task to work on"""
    task = suggest_next_task()
    
    if not task:
        return jsonify({"message": "No tasks to suggest"}), 404
    
    return jsonify(task.to_dict())

@tasks_bp.route('/overdue', methods=['GET'])
def get_overdue_tasks():
    """Get all overdue tasks"""
    now = datetime.utcnow()
    
    tasks = get_all_tasks(completed=False)
    overdue_tasks = [task for task in tasks if task.deadline and task.deadline < now]
    
    return jsonify([task.to_dict() for task in overdue_tasks])
