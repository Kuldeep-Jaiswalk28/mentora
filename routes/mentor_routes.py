from flask import Blueprint, jsonify, request
from services.mentor_ai_service import (
    get_user_response,
    generate_proactive_message, 
    should_send_proactive_message,
    record_feedback
)

mentor_bp = Blueprint('mentor', __name__, url_prefix='/api/mentor')

@mentor_bp.route('/chat', methods=['POST'])
def chat_with_mentor():
    """Send a message to the AI mentor and get a response"""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    if 'message' not in data or not data['message'].strip():
        return jsonify({"error": "Message cannot be empty"}), 400
    
    # Get response from the AI mentor
    response = get_user_response(data['message'])
    
    return jsonify({
        "response": response
    })

@mentor_bp.route('/proactive/<message_type>', methods=['GET'])
def get_proactive_message(message_type):
    """Get a proactive message from the AI mentor"""
    # Validate message type
    valid_types = ['start_task', 'mid_task', 'end_task', 'evening_summary']
    if message_type not in valid_types:
        return jsonify({"error": f"Invalid message type. Must be one of: {', '.join(valid_types)}"}), 400
    
    # Check if we should send a message
    if not should_send_proactive_message(message_type):
        return jsonify({
            "should_send": False,
            "message": None
        })
    
    # Generate the message
    message = generate_proactive_message(message_type)
    
    return jsonify({
        "should_send": True,
        "message": message
    })

@mentor_bp.route('/feedback/<int:message_id>', methods=['POST'])
def provide_feedback(message_id):
    """Provide feedback on an AI mentor message"""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    if 'is_helpful' not in data or not isinstance(data['is_helpful'], bool):
        return jsonify({"error": "is_helpful field must be a boolean"}), 400
    
    # Record the feedback
    success = record_feedback(message_id, data['is_helpful'])
    
    if not success:
        return jsonify({"error": "Message not found"}), 404
    
    return jsonify({
        "success": True,
        "message": "Feedback recorded successfully"
    })