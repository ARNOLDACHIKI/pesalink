from apscheduler.schedulers.background import BackgroundScheduler

def start_validation_scheduler(validation_func, interval_hours=1):
    """
    Start a background scheduler that runs the given validation_func every interval_hours.
    Returns the scheduler instance.
    """
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(validation_func, 'interval', hours=interval_hours)
    scheduler.start()
    return scheduler
