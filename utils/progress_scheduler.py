"""
Progress Scheduler for Mentora application
Sets up scheduled tasks for progress tracking
"""
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from utils.progress_engine import log_daily_progress, generate_weekly_report
from services.mentor_ai_service import save_ai_message

logger = logging.getLogger(__name__)

def initialize_progress_tracking(scheduler):
    """
    Initialize the progress tracking scheduler
    
    Args:
        scheduler: The BackgroundScheduler instance
    """
    # Schedule daily logging at 11:59 PM
    scheduler.add_job(
        log_daily_progress,
        CronTrigger(hour=23, minute=59),
        id="daily_progress_logging",
        replace_existing=True
    )
    
    # Schedule weekly report generation on Sunday at 8:00 PM
    scheduler.add_job(
        generate_and_save_weekly_report,
        CronTrigger(day_of_week='sun', hour=20, minute=0),
        id="weekly_report_generation",
        replace_existing=True
    )
    
    logger.info("Progress tracking scheduler initialized")

def generate_and_save_weekly_report():
    """
    Generate weekly report and save it as an AI message
    """
    report = generate_weekly_report()
    
    # Save the report as an AI message
    save_ai_message(report, is_proactive=True)
    
    logger.info("Weekly report generated and saved")