"""
Intelligent Fertilization Recommendations

FYTA's fertilization recommendations are too simplistic (e.g., "fertilize in 190 days").
This module analyzes actual EC/soil_fertility values and trends to provide smart,
data-driven fertilization advice.

EC (Electrical Conductivity) / Soil Fertility Scale:
- 0.0 - 0.2: Very low - Urgent fertilization needed
- 0.2 - 0.6: Low - Fertilization recommended soon
- 0.6 - 1.0: Optimal - Well fertilized
- 1.0 - 1.5: High - Reduce fertilization
- 1.5+: Very high - Risk of nutrient burn, flush soil

Winter (Nov-Feb): Plants prefer lower end of range (0.2-1.0 mS/cm)

Different substrates have different EC requirements:
- Organic soil: 0.8 - 1.2 optimal
- Mineral substrates: 0.6 - 1.0 optimal
- Hydro/Semi-hydro: 0.4 - 0.8 optimal
- Lechuza PON: 0.5 - 0.9 optimal
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


def get_ec_status(ec_value: float, substrate_type: Optional[str] = None, consider_season: bool = True) -> Dict:
    """
    Evaluate EC/soil_fertility status with substrate-specific thresholds.

    Args:
        ec_value: Current EC value (mS/cm or equivalent)
        substrate_type: Type of substrate (organic, mineral, lechuza_pon, hydroponic, etc.)
        consider_season: If True, adjusts critical thresholds for winter dormancy (default: True)

    Returns:
        Dict with status, severity, and recommendation
    """
    # Substrate-specific optimal ranges
    optimal_ranges = {
        "organic": (0.8, 1.2),
        "mineral": (0.6, 1.0),
        "hydroponic": (0.4, 0.8),
        "semi_hydro": (0.4, 0.8),
        "lechuza_pon": (0.5, 0.9),
    }

    # Get optimal range for substrate, or use generic
    min_optimal, max_optimal = optimal_ranges.get(substrate_type, (0.6, 1.0))

    # Critical thresholds (substrate-independent)
    critical_low = 0.2  # Below 0.2 mS/cm = nutrient deficiency
    critical_high = 1.5

    # Adjust for winter dormancy (November-February in Northern Hemisphere)
    if consider_season:
        current_month = datetime.now().month
        is_winter = current_month in [11, 12, 1, 2]

        if is_winter:
            # In winter, plants still need nutrients but prefer lower end of range
            # Use more conservative thresholds: 0.2-1.0 mS/cm
            critical_low = 0.2  # Plants still need minimum nutrients
            min_optimal = max(0.2, min_optimal * 0.5)  # Lower end of optimal range
            max_optimal = min(1.0, max_optimal)  # Cap at 1.0 in winter

    if ec_value < critical_low:
        return {
            "status": "critical_low",
            "severity": "critical",
            "description": f"EC {ec_value} is critically low",
            "emoji": "🔴",
            "action_needed": "immediate",
            "explanation": "Plants are nutrient-starved. Fertilize within 1-2 days."
        }
    elif ec_value < min_optimal:
        return {
            "status": "low",
            "severity": "moderate",
            "description": f"EC {ec_value} is low",
            "emoji": "⚠️",
            "action_needed": "soon",
            "explanation": "Nutrient levels are declining. Fertilize within 1 week."
        }
    elif ec_value <= max_optimal:
        return {
            "status": "optimal",
            "severity": "none",
            "description": f"EC {ec_value} is optimal",
            "emoji": "✅",
            "action_needed": "none",
            "explanation": "Nutrient levels are perfect. Continue current fertilization schedule."
        }
    elif ec_value <= critical_high:
        return {
            "status": "high",
            "severity": "moderate",
            "description": f"EC {ec_value} is high",
            "emoji": "⚠️",
            "action_needed": "reduce",
            "explanation": "Too many nutrients. Skip next fertilization. Consider light watering to dilute."
        }
    else:
        return {
            "status": "critical_high",
            "severity": "critical",
            "description": f"EC {ec_value} is dangerously high",
            "emoji": "🔴",
            "action_needed": "flush",
            "explanation": "Risk of nutrient burn! Flush soil with 2-3x pot volume of water immediately."
        }


def analyze_ec_trend(measurements: List[Dict], days: int = 30) -> Dict:
    """
    Analyze EC trend over time to predict when fertilization is needed.

    Args:
        measurements: List of measurement dicts with timestamp and soil_fertility
        days: Number of days to analyze (default: 30)

    Returns:
        Dict with trend analysis and predictions
    """
    if not measurements:
        return {
            "analyzed": False,
            "message": "No measurements available"
        }

    # Extract EC values with timestamps
    ec_data = []
    cutoff_date = datetime.now() - timedelta(days=days)

    for m in measurements:
        try:
            # Get timestamp
            timestamp_str = None
            for field in ["date_utc", "measured_at", "timestamp", "created_at"]:
                if field in m and m[field]:
                    timestamp_str = m[field]
                    break

            if not timestamp_str:
                continue

            # Parse timestamp
            if "T" in timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            else:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

            # Skip old data
            if timestamp < cutoff_date:
                continue

            # Get EC value
            ec = m.get("soil_fertility") or m.get("salinity")
            if ec is not None:
                ec_data.append((timestamp, float(ec)))

        except Exception:
            continue

    if len(ec_data) < 3:
        return {
            "analyzed": False,
            "message": "Insufficient data for trend analysis (need at least 3 measurements)"
        }

    # Sort by timestamp
    ec_data.sort(key=lambda x: x[0])

    # Calculate trend using linear regression
    timestamps_numeric = [(t - ec_data[0][0]).total_seconds() / 3600 for t, _ in ec_data]
    ec_values = [ec for _, ec in ec_data]

    n = len(timestamps_numeric)
    sum_x = sum(timestamps_numeric)
    sum_y = sum(ec_values)
    sum_xy = sum(x * y for x, y in zip(timestamps_numeric, ec_values))
    sum_x2 = sum(x * x for x in timestamps_numeric)

    # Linear regression: y = mx + b
    denominator = n * sum_x2 - sum_x * sum_x
    if denominator == 0:
        slope = 0
    else:
        slope = (n * sum_xy - sum_x * sum_y) / denominator

    # Slope is EC change per hour, convert to per day
    slope_per_day = slope * 24

    # Current and initial EC
    current_ec = ec_values[-1]
    initial_ec = ec_values[0]

    # Trend direction
    if abs(slope_per_day) < 0.01:
        direction = "stable"
    elif slope_per_day > 0:
        direction = "increasing"
    else:
        direction = "decreasing"

    # Calculate R² for confidence
    y_mean = sum_y / n
    ss_tot = sum((y - y_mean) ** 2 for y in ec_values)
    y_pred = [slope * x + (sum_y - slope * sum_x) / n for x in timestamps_numeric]
    ss_res = sum((y_actual - y_pred[i]) ** 2 for i, y_actual in enumerate(ec_values))

    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

    result = {
        "analyzed": True,
        "days_analyzed": days,
        "data_points": n,
        "current_ec": round(current_ec, 2),
        "initial_ec": round(initial_ec, 2),
        "change": round(current_ec - initial_ec, 2),
        "trend": direction,
        "slope_per_day": round(slope_per_day, 4),
        "confidence": round(r_squared, 2),
        "first_measurement": ec_data[0][0].isoformat(),
        "last_measurement": ec_data[-1][0].isoformat()
    }

    # Predict when EC will reach critical low (0.2)
    if direction == "decreasing" and current_ec > 0.2:
        days_until_critical = (current_ec - 0.2) / abs(slope_per_day)
        if days_until_critical > 0:
            critical_date = datetime.now() + timedelta(days=days_until_critical)
            result["prediction"] = {
                "days_until_critical": round(days_until_critical, 1),
                "critical_date": critical_date.date().isoformat(),
                "action": "fertilize_before",
                "urgency": "immediate" if days_until_critical < 3 else "high" if days_until_critical < 7 else "medium"
            }

    # Consumption rate (for stable/decreasing trends)
    if direction in ["decreasing", "stable"] and n > 1:
        days_elapsed = (ec_data[-1][0] - ec_data[0][0]).days
        if days_elapsed > 0:
            consumption_rate = abs(initial_ec - current_ec) / days_elapsed
            result["consumption_rate"] = {
                "ec_per_day": round(consumption_rate, 4),
                "description": f"Plant consumes ~{round(consumption_rate * 7, 2)} EC per week"
            }

    return result


def get_fertilization_recommendation(
    current_ec: float,
    ec_trend: Optional[Dict] = None,
    substrate_type: Optional[str] = None,
    last_fertilized: Optional[str] = None,
    care_history: Optional[List[Dict]] = None
) -> Dict:
    """
    Generate comprehensive fertilization recommendation.

    Args:
        current_ec: Current EC value
        ec_trend: EC trend analysis from analyze_ec_trend()
        substrate_type: Type of substrate
        last_fertilized: ISO date string of last fertilization
        care_history: Care action history (for fertilization frequency analysis)

    Returns:
        Dict with recommendation, timing, dosage advice
    """
    # Get current EC status
    ec_status = get_ec_status(current_ec, substrate_type)

    recommendation = {
        "current_status": ec_status,
        "action": None,
        "timing": None,
        "dosage": None,
        "reasoning": [],
        "warnings": []
    }

    # Analyze last fertilization
    days_since_fertilization = None
    if last_fertilized:
        try:
            last_fert_date = datetime.fromisoformat(last_fertilized.replace("Z", ""))
            days_since_fertilization = (datetime.now() - last_fert_date).days
            recommendation["days_since_fertilization"] = days_since_fertilization
        except Exception:
            pass

    # Analyze fertilization frequency from care history
    if care_history:
        fert_actions = [a for a in care_history if a.get("action_type") == "fertilizing"]
        if len(fert_actions) >= 2:
            # Calculate average interval
            intervals = []
            for i in range(1, len(fert_actions)):
                try:
                    date1 = datetime.fromisoformat(fert_actions[i-1]["timestamp"])
                    date2 = datetime.fromisoformat(fert_actions[i]["timestamp"])
                    intervals.append((date2 - date1).days)
                except Exception:
                    continue

            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                recommendation["average_fertilization_interval"] = round(avg_interval, 1)

    # Generate recommendation based on EC status
    if ec_status["action_needed"] == "immediate":
        recommendation["action"] = "fertilize_now"
        recommendation["timing"] = "Within 1-2 days"
        recommendation["dosage"] = "50-75% of recommended dosage (plant is weakened)"
        recommendation["reasoning"].append(f"EC critically low at {current_ec}")

        if ec_trend and ec_trend.get("analyzed"):
            if ec_trend["trend"] == "decreasing":
                recommendation["reasoning"].append(
                    f"EC declining at {abs(ec_trend['slope_per_day'])} per day - plant consuming nutrients rapidly"
                )

    elif ec_status["action_needed"] == "soon":
        recommendation["action"] = "fertilize_soon"
        recommendation["timing"] = "Within 1 week"
        recommendation["dosage"] = "Full recommended dosage"
        recommendation["reasoning"].append(f"EC low at {current_ec}")

        if ec_trend and ec_trend.get("prediction"):
            pred = ec_trend["prediction"]
            recommendation["timing"] = f"Before {pred['critical_date']} ({pred['days_until_critical']} days)"
            recommendation["reasoning"].append(
                f"Based on current trend, EC will reach critical level in {pred['days_until_critical']} days"
            )

    elif ec_status["action_needed"] == "none":
        recommendation["action"] = "maintain"
        recommendation["timing"] = "Continue regular schedule"
        recommendation["dosage"] = "Standard dosage when next scheduled"
        recommendation["reasoning"].append(f"EC optimal at {current_ec}")

        if ec_trend and ec_trend.get("consumption_rate"):
            consumption = ec_trend["consumption_rate"]
            recommendation["reasoning"].append(
                f"Plant consuming {consumption['description']}. Monitor weekly."
            )

    elif ec_status["action_needed"] == "reduce":
        recommendation["action"] = "skip_next"
        recommendation["timing"] = "Skip next 1-2 scheduled fertilizations"
        recommendation["dosage"] = "Reduce to 50% when resuming"
        recommendation["reasoning"].append(f"EC high at {current_ec}")
        recommendation["warnings"].append("Too much fertilizer can harm roots. Let plant use up existing nutrients.")

    elif ec_status["action_needed"] == "flush":
        recommendation["action"] = "flush_soil"
        recommendation["timing"] = "Immediately"
        recommendation["dosage"] = "No fertilizer! Flush with 2-3x pot volume of water"
        recommendation["reasoning"].append(f"EC critically high at {current_ec}")
        recommendation["warnings"].append(
            "🚨 Risk of nutrient burn! Water thoroughly to leach out excess salts. "
            "Wait 2-3 weeks before fertilizing again."
        )

    # Add substrate-specific advice
    if substrate_type:
        if substrate_type in ["mineral", "lechuza_pon"]:
            recommendation["reasoning"].append(
                f"Note: {substrate_type} substrates need regular fertilization (no nutrient storage)"
            )
        elif substrate_type == "organic":
            recommendation["reasoning"].append(
                "Organic soil contains nutrients. Fertilize less frequently than mineral substrates."
            )

    return recommendation


def format_recommendation_for_llm(recommendation: Dict) -> str:
    """
    Format fertilization recommendation in a human-readable way for LLM consumption.

    Args:
        recommendation: Output from get_fertilization_recommendation()

    Returns:
        Formatted string
    """
    status = recommendation["current_status"]
    lines = []

    lines.append(f"{status['emoji']} **EC Status**: {status['description']}")
    lines.append(f"**Action**: {recommendation['action'].replace('_', ' ').title()}")
    lines.append(f"**Timing**: {recommendation['timing']}")
    lines.append(f"**Dosage**: {recommendation['dosage']}")

    if recommendation.get("days_since_fertilization"):
        lines.append(f"**Last Fertilized**: {recommendation['days_since_fertilization']} days ago")

    if recommendation["reasoning"]:
        lines.append("\n**Reasoning**:")
        for reason in recommendation["reasoning"]:
            lines.append(f"  • {reason}")

    if recommendation["warnings"]:
        lines.append("\n**⚠️ Warnings**:")
        for warning in recommendation["warnings"]:
            lines.append(f"  • {warning}")

    return "\n".join(lines)
