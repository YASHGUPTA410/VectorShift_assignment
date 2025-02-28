# airtable.py

import datetime
import json
import secrets
import httpx
import asyncio
import base64
import hashlib
import logging
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

# Configure logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Adjust level as needed

# Constants for Airtable OAuth
CLIENT_ID = 'ab59156a-e48f-466e-92fa-b9e263b7e48a'
CLIENT_SECRET = 'b796e05cafdb0fa23a5235f832e8e2a7438512c828f7070a7504822591eec57a'
REDIRECT_URI = 'http://localhost:8000/integrations/airtable/oauth2callback'
authorization_url = (
    f'https://airtable.com/oauth2/v1/authorize?client_id={CLIENT_ID}&response_type=code&owner=user'
    f'&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fintegrations%2Fairtable%2Foauth2callback'
)
encoded_client_id_secret = base64.b64encode(f'{CLIENT_ID}:{CLIENT_SECRET}'.encode()).decode()
scope = (
    'data.records:read data.records:write data.recordComments:read data.recordComments:write '
    'schema.bases:read schema.bases:write'
)

async def authorize_airtable(user_id: str, org_id: str) -> str:
    """
    Initiates the Airtable OAuth2 flow by generating state and PKCE values,
    storing them in Redis, and constructing the authorization URL.
    """
    logger.info("Starting Airtable authorization for user_id: %s, org_id: %s", user_id, org_id)
    
    # Generate state for CSRF protection
    state_data = {
        'state': secrets.token_urlsafe(32),
        'user_id': user_id,
        'org_id': org_id
    }
    # Encode state as a URL-safe string (using base64 for additional safety)
    encoded_state = base64.urlsafe_b64encode(json.dumps(state_data).encode('utf-8')).decode('utf-8')

    # Generate PKCE code verifier and code challenge
    code_verifier = secrets.token_urlsafe(32)
    m = hashlib.sha256()
    m.update(code_verifier.encode('utf-8'))
    code_challenge = base64.urlsafe_b64encode(m.digest()).decode('utf-8').replace('=', '')

    # Build the authorization URL with state, PKCE parameters, and scope
    auth_url = (
        f'{authorization_url}&state={encoded_state}&code_challenge={code_challenge}'
        f'&code_challenge_method=S256&scope={scope}'
    )
    logger.debug("Generated authorization URL: %s", auth_url)

    # Store state and verifier in Redis with a short expiration (600 seconds)
    await asyncio.gather(
        add_key_value_redis(f'airtable_state:{org_id}:{user_id}', json.dumps(state_data), expire=600),
        add_key_value_redis(f'airtable_verifier:{org_id}:{user_id}', code_verifier, expire=600),
    )
    logger.info("Stored state and code verifier in Redis for user_id: %s, org_id: %s", user_id, org_id)
    return auth_url

async def oauth2callback_airtable(request: Request) -> HTMLResponse:
    """
    Handles the Airtable OAuth2 callback by validating the state,
    exchanging the authorization code for tokens, and storing credentials in Redis.
    """
    logger.info("Handling OAuth2 callback for Airtable")
    if request.query_params.get('error'):
        error_desc = request.query_params.get('error_description')
        logger.error("Error received in callback: %s", error_desc)
        raise HTTPException(status_code=400, detail=error_desc)
    
    code = request.query_params.get('code')
    encoded_state = request.query_params.get('state')
    # Decode the state back from base64 and JSON
    state_data = json.loads(base64.urlsafe_b64decode(encoded_state).decode('utf-8'))
    original_state = state_data.get('state')
    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')

    logger.debug("Callback state: %s, user_id: %s, org_id: %s", original_state, user_id, org_id)

    # Retrieve the stored state and code verifier from Redis
    saved_state, code_verifier = await asyncio.gather(
        get_value_redis(f'airtable_state:{org_id}:{user_id}'),
        get_value_redis(f'airtable_verifier:{org_id}:{user_id}'),
    )
    
    if not saved_state or original_state != json.loads(saved_state).get('state'):
        logger.error("State mismatch for user_id: %s, org_id: %s", user_id, org_id)
        raise HTTPException(status_code=400, detail='State does not match.')

    # Exchange the authorization code for tokens using Airtable's token endpoint
    async with httpx.AsyncClient() as client:
        response, _, _ = await asyncio.gather(
            client.post(
                'https://airtable.com/oauth2/v1/token',
                data={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': REDIRECT_URI,
                    'client_id': CLIENT_ID,
                    'code_verifier': code_verifier,  # code_verifier is already a string
                },
                headers={
                    'Authorization': f'Basic {encoded_client_id_secret}',
                    'Content-Type': 'application/x-www-form-urlencoded',
                }
            ),
            delete_key_redis(f'airtable_state:{org_id}:{user_id}'),
            delete_key_redis(f'airtable_verifier:{org_id}:{user_id}'),
        )
    logger.info("Exchanged authorization code for tokens for user_id: %s, org_id: %s", user_id, org_id)

    # Store the token credentials in Redis
    await add_key_value_redis(f'airtable_credentials:{org_id}:{user_id}', json.dumps(response.json()), expire=600)
    logger.debug("Stored Airtable credentials in Redis for user_id: %s, org_id: %s", user_id, org_id)
    
    # Return HTML instructing the browser to close the window after success
    close_window_script = """
    <html>
        <script>
            window.close();
        </script>
    </html>
    """
    return HTMLResponse(content=close_window_script)

