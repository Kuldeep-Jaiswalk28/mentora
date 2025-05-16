from flask import Blueprint, jsonify
from utils.reward_system import (
    check_for_new_badges,
    get_all_badges,
    get_earned_badges
)

reward_bp = Blueprint('rewards', __name__, url_prefix='/api/rewards')

@reward_bp.route('/badges', methods=['GET'])
def get_badges():
    """Get all badges with earned status"""
    badges = get_all_badges()
    
    return jsonify(badges)

@reward_bp.route('/earned', methods=['GET'])
def get_earned():
    """Get badges earned by the user"""
    badges = get_earned_badges()
    
    return jsonify({
        "badges": badges,
        "total": len(badges)
    })

@reward_bp.route('/check', methods=['POST'])
def check_badges():
    """Check for new badges"""
    new_badges = check_for_new_badges()
    
    return jsonify({
        "new_badges": new_badges,
        "found": len(new_badges) > 0
    })