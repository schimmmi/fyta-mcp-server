# Release Notes v1.3.2 - Fix Winter Fertilization Logic

**Release Date:** 2026-01-15

## ❄️ Overview

This release fixes overly lenient winter fertilization thresholds that incorrectly treated very low EC values (0.08 mS/cm) as "optimal". Plants need adequate nutrients year-round, even during winter dormancy.

## Fixed

### Winter Fertilization Logic

**Problem:** The previous winter logic was too lenient, treating EC values as low as 0.08 mS/cm as "optimal" during winter months (November-February). This led to incorrect recommendations:
- EC=0.1 → Status: "optimal", Action: "maintain" ❌
- Plants were not getting fertilization recommendations despite nutrient deficiency

**Root Cause:** Overly aggressive winter adjustments assumed plants need almost no nutrients during dormancy.

**Reality:** Even in winter, plants need a minimum nutrient level. While they may consume nutrients more slowly, EC values below 0.2 mS/cm indicate deficiency.

**Fix:**
- Winter `critical_low` updated from 0.05 to 0.2 mS/cm
- Winter `min_optimal` now calculated from substrate-specific ranges (0.2-0.5 mS/cm)
- Winter `max_optimal` capped at 1.0 mS/cm
- EC < 0.2 now correctly triggers fertilization recommendations in all seasons

## Impact on Users

### Before This Release (Winter)

```
Plant: Efeutute Bad
EC: 0.1 mS/cm
Status: ✅ Optimal
Action: maintain - "Continue regular schedule"
```

### After This Release (Winter)

```
Plant: Efeutute Bad
EC: 0.1 mS/cm
Status: 🔴 Critical Low
Action: fertilize_now - "Within 1-2 days"
```

## Technical Details

### Code Changes

**File:** `src/fyta_mcp_server/utils/fertilization.py`

Lines 50-63: Updated winter threshold logic
```python
# OLD (Winter)
critical_low = 0.05  # Only truly starved plants
min_optimal = 0.08   # Very low EC is acceptable in winter dormancy
max_optimal = max(max_optimal, 0.8)

# NEW (Winter)
critical_low = 0.2  # Plants still need minimum nutrients
min_optimal = max(0.2, min_optimal * 0.5)  # Lower end of optimal range
max_optimal = min(1.0, max_optimal)  # Cap at 1.0 in winter
```

Lines 9-15: Updated documentation
```python
# OLD
- 0.0 - 0.3: Very low - Urgent fertilization needed

# NEW
- 0.0 - 0.2: Very low - Urgent fertilization needed
Winter (Nov-Feb): Plants prefer lower end of range (0.2-1.0 mS/cm)
```

Lines 228-230: Updated trend prediction
```python
# OLD
if direction == "decreasing" and current_ec > 0.3:
    days_until_critical = (current_ec - 0.3) / abs(slope_per_day)

# NEW
if direction == "decreasing" and current_ec > 0.2:
    days_until_critical = (current_ec - 0.2) / abs(slope_per_day)
```

## Winter vs Summer Thresholds

| Season | Critical Low | Min Optimal | Max Optimal |
|--------|-------------|-------------|-------------|
| **Summer** | 0.2 mS/cm | 0.6 mS/cm | 1.0 mS/cm |
| **Winter** | 0.2 mS/cm | 0.2-0.5 mS/cm | 1.0 mS/cm |

**Key Points:**
- Critical threshold is **the same** year-round (0.2 mS/cm)
- Winter allows **lower optimal range** (plants prefer less nutrients)
- Winter still requires **minimum 0.2 mS/cm** to avoid deficiency

## Example Scenarios

### Scenario 1: EC=0 (Any Season)
```json
{
  "salinity": 0,
  "season": "winter"
}
```

**Result:** Status = "critical_low", Action = "fertilize_now"
**Reason:** EC=0 means no nutrients present, requires immediate fertilization

### Scenario 2: EC=0.1 (Winter)
```json
{
  "salinity": 0.1,
  "season": "winter"
}
```

**Before:** Status = "optimal", Action = "maintain" ❌
**After:** Status = "critical_low", Action = "fertilize_now" ✅
**Reason:** Even in winter, EC < 0.2 indicates nutrient deficiency

### Scenario 3: EC=0.3 (Winter)
```json
{
  "salinity": 0.3,
  "season": "winter"
}
```

**Result:** Status = "optimal", Action = "maintain"
**Reason:** EC=0.3 is within winter optimal range (0.2-1.0)

### Scenario 4: EC=0.3 (Summer)
```json
{
  "salinity": 0.3,
  "season": "summer"
}
```

**Result:** Status = "low", Action = "fertilize_soon"
**Reason:** EC=0.3 is below summer optimal range (0.6-1.0)

## Migration Notes

No breaking changes. The server will automatically use the new winter thresholds.

### If you see different diagnoses after upgrading:

**Plants showing "critical_low" nutrients that previously showed "optimal" in winter:**
- This is correct! EC < 0.2 means nutrient deficiency, even in winter
- Fertilize your plants with 50-75% of normal dosage
- Monitor weekly to ensure EC increases

**More fertilization recommendations in winter:**
- This is expected and correct behavior
- Plants still need minimum nutrients during dormancy
- Use slightly reduced dosages (50-75%) in winter months

## Substrate-Specific Behavior

The winter adjustments respect substrate-specific requirements:

| Substrate | Summer Optimal | Winter Optimal |
|-----------|----------------|----------------|
| Organic | 0.8-1.2 | 0.4-1.0 |
| Mineral | 0.6-1.0 | 0.3-1.0 |
| Hydro/Semi-Hydro | 0.4-0.8 | 0.2-0.8 |
| Lechuza PON | 0.5-0.9 | 0.25-0.9 |

## Installation

Update to v1.3.2 by cloning/pulling the repository:

```bash
cd /path/to/fyta-mcp-server
git pull
git checkout v1.3.2
```

Or clone fresh:

```bash
git clone https://github.com/schimmmi/fyta-mcp-server.git
cd fyta-mcp-server
git checkout v1.3.2
```

## Links

- **GitHub Release:** https://github.com/schimmmi/fyta-mcp-server/releases/tag/v1.3.2
- **Full Changelog:** [CHANGELOG.md](../CHANGELOG.md)
- **Previous Release:** [v1.3.1](RELEASE_NOTES_v1.3.1.md)
- **Documentation:** [README.md](../README.md)

## Credits

Thanks to user feedback for identifying that winter thresholds were too lenient and plants were not receiving adequate fertilization recommendations.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
