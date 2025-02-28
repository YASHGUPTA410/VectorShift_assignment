# utils.py

import json
import secrets
import base64
import httpx
import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis
from config import STATE_TOKEN_EXPIRATION, CLIENT_CONFIGS

# Set up a module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Adjust logging level as needed

async def generate_and_store_state(integration: str, user_id: str, org_id: str) -> str:
    """
    Generate and store a state token for the OAuth flow.
    
    Args:
        integration (str): Integration identifier (e.g., "hubspot", "notion").
        user_id (str): User identifier.
        org_id (str): Organization identifier.
    
    Returns:
        str: The encoded state token.
    """
    logger.debug("Generating state token for integration=%s, user_id=%s, org_id=%s", integration, user_id, org_id)
    state_data = {
        'state': secrets.token_urlsafe(32),
        'user_id': user_id,
        'org_id': org_id
    }
    encoded_state = json.dumps(state_data)
    redis_key = f'{integration}_state:{org_id}:{user_id}'
    logger.debug("Storing state token in Redis with key=%s", redis_key)
    await add_key_value_redis(redis_key, encoded_state, expire=STATE_TOKEN_EXPIRATION)
    logger.debug("State token stored successfully")
    return encoded_state

async def validate_state(integration: str, encoded_state: str) -> Dict[str, str]:
    """
    Validate the state token received from the OAuth callback.
    
    Args:
        integration (str): Integration identifier.
        encoded_state (str): Encoded state token from the callback.
    
    Returns:
        Dict[str, str]: Decoded state data.
    
    Raises:
        HTTPException: If state is missing, invalid, or does not match.
    """
    logger.debug("Validating state token for integration=%s", integration)
    try:
        state_data = json.loads(encoded_state)
        original_state = state_data.get('state')
        user_id = state_data.get('user_id')
        org_id = state_data.get('org_id')
        logger.debug("Extracted state data: %s", state_data)
        
        if not all([original_state, user_id, org_id]):
            logger.error("Missing required fields in state data: %s", state_data)
            raise HTTPException(status_code=400, detail='Invalid state data.')
        
        redis_key = f'{integration}_state:{org_id}:{user_id}'
        saved_state = await get_value_redis(redis_key)
        logger.debug("Retrieved saved state from Redis for key=%s: %s", redis_key, saved_state)
        if not saved_state or original_state != json.loads(saved_state).get('state'):
            logger.error("State token mismatch: original=%s, saved=%s", original_state, saved_state)
            raise HTTPException(status_code=400, detail='State does not match.')
        
        return state_data
    except json.JSONDecodeError:
        logger.exception("Failed to decode state token: %s", encoded_state)
        raise HTTPException(status_code=400, detail='Invalid state format.')

def get_basic_auth_header(integration: str) -> str:
    """
    Generate a Basic Auth header for OAuth token requests.
    
    Args:
        integration (str): Integration identifier.
    
    Returns:
        str: A Basic Auth header string.
    """
    logger.debug("Generating Basic Auth header for integration=%s", integration)
    client_id = CLIENT_CONFIGS[integration]["client_id"]
    client_secret = CLIENT_CONFIGS[integration]["client_secret"]
    credentials = f"{client_id}:{client_secret}"
    # Note: For security, avoid logging the actual credentials.
    encoded = base64.b64encode(credentials.encode()).decode()
    header = f"Basic {encoded}"
    logger.debug("Basic Auth header generated for integration=%s", integration)
    return header

# async def exchange_code_for_token(
#     integration: str,
#     code: str,
#     additional_params: Optional[Dict[str, Any]] = None
# ) -> Dict[str, Any]:
#     """
#     Exchange an authorization code for an access token.
    
#     Args:
#         integration (str): Integration identifier.
#         code (str): Authorization code received from OAuth.
#         additional_params (Optional[Dict[str, Any]]): Additional parameters for the token request.
    
#     Returns:
#         Dict[str, Any]: The token response as a JSON dictionary.
    
#     Raises:
#         HTTPException: If the token exchange fails.
#     """
#     logger.debug("Exchanging code for token for integration=%s", integration)
#     config = CLIENT_CONFIGS[integration]
#     token_url = {
#         "hubspot": "https://api.hubspot.com/oauth/v1/token",
#         "notion": "https://api.notion.com/v1/oauth/token",
#         "airtable": "https://airtable.com/oauth/v1/token"
#     }.get(integration)

#     if not token_url:
#         logger.error("Unsupported integration for token exchange: %s", integration)
#         raise HTTPException(status_code=400, detail=f'Unsupported integration: {integration}')

