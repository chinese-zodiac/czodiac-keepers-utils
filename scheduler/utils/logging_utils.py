"""
Logging utilities for the scheduler application.
"""

import logging
import sys
from typing import Optional

from ..config import LOG_LEVEL, LOG_FORMAT


def setup_logging(name: Optional[str] = None) -> logging.Logger:
    """
    Set up and configure logging.
    
    Args:
        name: Logger name, defaults to root logger if None
        
    Returns:
        Configured logger instance
    """
    # Get the logger
    logger = logging.getLogger(name)
    
    # Clear existing handlers
    logger.handlers = []
    
    # Set the log level
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Create a console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, LOG_LEVEL))
    
    # Set formatter based on configuration
    if LOG_FORMAT.lower() == "json":
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"name": "%(name)s", "message": "%(message)s"}'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    
    # Add the handler to the logger
    logger.addHandler(console_handler)
    
    # Prevent propagation to the root logger
    logger.propagate = False
    
    return logger 