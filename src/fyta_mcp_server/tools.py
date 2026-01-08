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
        Tool(
            name="get_plant_measurements",
            description=(
                "Get historical measurements and sensor data for a specific plant by ID. "
                "Returns time-series data including temperature, light, moisture, and "
                "nutrient measurements over time. Useful for tracking trends and plant health history. "
                "You can specify a timeline (hour, day, week, month) to control the time range."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "plant_id": {
                        "type": "number",
                        "description": "The ID of the plant to retrieve measurements for"
                    },
                    "timeline": {
                        "type": "string",
                        "description": "Time range for measurements: 'hour', 'day', 'week', or 'month' (default: 'month')",
                        "enum": ["hour", "day", "week", "month"]
                    }
                },
                "required": ["plant_id"]
            }
        ),
        Tool(
            name="diagnose_plant",
            description=(
                "Perform intelligent health diagnosis for a specific plant. "
                "Analyzes current sensor status, historical trends, and thresholds to provide: "
                "- Overall health assessment (critical/poor/fair/good/excellent) "
                "- Main issues identified with detailed explanations "
                "- Trend analysis from historical data "
                "- Confidence score based on data quality and recency "
                "This is the most powerful tool for understanding plant health and automation decisions."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "plant_id": {
                        "type": "number",
                        "description": "The ID of the plant to diagnose"
                    },
                    "include_recommendations": {
                        "type": "boolean",
                        "description": "Include actionable care recommendations (default: true)"
                    }
                },
                "required": ["plant_id"]
            }
        ),
        Tool(
            name="get_plant_trends",
            description=(
                "Analyze historical trends for a specific plant's sensor data. "
                "Calculates slopes, direction, and forecasts for temperature, light, moisture, and nutrients. "
                "Helps predict issues before they become critical: "
                "- Detects declining moisture before soil dries out completely "
                "- Identifies gradual temperature changes "
                "- Predicts when intervention is needed "
                "- Reduces false alarms by analyzing patterns over time "
                "Essential for proactive plant care and automation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "plant_id": {
                        "type": "number",
                        "description": "The ID of the plant to analyze"
                    },
                    "metric": {
                        "type": "string",
                        "description": "Specific metric to analyze (temperature/light/moisture/nutrients) or 'all' for complete analysis",
                        "enum": ["temperature", "light", "moisture", "nutrients", "all"]
                    },
                    "timeframe": {
                        "type": "string",
                        "description": "Time range for trend analysis: 'hour', 'day', 'week', or 'month' (default: 'week')",
                        "enum": ["hour", "day", "week", "month"]
                    }
                },
                "required": ["plant_id"]
            }
        ),
        Tool(
            name="get_plant_statistics",
            description=(
                "Comprehensive statistical analysis of plant sensor data. "
                "Provides deep insights into historical patterns and behaviors: "
                "- Descriptive statistics (mean, median, std deviation, min/max, percentiles) "
                "- Anomaly detection (outliers, unusual patterns) "
                "- Optimal ranges derived from actual plant performance "
                "- Variability analysis (stability vs fluctuations) "
                "- Correlation analysis between different metrics "
                "- Day/night cycle patterns "
                "Perfect for understanding plant behavior patterns and setting realistic thresholds."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "plant_id": {
                        "type": "number",
                        "description": "The ID of the plant to analyze"
                    },
                    "timeframe": {
                        "type": "string",
                        "description": "Time range for statistical analysis: 'day', 'week', or 'month' (default: 'month')",
                        "enum": ["day", "week", "month"]
                    },
                    "include_correlations": {
                        "type": "boolean",
                        "description": "Include correlation analysis between metrics (default: false)"
                    }
                },
                "required": ["plant_id"]
            }
        ),
        Tool(
            name="get_plant_dli_analysis",
            description=(
                "Advanced DLI (Daily Light Integral) analysis - goes beyond basic FYTA data. "
                "Provides intelligent light management insights: "
                "- Daily DLI calculations and trends over time "
                "- Chronic deficit detection (days/weeks below optimal) "
                "- Precise grow light recommendations with specs and costs "
                "- Seasonal predictions (next 3 months forecast) "
                "- Energy cost estimates for supplemental lighting "
                "- Placement and duration recommendations "
                "This is THE tool for optimizing plant lighting and avoiding light stress."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "plant_id": {
                        "type": "number",
                        "description": "The ID of the plant to analyze"
                    },
                    "timeframe": {
                        "type": "string",
                        "description": "Time range for DLI analysis: 'week' or 'month' (default: 'week')",
                        "enum": ["week", "month"]
                    },
                    "include_grow_light_recommendations": {
                        "type": "boolean",
                        "description": "Include detailed grow light product recommendations (default: true)"
                    }
                },
                "required": ["plant_id"]
            }
        ),
        Tool(
            name="log_plant_care_action",
            description=(
                "Log manual care actions that FYTA doesn't track automatically. "
                "Track watering, fertilizing, repotting, pruning, and more. "
                "This fills FYTA's biggest gap - knowing what YOU did! "
                "Enables: "
                "- Correlation analysis (Did watering help?) "
                "- Frequency tracking (Water every X days) "
                "- Smart recommendations based on YOUR care history "
                "- Learning what works for YOUR plants "
                "Essential for closing the feedback loop and improving care over time."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "plant_id": {
                        "type": "number",
                        "description": "The ID of the plant"
                    },
                    "action_type": {
                        "type": "string",
                        "description": "Type of care action performed",
                        "enum": ["watering", "fertilizing", "repotting", "pruning", "misting",
                                "cleaning", "rotating", "pest_treatment", "other"]
                    },
                    "amount": {
                        "type": "string",
                        "description": "Amount (e.g., '500ml', '2 cups', 'thorough')"
                    },
                    "product": {
                        "type": "string",
                        "description": "Product used (fertilizer brand, pest treatment, etc.)"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional notes or observations"
                    }
                },
                "required": ["plant_id", "action_type"]
            }
        ),
        Tool(
            name="get_plant_care_history",
            description=(
                "Get care action history and intelligent analysis. "
                "Shows: "
                "- Complete care timeline "
                "- Watering frequency analysis "
                "- Effectiveness correlation (Did it work?) "
                "- Smart recommendations based on YOUR data "
                "- Care insights (e.g., 'water more thoroughly', 'fertilize soon') "
                "This tool learns from YOUR care actions and helps optimize your routine."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "plant_id": {
                        "type": "number",
                        "description": "The ID of the plant"
                    },
                    "days": {
                        "type": "number",
                        "description": "Limit to last N days (default: all history)"
                    },
                    "action_type": {
                        "type": "string",
                        "description": "Filter by action type",
                        "enum": ["watering", "fertilizing", "repotting", "pruning", "misting",
                                "cleaning", "rotating", "pest_treatment", "other"]
                    },
                    "include_analysis": {
                        "type": "boolean",
                        "description": "Include effectiveness analysis and recommendations (default: true)"
                    }
                },
                "required": ["plant_id"]
            }
        ),
        Tool(
            name="get_plant_events",
            description=(
                "Real-time event detection and automation triggers - the DevOps heart of plant care! "
                "Detects actionable events for automation systems (n8n, Home Assistant, Telegram, Jenkins): "
                "- Status transitions (Low → TooLow, Optimal → Low, etc.) "
                "- Sensor silence alerts (>90min no data) "
                "- Battery low warnings (<20%) "
                "- WiFi disconnection detection "
                "- Critical moisture alerts (needs water NOW!) "
                "- Temperature extremes (heat stress) "
                "Perfect for: webhooks, push notifications, automated actions. "
                "Returns webhook-ready JSON with severity, priority, and actionable suggestions."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "plant_id": {
                        "type": "number",
                        "description": "Optional: Filter events for specific plant ID. Omit to get events for all plants."
                    },
                    "severity": {
                        "type": "string",
                        "description": "Filter by severity: 'critical', 'warning', or 'info'",
                        "enum": ["critical", "warning", "info"]
                    },
                    "priority": {
                        "type": "string",
                        "description": "Filter by priority: 'immediate', 'high', 'medium', or 'low'",
                        "enum": ["immediate", "high", "medium", "low"]
                    },
                    "event_type": {
                        "type": "string",
                        "description": "Filter by event type: status_change, sensor_silence, battery_low, etc.",
                        "enum": ["status_change", "sensor_silence", "battery_low", "wifi_disconnected",
                                "critical_moisture", "temperature_extreme"]
                    },
                    "actionable_only": {
                        "type": "boolean",
                        "description": "Return only events that require action (default: false)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="set_plant_context",
            description=(
                "Set context information for a plant that FYTA doesn't know about. "
                "Store critical setup details to get context-aware recommendations: "
                "- Substrate type (mineral, organic, lechuza_pon, hydroponic, semi_hydro) "
                "- Container type (lechuza, self_watering, terracotta, plastic) "
                "- Growth phase (seedling, vegetative, flowering, fruiting, dormant) "
                "- Special care requirements or notes "
                "This enables intelligent sensor interpretation: "
                "- 'Low moisture' in Lechuza-PON is often NORMAL (wicks from reservoir) "
                "- Terracotta dries faster than plastic (expected behavior) "
                "- Flowering plants need MORE light than vegetative phase "
                "- Mineral substrates require frequent fertilizing "
                "Essential for getting accurate recommendations for YOUR specific setup!"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "plant_id": {
                        "type": "number",
                        "description": "The ID of the plant"
                    },
                    "substrate": {
                        "type": "string",
                        "description": "Substrate/growing medium type",
                        "enum": ["mineral", "organic", "lechuza_pon", "hydroponic", "semi_hydro"]
                    },
                    "container": {
                        "type": "string",
                        "description": "Container/pot type",
                        "enum": ["lechuza", "self_watering", "terracotta", "plastic"]
                    },
                    "growth_phase": {
                        "type": "string",
                        "description": "Current growth phase",
                        "enum": ["seedling", "vegetative", "flowering", "fruiting", "dormant"]
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional context or special care requirements"
                    }
                },
                "required": ["plant_id"]
            }
        ),
        Tool(
            name="get_plant_context",
            description=(
                "Get stored context and context-aware recommendations for a plant. "
                "Returns: "
                "- All stored context (substrate, container, growth phase) "
                "- Context-aware sensor interpretations "
                "- Adjusted recommendations based on YOUR setup "
                "- Specific care advice for YOUR substrate/container/phase "
                "Example: Instead of generic 'moisture low' warning, get: "
                "'Lechuza-PON often shows low at surface while reservoir is full - check water indicator!' "
                "This tool makes FYTA recommendations accurate for YOUR specific growing conditions."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "plant_id": {
                        "type": "number",
                        "description": "The ID of the plant"
                    }
                },
                "required": ["plant_id"]
            }
        ),
        Tool(
            name="get_fyta_raw_data",
            description=(
                "Get raw FYTA API response data including all available fields. "
                "This returns the complete, unfiltered API response which may include: "
                "- Plants data (detailed sensor readings) "
                "- Gardens data (garden organization) "
                "- Hubs data (FYTA Hub status and information) "
                "- Devices data (sensor devices, firmware versions, connectivity) "
                "- Any other metadata provided by FYTA API "
                "Useful for debugging, discovering new API features, or accessing "
                "data not yet exposed through specialized tools."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_all_hubs",
            description=(
                "Get status and information about all FYTA Hubs in your account. "
                "Returns comprehensive hub data including: "
                "- Hub ID and name "
                "- Firmware version "
                "- Online/offline status "
                "- Last data received timestamp "
                "- Connected plants/sensors "
                "- Connectivity health indicators "
                "Use this to monitor hub health, diagnose connectivity issues, "
                "or check for firmware updates."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_hub_details",
            description=(
                "Get detailed information about a specific FYTA Hub. "
                "Includes: "
                "- Hub specifications (ID, name, MAC address, version) "
                "- Current status and uptime "
                "- All plants/sensors connected to this hub "
                "- Connectivity metrics (last seen, data reception) "
                "- Lost connection warnings "
                "Perfect for troubleshooting hub-specific issues."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "hub_id": {
                        "type": "string",
                        "description": "The MAC address/ID of the hub (e.g., 'E8:06:90:C4:B7:EE')"
                    }
                },
                "required": ["hub_id"]
            }
        ),
    ]
