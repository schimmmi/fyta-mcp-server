# Home Assistant Integration Examples

## Files

- `configuration.yaml` - REST sensors and template sensors
- `automations.yaml` - Pre-configured automations
- `lovelace_dashboard.yaml` - Dashboard cards

## Setup

### 1. Start API Wrapper

```bash
cd /path/to/fyta-mcp-server
python examples/api_wrapper.py
```

### 2. Add Configuration

**Option A: Via configuration.yaml**
```bash
# Copy content from configuration.yaml to your Home Assistant config
nano /config/configuration.yaml
```

**Option B: Via UI (recommended)**
1. Go to Settings → Devices & Services
2. Click "+ Add Integration"
3. Search for "RESTful"
4. Add sensor manually

### 3. Add Automations

**Via UI:**
1. Go to Settings → Automations & Scenes
2. Click "+ Create Automation"
3. Switch to YAML mode
4. Paste automation from `automations.yaml`

**Via File:**
```bash
# Append to your automations.yaml
cat examples/homeassistant/automations.yaml >> /config/automations.yaml
```

### 4. Add Dashboard

1. Go to your Lovelace dashboard
2. Click "Edit Dashboard"
3. Click "+ Add Card"
4. Choose "Manual" card
5. Paste YAML from `lovelace_dashboard.yaml`

### 5. Restart Home Assistant

```bash
# Check configuration first
ha core check

# Restart
ha core restart
```

## Configuration Steps

### Find Your Plant IDs

1. Call the API:
   ```bash
   curl http://localhost:5000/api/plants | jq '.plants[] | {id, nickname}'
   ```

2. Update template sensors in `configuration.yaml`:
   - Replace `108009` with your plant IDs
   - Create one template sensor per plant

### Configure Notifications

Update notification services in automations:
- `notify.mobile_app_your_phone` - Replace with your device name
- Find device name in Settings → Companion App

### Optional: MQTT Setup

If using MQTT:

1. Install Mosquitto broker (Add-on or external)

2. Run MQTT API wrapper:
   ```bash
   pip install paho-mqtt
   python examples/api_wrapper_with_mqtt.py
   ```

3. Uncomment MQTT section in `configuration.yaml`

4. Add cron job:
   ```bash
   # Publish to MQTT every 5 minutes
   */5 * * * * curl -X POST http://localhost:5000/api/events/mqtt
   ```

## Entities Created

After setup, you'll have:

### Sensors
- `sensor.fyta_plants` - Number of plants
- `sensor.fyta_events` - Number of active events
- `sensor.plant_epipremnum_health` - Individual plant health (repeat per plant)

### Binary Sensors
- `binary_sensor.fyta_critical_alert` - Critical alert indicator

### Attributes
Each plant sensor has attributes:
- `temperature`
- `moisture`
- `light`
- `nutrients`

## Automations Included

1. **Critical Plant Alert** - Immediate notification for critical issues
2. **Water Reminder** - Notification when plants need water
3. **Daily Plant Report** - Morning summary of all plants
4. **Temperature Alert with AC Control** - Auto-adjust AC when plants too hot
5. **Automatic Watering** - Auto-water via smart valve (requires hardware)
6. **Low Battery Alert** - Notification for low sensor batteries

## Troubleshooting

### Sensors showing "unavailable"

Check API is running:
```bash
curl http://localhost:5000/health
```

Check logs:
```bash
tail -f /config/home-assistant.log | grep fyta
```

### Automations not triggering

1. Check automation is enabled (toggle in UI)
2. Check trigger conditions in logs
3. Test manually: Settings → Automations → Run

### Template errors

Validate templates:
1. Go to Developer Tools → Template
2. Paste template code
3. Check for errors

## Advanced: Custom Cards

### Install Mushroom Cards

```bash
# Via HACS
1. HACS → Frontend
2. Search "Mushroom"
3. Install
4. Restart Home Assistant
```

### Install Mini Graph Card

For better history visualization:
```bash
# Via HACS
1. HACS → Frontend
2. Search "Mini Graph Card"
3. Install
```

Example usage:
```yaml
type: custom:mini-graph-card
entities:
  - entity: sensor.plant_epipremnum_health
    attribute: temperature
    name: Temperature
  - entity: sensor.plant_epipremnum_health
    attribute: moisture
    name: Moisture
hours_to_show: 24
points_per_hour: 2
```
