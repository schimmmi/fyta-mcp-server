"""
FYTA MCP Server - Flask API Wrapper with MQTT Publishing
Publishes events to MQTT broker for Home Assistant and other systems
"""
from flask import Flask, jsonify
import asyncio
import json
import paho.mqtt.client as mqtt
from src.fyta_mcp_server.client import FytaClient
from src.fyta_mcp_server.handlers import handle_get_plant_events
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuration
FYTA_EMAIL = os.getenv('FYTA_EMAIL')
FYTA_PASSWORD = os.getenv('FYTA_PASSWORD')
MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
MQTT_TOPIC_PREFIX = os.getenv('MQTT_TOPIC_PREFIX', 'homeassistant/sensor/fyta')
MQTT_USERNAME = os.getenv('MQTT_USERNAME')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD')

# Initialize MQTT client
mqtt_client = mqtt.Client()
if MQTT_USERNAME and MQTT_PASSWORD:
    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

try:
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
    print(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
except Exception as e:
    print(f"Could not connect to MQTT broker: {e}")


@app.route('/api/events', methods=['GET'])
def get_events():
    """Get plant events"""
    async def fetch():
        client = FytaClient(email=FYTA_EMAIL, password=FYTA_PASSWORD)
        await client.login()
        result = await handle_get_plant_events(client, {})
        return json.loads(result[0].text)

    return jsonify(asyncio.run(fetch()))


@app.route('/api/events/mqtt', methods=['POST'])
def publish_events_mqtt():
    """Publish events to MQTT"""
    async def fetch_and_publish():
        client = FytaClient(email=FYTA_EMAIL, password=FYTA_PASSWORD)
        await client.login()
        result = await handle_get_plant_events(client, {})
        events_data = json.loads(result[0].text)

        # Publish summary
        mqtt_client.publish(
            f"{MQTT_TOPIC_PREFIX}/events/count",
            events_data['event_count']
        )
        mqtt_client.publish(
            f"{MQTT_TOPIC_PREFIX}/events/critical",
            events_data['summary']['critical']
        )

        # Publish each event
        for event in events_data['events']:
            topic = f"{MQTT_TOPIC_PREFIX}/plant/{event['plant_id']}/event"
            mqtt_client.publish(topic, json.dumps(event))
            print(f"Published event to MQTT: {topic}")

        return events_data

    return jsonify(asyncio.run(fetch_and_publish()))


if __name__ == '__main__':
    print("Starting FYTA API Wrapper with MQTT on http://0.0.0.0:5000")
    print(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"MQTT Topic Prefix: {MQTT_TOPIC_PREFIX}")
    print("\nTo publish to MQTT, use:")
    print("  curl -X POST http://localhost:5000/api/events/mqtt")
    app.run(host='0.0.0.0', port=5000)
