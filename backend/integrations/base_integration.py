# base_integration.py

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import time

# Import helper functions for state generation, token exchange, and credential storage.
from utils import (
    generate_and_store_state,
    validate_state,
    exchange_code_for_token,
    store_credentials,
    get_credentials
)
# Import loggers and logging helper functions for integration events and errors.
from logger import (
    log_integration_event,
    log_error,
    hubspot_logger,
    notion_logger,
    airtable_logger
)
from config import CLIENT_CONFIGS, HUBSPOT_AUTH_URL
from integrations.integration_item import IntegrationItem

class BaseIntegration(ABC):
    def __init__(self, integration_name: str):
        """
        BaseIntegration constructor.
        
        Initializes the integration by loading its configuration and setting up
        the appropriate logger. Raises ValueError if required configuration or logger
        is missing.
        """
        self.integration_name = integration_name
        self.config = CLIENT_CONFIGS.get(integration_name)
        if not self.config:
            raise ValueError(f"No configuration found for {integration_name}")
        
        # Choose the logger based on the integration name.
        self.logger = {
            "hubspot": hubspot_logger,
            "notion": notion_logger,
            "airtable": airtable_logger
        }.get(integration_name)
        if not self.logger:
            raise ValueError(f"No logger configured for {integration_name}")

    async def authorize(self, user_id: str, org_id: str) -> str:
        """
        Initiates the OAuth authorization flow.
        
        Generates an encoded state parameter, constructs the authorization URL,
        logs the event with duration, and returns the URL for redirection.
        """
        try:
            start_time = time.time()
            # Generate and store state for CSRF protection
            encoded_state = await generate_and_store_state(self.integration_name, user_id, org_id)
            
            # Construct the authorization URL based on the integration.
            if self.integration_name == "hubspot":
                auth_url = (
                    f"{HUBSPOT_AUTH_URL}"
                    f"?client_id={self.config['client_id']}"
                    f"&redirect_uri={self.config['redirect_uri']}"
                    f"&scope={self.config['scopes']}"
                    f"&state={encoded_state}"
                )
            else:
                # If other integrations are supported, implement their URL generation here.
                raise NotImplementedError(f"Authorization URL not implemented for {self.integration_name}")
            
            duration = time.time() - start_time
            log_integration_event(
                self.logger,
                "AUTHORIZE_START",
                self.integration_name,
                user_id,
                org_id,
                {
                    "duration_ms": duration * 1000,
                    "redirect_uri": self.config['redirect_uri']
                }
            )
            return auth_url
        except Exception as e:
            log_error(
                self.logger,
                e,
                {
                    "user_id": user_id,
                    "org_id": org_id,
                    "integration": self.integration_name,
                    "operation": "authorize"
                }
            )
            raise

    async def oauth2callback(self, request: Request) -> HTMLResponse:
        """
        Handles the OAuth2 callback from the authorization server.
        
        Validates the state parameter, exchanges the authorization code for an access token,
        stores the credentials, logs the event, and returns an HTML response to close the popup.
        """
        start_time = time.time()
        try:
            # Check if an error is returned in the callback query parameters
            if request.query_params.get('error'):
                error_msg = request.query_params.get('error')
                log_error(
                    self.logger,
                    Exception(error_msg),
                    {"operation": "oauth2callback", "error_type": "oauth_error"}
                )
                raise HTTPException(status_code=400, detail=error_msg)
            
            code = request.query_params.get('code')
            encoded_state = request.query_params.get('state')
            if not code or not encoded_state:
                log_error(
                    self.logger,
                    ValueError("Missing code or state"),
                    {"operation": "oauth2callback"}
                )
                raise HTTPException(status_code=400, detail='Missing code or state')
            
            # Validate the state token and extract user and organization IDs
            state_data = await validate_state(self.integration_name, encoded_state)
            user_id = state_data.get('user_id')
            org_id = state_data.get('org_id')
            
            # Exchange the authorization code for an access token
            credentials = await exchange_code_for_token(
                self.integration_name,
                code,
                self.get_additional_token_params()
            )
            
            # Store credentials for later use (e.g., API calls)
            await store_credentials(self.integration_name, user_id, org_id, credentials)
            
            duration = time.time() - start_time
            log_integration_event(
                self.logger,
                "OAUTH_CALLBACK_SUCCESS",
                self.integration_name,
                user_id,
                org_id,
                {
                    "duration_ms": duration * 1000,
                    "has_access_token": "access_token" in credentials
                }
            )
            
            # Return HTML instructing the browser to close the popup window upon success
            close_window_script = """
            <html>
                <script>
                    window.close();
                </script>
            </html>
            """
            return HTMLResponse(content=close_window_script)
        except Exception as e:
            log_error(
                self.logger,
                e,
                {
                    "operation": "oauth2callback",
                    "integration": self.integration_name
                }
            )
            raise

    async def get_credentials(self, user_id: str, org_id: str) -> Dict[str, Any]:
        """
        Retrieves stored OAuth credentials for the given user and organization.
        
        Logs the retrieval duration and success status.
        
        Returns:
            Dict[str, Any]: The OAuth credentials.
        
        Raises:
            HTTPException: If no credentials are found.
        """
        try:
            start_time = time.time()
            credentials = await get_credentials(self.integration_name, user_id, org_id)
            duration = time.time() - start_time
            log_integration_event(
                self.logger,
                "GET_CREDENTIALS",
                self.integration_name,
                user_id,
                org_id,
                {
                    "duration_ms": duration * 1000,
                    "success": bool(credentials)
                }
            )
            return credentials
        except Exception as e:
            log_error(
                self.logger,
                e,
                {
                    "user_id": user_id,
                    "org_id": org_id,
                    "integration": self.integration_name,
                    "operation": "get_credentials"
                }
            )
            raise

    @abstractmethod
    async def get_items(self, credentials: str) -> List[IntegrationItem]:
        """
        Abstract method to retrieve and format integration items.
        
        Must be implemented by each specific integration subclass.
        """
        pass

    def get_additional_token_params(self) -> Optional[Dict[str, Any]]:
        """
        Returns additional parameters required for token exchange.
        
        Subclasses can override this method if extra parameters are needed.
        """
        return None

    def create_integration_item(
        self,
        id: str,
        type: str,
        name: str,
        creation_time: Optional[datetime] = None,
        last_modified_time: Optional[datetime] = None,
        parent_id: Optional[str] = None,
        url: Optional[str] = None,
        directory: bool = False,
        **kwargs
    ) -> IntegrationItem:
        """
        Helper method to create an IntegrationItem object with consistent formatting.
        
        Args:
            id (str): The unique identifier for the item.
            type (str): The type or category of the item.
            name (str): The display name of the item.
            creation_time (Optional[datetime]): Creation timestamp.
            last_modified_time (Optional[datetime]): Last modified timestamp.
            parent_id (Optional[str]): Parent item identifier.
            url (Optional[str]): Associated URL.
            directory (bool): Flag indicating if the item is a directory.
            **kwargs: Additional attributes for the IntegrationItem.
        
        Returns:
            IntegrationItem: The constructed integration item.
        """
        return IntegrationItem(
            id=id,
            type=type,
            name=name,
            creation_time=creation_time,
            last_modified_time=last_modified_time,
            parent_id=parent_id,
            url=url,
            directory=directory,
            **kwargs
        )
