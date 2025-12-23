# FYTA MCP Server - Integration Examples

This directory contains ready-to-use code examples for integrating FYTA MCP Server with popular automation platforms.

## 📁 Directory Structure

```
examples/
├── api_wrapper.py                  # Basic Flask API wrapper
├── api_wrapper_with_webhooks.py   # API wrapper with webhook push support
├── api_wrapper_with_mqtt.py       # API wrapper with MQTT publishing
├── n8n/                           # n8n workflow examples
│   ├── workflow_basic_monitoring.json
│   └── README.md
├── homeassistant/                 # Home Assistant integration
│   ├── configuration.yaml
│   ├── automations.yaml
│   ├── lovelace_dashboard.yaml
│   └── README.md
└── ip-symcon/                     # IP-Symcon PHP scripts
    ├── FYTA_UpdateData.php
    ├── FYTA_WaterReminder.php
    ├── FYTA_WebFront.php
    └── README.md
```

## 🚀 Quick Start

### 1. Choose Your Platform

- **n8n** - Visual workflow automation (no-code/low-code)
- **Home Assistant** - Open-source home automation
- **IP-Symcon** - German home automation (commercial)

### 2. Start API Wrapper

All integrations require the API wrapper to be running:

```bash
# Install dependencies
pip install flask

# Basic API wrapper
python examples/api_wrapper.py

# With webhooks
python examples/api_wrapper_with_webhooks.py

# With MQTT
pip install paho-mqtt
python examples/api_wrapper_with_mqtt.py
```

The API wrapper provides HTTP endpoints:
- `GET /api/events` - Get plant events
- `GET /api/plants` - Get all plants
- `GET /api/diagnose/<plant_id>` - Diagnose specific plant
- `GET /health` - Health check

### 3. Follow Platform-Specific Guide

Each directory contains:
- ✅ **README.md** - Complete setup guide
- ✅ **Configuration files** - Ready to use
- ✅ **Example scripts** - Tested and working
- ✅ **Troubleshooting** - Common issues and solutions

## 📚 Platform Guides

### n8n (Workflow Automation)

**Location:** `examples/n8n/`

**What's included:**
- Pre-built workflow JSON (import and run)
- Schedule-based polling (every 5 minutes)
- Critical event notifications (Telegram/Email/Discord)
- Database logging example

**Setup time:** ~10 minutes

**Best for:**
- Complex workflows
- Multi-platform notifications
- Database integration
- Custom logic

[→ See n8n README](./n8n/README.md)

---

### Home Assistant

**Location:** `examples/homeassistant/`

**What's included:**
- Complete `configuration.yaml` with REST sensors
- Ready-to-use automations (6 examples)
- Lovelace dashboard cards
- MQTT integration (optional)

**Setup time:** ~20 minutes

**Best for:**
- Smart home integration
- Native HA dashboards
- iOS/Android app notifications
- Home automation devices

[→ See Home Assistant README](./homeassistant/README.md)

---

### IP-Symcon

**Location:** `examples/ip-symcon/`

**What's included:**
- PHP scripts for data fetching
- WebFront visualization
- Auto-watering logic
- Event handling

**Setup time:** ~15 minutes

**Best for:**
- German users
- Professional installations
- WebFront dashboards
- KNX/1-Wire integration

[→ See IP-Symcon README](./ip-symcon/README.md)

---

## 🔧 API Wrappers

### Basic API Wrapper

**File:** `api_wrapper.py`

Simple HTTP REST API for polling-based integrations.

```bash
python examples/api_wrapper.py
```

Endpoints:
- `http://localhost:5000/api/events`
- `http://localhost:5000/api/plants`
- `http://localhost:5000/api/diagnose/<plant_id>`

### Webhook Push Wrapper

**File:** `api_wrapper_with_webhooks.py`

Pushes events to webhooks (n8n, Make, Zapier).

```bash
# Set webhook URL in .env
echo "WEBHOOK_URL=https://your-n8n.com/webhook/fyta" >> .env

python examples/api_wrapper_with_webhooks.py

# Trigger push
curl -X POST http://localhost:5000/api/events/push
```

**Use with cron:**
```bash
# Add to crontab
*/5 * * * * curl -X POST http://localhost:5000/api/events/push
```

### MQTT Publisher Wrapper

**File:** `api_wrapper_with_mqtt.py`

Publishes to MQTT broker for real-time updates.

```bash
# Set MQTT broker in .env
echo "MQTT_BROKER=localhost" >> .env
echo "MQTT_PORT=1883" >> .env

python examples/api_wrapper_with_mqtt.py

# Publish to MQTT
curl -X POST http://localhost:5000/api/events/mqtt
```

**Topics published:**
- `homeassistant/sensor/fyta/events/count`
- `homeassistant/sensor/fyta/events/critical`
- `homeassistant/sensor/fyta/plant/<plant_id>/event`

---

## 🎯 Use Cases

### 1. Automatic Watering System

**Platforms:** All

**How:**
- Monitor moisture_critical events
- Trigger smart valve/pump
- Log watering action

