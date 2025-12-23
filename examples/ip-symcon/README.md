# IP-Symcon Integration Examples

## Files

- `FYTA_UpdateData.php` - Main script to fetch and update plant data
- `FYTA_WaterReminder.php` - Check for watering needs and trigger reminders
- `FYTA_WebFront.php` - WebFront visualization script

## Prerequisites

1. IP-Symcon 5.0 or higher
2. FYTA API Wrapper running (see root examples/)
3. PHP curl extension enabled

## Setup

### 1. Start API Wrapper

```bash
cd /path/to/fyta-mcp-server
python examples/api_wrapper.py
```

Verify it's working:
```bash
curl http://localhost:5000/health
```

### 2. Import Scripts to IP-Symcon

#### Option A: Via Console (recommended)

1. Open IP-Symcon Console
2. Right-click on "Scripts" → "Add Script"
3. Name: "FYTA_UpdateData"
4. Copy content from `FYTA_UpdateData.php`
5. Click "Apply" and note the Script ID

Repeat for:
- `FYTA_WaterReminder.php`
- `FYTA_WebFront.php`

#### Option B: Via File System

```bash
# Copy scripts to IP-Symcon directory
cp FYTA_UpdateData.php /var/lib/symcon/scripts/
cp FYTA_WaterReminder.php /var/lib/symcon/scripts/
cp FYTA_WebFront.php /var/lib/symcon/scripts/
```

### 3. Create Event for Automatic Updates

Create a new event:

1. Console → "Events" → Add Event
2. Type: "Cyclic"
3. Name: "FYTA Auto Update"
4. Trigger: Every 5 minutes
5. Action: Execute Script → Select "FYTA_UpdateData"

Or via PHP:

```php
<?php
// Create event for automatic updates
$eventId = IPS_CreateEvent(1); // Cyclic event
IPS_SetName($eventId, "FYTA Auto Update");
IPS_SetEventCyclic($eventId, 0, 0, 0, 0, 1, 5); // Every 5 minutes
IPS_SetEventActive($eventId, true);
IPS_SetParent($eventId, 0);
IPS_SetEventScript($eventId, 12345); // Replace with your FYTA_UpdateData script ID
?>
```

### 4. Test Scripts

#### Test Update Script

Console → Scripts → FYTA_UpdateData → Run

Expected output:
```
=== FYTA Update Started ===
Time: 2025-12-23 22:00:00

✓ Plant data updated successfully (2 plants)

✓ Events updated successfully (0 events)

=== FYTA Update Completed ===
```

Check Console → Object Tree:
- Should see "FYTA_Plant_108009" category
- With variables: Temperature, Moisture, Light, Nutrients, Status

#### Test Water Reminder

Console → Scripts → FYTA_WaterReminder → Run

### 5. Add WebFront Visualization

1. Open WebFront Editor
2. Create new page: "Pflanzen"
3. Add "PHP Script" element
4. Select "FYTA_WebFront" script
5. Save and view in WebFront

## Created Structure

After running the update script, you'll have:

```
├── FYTA_Plant_108009 (Epipremnum aureum)
│   ├── Temperature (Float)
│   ├── Moisture (Float)
│   ├── Light (Float)
│   ├── Nutrients (Float)
│   ├── Temperature_Status (Integer)
│   ├── Moisture_Status (Integer)
│   ├── Light_Status (Integer)
│   ├── Nutrients_Status (Integer)
│   ├── Status (String)
│   └── Last_Update (String)
├── FYTA_Plant_108010 (Epipremnum pinnatum)
│   └── ...
├── FYTA_Events
│   ├── EventCount (Integer)
│   ├── CriticalCount (Integer)
│   ├── WarningCount (Integer)
│   ├── EventList (String)
│   └── Last_Check (String)
└── FYTA_Reminders (created by WaterReminder)
    ├── Water_108009 (Boolean)
    └── Water_108010 (Boolean)
```

## Automations

### Create Watering Alert

```php
<?php
// Script: FYTA_Check_And_Alert
// Run this hourly via event

// Get critical count
$eventsId = IPS_GetObjectIDByIdent("FYTA_Events", 0);
$criticalCount = GetValue(IPS_GetObjectIDByIdent("CriticalCount", $eventsId));

if ($criticalCount > 0) {
    // Get event list
    $eventList = GetValue(IPS_GetObjectIDByIdent("EventList", $eventsId));

    // Send notification
    WFC_SendNotification(
        12345, // Your WebFront ID
        "FYTA Alarm",
        "🚨 $criticalCount kritische Ereignisse:\n\n$eventList",
        "alarm",
        0
    );
}
?>
```

