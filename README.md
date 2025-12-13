# FYTA MCP Server 🌱

A Model Context Protocol (MCP) Server for FYTA plant sensor data. Access your plant data directly through Claude!

## What is this?

FYTA is a smart plant sensor system that measures soil moisture, temperature, light, and nutrients. This MCP Server enables Claude to access this data and help you with plant care.

## Features

- 🌿 **Get all plants**: Complete overview of all your plants with sensor data
- 🔍 **Plant details**: Detailed information about individual plants
- ⚠️ **Plants needing attention**: Automatic detection of plants that need care
- 🏡 **Garden overview**: Organized view of your gardens and plants

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

### 1. Get all plants

```
Show me all my plants
```

### 2. Details for a specific plant

```
Show me details for plant with ID 123
```

### 3. Plants needing attention

```
Which of my plants need care right now?
```

### 4. Garden overview

```
Give me an overview of my gardens
```

## API Endpoints

The server uses the following FYTA API endpoints:

- `POST https://web.fyta.de/api/auth/login` - Authentication
- `GET https://web.fyta.de/api/user-plant` - Retrieve plant data

## Status Values

The sensors return the following status values:

- **1** = Too low (Low)
- **2** = Optimal
- **3** = Too high (High)

This applies to:
- Temperature (`temperature_status`)
- Light (`light_status`)
- Soil moisture (`moisture_status`)
- Nutrients/Salinity (`salinity_status`)

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

### Adding more endpoints

You can add more tools by:

1. Defining a new tool in `src/fyta_mcp_server/tools.py`
2. Implementing the handler in `src/fyta_mcp_server/handlers.py`

### API Documentation

The complete FYTA API documentation can be found here:
https://fyta-io.notion.site/FYTA-Public-API-d2f4c30306f74504924c9a40402a3afd

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
