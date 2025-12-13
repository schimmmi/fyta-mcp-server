# FYTA MCP Server v1.0.0 🌱

First stable release with complete project restructuring and professional architecture.

## 🎯 Features

### MCP Tools
- **get_all_plants** - Get all plants with their current sensor data
- **get_plant_details** - Get detailed information about a specific plant
- **get_plants_needing_attention** - Find plants that need care
- **get_garden_overview** - Get overview of all gardens with plant counts

### Architecture
- ✅ Modular Python package structure (`src/fyta_mcp_server/`)
- ✅ Separated components: client, tools, handlers, server
- ✅ Professional package layout following best practices
- ✅ Editable installation support

### Docker Support 🐳
- Dockerfile with Python 3.11-slim base image
- docker-compose.yml for easy deployment
- Optimized .dockerignore for smaller images

### Documentation 📚
- Comprehensive README with setup instructions
- QUICKSTART guide for fast setup
- OVERVIEW with project architecture
- Configuration examples for Claude Desktop

### Testing
- Connection test script
- Test suite structure
- Integration with FYTA API

## 📦 Installation

### With Docker (Recommended)
```bash
docker-compose up -d
```

### Without Docker
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## 🔧 Claude Desktop Configuration

```json
{
  "mcpServers": {
    "fyta": {
      "command": "/path/to/.venv/bin/python",
      "args": ["-m", "fyta_mcp_server"],
      "env": {
        "FYTA_EMAIL": "your-email@example.com",
        "FYTA_PASSWORD": "your-password"
      }
    }
  }
}
```

## 📋 Requirements

- Python 3.10+ (or Docker)
- FYTA account with plants
- Claude Desktop App (or other MCP-compatible client)

## 🔗 Links

- [Full CHANGELOG](https://github.com/schimmmi/fyta-mcp-server/blob/main/CHANGELOG.md)
- [Documentation](https://github.com/schimmmi/fyta-mcp-server/tree/main/docs)
- [Report Issues](https://github.com/schimmmi/fyta-mcp-server/issues)

## 🛠️ Technical Details

- **Python Version**: 3.10+
- **Dependencies**: httpx, mcp, python-dotenv
- **FYTA API**: web.fyta.de
- **MCP Protocol**: 2025-06-18
- **Docker Base**: Python 3.11-slim

## 📝 Project Structure

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

---

**Full Changelog**: https://github.com/schimmmi/fyta-mcp-server/compare/409fad0...v1.0.0
