# 📚 FYTA MCP Server - Dokumentation Übersicht

## 📁 Projekt-Struktur

```
fyta-mcp-server/
├── server.py              # Haupt-MCP-Server
├── test_connection.py     # Test-Script
├── requirements.txt       # Python Dependencies
├── pyproject.toml        # Package-Konfiguration
├── .env.example          # Beispiel-Umgebungsvariablen
├── .gitignore            # Git Ignore-Regeln
├── README.md             # Ausführliche Dokumentation
├── QUICKSTART.md         # Schnellstart-Anleitung
├── mcp_config_example.json # MCP-Konfigurations-Beispiel
└── OVERVIEW.md           # Diese Datei
```

## 🎯 Was macht dieser Server?

Der FYTA MCP Server ermöglicht es Claude, auf deine FYTA Pflanzensensor-Daten zuzugreifen. FYTA ist ein smartes System, das:

- 💧 **Bodenfeuchtigkeit** misst
- 🌡️ **Temperatur** überwacht
- ☀️ **Lichtverhältnisse** erfasst
- 🌱 **Nährstoffgehalt** (Salzgehalt) prüft

## 🛠️ Verfügbare Tools

### 1. `get_all_plants`
Holt alle deine Pflanzen mit kompletten Sensordaten.

**Beispiel**: "Zeig mir alle meine Pflanzen"

**Liefert**:
- Gesamtanzahl Pflanzen & Gärten
- Alle Pflanzendaten mit Status
- Sensor-Informationen
- Bilder

### 2. `get_plant_details`
Detaillierte Infos zu einer bestimmten Pflanze.

**Beispiel**: "Zeig mir Details zu Pflanze ID 123"

**Liefert**:
- Nickname & wissenschaftlicher Name
- Status-Übersicht (Temperatur, Licht, Feuchtigkeit, Nährstoffe)
- Optimale Stunden pro Tag
- Sensor-ID und WiFi-Status
- Bilder der Pflanze
- Letzte Datenaktualisierung

### 3. `get_plants_needing_attention`
Findet Pflanzen, die Pflege brauchen.

**Beispiel**: "Welche meiner Pflanzen brauchen Aufmerksamkeit?"

**Liefert**:
- Liste von Pflanzen mit Problemen
- Spezifische Issues (zu trocken, zu warm, zu dunkel, etc.)
- Priorisierte Handlungsempfehlungen

### 4. `get_garden_overview`
Organisierte Übersicht über deine Gärten.

**Beispiel**: "Zeig mir eine Übersicht meiner Gärten"

**Liefert**:
- Alle Gärten mit Anzahl Pflanzen
- Pflanzen pro Garten
- Status-Übersicht

## 📊 Status-Codes verstehen

Die FYTA API verwendet folgende Codes:

| Code | Bedeutung | Action |
|------|-----------|--------|
| **1** | Zu niedrig | Erhöhen (mehr Wasser, Licht, Wärme, Dünger) |
| **2** | Optimal ✅ | Alles gut! |
| **3** | Zu hoch | Reduzieren (weniger Wasser, Schatten, kühler, weniger Dünger) |

## 🔧 Setup-Varianten

### Option 1: Standard Python (Einfach)

```json
{
  "mcpServers": {
    "fyta": {
      "command": "python",
      "args": ["/pfad/zu/server.py"],
      "env": {
        "FYTA_EMAIL": "email@example.com",
        "FYTA_PASSWORD": "passwort"
      }
    }
  }
}
```

### Option 2: Mit UV (Empfohlen für Profis)

```json
{
  "mcpServers": {
    "fyta": {
      "command": "uv",
      "args": ["--directory", "/pfad/zu/fyta-mcp-server", "run", "server.py"],
      "env": {
        "FYTA_EMAIL": "email@example.com",
        "FYTA_PASSWORD": "passwort"
      }
    }
  }
}
```

### Option 3: Mit Virtual Environment

```json
{
  "mcpServers": {
    "fyta": {
      "command": "/pfad/zu/fyta-mcp-server/venv/bin/python",
      "args": ["/pfad/zu/fyta-mcp-server/server.py"],
      "env": {
        "FYTA_EMAIL": "email@example.com",
        "FYTA_PASSWORD": "passwort"
      }
    }
  }
}
```

## 💡 Beispiel-Konversationen

### Schneller Check

**Du**: "Wie geht's meinen Pflanzen?"

**Claude** (nutzt `get_all_plants`): "Du hast 5 Pflanzen in 2 Gärten. 4 davon sind in optimalem Zustand. Eine Pflanze braucht etwas Aufmerksamkeit..."

### Detaillierte Analyse

**Du**: "Was ist mit meiner Monstera los?"

**Claude** (nutzt `get_plants_needing_attention` und `get_plant_details`): "Deine Monstera (ID: 42) hat aktuell zu wenig Licht. Der Sensor zeigt, dass sie nur 2 Stunden optimales Licht am Tag bekommt. Empfehlung: Stelle sie näher ans Fenster oder nutze eine Pflanzenlampe."

### Garten-Management

**Du**: "Gib mir eine Übersicht meines Wohnzimmer-Gartens"

**Claude** (nutzt `get_garden_overview`): "Dein Wohnzimmer-Garten hat 3 Pflanzen: Monstera (optimal ✅), Ficus (braucht Wasser ⚠️), Philodendron (optimal ✅)..."

## 🔐 Sicherheit

**Wichtig**:
- Die `.env` Datei sollte NIEMALS in Git committed werden (ist in `.gitignore`)
- Deine Zugangsdaten werden nur lokal gespeichert
- Der Token läuft nach 60 Tagen ab und wird automatisch erneuert
- Nutze die gleichen Zugangsdaten wie für die FYTA App

## 🐛 Debugging

### Logs aktivieren

Setze `logging.INFO` auf `logging.DEBUG` in `server.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

### Test-Script nutzen

```bash
python test_connection.py
```

Zeigt dir:
- ✅/❌ Authentifizierung
- Anzahl Pflanzen & Gärten
- Status jeder Pflanze
- Problematische Pflanzen

### Claude Desktop Logs

**macOS**: `~/Library/Logs/Claude/mcp*.log`
**Windows**: `%APPDATA%\Claude\Logs\mcp*.log`

## 📖 Weiterführende Links

- **FYTA Website**: https://fyta.de/
- **FYTA API Docs**: https://fyta-io.notion.site/FYTA-Public-API-d2f4c30306f74504924c9a40402a3afd
- **Python Client**: https://github.com/dontinelli/fyta_cli
- **Home Assistant Integration**: https://github.com/dontinelli/fyta-custom_component
- **MCP Dokumentation**: https://modelcontextprotocol.io/

## 🤝 Contributing

Ideen für neue Features:

- 📈 Historische Datenanalyse
- 📸 Bilder-Download
- 🔔 Benachrichtigungen bei kritischen Zuständen
- 📊 Trend-Analysen
- 🌍 Multi-Sprachen-Support

## ⚖️ Lizenz

GPL-3.0 (kompatibel mit dem fyta_cli Projekt)

---

**Made with 🌿 for happy plants!**
