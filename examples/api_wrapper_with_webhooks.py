"""
FYTA MCP Server - Flask API Wrapper with Webhook Push
Supports both polling and push notifications to n8n/webhooks
"""
from flask import Flask, jsonify
import asyncio
import json
import requests
from src.fyta_mcp_server.client import FytaClient
from src.fyta_mcp_server.handlers import handle_get_plant_events
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuration
FYTA_EMAIL = os.getenv('FYTA_EMAIL')
FYTA_PASSWORD = os.getenv('FYTA_PASSWORD')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://your-n8n-instance.com/webhook/fyta-events')


@app.route('/api/events', methods=['GET'])
def get_events():
    """Get plant events"""
    async def fetch():
        client = FytaClient(email=FYTA_EMAIL, password=FYTA_PASSWORD)
        await client.login()
        result = await handle_get_plant_events(client, {})
        return json.loads(result[0].text)

    return jsonify(asyncio.run(fetch()))


@app.route('/api/events/push', methods=['POST'])
def push_events():
    """Check events and push to webhook if any found"""
    async def fetch_and_push():
        client = FytaClient(email=FYTA_EMAIL, password=FYTA_PASSWORD)
        await client.login()
        result = await handle_get_plant_events(client, {})
        events_data = json.loads(result[0].text)

        # Only push if there are events
        if events_data['event_count'] > 0:
            # Use webhook_format for cleaner data
            for event in events_data['webhook_format']:
                try:
                    response = requests.post(WEBHOOK_URL, json=event, timeout=10)
                    print(f"Pushed event {event['id']} to webhook: {response.status_code}")
                except Exception as e:
                    print(f"Error pushing event to webhook: {e}")

        return events_data

    return jsonify(asyncio.run(fetch_and_push()))


if __name__ == '__main__':
    print("Starting FYTA API Wrapper with Webhooks on http://0.0.0.0:5000")
    print("Webhook URL:", WEBHOOK_URL)
    print("\nTo trigger webhook push, use:")
    print("  curl -X POST http://localhost:5000/api/events/push")
    print("\nOr add to crontab:")
    print("  */5 * * * * curl -X POST http://localhost:5000/api/events/push")
    app.run(host='0.0.0.0', port=5000)