#     data = {
#         "grant_type": "authorization_code",
#         "code": code,
#         "redirect_uri": config["redirect_uri"],
#         **(additional_params or {})
#     }
#     headers = {
#         "Authorization": get_basic_auth_header(integration),
#         "Content-Type": "application/json"
#     }
#     logger.debug("Sending token exchange request to %s with data=%s", token_url, data)
#     async with httpx.AsyncClient() as client:
#         response = await client.post(token_url, json=data, headers=headers)
#         if response.status_code != 200:
#             logger.error("Token exchange failed for integration=%s with status=%s: %s", 
#                          integration, response.status_code, response.text)
#             raise HTTPException(
#                 status_code=response.status_code,
#                 detail=f"Token exchange failed: {response.text}"
#             )
#         token_response = response.json()
#         logger.debug("Token exchange successful for integration=%s: %s", integration, token_response)
#         return token_response


async def exchange_code_for_token(
    integration: str,
    code: str,
    additional_params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Exchange an authorization code for an access token.
    """
    logger.debug("Exchanging code for token for integration=%s", integration)
    config = CLIENT_CONFIGS[integration]
    token_url = {
        "hubspot": "https://api.hubspot.com/oauth/v1/token",
        "notion": "https://api.notion.com/v1/oauth/token",
        "airtable": "https://airtable.com/oauth/v1/token"
    }.get(integration)

    if not token_url:
        logger.error("Unsupported integration for token exchange: %s", integration)
        raise HTTPException(status_code=400, detail=f'Unsupported integration: {integration}')

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "redirect_uri": config["redirect_uri"]
    }
    headers = {
        "Authorization": get_basic_auth_header(integration),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    logger.debug("Sending token exchange request to %s with data=%s", token_url, data)
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data, headers=headers)
        if response.status_code != 200:
            logger.error("Token exchange failed for integration=%s with status=%s: %s", 
                         integration, response.status_code, response.text)
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Token exchange failed: {response.text}"
            )
        token_response = response.json()
        logger.debug("Token exchange successful for integration=%s: %s", integration, token_response)
        return token_response



def recursive_dict_search(data: Dict[str, Any], target_key: str) -> Optional[Any]:
    """
    Recursively search for a key in a nested dictionary or list.
    
    Args:
        data (Dict[str, Any]): The dictionary to search.
        target_key (str): The key to search for.
    
    Returns:
        Optional[Any]: The value associated with target_key if found, else None.
    """
    # Only log the start of the search to avoid overly verbose output during recursion.
    logger.debug("Starting recursive search for key '%s'", target_key)
    if target_key in data:
        return data[target_key]

    for value in data.values():
        if isinstance(value, dict):
            result = recursive_dict_search(value, target_key)
            if result is not None:
                return result
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    result = recursive_dict_search(item, target_key)
                    if result is not None:
                        return result
    return None

async def store_credentials(integration: str, user_id: str, org_id: str, credentials: Dict[str, Any]) -> None:
    """
    Store OAuth credentials in Redis.
    
    Args:
        integration (str): Integration identifier.
        user_id (str): User identifier.
        org_id (str): Organization identifier.
        credentials (Dict[str, Any]): Credentials to store.
    """
    redis_key = f'{integration}_credentials:{org_id}:{user_id}'
    logger.debug("Storing credentials in Redis with key=%s", redis_key)
    await add_key_value_redis(redis_key, json.dumps(credentials), expire=STATE_TOKEN_EXPIRATION)
    logger.debug("Credentials stored successfully for key=%s", redis_key)

async def get_credentials(integration: str, user_id: str, org_id: str) -> Dict[str, Any]:
    """
    Retrieve and delete OAuth credentials from Redis.
    
    Args:
        integration (str): Integration identifier.
        user_id (str): User identifier.
        org_id (str): Organization identifier.
    
    Returns:
        Dict[str, Any]: Retrieved credentials.
    
    Raises:
        HTTPException: If no credentials are found or if they are in an invalid format.
    """
    redis_key = f'{integration}_credentials:{org_id}:{user_id}'
    logger.debug("Retrieving credentials from Redis with key=%s", redis_key)
    credentials = await get_value_redis(redis_key)
    if not credentials:
        logger.error("No credentials found for key=%s", redis_key)
        raise HTTPException(status_code=400, detail='No credentials found.')
    
    try:
        credentials_dict = json.loads(credentials)
    except json.JSONDecodeError:
        logger.exception("Failed to decode credentials for key=%s", redis_key)
        raise HTTPException(status_code=400, detail='Invalid credentials format.')
    
    if not credentials_dict:
        logger.error("Empty credentials dictionary for key=%s", redis_key)
        raise HTTPException(status_code=400, detail='Invalid credentials format.')
    
    await delete_key_redis(redis_key)
    logger.debug("Credentials retrieved and deleted from Redis for key=%s", redis_key)
    return credentials_dict
