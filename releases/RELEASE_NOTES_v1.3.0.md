# Release v1.3.0 - Hub Monitoring & EC=0 Anomaly Fix

**Release Date**: 2026-01-08

## 🎉 What's New

### 🔌 Hub Status Monitoring

Track and monitor all your FYTA Hubs directly through Claude!

**New MCP Tools:**

#### 1. `get_all_hubs`
Get an overview of all your FYTA Hubs:
```
Show me my FYTA Hubs
```

**Returns:**
- Hub ID and name
- Firmware version
- Online/offline status
- Last communication timestamps
- Connected plants and sensors
- Connection health alerts

**Example output:**
```json
{
  "hubs": [
    {
      "hub_id": "E8:06:90:C4:B7:EE",
      "hub_name": "Hub 7EE",
      "version": "1.3.4",
      "status": 1,
      "status_text": "Online",
      "received_data_at": "2026-01-08 20:49:08",
      "reached_hub_at": "2026-01-08 20:49:08",
      "connected_plants": [...]
    }
  ],
  "total_hubs": 2,
  "hubs_with_lost_connection": [],
  "all_online": true
}
```

#### 2. `get_hub_details`
Get detailed information about a specific hub:
```
Show details for Hub E8:06:90:C4:B7:EE
```

**Returns:**
- Full hub specifications
- All connected plants with sensor details
- Battery status of each sensor
- Last data reception timestamps
- Connection warnings

#### 3. `get_fyta_raw_data`
Access the complete, unfiltered FYTA API response:
```
Show me the raw FYTA API data
```

Useful for:
- Debugging API issues
- Discovering new API features
- Accessing data not yet exposed through specialized tools

---

### 🌱 EC=0 Anomaly Detection Fix

**The Problem:**
FYTA's API incorrectly flags `soil_fertility_anomaly: true` even when EC=0 is completely normal (winter dormancy, plants don't need nutrients).

This caused false "Sensor-Anomalie ⚠️" warnings during winter.

**The Solution:**
Intelligent anomaly detection that understands context:

| Situation | Interpretation | Status |
|-----------|---------------|--------|
| EC=0 + Winter thresholds (min=0, max=0) | No nutrients needed | ✅ Normal |
| EC=0 + Summer thresholds (min>0) | Sensor malfunction | ⚠️ Error |
| EC≠0 + Anomaly flag set | Hardware issue | ⚠️ Error |

**Before:**
```
⚠️ Sensor-Anomalie: EC sensor malfunction or poor soil contact
```

**After:**
```
✅ Nutrients: No nutrients (EC=0) - normal for winter dormancy
```

---

## 🔧 Technical Changes

### Files Modified

**1. `src/fyta_mcp_server/tools.py`**
- Added `get_all_hubs` tool definition (lines 429-448)
- Added `get_hub_details` tool definition (lines 449-471)
- Added `get_fyta_raw_data` tool definition (lines 410-428)

**2. `src/fyta_mcp_server/handlers.py`**
- Implemented `handle_get_all_hubs()` (lines 1997-2043)
- Implemented `handle_get_hub_details()` (lines 2046-2110)
- Implemented `handle_get_fyta_raw_data()` (lines 1983-1994)
- Registered new handlers in `TOOL_HANDLERS` (lines 2129-2131)

**3. `src/fyta_mcp_server/utils/thresholds.py`**
- Smart EC=0 anomaly detection (lines 250-267)
- Context-aware winter/summer threshold detection

**4. Documentation**
- Updated `README.md` with Hub Monitoring section
- Updated `CHANGELOG.md` with v1.3.0 entry
- Enhanced event detection documentation
- Clarified MCP limitations (no push notifications)

---

## 📊 Use Cases

### Hub Health Monitoring
```
Question: "Are all my hubs online?"
→ get_all_hubs
→ Shows status of all hubs and connection issues
```

### Troubleshooting Connectivity
```
Question: "Why isn't my bathroom plant sensor updating?"
→ get_hub_details for specific hub
→ Shows which sensors are connected and last seen
```

### Winter Plant Care
```
Question: "Are my plants healthy?"
→ No more false "Sensor-Anomalie" warnings
→ Correct "EC=0 normal for winter" status
```

---

## 🚀 Upgrade Instructions

### Docker Users
```bash
cd ~/fyta-mcp-server
docker-compose pull
docker-compose up -d
```

### Python Users
```bash
cd ~/fyta-mcp-server
git pull
source .venv/bin/activate
pip install -e .
```

Restart Claude Desktop after update.

---

## 🐛 Bug Fixes

- **Fixed**: EC=0 false positive anomaly detection
- **Fixed**: Missing hub data access in MCP tools
- **Improved**: Documentation clarity on MCP limitations

---

## 📝 Notes

### MCP Protocol Limitations

**What MCP Cannot Do:**
- Push notifications (request-response only)
- Background monitoring
- Scheduled tasks

**Recommended Workarounds:**
- Ask Claude daily: "Are there issues with my plants?"
- Integrate with n8n/Home Assistant for automation
- Use cron jobs for scheduled checks

See [examples/](../examples/) for integration guides.

---

## 🙏 Credits

Special thanks to the community for reporting the EC=0 anomaly issue!

---

## 📦 Release Assets

- **Source code** (zip)
- **Source code** (tar.gz)

GitHub: https://github.com/schimmmi/fyta-mcp-server/releases/tag/v1.3.0

---

**Full Changelog**: https://github.com/schimmmi/fyta-mcp-server/blob/main/CHANGELOG.md
