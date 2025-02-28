# integration_item.py

import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Adjust logging level as needed

@dataclass
class IntegrationItem:
    """
    A class representing an integration item.
    
    Attributes:
        id (Optional[str]): Unique identifier for the integration item.
        type (Optional[str]): The type/category of the item (e.g., "contact", "company").
        directory (bool): Flag indicating if the item represents a directory.
        parent_path_or_name (Optional[str]): Name or path of the parent item.
        parent_id (Optional[str]): Unique identifier of the parent item.
        name (Optional[str]): Display name for the item.
        creation_time (Optional[datetime]): Timestamp when the item was created.
        last_modified_time (Optional[datetime]): Timestamp when the item was last modified.
        url (Optional[str]): A URL associated with the item.
        children (Optional[List[str]]): List of child item identifiers.
        mime_type (Optional[str]): MIME type associated with the item (if applicable).
        delta (Optional[str]): Delta value for tracking changes.
        drive_id (Optional[str]): Identifier of the drive or source.
        visibility (Optional[bool]): Flag indicating whether the item is visible.
    """
    id: Optional[str] = None
    type: Optional[str] = None
    directory: bool = False
    parent_path_or_name: Optional[str] = None
    parent_id: Optional[str] = None
    name: Optional[str] = None
    creation_time: Optional[datetime] = None
    last_modified_time: Optional[datetime] = None
    url: Optional[str] = None
    children: Optional[List[str]] = None
    mime_type: Optional[str] = None
    delta: Optional[str] = None
    drive_id: Optional[str] = None
    visibility: Optional[bool] = True

    def __post_init__(self):
        """
        Called immediately after the dataclass __init__ method.
        Logs the creation of the IntegrationItem with key attributes.
        """
        logger.debug("Created IntegrationItem: id=%s, type=%s, name=%s", self.id, self.type, self.name)

    def __str__(self):
        """
        Provides a human-readable string representation of the IntegrationItem.
        """
        return f"IntegrationItem(id={self.id}, type={self.type}, name={self.name})"
