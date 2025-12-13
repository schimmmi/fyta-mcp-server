#!/usr/bin/env python3
"""
FYTA MCP Server - Plant sensor data access via Model Context Protocol
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fyta-mcp-server")

# FYTA API Configuration
FYTA_BASE_URL = "https://web.fyta.de/api"
FYTA_AUTH_ENDPOINT = f"{FYTA_BASE_URL}/auth/login"
FYTA_USER_PLANT_ENDPOINT = f"{FYTA_BASE_URL}/user-plant"


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
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


def create_fyta_server(email: str, password: str) -> Server:
    """Create and configure the FYTA MCP server"""
    
    server = Server("fyta-mcp-server")
    fyta_client = FytaClient(email, password)
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available FYTA tools"""
        return [
            Tool(
                name="get_all_plants",
                description=(
                    "Get all plants with their current sensor data including "
                    "moisture, temperature, light, and nutrient status. "
                    "Returns comprehensive data about each plant including status, "
                    "sensor readings, and garden information."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_plant_details",
                description=(
                    "Get detailed information about a specific plant by ID. "
                    "Includes scientific name, nickname, sensor data, status "
                    "indicators, and optimal conditions."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "plant_id": {
                            "type": "number",
                            "description": "The ID of the plant to retrieve"
                        }
                    },
                    "required": ["plant_id"]
                }
            ),
            Tool(
                name="get_plants_needing_attention",
                description=(
                    "Get a list of plants that need attention based on their "
                    "status indicators. Returns plants with non-optimal moisture, "
                    "temperature, light, or nutrient levels (status != 2)."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_garden_overview",
                description=(
                    "Get an overview of all gardens with plant counts and summary. "
                    "Organizes plants by their assigned gardens."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Any) -> list[TextContent]:
        """Handle tool calls"""
        
        try:
            if name == "get_all_plants":
                data = await fyta_client.get_plants()
                
                # Format the response nicely
                plants = data.get("plants", [])
                gardens = data.get("gardens", [])
                
                result = {
                    "total_plants": len(plants),
                    "total_gardens": len(gardens),
                    "gardens": gardens,
                    "plants": plants
                }
                
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            
            elif name == "get_plant_details":
                plant_id = int(arguments["plant_id"])
                plant = await fyta_client.get_plant_by_id(plant_id)
                
                if not plant:
                    return [TextContent(
                        type="text",
                        text=f"Plant with ID {plant_id} not found"
                    )]
                
                # Interpret status values (1=low, 2=optimal, 3=high)
                status_map = {1: "Low", 2: "Optimal", 3: "High"}
                
                formatted_plant = {
                    "id": plant["id"],
                    "nickname": plant["nickname"],
                    "scientific_name": plant["scientific_name"],
                    "overall_status": plant["status"],
                    "sensor_status": {
                        "temperature": {
                            "status": status_map.get(plant["temperature_status"], "Unknown"),
                            "optimal_hours": plant["temperature_optimal_hours"]
                        },
                        "light": {
                            "status": status_map.get(plant["light_status"], "Unknown"),
                            "optimal_hours": plant["light_optimal_hours"]
                        },
                        "moisture": status_map.get(plant["moisture_status"], "Unknown"),
                        "nutrients": status_map.get(plant["salinity_status"], "Unknown")
                    },
                    "sensor_info": plant.get("sensor", {}),
                    "last_data_received": plant.get("received_data_at"),
                    "wifi_status": "Connected" if plant.get("wifi_status") == 1 else "Disconnected",
                    "images": {
                        "plant_thumb": plant.get("plant_thumb_path"),
                        "plant_full": plant.get("plant_origin_path"),
                        "user_thumb": plant.get("thumb_path"),
                        "user_full": plant.get("origin_path")
                    },
                    "garden_id": plant.get("garden", {}).get("id")
                }
                
                return [TextContent(
                    type="text",
                    text=json.dumps(formatted_plant, indent=2)
                )]
            
            elif name == "get_plants_needing_attention":
                data = await fyta_client.get_plants()
                plants = data.get("plants", [])
                
                # Filter plants that need attention (any status != 2)
                needs_attention = []
                for plant in plants:
                    issues = []
                    if plant["temperature_status"] != 2:
                        status_desc = "too low" if plant["temperature_status"] == 1 else "too high"
                        issues.append(f"Temperature {status_desc}")
                    if plant["light_status"] != 2:
                        status_desc = "too low" if plant["light_status"] == 1 else "too high"
                        issues.append(f"Light {status_desc}")
                    if plant["moisture_status"] != 2:
                        status_desc = "too low" if plant["moisture_status"] == 1 else "too high"
                        issues.append(f"Moisture {status_desc}")
                    if plant["salinity_status"] != 2:
                        status_desc = "too low" if plant["salinity_status"] == 1 else "too high"
                        issues.append(f"Nutrients {status_desc}")
                    
                    if issues:
                        needs_attention.append({
                            "id": plant["id"],
                            "nickname": plant["nickname"],
                            "scientific_name": plant["scientific_name"],
                            "issues": issues,
                            "last_data": plant.get("received_data_at")
                        })
                
                result = {
                    "plants_needing_attention": len(needs_attention),
                    "plants": needs_attention
                }
                
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            
            elif name == "get_garden_overview":
                data = await fyta_client.get_plants()
                plants = data.get("plants", [])
                gardens = data.get("gardens", [])
                
                # Organize plants by garden
                garden_map = {g["id"]: {**g, "plants": []} for g in gardens}
                
                for plant in plants:
                    garden_id = plant.get("garden", {}).get("id")
                    if garden_id in garden_map:
                        garden_map[garden_id]["plants"].append({
                            "id": plant["id"],
                            "nickname": plant["nickname"],
                            "status": plant["status"],
                            "has_sensor": plant.get("sensor", {}).get("has_sensor", False)
                        })
                
                result = {
                    "total_gardens": len(gardens),
                    "gardens": [
                        {
                            "id": gid,
                            "name": ginfo["garden_name"],
                            "plant_count": len(ginfo["plants"]),
                            "plants": ginfo["plants"]
                        }
                        for gid, ginfo in garden_map.items()
                    ]
                }
                
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            
            else:
                return [TextContent(
                    type="text",
                    text=f"Unknown tool: {name}"
                )]
        
        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            return [TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]
    
    return server


async def main():
    """Main entry point"""
    import os
    import sys
    
    # Get credentials from environment variables
    email = os.getenv("FYTA_EMAIL")
    password = os.getenv("FYTA_PASSWORD")
    
    if not email or not password:
        logger.error("FYTA_EMAIL and FYTA_PASSWORD environment variables must be set")
        sys.exit(1)
    
    logger.info("Starting FYTA MCP Server...")
    server = create_fyta_server(email, password)
    
    # Run the server
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
