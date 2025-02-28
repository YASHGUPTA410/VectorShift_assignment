# main.py

from fastapi import FastAPI, Form, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# Import integration functions
from integrations.airtable import (
    authorize_airtable,
    get_items_airtable,
    oauth2callback_airtable,
    get_airtable_credentials
)
from integrations.notion import (
    authorize_notion,
    get_items_notion,
    oauth2callback_notion,
    get_notion_credentials
)
from integrations.hubspot import (
    authorize_hubspot,
    get_hubspot_credentials,
    get_items_hubspot,
    oauth2callback_hubspot
)

from routes import logs
from logger import app_logger

# Initialize the FastAPI app with a title
app = FastAPI(title="VectorShift Integration API")

# Configure allowed CORS origins (e.g., React frontend)
origins = [
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the logs router for viewing application logs
app.include_router(logs.router, tags=["logs"])

# -------------------------------
# Define routers for each integration
# -------------------------------

# Airtable Router
airtable_router = APIRouter(prefix="/integrations/airtable", tags=["Airtable"])

@airtable_router.post("/authorize")
async def authorize_airtable_integration(user_id: str = Form(...), org_id: str = Form(...)):
    """
    Initiates the Airtable OAuth flow by generating an authorization URL.
    """
    app_logger.info("Airtable authorize: user_id=%s, org_id=%s", user_id, org_id)
    return await authorize_airtable(user_id, org_id)

@airtable_router.get("/oauth2callback")
async def oauth2callback_airtable_integration(request: Request):
    """
    Handles the Airtable OAuth callback to exchange the code for tokens.
    """
    app_logger.info("Airtable oauth2callback called")
    return await oauth2callback_airtable(request)

@airtable_router.post("/credentials")
async def get_airtable_credentials_integration(user_id: str = Form(...), org_id: str = Form(...)):
    """
    Retrieves stored Airtable credentials for the specified user and organization.
    """
    app_logger.info("Airtable get credentials: user_id=%s, org_id=%s", user_id, org_id)
    return await get_airtable_credentials(user_id, org_id)

@airtable_router.post("/load")
async def get_airtable_items(credentials: str = Form(...)):
    """
    Loads Airtable integration items using the provided credentials.
    """
    app_logger.info("Airtable load items")
    return await get_items_airtable(credentials)

# Notion Router
notion_router = APIRouter(prefix="/integrations/notion", tags=["Notion"])

@notion_router.post("/authorize")
async def authorize_notion_integration(user_id: str = Form(...), org_id: str = Form(...)):
    """
    Initiates the Notion OAuth flow by generating an authorization URL.
    """
    app_logger.info("Notion authorize: user_id=%s, org_id=%s", user_id, org_id)
    return await authorize_notion(user_id, org_id)

@notion_router.get("/oauth2callback")
async def oauth2callback_notion_integration(request: Request):
    """
    Handles the Notion OAuth callback to exchange the code for tokens.
    """
    app_logger.info("Notion oauth2callback called")
    return await oauth2callback_notion(request)

@notion_router.post("/credentials")
async def get_notion_credentials_integration(user_id: str = Form(...), org_id: str = Form(...)):
    """
    Retrieves stored Notion credentials for the specified user and organization.
    """
    app_logger.info("Notion get credentials: user_id=%s, org_id=%s", user_id, org_id)
    return await get_notion_credentials(user_id, org_id)

@notion_router.post("/load")
async def get_notion_items(credentials: str = Form(...)):
    """
    Loads Notion integration items using the provided credentials.
    """
    app_logger.info("Notion load items")
    return await get_items_notion(credentials)

# HubSpot Router
hubspot_router = APIRouter(prefix="/integrations/hubspot", tags=["HubSpot"])

@hubspot_router.post("/authorize")
async def authorize_hubspot_integration(user_id: str = Form(...), org_id: str = Form(...)):
    """
    Initiates the HubSpot OAuth flow by generating an authorization URL.
    """
    app_logger.info("HubSpot authorize: user_id=%s, org_id=%s", user_id, org_id)
    return await authorize_hubspot(user_id, org_id)

@hubspot_router.get("/oauth2callback")
async def oauth2callback_hubspot_integration(request: Request):
    """
    Handles the HubSpot OAuth callback to exchange the code for tokens.
    """
    app_logger.info("HubSpot oauth2callback called")
    return await oauth2callback_hubspot(request)

@hubspot_router.post("/credentials")
async def get_hubspot_credentials_integration(user_id: str = Form(...), org_id: str = Form(...)):
    """
    Retrieves stored HubSpot credentials for the specified user and organization.
    """
    app_logger.info("HubSpot get credentials: user_id=%s, org_id=%s", user_id, org_id)
    return await get_hubspot_credentials(user_id, org_id)

@hubspot_router.post("/load")
async def get_hubspot_items(credentials: str = Form(...)):
    """
    Loads HubSpot integration items using the provided credentials.
    """
    app_logger.info("HubSpot load items")
    return await get_items_hubspot(credentials)

# -------------------------------
# Include the integration routers in the main app
# -------------------------------
app.include_router(airtable_router)
app.include_router(notion_router)
app.include_router(hubspot_router)

# -------------------------------
# Health Check and Basic Endpoints
# -------------------------------

@app.get("/")
def read_root():
    """
    Basic health check endpoint.
    Returns service status and current UTC timestamp.
    """
    app_logger.info("Health check endpoint called")
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/healthcheck")
def health_check():
    """
    Secondary health check endpoint.
    """
    app_logger.info("Secondary health check endpoint called")
    return {"status": "ok"}

# -------------------------------
# Application Startup and Shutdown Events
# -------------------------------

@app.on_event("startup")
async def startup_event():
    """
    Event handler for application startup.
    """
    app_logger.info("Application startup")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Event handler for application shutdown.
    """
    app_logger.info("Application shutdown")
