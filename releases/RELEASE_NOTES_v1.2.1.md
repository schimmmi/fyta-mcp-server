# FYTA MCP Server v1.2.1 🔧

**Critical bugfix release** - Fixes event detection using incorrect FYTA status codes instead of smart evaluation.

## 🚨 Critical Fix

### Event Detection Now Uses Smart Evaluation

Fixed a critical bug where `get_plant_events` was generating false alerts based on FYTA's buggy status codes instead of using the smart threshold evaluation.

**Problem:**
- `get_plant_events` was detecting "temperature extreme" events even when temperature was optimal (18-20°C)
- FYTA's API returns `temperature_status: 3` (too high) even when actual temperature is within 5-25°C optimal range
- Plant objects from `/user-plant` endpoint contain only status codes, **not actual sensor values**
- Smart evaluation requires actual values (temperature, light, moisture, nutrients) to work correctly

**Solution:**
- Now enriches plant data with actual sensor values from latest measurement before evaluation
- Plant object is populated with `temperature`, `light`, `soil_moisture`, `soil_fertility` from measurements
- Smart threshold evaluation receives complete data and can correctly assess status
- Events are now generated based on accurate threshold evaluation, not buggy FYTA status codes

**Impact:**
- ✅ No more false "temperature extreme" alerts when temperature is actually optimal
- ✅ Event detection now consistent with `diagnose_plant` behavior
- ✅ Automation systems (n8n, Home Assistant, etc.) receive accurate events
- ✅ All metrics (temperature, light, moisture, nutrients) now evaluated correctly

## 🔍 Example

### Before (v1.2.0):
```json
{
  "event_type": "temperature_extreme",
  "message": "Temperature is too high - plant stress risk",
  "severity": "critical"
}
```
**Even though temperature was 19°C (optimal range: 5-25°C)** ❌

### After (v1.2.1):
```json
{
  "event_count": 0,
  "events": []
}
```
**No false alerts - temperature correctly recognized as optimal** ✅

## 🔧 Technical Details

### Changes in `handlers.py`

Added measurement value enrichment before smart evaluation:

```python
# Enrich plant object with latest measurement values
enriched_plant_data = plant.copy()
if measurements_week:
    measurements_list = extract_measurements_from_response(measurements_week)
    if measurements_list:
        latest = measurements_list[-1]
        # Add actual values from measurements (plant object only has status codes)
        enriched_plant_data["temperature"] = latest.get("temperature")
        enriched_plant_data["light"] = latest.get("light")
        enriched_plant_data["soil_moisture"] = latest.get("soil_moisture")
        enriched_plant_data["soil_fertility"] = latest.get("soil_fertility")

# Use smart status evaluation with enriched data
smart_status = evaluate_plant_status(enriched_plant_data, measurements_week)
```

### Debug Logging Added

Added comprehensive logging to `thresholds.py` for debugging:
- Whether thresholds were found
- Actual threshold values (min_good, max_good)
- Current sensor values
- Evaluation results

Useful for troubleshooting threshold-related issues.

## 📦 Installation

### Update from v1.2.0

```bash
cd /path/to/fyta-mcp-server
git pull
git checkout v1.2.1
pip install -e .  # If not using Docker
```

### Docker

```bash
cd /path/to/fyta-mcp-server
git pull
git checkout v1.2.1
docker-compose build
docker-compose up -d
```

### Verify Fix

Test event detection:
```
Get plant events
```

Should now only show actual issues, not false temperature alerts.

## 🎯 Who Should Update?

**Update immediately if:**
- ✅ You're using `get_plant_events` for automation (n8n, Home Assistant, webhooks)
- ✅ You rely on event notifications for plant care
- ✅ You experienced false temperature extreme alerts

**Safe to skip if:**
- ❌ You don't use `get_plant_events` tool
- ❌ You only use basic plant data tools (`get_all_plants`, `get_plant_details`)

## 📝 Related Issues

This fix addresses the same FYTA API inconsistency issue that was solved in v1.2.0 for `diagnose_plant`, but was missed in the `get_plant_events` implementation.

The root cause is that FYTA's `/user-plant` endpoint returns:
- ✅ Status codes (temperature_status, moisture_status, etc.)
- ❌ **NOT** actual sensor values

Actual values must be fetched from `/user-plant/measurements/[plantID]` endpoint.

## 🔗 Links

- [Full CHANGELOG](https://github.com/schimmmi/fyta-mcp-server/blob/main/CHANGELOG.md)
- [Documentation](https://github.com/schimmmi/fyta-mcp-server/blob/main/README.md)
- [Report Issues](https://github.com/schimmmi/fyta-mcp-server/issues)

---

**Full Changelog**: https://github.com/schimmmi/fyta-mcp-server/compare/v1.2.0...v1.2.1
