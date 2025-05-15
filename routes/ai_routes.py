from flask import Blueprint, jsonify, request
from services.ai_service import (
    get_all_messages,
    get_message_by_id,
    create_user_message,
    generate_ai_response,
    get_daily_advice
)

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')

@ai_bp.route('/chat', methods=['GET'])
def get_chat_history():
    """Get chat history"""
    limit = request.args.get('limit', 100, type=int)
    newest_first = request.args.get('newest_first', type=lambda v: v.lower() == 'true', default=False)
    
    messages = get_all_messages(limit=limit, newest_first=newest_first)
    return jsonify([message.to_dict() for message in messages])

@ai_bp.route('/chat/<int:message_id>', methods=['GET'])
def get_message(message_id):
    """Get a specific message by ID"""
    message = get_message_by_id(message_id)
    
    if not message:
        return jsonify({"error": "Message not found"}), 404
    
    return jsonify(message.to_dict())

@ai_bp.route('/chat', methods=['POST'])
def send_message():
    """Send a message to AI mentor and get a response"""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    if 'message' not in data or not data['message'].strip():
        return jsonify({"error": "Message cannot be empty"}), 400
    
    # Create user message
    user_message = create_user_message(data['message'])
    
    # Generate AI response
    ai_response = generate_ai_response(user_message.id)
    
    # Return both messages
    return jsonify({
        'user_message': user_message.to_dict(),
        'ai_response': ai_response.to_dict() if ai_response else None
    }), 201

@ai_bp.route('/advice', methods=['GET'])
def get_advice():
    """Get personalized daily advice from AI mentor"""
    advice = get_daily_advice()
    return jsonify(advice)