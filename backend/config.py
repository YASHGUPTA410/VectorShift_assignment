# config.py

import os
import logging
from typing import Dict

# Set up a module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Adjust logging level as needed
logger.info("Loading configuration settings...")

# Base URLs for HubSpot OAuth and API endpoints
HUBSPOT_AUTH_URL = "https://app.hubspot.com/oauth/authorize"  # URL for initiating HubSpot OAuth authorization
HUBSPOT_TOKEN_URL = "https://api.hubspot.com/oauth/v1/token"    # URL for exchanging authorization codes for tokens
HUBSPOT_API_BASE = "https://api.hubspot.com/crm/v3"             # Base URL for HubSpot CRM API v3

# Client configurations for different integrations.
# Each integration configuration includes its client ID, client secret, redirect URI,
# and scopes (if applicable). These values are used in the OAuth flows.
CLIENT_CONFIGS: Dict[str, Dict[str, str]] = {
    "hubspot": {
        "client_id": "06d95fd8-a81d-4699-8e0a-92da349d7ccf",
        "client_secret": "e8f4d008-2639-4e3b-bb84-e38da0fc253f",
        "redirect_uri": "http://localhost:8000/integrations/hubspot/oauth2callback",
        "scopes": "crm.objects.contacts.read crm.objects.companies.read crm.objects.deals.read oauth"
    },
    "notion": {
        "client_id": "XXX",
        "client_secret": "XXX",
        "redirect_uri": "http://localhost:8000/integrations/notion/oauth2callback"
    },
    "airtable": {
        "client_id": "XXX",
        "client_secret": "XXX",
        "redirect_uri": "http://localhost:8000/integrations/airtable/oauth2callback"
    }
}

# Redis configuration parameters for caching tokens and state data
REDIS_HOST = "localhost"  # Host address for the Redis server
REDIS_PORT = 6379         # Port on which Redis is running
REDIS_DB = 0              # Redis database index to use

# CORS configuration for the API.
# This list specifies the allowed origins for cross-origin requests (e.g., from your React frontend).
CORS_ORIGINS = [
    "http://localhost:3000",  # React app address
]

# State token expiration time (in seconds).
# This is used to set the lifespan for OAuth state tokens to protect against CSRF.
STATE_TOKEN_EXPIRATION = 300  # 5 minutes
