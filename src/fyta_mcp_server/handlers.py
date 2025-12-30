"""
Tool Handler Implementation - Refactored
Imports handlers from specialized modules for better organization
"""
import json
import logging
from datetime import datetime
from typing import Any, Optional

from mcp.types import TextContent

from .client import FytaClient
from .utils.statistics import (
    calculate_statistics,
    detect_anomalies,
    calculate_correlation,
    analyze_stability
)
from .utils.trends import calculate_trend, predict_critical_time
from .utils.dli import (
    calculate_daily_dlis,
    classify_dli_status,
    analyze_dli_trend,
    calculate_grow_light_needs,
    predict_seasonal_dli
)
from .utils.events import (
    detect_all_events,
    filter_events,
    format_event_for_webhook
)
from .utils.care_actions import (
    CareActionStore,
    analyze_watering_effectiveness,
    calculate_watering_frequency,
    correlate_fertilizing_with_growth,
    get_care_insights
)
from .utils.plant_context import (
    PlantContextStore,
    get_context_aware_recommendations,
    interpret_sensor_with_context
)
from .utils.thresholds import (
    evaluate_plant_status,
    get_status_emoji,
    get_status_description
)
from .utils.fertilization import (
    get_ec_status,
    analyze_ec_trend,
    get_fertilization_recommendation
)
from .utils.watering import (
    get_moisture_status,
    analyze_moisture_trend,
    get_watering_recommendation
)
from .utils.sensor_info import (
    get_sensor_info,
    check_light_capability,
    get_available_analyses
)

# Initialize singletons
care_store = CareActionStore()
context_store = PlantContextStore()

logger = logging.getLogger("fyta-mcp-server")


# ============================================================================
# BASIC PLANT HANDLERS
# ============================================================================

