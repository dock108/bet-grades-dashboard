"""
Task scheduler for periodic bet updates and grade calculations.
Uses APScheduler to manage recurring tasks.
"""
import logging
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.models.bet_models import BetGrade

logger = logging.getLogger(__name__)

def update_bets_and_grades():
    """
    Update bets and recalculate grades.
    This task runs every 5 minutes.
    """
    try:
        logger.info("Starting scheduled bet update and grade calculation")
        
        # Call the /bets/update endpoint
        response = requests.post('http://localhost:5000/bets/update')
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Successfully updated {result.get('updated_count', 0)} bets")
            
            # Force update of distribution stats
            BetGrade._get_distribution_stats(force_update=True)
            
            # Log any errors that occurred during update
            if result.get('errors'):
                for error in result['errors']:
                    logger.error(f"Error updating bet {error.get('bet_id')}: {error.get('error')}")
        else:
            logger.error(f"Failed to update bets. Status code: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error in scheduled bet update: {str(e)}")

def init_scheduler():
    """Initialize and start the task scheduler."""
    try:
        scheduler = BackgroundScheduler()
        
        # Add bet update job - runs every 5 minutes
        scheduler.add_job(
            func=update_bets_and_grades,
            trigger=IntervalTrigger(minutes=5),
            id='update_bets_and_grades',
            name='Update bets and recalculate grades',
            replace_existing=True
        )
        
        # Start the scheduler
        scheduler.start()
        logger.info("Task scheduler started successfully")
        
        return scheduler
    except Exception as e:
        logger.error(f"Error initializing scheduler: {str(e)}")
        return None 