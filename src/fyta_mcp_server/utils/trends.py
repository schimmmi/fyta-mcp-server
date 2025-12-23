"""
Trend analysis and prediction utilities
"""


def calculate_trend(data_points: list[tuple[float, float]]) -> dict:
    """
    Calculate trend statistics from time-series data

    Args:
        data_points: List of (timestamp, value) tuples

    Returns:
        Dictionary with trend analysis including slope, direction, forecast
    """
    if not data_points or len(data_points) < 2:
        return {
            "direction": "stable",
            "slope": 0.0,
            "confidence": 0.0,
            "forecast_hours": None,
            "data_points": 0
        }

    # Sort by timestamp
    data_points = sorted(data_points, key=lambda x: x[0])

    # Calculate linear regression (simple slope calculation)
    n = len(data_points)
    sum_x = sum(x for x, _ in data_points)
    sum_y = sum(y for _, y in data_points)
    sum_xy = sum(x * y for x, y in data_points)
    sum_x2 = sum(x * x for x, _ in data_points)

    # Slope calculation: m = (n*Σxy - Σx*Σy) / (n*Σx² - (Σx)²)
    denominator = n * sum_x2 - sum_x * sum_x
    if denominator == 0:
        slope = 0.0
    else:
        slope = (n * sum_xy - sum_x * sum_y) / denominator

    # Calculate R² for confidence
    mean_y = sum_y / n
    ss_tot = sum((y - mean_y) ** 2 for _, y in data_points)

    # Predicted values
    intercept = (sum_y - slope * sum_x) / n
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in data_points)

    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    # Determine direction
    # Normalize slope by time range to get per-hour change
    time_range = data_points[-1][0] - data_points[0][0]
    if time_range == 0:
        direction = "stable"
        slope_per_hour = 0.0
    else:
        slope_per_hour = slope / time_range

        # Threshold for "stable" - less than 0.5% change per hour
        recent_value = data_points[-1][1]
        if abs(slope_per_hour) < abs(recent_value * 0.005):
            direction = "stable"
        elif slope_per_hour > 0:
            direction = "increasing"
        else:
            direction = "decreasing"

    return {
        "direction": direction,
        "slope": round(slope_per_hour, 4),
        "slope_percent_per_hour": round((slope_per_hour / (recent_value if recent_value != 0 else 1)) * 100, 2),
        "confidence": round(r_squared, 2),
        "data_points": n,
        "first_value": round(data_points[0][1], 2),
        "last_value": round(data_points[-1][1], 2),
        "change": round(data_points[-1][1] - data_points[0][1], 2),
        "change_percent": round(((data_points[-1][1] - data_points[0][1]) / data_points[0][1] * 100) if data_points[0][1] != 0 else 0, 2)
    }


def predict_critical_time(trend_data: dict, current_value: float, critical_threshold: float) -> dict:
    """
    Predict when a metric will reach a critical threshold based on trend

    Args:
        trend_data: Trend analysis from calculate_trend()
        current_value: Current sensor value
        critical_threshold: Threshold value that indicates critical state

    Returns:
        Prediction with hours until critical and urgency level
    """
    if trend_data["direction"] == "stable" or trend_data["slope"] == 0:
        return {
            "will_reach_critical": False,
            "hours_until_critical": None,
            "urgency": "none",
            "message": "Trend is stable, no immediate action needed"
        }

    slope_per_hour = trend_data["slope"]

    # Check if we're moving towards critical threshold
    moving_towards_critical = (
        (slope_per_hour < 0 and current_value > critical_threshold and critical_threshold < current_value) or
        (slope_per_hour > 0 and current_value < critical_threshold and critical_threshold > current_value)
    )

    # For moisture, critical is typically low (threshold lower than current)
    # For temperature, critical could be high (threshold higher than current)
    diff = critical_threshold - current_value

    # Calculate hours until critical
    if slope_per_hour != 0:
        hours_until = diff / slope_per_hour
    else:
        hours_until = None

    if hours_until and hours_until > 0 and moving_towards_critical:
        if hours_until < 6:
            urgency = "immediate"
            message = f"Critical threshold will be reached in ~{int(hours_until)} hours. Immediate action required!"
        elif hours_until < 12:
            urgency = "high"
            message = f"Critical threshold expected in ~{int(hours_until)} hours. Action needed soon."
        elif hours_until < 24:
            urgency = "medium"
            message = f"Critical threshold expected in ~{int(hours_until)} hours. Plan intervention."
        elif hours_until < 48:
            urgency = "low"
            message = f"Critical threshold expected in ~{int(hours_until/24):.1f} days. Monitor closely."
        else:
            urgency = "none"
            message = f"Critical threshold not expected soon (~{int(hours_until/24)} days)."

        return {
            "will_reach_critical": True,
            "hours_until_critical": round(hours_until, 1),
            "urgency": urgency,
            "message": message
        }
    else:
        return {
            "will_reach_critical": False,
            "hours_until_critical": None,
            "urgency": "none",
            "message": "Not moving towards critical threshold" if not moving_towards_critical else "Stable or improving"
        }
