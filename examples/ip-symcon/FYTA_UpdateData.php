<?php
/**
 * FYTA MCP Server Integration for IP-Symcon
 * Script: FYTA_UpdateData
 *
 * Updates plant data and events from FYTA API
 */

// Configuration
$apiUrl = "http://localhost:5000/api";
$updateInterval = 300; // 5 minutes in seconds

/**
 * Fetch data from FYTA API
 */
function FetchFYTAData($endpoint) {
    global $apiUrl;
    $url = $apiUrl . $endpoint;

    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 30);

    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($httpCode != 200) {
        echo "Error fetching data from $url (HTTP $httpCode)\n";
        return false;
    }

    return json_decode($response, true);
}

/**
 * Update plant data
 */
function UpdatePlantData() {
    $plants = FetchFYTAData("/plants");

    if ($plants === false) {
        echo "Error fetching plant data\n";
        return;
    }

    $rootId = IPS_GetObject(0)['ObjectID'];

    foreach ($plants['plants'] as $plant) {
        $plantId = $plant['id'];
        $plantName = $plant['nickname'];

        // Create or update category for this plant
        $categoryId = CreateCategoryByIdent($rootId, "FYTA_Plant_" . $plantId, $plantName);

        // Temperature
        $varId = CreateVariableByIdent($categoryId, "Temperature", 2); // Float
        SetValue($varId, $plant['temperature'] ?? 0);

        // Moisture
        $varId = CreateVariableByIdent($categoryId, "Moisture", 2);
        SetValue($varId, $plant['moisture'] ?? 0);

        // Light
        $varId = CreateVariableByIdent($categoryId, "Light", 2);
        SetValue($varId, $plant['light'] ?? 0);

        // Nutrients
        $varId = CreateVariableByIdent($categoryId, "Nutrients", 2);
        SetValue($varId, $plant['salinity'] ?? 0);

        // Status codes
        $varId = CreateVariableByIdent($categoryId, "Temperature_Status", 1); // Integer
        SetValue($varId, $plant['temperature_status'] ?? 2);

        $varId = CreateVariableByIdent($categoryId, "Moisture_Status", 1);
        SetValue($varId, $plant['moisture_status'] ?? 2);

        $varId = CreateVariableByIdent($categoryId, "Light_Status", 1);
        SetValue($varId, $plant['light_status'] ?? 2);

        $varId = CreateVariableByIdent($categoryId, "Nutrients_Status", 1);
        SetValue($varId, $plant['salinity_status'] ?? 2);

        // Overall status text
        $varId = CreateVariableByIdent($categoryId, "Status", 3); // String
        SetValue($varId, GetStatusText(
            $plant['temperature_status'] ?? 2,
            $plant['moisture_status'] ?? 2,
            $plant['light_status'] ?? 2,
            $plant['salinity_status'] ?? 2
        ));

        // Last update
        $varId = CreateVariableByIdent($categoryId, "Last_Update", 3);
        SetValue($varId, date('Y-m-d H:i:s'));
    }

    echo "✓ Plant data updated successfully (" . count($plants['plants']) . " plants)\n";
}

/**
 * Update events
 */
function UpdateEvents() {
    $events = FetchFYTAData("/events");

    if ($events === false) {
        echo "Error fetching events\n";
        return;
    }

    // Create events category
    $rootId = IPS_GetObject(0)['ObjectID'];
    $categoryId = CreateCategoryByIdent($rootId, "FYTA_Events", "FYTA Ereignisse");

    // Event count
    $varId = CreateVariableByIdent($categoryId, "EventCount", 1); // Integer
    SetValue($varId, $events['event_count']);

    // Critical count
    $varId = CreateVariableByIdent($categoryId, "CriticalCount", 1);
    SetValue($varId, $events['summary']['critical']);

    // Warning count
    $varId = CreateVariableByIdent($categoryId, "WarningCount", 1);
    SetValue($varId, $events['summary']['warning']);

    // Event list (as string)
    $eventList = "";
    foreach ($events['events'] as $event) {
        $eventList .= "[" . strtoupper($event['severity']) . "] ";
        $eventList .= $event['plant_name'] . ": " . $event['message'] . "\n";
    }
    $varId = CreateVariableByIdent($categoryId, "EventList", 3); // String
    SetValue($varId, $eventList);

    // Last check
    $varId = CreateVariableByIdent($categoryId, "Last_Check", 3);
    SetValue($varId, date('Y-m-d H:i:s'));

    echo "✓ Events updated successfully (" . $events['event_count'] . " events)\n";

    // Trigger alert if critical events
    if ($events['summary']['critical'] > 0) {
        TriggerCriticalAlert($events['events']);
    }
}

