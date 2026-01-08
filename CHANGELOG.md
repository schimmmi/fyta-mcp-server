# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-01-08

### Added
- **Hub Status Monitoring** 🔌
  - New MCP tool: `get_all_hubs` - List all FYTA Hubs with status, firmware version, and connected plants
  - New MCP tool: `get_hub_details` - Get detailed information about a specific hub
  - New MCP tool: `get_fyta_raw_data` - Access complete unfiltered FYTA API response
  - Hub status includes: online/offline status, firmware version, last seen timestamps, connectivity health
  - Supports `hubs_with_lost_connection` API field for connection alerts

### Fixed
- **EC=0 False Positive Anomaly Detection** 🌱
  - FYTA API flags `soil_fertility_anomaly: true` even when EC=0 is normal (winter dormancy)
  - Now intelligently distinguishes:
    - EC=0 + Winter thresholds (min=0, max=0) → **Normal** (no nutrients needed, ignore anomaly flag)
    - EC=0 + Summer thresholds (min>0) → **Sensor error** (unusual, likely malfunction)
    - EC≠0 + Anomaly flag → **Sensor error** (actual hardware issue)
  - Prevents false "Sensor-Anomalie" warnings during winter when plants don't need nutrients

### Technical Details
- Hub data extracted from plant objects (each plant has associated hub info)
- Smart anomaly detection in `utils/thresholds.py:250-267`
- Handler implementations in `handlers.py:1997-2110`
- Tool definitions in `tools.py:410-471`

## [1.2.6] - 2026-01-04

### Fixed
- **Critical Bug: soil_fertility=0 treated as None**
  - Python's `0 or None` evaluates to `None` (0 is falsy)
  - Sensors reporting EC=0 had `nutrients=None` instead of `nutrients=0`
  - Affected plants with low/zero EC readings (winter dormancy, sensor issues)
  - Fixed in 6 locations using explicit `is not None` checks
  - Now correctly processes EC=0 values

- **Sensor anomaly detection for nutrients**
  - FYTA API provides `soil_fertility_anomaly` and `soil_moisture_anomaly` flags
  - These flags indicate sensor malfunction or poor soil contact
  - Now transfers anomaly flags from measurements to plant data
  - `evaluate_plant_status()` sets status=4 ("sensor_error") when anomaly detected
  - `diagnose_plant` shows clear "Nutrient sensor reports anomaly" warning

- **Smart evaluation was ignored in diagnose_plant**
  - Bug: `smart_status.get("use_fyta_status", True)` defaulted to True
  - Result: FYTA's buggy status codes used instead of smart evaluation
  - Fixed: Changed default to `False` - now uses smart evaluation when thresholds exist
  - Smart evaluation now properly detects sensor errors and anomalies

- **KeyError for optimal_hours in sensor error case**
  - Sensor error issues missing `optimal_hours` field caused crash
  - Added `optimal_hours: None` to sensor_error case
  - Changed access from `issue["optimal_hours"]` to safe `issue.get("optimal_hours")`

### Added
- Sensor anomaly flags now transferred from measurements:
  - `soil_fertility_anomaly` (EC sensor malfunction/poor contact)
  - `soil_moisture_anomaly` (moisture sensor issues)
- Enhanced logging shows anomaly flags in measurement extraction
- Status code 4 ("sensor_error") for unreliable sensor readings
- Clear explanations: "Check sensor placement and clean electrodes"

### Changed
- All 6 measurement extraction locations now handle EC=0 correctly
- Sensor error treated as high severity issue
- `get_status_description()` supports "sensor_error" status_name

### Technical Details
- Fixed locations: lines 115, 226, 314, 978, 1346, 1594 in handlers.py
- Pattern changed from:
  ```python
  nutrients = latest.get("soil_fertility") or latest.get("salinity")
  ```
  To:
  ```python
  nutrients = latest.get("soil_fertility") if latest.get("soil_fertility") is not None else latest.get("salinity")
  ```
- Added anomaly detection in `thresholds.py:evaluate_plant_status()`
- Enhanced `diagnose_plant` to show sensor errors as actionable issues

## [1.2.5] - 2025-12-30

