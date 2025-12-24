"""
Intelligent Watering Predictions

Analyzes moisture trends to predict when plants need watering.
Similar to fertilization.py but for moisture/watering.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import statistics


def get_moisture_status(moisture_value: float, substrate_type: Optional[str] = None) -> Dict:
    """
    Evaluate moisture status with substrate-specific thresholds.

    Args:
        moisture_value: Current moisture percentage (0-100)
        substrate_type: Type of substrate (organic, mineral, lechuza_pon, etc.)

    Returns:
        Dict with status, severity, and recommendation
    """
    # Substrate-specific optimal ranges
    optimal_ranges = {
        "organic": (40, 70),
        "mineral": (30, 60),
        "lechuza_pon": (30, 70),
        "semi_hydro": (20, 50),
        "hydroponic": (100, 100),  # Always wet
    }

    # Get optimal range for substrate, or use generic
    min_optimal, max_optimal = optimal_ranges.get(substrate_type, (30, 70))

    # Critical thresholds
    critical_low = 15  # Plant is severely stressed
    critical_high = 90  # Risk of root rot

    if moisture_value < critical_low:
        return {
            "status": "critical_low",
            "severity": "critical",
            "description": f"Moisture {moisture_value}% is critically low",
            "emoji": "🔴",
            "action_needed": "immediate",
            "explanation": "Plant is severely dehydrated. Water immediately and thoroughly."
        }
    elif moisture_value < min_optimal:
        return {
            "status": "low",
            "severity": "moderate",
            "description": f"Moisture {moisture_value}% is low",
            "emoji": "⚠️",
            "action_needed": "soon",
            "explanation": "Soil is drying out. Water within 1-2 days."
        }
    elif moisture_value <= max_optimal:
        return {
            "status": "optimal",
            "severity": "none",
            "description": f"Moisture {moisture_value}% is optimal",
            "emoji": "✅",
            "action_needed": "none",
            "explanation": "Moisture level is perfect. Continue current watering schedule."
        }
    elif moisture_value <= critical_high:
        return {
            "status": "high",
            "severity": "moderate",
            "description": f"Moisture {moisture_value}% is high",
            "emoji": "⚠️",
            "action_needed": "monitor",
            "explanation": "Soil is very wet. Skip next watering. Ensure good drainage."
        }
    else:
        return {
            "status": "critical_high",
            "severity": "critical",
            "description": f"Moisture {moisture_value}% is dangerously high",
            "emoji": "🔴",
            "action_needed": "urgent",
            "explanation": "Risk of root rot! Improve drainage immediately. Consider repotting if it persists."
        }


def analyze_moisture_trend(measurements: List[Dict], days: int = 7) -> Dict:
    """
    Analyze moisture trend over time to predict when watering is needed.

    Args:
        measurements: List of measurement dicts with timestamp and soil_moisture
        days: Number of days to analyze (default: 7)

    Returns:
        Dict with trend analysis and prediction
    """
    result = {
        "analyzed": False,
        "days_analyzed": days,
        "data_points": 0,
        "current_moisture": None,
        "initial_moisture": None,
        "change": None,
        "trend": "unknown",
        "slope_per_day": None,
        "confidence": 0.0,
        "prediction": None
    }

    if not measurements or len(measurements) < 2:
        return result

    # Filter to last N days
    cutoff_date = datetime.now() - timedelta(days=days)
    recent_measurements = []

    for m in measurements:
        # FYTA uses different field names - try all variants
        timestamp_value = m.get("date_utc") or m.get("timestamp") or m.get("measured_at")
        moisture_value = m.get("soil_moisture") or m.get("moisture")

        if not timestamp_value or moisture_value is None:
            continue

        try:
            ts = datetime.fromisoformat(timestamp_value.replace("Z", ""))
            if ts >= cutoff_date:
                recent_measurements.append({
                    "timestamp": ts,
                    "moisture": float(moisture_value)
                })
        except Exception:
            continue

    if len(recent_measurements) < 2:
        return result

    # Sort by timestamp
    recent_measurements.sort(key=lambda x: x["timestamp"])

    # Get moisture values
    moisture_values = [m["moisture"] for m in recent_measurements]
    current_moisture = moisture_values[-1]
    initial_moisture = moisture_values[0]

    result["analyzed"] = True
    result["data_points"] = len(recent_measurements)
    result["current_moisture"] = round(current_moisture, 1)
    result["initial_moisture"] = round(initial_moisture, 1)
    result["change"] = round(current_moisture - initial_moisture, 1)
    result["first_measurement"] = recent_measurements[0]["timestamp"].isoformat()
    result["last_measurement"] = recent_measurements[-1]["timestamp"].isoformat()

    # Calculate linear regression (slope)
    if len(moisture_values) >= 3:
        try:
            # Convert timestamps to days since first measurement
            first_ts = recent_measurements[0]["timestamp"]
            x_values = [(m["timestamp"] - first_ts).total_seconds() / 86400.0 for m in recent_measurements]
            y_values = moisture_values

            # Linear regression
            n = len(x_values)
            sum_x = sum(x_values)
            sum_y = sum(y_values)
            sum_xy = sum(x * y for x, y in zip(x_values, y_values))
            sum_x2 = sum(x * x for x in x_values)

            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            result["slope_per_day"] = round(slope, 3)

            # Determine trend
            if abs(slope) < 0.5:
                result["trend"] = "stable"
            elif slope < 0:
                result["trend"] = "decreasing"
            else:
                result["trend"] = "increasing"

            # Calculate confidence based on data consistency
            # R-squared calculation
            mean_y = sum_y / n
            ss_tot = sum((y - mean_y) ** 2 for y in y_values)
            ss_res = sum((y_values[i] - (slope * x_values[i] + (sum_y - slope * sum_x) / n)) ** 2 for i in range(n))

            if ss_tot > 0:
                r_squared = 1 - (ss_res / ss_tot)
                result["confidence"] = round(abs(r_squared), 2)
            else:
                result["confidence"] = 0.0

        except Exception:
            pass

    # Predict when watering is needed (if moisture is decreasing)
    if result["trend"] == "decreasing" and result["slope_per_day"] is not None and result["slope_per_day"] < 0:
        # Critical threshold: 20% moisture
        critical_moisture = 20
        # Optimal threshold: 30% moisture
        optimal_moisture = 30

        moisture_to_critical = current_moisture - critical_moisture
        moisture_to_optimal = current_moisture - optimal_moisture

        if moisture_to_critical > 0 and result["slope_per_day"] < 0:
            days_until_critical = moisture_to_critical / abs(result["slope_per_day"])
            critical_date = datetime.now() + timedelta(days=days_until_critical)

            days_until_optimal = None
            if moisture_to_optimal > 0:
                days_until_optimal = moisture_to_optimal / abs(result["slope_per_day"])

            result["prediction"] = {
                "days_until_critical": round(days_until_critical, 1),
                "critical_date": critical_date.strftime("%Y-%m-%d"),
                "days_until_optimal": round(days_until_optimal, 1) if days_until_optimal else None,
                "recommended_watering_date": (datetime.now() + timedelta(days=days_until_optimal)).strftime("%Y-%m-%d") if days_until_optimal else critical_date.strftime("%Y-%m-%d")
            }

    # Calculate consumption rate (moisture loss per day)
    if result["trend"] == "decreasing" and result["slope_per_day"] is not None:
        moisture_per_day = abs(result["slope_per_day"])
        moisture_per_week = moisture_per_day * 7

        result["consumption_rate"] = {
            "moisture_per_day": round(moisture_per_day, 2),
            "moisture_per_week": round(moisture_per_week, 1),
            "description": f"Plant consumes ~{round(moisture_per_week, 1)}% moisture per week"
        }

    return result


def get_watering_recommendation(
    current_moisture: float,
    moisture_trend: Optional[Dict] = None,
    substrate_type: Optional[str] = None,
    last_watered: Optional[str] = None
) -> Dict:
    """
    Generate comprehensive watering recommendation.

    Args:
        current_moisture: Current moisture percentage
        moisture_trend: Moisture trend analysis from analyze_moisture_trend()
        substrate_type: Type of substrate
        last_watered: ISO date string of last watering

    Returns:
        Dict with recommendation, timing, and advice
    """
    # Get current moisture status
    moisture_status = get_moisture_status(current_moisture, substrate_type)

    recommendation = {
        "current_status": moisture_status,
        "action": None,
        "timing": None,
        "amount": None,
        "reasoning": [],
        "warnings": []
    }

    # Analyze last watering
    days_since_watering = None
    if last_watered:
        try:
            last_water_date = datetime.fromisoformat(last_watered.replace("Z", ""))
            days_since_watering = (datetime.now() - last_water_date).days
            recommendation["days_since_watering"] = days_since_watering
        except Exception:
            pass

    # Generate recommendation based on moisture status
    if moisture_status["action_needed"] == "immediate":
        recommendation["action"] = "water_now"
        recommendation["timing"] = "Immediately"
        recommendation["amount"] = "Water thoroughly until water drains from bottom"
        recommendation["reasoning"].append(f"Moisture critically low at {current_moisture}%")

        if moisture_trend and moisture_trend.get("trend") == "decreasing":
            recommendation["reasoning"].append(
                f"Moisture declining rapidly at {abs(moisture_trend.get('slope_per_day', 0))}% per day"
            )

    elif moisture_status["action_needed"] == "soon":
        recommendation["action"] = "water_soon"
        recommendation["timing"] = "Within 1-2 days"
        recommendation["amount"] = "Water normally until soil is evenly moist"
        recommendation["reasoning"].append(f"Moisture low at {current_moisture}%")

        if moisture_trend and moisture_trend.get("prediction"):
            pred = moisture_trend["prediction"]
            if pred.get("days_until_optimal"):
                recommendation["timing"] = f"On {pred['recommended_watering_date']} ({round(pred['days_until_optimal'])} days)"
                recommendation["reasoning"].append(
                    f"Based on current trend, moisture will reach optimal watering threshold in {round(pred['days_until_optimal'])} days"
                )

    elif moisture_status["action_needed"] == "none":
        recommendation["action"] = "maintain"
        recommendation["timing"] = "Continue regular schedule"
        recommendation["amount"] = "Water when top 2-3cm of soil is dry"
        recommendation["reasoning"].append(f"Moisture optimal at {current_moisture}%")

        if moisture_trend and moisture_trend.get("consumption_rate"):
            consumption = moisture_trend["consumption_rate"]
            recommendation["reasoning"].append(
                f"{consumption['description']}. Monitor regularly."
            )

        if moisture_trend and moisture_trend.get("prediction"):
            pred = moisture_trend["prediction"]
            if pred.get("days_until_optimal"):
                recommendation["reasoning"].append(
                    f"Next watering estimated in ~{round(pred['days_until_optimal'])} days ({pred['recommended_watering_date']})"
                )

    elif moisture_status["action_needed"] == "monitor":
        recommendation["action"] = "skip_watering"
        recommendation["timing"] = "Skip next 1-2 scheduled waterings"
        recommendation["amount"] = "None - let soil dry out"
        recommendation["reasoning"].append(f"Moisture high at {current_moisture}%")
        recommendation["warnings"].append("Ensure pot has good drainage to prevent root rot")

    elif moisture_status["action_needed"] == "urgent":
        recommendation["action"] = "improve_drainage"
        recommendation["timing"] = "Urgent - act today"
        recommendation["amount"] = "Stop watering immediately"
        recommendation["reasoning"].append(f"Moisture dangerously high at {current_moisture}%")
        recommendation["warnings"].append("Risk of root rot! Check for drainage issues")
        recommendation["warnings"].append("Consider repotting if drainage is poor")

    # Add substrate-specific advice
    if substrate_type:
        if substrate_type in ["lechuza_pon", "semi_hydro"]:
            recommendation["substrate_note"] = "Mineral substrate holds water differently than soil. Adjust watering frequency accordingly."
        elif substrate_type == "organic":
            recommendation["substrate_note"] = "Organic soil contains nutrients. Fertilize less frequently than mineral substrates."

    return recommendation
