# FYTA MCP Server 🌱

A Model Context Protocol (MCP) Server for FYTA plant sensor data. Access your plant data directly through Claude!

## What is this?

FYTA is a smart plant sensor system that measures soil moisture, temperature, light, and nutrients. This MCP Server enables Claude to access this data and help you with plant care.

## Features

### Basic Plant Data
- 🌿 **Get all plants**: Complete overview of all your plants with sensor data
- 🔍 **Plant details**: Detailed information about individual plants
- 📊 **Plant measurements**: Historical sensor data and measurements over time
- ⚠️ **Plants needing attention**: Automatic detection of plants that need care
- 🏡 **Garden overview**: Organized view of your gardens and plants

### Advanced Analysis Tools
- 🔬 **Intelligent plant diagnosis**: Smart health analysis with threshold evaluation and sensor capability detection
- 📈 **Trend analysis**: Track changes in moisture, temperature, nutrients, and light over time
- 📊 **Statistical analysis**: Mean, min, max, stability scores, and anomaly detection
- ☀️ **DLI (Daily Light Integral) analysis**: Calculate daily light exposure and seasonal patterns
- 🌡️ **Smart threshold evaluation**: Fixes FYTA's inconsistent status codes using actual thresholds
- 💧 **Intelligent fertilization**: EC-based fertilization recommendations with trend prediction

### Context & Care Tracking
- 📝 **Plant context management**: Store substrate type, container type, and growth phase
- 🗓️ **Care action logging**: Track manual watering, fertilizing, and repotting
- 📖 **Care history analysis**: Analyze effectiveness of care actions
- 🔔 **Event detection**: Automatically detect significant changes in plant conditions

### Sensor Intelligence
- 🎯 **Sensor capability detection**: Automatically detects sensor types (Beam 2.0, Beam, Legacy)
- 💡 **Light sensor awareness**: Shows appropriate warnings when light data is unavailable
- 🔋 **Battery monitoring**: Track sensor battery status

## Installation

### Prerequisites

- Python 3.10 or higher (or Docker)
- A FYTA account with plants
- Claude Desktop App (or other MCP-compatible client)

### Setup with Docker (recommended)

1. **Install Docker and Docker Compose**

Make sure Docker is installed on your system.

2. **Clone repository**

```bash
cd ~/fyta-mcp-server
```

3. **Set environment variables**

Create a `.env` file:

```bash
cp .env.example .env
```

And enter your FYTA credentials:

```env
FYTA_EMAIL=your-email@example.com
FYTA_PASSWORD=your-password
```

4. **Build and start container**

```bash
docker-compose up -d
```

**Container commands:**

```bash
# Stop container
docker-compose down

# Show logs
docker-compose logs -f

# Rebuild container
docker-compose build

# Restart container
docker-compose restart
```

### Setup without Docker

1. **Clone repository or download files**

```bash
cd ~/fyta-mcp-server
```

