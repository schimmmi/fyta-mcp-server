# Release Notes v1.2.6

**Release Date:** 2026-01-04

## 🐛 Critical Bug Fixes

### 1. **soil_fertility=0 Treated as None**

**The Bug:**
```python
# Old code (WRONG!)
nutrients = latest.get("soil_fertility") or latest.get("salinity")
# If soil_fertility=0, this evaluates to None because 0 is falsy!
```

**Impact:**
- Plants with EC=0 (winter dormancy, sensor issues) showed `nutrients=None`
- Smart evaluation couldn't run without value
- Diagnose showed "nutrients: null" instead of detecting the issue

**The Fix:**
```python
# New code (CORRECT!)
nutrients = latest.get("soil_fertility") if latest.get("soil_fertility") is not None else latest.get("salinity")
# Explicitly checks for None, so 0 is preserved
```

Fixed in **6 locations** across handlers.py (lines 115, 226, 314, 978, 1346, 1594)

---

### 2. **Sensor Anomaly Detection Missing**

**The Problem:**
- FYTA API provides `soil_fertility_anomaly: true` flag when EC sensor has issues
- This flag was **ignored** - not transferred from measurements
- Result: Sensor malfunctions shown as "optimal" (winter thresholds allow EC=0)

**The Solution:**
- Transfer anomaly flags from measurements: `soil_fertility_anomaly`, `soil_moisture_anomaly`
- `evaluate_plant_status()` detects anomaly and sets status=4 ("sensor_error")
- `diagnose_plant` shows clear warning:

```json
{
  "parameter": "nutrients",
  "status": "sensor_error",
  "severity": "high",
  "explanation": "Nutrient sensor reports anomaly (e.g., EC sensor malfunction or poor soil contact). Check sensor placement and clean electrodes. Reading may be unreliable.",
  "anomaly": true
}
```

**Real-World Example:**
- Plant 108010 (Efeutute Bad): EC=0, `soil_fertility_anomaly: true`
- **Before:** "nutrients: Optimal" ✅ (WRONG!)
- **After:** "Nutrient sensor reports anomaly" ⚠️ (CORRECT!)

---

### 3. **Smart Evaluation Ignored in diagnose_plant**

**The Bug:**
```python
# Old code
if smart_status.get("use_fyta_status", True):  # Default True!
    # Use buggy FYTA status codes
else:
    # Use smart evaluation
```

**Impact:**
- Smart evaluation ran but results were **thrown away**
- FYTA's unreliable status codes used instead
- Sensor errors not detected

**The Fix:**
```python
# New code
if smart_status.get("use_fyta_status", False):  # Default False!
    # Use FYTA only as fallback (no thresholds available)
else:
    # Use smart evaluation (preferred)
```

Now smart evaluation is **actually used** when thresholds exist!

---

### 4. **KeyError for optimal_hours**

**The Bug:**
- Sensor error issues didn't have `optimal_hours` field
- Code assumed all issues have this field → crash

**The Fix:**
- Added `optimal_hours: None` to sensor_error case
- Changed `issue["optimal_hours"]` to safe `issue.get("optimal_hours")`

---

## 🆕 What's New

### Enhanced Logging
```
INFO: Plant 108010 - Latest measurement values: soil_fertility=0, soil_fertility_anomaly=True
INFO: Plant 108010 - Enriched data: nutrients=0, soil_fertility_anomaly=True
WARNING: Nutrients sensor anomaly detected for plant 108010: value=0, treating as unreliable
```

### New Status Code
- **Status 4:** "sensor_error" - for unreliable sensor readings
- Treated as high severity issue with actionable guidance

---

## 📊 Impact Summary

| Issue | Before | After |
|-------|--------|-------|
| EC=0 handling | `nutrients=None` | `nutrients=0` ✓ |
| Sensor anomaly | Ignored, shown as "Optimal" | Detected, shown as "sensor_error" ✓ |
| Smart evaluation | Ignored (used buggy FYTA codes) | Active and working ✓ |
| Crash on sensor error | KeyError | Handled gracefully ✓ |

---

## 🔧 Technical Details

### Files Changed
- `src/fyta_mcp_server/handlers.py`: 6 locations fixed for EC=0 handling, sensor error support
- `src/fyta_mcp_server/utils/thresholds.py`: Anomaly detection, sensor_error status
- Enhanced logging throughout

### Breaking Changes
None - this is a pure bug fix release

### Migration Guide
No action needed - just update to v1.2.6

---

## 🧪 Testing

### Verified With
- **Plant 108010** (Efeutute Bad): EC=0, `soil_fertility_anomaly: true`
  - Correctly shows sensor error warning
  - No longer reports false "Optimal" status
  - Actionable guidance provided

### Test Command
```bash
Fdiagnose_plant plant_id=108010
```

---

## 🙏 Credits

Found and fixed during real-world debugging session with user feedback.

**Key Insight:** *"0 ist auch im Winter zu wenig"* - Even in winter, EC=0 isn't normal. The sensor had an anomaly flag all along!