async def handle_get_all_plants(fyta_client: FytaClient, arguments: Any) -> list[TextContent]:
    """Handle get_all_plants tool call - returns LLM-friendly enriched data"""
    data = await fyta_client.get_plants()

    plants = data.get("plants", [])
    gardens = data.get("gardens", [])

    # Create garden lookup map
    garden_map = {g["id"]: g["garden_name"] for g in gardens}

    # Enrich plants with LLM-friendly data
    enriched_plants = []
    for plant in plants:
        # === APPLY SMART STATUS EVALUATION ===
        # Get measurements for smart threshold evaluation
        measurements_week = None
        try:
            measurements_week = await fyta_client.get_plant_measurements(plant["id"], "week")
        except Exception as e:
            logger.warning(f"Could not get measurements for plant {plant['id']}: {e}")

        # Enrich plant object with latest measurement values
        # IMPORTANT: Plant object only has status codes, actual values come from measurements!
        enriched_plant_data = plant.copy()
        # Remove potentially stale values from plant object
        enriched_plant_data.pop("temperature", None)
        enriched_plant_data.pop("moisture", None)
        enriched_plant_data.pop("soil_moisture", None)
        enriched_plant_data.pop("light", None)
        enriched_plant_data.pop("salinity", None)
        enriched_plant_data.pop("soil_fertility", None)

        if measurements_week:
            measurements_list = extract_measurements_from_response(measurements_week)
            if measurements_list:
                latest = get_latest_measurement(measurements_list)
                enriched_plant_data["temperature"] = latest.get("temperature")
                enriched_plant_data["light"] = latest.get("light")
                enriched_plant_data["soil_moisture"] = latest.get("soil_moisture") or latest.get("moisture")
                enriched_plant_data["soil_fertility"] = latest.get("soil_fertility") or latest.get("salinity")

        # Use smart status evaluation to fix FYTA's buggy status codes
        smart_status = evaluate_plant_status(enriched_plant_data, measurements_week)

        # Extract status codes from smart evaluation
        temp_status = smart_status.get("temperature", {})
        temp_status_code = temp_status.get("status", 2) if isinstance(temp_status, dict) else plant.get("temperature_status", 2)

        light_status = smart_status.get("light", {})
        light_status_code = light_status.get("status", 2) if isinstance(light_status, dict) else plant.get("light_status", 2)

        moisture_status = smart_status.get("moisture", {})
        moisture_status_code = moisture_status.get("status", 2) if isinstance(moisture_status, dict) else plant.get("moisture_status", 2)

        nutrients_status = smart_status.get("nutrients", {})
        nutrients_status_code = nutrients_status.get("status", 2) if isinstance(nutrients_status, dict) else plant.get("salinity_status", 2)

        # Calculate minutes since last update
        last_update_minutes = None
        if plant.get("received_data_at"):
            try:
                last_update = datetime.fromisoformat(plant["received_data_at"].replace("Z", "+00:00"))
                now = datetime.now(last_update.tzinfo)
                delta = now - last_update
                last_update_minutes = int(delta.total_seconds() / 60)
            except Exception:
                pass

        # Determine overall status using smart evaluation results
        statuses = [temp_status_code, light_status_code, moisture_status_code, nutrients_status_code]

        if all(s == 2 for s in statuses):
            overall_status = "good"
        elif any(s == 1 or s == 3 for s in statuses):
            if moisture_status_code == 1 or temp_status_code == 3:
                overall_status = "bad"
            else:
                overall_status = "ok"
        else:
            overall_status = "ok"

        garden_id = plant.get("garden", {}).get("id")
        garden_name = garden_map.get(garden_id, "Unknown")
        has_sensor = plant.get("sensor", {}).get("has_sensor", False)

        enriched_plant = {
            "plantId": plant["id"],
            "nickname": plant.get("nickname", "Unnamed"),
            "scientificName": plant.get("scientific_name", "Unknown"),
            "garden": garden_name,
            "hasSensor": has_sensor,
            "overallStatus": overall_status,
            "lastUpdateMinutesAgo": last_update_minutes,
            "sensorStatus": {
                "temperature": temp_status_code,
                "light": light_status_code,
                "moisture": moisture_status_code,
                "nutrients": nutrients_status_code
            },
            "_raw": plant
        }
        enriched_plants.append(enriched_plant)

    result = {
        "total_plants": len(plants),
        "total_gardens": len(gardens),
        "plants": enriched_plants,
        "_raw_gardens": gardens
    }

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def handle_get_plant_details(fyta_client: FytaClient, arguments: Any) -> list[TextContent]:
    """Handle get_plant_details tool call - uses smart evaluation instead of buggy FYTA status codes"""
    plant_id = int(arguments["plant_id"])
    plant = await fyta_client.get_plant_by_id(plant_id)

    if not plant:
        return [TextContent(type="text", text=f"Plant with ID {plant_id} not found")]

    # === APPLY SMART STATUS EVALUATION ===
    # Get measurements for smart threshold evaluation
    measurements_week = None
    try:
        measurements_week = await fyta_client.get_plant_measurements(plant_id, "week")
    except Exception as e:
        logger.warning(f"Could not get measurements for plant {plant_id}: {e}")

    # Enrich plant object with latest measurement values
    # IMPORTANT: Plant object only has status codes, actual values come from measurements!
    enriched_plant_data = plant.copy()
    # Remove potentially stale values from plant object
    enriched_plant_data.pop("temperature", None)
    enriched_plant_data.pop("moisture", None)
    enriched_plant_data.pop("soil_moisture", None)
    enriched_plant_data.pop("light", None)
    enriched_plant_data.pop("salinity", None)
    enriched_plant_data.pop("soil_fertility", None)

    if measurements_week:
        measurements_list = extract_measurements_from_response(measurements_week)
        if measurements_list:
            latest = measurements_list[-1]
            enriched_plant_data["temperature"] = latest.get("temperature")
            enriched_plant_data["light"] = latest.get("light")
            enriched_plant_data["soil_moisture"] = latest.get("soil_moisture") or latest.get("moisture")
            enriched_plant_data["soil_fertility"] = latest.get("soil_fertility") or latest.get("salinity")

    # Use smart status evaluation to fix FYTA's buggy status codes
    smart_status = evaluate_plant_status(enriched_plant_data, measurements_week)

    # Extract status codes from smart evaluation
    status_map = {1: "Low", 2: "Optimal", 3: "High", 4: "Critical"}

    temp_status = smart_status.get("temperature", {})
    temp_status_code = temp_status.get("status", 2) if isinstance(temp_status, dict) else plant.get("temperature_status", 2)

    light_status = smart_status.get("light", {})
    light_status_code = light_status.get("status", 2) if isinstance(light_status, dict) else plant.get("light_status", 2)

    moisture_status = smart_status.get("moisture", {})
    moisture_status_code = moisture_status.get("status", 2) if isinstance(moisture_status, dict) else plant.get("moisture_status", 2)

    nutrients_status = smart_status.get("nutrients", {})
    nutrients_status_code = nutrients_status.get("status", 2) if isinstance(nutrients_status, dict) else plant.get("salinity_status", 2)

    formatted_plant = {
        "id": plant["id"],
        "nickname": plant["nickname"],
        "scientific_name": plant["scientific_name"],
        "overall_status": plant["status"],
        "sensor_status": {
            "temperature": {
                "status": status_map.get(temp_status_code, "Unknown"),
                "optimal_hours": plant["temperature_optimal_hours"]
            },
            "light": {
                "status": status_map.get(light_status_code, "Unknown"),
                "optimal_hours": plant["light_optimal_hours"]
            },
            "moisture": status_map.get(moisture_status_code, "Unknown"),
            "nutrients": status_map.get(nutrients_status_code, "Unknown")
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

    return [TextContent(type="text", text=json.dumps(formatted_plant, indent=2))]


async def handle_get_plants_needing_attention(fyta_client: FytaClient, arguments: Any) -> list[TextContent]:
    """Handle get_plants_needing_attention tool call - uses smart evaluation instead of buggy FYTA status codes"""
    data = await fyta_client.get_plants()
    plants = data.get("plants", [])

    needs_attention = []
    for plant in plants:
        # === APPLY SMART STATUS EVALUATION ===
        # Get measurements for smart threshold evaluation
        measurements_week = None
        try:
            measurements_week = await fyta_client.get_plant_measurements(plant["id"], "week")
        except Exception as e:
            logger.warning(f"Could not get measurements for plant {plant['id']}: {e}")
            continue  # Skip plant if we can't get measurements

        # Enrich plant object with latest measurement values (plant object only has status codes)
        enriched_plant_data = plant.copy()
        # Remove potentially stale values from plant object
        enriched_plant_data.pop("temperature", None)
        enriched_plant_data.pop("moisture", None)
        enriched_plant_data.pop("soil_moisture", None)
        enriched_plant_data.pop("light", None)
        enriched_plant_data.pop("salinity", None)
        enriched_plant_data.pop("soil_fertility", None)

        if measurements_week:
            measurements_list = extract_measurements_from_response(measurements_week)
            if measurements_list:
                latest = get_latest_measurement(measurements_list)
                # Add actual values from measurements
                enriched_plant_data["temperature"] = latest.get("temperature")
                enriched_plant_data["light"] = latest.get("light")
                enriched_plant_data["soil_moisture"] = latest.get("soil_moisture") or latest.get("moisture")
                enriched_plant_data["soil_fertility"] = latest.get("soil_fertility") or latest.get("salinity")

        # Use smart status evaluation to fix FYTA's buggy status codes
        smart_status = evaluate_plant_status(enriched_plant_data, measurements_week)

        # Build issues list from smart evaluation
        # Note: smart_status returns dicts with {"status": code, "value": value, ...}
        issues = []
        temp_status = smart_status.get("temperature")
        if temp_status and isinstance(temp_status, dict):
            status_code = temp_status.get("status")
            if status_code == 1:
                issues.append("Temperature too low")
            elif status_code == 3:
                issues.append("Temperature too high")

        light_status = smart_status.get("light")
        if light_status and isinstance(light_status, dict):
            status_code = light_status.get("status")
            if status_code == 1:
                issues.append("Light too low")
            elif status_code == 3:
                issues.append("Light too high")

        moisture_status = smart_status.get("moisture")
        if moisture_status and isinstance(moisture_status, dict):
            status_code = moisture_status.get("status")
            if status_code == 1:
                issues.append("Moisture too low")
            elif status_code == 3:
                issues.append("Moisture too high")

        nutrients_status = smart_status.get("nutrients")
        if nutrients_status and isinstance(nutrients_status, dict):
            status_code = nutrients_status.get("status")
            if status_code == 1:
                issues.append("Nutrients too low")
            elif status_code == 3:
                issues.append("Nutrients too high")

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

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def handle_get_garden_overview(fyta_client: FytaClient, arguments: Any) -> list[TextContent]:
    """Handle get_garden_overview tool call"""
    data = await fyta_client.get_plants()
    plants = data.get("plants", [])
    gardens = data.get("gardens", [])

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

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def handle_get_plant_measurements(fyta_client: FytaClient, arguments: Any) -> list[TextContent]:
    """Handle get_plant_measurements tool call"""
    plant_id = int(arguments["plant_id"])
    timeline = arguments.get("timeline", "month")

    try:
        measurements = await fyta_client.get_plant_measurements(plant_id, timeline)
        return [TextContent(type="text", text=json.dumps(measurements, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Could not retrieve measurements for plant {plant_id}: {str(e)}")]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_measurements_from_response(measurements_data: Any) -> list:
    """
    Extract measurements list from FYTA API response.
    The API might return measurements in various structures.
    """
    if isinstance(measurements_data, list):
        return measurements_data

    if not isinstance(measurements_data, dict):
        return []

    # Try common keys
    for key in ["measurements", "data", "items", "results"]:
        if key in measurements_data and isinstance(measurements_data[key], list):
            return measurements_data[key]

    # Try to find any list with measurement-like objects
    for key, value in measurements_data.items():
        if isinstance(value, list) and len(value) > 0:
            # Check if first item looks like a measurement
            first_item = value[0]
            if isinstance(first_item, dict) and any(
                field in first_item for field in ["measured_at", "timestamp", "temperature", "moisture", "light"]
            ):
                logger.info(f"Found measurements in key: {key}")
                return value

    return []


def get_latest_measurement(measurements_list: list) -> Optional[dict]:
    """
    Get the most recent measurement from a list by sorting by timestamp.

    CRITICAL: The FYTA API does NOT return measurements in chronological order!
    We must sort by timestamp to get the actual latest measurement.

    Args:
        measurements_list: List of measurement dicts

    Returns:
        The measurement with the newest timestamp, or None if list is empty
    """
    if not measurements_list:
        return None

    # Sort by timestamp (newest last)
    sorted_measurements = sorted(
        measurements_list,
        key=lambda m: m.get("date_utc", "") or m.get("timestamp", "") or m.get("measured_at", "")
    )

    return sorted_measurements[-1]


def get_timestamp_from_measurement(measurement: dict) -> Optional[str]:
    """
    Extract timestamp from measurement object.
    FYTA API might use different field names.
    """
    # FYTA uses "date_utc" as primary timestamp field
    for field in ["date_utc", "measured_at", "timestamp", "created_at", "date", "time"]:
        if field in measurement and measurement[field]:
            return measurement[field]
    return None


def calculate_severity(current_value: float, status_code: int, thresholds: dict, metric_name: str) -> str:
    """
    Calculate severity based on how far the value is from optimal thresholds.

    Args:
        current_value: The current measured value
        status_code: Status code (1=low, 2=optimal, 3=high)
        thresholds: Dict with min_good and max_good
        metric_name: Name of metric (for specific handling)

    Returns:
        Severity level: "info", "low", "moderate", "high", or "critical"
    """
    if status_code == 2:
        return "info"  # Optimal - no issue

    min_good = thresholds.get("min_good", 0)
    max_good = thresholds.get("max_good", 100)

    # Calculate how far outside the optimal range we are
    if status_code == 1:  # Too low
        if min_good > 0:
            deviation = min_good - current_value
            deviation_percent = (deviation / min_good) * 100
        else:
            deviation_percent = 100  # Can't calculate, assume moderate

        # Moisture is most critical when low!
        if metric_name == "moisture":
            if current_value < 15:  # Critical dehydration
                return "critical"
            elif deviation_percent > 30:  # More than 30% below threshold
                return "high"
            else:
                return "moderate"
        # Temperature/nutrients low is less urgent
        else:
            if deviation_percent > 50:
                return "high"
            elif deviation_percent > 25:
                return "moderate"
            else:
                return "low"

    elif status_code == 3:  # Too high
        if max_good > 0:
            deviation = current_value - max_good
            deviation_percent = (deviation / max_good) * 100
        else:
            deviation_percent = 100

        # Moisture too high = root rot risk
        if metric_name == "moisture":
            if current_value > 90:  # Critical saturation
                return "critical"
            elif deviation_percent > 20:
                return "high"
            else:
                return "moderate"
        # Temperature too high = stress
        elif metric_name == "temperature":
            if deviation_percent > 20:  # More than 20% above threshold
                return "high"
            elif deviation_percent > 10:
                return "moderate"
            else:
                return "low"
        # Nutrients too high
        else:
            if deviation_percent > 50:
                return "high"
            elif deviation_percent > 20:
                return "moderate"
            else:
                return "low"

    return "moderate"  # Default fallback


# ============================================================================
# ANALYSIS HANDLERS (Diagnosis, Trends, Statistics)
# ============================================================================
async def handle_get_plant_trends(fyta_client: FytaClient, arguments: Any) -> list[TextContent]:
    """Handle get_plant_trends tool call - trend analysis and forecasting"""
    from datetime import datetime

    plant_id = int(arguments["plant_id"])
    metric = arguments.get("metric", "all")
    timeframe = arguments.get("timeframe", "week")

    try:
        # Get plant info for context
        plant = await fyta_client.get_plant_by_id(plant_id)
        if not plant:
            return [TextContent(
                type="text",
                text=f"Plant with ID {plant_id} not found"
            )]

        # Get measurements
        measurements_data = await fyta_client.get_plant_measurements(plant_id, timeframe)
        measurements = extract_measurements_from_response(measurements_data)

        if not measurements:
            return [TextContent(
                type="text",
                text=f"No measurement data available for plant {plant_id} in timeframe '{timeframe}'. API response keys: {list(measurements_data.keys()) if isinstance(measurements_data, dict) else 'not a dict'}"
            )]

        # Parse measurement data into time series
        # FYTA API field names: soil_moisture, soil_fertility, temperature, light
        metric_mapping = {
            "temperature": "temperature",
            "light": "light",
            "moisture": "soil_moisture",  # FYTA uses "soil_moisture"
            "nutrients": "soil_fertility"  # FYTA uses "soil_fertility" for nutrients
        }

        result = {
            "plantId": plant_id,
            "plantName": plant.get("nickname", "Unknown"),
            "timeframe": timeframe,
            "dataPoints": len(measurements),
            "trends": {}
        }

        # Metrics to analyze
        metrics_to_analyze = [metric] if metric != "all" else list(metric_mapping.keys())

        for metric_name in metrics_to_analyze:
            api_field = metric_mapping.get(metric_name)
            if not api_field:
                continue

            # Extract time series data
            data_points = []
            for measurement in measurements:
                timestamp_str = get_timestamp_from_measurement(measurement)
                value = measurement.get(api_field)

                if timestamp_str and value is not None:
                    try:
                        # FYTA returns timestamp as string without timezone, assume UTC
                        if "T" in timestamp_str:
                            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                        else:
                            # Handle "2025-12-23 20:00:55" format
                            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

                        # Convert to hours since epoch for easier calculations
                        hours_since_epoch = timestamp.timestamp() / 3600
                        data_points.append((hours_since_epoch, float(value)))
                    except Exception as e:
                        logger.debug(f"Failed to parse timestamp {timestamp_str}: {e}")
                        continue

            if not data_points:
                result["trends"][metric_name] = {
                    "status": "no_data",
                    "message": f"No valid data points for {metric_name}"
                }
                continue

            # Calculate trend
            trend = calculate_trend(data_points)

            # Get current value and status
            current_value = trend["last_value"]
            current_status = plant.get(f"{api_field}_status", 2)

            # Define critical thresholds based on metric
            # These are educated guesses - you might want to get actual min/max from plant data
            critical_thresholds = {
                "moisture": current_value * 0.3,  # 30% of current = critical low
                "temperature": current_value * 1.2 if current_status != 3 else current_value,  # 20% higher
                "light": current_value * 0.5,  # 50% of current = critical low
                "nutrients": current_value * 0.4  # 40% of current
            }

            critical_threshold = critical_thresholds.get(metric_name, current_value * 0.5)

            # Predict when critical threshold will be reached
            prediction = predict_critical_time(trend, current_value, critical_threshold)

            # Build human-readable summary
            if trend["direction"] == "increasing":
                trend_description = f"{metric_name.capitalize()} is increasing at {abs(trend['slope_percent_per_hour'])}% per hour"
            elif trend["direction"] == "decreasing":
                trend_description = f"{metric_name.capitalize()} is decreasing at {abs(trend['slope_percent_per_hour'])}% per hour"
            else:
                trend_description = f"{metric_name.capitalize()} is stable"

            # Add context
            if metric_name == "moisture" and trend["direction"] == "decreasing":
                trend_description += f". Soil moisture has dropped {abs(trend['change_percent'])}% over {timeframe}."
            elif metric_name == "temperature" and trend["direction"] == "increasing":
                trend_description += f". Temperature has risen {trend['change_percent']}% over {timeframe}."

            result["trends"][metric_name] = {
                "current_value": current_value,
                "current_status": current_status,
                "trend": trend,
                "prediction": prediction,
                "description": trend_description,
                "data_quality": "high" if trend["confidence"] > 0.7 else "medium" if trend["confidence"] > 0.4 else "low"
            }

        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    except Exception as e:
        logger.error(f"Error analyzing trends for plant {plant_id}: {e}")
        import traceback
        traceback.print_exc()
        return [TextContent(
            type="text",
            text=f"Error analyzing trends: {str(e)}"
        )]


async def handle_get_plant_statistics(fyta_client: FytaClient, arguments: Any) -> list[TextContent]:
    """Handle get_plant_statistics tool call - comprehensive statistical analysis"""
    from datetime import datetime

    plant_id = int(arguments["plant_id"])
    timeframe = arguments.get("timeframe", "month")
    include_correlations = arguments.get("include_correlations", False)

    try:
        # Get plant info
        plant = await fyta_client.get_plant_by_id(plant_id)
        if not plant:
            return [TextContent(
                type="text",
                text=f"Plant with ID {plant_id} not found"
            )]

        # Get measurements
        measurements_data = await fyta_client.get_plant_measurements(plant_id, timeframe)
        measurements = extract_measurements_from_response(measurements_data)

        if not measurements:
            return [TextContent(
                type="text",
                text=f"No measurement data available for plant {plant_id} in timeframe '{timeframe}'. API response keys: {list(measurements_data.keys()) if isinstance(measurements_data, dict) else 'not a dict'}"
            )]

        # Extract data for each metric
        # FYTA API field names: soil_moisture, soil_fertility, temperature, light
        metric_mapping = {
            "temperature": "temperature",
            "light": "light",
            "moisture": "soil_moisture",  # FYTA uses "soil_moisture"
            "nutrients": "soil_fertility"  # FYTA uses "soil_fertility" for nutrients
        }

        metric_data = {name: [] for name in metric_mapping.keys()}
        timestamps = []

        for measurement in measurements:
            timestamp_str = get_timestamp_from_measurement(measurement)
            if timestamp_str:
                try:
                    # FYTA returns timestamp as string without timezone, assume UTC
                    if "T" in timestamp_str:
                        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                    else:
                        # Handle "2025-12-23 20:00:55" format
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

                    timestamps.append(timestamp)

                    for metric_name, api_field in metric_mapping.items():
                        value = measurement.get(api_field)
                        if value is not None:
                            metric_data[metric_name].append(float(value))
                        else:
                            metric_data[metric_name].append(None)
                except Exception as e:
                    logger.debug(f"Failed to parse measurement: {e}")
                    continue

        # Build result
        result = {
            "plantId": plant_id,
            "plantName": plant.get("nickname", "Unknown"),
            "scientificName": plant.get("scientific_name", "Unknown"),
            "timeframe": timeframe,
            "period": {
                "start": timestamps[0].isoformat() if timestamps else None,
                "end": timestamps[-1].isoformat() if timestamps else None,
                "duration_hours": (timestamps[-1] - timestamps[0]).total_seconds() / 3600 if len(timestamps) > 1 else 0
            },
            "metrics": {}
        }

        # Analyze each metric
        for metric_name, values in metric_data.items():
            # Filter out None values
            clean_values = [v for v in values if v is not None]

            if not clean_values:
                result["metrics"][metric_name] = {
                    "status": "no_data",
                    "message": f"No valid data for {metric_name}"
                }
                continue

            # Calculate statistics
            stats = calculate_statistics(clean_values)

            # Detect anomalies
            anomalies = detect_anomalies(clean_values, threshold_sigma=2.5)

            # Analyze stability
            stability = analyze_stability(clean_values)

            # Determine optimal range (middle 50% = IQR)
            optimal_range = {
                "lower": stats["percentiles"]["p25"],
                "upper": stats["percentiles"]["p75"],
                "interpretation": f"Plant performs best when {metric_name} is between {stats['percentiles']['p25']} and {stats['percentiles']['p75']}"
            }

            # Current status
            current_value = clean_values[-1]
            current_status_code = plant.get(f"{metric_mapping[metric_name]}_status", 2)

            # Interpretation
            if current_value < stats["percentiles"]["p10"]:
                performance = "critically_low"
            elif current_value < stats["percentiles"]["p25"]:
                performance = "below_optimal"
            elif current_value <= stats["percentiles"]["p75"]:
                performance = "optimal"
            elif current_value <= stats["percentiles"]["p90"]:
                performance = "above_optimal"
            else:
                performance = "critically_high"

            result["metrics"][metric_name] = {
                "current_value": round(current_value, 2),
                "current_status": current_status_code,
                "performance": performance,
                "statistics": stats,
                "optimal_range": optimal_range,
                "stability": stability,
                "anomalies": anomalies
            }

        # Correlation analysis (if requested)
        if include_correlations:
            correlations = {}

            metrics = list(metric_mapping.keys())
            for i, metric1 in enumerate(metrics):
                for metric2 in metrics[i+1:]:
                    values1 = [v for v in metric_data[metric1] if v is not None]
                    values2 = [v for v in metric_data[metric2] if v is not None]

                    # Need same length for correlation
                    min_len = min(len(values1), len(values2))
                    if min_len > 2:
                        values1 = values1[:min_len]
                        values2 = values2[:min_len]

                        corr = calculate_correlation(values1, values2)
                        corr_rounded = round(corr, 3)

                        # Interpret correlation
                        if abs(corr_rounded) < 0.3:
                            strength = "weak"
                        elif abs(corr_rounded) < 0.7:
                            strength = "moderate"
                        else:
                            strength = "strong"

                        direction = "positive" if corr_rounded > 0 else "negative"

                        correlations[f"{metric1}_vs_{metric2}"] = {
                            "coefficient": corr_rounded,
                            "strength": strength,
                            "direction": direction,
                            "interpretation": f"{strength.capitalize()} {direction} correlation between {metric1} and {metric2}"
                        }

            result["correlations"] = correlations

        # Overall health assessment based on statistics
        optimal_count = sum(1 for m in result["metrics"].values()
                           if isinstance(m, dict) and m.get("performance") == "optimal")
        total_metrics = len([m for m in result["metrics"].values() if isinstance(m, dict) and "performance" in m])

        if total_metrics > 0:
            optimal_percentage = (optimal_count / total_metrics) * 100
            result["overall_assessment"] = {
                "optimal_metrics": optimal_count,
                "total_metrics": total_metrics,
                "optimal_percentage": round(optimal_percentage, 1),
                "health_score": f"{round(optimal_percentage, 0)}/100"
            }

        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    except Exception as e:
        logger.error(f"Error calculating statistics for plant {plant_id}: {e}")
        import traceback
        traceback.print_exc()
        return [TextContent(
            type="text",
            text=f"Error calculating statistics: {str(e)}"
        )]


async def handle_diagnose_plant(fyta_client: FytaClient, arguments: Any) -> list[TextContent]:
    """Handle diagnose_plant tool call - intelligent health analysis"""
    from datetime import datetime

    plant_id = int(arguments["plant_id"])
    include_recommendations = arguments.get("include_recommendations", True)

    try:
        # Get current plant data
        plant = await fyta_client.get_plant_by_id(plant_id)
        if not plant:
            return [TextContent(
                type="text",
                text=f"Plant with ID {plant_id} not found"
            )]

        # Get historical measurements for trend analysis AND thresholds
        measurements_week = None
        try:
            measurements_week = await fyta_client.get_plant_measurements(plant_id, "week")
        except Exception:
            pass

        # === SMART STATUS EVALUATION ===
        # CRITICAL: Plant object from FYTA API may contain stale/invalid measurement values!
        # The ONLY reliable source for current values is the measurements endpoint!
        # We create a clean dict with ONLY the values from measurements.

        enriched_plant_data = {
            "id": plant.get("id"),
            "nickname": plant.get("nickname"),
            "scientific_name": plant.get("scientific_name"),
            # Keep status codes from plant object (these are semi-reliable)
            "temperature_status": plant.get("temperature_status"),
            "moisture_status": plant.get("moisture_status"),
            "light_status": plant.get("light_status"),
            "salinity_status": plant.get("salinity_status"),
            # Keep other metadata
            "sensor": plant.get("sensor"),
            "thresholds_list": plant.get("thresholds_list"),
            # Measurement values will be added below ONLY if we have them
        }

        if measurements_week:
            measurements_list = extract_measurements_from_response(measurements_week)
            logger.info(f"Plant {plant_id} - Got {len(measurements_list) if measurements_list else 0} measurements")
            if measurements_list:
                # Get the most recent measurement (sorted by timestamp)
                latest = get_latest_measurement(measurements_list)
                logger.info(f"Plant {plant_id} - Latest measurement timestamp: {latest.get('date_utc')}")
                logger.info(f"Plant {plant_id} - Latest measurement keys: {list(latest.keys())}")
                logger.info(f"Plant {plant_id} - Latest measurement values: temp={latest.get('temperature')}, "
                           f"moisture={latest.get('moisture')}, soil_moisture={latest.get('soil_moisture')}, "
                           f"salinity={latest.get('salinity')}, soil_fertility={latest.get('soil_fertility')}")

                # Extract actual measurement values - ONLY add if they exist
                if latest.get("temperature") is not None:
                    enriched_plant_data["temperature"] = latest.get("temperature")
                if latest.get("light") is not None:
                    enriched_plant_data["light"] = latest.get("light")

                moisture_val = latest.get("soil_moisture") or latest.get("moisture")
                if moisture_val is not None:
                    enriched_plant_data["soil_moisture"] = moisture_val
                    enriched_plant_data["moisture"] = moisture_val  # Set both for compatibility

                nutrients_val = latest.get("soil_fertility") or latest.get("salinity")
                if nutrients_val is not None:
                    enriched_plant_data["soil_fertility"] = nutrients_val
                    enriched_plant_data["salinity"] = nutrients_val  # Set both for compatibility

                logger.info(f"Plant {plant_id} - Enriched data after extraction: temp={enriched_plant_data.get('temperature')}, "
                           f"moisture={enriched_plant_data.get('soil_moisture')}, "
                           f"nutrients={enriched_plant_data.get('soil_fertility')}")
        else:
            logger.warning(f"Plant {plant_id} - No measurements_week data available!")

        # Use our intelligent evaluation instead of trusting FYTA's inconsistent status codes
        smart_status = evaluate_plant_status(enriched_plant_data, measurements_week)

        # === ANALYZE CURRENT STATUS ===
        issues = []

        # Use smart status if available, otherwise fallback to FYTA status
        if smart_status.get("use_fyta_status", True):
            status_details = {
                "temperature": plant.get("temperature_status", 2),
                "light": plant.get("light_status", 2),
                "moisture": plant.get("moisture_status", 2),
                "nutrients": plant.get("salinity_status", 2)
            }
        else:
            # Extract status from smart_status with safe defaults
            temp_data = smart_status.get("temperature") or {}
            light_data = smart_status.get("light") or {}
            moisture_data = smart_status.get("moisture") or {}
            nutrients_data = smart_status.get("nutrients") or {}

            status_details = {
                "temperature": temp_data.get("status", 2),
                "light": light_data.get("status", 2),
                "moisture": moisture_data.get("status", 2),
                "nutrients": nutrients_data.get("status", 2)
            }

        # === CHECK SENSOR CAPABILITIES ===
        sensor_info = get_sensor_info(plant)
        light_capability = check_light_capability(plant)

        # Status explanations with severity
        status_names = {1: "low", 2: "optimal", 3: "high"}

        # Temperature analysis
        if status_details["temperature"] != 2:
            # Calculate dynamic severity based on actual value and thresholds
            temp_value = temp_data.get("value") if temp_data else None
            temp_thresholds = temp_data.get("thresholds", {}) if temp_data else {}

            if temp_value is not None and temp_thresholds:
                severity = calculate_severity(temp_value, status_details["temperature"], temp_thresholds, "temperature")
            else:
                # Fallback to old logic if we don't have threshold data
                severity = "critical" if status_details["temperature"] == 3 else "moderate"

            issues.append({
                "parameter": "temperature",
                "status": status_names[status_details["temperature"]],
                "severity": severity,
                "explanation": f"Temperature is {status_names[status_details['temperature']]}. " +
                              ("High temperatures can cause stress and wilting. " if status_details['temperature'] == 3
                               else "Low temperatures slow growth and can damage plant tissue. "),
                "optimal_hours": plant.get("temperature_optimal_hours", 0)
            })

        # Light analysis (only if sensor has light capability)
        if light_capability["capable"]:
            if status_details["light"] != 2:
                # Calculate dynamic severity
                light_value = light_data.get("value") if light_data else None
                light_thresholds = light_data.get("thresholds", {}) if light_data else {}

                if light_value is not None and light_thresholds:
                    severity = calculate_severity(light_value, status_details["light"], light_thresholds, "light")
                else:
                    severity = "high" if status_details["light"] == 1 else "moderate"

                issues.append({
                    "parameter": "light",
                    "status": status_names[status_details["light"]],
                    "severity": severity,
                    "explanation": f"Light is {status_names[status_details['light']]}. " +
                                  ("Insufficient light reduces photosynthesis and weakens the plant. " if status_details['light'] == 1
                                   else "Too much direct light can cause leaf burn. "),
                    "optimal_hours": plant.get("light_optimal_hours", 0)
                })
        else:
            # Add informational note about missing light sensor
            issues.append({
                "parameter": "light",
                "status": "unavailable",
                "severity": "info",
                "explanation": light_capability["message"],
                "recommendation": light_capability.get("recommendation"),
                "optimal_hours": None
            })

        # Moisture analysis (most critical!)
        if status_details["moisture"] != 2:
            # Calculate dynamic severity
            moisture_value = moisture_data.get("value") if moisture_data else None
            moisture_thresholds = moisture_data.get("thresholds", {}) if moisture_data else {}

            if moisture_value is not None and moisture_thresholds:
                severity = calculate_severity(moisture_value, status_details["moisture"], moisture_thresholds, "moisture")
            else:
                severity = "critical" if status_details["moisture"] == 1 else "high"

            issues.append({
                "parameter": "moisture",
                "status": status_names[status_details["moisture"]],
                "severity": severity,
                "explanation": f"Soil moisture is {status_names[status_details['moisture']]}. " +
                              ("Dry soil can cause wilting and root damage. Immediate watering needed! " if status_details['moisture'] == 1
                               else "Overwatering can lead to root rot. Reduce watering frequency. "),
                "optimal_hours": plant.get("moisture_optimal_hours", 0) if plant.get("moisture_optimal_hours") else None
            })

        # Nutrients analysis
        if status_details["nutrients"] != 2:
            # Calculate dynamic severity
            nutrients_value = nutrients_data.get("value") if nutrients_data else None
            nutrients_thresholds = nutrients_data.get("thresholds", {}) if nutrients_data else {}

            if nutrients_value is not None and nutrients_thresholds:
                severity = calculate_severity(nutrients_value, status_details["nutrients"], nutrients_thresholds, "nutrients")
            else:
                severity = "moderate" if status_details["nutrients"] == 1 else "high"

            issues.append({
                "parameter": "nutrients",
                "status": status_names[status_details["nutrients"]],
                "severity": severity,
                "explanation": f"Nutrient level (salinity) is {status_names[status_details['nutrients']]}. " +
                              ("Low nutrients affect growth and leaf color. Consider fertilizing. " if status_details['nutrients'] == 1
                               else "High salt concentration can damage roots. Flush soil with water. "),
                "optimal_hours": plant.get("salinity_optimal_hours", 0) if plant.get("salinity_optimal_hours") else None
            })

        # === DETERMINE OVERALL HEALTH ===
        critical_issues = [i for i in issues if i["severity"] == "critical"]
        high_issues = [i for i in issues if i["severity"] == "high"]
        moderate_issues = [i for i in issues if i["severity"] == "moderate"]

        if critical_issues:
            health = "critical"
        elif len(high_issues) >= 2:
            health = "poor"
        elif len(high_issues) == 1 or len(moderate_issues) >= 2:
            health = "fair"
        elif len(moderate_issues) == 1:
            health = "good"
        else:
            health = "excellent"

        # === CALCULATE CONFIDENCE SCORE ===
        confidence = 1.0
        confidence_factors = []

        # Check sensor availability
        has_sensor = plant.get("sensor", {}).get("has_sensor", False)
        if not has_sensor:
            confidence *= 0.5
            confidence_factors.append("No active sensor")

        # Check data recency
        last_update = plant.get("received_data_at")
        if last_update:
            try:
                last_update_dt = datetime.fromisoformat(last_update.replace("Z", "+00:00"))
                now = datetime.now(last_update_dt.tzinfo)
                hours_ago = (now - last_update_dt).total_seconds() / 3600

                if hours_ago > 24:
                    confidence *= 0.8
                    confidence_factors.append(f"Data is {int(hours_ago)} hours old")
                elif hours_ago > 48:
                    confidence *= 0.6
                    confidence_factors.append(f"Data is {int(hours_ago/24)} days old")
            except Exception:
                confidence *= 0.7
                confidence_factors.append("Could not parse update timestamp")
        else:
            confidence *= 0.6
            confidence_factors.append("No recent data timestamp")

        # Check if we have historical data
        if measurements_week:
            confidence *= 1.1  # Boost confidence if we have trends
            confidence = min(confidence, 1.0)  # Cap at 1.0
        else:
            confidence *= 0.9
            confidence_factors.append("No historical trend data available")

        # === BUILD EXPLANATIONS ===
        explanations = {}
        for issue in issues:
            param = issue["parameter"]
            explanations[param] = issue["explanation"]
            if issue["optimal_hours"] is not None and issue["optimal_hours"] > 0:
                explanations[param] += f" Currently optimal for {issue['optimal_hours']}h/day."

        # === TREND ANALYSIS ===
        trends = {}
        if measurements_week and "measurements" in measurements_week:
            # Perform detailed trend analysis for critical metrics
            measurements = measurements_week["measurements"]

            for metric_name, api_field in [("moisture", "moisture"), ("temperature", "temperature")]:
                data_points = []
                for measurement in measurements:
                    timestamp_str = measurement.get("measured_at")
                    value = measurement.get(api_field)

                    if timestamp_str and value is not None:
                        try:
                            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                            hours_since_epoch = timestamp.timestamp() / 3600
                            data_points.append((hours_since_epoch, float(value)))
                        except Exception:
                            continue

                if data_points:
                    trend = calculate_trend(data_points)

                    # Predict critical times for moisture (most important)
                    if metric_name == "moisture" and trend["direction"] == "decreasing":
                        current_moisture = trend["last_value"]
                        critical_threshold = current_moisture * 0.3
                        prediction = predict_critical_time(trend, current_moisture, critical_threshold)

                        trends[metric_name] = {
                            "direction": trend["direction"],
                            "change_percent": trend["change_percent"],
                            "prediction": prediction,
                            "summary": f"Moisture {trend['direction']} by {abs(trend['change_percent'])}% over past week. {prediction['message']}"
                        }
                    elif metric_name == "temperature":
                        trends[metric_name] = {
                            "direction": trend["direction"],
                            "change_percent": trend["change_percent"],
                            "summary": f"Temperature {trend['direction']} by {abs(trend['change_percent'])}% over past week."
                        }

        # === RECOMMENDATIONS ===
        recommendations = []
        if include_recommendations:
            for issue in sorted(issues, key=lambda x: {"critical": 0, "high": 1, "moderate": 2, "info": 3}.get(x["severity"], 4)):
                param = issue["parameter"]
                status = issue["status"]

                if param == "moisture" and status == "low":
                    recommendations.append({
                        "priority": "immediate",
                        "action": "Water the plant",
                        "details": "Check soil moisture with finger. Water thoroughly until it drains from bottom."
                    })
                elif param == "moisture" and status == "high":
                    recommendations.append({
                        "priority": "high",
                        "action": "Stop watering",
                        "details": "Let soil dry out. Check for proper drainage. Consider repotting if root rot suspected."
                    })
                elif param == "light" and status == "low":
                    recommendations.append({
                        "priority": "high",
                        "action": "Increase light exposure",
                        "details": "Move plant closer to window or add grow light. Aim for bright indirect light."
                    })
                elif param == "light" and status == "high":
                    recommendations.append({
                        "priority": "medium",
                        "action": "Reduce direct sunlight",
                        "details": "Move plant away from direct sun or use sheer curtain to filter light."
                    })
                elif param == "temperature" and status == "high":
                    recommendations.append({
                        "priority": "high",
                        "action": "Cool down environment",
                        "details": "Move plant to cooler location, increase ventilation, or mist leaves."
                    })
                elif param == "temperature" and status == "low":
                    recommendations.append({
                        "priority": "medium",
                        "action": "Warm up environment",
                        "details": "Move away from cold drafts/windows. Maintain stable room temperature."
                    })
                elif param == "nutrients" and status == "low":
                    recommendations.append({
                        "priority": "low",
                        "action": "Fertilize plant",
                        "details": "Apply balanced liquid fertilizer according to package instructions."
                    })
                elif param == "nutrients" and status == "high":
                    recommendations.append({
                        "priority": "medium",
                        "action": "Flush excess nutrients",
                        "details": "Water thoroughly multiple times to leach out excess salts from soil."
                    })

        # === BUILD RESULT ===
        result = {
            "plantId": plant_id,
            "plantName": plant.get("nickname", "Unknown"),
            "scientificName": plant.get("scientific_name", "Unknown"),
            "health": health,
            "mainIssues": [i["parameter"] for i in issues],
            "issueDetails": issues,
            "explanations": explanations,
            "confidence": round(confidence, 2),
            "confidenceFactors": confidence_factors if confidence < 1.0 else ["High quality recent data"],
            "dataAge": {
                "lastUpdate": last_update,
                "hasSensor": has_sensor
            },
            "sensorStatus": status_details,
            "sensorInfo": sensor_info,
            "lightCapability": light_capability,
            "evaluation": {
                "method": smart_status.get("evaluation_method", "fyta"),
                "smart_status": smart_status if not smart_status["use_fyta_status"] else None
            }
        }

        if include_recommendations:
            result["recommendations"] = recommendations

        if trends:
            result["trends"] = trends

        # === INTELLIGENT FERTILIZATION RECOMMENDATION ===
        # Get current EC value from latest measurement
        current_ec = None
        measurements_list = []
        if measurements_week:
            measurements_list = extract_measurements_from_response(measurements_week)
            logger.info(f"Extracted {len(measurements_list)} measurements for fertilization analysis")
            if measurements_list:
                # Get most recent measurement
                latest = get_latest_measurement(measurements_list)
                current_ec = latest.get("soil_fertility") or latest.get("salinity")
                logger.info(f"Current EC value: {current_ec}")

        logger.info(f"Fertilization check: current_ec={current_ec}, has_measurements={len(measurements_list)}")

        if current_ec is not None and measurements_list:
            try:
                logger.info("Starting fertilization analysis...")
                # Get plant context for substrate info
                context = context_store.get_context(plant_id)
                substrate_type = context.get("substrate") if context else None

                # Analyze EC trend
                ec_trend = analyze_ec_trend(measurements_list, days=30)
                logger.info(f"EC trend analyzed: {ec_trend.get('analyzed', False)}")

                # Get care history for fertilization frequency
                care_history = care_store.get_plant_history(plant_id, days=90, action_type="fertilizing")

                # Get last fertilization date from FYTA
                last_fertilized = plant.get("fertilisation", {}).get("last_fertilised_at")

                # Generate recommendation
                fert_recommendation = get_fertilization_recommendation(
                    current_ec=current_ec,
                    ec_trend=ec_trend,
                    substrate_type=substrate_type,
                    last_fertilized=last_fertilized,
                    care_history=care_history
                )

                logger.info(f"Fertilization recommendation generated: {fert_recommendation is not None}")

                result["fertilization"] = {
                    "recommendation": fert_recommendation,
                    "ec_trend": ec_trend if ec_trend.get("analyzed") else None,
                    "fyta_says": plant.get("fertilisation", {})
                }

            except Exception as e:
                logger.error(f"Error generating fertilization recommendation: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # Don't fail the whole diagnosis if fertilization analysis fails

        # === WATERING ANALYSIS ===
        current_moisture = None
        if measurements_week:
            measurements_list = extract_measurements_from_response(measurements_week)
            if measurements_list:
                # Get most recent measurement
                latest_measurement = get_latest_measurement(measurements_list)
                current_moisture = latest_measurement.get("soil_moisture")

        if current_moisture is not None and measurements_list:
            try:
                logger.info("Starting watering analysis...")
                # Get plant context for substrate info
                context = context_store.get_context(plant_id)
                substrate_type = context.get("substrate_type") if context else None

                # Analyze moisture trend
                moisture_trend = analyze_moisture_trend(measurements_list, days=7)
                logger.info(f"Moisture trend analyzed: {moisture_trend.get('analyzed', False)}")

                # Get care history for watering frequency
                care_history = care_store.get_plant_history(plant_id, days=30, action_type="watering")

                # Get last watering date from care history
                last_watered = None
                if care_history:
                    last_watered = care_history[0].get("timestamp")

                # Generate recommendation
                watering_recommendation = get_watering_recommendation(
                    current_moisture=current_moisture,
                    moisture_trend=moisture_trend,
                    substrate_type=substrate_type,
                    last_watered=last_watered
                )

                logger.info(f"Watering recommendation generated: {watering_recommendation is not None}")

                result["watering"] = {
                    "recommendation": watering_recommendation,
                    "moisture_trend": moisture_trend if moisture_trend.get("analyzed") else None
                }

            except Exception as e:
                logger.error(f"Error generating watering recommendation: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # Don't fail the whole diagnosis if watering analysis fails

        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    except Exception as e:
        logger.error(f"Error diagnosing plant {plant_id}: {e}")
        import traceback
        traceback.print_exc()
        return [TextContent(
            type="text",
            text=f"Error diagnosing plant: {str(e)}"
        )]


async def handle_log_plant_care_action(fyta_client: FytaClient, arguments: Any) -> list[TextContent]:
    """Handle log_plant_care_action tool call - track manual care"""
    plant_id = int(arguments["plant_id"])
    action_type = arguments["action_type"]

    # Build metadata from optional fields
    metadata = {}
    if "amount" in arguments:
        metadata["amount"] = arguments["amount"]
    if "product" in arguments:
        metadata["product"] = arguments["product"]
    if "notes" in arguments:
        metadata["notes"] = arguments["notes"]

    # Verify plant exists
    plant = await fyta_client.get_plant_by_id(plant_id)
    if not plant:
        return [TextContent(type="text", text=f"Plant with ID {plant_id} not found")]

    # Log the action
    action = care_store.log_action(plant_id, action_type, metadata)

    result = {
        "success": True,
        "action": action,
        "plant_name": plant.get("nickname", "Unknown"),
        "message": f"Logged {action_type} for {plant.get('nickname', 'plant')} at {action['timestamp']}"
    }

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def handle_get_plant_care_history(fyta_client: FytaClient, arguments: Any) -> list[TextContent]:
    """Handle get_plant_care_history tool call - get history with analysis"""
    plant_id = int(arguments["plant_id"])
    days = arguments.get("days")
    action_type = arguments.get("action_type")
    include_analysis = arguments.get("include_analysis", True)

    # Get plant info
    plant = await fyta_client.get_plant_by_id(plant_id)
    if not plant:
        return [TextContent(type="text", text=f"Plant with ID {plant_id} not found")]

    # Get care history
    care_history = care_store.get_plant_history(plant_id, days, action_type)

    result = {
        "plant_id": plant_id,
        "plant_name": plant.get("nickname", "Unknown"),
        "care_history": care_history,
        "total_actions": len(care_history)
    }

    # Add analysis if requested
    if include_analysis and care_history:
        # Get measurements for correlation
        try:
            measurements_data = await fyta_client.get_plant_measurements(plant_id, "month")
            measurements = extract_measurements_from_response(measurements_data)

            # Watering effectiveness
            if any(a["action_type"] == "watering" for a in care_history):
                watering_analysis = analyze_watering_effectiveness(care_history, measurements)
                result["watering_analysis"] = watering_analysis

                # Frequency analysis
                frequency = calculate_watering_frequency(care_history)
                result["watering_frequency"] = frequency

            # Fertilizing correlation
            if any(a["action_type"] == "fertilizing" for a in care_history):
                fert_analysis = correlate_fertilizing_with_growth(care_history, measurements)
                result["fertilizing_analysis"] = fert_analysis

        except Exception as e:
            logger.warning(f"Could not perform analysis: {e}")

        # Care insights
        insights = get_care_insights(care_history, plant)
        if insights:
            result["insights"] = insights

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def handle_get_plant_events(fyta_client: FytaClient, arguments: Any) -> list[TextContent]:
    """Handle get_plant_events tool call - real-time event detection for automation"""
    try:
        # Get filter parameters
        target_plant_id = arguments.get("plant_id")
        severity_filter = arguments.get("severity")
        priority_filter = arguments.get("priority")
        event_type_filter = arguments.get("event_type")
        actionable_only = arguments.get("actionable_only", False)

        # Get all plants
        data = await fyta_client.get_plants()
        plants = data.get("plants", [])

        if not plants:
            return [TextContent(type="text", text=json.dumps({"events": [], "count": 0}, indent=2))]

        # Filter to specific plant if requested
        if target_plant_id:
            plants = [p for p in plants if p["id"] == target_plant_id]
            if not plants:
                return [TextContent(type="text", text=f"Plant with ID {target_plant_id} not found")]

        # Detect events for each plant
        all_events = []

        for plant in plants:
            # === APPLY SMART STATUS EVALUATION ===
            # Get measurements for smart threshold evaluation
            measurements_week = None
            try:
                measurements_week = await fyta_client.get_plant_measurements(plant["id"], "week")
            except Exception as e:
                logger.warning(f"Could not get measurements for plant {plant['id']}: {e}")

            # Enrich plant object with latest measurement values
            enriched_plant_data = plant.copy()
            # Remove potentially stale values from plant object
            enriched_plant_data.pop("temperature", None)
            enriched_plant_data.pop("moisture", None)
            enriched_plant_data.pop("soil_moisture", None)
            enriched_plant_data.pop("light", None)
            enriched_plant_data.pop("salinity", None)
            enriched_plant_data.pop("soil_fertility", None)

            if measurements_week:
                measurements_list = extract_measurements_from_response(measurements_week)
                if measurements_list:
                    latest = get_latest_measurement(measurements_list)
                    # Add actual values from measurements (plant object only has status codes)
                    enriched_plant_data["temperature"] = latest.get("temperature")
                    enriched_plant_data["light"] = latest.get("light")
                    enriched_plant_data["soil_moisture"] = latest.get("soil_moisture") or latest.get("moisture")
                    enriched_plant_data["soil_fertility"] = latest.get("soil_fertility") or latest.get("salinity")
                    logger.info(f"Plant {plant['id']}: Enriched with measurements - temp={latest.get('temperature')}")

            # Use smart status evaluation to fix FYTA's buggy status codes
            smart_status = evaluate_plant_status(enriched_plant_data, measurements_week)

            logger.info(f"Plant {plant['id']}: use_fyta_status={smart_status.get('use_fyta_status')}, method={smart_status.get('evaluation_method')}")

            # Create final enriched plant object with smart status
            enriched_plant = enriched_plant_data.copy()
            if not smart_status.get("use_fyta_status", True):
                # Override buggy FYTA status with smart evaluation
                temp_data = smart_status.get("temperature") or {}
                light_data = smart_status.get("light") or {}
                moisture_data = smart_status.get("moisture") or {}
                nutrients_data = smart_status.get("nutrients") or {}

                old_temp = plant.get("temperature_status", 2)
                new_temp = temp_data.get("status", old_temp)

                logger.info(f"Plant {plant['id']}: Overriding temperature_status {old_temp} -> {new_temp}")

                enriched_plant["temperature_status"] = new_temp
                enriched_plant["light_status"] = light_data.get("status", plant.get("light_status", 2))
                enriched_plant["moisture_status"] = moisture_data.get("status", plant.get("moisture_status", 2))
                enriched_plant["salinity_status"] = nutrients_data.get("status", plant.get("salinity_status", 2))
            else:
                logger.info(f"Plant {plant['id']}: Using FYTA status (no thresholds available)")

            # For state comparison, we could use measurements from 1 hour ago
            # Since we don't have persistent state, we'll detect based on current state only
            # Status changes won't be detected without previous state
            # But sensor silence, battery low, critical states can still be detected

            previous_state = None  # In a real implementation, this would be from a database/cache

            # Detect events using enriched plant data with smart status
            plant_events = detect_all_events(
                enriched_plant,
                previous_state,
                config={
                    "silence_threshold_minutes": 90,
                    "battery_threshold": 20.0
                }
            )

            all_events.extend(plant_events)

        # Apply filters
        filters = {}
        if severity_filter:
            filters["severity"] = severity_filter
        if priority_filter:
            filters["priority"] = priority_filter
        if event_type_filter:
            filters["event_type"] = event_type_filter
        if actionable_only:
            filters["actionable"] = True

        filtered_events = filter_events(all_events, filters if filters else None)

        # Sort by priority and severity
        priority_order = {"immediate": 0, "high": 1, "medium": 2, "low": 3}
        severity_order = {"critical": 0, "warning": 1, "info": 2}

        filtered_events.sort(
            key=lambda e: (priority_order.get(e.get("priority", "low"), 4),
                          severity_order.get(e.get("severity", "info"), 3))
        )

        # Format for webhooks/automation
        webhook_events = [format_event_for_webhook(event) for event in filtered_events]

        result = {
            "event_count": len(filtered_events),
            "events": filtered_events,
            "webhook_format": webhook_events,
            "summary": {
                "critical": len([e for e in filtered_events if e.get("severity") == "critical"]),
                "warning": len([e for e in filtered_events if e.get("severity") == "warning"]),
                "info": len([e for e in filtered_events if e.get("severity") == "info"]),
                "actionable": len([e for e in filtered_events if e.get("actionable")])
            },
            "polling_info": {
                "recommended_interval_seconds": 300,  # 5 minutes
                "note": "For state-change detection, store previous state and compare on next poll"
            }
        }

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error detecting events: {e}")
        import traceback
        traceback.print_exc()
        return [TextContent(type="text", text=f"Error detecting events: {str(e)}")]


async def handle_get_plant_dli_analysis(fyta_client: FytaClient, arguments: Any) -> list[TextContent]:
    """Handle get_plant_dli_analysis tool call - advanced DLI intelligence"""
    plant_id = int(arguments["plant_id"])
    timeframe = arguments.get("timeframe", "week")
    include_recommendations = arguments.get("include_grow_light_recommendations", True)

    try:
        # Get plant info
        plant = await fyta_client.get_plant_by_id(plant_id)
        if not plant:
            return [TextContent(type="text", text=f"Plant with ID {plant_id} not found")]

        # Check if sensor has light capability
        light_capability = check_light_capability(plant)
        if not light_capability["capable"]:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "plantId": plant_id,
                    "plantName": plant.get("nickname", "Unknown"),
                    "dli_available": False,
                    "reason": light_capability["reason"],
                    "message": light_capability["message"],
                    "recommendation": light_capability.get("recommendation"),
                    "sensor_info": light_capability.get("sensor_info")
                }, indent=2)
            )]

        # Get measurements
        measurements_data = await fyta_client.get_plant_measurements(plant_id, timeframe)
        measurements = extract_measurements_from_response(measurements_data)

        if not measurements:
            return [TextContent(
                type="text",
                text=f"No measurement data available for plant {plant_id} in timeframe '{timeframe}'. API response keys: {list(measurements_data.keys()) if isinstance(measurements_data, dict) else 'not a dict'}"
            )]

        # Calculate daily DLIs
        daily_dlis = calculate_daily_dlis(measurements)

        if not daily_dlis:
            return [TextContent(type="text", text="No valid DLI data could be calculated")]

        # Get DLI thresholds from plant data (if available)
        # FYTA provides min/max DLI in plant profile
        min_dli = plant.get("min_dli", 5.0)  # Default: 5 mol/m²/day (low light plants)
        max_dli = plant.get("max_dli", 15.0)  # Default: 15 mol/m²/day

        # Get current (most recent) DLI
        current_date, current_dli = daily_dlis[-1]

        # Classify current DLI status
        dli_status = classify_dli_status(current_dli, min_dli, max_dli)

        # Analyze DLI trend
        trend_analysis = analyze_dli_trend(daily_dlis, min_dli)

        # Build result
        result = {
            "plantId": plant_id,
            "plantName": plant.get("nickname", "Unknown"),
            "scientificName": plant.get("scientific_name", "Unknown"),
            "timeframe": timeframe,
            "current_dli": {
                "value": current_dli,
                "date": current_date.isoformat(),
                "status": dli_status
            },
            "trend_analysis": trend_analysis,
            "daily_dlis": [
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "dli": dli,
                    "is_optimal": min_dli <= dli <= max_dli
                }
                for date, dli in daily_dlis[-14:]  # Last 14 days max
            ]
        }

        # Add chronic deficit warning
        if trend_analysis["consecutive_deficit_days"] >= 3:
            result["chronic_deficit_warning"] = {
                "severity": "high" if trend_analysis["consecutive_deficit_days"] >= 5 else "moderate",
                "message": f"Plant has been below optimal DLI for {trend_analysis['consecutive_deficit_days']} consecutive days. "
                          "This can lead to etiolation (stretching), weak growth, and poor health.",
                "days_below_optimal": trend_analysis["days_below_optimal"],
                "deficit_rate": f"{trend_analysis['deficit_percentage']}% of days analyzed"
            }

        # Grow light recommendations
        if include_recommendations and dli_status["status"] in ["deficit", "severe_deficit", "critical_deficit"]:
            # Calculate what's needed to reach minimum optimal DLI
            target_dli = min_dli

            # Typical supplemental lighting schedule: 12-14 hours
            grow_light_rec = calculate_grow_light_needs(current_dli, target_dli, hours_available=12)

            result["grow_light_recommendations"] = grow_light_rec

        # Seasonal predictions
        current_month = datetime.now().month
        seasonal_forecast = predict_seasonal_dli(current_dli, current_month)
        result["seasonal_forecast"] = seasonal_forecast

        # Smart insights
        insights = []

        # Insight 1: Chronic deficit
        if trend_analysis["consecutive_deficit_days"] >= 5:
            insights.append({
                "type": "critical",
                "title": "Chronic Light Deficit Detected",
                "message": f"Your {plant.get('nickname', 'plant')} has been receiving insufficient light for "
                          f"{trend_analysis['consecutive_deficit_days']} days straight. "
                          "Consider immediate supplemental lighting or relocating to a brighter spot."
            })

        # Insight 2: Seasonal warning
        if current_month in [11, 12, 1, 2] and dli_status["missing_percent"] > 30:
            insights.append({
                "type": "warning",
                "title": "Winter Light Challenge",
                "message": f"Natural DLI is {dli_status['missing_percent']}% below optimal during winter months. "
                          "Most indoor plants benefit from grow lights November through February."
            })

        # Insight 3: Improvement trend
        if trend_analysis["trend"] == "improving" and dli_status["status"] in ["deficit", "severe_deficit"]:
            insights.append({
                "type": "positive",
                "title": "Light Conditions Improving",
                "message": "DLI trend is improving! If you've recently added grow lights or moved the plant, "
                          "keep monitoring. Should reach optimal levels soon."
            })

        # Insight 4: Perfect DLI
        if dli_status["status"] == "optimal" and trend_analysis["deficit_percentage"] < 20:
            insights.append({
                "type": "success",
                "title": "Excellent Light Management",
                "message": f"Your {plant.get('nickname', 'plant')} is receiving optimal DLI! "
                          f"{100 - trend_analysis['deficit_percentage']}% of days are in the perfect range. Keep it up!"
            })

        result["insights"] = insights

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error analyzing DLI for plant {plant_id}: {e}")
        import traceback
        traceback.print_exc()
        return [TextContent(type="text", text=f"Error analyzing DLI: {str(e)}")]


# ============================================================================
# PLANT CONTEXT HANDLERS
# ============================================================================

async def handle_set_plant_context(fyta_client: FytaClient, arguments: Any) -> list[TextContent]:
    """Set context information for a plant"""
    try:
        plant_id = int(arguments.get("plant_id"))

        # Build context from arguments
        context = {}

        if "substrate" in arguments:
            context["substrate"] = arguments["substrate"]

        if "container" in arguments:
            context["container"] = arguments["container"]

        if "growth_phase" in arguments:
            context["growth_phase"] = arguments["growth_phase"]

        if "notes" in arguments:
            context["notes"] = arguments["notes"]

        if not context:
            return [TextContent(
                type="text",
                text="Error: At least one context field (substrate, container, growth_phase, notes) must be provided"
            )]

        # Store context
        updated_context = context_store.set_context(plant_id, context)

        result = {
            "success": True,
            "plant_id": plant_id,
            "context": updated_context,
            "message": "Plant context updated successfully"
        }

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error setting plant context: {e}")
        return [TextContent(type="text", text=f"Error setting context: {str(e)}")]


async def handle_get_plant_context(fyta_client: FytaClient, arguments: Any) -> list[TextContent]:
    """Get stored context and context-aware recommendations for a plant"""
    try:
        plant_id = int(arguments.get("plant_id"))

        # Get stored context
        context = context_store.get_context(plant_id)

        # Get current plant data for recommendations
        data = await fyta_client.get_plants()
        plants = data.get("plants", [])

        plant = next((p for p in plants if p["id"] == plant_id), None)
        if not plant:
            return [TextContent(type="text", text=f"Plant with ID {plant_id} not found")]

        result = {
            "plant_id": plant_id,
            "nickname": plant.get("nickname", "Unnamed"),
            "context": context if context else {"message": "No context stored for this plant"},
            "has_context": context is not None
        }

        # Generate context-aware recommendations if context exists
        if context:
            recommendations = get_context_aware_recommendations(plant, context)
            sensor_adjustments = interpret_sensor_with_context(plant, context)

            result["recommendations"] = recommendations
            result["sensor_interpretation"] = sensor_adjustments

            # Add knowledge base info for reference
            from .utils.plant_context import (
                SUBSTRATE_KNOWLEDGE,
                CONTAINER_KNOWLEDGE,
                GROWTH_PHASE_KNOWLEDGE
            )

            knowledge = {}
            if context.get("substrate") and context["substrate"] in SUBSTRATE_KNOWLEDGE:
                knowledge["substrate_info"] = SUBSTRATE_KNOWLEDGE[context["substrate"]]

            if context.get("container") and context["container"] in CONTAINER_KNOWLEDGE:
                knowledge["container_info"] = CONTAINER_KNOWLEDGE[context["container"]]

            if context.get("growth_phase") and context["growth_phase"] in GROWTH_PHASE_KNOWLEDGE:
                knowledge["growth_phase_info"] = GROWTH_PHASE_KNOWLEDGE[context["growth_phase"]]

            if knowledge:
                result["knowledge_base"] = knowledge

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error getting plant context: {e}")
        import traceback
        traceback.print_exc()
        return [TextContent(type="text", text=f"Error getting context: {str(e)}")]


# Tool handler mapping
TOOL_HANDLERS = {
    "get_all_plants": handle_get_all_plants,
    "get_plant_details": handle_get_plant_details,
    "get_plants_needing_attention": handle_get_plants_needing_attention,
    "get_garden_overview": handle_get_garden_overview,
    "get_plant_measurements": handle_get_plant_measurements,
    "diagnose_plant": handle_diagnose_plant,
    "get_plant_trends": handle_get_plant_trends,
    "get_plant_statistics": handle_get_plant_statistics,
    "get_plant_dli_analysis": handle_get_plant_dli_analysis,
    "get_plant_events": handle_get_plant_events,
    "log_plant_care_action": handle_log_plant_care_action,
    "get_plant_care_history": handle_get_plant_care_history,
    "set_plant_context": handle_set_plant_context,
    "get_plant_context": handle_get_plant_context,
}


async def handle_tool_call(name: str, arguments: Any, fyta_client: FytaClient) -> list[TextContent]:
    """Route tool calls to appropriate handlers"""
    handler = TOOL_HANDLERS.get(name)

    if not handler:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    try:
        return await handler(fyta_client, arguments)
    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