### Auto-Water with Smart Valve

```php
<?php
// Script: FYTA_Auto_Water_Plant_1
// Triggered by moisture critical event

$plantId = 108009;
$valveVariableId = 54321; // Your valve switch variable ID

// Check if plant needs water
$eventsId = IPS_GetObjectIDByIdent("FYTA_Events", 0);
$eventList = GetValue(IPS_GetObjectIDByIdent("EventList", $eventsId));

if (strpos($eventList, "Epipremnum aureum") !== false &&
    strpos($eventList, "moisture") !== false) {

    // Open valve
    SetValue($valveVariableId, true);
    IPS_LogMessage("FYTA AutoWater", "Watering plant $plantId");

    // Wait 30 seconds
    IPS_Sleep(30000);

    // Close valve
    SetValue($valveVariableId, false);
    IPS_LogMessage("FYTA AutoWater", "Watering completed for plant $plantId");
}
?>
```

### Daily Status Report Email

```php
<?php
// Script: FYTA_Daily_Report
// Run at 9:00 AM daily

$rootId = IPS_GetObject(0)['ObjectID'];
$plantCount = 0;
$issueCount = 0;
$message = "🌱 Täglicher Pflanzen-Bericht\n\n";

// Count plants and issues
$allObjects = IPS_GetChildrenIDs($rootId);
foreach ($allObjects as $objectId) {
    $obj = IPS_GetObject($objectId);
    if ($obj['ObjectType'] == 0 && strpos($obj['ObjectIdent'], 'FYTA_Plant_') === 0) {
        $plantCount++;
        $status = GetValue(IPS_GetObjectIDByIdent("Status", $objectId));
        if ($status != "Alles OK ✓") {
            $issueCount++;
            $message .= "⚠️ " . $obj['ObjectName'] . ": $status\n";
        }
    }
}

$message .= "\nGesamt: $plantCount Pflanzen\n";
if ($issueCount == 0) {
    $message .= "✓ Alle Pflanzen sind gesund!";
} else {
    $message .= "⚠️ $issueCount Pflanzen benötigen Aufmerksamkeit";
}

// Send email
SMTP_SendMailEx(
    12345, // Your SMTP Instance ID
    "your@email.com",
    "FYTA Tagesbericht",
    $message
);
?>
```

## Configuration

### API URL

If API is not on localhost, update in scripts:

```php
$apiUrl = "http://your-server-ip:5000/api";
```

### Update Interval

Change in event or script:

```php
$updateInterval = 300; // 5 minutes
```

### Notifications

#### Enable WebFront Notifications

```php
WFC_SendNotification(
    12345,          // WebFront Instance ID (find in Console)
    "Title",        // Notification title
    "Message",      // Notification message
    "icon",         // Icon: alarm, info, water, etc.
    0               // Duration (0 = until dismissed)
);
```

#### Enable Email Notifications

1. Setup SMTP instance in IP-Symcon
2. Use in scripts:

```php
SMTP_SendMailEx(
    12345,              // SMTP Instance ID
    "your@email.com",   // Recipient
    "Subject",          // Email subject
    "Message"           // Email body
);
```

## Troubleshooting

### Scripts Not Running

Check logs:
```
Console → Messages → Filter by "FYTA"
```

### No Data Received

Test API manually:
```bash
curl http://localhost:5000/api/plants
```

Check PHP curl:
```php
<?php
echo "Curl enabled: " . (function_exists('curl_init') ? "Yes" : "No");
?>
```

### Variables Not Created

Check permissions:
- IP-Symcon needs read/write access to object tree
- Scripts must run with admin privileges

### WebFront Not Showing Data

1. Clear WebFront cache
2. Refresh page
3. Check if script has errors (Console → Messages)

## Advanced: Create Custom Module

For better integration, create a custom IP-Symcon module:

1. Create directory: `/modules/FYTA/`
2. Create `module.json`:

```json
{
    "id": "{FYTA-0000-0000-0000-000000000001}",
    "name": "FYTA",
    "type": 3,
    "vendor": "FYTA",
    "aliases": ["FYTA Plant Monitor"],
    "parentRequirements": [],
    "childRequirements": [],
    "implemented": [],
    "prefix": "FYTA"
}
```

3. Create `module.php` with class FYTADevice

This allows native IP-Symcon integration with discovery and automatic updates.

## Support

For IP-Symcon specific issues:
- [IP-Symcon Forum](https://community.symcon.de/)
- [IP-Symcon Documentation](https://www.symcon.de/dokumentation/)

For FYTA integration issues:
- [GitHub Issues](https://github.com/schimmmi/fyta-mcp-server/issues)
