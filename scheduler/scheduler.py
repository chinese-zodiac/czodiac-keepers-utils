"""
Scheduler for blockchain contract method calls.
"""

import time
import signal
import logging
import schedule
from typing import Dict, List, Optional, Callable, Any, Tuple

from .models import ContractJob, ContractJobMulti, AnyJob
from .utils import execute_any_job, setup_logging

# Initialize the logger
logger = setup_logging(__name__)

# Store for registered jobs
_jobs: Dict[str, AnyJob] = {}


def register_job(job: AnyJob) -> None:
    """
    Register a contract job for scheduling.
    
    Args:
        job: Contract job configuration (ContractJob, ContractJobCustomArgs, or ContractJobMulti)
    """
    if job.name in _jobs:
        logger.warning(f"Job '{job.name}' already registered, overwriting")
    
    _jobs[job.name] = job
    logger.info(f"Registered job: {job.name}")


def register_jobs(jobs: List[AnyJob]) -> None:
    """
    Register multiple contract jobs at once.
    
    Args:
        jobs: List of contract job configurations
    """
    for job in jobs:
        register_job(job)


def _job_executor(job_name: str) -> Callable[[], None]:
    """
    Create a job executor function for the given job name.
    
    Args:
        job_name: Name of the job to execute
        
    Returns:
        Function that executes the job when called
    """
    def execute() -> None:
        job = _jobs.get(job_name)
        if not job:
            logger.error(f"Job '{job_name}' not found")
            return
            
        logger.info(f"Executing job: {job_name}")
        success, result, error = execute_any_job(job)
        
        if success:
            logger.info(f"Job '{job_name}' completed successfully. Result: {result}")
        else:
            logger.error(f"Job '{job_name}' failed: {error}")
    
    return execute


def _schedule_job(job: AnyJob) -> None:
    """
    Schedule a job according to its schedule expression.
    
    Args:
        job: Job configuration (ContractJob, ContractJobCustomArgs, or ContractJobMulti)
    """
    # Skip jobs without a schedule (they are part of multi-jobs)
    if not job.schedule:
        logger.debug(f"Skipping scheduling for job '{job.name}' - no schedule defined (likely part of multi-job)")
        return
    
    # Create the job executor
    executor = _job_executor(job.name)
    
    # Parse the schedule expression
    schedule_parts = job.schedule.strip().split()
    
    if len(schedule_parts) < 2:
        logger.error(f"Invalid schedule format for job '{job.name}': {job.schedule}")
        return
    
    # Handle different schedule formats
    if schedule_parts[0].lower() == "every":
        if len(schedule_parts) >= 3 and schedule_parts[2].lower() == "at":
            # Format: "every day at HH:MM"
            if schedule_parts[1].lower() == "day":
                time_spec = " ".join(schedule_parts[3:])
                schedule.every().day.at(time_spec).do(executor)
                logger.info(f"Scheduled job '{job.name}' to run daily at {time_spec}")
            # Format: "every monday at HH:MM"
            elif schedule_parts[1].lower() in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
                weekday = schedule_parts[1].lower()
                time_spec = " ".join(schedule_parts[3:])
                getattr(schedule.every(), weekday).at(time_spec).do(executor)
                logger.info(f"Scheduled job '{job.name}' to run every {weekday} at {time_spec}")
        else:
            # Check for "to" syntax for random intervals
            # Format: "every X to Y minutes/hours/seconds"
            if len(schedule_parts) >= 4 and schedule_parts[2].lower() == "to":
                try:
                    min_interval = int(schedule_parts[1])
                    max_interval = int(schedule_parts[3])
                    unit = schedule_parts[4].lower() if len(schedule_parts) > 4 else ""
                    
                    if unit in ["second", "seconds"]:
                        schedule.every(min_interval).to(max_interval).seconds.do(executor)
                        logger.info(f"Scheduled job '{job.name}' to run every {min_interval} to {max_interval} {unit}")
                    elif unit in ["minute", "minutes"]:
                        schedule.every(min_interval).to(max_interval).minutes.do(executor)
                        logger.info(f"Scheduled job '{job.name}' to run every {min_interval} to {max_interval} {unit}")
                    elif unit in ["hour", "hours"]:
                        schedule.every(min_interval).to(max_interval).hours.do(executor)
                        logger.info(f"Scheduled job '{job.name}' to run every {min_interval} to {max_interval} {unit}")
                    else:
                        logger.error(f"Unsupported time unit for job '{job.name}': {unit}")
                        return
                except (ValueError, IndexError):
                    logger.error(f"Invalid random interval format for job '{job.name}': {job.schedule}")
            else:
                # Format: "every N minutes/hours"
                try:
                    interval = int(schedule_parts[1])
                    unit = schedule_parts[2].lower()
                    if unit in ["second", "seconds"]:
                        schedule.every(interval).seconds.do(executor)
                    elif unit in ["minute", "minutes"]:
                        schedule.every(interval).minutes.do(executor)
                    elif unit in ["hour", "hours"]:
                        schedule.every(interval).hours.do(executor)
                    else:
                        logger.error(f"Unsupported time unit for job '{job.name}': {unit}")
                        return
                    logger.info(f"Scheduled job '{job.name}' to run every {interval} {unit}")
                except (ValueError, IndexError):
                    logger.error(f"Invalid schedule format for job '{job.name}': {job.schedule}")
    else:
        logger.error(f"Unsupported schedule format for job '{job.name}': {job.schedule}")


def _schedule_all_jobs() -> None:
    """Schedule all registered jobs."""
    for job_name, job in _jobs.items():
        if job.enabled:
            _schedule_job(job)
        else:
            logger.info(f"Job '{job_name}' is disabled, not scheduling")


def _handle_signals() -> None:
    """Set up signal handlers for graceful shutdown."""
    def handle_exit_signal(signum, frame):
        logger.info("Received exit signal, shutting down...")
        # This will break out of the infinite loop in run_scheduler
        raise KeyboardInterrupt
    
    signal.signal(signal.SIGINT, handle_exit_signal)
    signal.signal(signal.SIGTERM, handle_exit_signal)


def run_scheduler(run_once: bool = False, interval: int = 1) -> None:
    """
    Run the scheduler with the registered jobs.
    
    Args:
        run_once: If True, run all jobs once immediately and exit
        interval: Time interval in seconds between scheduler runs
    """
    if not _jobs:
        logger.warning("No jobs registered")
        return
    
    logger.info("Starting scheduler")
    
    # Schedule all registered jobs
    _schedule_all_jobs()
    
    # Set up signal handlers
    _handle_signals()
    
    try:
        if run_once:
            logger.info("Running all jobs once immediately")
            # Instead of running only pending jobs, directly execute all enabled jobs
            for job_name, job in _jobs.items():
                if job.enabled:
                    executor = _job_executor(job_name)
                    executor()
        else:
            logger.info(f"Scheduler running with {interval}s interval. Press Ctrl+C to exit.")
            while True:
                schedule.run_pending()
                time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped")
    except Exception as e:
        logger.exception(f"Error in scheduler: {str(e)}")
    finally:
        # Clear all scheduled jobs
        schedule.clear()
        logger.info("All jobs cleared") 