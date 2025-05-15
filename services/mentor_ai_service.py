"""
Advanced AI Mentor Service for the Mentora application
Implements the intelligent AI mentor functionality with:
- Context awareness
- Proactive behavior
- Personalized responses
- Feedback integration
"""
import logging
import json
import os
from datetime import datetime, timedelta
import requests

from app import db
from models import (
    AIMessage, Task, Goal, Category, Blueprint, 
    TimeSlot, UserPreference
)
from utils.priority_engine import suggest_next_task
from services.progress_service import get_overall_progress

logger = logging.getLogger(__name__)

# System prompt defining Mentora's persona
MENTORA_PERSONA = """
You are Mentora, a personal AI teacher, productivity coach, and life guide for a 17-year-old high-potential student.
Your tone is gentle, positive, focused, and knowledgeable. You are emotionally intelligent and supportive.
You provide thoughtful guidance and relevant encouragement or reflection, not robotic replies.
You are helping the student balance their studies, freelancing work, AI tools learning, and certifications.

Guidelines for your responses:
1. Be concise but warm - use conversational language appropriate for a teenager.
2. Always acknowledge the student's current context (time, current task, progress).
3. Provide specific, actionable advice rather than generic platitudes.
4. Focus on progress and growth, not perfection.
5. Use positive reinforcement and growth mindset language.
6. Never provide medical, financial, or personal safety advice.
7. If asked something outside your scope, politely redirect to academic or productivity topics.
8. Adapt your tone based on the student's current task and historical performance.

You are a mentor, not just a task manager. Your goal is to help the student develop good habits,
stay motivated, and achieve their educational and career goals.
"""

def get_deepseek_api_key():
    """Get Deepseek API key from environment variables"""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        logger.error("DEEPSEEK_API_KEY environment variable not set")
    return api_key

def build_context(user_input=None):
    """
    Build the context for AI responses
    
    Args:
        user_input: Optional message from user
        
    Returns:
        Dictionary with context information
    """
    now = datetime.utcnow()
    
    # Get current time context
    time_context = {
        "current_time": now.strftime("%H:%M"),
        "current_date": now.strftime("%Y-%m-%d"),
        "day_of_week": now.strftime("%A")
    }
    
    # Get current task from schedule
    from services.blueprint_service import get_today_schedule
    schedule = get_today_schedule()
    
    current_task = None
    next_task = None
    time_left = None
    
    if schedule.get('has_schedule', False):
        time_slots = schedule.get('time_slots', [])
        
        # Convert current time to comparable format
        current_hour, current_minute = map(int, time_context['current_time'].split(':'))
        
        for slot in time_slots:
            # Parse start and end times
            start_hour, start_minute = map(int, slot['start_time'].split(':'))
            end_hour, end_minute = map(int, slot['end_time'].split(':'))
            
            # Check if current time is within this slot
            if (current_hour > start_hour or (current_hour == start_hour and current_minute >= start_minute)) and \
               (current_hour < end_hour or (current_hour == end_hour and current_minute < end_minute)):
                current_task = slot
                
                # Calculate time left in minutes
                time_left_minutes = (end_hour - current_hour) * 60 + (end_minute - current_minute)
                time_left = f"{time_left_minutes} minutes"
                break
            
            # Find the next task
            if not next_task and (current_hour < start_hour or (current_hour == start_hour and current_minute < start_minute)):
                next_task = slot
                break
    
    # If we don't have a current task from schedule, get next suggested task
    suggested_task = None
    if not current_task:
        suggested_task = suggest_next_task()
        if suggested_task:
            suggested_task = {
                'id': suggested_task.id,
                'title': suggested_task.title,
                'description': suggested_task.description,
                'goal_id': suggested_task.goal_id,
                'deadline': suggested_task.deadline.isoformat() if suggested_task.deadline else None,
                'priority': suggested_task.priority
            }
    
    # Get user progress stats
    progress_stats = get_overall_progress()
    
    # Get recent interactions
    recent_messages = AIMessage.query.order_by(AIMessage.timestamp.desc()).limit(5).all()
    recent_interactions = [
        {
            'is_from_user': msg.is_from_user,
            'message': msg.message,
            'timestamp': msg.timestamp.isoformat() if msg.timestamp else None
        }
        for msg in recent_messages
    ]
    
    # Get user preferences
    user_prefs = UserPreference.query.first()
    user_preferences = None
    if user_prefs:
        user_preferences = {
            'theme': user_prefs.theme,
            'enable_voice': user_prefs.enable_voice,
            'do_not_disturb': user_prefs.do_not_disturb
        }
    
    # Build the complete context
    context = {
        'time_context': time_context,
        'current_task': current_task,
        'next_task': next_task,
        'time_left': time_left,
        'suggested_task': suggested_task,
        'progress_stats': progress_stats,
        'recent_interactions': recent_interactions,
        'user_preferences': user_preferences,
        'user_input': user_input
    }
    
    return context

