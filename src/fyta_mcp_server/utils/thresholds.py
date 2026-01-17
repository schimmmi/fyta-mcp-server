"""
Threshold Evaluation Utilities

FYTA's status codes (temperature_status, moisture_status, etc.) are often inconsistent
with the actual threshold values they provide. This module implements intelligent
threshold evaluation that actually uses the thresholds correctly.

Status codes:
- 1: Too low (below acceptable range)
- 2: Optimal (within good range)
- 3: Too high (above acceptable range)
- 4: Outside acceptable (below min_acceptable or above max_acceptable)
"""
from typing import Dict, Optional, Tuple


def evaluate_metric_status(
    value: float,
    min_good: float,
    max_good: float,
    min_acceptable: Optional[float] = None,
    max_acceptable: Optional[float] = None
) -> Tuple[int, str]:
    """
    Evaluate a metric value against thresholds.

    Args:
        value: The measured value
        min_good: Minimum value for "good" status
        max_good: Maximum value for "good" status
        min_acceptable: Minimum acceptable value (optional)
        max_acceptable: Maximum acceptable value (optional)

    Returns:
        Tuple of (status_code, status_name)
        - status_code: 1 (low), 2 (optimal), 3 (high), 4 (critical)
        - status_name: "low", "optimal", "high", "critical"
    """
    # Check if within good range
    if min_good <= value <= max_good:
        return (2, "optimal")

    # Check if below good range
    if value < min_good:
        # Check if critically low (below acceptable)
        if min_acceptable is not None and value < min_acceptable:
            return (4, "critical_low")
        return (1, "low")

    # Check if above good range
    if value > max_good:
        # Check if critically high (above acceptable)
        if max_acceptable is not None and value > max_acceptable:
            return (4, "critical_high")
        return (3, "high")

    # Fallback (shouldn't reach here)
    return (2, "optimal")


def get_active_thresholds(plant: Dict) -> Optional[Dict]:
    """
    Get the active thresholds for a plant based on current season.

    FYTA provides multiple threshold sets (winter/summer) in the measurements response.
    The plant object should have a thresholds_id that indicates which set is active.

    Args:
        plant: Plant object from FYTA API (should include threshold data from measurements)

    Returns:
        Dict with threshold values or None
    """
    # Try to get thresholds from plant data
    # This would typically come from the measurements endpoint
    thresholds = plant.get("thresholds")

    if not thresholds:
        # Try to get from thresholds_list (from measurements response)
        thresholds_list = plant.get("thresholds_list", [])
        if thresholds_list:
            # Use first threshold set (usually active season)
            thresholds = thresholds_list[0]

    return thresholds


