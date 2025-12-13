#!/usr/bin/env python3
"""
Test script für den FYTA MCP Server
Testet die Verbindung zur FYTA API und zeigt verfügbare Daten an
"""
import asyncio
import os
import sys
from pathlib import Path

# .env Datei laden wenn vorhanden
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("python-dotenv nicht installiert - Umgebungsvariablen müssen manuell gesetzt werden")

# Server-Modul importieren
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from fyta_mcp_server.client import FytaClient


async def test_connection():
    """Teste die Verbindung zur FYTA API"""
    
    email = os.getenv("FYTA_EMAIL")
    password = os.getenv("FYTA_PASSWORD")
    
    if not email or not password:
        print("❌ FEHLER: FYTA_EMAIL und FYTA_PASSWORD müssen gesetzt sein!")
        print("\nBitte erstelle eine .env Datei mit:")
        print("FYTA_EMAIL=deine-email@example.com")
        print("FYTA_PASSWORD=dein-passwort")
        return False
    
    print("🌱 FYTA MCP Server Test")
    print("=" * 50)
    print(f"📧 Email: {email}")
    print()
    
    # Client erstellen
    client = FytaClient(email, password)
    
    try:
        # Authentifizierung testen
        print("🔐 Teste Authentifizierung...")
        auth_result = await client.authenticate()
        
        if not auth_result:
            print("❌ Authentifizierung fehlgeschlagen!")
            return False
        
        print("✅ Authentifizierung erfolgreich!")
        print(f"   Token läuft ab am: {client.token_expires_at}")
        print()
        
        # Pflanzendaten abrufen
        print("🌿 Hole Pflanzendaten...")
        data = await client.get_plants()
        
        plants = data.get("plants", [])
        gardens = data.get("gardens", [])
        
        print(f"✅ {len(plants)} Pflanzen gefunden")
        print(f"✅ {len(gardens)} Gärten gefunden")
        print()
        
        # Gärten anzeigen
        if gardens:
            print("🏡 Gärten:")
            for garden in gardens:
                print(f"   - {garden['garden_name']} (ID: {garden['id']})")
            print()
        
        # Pflanzen anzeigen
        if plants:
            print("🌱 Pflanzen:")
            status_emoji = {1: "⚠️", 2: "✅", 3: "⚠️"}
            
            for i, plant in enumerate(plants, 1):
                print(f"\n{i}. {plant['nickname']}")
                print(f"   Wissenschaftlicher Name: {plant['scientific_name']}")
                print(f"   Pflanze-ID: {plant['id']}")
                print(f"   Sensor: {'Ja ✅' if plant.get('sensor', {}).get('has_sensor') else 'Nein ❌'}")
                
                if plant.get('sensor', {}).get('has_sensor'):
                    print(f"   Letzte Daten: {plant.get('received_data_at', 'N/A')}")
                    print(f"   Status:")
                    print(f"     Temperatur: {status_emoji.get(plant['temperature_status'], '❓')}")
                    print(f"     Licht: {status_emoji.get(plant['light_status'], '❓')}")
                    print(f"     Feuchtigkeit: {status_emoji.get(plant['moisture_status'], '❓')}")
                    print(f"     Nährstoffe: {status_emoji.get(plant['salinity_status'], '❓')}")
        
        # Pflanzen mit Problemen
        print("\n" + "=" * 50)
        print("⚠️  Pflanzen, die Aufmerksamkeit brauchen:")
        needs_attention = False
        
        for plant in plants:
            issues = []
            if plant["temperature_status"] != 2:
                issues.append("Temperatur")
            if plant["light_status"] != 2:
                issues.append("Licht")
            if plant["moisture_status"] != 2:
                issues.append("Feuchtigkeit")
            if plant["salinity_status"] != 2:
                issues.append("Nährstoffe")
            
            if issues:
                needs_attention = True
                print(f"   • {plant['nickname']}: {', '.join(issues)}")
        
        if not needs_attention:
            print("   Alle Pflanzen sind in optimalem Zustand! ✅")
        
        print("\n" + "=" * 50)
        print("✅ Test erfolgreich abgeschlossen!")
        print("\nDer MCP Server ist bereit für Claude! 🚀")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await client.close()


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
