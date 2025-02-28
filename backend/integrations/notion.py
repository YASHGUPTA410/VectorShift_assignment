# notion.py

import json
import secrets
import logging
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import asyncio
import base64
from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to DEBUG for detailed logging; adjust as needed

# Notion OAuth client configuration (redacted for security)
CLIENT_ID = 'XXX'
CLIENT_SECRET = 'XXX'
encoded_client_id_secret = base64.b64encode(f'{CLIENT_ID}:{CLIENT_SECRET}'.encode()).decode()

REDIRECT_URI = 'http://localhost:8000/integrations/notion/oauth2callback'
authorization_url = (
    f'https://api.notion.com/v1/oauth/authorize?client_id={CLIENT_ID}'
    f'&response_type=code&owner=user&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fintegrations%2Fnotion%2Foauth2callback'
)

async def authorize_notion(user_id, org_id):
    """
    Initiates the Notion OAuth2 authorization flow.
    Generates a state object for CSRF protection, stores it in Redis, and returns the full authorization URL.
    """
    logger.debug("Starting Notion authorization for user_id: %s, org_id: %s", user_id, org_id)
    # Generate a secure state token and construct the state object
    state_token = secrets.token_urlsafe(32)
    state_data = {
        'state': state_token,
        'user_id': user_id,
        'org_id': org_id
    }
    encoded_state = json.dumps(state_data)
    # Store the state in Redis with an expiration time (10 minutes)
    await add_key_value_redis(f'notion_state:{org_id}:{user_id}', encoded_state, expire=600)
    logger.debug("Stored Notion state in Redis for user_id: %s, org_id: %s", user_id, org_id)
    # Build the full authorization URL with the encoded state appended
    auth_url = f'{authorization_url}&state={encoded_state}'
    logger.debug("Generated Notion authorization URL: %s", auth_url)
    return auth_url

async def oauth2callback_notion(request: Request):
    """
    Handles the OAuth2 callback from Notion.
    Validates the state parameter, exchanges the authorization code for tokens,
    stores the credentials in Redis, and returns an HTML response to close the browser window.
    """
    logger.debug("Processing Notion OAuth2 callback")
    # Handle potential error parameter from the callback
    if request.query_params.get('error'):
        error_detail = request.query_params.get('error')
        logger.error("Error in Notion OAuth2 callback: %s", error_detail)
        raise HTTPException(status_code=400, detail=error_detail)
    
    # Extract authorization code and state from the request
    code = request.query_params.get('code')
    encoded_state = request.query_params.get('state')
    state_data = json.loads(encoded_state)
    original_state = state_data.get('state')
    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')
    logger.debug("Notion callback received code for user_id: %s, org_id: %s", user_id, org_id)

    # Validate the state by comparing with the state stored in Redis
    saved_state = await get_value_redis(f'notion_state:{org_id}:{user_id}')
    if not saved_state or original_state != json.loads(saved_state).get('state'):
        logger.error("State mismatch for Notion OAuth2 callback for user_id: %s, org_id: %s", user_id, org_id)
        raise HTTPException(status_code=400, detail='State does not match.')

    # Exchange the authorization code for an access token and delete the stored state concurrently
    async with httpx.AsyncClient() as client:
        logger.debug("Exchanging code for Notion token for user_id: %s, org_id: %s", user_id, org_id)
        token_response, _ = await asyncio.gather(
            client.post(
                'https://api.notion.com/v1/oauth/token',
                json={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': REDIRECT_URI
                },
                headers={
                    'Authorization': f'Basic {encoded_client_id_secret}',
                    'Content-Type': 'application/json',
                }
            ),
            delete_key_redis(f'notion_state:{org_id}:{user_id}'),
        )
        logger.debug("Received token response from Notion: %s", token_response.json())

    # Store the received credentials in Redis with an expiration time (10 minutes)
    await add_key_value_redis(f'notion_credentials:{org_id}:{user_id}', json.dumps(token_response.json()), expire=600)
    logger.debug("Stored Notion credentials in Redis for user_id: %s, org_id: %s", user_id, org_id)
    
    # Return HTML content that triggers the closing of the browser window
    close_window_script = """
    <html>
        <script>
            window.close();
        </script>
    </html>
    """
    return HTMLResponse(content=close_window_script)

