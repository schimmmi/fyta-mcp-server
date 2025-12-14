# FYTA MCP Server v1.1.1 🔧

**Critical bugfix release** - Fixes measurements endpoint that did not work in v1.1.0.

## 🚨 Critical Fix

### Measurements Endpoint Corrected
- **Fixed 422 error** when retrieving plant measurements
- Changed from `GET` to `POST` method (as required by FYTA API)
- Added required request body with timeline parameter

**If you installed v1.1.0, please update to v1.1.1 immediately.**

## 🎯 What's Fixed

### API Method Correction
The measurements endpoint now correctly uses:
```
POST /user-plant/measurements/[plantID]
Body: { "search": { "timeline": "month" } }
```

Previously incorrectly attempted:
```
GET /user-plant/measurements/[plantID]  ❌
```

### Timeline Parameter
- Added optional `timeline` parameter to tool
- Accepted values: "hour", "day", "week", "month"
- Default: "month"

## 📦 Installation

Update to v1.1.1:

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

## 🔧 Usage

```
Show me measurements for plant 123 from the last week
```

The tool will now work correctly and can optionally specify the timeline.

## 📝 Changes

- `client.py`: Changed to POST with JSON body
- `tools.py`: Added timeline parameter with enum validation
- `handlers.py`: Pass timeline parameter to client
- `README.md`: Updated API endpoint documentation
- `CHANGELOG.md`: Added v1.1.1 entry

## 🔗 Links

- [Full CHANGELOG](https://github.com/schimmmi/fyta-mcp-server/blob/main/CHANGELOG.md)
- [Report Issues](https://github.com/schimmmi/fyta-mcp-server/issues)

---

**Full Changelog**: https://github.com/schimmmi/fyta-mcp-server/compare/v1.1.0...v1.1.1
