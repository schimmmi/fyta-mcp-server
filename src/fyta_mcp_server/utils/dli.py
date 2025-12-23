"""
DLI (Daily Light Integral) analysis utilities

DLI = Daily Light Integral measured in mol/m²/day
It represents the total amount of photosynthetically active radiation (PAR)
that plants receive over a 24-hour period.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Tuple


def calculate_dli(light_values: List[float], hours: float) -> float:
    """
    Calculate DLI from light measurements

    Args:
        light_values: List of light measurements (μmol/m²/s)
        hours: Time period in hours

    Returns:
        DLI in mol/m²/day
    """
    if not light_values or hours <= 0:
        return 0.0

    # Average light intensity (μmol/m²/s)
    avg_light = sum(light_values) / len(light_values)

    # Convert to DLI: (μmol/m²/s) * (seconds) * (1 mol / 1,000,000 μmol)
    # DLI = avg_light * 3600 * hours / 1,000,000
    dli = (avg_light * 3600 * hours) / 1_000_000

    return round(dli, 2)


def calculate_daily_dlis(measurements: List[Dict]) -> List[Tuple[datetime, float]]:
    """
    Calculate DLI for each day from measurement data

    Args:
        measurements: List of measurement dictionaries with timestamp and 'light'

    Returns:
        List of (date, dli) tuples
    """
    if not measurements:
        return []

    # Group measurements by day
    daily_data = {}

    for measurement in measurements:
        try:
            # Try multiple possible timestamp field names (FYTA uses "date_utc")
            timestamp_str = None
            for field in ["date_utc", "measured_at", "timestamp", "created_at", "date", "time"]:
                if field in measurement and measurement[field]:
                    timestamp_str = measurement[field]
                    break

            if not timestamp_str:
                continue

            # FYTA returns timestamp as string without timezone, assume UTC
            if "T" in timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            else:
                # Handle "2025-12-23 20:00:55" format
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

            light = measurement.get("light")

            if light is None:
                continue

            # Get date (without time)
            date = timestamp.date()

            if date not in daily_data:
                daily_data[date] = []

            daily_data[date].append(light)
        except Exception:
            continue

    # Calculate DLI for each day
    daily_dlis = []
    for date, light_values in sorted(daily_data.items()):
        # Assume measurements cover the full day (24 hours)
        dli = calculate_dli(light_values, 24)
        daily_dlis.append((datetime.combine(date, datetime.min.time()), dli))

    return daily_dlis


def classify_dli_status(current_dli: float, min_dli: float, max_dli: float) -> Dict:
    """
    Classify DLI status relative to optimal range

    Args:
        current_dli: Current DLI value
        min_dli: Minimum optimal DLI
        max_dli: Maximum optimal DLI

    Returns:
        Dictionary with status classification
    """
    if current_dli < min_dli * 0.5:
        status = "critical_deficit"
        severity = "critical"
        message = f"DLI is critically low ({current_dli} vs min {min_dli})"
    elif current_dli < min_dli * 0.7:
        status = "severe_deficit"
        severity = "high"
        message = f"DLI is severely below optimal ({current_dli} vs min {min_dli})"
    elif current_dli < min_dli:
        status = "deficit"
        severity = "moderate"
        message = f"DLI is below optimal range ({current_dli} vs min {min_dli})"
    elif current_dli <= max_dli:
        status = "optimal"
        severity = "none"
        message = f"DLI is within optimal range ({min_dli} - {max_dli})"
    elif current_dli <= max_dli * 1.3:
        status = "excess"
        severity = "low"
        message = f"DLI is above optimal range ({current_dli} vs max {max_dli})"
    else:
        status = "severe_excess"
        severity = "moderate"
        message = f"DLI is significantly above optimal ({current_dli} vs max {max_dli})"

    # Calculate deficit/excess percentage
    if current_dli < min_dli:
        missing_percent = int(((min_dli - current_dli) / min_dli) * 100)
        excess_percent = 0
    elif current_dli > max_dli:
        missing_percent = 0
        excess_percent = int(((current_dli - max_dli) / max_dli) * 100)
    else:
        missing_percent = 0
        excess_percent = 0

    return {
        "status": status,
        "severity": severity,
        "message": message,
        "missing_percent": missing_percent,
        "excess_percent": excess_percent,
        "current_dli": round(current_dli, 2),
        "optimal_range": {"min": round(min_dli, 2), "max": round(max_dli, 2)}
    }


def analyze_dli_trend(daily_dlis: List[Tuple[datetime, float]], min_dli: float) -> Dict:
    """
    Analyze DLI trends over time

    Args:
        daily_dlis: List of (date, dli) tuples
        min_dli: Minimum optimal DLI

    Returns:
        Dictionary with trend analysis
    """
    if len(daily_dlis) < 2:
        return {
            "trend": "insufficient_data",
            "days_below_optimal": 0,
            "consecutive_deficit_days": 0
        }

    # Count days below optimal
    days_below = sum(1 for _, dli in daily_dlis if dli < min_dli)

    # Find longest consecutive deficit streak
    max_streak = 0
    current_streak = 0

    for _, dli in daily_dlis:
        if dli < min_dli:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0

    # Determine trend
    if len(daily_dlis) >= 3:
        recent_avg = sum(dli for _, dli in daily_dlis[-3:]) / 3
        earlier_avg = sum(dli for _, dli in daily_dlis[:3]) / 3

        if recent_avg > earlier_avg * 1.1:
            trend = "improving"
        elif recent_avg < earlier_avg * 0.9:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "stable"

    # Calculate average DLI
    avg_dli = sum(dli for _, dli in daily_dlis) / len(daily_dlis)

    return {
        "trend": trend,
        "days_analyzed": len(daily_dlis),
        "days_below_optimal": days_below,
        "consecutive_deficit_days": max_streak,
        "average_dli": round(avg_dli, 2),
        "deficit_percentage": int((days_below / len(daily_dlis)) * 100)
    }


def calculate_grow_light_needs(current_dli: float, target_dli: float,
                               hours_available: float = 12.0) -> Dict:
    """
    Calculate grow light requirements to reach target DLI

    Args:
        current_dli: Current DLI from natural light
        target_dli: Target DLI to achieve
        hours_available: Hours per day available for supplemental lighting

    Returns:
        Dictionary with grow light recommendations
    """
    if current_dli >= target_dli:
        return {
            "needs_supplement": False,
            "message": "Current DLI is sufficient, no supplemental lighting needed"
        }

    # Calculate DLI deficit
    deficit = target_dli - current_dli

    # Convert deficit to required light intensity
    # DLI (mol/m²/day) = intensity (μmol/m²/s) × hours × 3600 / 1,000,000
    # intensity = DLI × 1,000,000 / (hours × 3600)
    required_intensity = (deficit * 1_000_000) / (hours_available * 3600)

    # Typical grow light recommendations
    light_types = []

    if required_intensity < 50:
        light_types.append({
            "type": "Low-intensity LED strip",
            "specs": "~25-50 μmol/m²/s",
            "placement": "30-45cm from plant",
            "cost": "€15-30"
        })
    elif required_intensity < 150:
        light_types.append({
            "type": "Standard LED grow light",
            "specs": "~100-150 μmol/m²/s",
            "placement": "30-60cm from plant",
            "cost": "€40-80"
        })
    elif required_intensity < 300:
        light_types.append({
            "type": "High-output LED panel",
            "specs": "~200-300 μmol/m²/s",
            "placement": "45-75cm from plant",
            "cost": "€80-150"
        })
    else:
        light_types.append({
            "type": "Professional grow light system",
            "specs": f"~{int(required_intensity)} μmol/m²/s",
            "placement": "60-90cm from plant",
            "cost": "€150+"
        })

    # Calculate energy cost (rough estimate)
    # Typical LED efficiency: ~2.5 μmol/J
    watts_needed = required_intensity / 2.5
    daily_kwh = (watts_needed * hours_available) / 1000
    monthly_kwh = daily_kwh * 30

    # Average electricity cost: €0.30/kWh (Germany)
    monthly_cost = monthly_kwh * 0.30

    return {
        "needs_supplement": True,
        "deficit_dli": round(deficit, 2),
        "required_intensity": int(required_intensity),
        "recommended_hours": hours_available,
        "light_options": light_types,
        "energy_estimate": {
            "watts": int(watts_needed),
            "daily_kwh": round(daily_kwh, 2),
            "monthly_kwh": round(monthly_kwh, 1),
            "monthly_cost_eur": round(monthly_cost, 2)
        },
        "message": f"Add {int(required_intensity)} μmol/m²/s for {hours_available}h/day to reach target DLI"
    }


def predict_seasonal_dli(current_dli: float, current_month: int) -> Dict:
    """
    Predict DLI changes based on seasonal patterns

    Args:
        current_dli: Current DLI measurement
        current_month: Current month (1-12)

    Returns:
        Dictionary with seasonal predictions
    """
    # Seasonal multipliers for Central Europe (approximate)
    # These represent typical seasonal light availability
    seasonal_factors = {
        1: 0.3,   # January - very low
        2: 0.4,   # February - low
        3: 0.6,   # March - increasing
        4: 0.8,   # April - moderate
        5: 1.0,   # May - high
        6: 1.1,   # June - peak
        7: 1.1,   # July - peak
        8: 1.0,   # August - high
        9: 0.8,   # September - decreasing
        10: 0.6,  # October - moderate
        11: 0.4,  # November - low
        12: 0.3   # December - very low
    }

    current_factor = seasonal_factors[current_month]

    # Predict next 3 months
    predictions = []
    for i in range(1, 4):
        next_month = ((current_month + i - 1) % 12) + 1
        next_factor = seasonal_factors[next_month]

        # Estimate DLI based on seasonal factor
        predicted_dli = (current_dli / current_factor) * next_factor if current_factor > 0 else current_dli

        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        predictions.append({
            "month": month_names[next_month - 1],
            "predicted_dli": round(predicted_dli, 2),
            "change_percent": int(((predicted_dli - current_dli) / current_dli * 100)) if current_dli > 0 else 0
        })

    return {
        "current_season": get_season(current_month),
        "predictions": predictions,
        "recommendation": get_seasonal_recommendation(current_month)
    }


def get_season(month: int) -> str:
    """Get season name from month"""
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:
        return "autumn"


def get_seasonal_recommendation(month: int) -> str:
    """Get seasonal care recommendation"""
    season = get_season(month)

    recommendations = {
        "winter": "Consider supplemental lighting. Natural DLI is at its lowest. Most plants need grow lights.",
        "spring": "Natural light is increasing. Monitor if supplemental lighting can be reduced.",
        "summer": "Natural DLI is at peak. Ensure plants don't get too much direct sun. May need shade.",
        "autumn": "Natural light is decreasing. Start planning for supplemental lighting needs."
    }

    return recommendations[season]
