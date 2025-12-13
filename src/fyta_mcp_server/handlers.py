"""
Tool Handler Implementation
"""
import json
import logging
from typing import Any

from mcp.types import TextContent

from .client import FytaClient

logger = logging.getLogger("fyta-mcp-server")


async def handle_get_all_plants(fyta_client: FytaClient, arguments: Any) -> list[TextContent]:
    """Handle get_all_plants tool call"""
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


async def handle_get_plant_details(fyta_client: FytaClient, arguments: Any) -> list[TextContent]:
    """Handle get_plant_details tool call"""
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


async def handle_get_plants_needing_attention(fyta_client: FytaClient, arguments: Any) -> list[TextContent]:
    """Handle get_plants_needing_attention tool call"""
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


async def handle_get_garden_overview(fyta_client: FytaClient, arguments: Any) -> list[TextContent]:
    """Handle get_garden_overview tool call"""
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


async def handle_get_plant_measurements(fyta_client: FytaClient, arguments: Any) -> list[TextContent]:
    """Handle get_plant_measurements tool call"""
    plant_id = int(arguments["plant_id"])
    timeline = arguments.get("timeline", "month")  # Default to "month"

    try:
        measurements = await fyta_client.get_plant_measurements(plant_id, timeline)

        return [TextContent(
            type="text",
            text=json.dumps(measurements, indent=2)
        )]
    except Exception as e:
        # If plant not found or no measurements available
        return [TextContent(
            type="text",
            text=f"Could not retrieve measurements for plant {plant_id}: {str(e)}"
        )]


# Tool handler mapping
TOOL_HANDLERS = {
    "get_all_plants": handle_get_all_plants,
    "get_plant_details": handle_get_plant_details,
    "get_plants_needing_attention": handle_get_plants_needing_attention,
    "get_garden_overview": handle_get_garden_overview,
    "get_plant_measurements": handle_get_plant_measurements,
}


async def handle_tool_call(name: str, arguments: Any, fyta_client: FytaClient) -> list[TextContent]:
    """Route tool calls to appropriate handlers"""
    handler = TOOL_HANDLERS.get(name)

    if not handler:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]

    try:
        return await handler(fyta_client, arguments)
    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]