/**
 * Helper: Create category if not exists
 */
function CreateCategoryByIdent($parentId, $ident, $name) {
    $catId = @IPS_GetObjectIDByIdent($ident, $parentId);
    if ($catId === false) {
        $catId = IPS_CreateCategory();
        IPS_SetParent($catId, $parentId);
        IPS_SetIdent($catId, $ident);
        IPS_SetName($catId, $name);
        IPS_SetIcon($catId, "Flower");
    }
    return $catId;
}

/**
 * Helper: Create variable if not exists
 */
function CreateVariableByIdent($parentId, $ident, $type) {
    $varId = @IPS_GetObjectIDByIdent($ident, $parentId);
    if ($varId === false) {
        $varId = IPS_CreateVariable($type);
        IPS_SetParent($varId, $parentId);
        IPS_SetIdent($varId, $ident);
        IPS_SetName($varId, str_replace("_", " ", $ident));

        // Set appropriate icons
        switch ($ident) {
            case "Temperature":
                IPS_SetIcon($varId, "Temperature");
                break;
            case "Moisture":
                IPS_SetIcon($varId, "Drops");
                break;
            case "Light":
                IPS_SetIcon($varId, "Sun");
                break;
            case "Nutrients":
                IPS_SetIcon($varId, "Leaf");
                break;
        }
    }
    return $varId;
}

/**
 * Helper: Get status text
 */
function GetStatusText($temp, $moisture, $light, $nutrients) {
    $statusMap = [1 => "Zu niedrig", 2 => "Optimal", 3 => "Zu hoch"];

    $issues = [];
    if ($temp != 2) $issues[] = "Temperatur " . $statusMap[$temp];
    if ($moisture != 2) $issues[] = "Feuchtigkeit " . $statusMap[$moisture];
    if ($light != 2) $issues[] = "Licht " . $statusMap[$light];
    if ($nutrients != 2) $issues[] = "Nährstoffe " . $statusMap[$nutrients];

    return empty($issues) ? "Alles OK ✓" : implode(", ", $issues);
}

/**
 * Helper: Trigger alert
 */
function TriggerCriticalAlert($events) {
    echo "⚠️  CRITICAL ALERT: " . count($events) . " critical issues!\n";

    // Build message
    $message = "🚨 Pflanzen benötigen Aufmerksamkeit!\n\n";
    foreach ($events as $event) {
        if ($event['severity'] == 'critical') {
            $message .= "• " . $event['plant_name'] . ": " . $event['message'] . "\n";
        }
    }

    // Send WebFront notification (adjust WebFront ID)
    // WFC_SendNotification(12345, "FYTA Alarm", $message, "alarm", 0);

    // Alternative: Send email
    // SMTP_SendMailEx(12345, "your@email.com", "FYTA Critical Alert", $message);

    // Alternative: Trigger script
    // IPS_RunScript(54321); // Your notification script

    // For now, just log
    IPS_LogMessage("FYTA Alert", $message);
}

// ============================================================================
// MAIN EXECUTION
// ============================================================================

echo "=== FYTA Update Started ===\n";
echo "Time: " . date('Y-m-d H:i:s') . "\n\n";

UpdatePlantData();
echo "\n";
UpdateEvents();

echo "\n=== FYTA Update Completed ===\n";

?>
