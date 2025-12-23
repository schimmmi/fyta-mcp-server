# n8n Integration Examples

## Files

- `workflow_basic_monitoring.json` - Basic monitoring workflow with critical event notifications

## Setup

1. Start the API wrapper:
   ```bash
   cd /path/to/fyta-mcp-server
   python examples/api_wrapper.py
   ```

2. Import workflow to n8n:
   - Open n8n interface
   - Click "Import from File"
   - Select `workflow_basic_monitoring.json`

3. Configure credentials:
   - Add your Telegram bot credentials (or replace with email/Discord)
   - Update API URL if not running on localhost

4. Activate workflow

## Workflow Description

**Schedule Trigger** → **Get FYTA Events** → **Has Critical Events?** → **Send Notification**

- Runs every 5 minutes
- Fetches plant events from API
- Checks if any critical events exist
- Sends notification via Telegram

## Customization

### Change Notification Platform

Replace the "Send Notification" node with:
- **Email** - Use "Send Email" node
- **Discord** - Use "Discord" node with webhook
- **Slack** - Use "Slack" node
- **Push Notification** - Use "Pushover" or "Pushbullet"

### Add Database Logging

After "Get FYTA Events", add:
- **Postgres** node to store events in database
- **MySQL** node for MySQL database
- **MongoDB** node for document storage

### Per-Plant Monitoring

Add nodes:
1. HTTP Request: Get All Plants
2. Split In Batches
3. HTTP Request: Diagnose Each Plant
4. Filter: Only plants with issues
5. Send Notification
