# FYTA MCP Server - Integration Guide 🔌

Complete guide for integrating FYTA MCP Server with automation platforms.

## Table of Contents

- [n8n Integration](#n8n-integration)
- [Home Assistant Integration](#home-assistant-integration)
- [IP-Symcon Integration](#ip-symcon-integration)
- [Webhook Format](#webhook-format)
- [Best Practices](#best-practices)

---

## n8n Integration

n8n is a workflow automation tool that can poll the FYTA MCP Server and trigger actions based on plant events.

### Method 1: Direct MCP Integration (Recommended) 🔥

Use the **n8n-nodes-mcp** community node to directly connect to the FYTA MCP Server without needing an HTTP wrapper.

#### Prerequisites

1. **n8n installed** (self-hosted or desktop app)
2. **FYTA MCP Server running locally**
3. **n8n-nodes-mcp** community node installed

#### 1. Install n8n-nodes-mcp Community Node

In n8n:
1. Go to **Settings** → **Community Nodes**
2. Search for `@joshuatz/n8n-nodes-mcp`
3. Click **Install**
4. Restart n8n

Or install via command line:
```bash
cd ~/.n8n
npm install @joshuatz/n8n-nodes-mcp
# Restart n8n
```

#### 2. Configure MCP Server Connection

You can configure the MCP server connection either via **UI** (recommended for beginners) or **config file** (for advanced users).

---

##### **Option A: UI Configuration (Recommended)** 🎨

The easiest way to set up the FYTA MCP Server in n8n is through the visual interface:

**Step 1: Create MCP Credential**

1. In n8n, go to **Credentials** (gear icon in top menu)
2. Click **Add Credential**
3. Search for **"MCP"** and select **"MCP Server"**
4. Fill in the fields:

**For stdio transport (n8n starts server):**

| Field | Value |
|-------|-------|
| **Name** | `FYTA Plant Monitor` |
| **Transport Type** | `stdio` |
| **Command** | `python` |
| **Arguments** | `-m fyta_mcp_server` |
| **Working Directory** | `/absolute/path/to/fyta-mcp-server` |
| **Environment Variables** | Click "Add Environment Variable" |
| └─ **Name** | `FYTA_EMAIL` |
| └─ **Value** | `your-email@example.com` |
| └─ **Name** | `FYTA_PASSWORD` |
| └─ **Value** | `your-password` |

**Important Notes:**
- ⚠️ Use **absolute path** for Working Directory (e.g., `/home/user/fyta-mcp-server`)
- ⚠️ Make sure Python virtual environment is activated or use full path to Python (e.g., `/home/user/fyta-mcp-server/.venv/bin/python`)
- ✅ Arguments should be entered as **separate array items** if the UI allows, or as single string `-m fyta_mcp_server`

**Step 2: Test Connection**

1. Click **"Test Connection"** button
2. You should see: ✅ "Connection successful"
3. If it fails, check:
   - Python path is correct
   - Virtual environment is activated
   - Credentials are valid
   - Working directory exists

**Step 3: Use in Workflow**

1. Add an **"MCP Tool"** node to your workflow
2. In the node settings:
   - **Credential**: Select `FYTA Plant Monitor`
   - **Tool**: Select from dropdown (e.g., `list_plants`)
   - **Parameters**: Enter JSON (e.g., `{}` for list_plants)

---

##### **Option B: UI Configuration with SSE** 🌐

If you prefer to run the MCP server separately:

**Step 1: Start FYTA MCP Server**

```bash
cd /path/to/fyta-mcp-server
source .venv/bin/activate

# Set credentials
export FYTA_EMAIL="your-email@example.com"
export FYTA_PASSWORD="your-password"

# Start server with SSE transport
python -m fyta_mcp_server --transport sse --port 3000
```

**Step 2: Create MCP Credential in n8n UI**

1. Go to **Credentials** → **Add Credential** → **MCP Server**
2. Fill in:

| Field | Value |
|-------|-------|
| **Name** | `FYTA Plant Monitor (SSE)` |
| **Transport Type** | `sse` (or `http` depending on node version) |
| **URL** | `http://localhost:3000/sse` |

**Step 3: Test & Use**

1. Click **"Test Connection"** → Should succeed
2. Add **MCP Tool** node and select this credential

---

##### **Option C: Config File (Advanced)** ⚙️

For power users who prefer configuration files:

Create `~/.n8n/mcp-config.json`:

**stdio transport:**
```json
{
  "mcpServers": {
    "fyta": {
      "command": "python",
      "args": [
        "-m",
        "fyta_mcp_server"
      ],
      "env": {
        "FYTA_EMAIL": "your-email@example.com",
        "FYTA_PASSWORD": "your-password"
      },
      "cwd": "/path/to/fyta-mcp-server"
    }
  }
}
```

**SSE transport:**
```json
{
  "mcpServers": {
    "fyta": {
      "url": "http://localhost:3000/sse",
      "transport": "sse"
    }
  }
}
```

After creating the config file, restart n8n:
```bash
# If using Docker
docker restart n8n

# If using npm
pkill -f n8n
n8n start
```

#### 3. Create n8n Workflow with MCP Node

**Example Workflow: Daily Plant Health Check**

```
[Schedule Trigger: 9:00 AM]
    → [MCP Tool: list_plants]
    → [Code: Filter Unhealthy Plants]
    → [IF: Has Issues]
        → [MCP Tool: diagnose_plant]
        → [Send Notification]
```

**A. Schedule Trigger Node**
- **Trigger**: Schedule Trigger
- **Trigger Interval**: Daily at 9:00 AM

**B. MCP Tool Node - List Plants**
- **Node**: MCP Tool
- **MCP Server**: `fyta`
- **Tool**: `list_plants`
- **Parameters**: `{}` (empty)

**C. Code Node - Filter Plants**
```javascript
// Filter plants that need attention
const plants = $input.item.json.plants;

const needsAttention = plants.filter(plant => {
  return plant.status !== 'good' && plant.status !== 'excellent';
});

return needsAttention.map(plant => ({
  json: {
    plant_id: plant.id,
    plant_name: plant.nickname,
    status: plant.status,
    issues: plant.issues
  }
}));
```

**D. IF Node - Check if Plants Need Attention**
- **Condition**: `{{ $json.plant_id !== undefined }}`

**E. MCP Tool Node - Diagnose Plant** (in True branch)
- **Node**: MCP Tool
- **MCP Server**: `fyta`
- **Tool**: `diagnose_plant`
- **Parameters**:
  ```json
  {
    "plant_id": "{{ $json.plant_id }}",
    "include_recommendations": true
  }
  ```

**F. Send Notification Node**
- **Node**: Send Email / Telegram / Discord (your choice)
- **Message Template**:
  ```
  🌱 Plant Alert: {{ $json.plantName }}

  Health: {{ $json.health }}
  Issues: {{ $json.mainIssues.join(', ') }}

  Recommendations:
  {{ $json.recommendations.map(r => `• ${r.action}: ${r.details}`).join('\n') }}

  Watering: {{ $json.watering.recommendation.action }}
  Fertilization: {{ $json.fertilization.recommendation.action }}
  ```

#### 4. Advanced Workflow Examples

**Example 1: Auto-Fertilization Reminder**

```
[Schedule: Check every 6 hours]
    → [MCP Tool: list_plants]
    → [Split In Batches]
        → [MCP Tool: diagnose_plant]
        → [Code: Check Fertilization Status]
        → [IF: Needs Fertilization]
            → [Create Todo in Todoist]
            → [Send Push Notification]
```

**Code Node - Check Fertilization:**
```javascript
const diagnosis = $input.item.json;
const fertRecommendation = diagnosis.fertilization?.recommendation;

if (!fertRecommendation) {
  return [];
}

// Check if fertilization needed
const needsFertilization =
  fertRecommendation.action === 'fertilize_now' ||
  fertRecommendation.action === 'fertilize_soon';

if (needsFertilization) {
  return [{
    json: {
      plant_id: diagnosis.plantId,
      plant_name: diagnosis.plantName,
      action: fertRecommendation.action,
      timing: fertRecommendation.timing,
      dosage: fertRecommendation.dosage,
      reasoning: fertRecommendation.reasoning.join('. ')
    }
  }];
}

return [];
```

**Example 2: Real-time Event Monitoring**

```
[Schedule: Every 5 minutes]
    → [MCP Tool: get_plant_events]
    → [Code: Process Events]
    → [Switch by Severity]
        → Critical: [Urgent Notification + Log to DB]
        → Warning: [Standard Notification]
        → Info: [Log Only]
```

**Code Node - Process Events:**
```javascript
const eventsData = $input.item.json;
const events = eventsData.events || [];

// Group by severity
const grouped = {
  critical: [],
  warning: [],
  info: []
};

events.forEach(event => {
  grouped[event.severity].push(event);
});

// Return items for switch node
return Object.keys(grouped).flatMap(severity =>
  grouped[severity].map(event => ({
    json: {
      ...event,
      severity_group: severity
    }
  }))
);
```

**Switch Node Configuration:**
```javascript
// Mode: Based on Expression
// Output: Multiple

// Route 1: Critical
{{ $json.severity_group === 'critical' }}

// Route 2: Warning
{{ $json.severity_group === 'warning' }}

// Route 3: Info
{{ $json.severity_group === 'info' }}
```

**Example 3: Smart Watering with Database History**

```
[Webhook: Water Plant Completed]
    → [MCP Tool: log_care_action]
    → [PostgreSQL: Store History]
    → [MCP Tool: diagnose_plant]
    → [Code: Calculate Next Watering]
    → [Schedule Future Reminder]
```

**MCP Tool - Log Care Action:**
```json
{
  "plant_id": "{{ $json.plant_id }}",
  "action_type": "watering",
  "notes": "Watered {{ $json.amount }}ml"
}
```

#### 5. Available MCP Tools

The FYTA MCP Server provides these tools:

| Tool | Parameters | Description |
|------|------------|-------------|
| `list_plants` | - | Get all plants with current status |
| `get_plant` | `plant_id` | Get details for specific plant |
| `diagnose_plant` | `plant_id`, `include_recommendations` | Full diagnosis with recommendations |
| `get_plant_events` | `severity?`, `days?` | Get plant events/alerts |
| `get_measurements` | `plant_id`, `timeline` | Get sensor measurements |
| `log_care_action` | `plant_id`, `action_type`, `notes?` | Log care activity |
| `get_care_history` | `plant_id`, `days?`, `action_type?` | Get care history |
| `get_sensor_info` | `plant_id` | Get sensor details |
| `interpret_sensor` | `plant_id`, `value`, `metric` | Interpret sensor reading |

#### 6. Error Handling

Always add error handling to your workflows:

**Try-Catch Pattern:**
```
[MCP Tool]
    → [On Error: Catch]
        → [Log Error to File/DB]
        → [Send Error Notification]
        → [Stop and Wait]
```

**Retry Logic:**
```javascript
// In Code node before MCP call
const maxRetries = 3;
let retryCount = $executionData.retryCount || 0;

if (retryCount >= maxRetries) {
  throw new Error('Max retries reached');
}

// Store retry count
return {
  json: {
    ...($json),
    retryCount: retryCount + 1
  }
};
```

#### 7. Best Practices

**Performance:**
- ✅ Use **Split In Batches** when processing multiple plants
- ✅ Set reasonable polling intervals (5-15 minutes for events, 30-60 minutes for diagnostics)
- ✅ Cache plant data in n8n memory/database for frequently accessed info

**Reliability:**
- ✅ Add **error handlers** to all MCP Tool nodes
- ✅ Implement **retry logic** with exponential backoff
- ✅ Log all failures to database for debugging

**Security:**
- ✅ Store FYTA credentials in **environment variables** (not in workflow JSON)
- ✅ Use n8n's credential system for sensitive data
- ✅ Don't expose MCP server to internet without authentication

**Notifications:**
- ✅ Implement **notification throttling** (max 1 per plant per day)
- ✅ Use different channels for different severities (critical → push, warning → email)
- ✅ Add **action buttons** to notifications (e.g., "Mark as watered")

#### 8. Troubleshooting

**MCP Server Not Connecting:**
```bash
# Check if server is running
ps aux | grep fyta_mcp_server

# Test MCP connection manually
python -m fyta_mcp_server --transport stdio

# Check logs
tail -f ~/.n8n/logs/mcp-fyta.log
```

**n8n-nodes-mcp Issues:**
```bash
# Reinstall community node
cd ~/.n8n
npm uninstall @joshuatz/n8n-nodes-mcp
npm install @joshuatz/n8n-nodes-mcp

# Check n8n logs
docker logs n8n  # if using Docker
# or
~/.n8n/logs/n8n.log  # if using npm
```

**Tool Call Errors:**
```javascript
// In Code node, add debug logging
console.log('MCP Response:', JSON.stringify($input.item.json, null, 2));

// Check for error fields
if ($input.item.json.error) {
  throw new Error($input.item.json.error);
}
```

#### 9. Example: Complete Workflow JSON

Download ready-to-use workflows:
- [Daily Plant Health Report](../examples/n8n/daily-health-report.json)
- [Critical Event Alerts](../examples/n8n/critical-alerts.json)
- [Fertilization Tracker](../examples/n8n/fertilization-tracker.json)

---

### Method 2: HTTP Request with Polling

#### 1. Setup Python API Wrapper

First, create a simple Flask API wrapper for the MCP server:

```bash
cd /path/to/fyta-mcp-server
pip install flask
```

Create `api_wrapper.py`:

```python
from flask import Flask, jsonify
import asyncio
import json
from src.fyta_mcp_server.client import FytaClient
from src.fyta_mcp_server.handlers import handle_get_plant_events, handle_diagnose_plant
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route('/api/events', methods=['GET'])
def get_events():
    """Get plant events"""
    async def fetch():
        client = FytaClient(
            email=os.getenv('FYTA_EMAIL'),
            password=os.getenv('FYTA_PASSWORD')
        )
        await client.login()
        result = await handle_get_plant_events(client, {})
        return json.loads(result[0].text)

    return jsonify(asyncio.run(fetch()))

@app.route('/api/plants', methods=['GET'])
def get_plants():
    """Get all plants"""
    async def fetch():
        client = FytaClient(
            email=os.getenv('FYTA_EMAIL'),
            password=os.getenv('FYTA_PASSWORD')
        )
        await client.login()
        data = await client.get_plants()
        return data

    return jsonify(asyncio.run(fetch()))

@app.route('/api/diagnose/<int:plant_id>', methods=['GET'])
def diagnose_plant(plant_id):
    """Diagnose specific plant"""
    async def fetch():
        client = FytaClient(
            email=os.getenv('FYTA_EMAIL'),
            password=os.getenv('FYTA_PASSWORD')
        )
        await client.login()
        result = await handle_diagnose_plant(client, {'plant_id': plant_id})
        return json.loads(result[0].text)

    return jsonify(asyncio.run(fetch()))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

Run the API wrapper:
```bash
python api_wrapper.py
```

#### 2. Create n8n Workflow

**Workflow Structure:**
```
[Schedule Trigger]
    → [HTTP Request: Get Events]
    → [IF: Has Critical Events]
        → [Send Notification]
        → [Log to Database]
```

**Nodes Configuration:**

**A. Schedule Trigger Node**
- Trigger: `Schedule Trigger`
- Interval: Every 5 minutes
- This polls the API regularly

**B. HTTP Request Node - Get Events**
- Method: `GET`
- URL: `http://localhost:5000/api/events`
- Response Format: `JSON`

**C. IF Node - Check for Critical Events**
- Condition: `{{ $json.summary.critical }} > 0`

**D. Send Notification (Multiple Options)**

**Option 1: Email**
```javascript
Subject: 🚨 Plant Alert: {{ $json.summary.critical }} Critical Issues
Body:
{{ $json.events.map(e => `
Plant: ${e.plant_name}
Issue: ${e.message}
Actions: ${e.suggested_actions.join(', ')}
`).join('\n\n') }}
```

**Option 2: Telegram**
- Use Telegram node
- Chat ID: Your chat ID
- Message:
```
🌱 *Plant Alert*

{{ $json.events.map(e => `
*${e.plant_name}*
${e.message}
Severity: ${e.severity}
`).join('\n') }}
```

**Option 3: Discord Webhook**
```json
{
  "embeds": [{
    "title": "🚨 Plant Alert",
    "description": "{{ $json.summary.critical }} critical issues detected",
    "color": 15158332,
    "fields": [
      {{#each $json.events}}
      {
        "name": "{{ plant_name }}",
        "value": "{{ message }}\n**Actions:** {{ suggested_actions.join(', ') }}"
      }
      {{/each}}
    ]
  }]
}
```

**E. Write to Database (Optional)**
- Store events in PostgreSQL/MySQL for history tracking

#### 3. Advanced Workflow: Per-Plant Monitoring

```
[Schedule Trigger: Every 10 min]
    → [HTTP: Get All Plants]
    → [Split In Batches]
        → [HTTP: Diagnose Plant]
        → [IF: Health != "excellent"]
            → [Switch by Severity]
                → Critical: [Urgent Notification]
                → Warning: [Daily Summary]
                → Info: [Log Only]
```

### Method 2: Webhook Push (Advanced)

Modify `api_wrapper.py` to push to n8n webhook when events detected:

```python
import requests

WEBHOOK_URL = "https://your-n8n-instance.com/webhook/fyta-events"

@app.route('/api/events/push', methods=['POST'])
def push_events():
    """Check events and push to n8n webhook if any found"""
    async def fetch_and_push():
        client = FytaClient(
            email=os.getenv('FYTA_EMAIL'),
            password=os.getenv('FYTA_PASSWORD')
        )
        await client.login()
        result = await handle_get_plant_events(client, {})
        events_data = json.loads(result[0].text)

        # Only push if there are events
        if events_data['event_count'] > 0:
            # Use webhook_format for cleaner data
            for event in events_data['webhook_format']:
                requests.post(WEBHOOK_URL, json=event)

        return events_data

    return jsonify(asyncio.run(fetch_and_push()))
```

Then use cron to trigger:
```bash
# Add to crontab
*/5 * * * * curl -X POST http://localhost:5000/api/events/push
```

---

## Home Assistant Integration

Home Assistant can integrate FYTA data as sensors and trigger automations.

### Method 1: RESTful Sensors

#### 1. Install REST Integration

Add to `configuration.yaml`:

```yaml
# FYTA Plant Sensors
sensor:
  # All Plants Overview
  - platform: rest
    name: FYTA Plants
    resource: http://localhost:5000/api/plants
    method: GET
    value_template: "{{ value_json.plants | length }}"
    json_attributes:
      - plants
    scan_interval: 300  # Update every 5 minutes

  # Plant Events
  - platform: rest
    name: FYTA Events
    resource: http://localhost:5000/api/events
    method: GET
    value_template: "{{ value_json.event_count }}"
    json_attributes:
      - events
      - summary
    scan_interval: 300

# Template Sensors for Individual Plants
template:
  - sensor:
      # Plant 1 - Epipremnum aureum
      - name: "Plant Epipremnum Health"
        unique_id: plant_108009_health
        state: >
          {% set plants = state_attr('sensor.fyta_plants', 'plants') %}
          {% set plant = plants | selectattr('id', 'equalto', 108009) | first %}
          {{ plant.status | default('unknown') }}
        attributes:
          temperature: >
            {% set plants = state_attr('sensor.fyta_plants', 'plants') %}
            {% set plant = plants | selectattr('id', 'equalto', 108009) | first %}
            {{ plant.temperature | default(0) }}
          moisture: >
            {% set plants = state_attr('sensor.fyta_plants', 'plants') %}
            {% set plant = plants | selectattr('id', 'equalto', 108009) | first %}
            {{ plant.moisture | default(0) }}
          light: >
            {% set plants = state_attr('sensor.fyta_plants', 'plants') %}
            {% set plant = plants | selectattr('id', 'equalto', 108009) | first %}
            {{ plant.light | default(0) }}
          nutrients: >
            {% set plants = state_attr('sensor.fyta_plants', 'plants') %}
            {% set plant = plants | selectattr('id', 'equalto', 108009) | first %}
            {{ plant.salinity | default(0) }}

  - binary_sensor:
      # Critical Events Alert
      - name: "FYTA Critical Alert"
        unique_id: fyta_critical_alert
        state: >
          {{ state_attr('sensor.fyta_events', 'summary')['critical'] | int > 0 }}
        device_class: problem
```

#### 2. Create Automations

**A. Critical Alert Notification**

Create file `automations.yaml`:

```yaml
# FYTA Critical Plant Alert
- id: fyta_critical_alert
  alias: "FYTA: Critical Plant Alert"
  description: "Send notification when critical plant issues detected"
  trigger:
    - platform: state
      entity_id: binary_sensor.fyta_critical_alert
      to: "on"
  condition:
    - condition: template
      value_template: "{{ state_attr('sensor.fyta_events', 'summary')['critical'] | int > 0 }}"
  action:
    - service: notify.mobile_app_your_phone
      data:
        title: "🚨 Plant Alert"
        message: >
          {% set events = state_attr('sensor.fyta_events', 'events') %}
          {% set critical = events | selectattr('severity', 'equalto', 'critical') | list %}
          {{ critical | length }} critical plant issues detected:
          {% for event in critical %}
          - {{ event.plant_name }}: {{ event.message }}
          {% endfor %}
        data:
          priority: high
          ttl: 0

# Water Reminder
- id: fyta_water_reminder
  alias: "FYTA: Water Plant Reminder"
  description: "Remind to water plants when moisture critical"
  trigger:
    - platform: state
      entity_id: sensor.fyta_events
  condition:
    - condition: template
      value_template: >
        {% set events = state_attr('sensor.fyta_events', 'events') %}
        {{ events | selectattr('event_type', 'equalto', 'moisture_critical') | list | length > 0 }}
  action:
    - service: notify.persistent_notification
      data:
        title: "💧 Time to Water Plants"
        message: >
          {% set events = state_attr('sensor.fyta_events', 'events') %}
          {% set water_events = events | selectattr('event_type', 'equalto', 'moisture_critical') | list %}
          The following plants need water:
          {% for event in water_events %}
          - {{ event.plant_name }}
          {% endfor %}

# Daily Plant Status Report
- id: fyta_daily_report
  alias: "FYTA: Daily Plant Status Report"
  description: "Send daily summary of all plants"
  trigger:
    - platform: time
      at: "09:00:00"
  action:
    - service: notify.mobile_app_your_phone
      data:
        title: "🌱 Daily Plant Report"
        message: >
          {% set plants = state_attr('sensor.fyta_plants', 'plants') %}
          Total plants: {{ plants | length }}

          {% set needs_attention = plants | selectattr('status', 'ne', 'good') | list %}
          {% if needs_attention | length > 0 %}
          Needs attention: {{ needs_attention | length }}
          {% for plant in needs_attention %}
          - {{ plant.nickname }}: {{ plant.status }}
          {% endfor %}
          {% else %}
          All plants are healthy! ✅
          {% endif %}
```

#### 3. Lovelace Dashboard Card

Add to your Lovelace dashboard (`ui-lovelace.yaml` or via UI):

```yaml
type: vertical-stack
cards:
  # Summary Card
  - type: entities
    title: 🌱 FYTA Plant Monitor
    entities:
      - entity: sensor.fyta_plants
        name: Total Plants
        icon: mdi:flower
      - entity: sensor.fyta_events
        name: Active Events
        icon: mdi:alert
      - entity: binary_sensor.fyta_critical_alert
        name: Critical Alert

  # Events Card
  - type: conditional
    conditions:
      - entity: sensor.fyta_events
        state_not: "0"
    card:
      type: markdown
      content: >
        {% set events = state_attr('sensor.fyta_events', 'events') %}
        ## 🚨 Active Events
        {% for event in events %}
        **{{ event.plant_name }}**
        {{ event.message }}
        *Severity: {{ event.severity }}*

        {% endfor %}

  # Individual Plant Card (repeat for each plant)
  - type: gauge
    entity: sensor.plant_epipremnum_health
    name: Epipremnum aureum
    min: 0
    max: 100
    severity:
      green: 70
      yellow: 40
      red: 0
```

### Method 2: MQTT Integration (Advanced)

For real-time updates, use MQTT:

#### 1. Install Mosquitto MQTT Broker

```bash
# Home Assistant Add-on or standalone
docker run -d --name mosquitto -p 1883:1883 eclipse-mosquitto
```

#### 2. Modify API Wrapper to Publish MQTT

```python
import paho.mqtt.client as mqtt

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_PREFIX = "homeassistant/sensor/fyta"

mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

@app.route('/api/events/mqtt', methods=['POST'])
def publish_events_mqtt():
    """Publish events to MQTT"""
    async def fetch_and_publish():
        client = FytaClient(
            email=os.getenv('FYTA_EMAIL'),
            password=os.getenv('FYTA_PASSWORD')
        )
        await client.login()
        result = await handle_get_plant_events(client, {})
        events_data = json.loads(result[0].text)

        # Publish summary
        mqtt_client.publish(
            f"{MQTT_TOPIC_PREFIX}/events/count",
            events_data['event_count']
        )

        # Publish each event
        for event in events_data['events']:
            topic = f"{MQTT_TOPIC_PREFIX}/plant/{event['plant_id']}/event"
            mqtt_client.publish(topic, json.dumps(event))

        return events_data

    return jsonify(asyncio.run(fetch_and_publish()))
```

#### 3. Home Assistant MQTT Configuration

```yaml
mqtt:
  sensor:
    - name: "FYTA Event Count"
      state_topic: "homeassistant/sensor/fyta/events/count"
      unit_of_measurement: "events"
      icon: mdi:alert
```

---

## IP-Symcon Integration

IP-Symcon is a German home automation platform that can integrate FYTA via PHP scripts.

### Method 1: HTTP Request Module

#### 1. Create FYTA Module

In IP-Symcon Console, create new category "FYTA Plants".

#### 2. Create PHP Script for Data Fetching

**Script: "FYTA_UpdateData"**

```php
<?php
// Configuration
$apiUrl = "http://localhost:5000/api";
$updateInterval = 300; // 5 minutes in seconds

// Function to fetch FYTA data
function FetchFYTAData($endpoint) {
    global $apiUrl;
    $url = $apiUrl . $endpoint;

    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 30);

    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($httpCode != 200) {
        return false;
    }

    return json_decode($response, true);
}

// Update plant data
function UpdatePlantData() {
    $plants = FetchFYTAData("/plants");

    if ($plants === false) {
        echo "Error fetching plant data\n";
        return;
    }

    foreach ($plants['plants'] as $plant) {
        $plantId = $plant['id'];
        $plantName = $plant['nickname'];

        // Create or update variables
        $categoryId = CreateCategoryByName(IPS_GetObject(0)['ObjectID'], "FYTA_Plant_" . $plantId, $plantName);

        // Temperature
        $varId = CreateVariableByName($categoryId, "Temperature", 2); // Float
        SetValue($varId, $plant['temperature']);

        // Moisture
        $varId = CreateVariableByName($categoryId, "Moisture", 2);
        SetValue($varId, $plant['moisture']);

        // Light
        $varId = CreateVariableByName($categoryId, "Light", 2);
        SetValue($varId, $plant['light']);

        // Nutrients
        $varId = CreateVariableByName($categoryId, "Nutrients", 2);
        SetValue($varId, $plant['salinity']);

        // Status
        $varId = CreateVariableByName($categoryId, "Status", 3); // String
        SetValue($varId, GetStatusText($plant['temperature_status'], $plant['moisture_status'], $plant['light_status']));
    }

    echo "Plant data updated successfully\n";
}

// Update events
function UpdateEvents() {
    $events = FetchFYTAData("/events");

    if ($events === false) {
        echo "Error fetching events\n";
        return;
    }

    // Create events category
    $categoryId = CreateCategoryByName(IPS_GetObject(0)['ObjectID'], "FYTA_Events", "FYTA Events");

    // Event count
    $varId = CreateVariableByName($categoryId, "EventCount", 1); // Integer
    SetValue($varId, $events['event_count']);

    // Critical count
    $varId = CreateVariableByName($categoryId, "CriticalCount", 1);
    SetValue($varId, $events['summary']['critical']);

    // Event list (as string)
    $eventList = "";
    foreach ($events['events'] as $event) {
        $eventList .= $event['plant_name'] . ": " . $event['message'] . "\n";
    }
    $varId = CreateVariableByName($categoryId, "EventList", 3); // String
    SetValue($varId, $eventList);

    // Trigger alert if critical events
    if ($events['summary']['critical'] > 0) {
        TriggerCriticalAlert($events['events']);
    }

    echo "Events updated successfully\n";
}

// Helper: Create category if not exists
function CreateCategoryByName($parentId, $ident, $name) {
    $catId = @IPS_GetObjectIDByIdent($ident, $parentId);
    if ($catId === false) {
        $catId = IPS_CreateCategory();
        IPS_SetParent($catId, $parentId);
        IPS_SetIdent($catId, $ident);
        IPS_SetName($catId, $name);
    }
    return $catId;
}

// Helper: Create variable if not exists
function CreateVariableByName($parentId, $name, $type) {
    $varId = @IPS_GetObjectIDByIdent(str_replace(" ", "_", $name), $parentId);
    if ($varId === false) {
        $varId = IPS_CreateVariable($type);
        IPS_SetParent($varId, $parentId);
        IPS_SetIdent($varId, str_replace(" ", "_", $name));
        IPS_SetName($varId, $name);
    }
    return $varId;
}

// Helper: Get status text
function GetStatusText($temp, $moisture, $light) {
    $statusMap = [1 => "Zu niedrig", 2 => "Optimal", 3 => "Zu hoch"];

    $issues = [];
    if ($temp != 2) $issues[] = "Temperatur " . $statusMap[$temp];
    if ($moisture != 2) $issues[] = "Feuchtigkeit " . $statusMap[$moisture];
    if ($light != 2) $issues[] = "Licht " . $statusMap[$light];

    return empty($issues) ? "Alles OK ✓" : implode(", ", $issues);
}

// Helper: Trigger alert
function TriggerCriticalAlert($events) {
    // Send WebFront notification
    $message = "🚨 Pflanzen benötigen Aufmerksamkeit!\n\n";
    foreach ($events as $event) {
        if ($event['severity'] == 'critical') {
            $message .= "• " . $event['plant_name'] . ": " . $event['message'] . "\n";
        }
    }

    // Use IP-Symcon notification system
    WFC_SendNotification(12345 /*WebFront ID*/, "FYTA Alarm", $message, "alarm", 0);
}

// Main execution
UpdatePlantData();
UpdateEvents();
?>
```

#### 3. Create Event Script for Automations

**Script: "FYTA_WaterReminder"**

```php
<?php
// Check if watering needed
$events = FetchFYTAData("/events");

if ($events !== false) {
    foreach ($events['events'] as $event) {
        if ($event['event_type'] == 'moisture_critical') {
            // Trigger watering reminder
            $message = "💧 Pflanze gießen: " . $event['plant_name'];

            // Send push notification
            WFC_SendNotification(12345, "Gießen!", $message, "water", 0);

            // Or trigger other action (e.g., open valve, send email)
            // SetValue(54321 /*Valve Variable*/, true);
        }
    }
}
?>
```

#### 4. Create Event Handler

Create event "OnHourChange" to trigger updates:

```php
<?php
// Run every hour
IPS_RunScript(12345 /*FYTA_UpdateData Script ID*/);
?>
```

#### 5. Create WebFront Visualization

In WebFront, create a new view:

```php
<?php
// FYTA Dashboard
$categoryId = IPS_GetObjectIDByIdent("FYTA_Events", 0);

echo "<h2>🌱 FYTA Pflanzen-Monitor</h2>";

// Event summary
$eventCount = GetValue(IPS_GetObjectIDByIdent("EventCount", $categoryId));
$criticalCount = GetValue(IPS_GetObjectIDByIdent("CriticalCount", $categoryId));

echo "<div style='padding: 10px; background: " . ($criticalCount > 0 ? "#ffebee" : "#e8f5e9") . "'>";
echo "<strong>Aktive Ereignisse:</strong> $eventCount<br>";
echo "<strong>Kritisch:</strong> $criticalCount<br>";
echo "</div>";

// Event list
$eventList = GetValue(IPS_GetObjectIDByIdent("EventList", $categoryId));
if (!empty($eventList)) {
    echo "<h3>⚠️ Aktive Warnungen</h3>";
    echo "<pre>" . htmlspecialchars($eventList) . "</pre>";
}

// Plant list
$plants = IPS_GetChildrenIDs(0);
echo "<h3>Alle Pflanzen</h3>";
echo "<table>";
foreach ($plants as $plantCatId) {
    $obj = IPS_GetObject($plantCatId);
    if (strpos($obj['ObjectIdent'], 'FYTA_Plant_') === 0) {
        $plantName = $obj['ObjectName'];
        $temp = GetValue(IPS_GetObjectIDByIdent("Temperature", $plantCatId));
        $moisture = GetValue(IPS_GetObjectIDByIdent("Moisture", $plantCatId));
        $status = GetValue(IPS_GetObjectIDByIdent("Status", $plantCatId));

        echo "<tr>";
        echo "<td><strong>$plantName</strong></td>";
        echo "<td>🌡️ {$temp}°C</td>";
        echo "<td>💧 {$moisture}%</td>";
        echo "<td>$status</td>";
        echo "</tr>";
    }
}
echo "</table>";
?>
```

---

## Webhook Format

All automation systems can consume the webhook format from events:

```json
{
  "id": "8084a3189f37",
  "type": "temperature_extreme",
  "timestamp": "2025-12-23T22:12:40.039486",
  "plant": {
    "id": 108009,
    "name": "Epipremnum aureum"
  },
  "severity": "critical",
  "priority": "high",
  "message": "Temperature is too high - plant stress risk",
  "actionable": true,
  "actions": [
    "Move plant to cooler location",
    "Increase ventilation"
  ],
  "metadata": {}
}
```

### Event Types

- `status_change` - Metric changed from one status to another
- `moisture_critical` - Plant needs water urgently
- `temperature_extreme` - Temperature too high (dangerous)
- `sensor_silence` - Sensor hasn't reported in a while
- `battery_low` - Sensor battery low
- `wifi_disconnected` - Sensor lost WiFi connection

### Severity Levels

- `critical` - Immediate action required
- `warning` - Should be addressed soon
- `info` - Informational only

---

## Best Practices

### 1. Polling Intervals

- **Events**: Poll every 5 minutes (300 seconds)
- **Plant Data**: Poll every 15-30 minutes
- **Diagnostics**: Poll every hour or on-demand

### 2. Error Handling

Always implement retry logic:

```python
import time

def fetch_with_retry(url, max_retries=3):
    for i in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if i == max_retries - 1:
                raise
            time.sleep(5 * (i + 1))  # Exponential backoff
```

### 3. Rate Limiting

Don't overload the FYTA API:
- Maximum 1 request per second
- Use caching for frequently accessed data
- Batch requests when possible

### 4. Notification Filtering

Avoid notification fatigue:

```python
# Only notify once per event per day
last_notified = {}

def should_notify(event_id):
    now = datetime.now()
    if event_id in last_notified:
        if (now - last_notified[event_id]).seconds < 86400:  # 24 hours
            return False
    last_notified[event_id] = now
    return True
```

### 5. Security

- ✅ Use HTTPS for API wrapper in production
- ✅ Store credentials in environment variables
- ✅ Use authentication tokens for webhook endpoints
- ✅ Implement IP whitelisting if exposing to internet

### 6. Data Persistence

Store historical data for trends:

```python
# Example with SQLite
import sqlite3

conn = sqlite3.connect('fyta_history.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    timestamp TEXT,
    plant_id INTEGER,
    plant_name TEXT,
    event_type TEXT,
    severity TEXT,
    message TEXT
)
''')

# Insert events
for event in events['events']:
    cursor.execute('''
        INSERT OR IGNORE INTO events VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        event['event_id'],
        event['timestamp'],
        event['plant_id'],
        event['plant_name'],
        event['event_type'],
        event['severity'],
        event['message']
    ))

conn.commit()
```

---

## Troubleshooting

### API Wrapper Not Responding

```bash
# Check if running
ps aux | grep api_wrapper

# Check logs
tail -f /var/log/fyta_api.log

# Restart
pkill -f api_wrapper.py
python api_wrapper.py &
```

### Home Assistant Not Updating

```bash
# Check REST sensor configuration
# Go to Developer Tools > States
# Look for sensor.fyta_plants

# Check logs
tail -f /config/home-assistant.log | grep fyta
```

### IP-Symcon Script Errors

```
# Enable debug mode in script
ini_set('display_errors', 1);
error_reporting(E_ALL);

# Check IP-Symcon logs
Console > Meldungen > Fehler
```

---

## Example Use Cases

### 1. Automatic Watering System

When moisture critical, open smart valve for 30 seconds:

**n8n:**
```
[Event: moisture_critical] → [HTTP: Open Valve] → [Wait 30s] → [HTTP: Close Valve]
```

**Home Assistant:**
```yaml
automation:
  - trigger:
      - platform: template
        value_template: "{{ ... moisture_critical ... }}"
    action:
      - service: switch.turn_on
        entity_id: switch.garden_valve_1
      - delay: 00:00:30
      - service: switch.turn_off
        entity_id: switch.garden_valve_1
```

### 2. Light Adjustment

Adjust grow lights based on DLI:

```yaml
# Home Assistant
automation:
  - trigger:
      - platform: numeric_state
        entity_id: sensor.plant_dli
        below: 10
    action:
      - service: light.turn_on
        entity_id: light.grow_light
        data:
          brightness_pct: 100
```

### 3. Temperature Alert with Smart Thermostat

If temperature too high, adjust room temperature:

```javascript
// n8n
if (event.type === 'temperature_extreme') {
  // Lower room temperature
  await $http.post('http://nest-api/temperature', {
    target: 20
  });
}
```

---

## Support

For integration issues:
- [GitHub Issues](https://github.com/schimmmi/fyta-mcp-server/issues)
- [n8n Community](https://community.n8n.io/)
- [Home Assistant Forums](https://community.home-assistant.io/)
- [IP-Symcon Forum](https://community.symcon.de/)

---

**Happy Automating! 🌱🤖**
