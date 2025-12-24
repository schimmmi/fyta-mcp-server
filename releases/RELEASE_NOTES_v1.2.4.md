# Release Notes - v1.2.4

## 🎯 Overview

Version 1.2.4 completes the smart evaluation migration across all MCP tools and introduces intelligent watering prediction with moisture trend analysis. This release fixes the remaining tools that were still using FYTA's buggy status codes and adds winter-aware fertilization thresholds.

## ✨ New Features

### 💧 Intelligent Watering Prediction

Complete moisture trend analysis system with predictive recommendations:

- **7-day trend analysis** using linear regression
- **Predictive watering dates**: "Water in X days" based on consumption rate
- **Moisture consumption tracking**: Shows % moisture loss per day/week
- **Substrate-specific thresholds**: Different optimal ranges for organic, mineral, PON, semi-hydro, hydroponic substrates
- **Confidence scoring**: R² calculation to assess prediction reliability
- **Integrated into `diagnose_plant`**: Full watering recommendations with trend data

Example output:
```json
{
  "watering": {
    "moisture_trend": {
      "analyzed": true,
      "data_points": 654,
      "current_moisture": 69,
      "trend": "decreasing",
      "slope_per_day": -4.893,
      "confidence": 0.99,
      "prediction": {
        "days_until_optimal": 2.0,
        "recommended_watering_date": "2025-12-26"
      },
      "consumption_rate": {
        "moisture_per_day": 4.89,
        "moisture_per_week": 34.3,
        "description": "Plant consumes ~34.3% moisture per week"
      }
    }
  }
}
```

### 🌱 Winter-Aware Fertilization

Season-aware EC thresholds prevent false alerts during dormancy:

- **Winter detection**: Automatically adjusts thresholds for November-February
- **Dormancy-appropriate ranges**: EC 0.08-0.8 considered optimal in winter (vs 0.6-1.0 in summer)
- **Prevents false "critical low" alerts**: EC 0.1 is normal during winter dormancy
- **More realistic recommendations**: Accounts for reduced nutrient consumption

Before v1.2.4:
```
EC 0.1 → 🔴 Critical Low - Fertilize immediately!
```

After v1.2.4:
```
EC 0.1 → ✅ Optimal (winter dormancy threshold)
```

## 🔧 Critical Fixes

### Complete Smart Evaluation Migration

**All tools now use smart evaluation instead of buggy FYTA status codes:**

- ✅ `get_plant_details`: Now enriches data and uses smart evaluation
- ✅ `get_all_plants`: Now enriches data and uses smart evaluation for all plants
- ✅ `diagnose_plant`: Added measurement enrichment before evaluation
- ✅ `get_plants_needing_attention`: Fixed in v1.2.3
- ✅ `get_plant_events`: Fixed in v1.2.1

**Why this matters**: FYTA's status codes (temperature_status, light_status, etc.) are often inconsistent with actual threshold values. Smart evaluation compares actual measured values against thresholds for accurate assessments.

### Bug Fixes

1. **Light Evaluation**: Fixed Light=0 handling
   - Light=0 at night no longer shows as "Critical"
   - Adjusted `min_acceptable=0` to prevent false alerts
   - Added Status 4 (Critical) support in status_map

2. **Moisture Trend Analysis**: Fixed field name handling
   - Now tries multiple field name variants: `date_utc`, `timestamp`, `measured_at`
   - Handles both `soil_moisture` and `moisture` field names
   - Robust ISO timestamp parsing

3. **Fertilization**: Fixed winter threshold logic
   - `critical_low`: 0.3 → 0.05 (winter)
   - `min_optimal`: 0.6 → 0.08 (winter)
   - `max_optimal`: 1.0 → 0.8 (winter)

## 📁 Technical Details

### New Files

**`src/fyta_mcp_server/utils/watering.py`** (360 lines)
- `get_moisture_status()`: Evaluate current moisture with substrate-specific thresholds
- `analyze_moisture_trend()`: 7-day trend analysis with linear regression and prediction
- `get_watering_recommendation()`: Comprehensive watering advice

### Modified Files

**`src/fyta_mcp_server/handlers.py`**
- Watering analysis integration in `diagnose_plant` (lines 1151-1198)
- Fixed `get_plant_details` to use smart evaluation (lines 145-219)
- Fixed `get_all_plants` to use smart evaluation (lines 81-163)
- Added measurement enrichment to `diagnose_plant` (lines 790-803)
- All tools now extract status codes correctly from evaluation result dicts
- Fixed status_map to include Status 4 (Critical)

**`src/fyta_mcp_server/utils/thresholds.py`**
- Light evaluation with adjusted min_acceptable to prevent false critical alerts
- Added threshold info to all evaluation results
- Comprehensive debug logging for temperature, light, moisture, nutrients

**`src/fyta_mcp_server/utils/fertilization.py`**
- Season-aware thresholds with `consider_season` parameter
- Winter dormancy detection (months 11, 12, 1, 2)
- Adjusted thresholds: `critical_low=0.05`, `min_optimal=0.08`, `max_optimal=0.8`

## 🔄 Migration Guide

If you were using previous versions, no changes are required. All improvements are transparent:

- **get_plant_details**: Now returns more accurate status assessments
- **get_all_plants**: Plant statuses are now reliable
- **diagnose_plant**: Now includes watering prediction and winter-aware fertilization
- **get_plants_needing_attention**: More accurate alert detection (fixed in v1.2.3)

## 📊 Performance

- **Watering prediction**: Analyzes up to 7 days of measurements (typically 300-700 data points)
- **Linear regression**: Fast calculation, even with large datasets
- **Data enrichment**: Minimal overhead, only fetches measurements once per tool call

## 🙏 Acknowledgments

Special thanks to the community for reporting the false alert issues and suggesting the watering prediction feature!

## 🐛 Known Issues

None at this time.

## 📝 Full Changelog

See [CHANGELOG.md](../CHANGELOG.md) for complete details.

---

**Installation**: `pip install fyta-mcp-server==1.2.4`

**Docker**: `docker pull schimmmi/fyta-mcp-server:1.2.4`

**Documentation**: See [README.md](../README.md) for complete usage guide.