def evaluate_plant_status(plant: Dict, measurements_data: Optional[Dict] = None, ec_trend: Optional[Dict] = None) -> Dict:
    """
    Evaluate all metrics for a plant using actual thresholds.

    This provides a smart alternative to FYTA's inconsistent status codes.

    Args:
        plant: Plant object from FYTA API
        measurements_data: Optional measurements data with thresholds

    Returns:
        Dict with evaluated status for each metric
    """
    result = {
        "temperature": None,
        "light": None,
        "moisture": None,
        "nutrients": None,
        "use_fyta_status": False,
        "evaluation_method": "smart"
    }

    # Get thresholds from measurements data if available
    thresholds = None
    if measurements_data and isinstance(measurements_data, dict):
        thresholds = measurements_data.get("thresholds")
        if not thresholds and "thresholds_list" in measurements_data:
            # Get active threshold set (first one is usually active season)
            thresholds_list = measurements_data.get("thresholds_list", [])
            if thresholds_list and len(thresholds_list) > 0:
                thresholds = thresholds_list[0]

    # Fallback to plant thresholds
    if not thresholds:
        thresholds = get_active_thresholds(plant)

    # Debug logging
    import logging
    logger = logging.getLogger("fyta-mcp-server")
    logger.info(f"Plant {plant.get('id')}: Thresholds found: {thresholds is not None}, temp={plant.get('temperature')}")
    if thresholds:
        logger.info(f"Plant {plant.get('id')}: temp_min_good={thresholds.get('temperature_min_good')}, temp_max_good={thresholds.get('temperature_max_good')}")

    if not thresholds:
        # No thresholds available, use FYTA status
        logger.warning(f"No thresholds available for plant {plant.get('id')}, using FYTA status")
        result["use_fyta_status"] = True
        result["evaluation_method"] = "fyta"
        result["temperature"] = {
            "status": plant.get("temperature_status", 2),
            "value": plant.get("temperature")
        }
        result["moisture"] = {
            "status": plant.get("moisture_status", 2),
            "value": plant.get("moisture")
        }
        result["nutrients"] = {
            "status": plant.get("salinity_status", 2),
            "value": plant.get("salinity")
        }
        result["light"] = {
            "status": plant.get("light_status", 2),
            "value": plant.get("light")
        }
        return result

    # Evaluate temperature
    temp = plant.get("temperature")
    logger.info(f"Plant {plant.get('id')} - evaluate_plant_status: temp from plant dict = {temp}")
    if temp is not None:
        temp_min_good = thresholds.get("temperature_min_good", 0)
        temp_max_good = thresholds.get("temperature_max_good", 100)

        status_code, status_name = evaluate_metric_status(
            temp,
            temp_min_good,
            temp_max_good,
            thresholds.get("temperature_min_acceptable"),
            thresholds.get("temperature_max_acceptable")
        )

        # Debug logging
        import logging
        logger = logging.getLogger("fyta-mcp-server")
        logger.info(f"Temperature evaluation: value={temp}, min_good={temp_min_good}, max_good={temp_max_good}, result={status_code} ({status_name})")

        result["temperature"] = {
            "status": status_code,
            "status_name": status_name,
            "value": temp,
            "thresholds": {
                "min_good": temp_min_good,
                "max_good": temp_max_good
            },
            "fyta_status": plant.get("temperature_status"),
            "matches_fyta": status_code == plant.get("temperature_status", 2)
        }

    # Evaluate moisture
    moisture = plant.get("moisture") or plant.get("soil_moisture")
    logger.info(f"Plant {plant.get('id')} - evaluate_plant_status: moisture={plant.get('moisture')}, soil_moisture={plant.get('soil_moisture')}, using={moisture}")
    if moisture is not None:
        moisture_min_good = thresholds.get("moisture_min_good", 0)
        moisture_max_good = thresholds.get("moisture_max_good", 100)

        status_code, status_name = evaluate_metric_status(
            moisture,
            moisture_min_good,
            moisture_max_good,
            thresholds.get("moisture_min_acceptable"),
            thresholds.get("moisture_max_acceptable")
        )

        logger.info(f"Moisture evaluation: value={moisture}, min_good={moisture_min_good}, max_good={moisture_max_good}, result={status_code} ({status_name})")

        result["moisture"] = {
            "status": status_code,
            "status_name": status_name,
            "value": moisture,
            "thresholds": {
                "min_good": moisture_min_good,
                "max_good": moisture_max_good
            },
            "fyta_status": plant.get("moisture_status"),
            "matches_fyta": status_code == plant.get("moisture_status", 2)
        }

    # Evaluate nutrients (salinity/soil_fertility)
    nutrients = plant.get("salinity") or plant.get("soil_fertility")
    nutrients_anomaly = plant.get("soil_fertility_anomaly", False)

    if nutrients is not None:
        # Handle special case: FYTA winter thresholds often have min=max=0 for salinity
        # In this case, any value > 0 is considered "high" but not critical
        min_good = thresholds.get("salinity_min_good", 0)
        max_good = thresholds.get("salinity_max_good", 0)

        # If both are 0, use more sensible defaults based on summer thresholds
        if min_good == 0 and max_good == 0:
            # Check if we have summer thresholds available
            if measurements_data and isinstance(measurements_data, dict) and "thresholds_list" in measurements_data:
                thresholds_list = measurements_data.get("thresholds_list", [])
                if thresholds_list:
                    for t in thresholds_list:
                        if t and isinstance(t, dict) and t.get("thresholds_type") == "summer":
                            min_good = t.get("salinity_min_good", 0.2)
                            max_good = t.get("salinity_max_good", 1.0)
                            break

            # Fallback to reasonable defaults
            # Optimal range: 0.2-1.0 mS/cm (winter: lower end, summer: upper end)
            if min_good == 0 and max_good == 0:
                min_good = 0.2
                max_good = 1.0

        status_code, status_name = evaluate_metric_status(
            nutrients,
            min_good,
            max_good,
            thresholds.get("salinity_min_acceptable"),
            thresholds.get("salinity_max_acceptable")
        )

        # Smart anomaly detection: Only treat as sensor error if EC suddenly dropped to 0
        # Gradual decline to 0 = real nutrient depletion (needs fertilization)
        # Sudden drop from >0.3 to 0 = sensor issue (poor contact or malfunction)
        if nutrients_anomaly and nutrients == 0:
            # FYTA reports anomaly at EC=0 - check if it's real depletion or sensor issue
            is_sensor_error = False

            if ec_trend and ec_trend.get("analyzed"):
                trend = ec_trend.get("trend")
                initial_ec = ec_trend.get("initial_ec", 0)

                # Sudden drop: EC was > 0.3 within last 30 days and is now suddenly 0
                # (not a gradual decreasing trend)
                if initial_ec > 0.3 and trend != "decreasing":
                    is_sensor_error = True
                    logger.warning(f"Sensor anomaly detected: sudden drop from {initial_ec} to 0 (trend: {trend})")
                else:
                    # Gradual decline to 0 = real nutrient depletion
                    logger.info(f"EC=0 is real nutrient depletion (trend: {trend}, initial: {initial_ec})")
            else:
                # No trend data available - treat conservatively as sensor error
                # (better to check sensor than over-fertilize based on bad reading)
                is_sensor_error = True
                logger.warning(f"Insufficient data for anomaly detection, treating EC=0 as potential sensor issue")

            if is_sensor_error:
                status_code = 4  # Critical - sensor issue
                status_name = "sensor_error"
        elif nutrients_anomaly and nutrients != 0:
            # Real sensor anomaly detected (malfunction while measuring non-zero value)
            logger.warning(f"Nutrients sensor anomaly detected for plant {plant.get('id')}: value={nutrients}, treating as unreliable")
            status_code = 4  # Critical - sensor issue
            status_name = "sensor_error"
        elif nutrients == 0 and not nutrients_anomaly:
            # EC=0 without anomaly flag = valid measurement (no nutrients)
            logger.info(f"Nutrients EC=0 for plant {plant.get('id')} - no nutrients present (fertilization needed)")

        logger.info(f"Nutrients evaluation: value={nutrients}, min_good={min_good}, max_good={max_good}, result={status_code} ({status_name}), adjusted={min_good != thresholds.get('salinity_min_good', 0)}, anomaly={nutrients_anomaly}")

        result["nutrients"] = {
            "status": status_code,
            "status_name": status_name,
            "value": nutrients,
            "anomaly": nutrients_anomaly,
            "thresholds": {
                "min_good": min_good,
                "max_good": max_good
            },
            "fyta_status": plant.get("salinity_status"),
            "matches_fyta": status_code == plant.get("salinity_status", 2),
            "adjusted_thresholds": min_good != thresholds.get("salinity_min_good", 0)
        }

    # Evaluate light
    light = plant.get("light")
    if light is not None:
        light_min_good = thresholds.get("light_min_good", 0)
        light_max_good = thresholds.get("light_max_good", 1000)
        light_min_acceptable = thresholds.get("light_min_acceptable")

        # For light, don't treat low values as "critical" - just "low"
        # Low light is concerning but rarely critical for plant survival
        # Set min_acceptable to 0 to avoid critical status
        if light_min_acceptable is None or light_min_acceptable > 0:
            light_min_acceptable = 0

        status_code, status_name = evaluate_metric_status(
            light,
            light_min_good,
            light_max_good,
            light_min_acceptable,
            thresholds.get("light_max_acceptable")
        )

        logger.info(f"Light evaluation: value={light}, min_good={light_min_good}, max_good={light_max_good}, min_acceptable={light_min_acceptable}, result={status_code} ({status_name})")

        result["light"] = {
            "status": status_code,
            "status_name": status_name,
            "value": light,
            "thresholds": {
                "min_good": light_min_good,
                "max_good": light_max_good,
                "min_acceptable": light_min_acceptable
            },
            "fyta_status": plant.get("light_status"),
            "matches_fyta": status_code == plant.get("light_status", 2)
        }
    else:
        logger.warning(f"Plant {plant.get('id')}: Light value is None, skipping light evaluation")

    return result


def get_status_emoji(status: int) -> str:
    """Get emoji for status code"""
    return {
        1: "⚠️",  # Low
        2: "✅",  # Optimal
        3: "⚠️",  # High
        4: "🔴"   # Critical
    }.get(status, "❓")


def get_status_description(status: int, metric: str, status_name: str = None) -> str:
    """Get human-readable status description"""
    # Check for sensor error first
    if status_name == "sensor_error":
        return f"{metric} sensor error or anomaly detected"

    if status == 1:
        return f"{metric} is too low"
    elif status == 2:
        return f"{metric} is optimal"
    elif status == 3:
        return f"{metric} is too high"
    elif status == 4:
        return f"{metric} is critically out of range"
    return f"{metric} status unknown"
