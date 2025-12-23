# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-12-23

### Added
- **Intelligent Plant Diagnosis** (`diagnose_plant`): Comprehensive health analysis with smart threshold evaluation
- **Smart Threshold Evaluation**: Fixes FYTA's inconsistent status codes using actual threshold values
- **EC-Based Fertilization**: Intelligent fertilization recommendations with trend prediction
  - Substrate-specific thresholds (organic, mineral, PON, hydroponic)
  - Linear regression for EC trend analysis
  - Prediction of when EC reaches critical levels
- **Sensor Capability Detection**: Automatically detects sensor types (Beam 2.0, Beam, Legacy)
  - Shows appropriate warnings when light sensor unavailable
  - Prevents DLI analysis on sensors without light capability
- **Trend Analysis** (`get_plant_trends`): Track changes in moisture, temperature, nutrients, light
  - Direction and percentage change
  - Critical time predictions for moisture
- **Statistical Analysis** (`get_plant_statistics`): Mean, min, max, stability scores, anomaly detection
- **DLI Analysis** (`get_plant_dli_analysis`): Daily Light Integral calculations with seasonal predictions
- **Plant Context Management**: Store substrate type, container type, and growth phase
  - `set_plant_context`: Store context information FYTA doesn't know
  - `get_plant_context`: Retrieve context with context-aware recommendations
- **Care Action Tracking**: Log and analyze manual care actions
  - `log_plant_care_action`: Track watering, fertilizing, repotting
  - `get_plant_care_history`: View history with effectiveness analysis
- **Event Detection** (`get_plant_events`): Automatically detect significant changes
  - Moisture drops, temperature spikes, light changes, nutrient depletion

### Fixed
- **Critical**: Fixed field name mappings for FYTA API
  - Changed `moisture` → `soil_moisture`
  - Changed `salinity` → `soil_fertility`
  - Changed `measured_at` → `date_utc`
- **Critical**: Fixed timestamp parsing for FYTA's "YYYY-MM-DD HH:MM:SS" format
- Fixed NoneType errors in smart status evaluation with safe dictionary access
- Fixed sensor type detection (type 3 = Beam without light sensor)
- Fixed severity sorting in recommendations (added "info" severity level)
- Fixed EC value extraction from measurements (not from plant object)
- Fixed `get_plant_history` method name (was incorrectly `get_actions`)

### Changed
- Enhanced `diagnose_plant` with confidence scoring based on data quality
- Improved README.md with comprehensive documentation of all features
- Added detailed technical documentation for sensor types and field names
- Organized utility modules for better code structure

### Technical Details
- New utility modules:
  - `utils/thresholds.py`: Smart threshold evaluation (240 lines)
  - `utils/fertilization.py`: EC-based fertilization logic (370 lines)
  - `utils/sensor_info.py`: Sensor capability detection (240 lines)
  - `utils/trends.py`: Trend analysis with linear regression
  - `utils/statistics.py`: Statistical analysis and anomaly detection
  - `utils/dli.py`: Daily Light Integral calculations
  - `utils/events.py`: Event detection system
  - `utils/care_actions.py`: Care tracking and analysis
  - `utils/plant_context.py`: Context storage and recommendations
- Winter salinity bug workaround (uses summer thresholds when min=max=0)
- Substrate-aware EC thresholds with different ranges per substrate type
- R² confidence scoring for trend predictions

## [1.1.1] - 2025-12-13

### Fixed
- **Critical**: Fixed measurements endpoint to use POST instead of GET
- Added required request body with timeline parameter
- Fixed 422 error when retrieving plant measurements

### Changed
- `get_plant_measurements` now accepts optional `timeline` parameter ("hour", "day", "week", "month")
- Updated API documentation to reflect POST method
- Default timeline is "month" if not specified

### Technical Details
- Changed from `client.get()` to `client.post()` with JSON body
- Added timeline parameter to tool schema with enum validation
- Handler now passes timeline parameter to client method

## [1.1.0] - 2025-12-13

### Added
- New MCP tool: `get_plant_measurements` - Get historical sensor measurements for a specific plant
- New API endpoint integration: `GET /user-plant/measurements/[plantID]`
- Time-series data support for temperature, light, moisture, and nutrients
- Enhanced plant monitoring with historical data access

### Changed
- Updated README.md with new tool documentation
- Added API endpoint to documentation
- Updated version to 1.1.0

### Technical Details
- New method in FytaClient: `get_plant_measurements(plant_id)`
- New tool handler: `handle_get_plant_measurements()`
- Returns complete historical measurement data in JSON format

## [1.0.0] - 2025-12-13

### Added
- Initial release of FYTA MCP Server
- Complete project restructuring with modular architecture
  - Separated client, tools, handlers, and server logic
  - Professional Python package structure (`src/fyta_mcp_server/`)
- Four MCP tools for plant monitoring:
  - `get_all_plants` - Get all plants with sensor data
  - `get_plant_details` - Get detailed info for specific plant
  - `get_plants_needing_attention` - Find plants requiring care
  - `get_garden_overview` - Get overview of all gardens
- Docker support with Dockerfile and docker-compose.yml
- Comprehensive documentation:
  - README.md with installation and usage instructions
  - QUICKSTART.md guide
  - OVERVIEW.md with project structure
- Test suite with connection test script
- Configuration examples for Claude Desktop integration
- Support for environment variables via .env file
- Automatic token refresh and authentication handling

### Technical Details
- Python 3.10+ support
- Dependencies: httpx, mcp, python-dotenv
- FYTA API integration (web.fyta.de)
- MCP Protocol 2025-06-18 compatibility
- Docker image based on Python 3.11-slim
- Editable package installation support

### Project Structure
```
fyta-mcp-server/
├── src/fyta_mcp_server/     # Main package
│   ├── __init__.py
│   ├── __main__.py
│   ├── client.py           # FYTA API client
│   ├── handlers.py         # Tool handlers
│   ├── server.py           # MCP server setup
│   └── tools.py            # Tool definitions
├── tests/                   # Test suite
├── docs/                    # Documentation
└── Docker files             # Container support
```

[1.2.0]: https://github.com/schimmmi/fyta-mcp-server/releases/tag/v1.2.0
[1.1.1]: https://github.com/schimmmi/fyta-mcp-server/releases/tag/v1.1.1
[1.1.0]: https://github.com/schimmmi/fyta-mcp-server/releases/tag/v1.1.0
[1.0.0]: https://github.com/schimmmi/fyta-mcp-server/releases/tag/v1.0.0