2. **Create virtual environment (optional but recommended)**

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
pip install -e .
```

4. **Set environment variables**

Create a `.env` file:

```bash
cp .env.example .env
```

And enter your FYTA credentials:

```env
FYTA_EMAIL=your-email@example.com
FYTA_PASSWORD=your-password
```

**Important**: The `.env` file should NEVER be committed to Git!

## Configuration for Claude Desktop

Add the following to your Claude Desktop configuration:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### With Docker (recommended)

```json
{
  "mcpServers": {
    "fyta": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--env-file",
        "/absolute/path/to/fyta-mcp-server/.env",
        "fyta-mcp-server"
      ]
    }
  }
}
```

Or with docker-compose:

```json
{
  "mcpServers": {
    "fyta": {
      "command": "docker-compose",
      "args": [
        "-f",
        "/absolute/path/to/fyta-mcp-server/docker-compose.yml",
        "run",
        "--rm",
        "fyta-mcp-server"
      ]
    }
  }
}
```

### Without Docker (Python directly)

```json
{
  "mcpServers": {
    "fyta": {
      "command": "/absolute/path/to/fyta-mcp-server/.venv/bin/python",
      "args": [
        "-m",
        "fyta_mcp_server"
      ],
      "env": {
        "FYTA_EMAIL": "your-email@example.com",
        "FYTA_PASSWORD": "your-password"
      }
    }
  }
}
```

Or with uv:

```json
{
  "mcpServers": {
    "fyta": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/fyta-mcp-server",
        "run",
        "python",
        "-m",
        "fyta_mcp_server"
      ],
      "env": {
        "FYTA_EMAIL": "your-email@example.com",
        "FYTA_PASSWORD": "your-password"
      }
    }
  }
}
```

## Usage

After restarting Claude Desktop, the following tools are available:

### Basic Plant Data

#### Get all plants
```
Show me all my plants
```

#### Plant details
```
Show me details for plant with ID 123
```

#### Historical measurements
```
Show me measurements for plant 123 from the last week
```

#### Plants needing attention
```
Which of my plants need care right now?
```

#### Garden overview
```
Give me an overview of my gardens
```

### Advanced Analysis

#### Intelligent diagnosis
```
Diagnose plant 123 and give me detailed recommendations
```
Returns comprehensive health analysis including:
- Smart threshold evaluation (fixes FYTA's inconsistent status codes)
- Sensor capability detection (shows if light sensor is available)
- Intelligent fertilization recommendations based on EC trends
- Confidence scoring based on data quality

#### Trend analysis
```
Show me moisture and nutrient trends for plant 123 over the last month
```
Tracks changes over time with direction, percentage change, and predictions.

#### Statistical analysis
```
Give me statistics for all metrics of plant 123
```
Provides mean, min, max, standard deviation, stability scores, and anomaly detection.

#### DLI analysis
```
Calculate daily light integral for plant 123
```
Only works with sensors that have light sensors (FYTA Beam 2.0). Provides:
- Daily light exposure in mol/m²/day
- Optimal DLI recommendations per plant species
- Grow light recommendations
- Seasonal predictions

### Context Management

#### Set plant context
```
Set context for plant 123: organic soil in a terracotta pot, currently in vegetative growth
```
Store important information FYTA doesn't know:
- **Substrate**: mineral, organic, lechuza_pon, hydroponic, semi_hydro
- **Container**: lechuza, self_watering, terracotta, plastic, ceramic
- **Growth phase**: seedling, vegetative, flowering, fruiting, dormant

#### Get plant context
```
What context information do you have for plant 123?
```
Returns stored context with context-aware recommendations.

### Care Tracking

#### Log care action
```
Log that I watered plant 123 with 500ml today
```
Track manual care actions that FYTA doesn't know about:
- Watering (with amount)
- Fertilizing (with product and amount)
- Repotting (with substrate and pot size)
- Other custom actions

#### Get care history
```
Show me the care history for plant 123 from the last 30 days
```
View past care actions with effectiveness analysis.

### Event Detection

#### Get plant events
```
Show me recent events for plant 123
```
Automatically detects:
- Sudden moisture drops (watering needed)
- Temperature spikes (heat stress)
- Light changes (moved to new location)
- Nutrient depletion (fertilization needed)

## API Endpoints

The server uses the following FYTA API endpoints:

- `POST https://web.fyta.de/api/auth/login` - Authentication
- `GET https://web.fyta.de/api/user-plant` - Retrieve plant data
- `POST https://web.fyta.de/api/user-plant/measurements/[plantID]` - Retrieve historical measurements (with timeline: hour, day, week, month)

## Technical Details

### Status Values

The sensors return the following status values:

- **1** = Too low (Low)
- **2** = Optimal
- **3** = Too high (High)

This applies to:
- Temperature (`temperature_status`)
- Light (`light_status`)
- Soil moisture (`moisture_status`)
- Nutrients/Salinity (`salinity_status`)

**Note**: FYTA's status codes can be inconsistent. The `diagnose_plant` tool uses smart threshold evaluation to provide more accurate status assessments.

### Sensor Types

The server automatically detects which sensor type is connected:

| Type | Name | Light Sensor | Capabilities |
|------|------|--------------|--------------|
| 1 | FYTA (Legacy) | ❌ | Temperature, Moisture, Nutrients |
| 2 | FYTA Beam 2.0 | ✅ | Temperature, Moisture, Nutrients, Light |
| 3 | FYTA Beam | ❌ | Temperature, Moisture, Nutrients |

Tools like `get_plant_dli_analysis` will automatically warn you if your sensor doesn't support light measurements.

### Field Names

The FYTA API uses specific field names in measurement data:
- `soil_moisture` (not `moisture`)
- `soil_fertility` (not `salinity` or `nutrients`)
- `date_utc` (format: "YYYY-MM-DD HH:MM:SS")
- `temperature` and `light` (as expected)

