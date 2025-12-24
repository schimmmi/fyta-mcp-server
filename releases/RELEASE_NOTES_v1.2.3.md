# Release v1.2.3 - Critical Bugfix for get_plants_needing_attention

🎄 **Frohe Weihnachten!** This release fixes a critical bug in the `get_plants_needing_attention` tool that was still using FYTA's unreliable status codes instead of smart threshold evaluation.

## 🐛 Critical Bug Fix

### Issue
The `get_plants_needing_attention` tool was still using FYTA's buggy status codes directly, leading to false alerts like:
- "Temperature too high" when temperature was 19°C (optimal range: 5-25°C)
- "Moisture too high" when moisture was within normal range
- "Nutrients too high" when nutrients were optimal

This was the **same issue** fixed in v1.2.1 for `get_plant_events`, but `get_plants_needing_attention` was overlooked.

### Root Cause
Two bugs were present:

1. **Using FYTA status codes directly**: The tool checked `plant["temperature_status"] != 2` instead of using smart evaluation
2. **Wrong data structure handling**: Smart evaluation returns dictionaries like `{"status": 2, "value": 19, ...}`, but the code was comparing the entire dict against integers

### The Fix

**Before:**
```python
# ❌ Using buggy FYTA status codes directly
if plant["temperature_status"] != 2:
    issues.append("Temperature too high")
```

**After:**
```python
# ✅ Enrich plant data with actual measurements
enriched_plant_data = plant.copy()
measurements_list = extract_measurements_from_response(measurements_week)
if measurements_list:
    latest = measurements_list[-1]
    enriched_plant_data["temperature"] = latest.get("temperature")
    # ... other metrics

# ✅ Use smart evaluation
smart_status = evaluate_plant_status(enriched_plant_data, measurements_week)

# ✅ Extract status code from result dictionary
temp_status = smart_status.get("temperature")
if temp_status and isinstance(temp_status, dict):
    status_code = temp_status.get("status")
    if status_code == 3:
        issues.append("Temperature too high")
```

## 🔧 Technical Changes

### Updated Files
- **`src/fyta_mcp_server/handlers.py`**:
  - Fixed `handle_get_plants_needing_attention` to use smart evaluation
  - Added measurement data enrichment
  - Fixed status code extraction from evaluation results

- **`src/fyta_mcp_server/utils/thresholds.py`**:
  - Added debug logging for moisture evaluation
  - Added debug logging for nutrients evaluation
  - Added threshold information to evaluation results

### Debug Logging Examples

The enhanced logging now shows:
```
Temperature evaluation: value=17, min_good=5, max_good=25, result=2 (optimal)
Moisture evaluation: value=71, min_good=30, max_good=70, result=3 (high)
Nutrients evaluation: value=0.7, min_good=0.6, max_good=1, result=2 (optimal), adjusted=True
```

This makes it much easier to understand why a plant is flagged for attention and whether the thresholds are reasonable.

## 📊 Impact

### What Works Now
- `get_plants_needing_attention` correctly evaluates plant status against actual threshold values
- No more false alerts for temperature, moisture, or nutrients when values are within optimal range
- Consistent behavior with `get_plant_events` (both use smart evaluation)

### Example
**Before v1.2.3:**
```json
{
  "plants_needing_attention": 2,
  "plants": [
    {
      "id": 108009,
      "issues": ["Temperature too high", "Moisture too high", "Nutrients too high"]
    }
  ]
}
```

**After v1.2.3 (with same plant data):**
```json
{
  "plants_needing_attention": 1,
  "plants": [
    {
      "id": 108009,
      "issues": ["Moisture too high"]  // Only real issue (71% vs 30-70% threshold)
    }
  ]
}
```

## 🎯 For Users

### Who Should Upgrade?
**Everyone using `get_plants_needing_attention`** should upgrade immediately. The old version produces unreliable results.

### Breaking Changes
None - this is a pure bugfix that makes the tool work as originally intended.

### Notes on Alerts
After upgrading, you may notice:
- **Fewer false alerts**: Temperature, moisture, and nutrients are now evaluated correctly
- **Different alerts**: Smart evaluation uses actual values vs. thresholds, not buggy status codes
- **Substrate considerations**: Some alerts may still occur with PON/Lechuza systems due to different electrical properties compared to soil - these are measurement limitations, not bugs

## 📝 Related Issues

This completes the smart evaluation migration started in v1.2.1:
- ✅ v1.2.1: Fixed `get_plant_events`
- ✅ v1.2.3: Fixed `get_plants_needing_attention`

Both tools now consistently use smart threshold evaluation instead of FYTA's unreliable status codes.

## 🙏 Acknowledgments

Thanks to @schimmmi for testing and identifying that `get_plants_needing_attention` still had the status code bug! The detailed testing on Christmas Eve with Lechuza/PON plants helped nail down both the bug and the correct fix.

---

**Full Changelog**: https://github.com/schimmmi/fyta-mcp-server/compare/v1.2.2...v1.2.3
