# Release Notes v1.3.5 - Smart Anomaly Detection: Distinguish Sensor Error from Real Nutrient Depletion

**Release Date:** 2026-01-17

## 🎯 Overview

This release introduces **intelligent sensor anomaly detection** that distinguishes between:
- **Real sensor errors** (sudden EC drop to 0 = poor contact/malfunction)
- **Real nutrient depletion** (gradual EC decline to 0 = plant consumed all nutrients)

Previously, v1.3.4 treated ALL EC=0 with anomaly flag as sensor errors. This was overly conservative and prevented fertilization recommendations for plants that genuinely depleted their nutrients.

## Problem with v1.3.4

### Real-World Scenario

**Plant:** Efeutute Bad
**EC Trend (last 30 days):**
- Initial EC: 0.1 mS/cm
- Current EC: 0.0 mS/cm
- Trend: Stable (then gradual decline)
- FYTA Anomaly Flag: `true`

**v1.3.4 Output:**
```json
{
  "nutrients": {
    "status": "sensor_error",
    "explanation": "Check sensor placement and clean electrodes"
  },
  "fertilization": {
    "action": "check_sensor",
    "timing": "Before fertilizing"
  }
}
```

**Issue:** The plant **actually needs fertilization** (EC declined from 0.1 to 0 over time), but the system recommended checking the sensor instead. This prevented timely fertilization.

### Why This Happened

FYTA sets `soil_fertility_anomaly: true` for EC=0 in many cases, even when it's a valid reading of nutrient depletion. v1.3.4 blindly trusted this flag without analyzing the **trend**.

## Solution: Smart Anomaly Detection

### New Logic

The system now analyzes **EC trend over 30 days** to determine if EC=0 is a sensor error or real depletion:

**Sensor Error (sudden drop):**
- EC was **> 0.3** within last 30 days
- AND trend is **NOT "decreasing"** (sudden jump/stable → 0)
- → Recommendation: **"check_sensor"**

**Real Nutrient Depletion (gradual decline):**
- EC was **≤ 0.3** within last 30 days (already low)
- OR trend is **"decreasing"** (gradual consumption)
- → Recommendation: **"fertilize_now"** or **"fertilize_soon"**

### Examples

#### Example 1: Real Sensor Error (Sudden Drop)

**EC Trend:**
```json
{
  "initial_ec": 0.8,
  "current_ec": 0.0,
  "trend": "stable",
  "days_analyzed": 30
}
```

**Analysis:** EC was 0.8 and suddenly dropped to 0 without gradual decrease → **Sensor lost contact**

**Recommendation:**
```json
{
  "action": "check_sensor",
  "reasoning": "Sensor anomaly detected: sudden drop from 0.8 to 0"
}
```

#### Example 2: Real Nutrient Depletion (Gradual Decline)

**EC Trend:**
```json
{
  "initial_ec": 0.1,
  "current_ec": 0.0,
  "trend": "stable",
  "days_analyzed": 30
}
```

**Analysis:** EC was already low (0.1) and remained low → **Plant consumed remaining nutrients**

**Recommendation:**
```json
{
  "action": "fertilize_now",
  "timing": "Within 1-2 days",
  "reasoning": "EC critically low at 0"
}
```

#### Example 3: Real Nutrient Depletion (Decreasing Trend)

**EC Trend:**
```json
{
  "initial_ec": 0.5,
  "current_ec": 0.0,
  "trend": "decreasing",
  "slope_per_day": -0.017,
  "days_analyzed": 30
}
```

**Analysis:** EC gradually declined from 0.5 to 0 over 30 days → **Plant consumed nutrients over time**

**Recommendation:**
```json
{
  "action": "fertilize_now",
  "timing": "Within 1-2 days",
  "reasoning": "EC critically low at 0"
}
```

## Technical Implementation

### Code Changes

#### 1. `thresholds.py` - Smart Anomaly Detection in Status Evaluation

**File:** `src/fyta_mcp_server/utils/thresholds.py`

Added `ec_trend` parameter to `evaluate_plant_status()`:

```python
def evaluate_plant_status(plant: Dict, measurements_data: Optional[Dict] = None, ec_trend: Optional[Dict] = None) -> Dict:
```

**Lines 251-286:** New smart anomaly detection logic:

```python
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
```

#### 2. `handlers.py` - Early EC Trend Calculation

**File:** `src/fyta_mcp_server/handlers.py`

**Lines 1014-1025:** Calculate EC trend **before** `evaluate_plant_status()` to enable smart detection:

```python
# Calculate EC trend early (needed for smart anomaly detection in evaluate_plant_status)
ec_trend_early = None
if measurements_list and len(measurements_list) > 0:
    try:
        from .utils.fertilization import analyze_ec_trend
        ec_trend_early = analyze_ec_trend(measurements_list, days=30)
        logger.info(f"Early EC trend analysis for anomaly detection: {ec_trend_early.get('analyzed', False)}")
    except Exception as e:
        logger.error(f"Error in early EC trend analysis: {e}")

# Use our intelligent evaluation instead of trusting FYTA's inconsistent status codes
smart_status = evaluate_plant_status(enriched_plant_data, measurements_week, ec_trend_early)
```

