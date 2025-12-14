# FYTA MCP Server v1.1.0 📊

Feature release adding historical plant measurements support.

## 🎯 New Features

### Historical Measurements Tool
- **get_plant_measurements** - Access historical sensor data for any plant
- Retrieve time-series data for comprehensive plant health tracking
- Monitor trends in temperature, light, moisture, and nutrients over time

## 📈 What's New

### API Integration
- New endpoint: `GET /user-plant/measurements/[plantID]`
- Returns complete historical measurement data
- Seamless integration with existing FYTA API authentication

### MCP Tool
```
Show me historical measurements for plant with ID 123
```

Returns detailed time-series data including:
- Temperature readings over time
- Light exposure history
- Soil moisture trends
- Nutrient level changes

## 🔧 Technical Changes

### Client Updates
- Added `get_plant_measurements(plant_id)` method to FytaClient
- New API endpoint constant: `FYTA_MEASUREMENTS_ENDPOINT`

### Tool Handler
- Implemented `handle_get_plant_measurements()` handler
- Proper error handling for invalid plant IDs
- JSON formatted measurement data output

### Documentation
- Updated README.md with new tool information
- Added usage example for measurements tool
- Updated API endpoints list

## 📦 Installation

Update to v1.1.0:

```bash
cd /path/to/fyta-mcp-server
git pull
pip install -e .  # If not using Docker
```

Or rebuild Docker container:

```bash
docker-compose build
docker-compose up -d
```

## 🔗 Links

- [Full CHANGELOG](https://github.com/schimmmi/fyta-mcp-server/blob/main/CHANGELOG.md)
- [Documentation](https://github.com/schimmmi/fyta-mcp-server/tree/main/docs)
- [Report Issues](https://github.com/schimmmi/fyta-mcp-server/issues)

---

**Full Changelog**: https://github.com/schimmmi/fyta-mcp-server/compare/v1.0.0...v1.1.0
