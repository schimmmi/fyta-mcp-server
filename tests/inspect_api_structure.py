#!/usr/bin/env python3
"""
Inspect FYTA API structure to find all available fields for diagnosis
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


async def inspect_api():
    """Inspect full API structure"""

    email = os.getenv("FYTA_EMAIL")
    password = os.getenv("FYTA_PASSWORD")

    if not email or not password:
        print("❌ FYTA_EMAIL and FYTA_PASSWORD required!")
        return

    client = FytaClient(email, password)

    try:
        await client.authenticate()
        print("✅ Authenticated\n")

        # Get plants data
        data = await client.get_plants()
        plants = data.get("plants", [])

        if plants:
            print("=" * 80)
            print("FIRST PLANT - FULL STRUCTURE:")
            print("=" * 80)
            print(json.dumps(plants[0], indent=2))

            # Look for threshold fields
            print("\n" + "=" * 80)
            print("THRESHOLD FIELDS:")
            print("=" * 80)

            plant = plants[0]
            threshold_keys = [k for k in plant.keys() if 'min' in k.lower() or 'max' in k.lower() or 'acceptable' in k.lower() or 'good' in k.lower()]

            if threshold_keys:
                print("Found threshold fields:")
                for key in threshold_keys:
                    print(f"  {key}: {plant[key]}")
            else:
                print("No obvious threshold fields found in plant object")

            # Get measurements for first plant with sensor
            for plant in plants:
                if plant.get("sensor", {}).get("has_sensor"):
                    print("\n" + "=" * 80)
                    print(f"MEASUREMENTS FOR PLANT: {plant['nickname']} (ID: {plant['id']})")
                    print("=" * 80)

                    measurements = await client.get_plant_measurements(plant["id"], "day")
                    print(json.dumps(measurements, indent=2))
                    break

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(inspect_api())
