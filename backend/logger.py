# logger.py

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional

# Ensure that the logs directories exist
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
INTEGRATIONS_LOGS_DIR = os.path.join(LOGS_DIR, "integrations")
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(INTEGRATIONS_LOGS_DIR, exist_ok=True)

# Define the log message and date format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Configure a logger with console and optional file handlers.
    
    Args:
        name (str): Name of the logger.
        log_file (Optional[str]): Log file name (relative to LOGS_DIR) for file output.
        level (int): Logging level threshold.
        max_bytes (int): Maximum size in bytes for each log file before rotation.
        backup_count (int): Number of backup files to retain.
    
    Returns:
        logging.Logger: The configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create a formatter for log messages
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)

    # Set up console handler for real-time logging
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # If a log file is provided, set up a rotating file handler
    if log_file:
        file_path = os.path.join(LOGS_DIR, log_file)
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

# Create application-wide loggers
app_logger = setup_logger("app", "app.log")
error_logger = setup_logger("error", "error.log", level=logging.ERROR)
redis_logger = setup_logger("redis", "redis.log")

# Create integration-specific loggers (log files are stored under logs/integrations)
hubspot_logger = setup_logger("hubspot", os.path.join("integrations", "hubspot.log"))
notion_logger = setup_logger("notion", os.path.join("integrations", "notion.log"))
airtable_logger = setup_logger("airtable", os.path.join("integrations", "airtable.log"))

def log_request(logger: logging.Logger, method: str, path: str, status_code: int, duration: float) -> None:
    """
    Log details of an HTTP request.
    
    Args:
        logger (logging.Logger): Logger instance to use.
        method (str): HTTP method (e.g., GET, POST).
        path (str): Request URL or endpoint.
        status_code (int): HTTP status code returned.
        duration (float): Request processing time in seconds.
    """
    logger.info(
        "Request: %s %s - Status: %d - Duration: %.2fms",
        method,
        path,
        status_code,
        duration * 1000  # convert seconds to milliseconds
    )

def log_error(logger: logging.Logger, error: Exception, context: Optional[dict] = None) -> None:
    """
    Log an error with optional additional context.
    
    Args:
        logger (logging.Logger): Logger instance to use.
        error (Exception): The error/exception instance.
        context (Optional[dict]): Additional context information.
    """
    error_msg = f"Error: {type(error).__name__} - {str(error)}"
    if context:
        error_msg += f" - Context: {context}"
    logger.error(error_msg, exc_info=True)

def log_integration_event(
    logger: logging.Logger,
    event_type: str,
    integration: str,
    user_id: str,
    org_id: str,
    details: Optional[dict] = None
) -> None:
    """
    Log an integration-related event.
    
    Args:
        logger (logging.Logger): Logger instance to use.
        event_type (str): The type of event (e.g., "AUTHORIZE_START").
        integration (str): Name of the integration.
        user_id (str): User identifier.
        org_id (str): Organization identifier.
        details (Optional[dict]): Additional details about the event.
    """
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "integration": integration,
        "user_id": user_id,
        "org_id": org_id
    }
    if details:
        log_data["details"] = details
    logger.info("Integration Event: %s", log_data)
