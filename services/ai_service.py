"""
AI Service for the Mentora application
Handles interaction with AI mentor functionality
"""
import logging
import random
from datetime import datetime
from app import db
from models import AIMessage, Task, Goal

logger = logging.getLogger(__name__)

# Placeholder motivational messages for the AI mentor
MOTIVATIONAL_MESSAGES = [
    "Remember that consistency beats perfection. Keep making progress on your tasks, even if it's just small steps.",
    "It's normal to feel overwhelmed sometimes. Break down your big goals into smaller, manageable tasks.",
    "Your effort today is an investment in your future self. Stay focused on your long-term vision.",
    "Learning is a journey, not a destination. Embrace the process and be patient with yourself.",
    "Every expert was once a beginner. Keep practicing and improving your skills.",
    "Celebrate your progress, no matter how small. Each completed task brings you closer to your goals.",
    "Balance is key - make sure to take breaks and recharge. It actually improves your productivity.",
    "Challenges are opportunities to grow. When you face difficulties, ask yourself: what can I learn from this?",
    "Your goals matter because YOU matter. Stay committed to your personal growth.",
    "Focus on what you can control, and let go of what you can't. This mindset will reduce stress and increase effectiveness."
]

# Placeholder educational insights
EDUCATIONAL_INSIGHTS = [
    "Spaced repetition is one of the most effective study techniques. Review material at increasing intervals.",
    "Active recall (testing yourself) is more effective than passive re-reading for learning.",
    "The Pomodoro Technique (25 min work, 5 min break) can help maintain focus and prevent burnout.",
    "Your brain consolidates memories during sleep. Prioritize good sleep for better learning outcomes.",
    "Interleaving (mixing different subjects) during study sessions improves long-term retention.",
    "Teaching concepts to others is one of the best ways to solidify your own understanding.",
    "Regular physical exercise improves cognitive function and learning ability.",
    "A growth mindset—believing abilities can be developed through dedication and hard work—boosts achievement.",
    "Creating mental associations and visualizations helps with memorization and understanding complex concepts.",
    "Learning through multiple modalities (reading, listening, discussing) strengthens neural connections."
]