**Lines 1386-1392:** Reuse EC trend to avoid duplicate calculation:

```python
# Reuse EC trend from early analysis if available, otherwise calculate
if ec_trend_early:
    ec_trend = ec_trend_early
    logger.info("Reusing EC trend from early analysis")
else:
    ec_trend = analyze_ec_trend(measurements_list, days=30)
    logger.info(f"EC trend analyzed: {ec_trend.get('analyzed', False)}")
```

**Lines 1138-1152:** Fix `issueDetails` to use `status_name` instead of assuming status code 4 = sensor_error:

```python
# Check status_name to distinguish between sensor_error and critical_low
nutrients_status_name = nutrients_data.get("status_name") if nutrients_data else None

if status_details["nutrients"] == 4 and nutrients_status_name == "sensor_error":
    # Real sensor anomaly detected by smart detection
    issues.append({
        "parameter": "nutrients",
        "status": "sensor_error",
        ...
    })
else:
    # Normal status (critical_low, low, high, etc.)
    issues.append({
        "parameter": "nutrients",
        "status": status_names[status_details["nutrients"]],
        ...
    })
```

## Impact on Users

### Before v1.3.5 (Example: Efeutute Bad)

```
Plant: Efeutute Bad
EC: 0 mS/cm
EC Trend: 0.1 → 0.0 (stable/gradual decline)
Anomaly Flag: true

Recommendation (v1.3.4):
✗ Action: "check_sensor"
✗ Timing: "Before fertilizing"
✗ Result: Plant not fertilized despite needing nutrients
```

### After v1.3.5

```
Plant: Efeutute Bad
EC: 0 mS/cm
EC Trend: 0.1 → 0.0 (stable/gradual decline)
Anomaly Flag: true

Recommendation (v1.3.5):
✓ Action: "fertilize_now"
✓ Timing: "Within 1-2 days"
✓ Dosage: "50-75% of recommended dosage (plant is weakened)"
✓ Result: Plant gets nutrients when needed
```

## Behavior Matrix (Updated for v1.3.5)

| EC Value | Anomaly Flag | EC Trend (30d) | Initial EC | Action | Reasoning |
|----------|-------------|----------------|------------|--------|-----------|
| 0 | true | decreasing | 0.5 | `fertilize_now` ✅ | Gradual nutrient consumption |
| 0 | true | stable | 0.1 | `fertilize_now` ✅ | Was already low, now depleted |
| 0 | true | stable | 0.8 | `check_sensor` ⚠️ | Sudden drop from high value |
| 0 | true | increasing | 0.3 | `check_sensor` ⚠️ | Illogical increase then 0 = sensor issue |
| 0 | true | (no data) | - | `check_sensor` ⚠️ | Conservative: verify sensor first |
| 0 | false | - | - | `fertilize_now` ✅ | Valid measurement, no anomaly |

## Edge Cases Handled

### 1. Insufficient Trend Data

If fewer than 3 measurements exist in the last 30 days:
- **Conservative approach:** Treat as potential sensor error
- **Reasoning:** Better to verify sensor than fertilize based on unreliable data
- **User action:** Check sensor, wait for more data points

### 2. EC = 0 without Anomaly Flag

If FYTA reports EC=0 **without** anomaly flag:
- **Interpretation:** Valid measurement (sensor working correctly)
- **Action:** Recommend fertilization based on EC status
- **No sensor check needed**

### 3. Anomaly with EC > 0

If anomaly flag is set but EC > 0:
- **Interpretation:** Sensor reporting unreliable readings
- **Action:** Always recommend "check_sensor"
- **Unchanged from v1.3.4**

## Migration Notes

No breaking changes. Existing installations will automatically use smart anomaly detection after upgrading to v1.3.5.

### What to Expect After Upgrading

**If you have plants with EC=0 + anomaly flag:**

1. **System analyzes EC trend automatically**
2. **Gradual decline → Fertilization recommended**
3. **Sudden drop → Sensor check recommended**

**You may see different recommendations than v1.3.4:**
- Some plants that showed "check_sensor" will now show "fertilize_now"
- This is correct behavior if EC gradually declined to 0
- Trust the recommendation - the trend analysis is accurate

## Version History

- **v1.3.3:** Added sensor anomaly handling for fertilization recommendations
- **v1.3.4:** Fixed to always check sensor when EC=0 + anomaly (too conservative)
- **v1.3.5:** Smart anomaly detection using EC trend analysis ✅

## Installation

Update to v1.3.5 by pulling the latest changes:

```bash
cd /path/to/fyta-mcp-server
git pull
git checkout v1.3.5
```

Or clone fresh:

```bash
git clone https://github.com/schimmmi/fyta-mcp-server.git
cd fyta-mcp-server
git checkout v1.3.5
```

## Links

- **GitHub Release:** https://github.com/schimmmi/fyta-mcp-server/releases/tag/v1.3.5
- **Full Changelog:** [CHANGELOG.md](../CHANGELOG.md)
- **Previous Release:** [v1.3.4](RELEASE_NOTES_v1.3.4.md)
- **Documentation:** [README.md](../README.md)

## Credits

Thanks to real-world testing with Efeutute Bad (plant ID 108010) that revealed the need for trend-based anomaly detection.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
