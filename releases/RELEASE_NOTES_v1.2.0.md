# FYTA MCP Server v1.2.0 🌟

**Major feature release** - Advanced plant intelligence with smart diagnosis, EC-based fertilization, and comprehensive analysis tools.

## 🎯 Highlights

This release transforms the FYTA MCP Server into an intelligent plant care assistant with advanced analysis capabilities that go far beyond what the FYTA app provides.

### 🔬 Intelligent Plant Diagnosis

The new `diagnose_plant` tool provides comprehensive health analysis with:

- **Smart Threshold Evaluation**: Fixes FYTA's inconsistent status codes by evaluating values against actual thresholds
  - Example: Temperature 19°C correctly shown as "optimal" (not "high")
- **Sensor Capability Detection**: Automatically detects sensor types and shows appropriate warnings
  - FYTA Beam 2.0 (with light sensor)
  - FYTA Beam (without light sensor)
  - FYTA Legacy (without light sensor)
- **Confidence Scoring**: Evaluates data quality and recency for reliable recommendations

### 💧 EC-Based Fertilization

Intelligent fertilization recommendations based on electrical conductivity trends:

- **Current EC Status**: Critical low, Low, Optimal, High
- **Substrate-Specific Thresholds**: Different optimal ranges for:
  - Organic soil (0.8-1.2)
  - Mineral soil (0.6-1.0)
  - Lechuza PON (0.5-0.9)
  - Hydroponic (0.4-0.8)
- **Trend Prediction**: Uses linear regression to predict when EC reaches critical levels
- **Action Timing**: Immediate, soon, or maintain based on current EC and trend

**Much smarter than FYTA's generic "fertilize in 190 days" prediction!**

### 📊 Advanced Analysis Tools

Four new analysis tools provide deep insights:

1. **Trend Analysis** (`get_plant_trends`)
   - Track changes in moisture, temperature, nutrients, light
   - Direction and percentage change
   - Critical time predictions for moisture

2. **Statistical Analysis** (`get_plant_statistics`)
   - Mean, min, max, standard deviation
   - Stability scores (0-100)
   - Anomaly detection

3. **DLI Analysis** (`get_plant_dli_analysis`)
   - Daily Light Integral calculations (mol/m²/day)
   - Optimal DLI recommendations per plant species
   - Grow light recommendations
   - Seasonal predictions

4. **Event Detection** (`get_plant_events`)
   - Sudden moisture drops (watering needed)
   - Temperature spikes (heat stress)
   - Light changes (moved to new location)
   - Nutrient depletion (fertilization needed)

### 📝 Context & Care Tracking

Store information FYTA doesn't know about:

- **Plant Context** (`set_plant_context`, `get_plant_context`)
  - Substrate type (organic, mineral, PON, hydroponic)
  - Container type (terracotta, plastic, Lechuza, self-watering)
  - Growth phase (seedling, vegetative, flowering, fruiting, dormant)
  - Get context-aware recommendations

- **Care Action Tracking** (`log_plant_care_action`, `get_plant_care_history`)
  - Track manual watering (with amount)
  - Track fertilizing (with product and amount)
  - Track repotting (with substrate and pot size)
  - Analyze effectiveness of care actions over time

## 🐛 Critical Fixes

### Field Name Mappings
FYTA API uses different field names than expected:
- Fixed: `moisture` → `soil_moisture`
- Fixed: `salinity` → `soil_fertility`
- Fixed: `measured_at` → `date_utc`

**This affected all analysis tools and caused "no_data" errors despite measurements existing.**

### Timestamp Parsing
- Fixed parsing for FYTA's "YYYY-MM-DD HH:MM:SS" format (without "T" or timezone)

### Sensor Detection
- Fixed sensor type 3 = FYTA Beam (without light sensor, not Beam 2.0)

### Error Handling
- Fixed NoneType errors in smart status evaluation
- Added safe dictionary access throughout
- Fixed severity sorting (added "info" severity level)
- Fixed EC value extraction from measurements

## 📦 All Available Tools (14 total)

### Basic Plant Data (5 tools)
- `get_all_plants` - Overview of all plants
- `get_plant_details` - Detailed info for specific plant
- `get_plant_measurements` - Historical sensor data
- `get_plants_needing_attention` - Plants requiring care
- `get_garden_overview` - Overview of gardens

