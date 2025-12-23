"""
Sensor Information and Capabilities

FYTA has different sensor types with different capabilities:
- FYTA Beam 2.0 (sensor_type_id: 2): Has light sensor
- FYTA Beam (sensor_type_id: 3): NO light sensor
- FYTA Legacy (sensor_type_id: 1): No light sensor

This module provides utilities to detect sensor capabilities and adjust
analysis accordingly.
"""
from typing import Dict, Optional


# Sensor type definitions
SENSOR_TYPES = {
    1: {
        "name": "FYTA (Legacy)",
        "has_light_sensor": False,
        "capabilities": ["temperature", "moisture", "nutrients"],
        "missing": ["light", "dli"]
    },
    2: {
        "name": "FYTA Beam 2.0",
        "has_light_sensor": True,
        "capabilities": ["temperature", "moisture", "nutrients", "light"],
        "missing": []
    },
    3: {
        "name": "FYTA Beam",
        "has_light_sensor": False,
        "capabilities": ["temperature", "moisture", "nutrients"],
        "missing": ["light", "dli"]
    }
}


def get_sensor_info(plant: Dict) -> Dict:
    """
    Get sensor information and capabilities for a plant.

    Args:
        plant: Plant dict from FYTA API

    Returns:
        Dict with sensor info and capabilities
    """
    sensor_data = plant.get("sensor", {})

    if not sensor_data or not sensor_data.get("has_sensor"):
        return {
            "has_sensor": False,
            "sensor_id": None,
            "sensor_type": "none",
            "has_light_sensor": False,
            "capabilities": [],
            "missing": ["temperature", "moisture", "nutrients", "light", "dli"],
            "warning": "No sensor connected to this plant"
        }

    sensor_type_id = sensor_data.get("sensor_type_id", 1)
    sensor_id = sensor_data.get("id", "Unknown")
    version = sensor_data.get("version", "Unknown")

    sensor_type_info = SENSOR_TYPES.get(sensor_type_id, SENSOR_TYPES[1])

    return {
        "has_sensor": True,
        "sensor_id": sensor_id,
        "sensor_type_id": sensor_type_id,
        "sensor_type": sensor_type_info["name"],
        "version": version,
        "has_light_sensor": sensor_type_info["has_light_sensor"],
        "capabilities": sensor_type_info["capabilities"],
        "missing": sensor_type_info["missing"],
        "is_battery_low": sensor_data.get("is_battery_low", False),
        "status": sensor_data.get("status", 0),
        "last_data": sensor_data.get("received_data_at")
    }


def check_light_capability(plant: Dict) -> Dict:
    """
    Check if plant's sensor can measure light.

    Args:
        plant: Plant dict from FYTA API

    Returns:
        Dict with capability status and message
    """
    sensor_info = get_sensor_info(plant)

    if not sensor_info["has_sensor"]:
        return {
            "capable": False,
            "reason": "no_sensor",
            "message": "No sensor connected to this plant",
            "recommendation": "Connect a FYTA sensor to monitor this plant"
        }

    if not sensor_info["has_light_sensor"]:
        return {
            "capable": False,
            "reason": "legacy_sensor",
            "message": f"Your sensor ({sensor_info['sensor_type']}) doesn't have a light sensor",
            "recommendation": "Upgrade to FYTA Beam 2.0 for light and DLI monitoring",
            "sensor_info": sensor_info
        }

    return {
        "capable": True,
        "reason": "has_sensor",
        "message": f"Light monitoring available ({sensor_info['sensor_type']})",
        "sensor_info": sensor_info
    }


def get_available_analyses(plant: Dict) -> Dict:
    """
    Get list of available analyses based on sensor capabilities.

    Args:
        plant: Plant dict from FYTA API

    Returns:
        Dict with available and unavailable analyses
    """
    sensor_info = get_sensor_info(plant)

    available = []
    unavailable = []

    # Basic metrics (always available if sensor exists)
    if sensor_info["has_sensor"]:
        available.extend(["temperature", "moisture", "nutrients"])
    else:
        unavailable.extend(["temperature", "moisture", "nutrients"])

    # Light-dependent analyses
    if sensor_info["has_light_sensor"]:
        available.extend(["light", "dli", "photoperiod"])
    else:
        unavailable.extend(["light", "dli", "photoperiod"])

    return {
        "available": available,
        "unavailable": unavailable,
        "sensor_info": sensor_info,
        "recommendations": get_analysis_recommendations(unavailable)
    }


def get_analysis_recommendations(unavailable: list) -> list:
    """
    Get recommendations for unavailable analyses.

    Args:
        unavailable: List of unavailable analysis types

    Returns:
        List of recommendation strings
    """
    recommendations = []

    if "light" in unavailable or "dli" in unavailable:
        recommendations.append(
            "💡 Light and DLI analysis unavailable. Upgrade to FYTA Beam 2.0 for automatic light monitoring."
        )
        recommendations.append(
            "Alternative: Use a manual light meter app on your phone to check light levels periodically."
        )

    if not any(item in unavailable for item in ["temperature", "moisture", "nutrients"]):
        # All basic metrics available
        pass
    else:
        recommendations.append(
            "⚠️ No sensor connected. Connect a FYTA sensor for automated plant monitoring."
        )

    return recommendations


def format_sensor_summary(plant: Dict) -> str:
    """
    Format sensor information as human-readable summary.

    Args:
        plant: Plant dict from FYTA API

    Returns:
        Formatted string
    """
    sensor_info = get_sensor_info(plant)

    if not sensor_info["has_sensor"]:
        return "❌ No sensor connected"

    lines = []
    lines.append(f"📡 **Sensor**: {sensor_info['sensor_type']} (v{sensor_info['version']})")
    lines.append(f"   ID: {sensor_info['sensor_id']}")

    if sensor_info["has_light_sensor"]:
        lines.append("   ✅ Light sensor: Available")
    else:
        lines.append("   ⚠️ Light sensor: Not available (upgrade to Beam 2.0)")

    if sensor_info["is_battery_low"]:
        lines.append("   🔋 Battery: Low - replace soon!")
    else:
        lines.append("   🔋 Battery: OK")

    lines.append(f"\n📊 **Capabilities**: {', '.join(sensor_info['capabilities'])}")

    if sensor_info["missing"]:
        lines.append(f"⚠️ **Not available**: {', '.join(sensor_info['missing'])}")

    return "\n".join(lines)