### Fixed
- **Critical Bug: Incorrect measurement values in diagnose_plant**
  - FYTA API returns measurements in **arbitrary order, not chronological**
  - Old code used `measurements_list[-1]` which gave outdated values
  - Example: Showed 19°C/34% moisture instead of actual 28°C/67%
  - Fixed by sorting measurements by timestamp before extracting latest value
  - Added `get_latest_measurement()` helper function used across all handlers
  - Affects: `diagnose_plant`, `get_plants_needing_attention`, `get_plant_events`, watering/fertilization analysis

- **Stale values from Plant object**
  - Plant object from FYTA API contains outdated/unreliable measurement values
  - Now using **only** measurements endpoint for actual values
  - Created clean enriched_plant_data dict without copying stale values
  - Plant object now only used for metadata and status codes

- **Dynamic severity calculation**
  - Old: Temperature 1°C over threshold = "critical" ❌
  - New: Severity based on actual deviation percentage ✅
  - 26°C at 25°C threshold: +4% = "low" (was "critical")
  - 28°C at 25°C threshold: +12% = "moderate" (was "critical")
  - 35°C at 25°C threshold: +40% = "high"
  - Added `calculate_severity()` function with metric-specific logic
  - Moisture low is treated most critical (dehydration risk)
  - Temperature/nutrients have more nuanced severity levels

### Changed
- Health assessment now much more realistic
  - Example: Plant at 26-28°C now rated "good"/"fair" instead of "critical"
  - Severity reflects actual risk to plant health, not arbitrary thresholds
  - "critical" reserved for true emergencies (e.g., moisture <15%)

### Technical Details
- New helper function: `get_latest_measurement(measurements_list)`
  - Sorts by timestamp (date_utc, timestamp, or measured_at)
  - Returns measurement with newest timestamp
  - Used in all 6 locations that extract latest measurement
- New helper function: `calculate_severity(value, status_code, thresholds, metric_name)`
  - Calculates deviation percentage from optimal range
  - Metric-specific severity rules (moisture, temperature, nutrients)
  - Returns: "info", "low", "moderate", "high", or "critical"
- Enhanced logging in diagnose_plant:
  - Shows measurement count, keys, and extracted values
  - Logs timestamp of latest measurement used
  - Helps debug measurement data issues

## [1.2.4] - 2025-12-24

### Added
- **Intelligent Watering Prediction**: New moisture trend analysis with predictive watering recommendations
  - Analyzes 7-day moisture trends with linear regression
  - Predicts "water in X days" based on consumption rate
  - Shows moisture consumption (% per day/week)
  - Integrated into `diagnose_plant` with full recommendations
- Winter-aware fertilization thresholds (November-February)
  - EC 0.08-0.8 considered optimal during dormancy
  - Prevents false "critical low" alerts in winter
  - More realistic recommendations for dormant plants
- Status 4 (Critical) support in status_map for get_plant_details
- Comprehensive debug logging for all metric evaluations

### Fixed
- **Complete Smart Evaluation Migration**: All tools now use smart evaluation instead of buggy FYTA status codes
  - `get_plant_details`: Now enriches data and uses smart evaluation
  - `get_all_plants`: Now enriches data and uses smart evaluation for all plants
  - `diagnose_plant`: Added measurement enrichment before evaluation
- Light evaluation: Fixed Light=0 handling (not critical, adjust min_acceptable=0)
- Moisture trend analysis: Fixed field name handling (date_utc, soil_moisture variants)
- Fertilization: Fixed winter threshold logic (critical_low: 0.05, min_optimal: 0.08)

### Technical Details
- Created `src/fyta_mcp_server/utils/watering.py`:
  - `get_moisture_status()`: Evaluate current moisture with substrate-specific thresholds
  - `analyze_moisture_trend()`: 7-day trend analysis with linear regression and prediction
  - `get_watering_recommendation()`: Comprehensive watering advice
- Enhanced `utils/thresholds.py`:
  - Light evaluation with adjusted min_acceptable to prevent false critical alerts
  - Added threshold info to all evaluation results
  - Comprehensive debug logging for temperature, light, moisture, nutrients
- Updated `utils/fertilization.py`:
  - Season-aware thresholds with `consider_season` parameter
  - Winter dormancy detection (months 11, 12, 1, 2)
  - Adjusted thresholds: critical_low=0.05, min_optimal=0.08, max_optimal=0.8