def get_all_messages(limit=100, newest_first=True):
    """
    Get chat history
    
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
        query = query.order_by(AIMessage.timestamp.asc())
    
    return query.limit(limit).all()

def get_message_by_id(message_id):
    """
    Get a message by ID
    
    Args:
        message_id: The ID of the message to retrieve
    
    Returns:
        AIMessage object or None if not found
    """
    return AIMessage.query.get(message_id)

def create_user_message(message_text):
    """
    Create a new message from the user
    
    Args:
        message_text: The message text
    
    Returns:
        Newly created AIMessage object
    """
    message = AIMessage(
        is_from_user=True,
        message=message_text
    )
    
    db.session.add(message)
    db.session.commit()
    
    logger.info(f"Created new user message: {message.id}")
    return message

def generate_ai_response(user_message_id):
    """
    Generate an AI response to a user message
    
    Args:
        user_message_id: ID of the user message to respond to
    
    Returns:
        Newly created AIMessage object with the AI response
    """
    user_message = get_message_by_id(user_message_id)
    
    if not user_message:
        logger.error(f"Cannot generate response: Message {user_message_id} not found")
        return None
    
    # In a real implementation, this would call an LLM API
    # For now, we'll use a simple rule-based approach
    
    message_text = user_message.message.lower()
    response_text = ""
    
    # Check for specific question types
    if "next focus" in message_text or "what should i do" in message_text or "next task" in message_text:
        response_text = generate_next_focus_response()
    elif "why am i behind" in message_text or "struggling with" in message_text:
        response_text = generate_challenge_response(message_text)
    elif "motivate me" in message_text or "motivation" in message_text:
        response_text = generate_motivation_response(message_text)
    elif "progress" in message_text or "how am i doing" in message_text:
        response_text = generate_progress_response()
    elif "hello" in message_text or "hi" in message_text or "hey" in message_text:
        response_text = "Hello! I'm Mentora, your AI mentor. How can I help with your studies, goals, or productivity today?"
    elif "thank" in message_text:
        response_text = "You're welcome! I'm here to support your learning and growth. Is there anything else you need help with?"
    else:
        # Default to a motivational or educational response
        if random.random() < 0.5:
            response_text = random.choice(MOTIVATIONAL_MESSAGES)
        else:
            response_text = random.choice(EDUCATIONAL_INSIGHTS)
    
    # Create the AI response
    ai_message = AIMessage(
        is_from_user=False,
        message=response_text,
        response_to=user_message_id
    )
    
    db.session.add(ai_message)
    db.session.commit()
    
    logger.info(f"Generated AI response: {ai_message.id}")
    return ai_message

def generate_next_focus_response():
    """Generate a response about what to focus on next"""
    # Get the next task from priority engine
    from utils.priority_engine import suggest_next_task
    next_task = suggest_next_task()
    
    if next_task:
        # Get the goal for context
        goal = Goal.query.get(next_task.goal_id)
        goal_context = f" as part of your {goal.title} goal" if goal else ""
        
        # Check if task has a deadline
        deadline_text = ""
        if next_task.deadline:
            now = datetime.utcnow()
            days_until = (next_task.deadline - now).days
            hours_until = int((next_task.deadline - now).total_seconds() / 3600)
            
            if days_until > 0:
                deadline_text = f" It's due in {days_until} days."
            elif hours_until > 0:
                deadline_text = f" It's due in {hours_until} hours!"
            else:
                deadline_text = " It's due very soon!"
        
        # Generate response
        priority_text = "high-priority " if next_task.priority == 1 else ""
        return f"I recommend focusing on '{next_task.title}'{goal_context}. This is a {priority_text}task{deadline_text} {next_task.description or ''}"
    else:
        # No tasks found
        return "You don't have any pending tasks at the moment. This would be a good time to plan your next goals or take a well-deserved break!"

def generate_challenge_response(message_text):
    """Generate a response for when the user is struggling"""
    # Try to identify the subject they're struggling with
    subjects = ["math", "science", "physics", "chemistry", "biology", "history", 
                "english", "literature", "programming", "coding", "web development",
                "design", "art", "music", "language", "economics", "business"]
    
    found_subject = None
    for subject in subjects:
        if subject in message_text:
            found_subject = subject
            break
    
    if found_subject:
        return f"It's completely normal to face challenges with {found_subject}. The most effective approach is to break it down into smaller concepts and master them one by one. Have you tried finding different learning resources that might explain {found_subject} in a way that clicks with your learning style? Sometimes a different perspective makes all the difference."
    else:
        return "Everyone faces obstacles in their learning journey. When you're struggling, try breaking the subject into smaller pieces, seek out different explanations, and give yourself permission to take breaks. Your brain often continues processing information even when you're not actively studying. What specific aspect are you finding most challenging?"

def generate_motivation_response(message_text):
    """Generate a motivational response"""
    # Check if a specific subject is mentioned
    subjects = ["exam", "test", "quiz", "math", "science", "physics", "chemistry", 
                "biology", "history", "english", "literature", "programming", "coding", 
                "web development", "design", "art", "music", "language", "economics"]
    
    found_subject = None
    for subject in subjects:
        if subject in message_text:
            found_subject = subject
            break
    
    if found_subject:
        return f"You've got this! Remember why you started learning {found_subject} in the first place. Think about how each study session is building your knowledge and bringing you closer to mastery. Your hard work now will open doors in the future. I believe in your ability to excel in {found_subject}!"
    else:
        return "You have everything you need to succeed already within you. Your dedication to improving yourself shows remarkable character. Remember that every expert started as a beginner, and every step forward—no matter how small—is progress. Trust in your ability to grow and overcome challenges. You've got this!"

def generate_progress_response():
    """Generate a response about the user's progress"""
    # Get progress statistics
    from services.progress_service import get_overall_progress, get_user_productivity_score
    
    progress = get_overall_progress()
    productivity = get_user_productivity_score()
    
    if progress['total_tasks'] == 0:
        return "You haven't created any tasks yet. Let's start setting some goals and breaking them down into manageable tasks to track your progress!"
    
    completion_rate = progress['task_completion_rate']
    productivity_score = productivity['productivity_score']
    
    if completion_rate > 80:
        progress_quality = "excellent"
    elif completion_rate > 60:
        progress_quality = "good"
    elif completion_rate > 40:
        progress_quality = "steady"
    else:
        progress_quality = "building"
    
    response = f"You're making {progress_quality} progress! You've completed {progress['completed_tasks']} out of {progress['total_tasks']} tasks ({completion_rate}% completion rate)."
    
    if progress['overdue_tasks'] > 0:
        response += f" You have {progress['overdue_tasks']} overdue tasks that might need attention."
    
    response += f" Your current productivity score is {productivity_score}/100."
    
    if productivity_score > 80:
        response += " That's excellent! Your consistency and timeliness are really paying off."
    elif productivity_score > 60:
        response += " That's a solid score. Keep up the good work and look for small ways to improve your consistency."
    else:
        response += " There's room for improvement, but remember that building good habits takes time. Focus on completing one task at a time."
    
    return response

def get_daily_advice():
    """
    Get personalized daily advice
    
    Returns:
        Dictionary with advice and insights
    """
    # Get progress and task data
    from services.progress_service import get_overall_progress, get_recent_progress
    from utils.priority_engine import get_daily_priorities
    
    progress = get_overall_progress()
    recent = get_recent_progress(days=3)
    daily_tasks = get_daily_priorities(limit=5)
    
    # Determine user's current strengths and areas for improvement
    strengths = []
    improvements = []
    
    # Check completion rate
    if progress['task_completion_rate'] > 70:
        strengths.append("task completion")
    elif progress['task_completion_rate'] < 40:
        improvements.append("task completion rate")
    
    # Check overdue tasks
    if progress['overdue_tasks'] == 0:
        strengths.append("meeting deadlines")
    elif progress['overdue_tasks'] > 3:
        improvements.append("timeliness with deadlines")
    
    # Check recent activity
    if recent['completed_tasks_count'] > 5:
        strengths.append("recent productivity")
    elif recent['completed_tasks_count'] < 2:
        improvements.append("consistent daily progress")
    
    # Generate advice
    advice = random.choice(MOTIVATIONAL_MESSAGES)
    
    if strengths:
        advice += f"\n\nYour strengths include {', '.join(strengths)}. Keep building on these strong areas!"
    
    if improvements:
        advice += f"\n\nYou might want to focus on improving your {', '.join(improvements)}."
    
    # Add task suggestions
    if daily_tasks:
        advice += "\n\nHere are your top priorities for today:"
        for i, task in enumerate(daily_tasks[:3], 1):
            advice += f"\n{i}. {task.title}"
    
    # Add an educational insight
    advice += f"\n\n{random.choice(EDUCATIONAL_INSIGHTS)}"
    
    return {
        'advice': advice,
        'generated_at': datetime.utcnow().isoformat(),
        'progress_rate': progress['task_completion_rate'],
        'strengths': strengths,
        'improvement_areas': improvements,
        'has_daily_tasks': len(daily_tasks) > 0
    }