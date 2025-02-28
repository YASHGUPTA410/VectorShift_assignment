# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel
# from typing import Dict, Any, Optional
# from datetime import datetime

# from logger import app_logger

# router = APIRouter()

# class LogEntry(BaseModel):
#     timestamp: str
#     level: str
#     component: str
#     action: str
#     details: Optional[Dict[str, Any]]
#     metadata: Optional[Dict[str, Any]]

# @router.post("/logs")
# async def store_log(log_entry: LogEntry):
#     """Store logs from frontend."""
#     try:
#         # Convert ISO timestamp to datetime
#         timestamp = datetime.fromisoformat(log_entry.timestamp.replace('Z', '+00:00'))
        
#         # Format the log message
#         log_message = (
#             f"[Frontend] {log_entry.component} - {log_entry.action}"
#             f" - Details: {log_entry.details or {}}"
#             f" - Metadata: {log_entry.metadata or {}}"
#         )

#         # Log using appropriate level
#         if log_entry.level == "ERROR":
#             app_logger.error(log_message)
#         elif log_entry.level == "WARN":
#             app_logger.warning(log_message)
#         elif log_entry.level == "DEBUG":
#             app_logger.debug(log_message)
#         else:
#             app_logger.info(log_message)

#         return {"status": "success", "message": "Log stored successfully"}
#     except Exception as e:
#         app_logger.error(f"Error storing frontend log: {str(e)}")
#         raise HTTPException(status_code=500, detail="Failed to store log")


from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

from logger import app_logger

router = APIRouter()

class LogEntry(BaseModel):
    """
    Pydantic model representing a log entry received from the frontend.
    
    Attributes:
        timestamp (str): ISO formatted timestamp of the log event.
        level (str): Log level (e.g., "ERROR", "WARN", "DEBUG", or others).
        component (str): Name of the component that generated the log.
        action (str): A description of the action performed.
        details (Optional[Dict[str, Any]]): Additional details regarding the event.
        metadata (Optional[Dict[str, Any]]): Any supplementary metadata.
    """
    timestamp: str
    level: str
    component: str
    action: str
    details: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

@router.post("/logs")
async def store_log(log_entry: LogEntry):
    """
    Endpoint to store logs from the frontend.
    
    The endpoint receives a LogEntry payload, converts the timestamp for validation,
    formats a log message including details and metadata, and logs it using the
    application logger at the appropriate level.
    
    Returns:
        A JSON response indicating successful log storage.
    
    Raises:
        HTTPException: If an error occurs while processing the log.
    """
    try:
        # Convert ISO timestamp to datetime (for validation and display)
        log_timestamp = datetime.fromisoformat(log_entry.timestamp.replace('Z', '+00:00'))
        
        # Format the log message including the timestamp, component, action, details, and metadata
        log_message = (
            f"[Frontend] {log_entry.component} - {log_entry.action} "
            f"(Timestamp: {log_timestamp.isoformat()}) - "
            f"Details: {log_entry.details or {}} - Metadata: {log_entry.metadata or {}}"
        )

        # Map log level strings to the corresponding logger methods.
        # Defaults to app_logger.info if the level is not recognized.
        log_methods = {
            "ERROR": app_logger.error,
            "WARN": app_logger.warning,
            "DEBUG": app_logger.debug
        }
        log_func = log_methods.get(log_entry.level.upper(), app_logger.info)
        
        # Log the formatted message
        log_func(log_message)

        return {"status": "success", "message": "Log stored successfully"}
    except Exception as e:
        # Log the error with stack trace and raise an HTTPException
        error_message = f"Error storing frontend log: {str(e)}"
        app_logger.error(error_message, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to store log")
