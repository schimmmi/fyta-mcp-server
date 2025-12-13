"""
MCP Tool Definitions
"""
from mcp.types import Tool


def get_tool_definitions() -> list[Tool]:
    """Get list of all available MCP tools"""
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
