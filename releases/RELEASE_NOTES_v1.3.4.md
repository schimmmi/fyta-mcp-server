# Release Notes v1.3.4 - Fix Sensor Anomaly Handling for EC=0

**Release Date:** 2026-01-15

## 🐛 Overview

This release fixes a critical bug in v1.3.3 where EC=0 with sensor anomaly flag still recommended "fertilize_now" instead of "check_sensor". The issue was caused by an overly restrictive condition that excluded EC=0 from anomaly handling.

## Fixed

### Sensor Anomaly with EC=0

**Problem:** In v1.3.3, the sensor anomaly check had this condition:
```python
if sensor_anomaly and current_ec != 0:
    return check_sensor_recommendation
```

This meant that when EC=0 with `soil_fertility_anomaly: true`, the anomaly was ignored and the system recommended "fertilize_now".

**Example from Real Data:**
```json
{
  "plantName": "Efeutute Wohnzimmer",
  "nutrients": {
    "value": 0,
    "anomaly": true
  }
}
```

**v1.3.3 Output (Bug):**
```json
{
  "fertilization": {
    "recommendation": {
      "action": "fertilize_now",
      "timing": "Within 1-2 days",
      "reasoning": ["EC critically low at 0"]
    }
  }
}
```

**Root Cause:** The `current_ec != 0` condition was based on the assumption that "EC=0 is always a valid measurement (no nutrients)". However, this ignored the fact that **EC=0 with anomaly flag likely means poor sensor contact** (no contact = EC reads as 0), not actual nutrient deficiency.

**Fix:** Removed the `current_ec != 0` condition. Now **ALL sensor anomalies** trigger "check_sensor", including EC=0.

```python
# OLD (v1.3.3)
if sensor_anomaly and current_ec != 0:
    return check_sensor_recommendation

# NEW (v1.3.4)
if sensor_anomaly:
    return check_sensor_recommendation
```

## Impact on Users

### Before v1.3.4

```
Plant: Efeutute Wohnzimmer
EC: 0 mS/cm
Anomaly: true

Recommendation:
→ Action: "fertilize_now"
→ Timing: "Within 1-2 days"
→ Dosage: "50-75% of recommended"
→ Reasoning: "EC critically low at 0"
```

**Problem:** Fertilizing based on a potentially false EC=0 reading (caused by poor sensor contact) could:
- Waste fertilizer
- Harm plant if soil actually has adequate nutrients
- Not solve the real issue (sensor placement)

### After v1.3.4

```
Plant: Efeutute Wohnzimmer
EC: 0 mS/cm
Anomaly: true

Recommendation:
→ Action: "check_sensor"
→ Timing: "Before fertilizing"
→ Dosage: None
→ Reasoning:
  - FYTA reports sensor anomaly - reading may be unreliable
  - Current reading: EC=0 (may be incorrect due to poor sensor contact)
  - Check sensor placement and soil contact
  - Clean sensor electrodes if needed
  - Wait for stable readings before fertilizing
→ Warnings:
  - ⚠️ Do not fertilize based on unreliable sensor data!
  - Sensor anomaly detected - reading may be false
  - Reposition sensor for better soil contact
  - Monitor readings for 24-48 hours before taking action
```

**Result:** User checks sensor, finds poor contact, repositions it, and gets accurate EC reading before deciding on fertilization.

## Technical Details

### Code Changes

**File:** `src/fyta_mcp_server/utils/fertilization.py`

Line 276: Removed EC≠0 condition
```python
# OLD (v1.3.3)
if sensor_anomaly and current_ec != 0:

# NEW (v1.3.4)
if sensor_anomaly:
```

Lines 289-301: Updated reasoning and warnings
```python
# Added clarification that EC=0 may be false reading
"reasoning": [
    "FYTA reports sensor anomaly - reading may be unreliable",
    f"Current reading: EC={current_ec} (may be incorrect due to poor sensor contact)",
    "Check sensor placement and soil contact",
    "Clean sensor electrodes if needed",
    "Wait for stable readings before fertilizing"
],
"warnings": [
    "⚠️ Do not fertilize based on unreliable sensor data!",
    "Sensor anomaly detected - reading may be false",
    "Reposition sensor for better soil contact",
    "Monitor readings for 24-48 hours before taking action"
]
```

## Understanding the Logic

### Why does EC=0 + anomaly = sensor problem?

When a FYTA sensor reports:
- `soil_fertility: 0`
- `soil_fertility_anomaly: true`

This combination suggests:

1. **Poor Soil Contact:** Sensor electrodes not properly inserted in soil → cannot measure conductivity → reads as 0
2. **Dirty Electrodes:** Buildup on electrodes prevents measurement → reads as 0
3. **Sensor Malfunction:** Hardware issue preventing measurement → reads as 0

In all these cases, EC=0 is a **false reading**, not actual "no nutrients". The soil might have adequate nutrients, but the sensor can't measure it.

### When is EC=0 a valid reading?

EC=0 **without** anomaly flag (`soil_fertility_anomaly: false`) indicates:
- Sensor is working correctly
- Soil contact is good
- But no nutrients are present in the soil
- → Fertilization recommended

## Behavior Matrix (Updated)

| EC Value | Anomaly Flag | Action | Reasoning |
|----------|-------------|--------|-----------|
| 0 | true | `check_sensor` ✅ | Likely poor sensor contact (no contact = EC=0) |
| 0 | false | `fertilize_now` | Valid measurement: no nutrients present |
| 0.1 | true | `check_sensor` | Unreliable reading, verify sensor first |
| 0.1 | false | `fertilize_now` | Valid low reading, fertilization needed |
| 0.5 | true | `check_sensor` | Unreliable reading, verify sensor first |
| 0.5 | false | `maintain` | Valid optimal reading (winter range) |

## Migration Notes

No breaking changes. Existing installations will automatically use the corrected logic after upgrading to v1.3.4.

### What to Expect After Upgrading

**If you have plants with EC=0 and anomaly flag:**
- You will now see "check_sensor" recommendations instead of "fertilize_now"
- This is correct behavior - follow the sensor check steps before fertilizing
- After repositioning sensor, wait 24-48 hours for stable readings
- Then reassess fertilization needs based on new (reliable) EC value

**Steps to Fix Sensor Issues:**

1. **Check Placement:** Ensure sensor is fully inserted in soil (not hanging in air)
2. **Check Contact:** Sensor should be in moist soil with good contact to electrodes
3. **Clean Electrodes:** Wipe sensor electrodes with damp cloth if dirty
4. **Wait:** Allow 24-48 hours for readings to stabilize
5. **Reassess:** Request new diagnosis once readings are stable

## Version History

- **v1.3.3:** Added sensor anomaly handling, but excluded EC=0 (bug)
- **v1.3.4:** Fixed to include EC=0 in anomaly handling ✅

## Installation

Update to v1.3.4 by cloning/pulling the repository:

```bash
cd /path/to/fyta-mcp-server
git pull
git checkout v1.3.4
```

Or clone fresh:

```bash
git clone https://github.com/schimmmi/fyta-mcp-server.git
cd fyta-mcp-server
git checkout v1.3.4
```

## Links

- **GitHub Release:** https://github.com/schimmmi/fyta-mcp-server/releases/tag/v1.3.4
- **Full Changelog:** [CHANGELOG.md](../CHANGELOG.md)
- **Previous Release:** [v1.3.3](RELEASE_NOTES_v1.3.3.md)
- **Documentation:** [README.md](../README.md)

## Credits

Thanks to user testing that identified the EC=0 edge case was not handled correctly in v1.3.3.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
