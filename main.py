#!/usr/bin/env python3
"""
Main entry point for the Web3 Contract Scheduler.

This application allows for declarative creation of jobs that call smart contract
methods on a schedule using the Python Schedule library.
"""

import argparse
import sys
import logging
from typing import List, Optional

from scheduler import register_job, run_scheduler
from scheduler.utils import setup_logging
from config import JOBS


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Web3 Contract Scheduler - Run blockchain contract calls on a schedule'
    )
    
    parser.add_argument(
        '--run-once',
        action='store_true',
        help='Run pending jobs once and exit'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=1,
        help='Time interval in seconds between scheduler runs (default: 1)'
    )
    
    parser.add_argument(
        '--job',
        type=str,
        action='append',
        help='Specific job name(s) to run (can be specified multiple times)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate jobs without executing transactions'
    )
    
    return parser.parse_args()


def filter_jobs(job_names: Optional[List[str]]) -> List:
    """
    Filter jobs by name if job names are provided.
    
    Args:
        job_names: List of job names to filter by, or None to include all jobs
        
    Returns:
        Filtered list of jobs
    """
    if not job_names:
        return JOBS
        
    filtered_jobs = []
    for job in JOBS:
        if job.name in job_names:
            filtered_jobs.append(job)
            
    return filtered_jobs


def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code
    """
    # Set up logging
    logger = setup_logging("main")
    
    # Parse command line arguments
    args = parse_args()
    
    try:
        # Filter jobs if specific ones are requested
        jobs_to_run = filter_jobs(args.job)
        
        if not jobs_to_run:
            logger.error("No jobs to run")
            return 1
            
        # If dry run, just print the jobs that would be executed
        if args.dry_run:
            logger.info("Dry run mode - would schedule the following jobs:")
            for job in jobs_to_run:
                status = "ENABLED" if job.enabled else "DISABLED"
                logger.info(f"  - {job.name} ({status}): {job.schedule}")
            return 0
        
        # Register jobs with the scheduler
        for job in jobs_to_run:
            register_job(job)
        
        # Run the scheduler
        run_scheduler(run_once=args.run_once, interval=args.interval)
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130
    except Exception as e:
        logger.exception(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 