### Advanced Analysis (4 tools)
- `diagnose_plant` - **NEW** - Comprehensive health analysis
- `get_plant_trends` - **NEW** - Trend analysis with predictions
- `get_plant_statistics` - **NEW** - Statistical analysis
- `get_plant_dli_analysis` - **NEW** - Daily light integral

### Context & Care (5 tools)
- `set_plant_context` - **NEW** - Store substrate, container, growth phase
- `get_plant_context` - **NEW** - Get context-aware recommendations
- `log_plant_care_action` - **NEW** - Track manual care
- `get_plant_care_history` - **NEW** - View care history
- `get_plant_events` - **NEW** - Detect significant changes

## 🔧 Technical Details

### New Utility Modules

Nine new utility modules provide advanced functionality:

```
src/fyta_mcp_server/utils/
├── care_actions.py      # Care tracking and analysis (300 lines)
├── dli.py              # Daily Light Integral calculations (350 lines)
├── events.py           # Event detection system (250 lines)
├── fertilization.py    # EC-based fertilization logic (370 lines)
├── plant_context.py    # Context storage and recommendations (350 lines)
├── sensor_info.py      # Sensor capability detection (240 lines)
├── statistics.py       # Statistical analysis (400 lines)
├── thresholds.py       # Smart threshold evaluation (240 lines)
└── trends.py           # Trend analysis with linear regression (300 lines)
```

**Total: ~2,800 lines of new analysis code**

### Workarounds for FYTA API Issues

1. **Winter Salinity Bug**: FYTA sets winter thresholds to min=max=0 for salinity. We detect this and use summer thresholds instead.

2. **Inconsistent Status Codes**: FYTA's status codes contradict actual thresholds. We evaluate values against actual thresholds for accurate status.

3. **Generic Fertilization**: FYTA's "fertilize in 190 days" prediction is generic. We analyze actual EC trends for smart recommendations.

### Smart Features

- **Substrate-Aware Thresholds**: Different optimal EC ranges per substrate type
- **R² Confidence Scoring**: Linear regression confidence for trend predictions
- **Sensor Capability Checks**: Automatic detection prevents errors when light sensor unavailable
- **Data Quality Assessment**: Confidence scoring based on data recency and completeness

## 📚 Usage Examples

### Intelligent Diagnosis
```
Diagnose plant 108009 and give me detailed recommendations
```

Returns comprehensive analysis including:
- Current health status with confidence score
- Smart threshold evaluation (fixes FYTA's bugs)
- Sensor information and capabilities
- EC-based fertilization recommendations
- Actionable recommendations

### Trend Analysis
```
Show me moisture and nutrient trends for plant 108009 over the last month
```

Returns:
- Direction (increasing, decreasing, stable)
- Percentage change
- Prediction when moisture reaches critical (if decreasing)

### Context Management
```
Set context for plant 108009: organic soil in a terracotta pot, currently in vegetative growth
```

Then get context-aware recommendations:
```
What context information do you have for plant 108009?
```

### Care Tracking
```
Log that I watered plant 108009 with 500ml today
```

Then analyze effectiveness:
```
Show me the care history for plant 108009 from the last 30 days
```

## 📝 Installation

### Update from v1.1.1

```bash
cd /path/to/fyta-mcp-server
git pull
git checkout v1.2.0
pip install -e .  # If not using Docker
```

### Docker

```bash
cd /path/to/fyta-mcp-server
git pull
git checkout v1.2.0
docker-compose build
docker-compose up -d
```

### Verify Installation

Test the new diagnosis tool:
```
Diagnose plant [YOUR_PLANT_ID]
```

## 🔗 Links

- [Full CHANGELOG](https://github.com/schimmmi/fyta-mcp-server/blob/main/CHANGELOG.md)
- [Documentation](https://github.com/schimmmi/fyta-mcp-server/blob/main/README.md)
- [Report Issues](https://github.com/schimmmi/fyta-mcp-server/issues)

## 🙏 Credits

This release was developed with assistance from [Claude Code](https://claude.com/claude-code).

---

**Full Changelog**: https://github.com/schimmmi/fyta-mcp-server/compare/v1.1.1...v1.2.0