def call_deepseek_api(messages):
    """
    Call Deepseek API with the given messages
    
    Args:
        messages: List of message objects (role, content)
        
    Returns:
        AI response as string or None if error
    """
    api_key = get_deepseek_api_key()
    if not api_key:
        return "I'm sorry, but I can't access my AI capabilities right now. Please check the API configuration."
    
    try:
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",  # Using deepseek-chat model
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.7
            },
            timeout=15
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            logger.error(f"Deepseek API error: {response.status_code} - {response.text}")
            return "I'm sorry, but I encountered an issue processing your request. Please try again later."
    
    except Exception as e:
        logger.error(f"Error calling Deepseek API: {str(e)}")
        return "I'm sorry, but I encountered an issue connecting to my AI capabilities. Please try again later."

def get_user_response(user_message):
    """
    Generate an AI response to a user message with full context awareness
    
    Args:
        user_message: Text message from the user
        
    Returns:
        AI response text
    """
    # Build context for the request
    context = build_context(user_message)
    
    # Format the context as a string for the prompt
    context_str = json.dumps(context, indent=2)
    
    # Create messages for the API call
    messages = [
        {"role": "system", "content": MENTORA_PERSONA + "\n\nCurrent context:\n" + context_str},
        {"role": "user", "content": user_message}
    ]
    
    # Call the API
    response_text = call_deepseek_api(messages)
    
    # Save the interaction
    save_user_message(user_message)
    ai_message = save_ai_message(response_text)
    
    logger.info(f"Generated AI response: {ai_message.id}")
    return response_text

def generate_proactive_message(message_type):
    """
    Generate a proactive message based on the current context
    
    Args:
        message_type: Type of proactive message ('start_task', 'mid_task', 'end_task', 'evening_summary')
        
    Returns:
        AI generated message
    """
    context = build_context()
    
    # Create a prompt based on the message type
    prompt = ""
    if message_type == 'start_task':
        if context['current_task']:
            task = context['current_task']
            prompt = f"Generate a short, motivational start-of-task reminder for the user who is about to begin '{task['title']}'. Be encouraging and specific."
        else:
            prompt = "Generate a short, motivational message encouraging the user to start their next task."
    
    elif message_type == 'mid_task':
        if context['current_task'] and context['time_left']:
            task = context['current_task']
            prompt = f"Generate a brief mid-task encouragement for '{task['title']}' with about {context['time_left']} remaining. Acknowledge progress and encourage focus."
        else:
            prompt = "Generate a brief message encouraging the user to stay focused on their current task."
    
    elif message_type == 'end_task':
        if context['current_task'] and context['next_task']:
            current = context['current_task']
            next_task = context['next_task']
            prompt = f"Generate a brief end-of-task transition message congratulating the user for completing '{current['title']}' and preparing them for '{next_task['title']}'."
        else:
            prompt = "Generate a brief message congratulating the user for completing their task and encouraging them to take a short break before continuing."
    
    elif message_type == 'evening_summary':
        stats = context['progress_stats']
        completed = stats.get('completed_tasks', 0)
        total = stats.get('total_tasks', 0)
        completion_rate = stats.get('task_completion_rate', 0)
        
        prompt = f"Generate an evening summary for the user who completed {completed} out of {total} tasks today ({completion_rate}% completion rate). Be supportive and forward-looking."
    
    # Create messages for the API call
    messages = [
        {"role": "system", "content": MENTORA_PERSONA},
        {"role": "user", "content": prompt}
    ]
    
    # Call the API
    response_text = call_deepseek_api(messages)
    
    # Save the interaction (as AI-initiated)
    ai_message = save_ai_message(response_text, is_proactive=True)
    
    logger.info(f"Generated proactive message ({message_type}): {ai_message.id}")
    return response_text