async def get_notion_credentials(user_id, org_id):
    """
    Retrieves stored Notion OAuth credentials from Redis, deletes them upon retrieval,
    and returns the credentials.
    """
    logger.debug("Retrieving Notion credentials for user_id: %s, org_id: %s", user_id, org_id)
    credentials = await get_value_redis(f'notion_credentials:{org_id}:{user_id}')
    if not credentials:
        logger.error("No Notion credentials found for user_id: %s, org_id: %s", user_id, org_id)
        raise HTTPException(status_code=400, detail='No credentials found.')
    credentials = json.loads(credentials)
    if not credentials:
        logger.error("Credentials data is empty for Notion user_id: %s, org_id: %s", user_id, org_id)
        raise HTTPException(status_code=400, detail='No credentials found.')
    # Delete the credentials from Redis after retrieval
    await delete_key_redis(f'notion_credentials:{org_id}:{user_id}')
    logger.debug("Notion credentials retrieved and deleted from Redis for user_id: %s, org_id: %s", user_id, org_id)
    return credentials

def _recursive_dict_search(data, target_key):
    """
    Recursively searches for a key in a nested dictionary or list structure.
    Returns the value if the key is found, otherwise returns None.
    """
    if isinstance(data, dict) and target_key in data:
        return data[target_key]

    if isinstance(data, dict):
        for value in data.values():
            result = _recursive_dict_search(value, target_key)
            if result is not None:
                return result

    if isinstance(data, list):
        for item in data:
            result = _recursive_dict_search(item, target_key)
            if result is not None:
                return result

    return None

def create_integration_item_metadata_object(response_json: dict) -> IntegrationItem:
    """
    Creates an IntegrationItem object from a Notion API response.
    Extracts and formats metadata needed for the integration.
    """
    logger.debug("Creating integration item metadata object from response")
    # Attempt to extract the 'content' from properties; if not found, try a recursive search
    name = _recursive_dict_search(response_json.get('properties', {}), 'content')
    parent_type = response_json.get('parent', {}).get('type')
    
    # Determine parent_id based on the type of parent
    if parent_type == 'workspace':
        parent_id = None
    else:
        parent_id = response_json.get('parent', {}).get(parent_type)
    
    # If no name was found, perform a recursive search on the entire response
    name = _recursive_dict_search(response_json, 'content') if name is None else name
    # Fallback to a default value if still None
    name = 'multi_select' if name is None else name
    # Combine object type with name for a descriptive label
    name = f"{response_json.get('object', '')} {name}"

    integration_item_metadata = IntegrationItem(
        id=response_json.get('id'),
        type=response_json.get('object'),
        name=name,
        creation_time=response_json.get('created_time'),
        last_modified_time=response_json.get('last_edited_time'),
        parent_id=parent_id,
    )
    logger.debug("Created IntegrationItem metadata: id=%s, type=%s, name=%s", 
                 integration_item_metadata.id, integration_item_metadata.type, integration_item_metadata.name)
    return integration_item_metadata

async def get_items_notion(credentials) -> list[IntegrationItem]:
    """
    Retrieves and aggregates metadata for a Notion integration.
    Performs an asynchronous search API call and creates IntegrationItem objects for each result.
    """
    logger.debug("Starting to retrieve Notion items")
    # Parse the credentials and set up the headers for the API request
    credentials = json.loads(credentials)
    headers = {
        'Authorization': f'Bearer {credentials.get("access_token")}',
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    }
    # Use an asynchronous HTTP client for the API call
    async with httpx.AsyncClient() as client:
        response = await client.post('https://api.notion.com/v1/search', headers=headers)
    list_of_integration_item_metadata = []
    if response.status_code == 200:
        results = response.json().get('results', [])
        logger.debug("Notion API returned %d results", len(results))
        for result in results:
            item = create_integration_item_metadata_object(result)
            list_of_integration_item_metadata.append(item)
            logger.debug("Processed Notion item with id: %s", result.get('id'))
        logger.info("Total Notion items processed: %d", len(list_of_integration_item_metadata))
    else:
        logger.error("Failed to retrieve Notion items. Status code: %s, Response: %s", 
                     response.status_code, response.text)
        raise HTTPException(status_code=response.status_code, detail="Failed to retrieve items from Notion")
    return list_of_integration_item_metadata