async def get_airtable_credentials(user_id: str, org_id: str):
    """
    Retrieve and delete stored Airtable credentials for a given user and organization.
    
    Raises:
        HTTPException: If no credentials are found.
    
    Returns:
        The token credentials as a dictionary.
    """
    logger.info("Retrieving Airtable credentials for user_id: %s, org_id: %s", user_id, org_id)
    credentials = await get_value_redis(f'airtable_credentials:{org_id}:{user_id}')
    if not credentials:
        logger.error("No Airtable credentials found for user_id: %s, org_id: %s", user_id, org_id)
        raise HTTPException(status_code=400, detail='No credentials found.')
    
    credentials = json.loads(credentials)
    await delete_key_redis(f'airtable_credentials:{org_id}:{user_id}')
    logger.debug("Deleted Airtable credentials from Redis for user_id: %s, org_id: %s", user_id, org_id)
    return credentials

def create_integration_item_metadata_object(
    response_json: dict, item_type: str, parent_id: str = None, parent_name: str = None
) -> IntegrationItem:
    """
    Create an IntegrationItem object from the given response JSON.
    
    Args:
        response_json (dict): JSON response from Airtable.
        item_type (str): The type of item (e.g., 'Base' or 'Table').
        parent_id (str, optional): Parent identifier.
        parent_name (str, optional): Parent name.
    
    Returns:
        IntegrationItem: The constructed integration item.
    """
    # Append '_Base' to parent_id if provided
    parent_id = None if parent_id is None else parent_id + '_Base'
    integration_item_metadata = IntegrationItem(
        id=response_json.get('id', None) + '_' + item_type,
        name=response_json.get('name', None),
        type=item_type,
        parent_id=parent_id,
        parent_path_or_name=parent_name,
    )
    logger.debug("Created IntegrationItem metadata: %s", integration_item_metadata)
    return integration_item_metadata

async def fetch_bases_async(access_token: str, url: str, aggregated_response: list, offset: str = None) -> None:
    """
    Asynchronously fetch Airtable bases with pagination and aggregate results.
    
    Args:
        access_token (str): The access token for Airtable.
        url (str): Endpoint URL to fetch bases.
        aggregated_response (list): List to accumulate bases.
        offset (str, optional): Pagination offset.
    """
    logger.debug("Fetching bases from %s with offset: %s", url, offset)
    params = {'offset': offset} if offset else {}
    headers = {'Authorization': f'Bearer {access_token}'}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        results = data.get('bases', [])
        aggregated_response.extend(results)
        logger.debug("Fetched %d bases", len(results))
        if data.get('offset'):
            # Recursively fetch the next page
            await fetch_bases_async(access_token, url, aggregated_response, offset=data.get('offset'))
    else:
        logger.error("Error fetching bases: %s", response.text)
        raise Exception("Failed to fetch bases from Airtable.")

async def fetch_tables_for_base_async(access_token: str, base_id: str) -> list:
    """
    Asynchronously fetch tables for a given Airtable base.
    
    Args:
        access_token (str): The access token.
        base_id (str): The base identifier.
    
    Returns:
        list: A list of table objects.
    """
    tables_url = f'https://api.airtable.com/v0/meta/bases/{base_id}/tables'
    headers = {'Authorization': f'Bearer {access_token}'}
    async with httpx.AsyncClient() as client:
        response = await client.get(tables_url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        tables = data.get('tables', [])
        logger.debug("Fetched %d tables for base %s", len(tables), base_id)
        return tables
    else:
        logger.error("Error fetching tables for base %s: %s", base_id, response.text)
        return []

async def get_items_airtable(credentials: str) -> list[IntegrationItem]:
    """
    Retrieve a list of Airtable IntegrationItem objects representing bases and their tables.
    
    Uses the provided credentials to asynchronously query Airtable metadata endpoints.
    
    Returns:
        list[IntegrationItem]: List of integration items.
    """
    logger.info("Retrieving Airtable items using provided credentials.")
    credentials_dict = json.loads(credentials)
    access_token = credentials_dict.get('access_token')
    if not access_token:
        logger.error("Access token missing in credentials.")
        raise HTTPException(status_code=400, detail="Access token missing.")
    
    bases_url = 'https://api.airtable.com/v0/meta/bases'
    bases = []
    # Asynchronously fetch all bases
    await fetch_bases_async(access_token, bases_url, bases)
    logger.debug("Total bases fetched: %d", len(bases))
    
    integration_items = []
    
    # Process each base to create an IntegrationItem and fetch its tables concurrently
    table_tasks = []
    for base in bases:
        # Create an IntegrationItem for the base
        integration_items.append(create_integration_item_metadata_object(base, 'Base'))
        # Schedule fetching tables for this base
        table_tasks.append(fetch_tables_for_base_async(access_token, base.get("id")))
    
    # Run all table fetching tasks concurrently
    tables_results = await asyncio.gather(*table_tasks)
    for base, tables in zip(bases, tables_results):
        for table in tables:
            integration_items.append(
                create_integration_item_metadata_object(
                    table,
                    'Table',
                    parent_id=base.get('id'),
                    parent_name=base.get('name')
                )
            )
    
    logger.info("Completed retrieval of Airtable items. Total items: %d", len(integration_items))
    logger.debug("Integration items: %s", integration_items)
    return integration_items
