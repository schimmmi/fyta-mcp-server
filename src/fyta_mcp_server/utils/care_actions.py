"""
Care Action Tracking and Learning System

Tracks manual care actions (watering, fertilizing, repotting) that FYTA doesn't know about.
Enables correlation analysis and intelligent recommendations based on care history.
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path


class CareActionStore:
    """Simple file-based storage for care actions"""

    def __init__(self, storage_path: Optional[str] = None):
        if storage_path is None:
            # Default to user's home directory
            home = Path.home()
            storage_dir = home / ".fyta_mcp"
            storage_dir.mkdir(exist_ok=True)
            self.storage_path = storage_dir / "care_actions.json"
        else:
            self.storage_path = Path(storage_path)

        self._ensure_storage()

    def _ensure_storage(self):
        """Ensure storage file exists"""
        if not self.storage_path.exists():
            self.storage_path.write_text(json.dumps({"actions": []}, indent=2))

    def _load_actions(self) -> List[Dict]:
        """Load all care actions from storage"""
        try:
            data = json.loads(self.storage_path.read_text())
            return data.get("actions", [])
        except Exception:
            return []

    def _save_actions(self, actions: List[Dict]):
        """Save all care actions to storage"""
        self.storage_path.write_text(json.dumps({"actions": actions}, indent=2))

    def log_action(self, plant_id: int, action_type: str, metadata: Optional[Dict] = None) -> Dict:
        """
        Log a care action

        Args:
            plant_id: Plant ID
            action_type: Type of action (watering, fertilizing, repotting, etc.)
            metadata: Additional metadata (amount, product, notes, etc.)

        Returns:
            The logged action with generated ID
        """
        actions = self._load_actions()

        action = {
            "id": len(actions) + 1,
            "plant_id": plant_id,
            "action_type": action_type,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        actions.append(action)
        self._save_actions(actions)

        return action

    def get_plant_history(self, plant_id: int, days: Optional[int] = None,
                         action_type: Optional[str] = None) -> List[Dict]:
        """
        Get care history for a plant

        Args:
            plant_id: Plant ID
            days: Limit to last N days
            action_type: Filter by action type

        Returns:
            List of care actions
        """
        actions = self._load_actions()

        # Filter by plant
        plant_actions = [a for a in actions if a["plant_id"] == plant_id]

        # Filter by action type
        if action_type:
            plant_actions = [a for a in plant_actions if a["action_type"] == action_type]

        # Filter by date
        if days:
            cutoff = datetime.now() - timedelta(days=days)
            plant_actions = [
                a for a in plant_actions
                if datetime.fromisoformat(a["timestamp"]) >= cutoff
            ]

        # Sort by timestamp (newest first)
        plant_actions.sort(key=lambda x: x["timestamp"], reverse=True)

        return plant_actions

    def get_all_actions(self, days: Optional[int] = None) -> List[Dict]:
        """Get all care actions, optionally filtered by days"""
        actions = self._load_actions()

        if days:
            cutoff = datetime.now() - timedelta(days=days)
            actions = [
                a for a in actions
                if datetime.fromisoformat(a["timestamp"]) >= cutoff
            ]

        actions.sort(key=lambda x: x["timestamp"], reverse=True)
        return actions


def analyze_watering_effectiveness(care_history: List[Dict], measurements: List[Dict]) -> Dict:
    """
    Analyze if watering actions effectively improved moisture

    Args:
        care_history: List of care actions
        measurements: List of sensor measurements

    Returns:
        Analysis of watering effectiveness
    """
    watering_actions = [a for a in care_history if a["action_type"] == "watering"]

    if not watering_actions or not measurements:
        return {
            "analyzed": False,
            "message": "Insufficient data for analysis"
        }

    effectiveness_scores = []

    for action in watering_actions:
        action_time = datetime.fromisoformat(action["timestamp"])

        # Find moisture measurements before and after watering
        before_measurements = []
        after_measurements = []

        for m in measurements:
            try:
                # Try multiple possible timestamp field names (FYTA uses "date_utc")
                timestamp_str = None
                for field in ["date_utc", "measured_at", "timestamp", "created_at", "date", "time"]:
                    if field in m and m[field]:
                        timestamp_str = m[field]
                        break

                if not timestamp_str:
                    continue

                # FYTA returns timestamp as string without timezone, assume UTC
                if "T" in timestamp_str:
                    m_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                else:
                    # Handle "2025-12-23 20:00:55" format
                    m_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

                # FYTA uses "soil_moisture" not "moisture"
                moisture = m.get("soil_moisture") or m.get("moisture")

                # 6 hours before watering
                if action_time - timedelta(hours=6) <= m_time < action_time:
                    if moisture is not None:
                        before_measurements.append(moisture)

                # 6-24 hours after watering
                elif action_time < m_time <= action_time + timedelta(hours=24):
                    if moisture is not None:
                        after_measurements.append(moisture)
            except Exception:
                continue

        if before_measurements and after_measurements:
            avg_before = sum(before_measurements) / len(before_measurements)
            avg_after = sum(after_measurements) / len(after_measurements)

            improvement = avg_after - avg_before
            improvement_percent = (improvement / avg_before * 100) if avg_before > 0 else 0

            effectiveness_scores.append({
                "timestamp": action["timestamp"],
                "moisture_before": round(avg_before, 1),
                "moisture_after": round(avg_after, 1),
                "improvement": round(improvement, 1),
                "improvement_percent": round(improvement_percent, 1),
                "effective": improvement > 0
            })

    if not effectiveness_scores:
        return {
            "analyzed": False,
            "message": "No watering actions with corresponding sensor data found"
        }

    avg_improvement = sum(s["improvement_percent"] for s in effectiveness_scores) / len(effectiveness_scores)
    effective_count = sum(1 for s in effectiveness_scores if s["effective"])

    return {
        "analyzed": True,
        "total_watering_events": len(effectiveness_scores),
        "effective_events": effective_count,
        "effectiveness_rate": round(effective_count / len(effectiveness_scores) * 100, 1),
        "average_improvement_percent": round(avg_improvement, 1),
        "recent_events": effectiveness_scores[:5],  # Last 5
        "recommendation": get_watering_recommendation(avg_improvement, effective_count, len(effectiveness_scores))
    }


def get_watering_recommendation(avg_improvement: float, effective_count: int, total_count: int) -> str:
    """Generate watering recommendation based on effectiveness"""
    effectiveness_rate = (effective_count / total_count * 100) if total_count > 0 else 0

    if effectiveness_rate > 80 and avg_improvement > 15:
        return "Excellent watering technique! Moisture improves significantly after watering."
    elif effectiveness_rate > 60 and avg_improvement > 10:
        return "Good watering habits. Consider watering slightly more thoroughly for better results."
    elif effectiveness_rate < 50:
        return "Watering may not be effective enough. Ensure water reaches the root zone thoroughly."
    elif avg_improvement < 5:
        return "Moisture improvement is minimal. Check for drainage issues or increase water amount."
    else:
        return "Watering effectiveness is moderate. Monitor and adjust amount as needed."


def calculate_watering_frequency(care_history: List[Dict]) -> Dict:
    """
    Calculate watering frequency and patterns

    Args:
        care_history: List of care actions

    Returns:
        Watering frequency analysis
    """
    watering_actions = [a for a in care_history if a["action_type"] == "watering"]

    if len(watering_actions) < 2:
        return {
            "insufficient_data": True,
            "message": "Need at least 2 watering events to calculate frequency"
        }

    # Calculate intervals between waterings
    watering_actions.sort(key=lambda x: x["timestamp"])

    intervals = []
    for i in range(1, len(watering_actions)):
        prev_time = datetime.fromisoformat(watering_actions[i-1]["timestamp"])
        curr_time = datetime.fromisoformat(watering_actions[i]["timestamp"])
        interval_days = (curr_time - prev_time).total_seconds() / 86400
        intervals.append(interval_days)

    avg_interval = sum(intervals) / len(intervals)
    min_interval = min(intervals)
    max_interval = max(intervals)

    # Calculate consistency (coefficient of variation)
    if avg_interval > 0:
        std_dev = (sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)) ** 0.5
        consistency = (std_dev / avg_interval) * 100
    else:
        consistency = 0

    # Determine consistency level
    if consistency < 20:
        consistency_level = "very_consistent"
    elif consistency < 40:
        consistency_level = "consistent"
    elif consistency < 60:
        consistency_level = "moderately_variable"
    else:
        consistency_level = "highly_variable"

    return {
        "total_watering_events": len(watering_actions),
        "average_interval_days": round(avg_interval, 1),
        "min_interval_days": round(min_interval, 1),
        "max_interval_days": round(max_interval, 1),
        "consistency_score": round(100 - consistency, 1),
        "consistency_level": consistency_level,
        "last_watered": watering_actions[-1]["timestamp"],
        "next_watering_estimate": (
            datetime.fromisoformat(watering_actions[-1]["timestamp"]) +
            timedelta(days=avg_interval)
        ).isoformat()
    }


def correlate_fertilizing_with_growth(care_history: List[Dict], measurements: List[Dict]) -> Dict:
    """
    Analyze correlation between fertilizing and plant health improvements

    Args:
        care_history: List of care actions
        measurements: List of sensor measurements

    Returns:
        Correlation analysis
    """
    fertilizing_actions = [a for a in care_history if a["action_type"] == "fertilizing"]

    if not fertilizing_actions or not measurements:
        return {
            "analyzed": False,
            "message": "Insufficient data for fertilizing analysis"
        }

    # For each fertilizing action, track nutrient/salinity levels before and after
    results = []

    for action in fertilizing_actions:
        action_time = datetime.fromisoformat(action["timestamp"])

        before_nutrients = []
        after_nutrients = []

        for m in measurements:
            try:
                # Try multiple possible timestamp field names (FYTA uses "date_utc")
                timestamp_str = None
                for field in ["date_utc", "measured_at", "timestamp", "created_at", "date", "time"]:
                    if field in m and m[field]:
                        timestamp_str = m[field]
                        break

                if not timestamp_str:
                    continue

                # FYTA returns timestamp as string without timezone, assume UTC
                if "T" in timestamp_str:
                    m_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                else:
                    # Handle "2025-12-23 20:00:55" format
                    m_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

                # FYTA uses "soil_fertility" not "salinity"
                nutrients = m.get("soil_fertility") or m.get("salinity")

                # 1 week before
                if action_time - timedelta(days=7) <= m_time < action_time:
                    if nutrients is not None:
                        before_nutrients.append(nutrients)

                # 1-2 weeks after
                elif action_time + timedelta(days=1) <= m_time <= action_time + timedelta(days=14):
                    if nutrients is not None:
                        after_nutrients.append(nutrients)
            except Exception:
                continue

        if before_nutrients and after_nutrients:
            avg_before = sum(before_nutrients) / len(before_nutrients)
            avg_after = sum(after_nutrients) / len(after_nutrients)

            results.append({
                "timestamp": action["timestamp"],
                "product": action.get("metadata", {}).get("product", "Unknown"),
                "nutrient_before": round(avg_before, 1),
                "nutrient_after": round(avg_after, 1),
                "change": round(avg_after - avg_before, 1)
            })

    if not results:
        return {
            "analyzed": False,
            "message": "No fertilizing events with corresponding sensor data"
        }

    return {
        "analyzed": True,
        "total_fertilizing_events": len(results),
        "recent_events": results[:5],
        "recommendation": "Continue monitoring nutrient levels after fertilizing to optimize timing and amount."
    }


def get_care_insights(care_history: List[Dict], plant_data: Dict) -> List[Dict]:
    """
    Generate actionable insights based on care history

    Args:
        care_history: Care action history
        plant_data: Current plant data

    Returns:
        List of insights
    """
    insights = []

    # Check last watering
    last_watering = next((a for a in care_history if a["action_type"] == "watering"), None)

    if last_watering:
        last_water_time = datetime.fromisoformat(last_watering["timestamp"])
        days_since_water = (datetime.now() - last_water_time).total_seconds() / 86400

        moisture_status = plant_data.get("moisture_status", 2)

        if days_since_water > 7 and moisture_status == 1:
            insights.append({
                "type": "warning",
                "category": "watering",
                "message": f"Last watered {int(days_since_water)} days ago and moisture is low. Water soon!",
                "priority": "high"
            })
        elif days_since_water < 1 and moisture_status == 3:
            insights.append({
                "type": "info",
                "category": "watering",
                "message": "Recently watered but moisture is high. Check drainage or reduce amount next time.",
                "priority": "medium"
            })

    # Check fertilizing schedule
    last_fertilizing = next((a for a in care_history if a["action_type"] == "fertilizing"), None)

    if last_fertilizing:
        last_fert_time = datetime.fromisoformat(last_fertilizing["timestamp"])
        days_since_fert = (datetime.now() - last_fert_time).total_seconds() / 86400

        if days_since_fert > 60:
            insights.append({
                "type": "info",
                "category": "fertilizing",
                "message": f"Last fertilized {int(days_since_fert)} days ago. Consider fertilizing soon.",
                "priority": "low"
            })

    # Check repotting
    last_repotting = next((a for a in care_history if a["action_type"] == "repotting"), None)

    if last_repotting:
        last_repot_time = datetime.fromisoformat(last_repotting["timestamp"])
        months_since_repot = (datetime.now() - last_repot_time).total_seconds() / (86400 * 30)

        if months_since_repot > 24:
            insights.append({
                "type": "info",
                "category": "repotting",
                "message": f"Last repotted {int(months_since_repot)} months ago. Consider repotting next spring.",
                "priority": "low"
            })

    return insights
