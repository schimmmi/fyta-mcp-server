# FYTA MCP Server 🌱

Ein Model Context Protocol (MCP) Server für FYTA Pflanzensensor-Daten. Damit kannst du über Claude direkt auf deine Pflanzen-Daten zugreifen!

## Was ist das?

FYTA ist ein smartes Pflanzensensor-System, das Bodenfeuchtigkeit, Temperatur, Licht und Nährstoffe misst. Dieser MCP Server ermöglicht es Claude, auf diese Daten zuzugreifen und dir bei der Pflanzenpflege zu helfen.

## Features

- 🌿 **Alle Pflanzen abrufen**: Kompletter Überblick über alle deine Pflanzen mit Sensordaten
- 🔍 **Pflanzendetails**: Detaillierte Infos zu einzelnen Pflanzen
- ⚠️ **Pflanzen mit Problemen**: Automatische Erkennung von Pflanzen, die Aufmerksamkeit brauchen
- 🏡 **Garten-Übersicht**: Organisierte Ansicht deiner Gärten und Pflanzen

## Installation

### Voraussetzungen

- Python 3.10 oder höher
- Ein FYTA Account mit Pflanzen
- Claude Desktop App (oder anderer MCP-kompatibler Client)

### Setup

1. **Repository klonen oder Dateien herunterladen**

```bash
cd ~/fyta-mcp-server
```

2. **Virtuelle Umgebung erstellen (optional aber empfohlen)**

```bash
python3 -m venv venv
source venv/bin/activate  # Auf Windows: venv\Scripts\activate
```

3. **Dependencies installieren**

```bash
pip install -r requirements.txt
```

4. **Umgebungsvariablen setzen**

Erstelle eine `.env` Datei:

```bash
cp .env.example .env
```

Und trage deine FYTA-Zugangsdaten ein:

```env
FYTA_EMAIL=deine-email@example.com
FYTA_PASSWORD=dein-passwort
```

**Wichtig**: Die `.env` Datei sollte NIEMALS in Git committed werden!

## Konfiguration für Claude Desktop

Füge folgendes zu deiner Claude Desktop Konfiguration hinzu:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "fyta": {
      "command": "python",
      "args": [
        "/absoluter/pfad/zu/fyta-mcp-server/server.py"
      ],
      "env": {
        "FYTA_EMAIL": "deine-email@example.com",
        "FYTA_PASSWORD": "dein-passwort"
      }
    }
  }
}
```

Oder mit uv (empfohlen):

```json
{
  "mcpServers": {
    "fyta": {
      "command": "uv",
      "args": [
        "--directory",
        "/absoluter/pfad/zu/fyta-mcp-server",
        "run",
        "server.py"
      ],
      "env": {
        "FYTA_EMAIL": "deine-email@example.com",
        "FYTA_PASSWORD": "dein-passwort"
      }
    }
  }
}
```

## Verwendung

Nach dem Neustart von Claude Desktop stehen dir folgende Tools zur Verfügung:

### 1. Alle Pflanzen abrufen

```
Zeig mir alle meine Pflanzen
```

### 2. Details zu einer bestimmten Pflanze

```
Zeig mir Details zu Pflanze mit ID 123
```

### 3. Pflanzen, die Aufmerksamkeit brauchen

```
Welche meiner Pflanzen brauchen gerade Pflege?
```

### 4. Garten-Übersicht

```
Gib mir eine Übersicht über meine Gärten
```

## API Endpoints

Der Server nutzt folgende FYTA API Endpoints:

- `POST https://web.fyta.de/api/auth/login` - Authentifizierung
- `GET https://web.fyta.de/api/user-plant` - Pflanzendaten abrufen

## Statuswerte

Die Sensoren geben folgende Statuswerte zurück:

- **1** = Zu niedrig (Low)
- **2** = Optimal
- **3** = Zu hoch (High)

Dies gilt für:
- Temperatur (`temperature_status`)
- Licht (`light_status`)
- Bodenfeuchtigkeit (`moisture_status`)
- Nährstoffe/Salzgehalt (`salinity_status`)

## Troubleshooting

### Server startet nicht

1. Überprüfe, ob die Umgebungsvariablen korrekt gesetzt sind
2. Teste die Authentifizierung:

```bash
python -c "
import asyncio
import os
from server import FytaClient

async def test():
    client = FytaClient(os.getenv('FYTA_EMAIL'), os.getenv('FYTA_PASSWORD'))
    result = await client.authenticate()
    print(f'Auth result: {result}')
    await client.close()

asyncio.run(test())
"
```

### Keine Daten verfügbar

- Stelle sicher, dass du einen FYTA Hub oder die mobile App als Gateway verwendest
- Die FYTA Beam Sensoren senden nur Rohdaten, die vom Server verarbeitet werden müssen
- Überprüfe in der FYTA App, ob deine Sensoren verbunden sind

## Entwicklung

### Weitere Endpoints hinzufügen

Du kannst weitere Tools hinzufügen, indem du:

1. Ein neues Tool in der `list_tools()` Funktion definierst
2. Die Logik in der `call_tool()` Funktion implementierst

### API Dokumentation

Die vollständige FYTA API Dokumentation findest du hier:
https://fyta-io.notion.site/FYTA-Public-API-d2f4c30306f74504924c9a40402a3afd

## Credits

- FYTA API: https://fyta.de/
- Basiert auf dem Python Client: https://github.com/dontinelli/fyta_cli
- Home Assistant Integration: https://github.com/dontinelli/fyta-custom_component

## Lizenz

GPL-3.0 (kompatibel mit dem fyta_cli Projekt)

## Support

Bei Fragen oder Problemen:
- Öffne ein Issue auf GitHub
- Schau in die FYTA Developer Community auf Discord
- Besuche https://fyta.de/ für mehr Infos zu den Sensoren

---

Viel Spaß beim Pflanzen-Monitoring mit Claude! 🌿🤖
