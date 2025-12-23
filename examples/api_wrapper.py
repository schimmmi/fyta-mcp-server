"""
FYTA MCP Server - Flask API Wrapper
Provides HTTP REST API endpoints for automation platforms
"""
from flask import Flask, jsonify
import asyncio
import json
from src.fyta_mcp_server.client import FytaClient
from src.fyta_mcp_server.handlers import (
    handle_get_plant_events,
    handle_diagnose_plant,
    handle_get_all_plants
)
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuration
FYTA_EMAIL = os.getenv('FYTA_EMAIL')
FYTA_PASSWORD = os.getenv('FYTA_PASSWORD')


@app.route('/api/events', methods=['GET'])
def get_events():
    """Get plant events"""
    async def fetch():
        client = FytaClient(email=FYTA_EMAIL, password=FYTA_PASSWORD)
        await client.login()
        result = await handle_get_plant_events(client, {})
        return json.loads(result[0].text)

    return jsonify(asyncio.run(fetch()))


@app.route('/api/plants', methods=['GET'])
def get_plants():
    """Get all plants"""
    async def fetch():
        client = FytaClient(email=FYTA_EMAIL, password=FYTA_PASSWORD)
        await client.login()
        data = await client.get_plants()
        return data

    return jsonify(asyncio.run(fetch()))


@app.route('/api/diagnose/<int:plant_id>', methods=['GET'])
def diagnose_plant(plant_id):
    """Diagnose specific plant"""
    async def fetch():
        client = FytaClient(email=FYTA_EMAIL, password=FYTA_PASSWORD)
        await client.login()
        result = await handle_diagnose_plant(client, {'plant_id': plant_id})
        return json.loads(result[0].text)

    return jsonify(asyncio.run(fetch()))


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "fyta-api-wrapper"})


if __name__ == '__main__':
    print("Starting FYTA API Wrapper on http://0.0.0.0:5000")
    print("Endpoints:")
    print("  GET /api/events - Get plant events")
    print("  GET /api/plants - Get all plants")
    print("  GET /api/diagnose/<plant_id> - Diagnose specific plant")
    print("  GET /health - Health check")
    app.run(host='0.0.0.0', port=5000)
