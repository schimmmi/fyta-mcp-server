<?php
/**
 * FYTA MCP Server Integration for IP-Symcon
 * Script: FYTA_WaterReminder
 *
 * Checks for plants needing water and triggers reminders/actions
 */

// Configuration
$apiUrl = "http://localhost:5000/api";

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
        return false;
    }

    return json_decode($response, true);
}

/**
 * Check for watering needs
 */
function CheckWateringNeeds() {
    $events = FetchFYTAData("/events");

    if ($events === false) {
        echo "Error fetching events\n";
        return;
    }

    $wateringNeeded = [];

    // Find moisture critical events
    foreach ($events['events'] as $event) {
        if ($event['event_type'] == 'moisture_critical') {
            $wateringNeeded[] = $event;
        }
    }

    if (empty($wateringNeeded)) {
        echo "No plants need watering ✓\n";
        return;
    }

    // Plants need water!
    echo "💧 " . count($wateringNeeded) . " plant(s) need water:\n";

    foreach ($wateringNeeded as $event) {
        echo "  - " . $event['plant_name'] . "\n";

        // Trigger actions
        TriggerWateringAction($event['plant_id'], $event['plant_name']);
    }
}

/**
 * Trigger watering action
 */
function TriggerWateringAction($plantId, $plantName) {
    $message = "💧 Pflanze gießen: " . $plantName;

    // Option 1: Send push notification
    // WFC_SendNotification(12345, "Gießen!", $message, "water", 0);

    // Option 2: Send email
    // SMTP_SendMailEx(12345, "your@email.com", "FYTA: Pflanze gießen", $message);

    // Option 3: Trigger smart valve (if available)
    // Example: Open valve for plant 1
    // if ($plantId == 108009) {
    //     SetValue(54321, true);  // Open valve
    //     IPS_Sleep(30000);       // Wait 30 seconds
    //     SetValue(54321, false); // Close valve
    // }

    // Option 4: Set reminder variable
    $rootId = IPS_GetObject(0)['ObjectID'];
    $categoryId = @IPS_GetObjectIDByIdent("FYTA_Reminders", $rootId);
    if ($categoryId === false) {
        $categoryId = IPS_CreateCategory();
        IPS_SetParent($categoryId, $rootId);
        IPS_SetIdent($categoryId, "FYTA_Reminders");
        IPS_SetName($categoryId, "FYTA Erinnerungen");
    }

    $varId = @IPS_GetObjectIDByIdent("Water_" . $plantId, $categoryId);
    if ($varId === false) {
        $varId = IPS_CreateVariable(0); // Boolean
        IPS_SetParent($varId, $categoryId);
        IPS_SetIdent($varId, "Water_" . $plantId);
        IPS_SetName($varId, "Gießen: " . $plantName);
        IPS_SetIcon($varId, "Drops");
    }
    SetValue($varId, true);

    // For now, just log
    IPS_LogMessage("FYTA Watering", $message);
}

/**
 * Clear watering reminder (call this after watering)
 */
function ClearWateringReminder($plantId) {
    $rootId = IPS_GetObject(0)['ObjectID'];
    $categoryId = @IPS_GetObjectIDByIdent("FYTA_Reminders", $rootId);

    if ($categoryId !== false) {
        $varId = @IPS_GetObjectIDByIdent("Water_" . $plantId, $categoryId);
        if ($varId !== false) {
            SetValue($varId, false);
            echo "✓ Watering reminder cleared for plant $plantId\n";
        }
    }
}

// ============================================================================
// MAIN EXECUTION
// ============================================================================

echo "=== FYTA Water Check Started ===\n";
echo "Time: " . date('Y-m-d H:i:s') . "\n\n";

CheckWateringNeeds();

echo "\n=== FYTA Water Check Completed ===\n";

?>