- Updated `handlers.py`:
  - Watering analysis integration in diagnose_plant (lines 1151-1198)
  - All tools now extract status codes correctly from evaluation result dicts
  - Fixed status_map to include Status 4 (Critical)

## [1.2.3] - 2025-12-24

### Fixed
- **Critical**: Fixed `get_plants_needing_attention` using buggy FYTA status codes instead of smart evaluation
  - Same issue as v1.2.1 but for different tool - was still using direct FYTA status codes
  - Now enriches plant data with actual measurements before smart evaluation
  - Correctly extracts status codes from smart evaluation result dictionaries
  - Added comprehensive debug logging for temperature, moisture, and nutrients evaluation
  - Fixes false alerts (e.g., "temperature too high" when actually optimal)

### Added
- Debug logging for moisture and nutrients threshold evaluation
- Threshold information in smart evaluation results for better debugging

### Technical Details
- Updated `handle_get_plants_needing_attention` to use same data enrichment pattern as `handle_get_plant_events`
- Fixed status code extraction: `smart_status["temperature"]` returns dict with `{"status": code, ...}` not integer
- Added `thresholds` field to moisture and nutrients evaluation results
- Enhanced logging shows actual values, thresholds, and evaluation results for all metrics

## [1.2.2] - 2025-12-23

### Added
- **Docker Support for API Wrappers**: Complete Docker deployment with docker-compose
  - Dockerfile for all API wrapper variants (basic, webhooks, MQTT)
  - docker-compose.yml with profiles for different deployment scenarios
  - Mosquitto MQTT broker integration
  - Automated cron containers for scheduled webhook/MQTT pushes
  - Health checks and auto-restart policies
- **Comprehensive Integration Examples**: Ready-to-use code for automation platforms
  - n8n: Workflow JSON, configuration examples
  - Home Assistant: configuration.yaml, automations.yaml, Lovelace dashboard
  - IP-Symcon: PHP scripts for data fetching, reminders, WebFront visualization
- **Integration Documentation**: Complete guides for automation platforms
  - `docs/INTEGRATIONS.md`: Detailed integration guide for n8n, Home Assistant, IP-Symcon
  - `examples/DOCKER.md`: Complete Docker deployment guide
  - Platform-specific READMEs with setup instructions and troubleshooting

### Changed
- Improved documentation structure with practical examples
- Added webhook format documentation for automation systems
- Enhanced API wrapper with production-ready Gunicorn configuration

### Technical Details
- Docker Compose services: fyta-api (5000), fyta-api-webhooks (5001), fyta-api-mqtt (5002)
- Mosquitto MQTT broker on ports 1883 (MQTT) and 9001 (WebSocket)
- Gunicorn with 4 workers and 120s timeout
- Bridge network for service communication
- Profile-based deployment: default, webhooks, mqtt

## [1.2.1] - 2025-12-23

### Fixed
- **Critical**: Fixed `get_plant_events` using buggy FYTA status codes instead of smart evaluation
  - Plant objects from `/user-plant` endpoint don't contain actual sensor values (only status codes)
  - Now enriches plant data with actual values from measurements before evaluation
  - Smart threshold evaluation now works correctly for event detection
  - Fixes false "temperature extreme" alerts when temperature is actually optimal

### Technical Details
- Added measurement value enrichment to `handle_get_plant_events`
- Plant object is now populated with `temperature`, `light`, `soil_moisture`, `soil_fertility` from latest measurement
- Smart evaluation receives complete data and can correctly assess status
- Added debug logging for threshold evaluation

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

[1.2.2]: https://github.com/schimmmi/fyta-mcp-server/releases/tag/v1.2.2
[1.2.1]: https://github.com/schimmmi/fyta-mcp-server/releases/tag/v1.2.1
[1.2.0]: https://github.com/schimmmi/fyta-mcp-server/releases/tag/v1.2.0
[1.1.1]: https://github.com/schimmmi/fyta-mcp-server/releases/tag/v1.1.1
[1.1.0]: https://github.com/schimmmi/fyta-mcp-server/releases/tag/v1.1.0
[1.0.0]: https://github.com/schimmmi/fyta-mcp-server/releases/tag/v1.0.0
