# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[1.1.0]: https://github.com/schimmmi/fyta-mcp-server/releases/tag/v1.1.0
[1.0.0]: https://github.com/schimmmi/fyta-mcp-server/releases/tag/v1.0.0
