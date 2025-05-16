from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from utils.progress_engine import (
    log_daily_progress, 
    get_daily_metrics, 
    get_weekly_metrics, 
    get_nudge_for_current_status,
    generate_weekly_report
)

progress_bp = Blueprint('progress', __name__, url_prefix='/api/progress')

@progress_bp.route('/daily', methods=['GET'])
def get_daily_progress():
    """Get daily progress metrics"""
    date_str = request.args.get('date')
    
    if date_str:
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    else:
        date = datetime.utcnow().date()
    
    # Get metrics for the specified date
    metrics = get_daily_metrics(date)
    
    return jsonify(metrics)

@progress_bp.route('/weekly', methods=['GET'])
def get_weekly_progress():
    """Get weekly progress metrics"""
    end_date_str = request.args.get('end_date')
    days = request.args.get('days', 7, type=int)
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    else:
        end_date = datetime.utcnow().date()
    
    # Get metrics for the specified week
    metrics = get_weekly_metrics(end_date, days)
    
    return jsonify(metrics)

@progress_bp.route('/log_today', methods=['POST'])
def log_today():
    """Manually trigger logging for today's progress"""
    log_daily_progress()
    
    return jsonify({
        "success": True,
        "message": "Daily progress logged successfully"
    })

@progress_bp.route('/nudge', methods=['GET'])
def get_nudge():
    """Get a smart nudge based on current status"""
    nudge = get_nudge_for_current_status()
    
    if nudge:
        return jsonify({
            "has_nudge": True,
            "nudge": nudge
        })
    else:
        return jsonify({
            "has_nudge": False
        })

@progress_bp.route('/weekly_report', methods=['GET'])
def get_weekly_report():
    """Get the weekly report"""
    report = generate_weekly_report()
    
    return jsonify({
        "report": report
    })

@progress_bp.route('/streak', methods=['GET'])
def get_streak():
    """Get the current streak"""
    # Get weekly metrics to determine streak
    metrics = get_weekly_metrics()
    
    return jsonify({
        "streak": metrics["streak"],
        "streak_text": f"{metrics['streak']} day{'s' if metrics['streak'] != 1 else ''} streak"
    })