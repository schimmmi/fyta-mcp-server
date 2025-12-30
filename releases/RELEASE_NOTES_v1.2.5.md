# Release v1.2.5 - Critical Bug Fixes for Measurement Accuracy

🐛 This release fixes critical bugs that caused `diagnose_plant` and other tools to show **outdated measurement values**.

## 🔴 Critical Bug Fixes

### 1. Incorrect Measurement Values (MAJOR BUG)

**The Problem:**
The FYTA API returns measurements in **arbitrary order**, not chronologically sorted! Our code blindly used `measurements_list[-1]`, which often returned **old data** instead of the latest measurement.

**Real-World Impact:**
```python
# What users saw (WRONG):
temperature: 19°C
moisture: 34%
health: "critical" ❌

# Actual current values:
temperature: 28°C
moisture: 67%
health: "good" ✅
```

**The Fix:**
- Added `get_latest_measurement()` helper that **sorts by timestamp**
- Now correctly identifies the newest measurement
- Applied across all 6 locations that extract latest values

**Affected Tools:**
- `diagnose_plant` ← Most visible impact
- `get_plants_needing_attention`
- `get_plant_events`
- Watering analysis
- Fertilization analysis
- All trend predictions

---

### 2. Stale Values from Plant Object

**The Problem:**
The Plant object from FYTA's `/plants` endpoint contains measurement fields (temperature, moisture, etc.) but these values are **stale/unreliable**. We were copying these into our enriched data.

**The Fix:**
- Create **clean** `enriched_plant_data` dict without copying measurement values
- Only add measurement values from the `/measurements` endpoint
- Plant object now only used for metadata and status codes

---

### 3. Overly Dramatic Severity Levels

**The Problem:**
Temperature 1°C above threshold → "critical" severity ❌

**Example:**
- Plant at 26°C, threshold is 25°C
- Old: **"critical"** (causes "health: critical")
- New: **"low"** (minor issue, plant is fine)

**The Fix:**
Dynamic severity calculation based on **actual deviation percentage**:

| Temperature | Threshold | Deviation | Old Severity | **New Severity** |
|-------------|-----------|-----------|--------------|------------------|
| 26°C | 25°C | +4% | critical | **low** ✅ |
| 28°C | 25°C | +12% | critical | **moderate** ✅ |
| 30°C | 25°C | +20% | critical | **high** |
| 35°C | 25°C | +40% | critical | **critical** |

**Metric-Specific Rules:**
- **Moisture low**: Most critical (dehydration risk)
  - <15% absolute = critical
  - >30% below threshold = high
- **Temperature**: Gradual severity
  - <10% deviation = low
  - 10-20% deviation = moderate
  - >20% deviation = high
- **Nutrients**: More tolerance for variation

---

## 🎯 Real-World Examples

### Before v1.2.5 (WRONG DATA):
```json
{
  "plantId": 108010,
  "health": "critical",
  "issueDetails": [
    {
      "parameter": "temperature",
      "status": "high",
      "severity": "critical",
      "value": 19
    },
    {
      "parameter": "moisture",
      "status": "low",
      "severity": "high",
      "value": 34
    }
  ]
}
```

### After v1.2.5 (CORRECT DATA):
```json
{
  "plantId": 108010,
  "health": "good",
  "issueDetails": [
    {
      "parameter": "temperature",
      "status": "high",
      "severity": "moderate",
      "value": 28
    },
    {
      "parameter": "moisture",
      "status": "optimal",
      "severity": "info",
      "value": 67
    }
  ]
}
```

---

## 🔧 Technical Changes

### New Helper Functions

**`get_latest_measurement(measurements_list)`** (`handlers.py:446-468`)
```python
def get_latest_measurement(measurements_list: list) -> Optional[dict]:
    """
    Get the most recent measurement by sorting by timestamp.

    CRITICAL: The FYTA API does NOT return measurements in chronological order!
    """
    if not measurements_list:
        return None

    # Sort by timestamp (newest last)
    sorted_measurements = sorted(
        measurements_list,
        key=lambda m: m.get("date_utc", "") or m.get("timestamp", "") or m.get("measured_at", "")
    )

    return sorted_measurements[-1]
```

**`calculate_severity(value, status_code, thresholds, metric_name)`** (`handlers.py:483-559`)
- Calculates deviation percentage from optimal range
- Returns appropriate severity level: "info", "low", "moderate", "high", "critical"
- Metric-specific rules for moisture, temperature, nutrients, light

### Enhanced Logging

Added debug logging to diagnose_plant:
```
Plant 108010 - Got 721 measurements
Plant 108010 - Latest measurement timestamp: 2025-12-30T13:31:40
Plant 108010 - Latest measurement keys: ['light', 'temperature', 'soil_moisture', ...]
Plant 108010 - Latest measurement values: temp=28, moisture=67, ...
Plant 108010 - Enriched data after extraction: temp=28, moisture=67, nutrients=0.5
```

### Code Locations Changed

**handlers.py:**
- Line 446-468: New `get_latest_measurement()` function
- Line 483-559: New `calculate_severity()` function
- Line 826-871: Clean enriched_plant_data creation (diagnose_plant)
- Line 1014-1034: Dynamic severity for temperature
- Line 1036-1056: Dynamic severity for light
- Line 1068-1087: Dynamic severity for moisture
- Line 1089-1108: Dynamic severity for nutrients
- 6 locations: Replaced `measurements_list[-1]` with `get_latest_measurement()`

---

## 📊 Impact Summary

| Issue | Before | After |
|-------|--------|-------|
| **Measurement Accuracy** | Used outdated values (could be hours/days old) | Always uses newest timestamp ✅ |
| **Plant Object Values** | Copied stale values from plant object | Only uses measurements endpoint ✅ |
| **Severity Levels** | 26°C = "critical" | 26°C = "low" (realistic) ✅ |
| **Health Assessment** | Often "critical" for healthy plants | Accurate assessment ✅ |
| **False Alarms** | Many | Minimal ✅ |

---

## 🚨 Who Should Upgrade?

**EVERYONE using `diagnose_plant` should upgrade immediately!**

The bug caused incorrect measurements to be displayed, which could lead to:
- ❌ Unnecessary watering (thought soil was dry when it wasn't)
- ❌ Panic over false "critical" health status
- ❌ Incorrect fertilization decisions
- ❌ Misunderstanding of plant conditions

---

## 🧪 Testing

Tested with real FYTA plants:
- Epipremnum pinnatum (Bad): 28°C/67% moisture
- Epipremnum aureum (Wohnzimmer): 26°C/67% moisture

**Before:** Both showed 19°C/34% moisture, rated "critical"
**After:** Correct values, rated "good"/"fair" ✅

---

## 🙏 Notes

Special thanks to the detailed debugging that uncovered this issue! The moisture_trend analysis was working correctly (showing 67%) while diagnose_plant showed 34% - that discrepancy led us to discover the unsorted measurements bug.

---

**Full Changelog**: https://github.com/schimmmi/fyta-mcp-server/compare/v1.2.4...v1.2.5
