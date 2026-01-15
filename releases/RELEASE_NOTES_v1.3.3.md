# Release Notes v1.3.3 - Sensor Anomaly Handling in Fertilization

**Release Date:** 2026-01-15

## ⚠️ Overview

This release adds proper handling of FYTA's `soil_fertility_anomaly` flag in fertilization recommendations. When a sensor anomaly is detected, the server now recommends checking/repositioning the sensor instead of blindly recommending fertilization based on potentially unreliable data.

## Fixed

### Sensor Anomaly Handling in Fertilization

**Problem:** Fertilization recommendations ignored the `soil_fertility_anomaly` flag from FYTA's API. Even when FYTA flagged a sensor as having issues (poor soil contact, malfunction), the server would still recommend "fertilize now" based on the unreliable EC reading.

**Example:**
```
Plant: Efeutute Wohnzimmer
EC: 0 mS/cm
soil_fertility_anomaly: true
→ Recommendation: "fertilize_now" ❌
```

**Root Cause:** The `get_fertilization_recommendation()` function didn't receive the anomaly flag and couldn't account for unreliable sensor data.

**Fix:**
- Added `sensor_anomaly` parameter to `get_fertilization_recommendation()`
- When `sensor_anomaly=true` AND `EC≠0`: Return `action: "check_sensor"` instead of fertilization advice
- Provide clear warnings not to fertilize based on unreliable data
- EC=0 still triggers fertilization (EC=0 is a valid measurement = no nutrients present)

## Impact on Users

### Before This Release

```
Plant: Efeutute Wohnzimmer
EC: 0 mS/cm
Anomaly: true
→ Action: "fertilize_now"
→ Timing: "Within 1-2 days"
→ Reasoning: "EC critically low at 0"
```

**Problem:** Fertilizing based on potentially faulty sensor reading could harm plant.

### After This Release

```
Plant: Efeutute Wohnzimmer
EC: 0 mS/cm
Anomaly: true
→ Action: "check_sensor"
→ Timing: "Before fertilizing"
→ Reasoning:
  - FYTA reports sensor anomaly - reading may be unreliable
  - Check sensor placement and soil contact
  - Clean sensor electrodes if needed
  - Wait for stable readings before fertilizing
→ Warnings:
  - ⚠️ Do not fertilize based on unreliable sensor data!
  - Reposition sensor for better soil contact
  - Monitor readings for 24-48 hours
```

## Technical Details

### Code Changes

**File:** `src/fyta_mcp_server/utils/fertilization.py`

Lines 253-300: Added sensor anomaly handling
```python
def get_fertilization_recommendation(
    current_ec: float,
    ec_trend: Optional[Dict] = None,
    substrate_type: Optional[str] = None,
    last_fertilized: Optional[str] = None,
    care_history: Optional[List[Dict]] = None,
    sensor_anomaly: bool = False  # NEW PARAMETER
) -> Dict:
    """Generate comprehensive fertilization recommendation."""

    # Check for sensor anomaly first
    if sensor_anomaly and current_ec != 0:
        return {
            "current_status": {
                "status": "sensor_error",
                "severity": "critical",
                "description": f"EC sensor reports anomaly at {current_ec}",
                "emoji": "⚠️",
                "action_needed": "check_sensor",
                "explanation": "Sensor may have poor soil contact or malfunction..."
            },
            "action": "check_sensor",
            "timing": "Before fertilizing",
            "dosage": None,
            "reasoning": [...],
            "warnings": [...]
        }
```

**File:** `src/fyta_mcp_server/handlers.py`

Lines 1376-1397: Pass anomaly flag to recommendation
```python
# Get sensor anomaly flag from latest measurement
latest = get_latest_measurement(measurements_list)
sensor_anomaly = latest.get("soil_fertility_anomaly", False) if latest else False

# Generate recommendation
fert_recommendation = get_fertilization_recommendation(
    current_ec=current_ec,
    ec_trend=ec_trend,
    substrate_type=substrate_type,
    last_fertilized=last_fertilized,
    care_history=care_history,
    sensor_anomaly=sensor_anomaly  # PASS FLAG
)
```

## Behavior Matrix

| EC Value | Anomaly Flag | Action | Reasoning |
|----------|-------------|--------|-----------|
| 0 | true | `fertilize_now` | EC=0 is valid: no nutrients present |
| 0 | false | `fertilize_now` | EC=0 is valid: no nutrients present |
| 0.1 | true | `check_sensor` | Unreliable reading, verify sensor first |
| 0.1 | false | `fertilize_now` | Valid low reading, fertilization needed |
| 0.5 | true | `check_sensor` | Unreliable reading, verify sensor first |
| 0.5 | false | `maintain` | Valid optimal reading (winter range) |

**Key Point:** EC=0 with anomaly flag still triggers fertilization because EC=0 is a valid measurement indicating no nutrients, regardless of sensor health.

## Migration Notes

No breaking changes. The server will automatically use the anomaly flag when available.

### If you see different recommendations after upgrading:

**"check_sensor" action appearing where "fertilize_now" was shown:**
- This is correct! The sensor has issues and readings may be unreliable
- Follow the recommendations:
  1. Check sensor placement in soil
  2. Ensure good soil contact
  3. Clean sensor electrodes if dirty
  4. Wait 24-48 hours for stable readings
  5. Then reassess fertilization needs

**EC=0 still shows "fertilize_now" despite anomaly flag:**
- This is correct! EC=0 means no nutrients, which is a valid measurement
- The anomaly flag might indicate poor sensor contact, but EC=0 still means the plant needs fertilization

## Example Diagnostic Output

### With Sensor Anomaly (EC≠0)

```json
{
  "fertilization": {
    "recommendation": {
      "action": "check_sensor",
      "timing": "Before fertilizing",
      "dosage": null,
      "current_status": {
        "status": "sensor_error",
        "severity": "critical",
        "emoji": "⚠️",
        "description": "EC sensor reports anomaly at 0.0"
      },
      "reasoning": [
        "FYTA reports sensor anomaly - reading may be unreliable",
        "Check sensor placement and soil contact",
        "Clean sensor electrodes if needed",
        "Wait for stable readings before fertilizing"
      ],
      "warnings": [
        "⚠️ Do not fertilize based on unreliable sensor data!",
        "Reposition sensor for better soil contact",
        "Monitor readings for 24-48 hours"
      ]
    }
  }
}
```

### Without Sensor Anomaly (Normal Operation)

```json
{
  "fertilization": {
    "recommendation": {
      "action": "fertilize_now",
      "timing": "Within 1-2 days",
      "dosage": "50-75% of recommended dosage (plant is weakened)",
      "current_status": {
        "status": "critical_low",
        "severity": "critical",
        "emoji": "🔴",
        "description": "EC 0.1 is critically low"
      },
      "reasoning": [
        "EC critically low at 0.1"
      ]
    }
  }
}
```

## Installation

Update to v1.3.3 by cloning/pulling the repository:

```bash
cd /path/to/fyta-mcp-server
git pull
git checkout v1.3.3
```

Or clone fresh:

```bash
git clone https://github.com/schimmmi/fyta-mcp-server.git
cd fyta-mcp-server
git checkout v1.3.3
```

## Links

- **GitHub Release:** https://github.com/schimmmi/fyta-mcp-server/releases/tag/v1.3.3
- **Full Changelog:** [CHANGELOG.md](../CHANGELOG.md)
- **Previous Release:** [v1.3.2](RELEASE_NOTES_v1.3.2.md)
- **Documentation:** [README.md](../README.md)

## Credits

Thanks to user feedback for identifying that sensor anomalies were not being properly handled in fertilization recommendations.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
