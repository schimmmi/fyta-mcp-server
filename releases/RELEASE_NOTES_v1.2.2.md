# FYTA MCP Server v1.2.2 🐳📚

**Documentation & Docker Integration Release** - Complete integration examples and Docker deployment support for automation platforms.

## 🎯 Highlights

This release adds comprehensive integration support for popular automation platforms with ready-to-use examples and Docker deployment options.

### 🐳 Docker Support

Deploy API wrappers easily with Docker and docker-compose:

```bash
cd examples

# Basic API wrapper
docker-compose up -d fyta-api

# With webhooks
docker-compose --profile webhooks up -d

# With MQTT
docker-compose --profile mqtt up -d
```

**Features:**
- ✅ Multi-variant Dockerfile (basic, webhooks, MQTT)
- ✅ docker-compose.yml with profiles
- ✅ Integrated Mosquitto MQTT broker
- ✅ Automated cron containers for scheduled pushes
- ✅ Health checks and auto-restart
- ✅ Production-ready with Gunicorn

### 📚 Integration Examples

Ready-to-use code for three major platforms:

#### n8n (Workflow Automation)
- Importable workflow JSON
- HTTP Request configurations
- Notification examples (Telegram, Discord, Email)
- Database logging examples

#### Home Assistant
- Complete `configuration.yaml` with REST sensors
- 6 pre-configured automations:
  - Critical plant alerts
  - Watering reminders
  - Daily status reports
  - Temperature control with AC
  - Automatic watering (smart valve)
  - Low battery alerts
- Lovelace dashboard cards
- MQTT integration support

#### IP-Symcon (German home automation)
- `FYTA_UpdateData.php` - Main data fetching script
- `FYTA_WaterReminder.php` - Watering automation
- `FYTA_WebFront.php` - Visual dashboard
- Event scripts for auto-updates
- WebFront/Email notification examples

### 📖 Complete Documentation

New documentation files:

1. **`docs/INTEGRATIONS.md`** (1000+ lines)
   - Detailed integration guides for all platforms
   - Step-by-step setup instructions
   - Configuration examples
   - Best practices
   - Troubleshooting sections

2. **`examples/DOCKER.md`** (500+ lines)
   - Complete Docker deployment guide
   - Service configuration
   - Monitoring and logging
   - Production deployment
   - Security best practices

3. **Platform-specific READMEs**
   - n8n setup and customization
   - Home Assistant integration details
   - IP-Symcon script installation

## 📦 What's Included

### Docker Files

```
examples/
├── Dockerfile                 # Multi-variant API wrapper image
├── docker-compose.yml         # Orchestration with profiles
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
└── mosquitto.conf            # MQTT broker config
```

**Services:**
- `fyta-api` (port 5000) - Basic REST API
- `fyta-api-webhooks` (port 5001) - With webhook push
- `fyta-api-mqtt` (port 5002) - With MQTT publishing
- `mosquitto` (1883, 9001) - MQTT broker
- `fyta-cron` - Webhook scheduler (every 5 min)
- `fyta-mqtt-cron` - MQTT scheduler (every 5 min)

### Integration Examples

```
examples/
├── n8n/
│   ├── workflow_basic_monitoring.json
│   └── README.md
├── homeassistant/
│   ├── configuration.yaml
│   ├── automations.yaml
│   ├── lovelace_dashboard.yaml
│   └── README.md
└── ip-symcon/
    ├── FYTA_UpdateData.php
    ├── FYTA_WaterReminder.php
    ├── FYTA_WebFront.php
    └── README.md
```

## 🚀 Quick Start

### Docker Deployment

```bash
# Clone repository
git clone https://github.com/schimmmi/fyta-mcp-server.git
cd fyta-mcp-server/examples

# Setup environment
cp .env.example .env
# Edit .env with your FYTA credentials

# Start API wrapper
docker-compose up -d fyta-api

# Verify
curl http://localhost:5000/health
curl http://localhost:5000/api/events
```

### n8n Integration

```bash
# Start API wrapper (Docker or Python)
docker-compose up -d fyta-api

# Import workflow to n8n
# Open n8n → Import → Select examples/n8n/workflow_basic_monitoring.json

# Configure Telegram/Email credentials
# Activate workflow
```

### Home Assistant Integration

```bash
# Start API wrapper
docker-compose up -d fyta-api

# Add to Home Assistant configuration.yaml
# Copy from examples/homeassistant/configuration.yaml

# Add automations
# Copy from examples/homeassistant/automations.yaml

# Restart Home Assistant
ha core restart
```

