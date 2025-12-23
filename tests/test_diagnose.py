#!/usr/bin/env python3
"""
Test script for the diagnose_plant functionality
"""
import asyncio
import json
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from fyta_mcp_server.client import FytaClient
from fyta_mcp_server.handlers import handle_diagnose_plant


async def test_diagnose():
    """Test the diagnose_plant handler"""

    email = os.getenv("FYTA_EMAIL")
    password = os.getenv("FYTA_PASSWORD")

    if not email or not password:
        print("❌ FYTA_EMAIL and FYTA_PASSWORD required!")
        return

    client = FytaClient(email, password)

    try:
        await client.authenticate()
        print("✅ Authenticated\n")

        # Get plants
        data = await client.get_plants()
        plants = data.get("plants", [])

        if not plants:
            print("❌ No plants found!")
            return

        # Test diagnose on first plant with sensor
        for plant in plants:
            if plant.get("sensor", {}).get("has_sensor"):
                print("=" * 80)
                print(f"DIAGNOSING: {plant['nickname']} (ID: {plant['id']})")
                print("=" * 80)

                # Call diagnose handler
                result = await handle_diagnose_plant(
                    client,
                    {"plant_id": plant["id"], "include_recommendations": True}
                )

                # Parse and pretty print result
                diagnosis = json.loads(result[0].text)
                print(json.dumps(diagnosis, indent=2))

                print("\n" + "=" * 80)
                print("SUMMARY:")
                print("=" * 80)
                print(f"Health: {diagnosis['health'].upper()}")
                print(f"Confidence: {diagnosis['confidence']}")
                print(f"Issues: {', '.join(diagnosis['mainIssues']) if diagnosis['mainIssues'] else 'None'}")

                if diagnosis.get('recommendations'):
                    print(f"\nRecommendations ({len(diagnosis['recommendations'])} actions):")
                    for rec in diagnosis['recommendations']:
                        print(f"  [{rec['priority'].upper()}] {rec['action']}")

                # Only test first plant
                break

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_diagnose())
