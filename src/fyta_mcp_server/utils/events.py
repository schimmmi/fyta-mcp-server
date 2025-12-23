"""
Event detection and automation utilities

Detects state changes, time-based triggers, and anomalies for automation systems
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import json
import hashlib


def generate_event_id(plant_id: int, event_type: str, timestamp: datetime) -> str:
    """Generate unique event ID"""
    data = f"{plant_id}:{event_type}:{timestamp.isoformat()}"
    return hashlib.md5(data.encode()).hexdigest()[:12]


def detect_status_changes(current_plant: Dict, previous_state: Optional[Dict]) -> List[Dict]:
    """
    Detect status transitions for temperature, light, moisture, nutrients

    Args:
        current_plant: Current plant data
        previous_state: Previous plant state (if available)

    Returns:
        List of status change events
    """
    events = []

    if not previous_state:
        return events

    status_mapping = {
        "temperature_status": "temperature",
        "light_status": "light",
        "moisture_status": "moisture",
        "salinity_status": "nutrients"
    }

    status_names = {1: "Low", 2: "Optimal", 3: "High"}

    for status_key, metric_name in status_mapping.items():
        current_status = current_plant.get(status_key, 2)
        previous_status = previous_state.get(status_key, 2)

        if current_status != previous_status:
            from_status = status_names.get(previous_status, "Unknown")
            to_status = status_names.get(current_status, "Unknown")

            # Determine severity
            if to_status == "Optimal":
                severity = "info"
                priority = "low"
            elif (from_status == "Optimal" and to_status in ["Low", "High"]) or \
                 (from_status in ["Low", "High"] and to_status == "Optimal"):
                severity = "warning"
                priority = "medium"
            else:
                # Getting worse (Low → Optimal was already handled)
                severity = "critical" if to_status in ["Low", "High"] else "warning"
                priority = "high" if severity == "critical" else "medium"

            event = {
                "event_type": "status_change",
                "event_id": generate_event_id(current_plant["id"], f"status_change_{metric_name}", datetime.now()),
                "timestamp": datetime.now().isoformat(),
                "plant_id": current_plant["id"],
                "plant_name": current_plant.get("nickname", "Unknown"),
                "metric": metric_name,
                "from_status": from_status,
                "to_status": to_status,
                "severity": severity,
                "priority": priority,
                "message": f"{metric_name.capitalize()} changed from {from_status} to {to_status}",
                "actionable": to_status != "Optimal"
            }

            events.append(event)

    return events


def detect_sensor_silence(current_plant: Dict, silence_threshold_minutes: int = 90) -> Optional[Dict]:
    """
    Detect if sensor hasn't reported in a while

    Args:
        current_plant: Current plant data
        silence_threshold_minutes: Minutes of silence before alerting

    Returns:
        Event dict if silence detected, None otherwise
    """
    last_data_str = current_plant.get("received_data_at")

    if not last_data_str:
        return None

    try:
        last_update = datetime.fromisoformat(last_data_str.replace("Z", "+00:00"))
        now = datetime.now(last_update.tzinfo)
        minutes_silent = (now - last_update).total_seconds() / 60

        if minutes_silent > silence_threshold_minutes:
            # Determine severity based on how long it's been
            if minutes_silent > 180:  # 3 hours
                severity = "critical"
                priority = "high"
            elif minutes_silent > 120:  # 2 hours
                severity = "warning"
                priority = "medium"
            else:
                severity = "info"
                priority = "low"

            return {
                "event_type": "sensor_silence",
                "event_id": generate_event_id(current_plant["id"], "sensor_silence", datetime.now()),
                "timestamp": datetime.now().isoformat(),
                "plant_id": current_plant["id"],
                "plant_name": current_plant.get("nickname", "Unknown"),
                "minutes_silent": int(minutes_silent),
                "last_update": last_data_str,
                "severity": severity,
                "priority": priority,
                "message": f"Sensor hasn't reported for {int(minutes_silent)} minutes",
                "actionable": True,
                "suggested_actions": [
                    "Check sensor battery",
                    "Verify WiFi connection",
                    "Restart FYTA Hub if present"
                ]
            }
    except Exception:
        pass

    return None


def detect_battery_low(current_plant: Dict, low_threshold: float = 20.0) -> Optional[Dict]:
    """
    Detect low battery in sensor

    Args:
        current_plant: Current plant data
        low_threshold: Battery percentage threshold

    Returns:
        Event dict if battery low, None otherwise
    """
    sensor_info = current_plant.get("sensor", {})
    battery_level = sensor_info.get("battery_level")

    if battery_level is not None and battery_level < low_threshold:
        if battery_level < 10:
            severity = "critical"
            priority = "high"
        elif battery_level < 15:
            severity = "warning"
            priority = "high"
        else:
            severity = "warning"
            priority = "medium"

        return {
            "event_type": "battery_low",
            "event_id": generate_event_id(current_plant["id"], "battery_low", datetime.now()),
            "timestamp": datetime.now().isoformat(),
            "plant_id": current_plant["id"],
            "plant_name": current_plant.get("nickname", "Unknown"),
            "battery_level": battery_level,
            "severity": severity,
            "priority": priority,
            "message": f"Sensor battery at {battery_level}%",
            "actionable": True,
            "suggested_actions": [
                "Replace sensor battery soon",
                "Order replacement batteries if needed"
            ]
        }

    return None


def detect_wifi_disconnect(current_plant: Dict, previous_state: Optional[Dict]) -> Optional[Dict]:
    """
    Detect WiFi connection loss

    Args:
        current_plant: Current plant data
        previous_state: Previous plant state

    Returns:
        Event dict if WiFi disconnected, None otherwise
    """
    current_wifi = current_plant.get("wifi_status", 1)

    if previous_state:
        previous_wifi = previous_state.get("wifi_status", 1)

        # 1 = connected, 0 = disconnected
        if previous_wifi == 1 and current_wifi == 0:
            return {
                "event_type": "wifi_disconnected",
                "event_id": generate_event_id(current_plant["id"], "wifi_disconnect", datetime.now()),
                "timestamp": datetime.now().isoformat(),
                "plant_id": current_plant["id"],
                "plant_name": current_plant.get("nickname", "Unknown"),
                "severity": "warning",
                "priority": "medium",
                "message": "Sensor lost WiFi connection",
                "actionable": True,
                "suggested_actions": [
                    "Check WiFi router",
                    "Move sensor closer to WiFi",
                    "Restart FYTA Hub"
                ]
            }

    return None


def detect_critical_moisture(current_plant: Dict, previous_state: Optional[Dict]) -> Optional[Dict]:
    """
    Detect critical moisture situations (watering urgency)

    Args:
        current_plant: Current plant data
        previous_state: Previous state for trend detection

    Returns:
        Event dict if critical moisture detected
    """
    moisture_status = current_plant.get("moisture_status", 2)

    # Status 1 = Too low (needs water)
    if moisture_status == 1:
        # Check if this is a new critical state or ongoing
        is_new = previous_state and previous_state.get("moisture_status", 2) != 1

        return {
            "event_type": "critical_moisture",
            "event_id": generate_event_id(current_plant["id"], "critical_moisture", datetime.now()),
            "timestamp": datetime.now().isoformat(),
            "plant_id": current_plant["id"],
            "plant_name": current_plant.get("nickname", "Unknown"),
            "severity": "critical",
            "priority": "immediate",
            "message": f"{'URGENT: ' if is_new else ''}Plant needs water NOW!",
            "actionable": True,
            "is_new_critical": is_new,
            "suggested_actions": [
                "Water the plant immediately",
                "Check soil with finger to confirm dryness",
                "Water thoroughly until it drains"
            ]
        }

    return None


def detect_temperature_extreme(current_plant: Dict) -> Optional[Dict]:
    """
    Detect extreme temperature (too hot - dangerous)

    Args:
        current_plant: Current plant data

    Returns:
        Event dict if extreme temperature detected
    """
    temp_status = current_plant.get("temperature_status", 2)

    # Status 3 = Too high
    if temp_status == 3:
        return {
            "event_type": "temperature_extreme",
            "event_id": generate_event_id(current_plant["id"], "temp_extreme", datetime.now()),
            "timestamp": datetime.now().isoformat(),
            "plant_id": current_plant["id"],
            "plant_name": current_plant.get("nickname", "Unknown"),
            "severity": "critical",
            "priority": "high",
            "message": "Temperature is too high - plant stress risk",
            "actionable": True,
            "suggested_actions": [
                "Move plant to cooler location",
                "Increase ventilation",
                "Mist leaves to cool down",
                "Check for direct sunlight exposure"
            ]
        }

    return None


def detect_all_events(current_plant: Dict, previous_state: Optional[Dict] = None,
                      config: Optional[Dict] = None) -> List[Dict]:
    """
    Run all event detectors and return all detected events

    Args:
        current_plant: Current plant data
        previous_state: Previous plant state for comparison
        config: Configuration for thresholds

    Returns:
        List of all detected events
    """
    if config is None:
        config = {
            "silence_threshold_minutes": 90,
            "battery_threshold": 20.0
        }

    events = []

    # Status changes
    if previous_state:
        events.extend(detect_status_changes(current_plant, previous_state))

    # Sensor silence
    silence_event = detect_sensor_silence(
        current_plant,
        config.get("silence_threshold_minutes", 90)
    )
    if silence_event:
        events.append(silence_event)

    # Battery low
    battery_event = detect_battery_low(
        current_plant,
        config.get("battery_threshold", 20.0)
    )
    if battery_event:
        events.append(battery_event)

    # WiFi disconnect
    if previous_state:
        wifi_event = detect_wifi_disconnect(current_plant, previous_state)
        if wifi_event:
            events.append(wifi_event)

    # Critical moisture
    moisture_event = detect_critical_moisture(current_plant, previous_state)
    if moisture_event:
        events.append(moisture_event)

    # Temperature extreme
    temp_event = detect_temperature_extreme(current_plant)
    if temp_event:
        events.append(temp_event)

    return events


def filter_events(events: List[Dict], filters: Optional[Dict] = None) -> List[Dict]:
    """
    Filter events based on criteria

    Args:
        events: List of events
        filters: Filter criteria (severity, priority, event_type, plant_id)

    Returns:
        Filtered list of events
    """
    if not filters:
        return events

    filtered = events

    if "severity" in filters:
        allowed_severities = filters["severity"] if isinstance(filters["severity"], list) else [filters["severity"]]
        filtered = [e for e in filtered if e.get("severity") in allowed_severities]

    if "priority" in filters:
        allowed_priorities = filters["priority"] if isinstance(filters["priority"], list) else [filters["priority"]]
        filtered = [e for e in filtered if e.get("priority") in allowed_priorities]

    if "event_type" in filters:
        allowed_types = filters["event_type"] if isinstance(filters["event_type"], list) else [filters["event_type"]]
        filtered = [e for e in filtered if e.get("event_type") in allowed_types]

    if "plant_id" in filters:
        plant_ids = filters["plant_id"] if isinstance(filters["plant_id"], list) else [filters["plant_id"]]
        filtered = [e for e in filtered if e.get("plant_id") in plant_ids]

    if "actionable" in filters:
        filtered = [e for e in filtered if e.get("actionable") == filters["actionable"]]

    return filtered


def format_event_for_webhook(event: Dict) -> Dict:
    """
    Format event for webhook/automation systems (n8n, Home Assistant, etc.)

    Args:
        event: Event dictionary

    Returns:
        Webhook-friendly format
    """
    return {
        "id": event["event_id"],
        "type": event["event_type"],
        "timestamp": event["timestamp"],
        "plant": {
            "id": event["plant_id"],
            "name": event.get("plant_name", "Unknown")
        },
        "severity": event["severity"],
        "priority": event["priority"],
        "message": event["message"],
        "actionable": event.get("actionable", False),
        "actions": event.get("suggested_actions", []),
        "metadata": {k: v for k, v in event.items()
                    if k not in ["event_id", "event_type", "timestamp", "plant_id",
                                "plant_name", "severity", "priority", "message",
                                "actionable", "suggested_actions"]}
    }
