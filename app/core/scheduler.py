from apscheduler.schedulers.background import BackgroundScheduler
from app.core.bot import bot_instance
import datetime

scheduler = BackgroundScheduler()

def scheduled_scan():
    if bot_instance.is_running:
        bot_instance._run_scan()

# Run the scan every 2 hours
scheduler.add_job(scheduled_scan, 'interval', hours=2)

def start_scheduler():
    scheduler.start()
