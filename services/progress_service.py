"""
Progress Service for Mentora application
Provides high-level interfaces for progress tracking, analytics, and insights
"""
import logging
from datetime import datetime, timedelta
from utils.progress_engine import get_daily_metrics, get_weekly_metrics

logger = logging.getLogger(__name__)

def get_overall_progress():
    """
    Get overall progress metrics across all goals and tasks
    
    Returns:
        Dictionary with overall progress metrics
    """
    # Get progress for last 30 days
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=29)
    
    # Get weekly metrics
    weekly_metrics = get_weekly_metrics(end_date, days=30)
    
    # Extract relevant metrics
    overall = {
        "total_tasks": weekly_metrics["total_tasks"],
        "completed_tasks": weekly_metrics["completed_tasks"],
        "completion_rate": weekly_metrics["completion_rate"],
        "completed_goals": weekly_metrics["completed_goals"],
        "total_time_spent": weekly_metrics["total_time_spent"],
        "streak": weekly_metrics["streak"],
        "time_by_category": weekly_metrics["time_by_category"]
    }
    
    return overall

def get_recent_progress(days=7):
    """
    Get daily progress metrics for recent days
    
    Args:
        days: Number of days to include
    
    Returns:
        List of daily metrics
    """
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days-1)
    
    daily_metrics = []
    current_date = start_date
    
    while current_date <= end_date:
        metrics = get_daily_metrics(current_date)
        
        # Format the date for better readability
        metrics["formatted_date"] = current_date.strftime("%a, %b %d")
        
        daily_metrics.append(metrics)
        current_date += timedelta(days=1)
    
    return {
        "days": days,
        "metrics": daily_metrics
    }

def get_progress_insights():
    """
    Get intelligent insights about the user's progress patterns
    
    Returns:
        Dictionary with progress insights
    """
    # Get recent metrics
    recent = get_recent_progress(14)  # Get the last 2 weeks
    
    # Initialize insights
    insights = {
        "patterns": [],
        "strengths": [],
        "areas_for_improvement": []
    }
    
    # Analyze completion rates
    completion_rates = [day["completion_rate"] for day in recent["metrics"]]
    avg_completion = sum(completion_rates) / len(completion_rates)
    
    # Identify patterns
    if all(rate > 70 for rate in completion_rates[-7:]):
        insights["patterns"].append("Consistently high completion rate in the past week")
    
    if all(rate < 50 for rate in completion_rates[-3:]):
        insights["patterns"].append("Several days of low task completion")
    
    # Check for weekend patterns
    weekend_rates = []
    for i, day in enumerate(recent["metrics"]):
        date = datetime.strptime(day["date"], "%Y-%m-%d")
        if date.weekday() >= 5:  # 5 and 6 are Saturday and Sunday
            weekend_rates.append(day["completion_rate"])
    
    if weekend_rates and sum(weekend_rates) / len(weekend_rates) < 30:
        insights["patterns"].append("Low productivity on weekends")
    
    # Identify strengths
    if avg_completion > 70:
        insights["strengths"].append("Strong overall task completion rate")
    
    streak = recent["metrics"][-1].get("streak", 0)
    if streak >= 5:
        insights["strengths"].append(f"Maintaining a {streak}-day streak of activity")
    
    # Identify areas for improvement
    if avg_completion < 50:
        insights["areas_for_improvement"].append("Overall task completion rate is below 50%")
    
    overdue = recent["metrics"][-1].get("overdue_tasks", 0)
    if overdue > 3:
        insights["areas_for_improvement"].append(f"Currently have {overdue} overdue tasks")
    
    # Check for most productive categories
    time_by_category = {}
    for day in recent["metrics"]:
        for category, time in day.get("time_by_category", {}).items():
            if category in time_by_category:
                time_by_category[category] += time
            else:
                time_by_category[category] = time
    
    if time_by_category:
        most_time_category = max(time_by_category.items(), key=lambda x: x[1])
        insights["strengths"].append(f"Most time invested in: {most_time_category[0]}")
        
        # Check for neglected categories
        neglected = [cat for cat, time in time_by_category.items() if time < 1]
        if neglected:
            neglected_str = ", ".join(neglected)
            insights["areas_for_improvement"].append(f"Limited time spent on: {neglected_str}")
    
    return insights