**Files:**
- n8n: Create workflow with HTTP Request → Switch node
- Home Assistant: `automations.yaml` (auto_water example)
- IP-Symcon: `FYTA_WaterReminder.php` (valve control)

---

### 2. Daily Plant Status Report

**Platforms:** All

**How:**
- Schedule daily at 9:00 AM
- Fetch all plants
- Send summary email/notification

**Files:**
- n8n: Schedule Trigger → HTTP Request → Email
- Home Assistant: `automations.yaml` (daily_report)
- IP-Symcon: Daily event → Email script

---

### 3. Critical Alerts with Priority

**Platforms:** All

**How:**
- Poll events every 5 minutes
- Filter critical severity
- Send high-priority push notification

**Files:**
- n8n: `workflow_basic_monitoring.json`
- Home Assistant: `automations.yaml` (critical_alert)
- IP-Symcon: `FYTA_UpdateData.php` (TriggerCriticalAlert)

---

### 4. Temperature Control Integration

**Platforms:** Home Assistant, IP-Symcon

**How:**
- Detect temperature_extreme events
- Lower AC/thermostat temperature
- Notify user

**Files:**
- Home Assistant: `automations.yaml` (temperature_alert)
- IP-Symcon: Custom script with climate control

---

### 5. Dashboard Visualization

**Platforms:** All

**How:**
- Display plant health metrics
- Show active events
- Real-time updates

**Files:**
- n8n: Store in database → Grafana
- Home Assistant: `lovelace_dashboard.yaml`
- IP-Symcon: `FYTA_WebFront.php`

---

## 🛠️ Customization

### Change Polling Interval

**n8n:** Edit "Schedule Trigger" node interval

**Home Assistant:** Edit `scan_interval` in `configuration.yaml`
```yaml
scan_interval: 300  # 5 minutes
```

**IP-Symcon:** Edit event cyclic time
```php
IPS_SetEventCyclic($eventId, 0, 0, 0, 0, 1, 5); // Every 5 minutes
```

### Add Custom Notifications

**Telegram:**
- n8n: Add Telegram node
- Home Assistant: Use `telegram_bot` integration
- IP-Symcon: Use Telegram module or HTTP API

**Email:**
- n8n: Add "Send Email" node
- Home Assistant: Use `smtp` notify platform
- IP-Symcon: Use `SMTP_SendMailEx()`

**Push Notifications:**
- n8n: Pushover/Pushbullet nodes
- Home Assistant: Mobile app notifications
- IP-Symcon: WebFront notifications

---

## 📊 Data Persistence

### Store Events in Database

**PostgreSQL (n8n):**
```
[HTTP Request] → [Postgres node]
Insert into events table
```

**SQLite (Home Assistant):**
```yaml
# Automatically stored in Home Assistant database
# Access via History panel or SQL
```

**CSV Log (IP-Symcon):**
```php
// Add to FYTA_UpdateData.php
$logFile = '/var/log/fyta_events.csv';
file_put_contents($logFile, $csvLine, FILE_APPEND);
```

---

## 🔒 Security

### Production Deployment

1. **Use HTTPS** for API wrapper:
   ```bash
   # Use reverse proxy (nginx/Apache)
   # Or gunicorn with SSL
   gunicorn -w 4 -b 0.0.0.0:443 --certfile cert.pem --keyfile key.pem api_wrapper:app
   ```

2. **Add authentication**:
   ```python
   from flask_httpauth import HTTPBasicAuth
   auth = HTTPBasicAuth()

   @auth.verify_password
   def verify(username, password):
       return username == 'admin' and password == 'secret'

   @app.route('/api/events')
   @auth.login_required
   def get_events():
       # ...
   ```

3. **Environment variables**:
   ```bash
   # Never commit credentials
   # Use .env file (already in .gitignore)
   ```

4. **Firewall rules**:
   ```bash
   # Only allow local network
   sudo ufw allow from 192.168.1.0/24 to any port 5000
   ```

---

## ❓ Troubleshooting

### API Wrapper Not Starting

```bash
# Check if port 5000 is available
sudo lsof -i :5000

# Check Python dependencies
pip list | grep -E 'flask|asyncio'

# Run with debug
python api_wrapper.py
```

### No Data Received

```bash
# Test FYTA MCP server
python -m fyta_mcp_server

# Test API directly
curl http://localhost:5000/api/plants
curl http://localhost:5000/api/events

# Check credentials
cat .env | grep FYTA
```

### Integration Not Working

**n8n:** Check workflow execution logs

**Home Assistant:** Check logs
```bash
tail -f /config/home-assistant.log | grep fyta
```

**IP-Symcon:** Check Console → Messages

---

## 🆘 Support

### Documentation
- [Main Integration Guide](../docs/INTEGRATIONS.md)
- [FYTA MCP Server README](../README.md)

### Community
- [GitHub Issues](https://github.com/schimmmi/fyta-mcp-server/issues)
- [n8n Community](https://community.n8n.io/)
- [Home Assistant Forums](https://community.home-assistant.io/)
- [IP-Symcon Forum](https://community.symcon.de/)

---

**Happy Automating! 🌱🤖**