### IP-Symcon Integration

```bash
# Start API wrapper
docker-compose up -d fyta-api

# Import scripts to IP-Symcon Console
# Copy from examples/ip-symcon/*.php

# Create cyclic event (every 5 minutes)
# Run FYTA_UpdateData script
```

## 🎯 Use Cases

All examples include implementations for:

### 1. Automatic Watering System
Monitor moisture and trigger smart valves automatically.

**Platforms:** n8n, Home Assistant, IP-Symcon

### 2. Critical Plant Alerts
High-priority notifications for urgent plant issues.

**Platforms:** n8n (Telegram/Discord), Home Assistant (mobile app), IP-Symcon (WebFront/Email)

### 3. Daily Status Reports
Morning summary of all plants' health.

**Platforms:** All three

### 4. Temperature Control
Adjust AC/thermostat when plants get too hot.

**Platforms:** Home Assistant, IP-Symcon

### 5. Dashboard Visualization
Real-time plant health monitoring.

**Platforms:** n8n (Grafana), Home Assistant (Lovelace), IP-Symcon (WebFront)

## 🔧 Technical Improvements

### Docker

- **Gunicorn** instead of Flask dev server
- **4 workers** for production performance
- **120s timeout** for long-running requests
- **Health checks** every 30 seconds
- **Auto-restart** on failure
- **Bridge network** for service communication

### API Wrappers

Enhanced with production features:
- Proper error handling
- Logging configuration
- Environment variable support
- Health check endpoints

### Documentation

- Step-by-step guides
- Configuration examples
- Troubleshooting sections
- Best practices
- Security recommendations

## 📊 Docker Architecture

```
┌─────────────────────────────────────────────────┐
│ Docker Compose Network: fyta-network           │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────┐  ┌──────────────┐            │
│  │  fyta-api    │  │ fyta-api-    │            │
│  │  :5000       │  │ webhooks     │            │
│  │              │  │ :5001        │            │
│  └──────────────┘  └──────────────┘            │
│                                                 │
│  ┌──────────────┐  ┌──────────────┐            │
│  │ fyta-api-    │  │ mosquitto    │            │
│  │ mqtt         │  │ :1883, :9001 │            │
│  │ :5002        │  │              │            │
│  └──────────────┘  └──────────────┘            │
│                                                 │
│  ┌──────────────┐  ┌──────────────┐            │
│  │ fyta-cron    │  │ fyta-mqtt-   │            │
│  │ (scheduler)  │  │ cron         │            │
│  │              │  │ (scheduler)  │            │
│  └──────────────┘  └──────────────┘            │
│                                                 │
└─────────────────────────────────────────────────┘
```

## 🔒 Security Notes

### Development

- `.env` file for credentials (gitignored)
- MQTT allows anonymous connections
- No HTTPS by default

### Production

Documentation includes:
- HTTPS setup with reverse proxy
- MQTT authentication configuration
- API authentication examples
- Resource limits
- Firewall rules

## 📝 Installation

### Update from Previous Version

```bash
cd /path/to/fyta-mcp-server
git pull
git checkout v1.2.2

# No code changes, just new examples and docs
# Existing functionality unchanged
```

### New Installation

```bash
git clone https://github.com/schimmmi/fyta-mcp-server.git
cd fyta-mcp-server/examples
cp .env.example .env
# Edit .env with credentials
docker-compose up -d fyta-api
```

## 📚 Documentation Links

- [Integration Guide](https://github.com/schimmmi/fyta-mcp-server/blob/main/docs/INTEGRATIONS.md) - Complete guide for all platforms
- [Docker Guide](https://github.com/schimmmi/fyta-mcp-server/blob/main/examples/DOCKER.md) - Docker deployment details
- [n8n Examples](https://github.com/schimmmi/fyta-mcp-server/tree/main/examples/n8n)
- [Home Assistant Examples](https://github.com/schimmmi/fyta-mcp-server/tree/main/examples/homeassistant)
- [IP-Symcon Examples](https://github.com/schimmmi/fyta-mcp-server/tree/main/examples/ip-symcon)

## 🙏 Credits

Examples and documentation developed with assistance from [Claude Code](https://claude.com/claude-code).

---

**Full Changelog**: https://github.com/schimmmi/fyta-mcp-server/compare/v1.2.1...v1.2.2
