# 🚀 FYTA MCP Server - Quick Start

## In 5 Minuten startklar!

### 1️⃣ Dependencies installieren

```bash
cd ~/fyta-mcp-server
pip install -r requirements.txt
```

### 2️⃣ Zugangsdaten konfigurieren

Erstelle eine `.env` Datei:

```bash
cp .env.example .env
```

Editiere die `.env` und trage deine FYTA-Zugangsdaten ein:

```env
FYTA_EMAIL=deine-email@example.com
FYTA_PASSWORD=dein-passwort
```

### 3️⃣ Verbindung testen

```bash
python test_connection.py
```

Du solltest eine Ausgabe wie diese sehen:

```
🌱 FYTA MCP Server Test
==================================================
📧 Email: deine-email@example.com

🔐 Teste Authentifizierung...
✅ Authentifizierung erfolgreich!
   Token läuft ab am: 2025-02-11 12:34:56

🌿 Hole Pflanzendaten...
✅ 5 Pflanzen gefunden
✅ 2 Gärten gefunden
```

### 4️⃣ Claude Desktop konfigurieren

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Füge hinzu:

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

**Wichtig**: Ersetze `/absoluter/pfad/zu/fyta-mcp-server` mit dem echten Pfad!

Auf macOS/Linux findest du den Pfad mit:
```bash
cd ~/fyta-mcp-server && pwd
```

### 5️⃣ Claude Desktop neu starten

Schließe Claude Desktop komplett und starte es neu.

### 6️⃣ Testen in Claude

Frag Claude einfach:

```
Zeig mir alle meine Pflanzen
```

Oder:

```
Welche meiner Pflanzen brauchen gerade Pflege?
```

## 🎉 Fertig!

Du kannst jetzt über Claude mit deinen Pflanzen sprechen! 🌿

---

## Troubleshooting

### "Module mcp not found"

```bash
pip install mcp
```

### "Authentication failed"

Überprüfe deine Zugangsdaten in der `.env` Datei. Teste mit:

```bash
python test_connection.py
```

### MCP Server erscheint nicht in Claude

1. Überprüfe die Konfigurationsdatei auf Syntax-Fehler
2. Stelle sicher, dass der Pfad absolut ist (z.B. `/home/user/...` statt `~/...`)
3. Starte Claude Desktop komplett neu
4. Schau in die Claude Desktop Logs (macOS: `~/Library/Logs/Claude/`)

---

Viel Erfolg! 🚀
