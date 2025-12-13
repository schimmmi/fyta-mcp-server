"""
FYTA API Client
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger("fyta-mcp-server")

# FYTA API Configuration
FYTA_BASE_URL = "https://web.fyta.de/api"
FYTA_AUTH_ENDPOINT = f"{FYTA_BASE_URL}/auth/login"
FYTA_USER_PLANT_ENDPOINT = f"{FYTA_BASE_URL}/user-plant"
FYTA_MEASUREMENTS_ENDPOINT = f"{FYTA_BASE_URL}/user-plant/measurements"


class FytaClient:
    """Client for interacting with the FYTA API"""

    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self.client = httpx.AsyncClient(timeout=30.0)

    async def authenticate(self) -> bool:
        """Authenticate with the FYTA API"""
        try:
            response = await self.client.post(
                FYTA_AUTH_ENDPOINT,
                json={"email": self.email, "password": self.password}
            )
            response.raise_for_status()

            data = response.json()
            self.access_token = data["access_token"]
            self.refresh_token = data.get("refresh_token")

            # Token expires in seconds (default: 5184000 = 60 days)
            expires_in = data.get("expires_in", 5184000)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)

            logger.info("Successfully authenticated with FYTA API")
            return True

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False

    async def ensure_authenticated(self):
        """Ensure we have a valid token"""
        if not self.access_token or (
            self.token_expires_at and datetime.now() >= self.token_expires_at
        ):
            await self.authenticate()

    async def get_plants(self) -> Dict[str, Any]:
        """Get all plants with their sensor data"""
        await self.ensure_authenticated()

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = await self.client.get(FYTA_USER_PLANT_ENDPOINT, headers=headers)
        response.raise_for_status()

        return response.json()

    async def get_plant_by_id(self, plant_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific plant by ID"""
        plants_data = await self.get_plants()

        for plant in plants_data.get("plants", []):
            if plant["id"] == plant_id:
                return plant

        return None

    async def get_plant_measurements(self, plant_id: int) -> Dict[str, Any]:
        """Get historical measurements for a specific plant"""
        await self.ensure_authenticated()

        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"{FYTA_MEASUREMENTS_ENDPOINT}/{plant_id}"
        response = await self.client.get(url, headers=headers)
        response.raise_for_status()

        return response.json()

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
