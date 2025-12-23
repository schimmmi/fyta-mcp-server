"""
Statistical analysis utilities
"""
import math


def calculate_statistics(values: list[float]) -> dict:
    """
    Calculate comprehensive statistics for a data series

    Args:
        values: List of numeric values

    Returns:
        Dictionary with statistical measures
    """
    if not values:
        return {
            "count": 0,
            "mean": None,
            "median": None,
            "std_dev": None,
            "min": None,
            "max": None,
            "range": None,
            "percentiles": {}
        }

    n = len(values)
    sorted_values = sorted(values)

    # Mean
    mean = sum(values) / n

    # Median
    if n % 2 == 0:
        median = (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
    else:
        median = sorted_values[n//2]

    # Standard deviation
    variance = sum((x - mean) ** 2 for x in values) / n
    std_dev = math.sqrt(variance)

    # Min/Max
    min_val = min(values)
    max_val = max(values)

    # Percentiles
    def percentile(data, p):
        """Calculate percentile"""
        k = (len(data) - 1) * p
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return data[int(k)]
        d0 = data[int(f)] * (c - k)
        d1 = data[int(c)] * (k - f)
        return d0 + d1

    percentiles = {
        "p10": round(percentile(sorted_values, 0.10), 2),
        "p25": round(percentile(sorted_values, 0.25), 2),
        "p50": round(median, 2),
        "p75": round(percentile(sorted_values, 0.75), 2),
        "p90": round(percentile(sorted_values, 0.90), 2)
    }

    # Coefficient of variation (relative std dev)
    cv = (std_dev / mean * 100) if mean != 0 else 0

    return {
        "count": n,
        "mean": round(mean, 2),
        "median": round(median, 2),
        "std_dev": round(std_dev, 2),
        "min": round(min_val, 2),
        "max": round(max_val, 2),
        "range": round(max_val - min_val, 2),
        "percentiles": percentiles,
        "coefficient_of_variation": round(cv, 2)
    }


def detect_anomalies(values: list[float], threshold_sigma: float = 2.0) -> dict:
    """
    Detect anomalies using statistical methods (Z-score)

    Args:
        values: List of numeric values
        threshold_sigma: Number of standard deviations for anomaly threshold

    Returns:
        Dictionary with anomaly information
    """
    if len(values) < 3:
        return {
            "has_anomalies": False,
            "anomaly_count": 0,
            "anomaly_indices": [],
            "method": "insufficient_data"
        }

    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    std_dev = math.sqrt(variance)

    if std_dev == 0:
        return {
            "has_anomalies": False,
            "anomaly_count": 0,
            "anomaly_indices": [],
            "method": "no_variation"
        }

    # Calculate Z-scores
    anomalies = []
    for i, value in enumerate(values):
        z_score = abs((value - mean) / std_dev)
        if z_score > threshold_sigma:
            anomalies.append({
                "index": i,
                "value": round(value, 2),
                "z_score": round(z_score, 2),
                "deviation_percent": round((value - mean) / mean * 100, 2)
            })

    return {
        "has_anomalies": len(anomalies) > 0,
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
        "method": "z_score",
        "threshold_sigma": threshold_sigma
    }


def calculate_correlation(x_values: list[float], y_values: list[float]) -> float:
    """
    Calculate Pearson correlation coefficient between two variables

    Args:
        x_values: First variable values
        y_values: Second variable values

    Returns:
        Correlation coefficient (-1 to 1)
    """
    if len(x_values) != len(y_values) or len(x_values) < 2:
        return 0.0

    n = len(x_values)
    mean_x = sum(x_values) / n
    mean_y = sum(y_values) / n

    numerator = sum((x_values[i] - mean_x) * (y_values[i] - mean_y) for i in range(n))
    denominator_x = math.sqrt(sum((x - mean_x) ** 2 for x in x_values))
    denominator_y = math.sqrt(sum((y - mean_y) ** 2 for y in y_values))

    if denominator_x == 0 or denominator_y == 0:
        return 0.0

    return numerator / (denominator_x * denominator_y)


def analyze_stability(values: list[float]) -> dict:
    """
    Analyze the stability/variability of a time series

    Args:
        values: List of numeric values

    Returns:
        Dictionary with stability metrics
    """
    if len(values) < 2:
        return {
            "stability": "unknown",
            "variability": "unknown"
        }

    stats = calculate_statistics(values)
    cv = stats["coefficient_of_variation"]

    # Classify based on coefficient of variation
    if cv < 5:
        stability = "very_stable"
        variability = "low"
    elif cv < 10:
        stability = "stable"
        variability = "low"
    elif cv < 20:
        stability = "moderate"
        variability = "medium"
    elif cv < 30:
        stability = "variable"
        variability = "high"
    else:
        stability = "highly_variable"
        variability = "very_high"

    return {
        "stability": stability,
        "variability": variability,
        "coefficient_of_variation": cv,
        "interpretation": f"The metric shows {variability} variability (CV={cv}%)"
    }
