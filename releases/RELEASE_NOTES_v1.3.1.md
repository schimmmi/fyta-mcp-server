# Release Notes v1.3.1 - Updated Salinity Thresholds & EC=0 Handling

**Release Date:** 2026-01-14

## 🌱 Overview

This release updates the optimal salinity (EC) thresholds to better align with actual plant nutrient requirements and fixes the handling of EC=0 measurements.

## Changes

### Updated Salinity Thresholds

**Previous values:** 0.3-1.2 mS/cm
**New values:** 0.2-1.0 mS/cm

The optimal range for electrical conductivity (EC/salinity) has been adjusted based on real-world plant requirements:
- **Winter:** Lower end of range (0.2 mS/cm) - plants need fewer nutrients during dormancy
- **Summer:** Higher end of range (1.0 mS/cm) - plants need more nutrients during active growth

This affects:
- Default fallback thresholds when FYTA provides min=max=0 for winter
- Summer threshold fallbacks
- Overall nutrient status evaluation

### Fixed EC=0 Anomaly Handling

**Problem:** The previous version treated EC=0 as "normal" during winter dormancy, assuming plants don't need nutrients.

**Reality:** EC=0 means **no nutrients present in soil** - this is always a "low" status requiring fertilization, regardless of season.

**Changes:**
- EC=0 is now correctly evaluated as "low" status (nutrients needed)
- Simplified anomaly detection logic:
  - **EC=0 + anomaly flag** → Sensor might have poor soil contact, but EC=0 still indicates no nutrients (treated as "low")
  - **EC≠0 + anomaly flag** → Real sensor malfunction (treated as "sensor_error")
- Removed incorrect assumption that EC=0 is "normal" in winter
- Documentation updated to clarify EC=0 handling

## Technical Details

### Code Changes

**File:** `src/fyta_mcp_server/utils/thresholds.py`

Lines 233-241: Updated default thresholds
```python
# OLD
min_good = t.get("salinity_min_good", 0.4)
max_good = t.get("salinity_max_good", 1.2)
# ...
min_good = 0.3
max_good = 1.2

# NEW
min_good = t.get("salinity_min_good", 0.2)
max_good = t.get("salinity_max_good", 1.0)
# ...
min_good = 0.2
max_good = 1.0
```

Lines 251-261: Simplified anomaly detection
```python
# OLD: Complex logic checking for winter thresholds
if nutrients_anomaly:
    winter_thresholds = thresholds.get("salinity_min_good", 0) == 0 and thresholds.get("salinity_max_good", 0) == 0
    is_winter_ec_zero = nutrients == 0 and winter_thresholds
    if is_winter_ec_zero:
        logger.info(f"Nutrients EC=0 with winter thresholds for plant {plant.get('id')} - ignoring anomaly flag (no nutrients needed)")
    else:
        status_code = 4
        status_name = "sensor_error"

# NEW: Simple logic
if nutrients_anomaly and nutrients != 0:
    logger.warning(f"Nutrients sensor anomaly detected for plant {plant.get('id')}: value={nutrients}, treating as unreliable")
    status_code = 4
    status_name = "sensor_error"
elif nutrients == 0:
    logger.info(f"Nutrients EC=0 for plant {plant.get('id')} - no nutrients present (fertilization needed)")
```

**File:** `README.md`

Lines 432-444: Updated documentation sections
- Changed "Winter Salinity Bug" to "Salinity Thresholds"
- Changed "EC=0 Anomaly Detection" to "EC=0 Handling"
- Clarified that EC=0 means nutrient deficiency

## Impact on Users

### Before This Release

```
Plant: Efeutute Wohnzimmer
EC: 0 mS/cm
Status: ✅ Normal (winter dormancy, no nutrients needed)
Anomaly: Ignored
```

### After This Release

```
Plant: Efeutute Wohnzimmer
EC: 0 mS/cm
Status: 🔴 Low (no nutrients present - fertilization needed)
Anomaly: Sensor might have poor contact, but EC=0 is valid measurement
```

## Example Scenarios

### Scenario 1: EC=0 with Anomaly Flag
```json
{
  "salinity": 0,
  "soil_fertility_anomaly": true
}
```

**Result:** Status = "low" (nutrients needed)
**Reason:** EC=0 is a valid measurement indicating no nutrients, even if sensor contact might be poor

### Scenario 2: EC=0.5 with Anomaly Flag
```json
{
  "salinity": 0.5,
  "soil_fertility_anomaly": true
}
```

**Result:** Status = "sensor_error" (unreliable)
**Reason:** Non-zero EC with anomaly flag indicates real sensor malfunction

### Scenario 3: EC=0 without Anomaly Flag
```json
{
  "salinity": 0,
  "soil_fertility_anomaly": false
}
```

**Result:** Status = "low" (nutrients needed)
**Reason:** EC=0 means no nutrients, sensor is working correctly

## Migration Notes

No breaking changes. The server will automatically use the new thresholds.

### If you see different diagnoses after upgrading:

**Plants showing "low" nutrients that previously showed "normal":**
- This is correct! EC=0 means no nutrients present
- Consider fertilizing your plants
- Check sensor placement if anomaly flag is set

**Fertilization recommendations appearing where they didn't before:**
- This is expected and correct behavior
- EC=0 always requires fertilization, regardless of season

## Installation

Update to v1.3.1:

```bash
pip install --upgrade fyta-mcp-server
```

Or with uv:
```bash
uv pip install --upgrade fyta-mcp-server
```

## Links

- **GitHub Release:** https://github.com/schimmmi/fyta-mcp-server/releases/tag/v1.3.1
- **Full Changelog:** [CHANGELOG.md](../CHANGELOG.md)
- **Documentation:** [README.md](../README.md)

## Credits

Thanks to user feedback for identifying the correct optimal salinity ranges and clarifying that EC=0 indicates nutrient deficiency.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