### Intelligent Features

#### Smart Threshold Evaluation
FYTA's status codes sometimes contradict the actual threshold values. For example, a temperature of 19°C might be marked as "high" even though the optimal range is 5-25°C. The `diagnose_plant` tool fixes this by evaluating values against actual thresholds.

#### EC-Based Fertilization
FYTA's fertilization predictions are generic and time-based ("fertilize in 190 days"). This server provides EC (electrical conductivity) based recommendations:
- **EC status**: Critical low (<0.3), Low (0.3-0.6), Optimal (0.6-1.2), High (>1.2)
- **Substrate-specific thresholds**: Different optimal ranges for organic, mineral, PON, and hydroponic substrates
- **Trend prediction**: Linear regression to predict when EC reaches critical levels
- **Action timing**: Immediate, soon, or maintain based on current EC and trend

#### Winter Salinity Bug
FYTA sometimes sets winter thresholds to min=max=0 for salinity. The server detects this and uses summer thresholds instead.

## Troubleshooting

### Server won't start

1. Check if environment variables are set correctly
2. Test authentication:

```bash
cd /path/to/fyta-mcp-server
source .venv/bin/activate
python tests/test_connection.py
```

### No data available

- Make sure you're using a FYTA Hub or the mobile app as a gateway
- FYTA Beam sensors only send raw data that needs to be processed by the server
- Check in the FYTA app if your sensors are connected

## Development

### Project Structure

```
fyta-mcp-server/
├── src/fyta_mcp_server/
│   ├── __init__.py
│   ├── server.py          # MCP server setup
│   ├── client.py          # FYTA API client
│   ├── tools.py           # Tool definitions
│   ├── handlers.py        # Tool handler implementations
│   └── utils/
│       ├── care_actions.py     # Care tracking and analysis
│       ├── dli.py              # Daily Light Integral calculations
│       ├── events.py           # Event detection
│       ├── fertilization.py    # EC-based fertilization logic
│       ├── plant_context.py    # Context storage and recommendations
│       ├── sensor_info.py      # Sensor capability detection
│       ├── statistics.py       # Statistical analysis
│       ├── thresholds.py       # Smart threshold evaluation
│       └── trends.py           # Trend analysis and predictions
```

### Adding New Tools

To add a new tool:

1. **Define the tool** in `src/fyta_mcp_server/tools.py`:
```python
Tool(
    name="my_new_tool",
    description="What this tool does",
    inputSchema={
        "type": "object",
        "properties": {
            "plant_id": {"type": "number"}
        },
        "required": ["plant_id"]
    }
)
```

2. **Implement the handler** in `src/fyta_mcp_server/handlers.py`:
```python
async def handle_my_new_tool(fyta_client: FytaClient, arguments: Any):
    plant_id = int(arguments["plant_id"])
    # Your logic here
    return [TextContent(type="text", text=result)]
```

3. **Register the handler** in `src/fyta_mcp_server/server.py`:
```python
elif name == "my_new_tool":
    return await handle_my_new_tool(fyta_client, arguments)
```

### Creating Utility Modules

For complex functionality, create a new module in `utils/`:

```python
# src/fyta_mcp_server/utils/my_feature.py
def analyze_something(data: List[Dict]) -> Dict:
    """Analyze data and return insights"""
    # Your analysis logic
    return {"result": "insights"}
```

Then import and use it in handlers.py:
```python
from .utils.my_feature import analyze_something
```

### API Documentation

The complete FYTA API documentation:
https://fyta-io.notion.site/FYTA-Public-API-d2f4c30306f74504924c9a40402a3afd

### Testing

Run the test connection script:
```bash
python tests/test_connection.py
```

### Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Credits

- FYTA API: https://fyta.de/
- Based on Python client: https://github.com/dontinelli/fyta_cli
- Home Assistant Integration: https://github.com/dontinelli/fyta-custom_component

## License

MIT License - see [LICENSE](LICENSE) file for details

## Support

For questions or issues:
- Open an issue on GitHub: https://github.com/schimmmi/fyta-mcp-server/issues
- Check out the FYTA Developer Community on Discord
- Visit https://fyta.de/ for more info about the sensors

## Repository

GitHub: https://github.com/schimmmi/fyta-mcp-server

---

Happy plant monitoring with Claude! 🌿🤖
