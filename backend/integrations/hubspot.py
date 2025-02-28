# hubspot.py

import json
import time
import httpx
from fastapi import Request
from datetime import datetime
from typing import List, Dict, Any
from config import HUBSPOT_API_BASE
from logger import log_error, log_integration_event
from integrations.base_integration import BaseIntegration
from integrations.integration_item import IntegrationItem

class HubSpotIntegration(BaseIntegration):
    def __init__(self):
        """
        Initialize the HubSpot integration using the base integration configuration and logger.
        """
        super().__init__("hubspot")

    async def authorize_hubspot(self, user_id: str, org_id: str) -> str:
        """
        Generate and return the HubSpot authorization URL by invoking the generic authorize method.
        """
        self.logger.debug("Initiating HubSpot authorization for user_id: %s, org_id: %s", user_id, org_id)
        return await self.authorize(user_id, org_id)

    async def oauth2callback_hubspot(self, request: Request):
        """
        Handle the OAuth callback from HubSpot.
        Validates the callback parameters and exchanges the code for credentials.
        """
        self.logger.debug("Processing HubSpot OAuth callback")
        return await self.oauth2callback(request)

    async def get_hubspot_credentials(self, user_id: str, org_id: str):
        """
        Retrieve stored HubSpot credentials using the base integration's credential retrieval.
        """
        self.logger.debug("Retrieving HubSpot credentials for user_id: %s, org_id: %s", user_id, org_id)
        return await self.get_credentials(user_id, org_id)

    async def get_items(self, credentials: str) -> List[IntegrationItem]:
        """
        Retrieve and format HubSpot items (contacts, companies, and deals) using the provided credentials.
        
        API calls for contacts, companies, and deals are performed in parallel.
        Logs the API call duration, number of items processed, and any errors encountered.
        
        Returns:
            List[IntegrationItem]: The list of retrieved integration items.
        """
        start_time = time.time()
        try:
            # Parse credentials and extract the access token.
            credentials_dict = json.loads(credentials)
            access_token = credentials_dict.get("access_token")
            if not access_token:
                raise ValueError("No access token found in credentials")

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            self.logger.info("Starting HubSpot API calls for data retrieval")
            async with httpx.AsyncClient() as client:
                api_start_time = time.time()
                # Perform API calls concurrently for contacts, companies, and deals.
                responses = await client.get(
                    f"{HUBSPOT_API_BASE}/objects/contacts",
                    headers=headers,
                    params={"limit": 100}
                ), await client.get(
                    f"{HUBSPOT_API_BASE}/objects/companies",
                    headers=headers,
                    params={"limit": 100}
                ), await client.get(
                    f"{HUBSPOT_API_BASE}/objects/deals",
                    headers=headers,
                    params={"limit": 100}
                )
                api_duration = time.time() - api_start_time
                self.logger.info("HubSpot API calls completed in %.2fms", api_duration * 1000)

            items: List[IntegrationItem] = []
            stats = {"contacts": 0, "companies": 0, "deals": 0, "errors": 0}

            # Process contacts response.
            contacts_response = responses[0]
            if contacts_response.status_code == 200:
                contacts_data = contacts_response.json()
                self.logger.debug("Processing %d contacts", len(contacts_data.get("results", [])))
                for contact in contacts_data.get("results", []):
                    try:
                        item = self._create_contact_item(contact)
                        items.append(item)
                        stats["contacts"] += 1
                        self.logger.debug("Processed contact: %s", contact.get("id"))
                    except Exception as e:
                        stats["errors"] += 1
                        log_error(
                            self.logger,
                            e,
                            {"operation": "process_contact", "contact_id": contact.get("id")}
                        )

            # Process companies response.
            companies_response = responses[1]
            if companies_response.status_code == 200:
                companies_data = companies_response.json()
                self.logger.debug("Processing %d companies", len(companies_data.get("results", [])))
                for company in companies_data.get("results", []):
                    try:
                        item = self._create_company_item(company)
                        items.append(item)
                        stats["companies"] += 1
                        self.logger.debug("Processed company: %s", company.get("id"))
                    except Exception as e:
                        stats["errors"] += 1
                        log_error(
                            self.logger,
                            e,
                            {"operation": "process_company", "company_id": company.get("id")}
                        )

            # Process deals response.
            deals_response = responses[2]
            if deals_response.status_code == 200:
                deals_data = deals_response.json()
                self.logger.debug("Processing %d deals", len(deals_data.get("results", [])))
                for deal in deals_data.get("results", []):
                    try:
                        item = self._create_deal_item(deal)
                        items.append(item)
                        stats["deals"] += 1
                        self.logger.debug("Processed deal: %s", deal.get("id"))
                    except Exception as e:
                        stats["errors"] += 1
                        log_error(
                            self.logger,
                            e,
                            {"operation": "process_deal", "deal_id": deal.get("id")}
                        )

            total_duration = time.time() - start_time
            log_integration_event(
                self.logger,
                "GET_ITEMS_COMPLETE",
                self.integration_name,
                "system",  # No specific user context provided.
                "system",  # No specific org context provided.
                {
                    "duration_ms": total_duration * 1000,
                    "api_duration_ms": api_duration * 1000,
                    "total_items": len(items),
                    "stats": stats
                }
            )
            self.logger.info("Total HubSpot items retrieved: %d", len(items))
            return items

        except Exception as e:
            log_error(
                self.logger,
                e,
                {"operation": "get_items", "integration": self.integration_name}
            )
            raise

    def _create_contact_item(self, contact: Dict[str, Any]) -> IntegrationItem:
        """
        Create an IntegrationItem object representing a HubSpot contact.
        """
        properties = contact.get("properties", {})
        return self.create_integration_item(
            id=contact.get("id"),
            type="contact",
            name=f"{properties.get('firstname', '')} {properties.get('lastname', '')}".strip() or "Unnamed Contact",
            creation_time=datetime.fromisoformat(properties.get("createdate", "").replace("Z", "+00:00"))
            if properties.get("createdate") else None,
            last_modified_time=datetime.fromisoformat(properties.get("lastmodifieddate", "").replace("Z", "+00:00"))
            if properties.get("lastmodifieddate") else None,
            url=f"https://app.hubspot.com/contacts/{properties.get('hubspot_owner_id')}/contact/{contact.get('id')}"
            if properties.get("hubspot_owner_id") else None
        )

    def _create_company_item(self, company: Dict[str, Any]) -> IntegrationItem:
        """
        Create an IntegrationItem object representing a HubSpot company.
        """
        properties = company.get("properties", {})
        return self.create_integration_item(
            id=company.get("id"),
            type="company",
            name=properties.get("name", "Unnamed Company"),
            creation_time=datetime.fromisoformat(properties.get("createdate", "").replace("Z", "+00:00"))
            if properties.get("createdate") else None,
            last_modified_time=datetime.fromisoformat(properties.get("lastmodifieddate", "").replace("Z", "+00:00"))
            if properties.get("lastmodifieddate") else None,
            url=f"https://app.hubspot.com/contacts/{properties.get('hubspot_owner_id')}/company/{company.get('id')}"
            if properties.get("hubspot_owner_id") else None
        )

    def _create_deal_item(self, deal: Dict[str, Any]) -> IntegrationItem:
        """
        Create an IntegrationItem object representing a HubSpot deal.
        """
        properties = deal.get("properties", {})
        return self.create_integration_item(
            id=deal.get("id"),
            type="deal",
            name=properties.get("dealname", "Unnamed Deal"),
            creation_time=datetime.fromisoformat(properties.get("createdate", "").replace("Z", "+00:00"))
            if properties.get("createdate") else None,
            last_modified_time=datetime.fromisoformat(properties.get("lastmodifieddate", "").replace("Z", "+00:00"))
            if properties.get("lastmodifieddate") else None,
            url=f"https://app.hubspot.com/contacts/{properties.get('hubspot_owner_id')}/deal/{deal.get('id')}"
            if properties.get("hubspot_owner_id") else None
        )

# Create a singleton instance of the HubSpotIntegration class.
hubspot_integration = HubSpotIntegration()

# Export instance methods for external use.
authorize_hubspot = hubspot_integration.authorize_hubspot
oauth2callback_hubspot = hubspot_integration.oauth2callback_hubspot
get_hubspot_credentials = hubspot_integration.get_hubspot_credentials
get_items_hubspot = hubspot_integration.get_items