def get_all_messages(limit=100, newest_first=True):
    """
    Get all AI messages from the database
    
    Args:
        limit: Maximum number of messages to return
        newest_first: Order by newest first if True
        
    Returns:
        List of AIMessage objects
    """
    query = AIMessage.query
    
    if newest_first:
        query = query.order_by(AIMessage.timestamp.desc())
    else:
        query = query.order_by(AIMessage.timestamp)
    
    return query.limit(limit).all()

def save_user_message(message_text):
    """
    Save a user message to the database
    
    Args:
        message_text: The message text
        
    Returns:
        Newly created AIMessage object
    """
    message = AIMessage(
        is_from_user=True,
        message=message_text,
        timestamp=datetime.utcnow()
    )
    
    db.session.add(message)
    db.session.commit()
    
    return message

def save_ai_message(message_text, response_to=None, is_proactive=False):
    """
    Save an AI message to the database
    
    Args:
        message_text: The message text
        response_to: ID of the user message this is responding to
        is_proactive: Whether this is a proactive message
        
    Returns:
        Newly created AIMessage object
    """
    message = AIMessage(
        is_from_user=False,
        message=message_text,
        response_to=response_to,
        timestamp=datetime.utcnow()
    )
    
    db.session.add(message)
    db.session.commit()
    
    return message

def record_feedback(message_id, is_helpful):
    """
    Record feedback for an AI message
    
    Args:
        message_id: ID of the message
        is_helpful: Whether the message was helpful
        
    Returns:
        True if successful, False if message not found
    """
    message = AIMessage.query.get(message_id)
    
    if not message:
        logger.warning(f"Attempted to record feedback for non-existent message with ID: {message_id}")
        return False
    
    # In a real implementation, we would update a feedback field and use this data
    # to adjust the AI's responses over time
    logger.info(f"Recorded feedback for message {message_id}: {'helpful' if is_helpful else 'not helpful'}")
    
    return True

def should_send_proactive_message(message_type):
    """
    Determine if a proactive message should be sent based on current context
    
    Args:
        message_type: Type of proactive message
        
    Returns:
        True if a message should be sent, False otherwise
    """
    # Get user preferences
    user_prefs = UserPreference.query.first()
    if user_prefs and user_prefs.do_not_disturb:
        return False
    
    context = build_context()
    now = datetime.utcnow()
    
    # Check the last message time to avoid sending too many messages
    last_message = AIMessage.query.order_by(AIMessage.timestamp.desc()).first()
    if last_message and (now - last_message.timestamp).total_seconds() < 300:  # 5 minutes
        return False
    
    if message_type == 'evening_summary':
        # Check if it's evening (between 6pm and 9pm)
        hour = now.hour
        if 18 <= hour <= 21:
            # Check if we've already sent an evening summary today
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            evening_start = now.replace(hour=18, minute=0, second=0, microsecond=0)
            
            # Look for evening summaries today
            recent_summary = AIMessage.query.filter(
                AIMessage.timestamp >= evening_start,
                AIMessage.is_from_user == False,
                AIMessage.message.like('%today you completed%')
            ).first()
            
            return recent_summary is None
    
    elif message_type == 'start_task':
        # Send if there's a current task that just started (within 5 minutes)
        if context['current_task']:
            task = context['current_task']
            start_time = task['start_time']
            start_hour, start_minute = map(int, start_time.split(':'))
            task_start = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
            
            return (now - task_start).total_seconds() <= 300
    
    elif message_type == 'mid_task':
        # Send if we're in the middle of a task
        if context['current_task'] and context['time_left']:
            time_left_minutes = int(context['time_left'].split()[0])
            total_minutes = 0
            
            # Calculate total task duration
            task = context['current_task']
            start_hour, start_minute = map(int, task['start_time'].split(':'))
            end_hour, end_minute = map(int, task['end_time'].split(':'))
            total_minutes = (end_hour - start_hour) * 60 + (end_minute - start_minute)
            
            # Send if we're approximately halfway through
            return abs(time_left_minutes - (total_minutes / 2)) < 5
    
    elif message_type == 'end_task':
        # Send if a task is about to end (within 5 minutes)
        if context['current_task']:
            task = context['current_task']
            end_time = task['end_time']
            end_hour, end_minute = map(int, end_time.split(':'))
            task_end = now.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
            
            return 0 < (task_end - now).total_seconds() <= 300
    
    return False