<?php
/**
 * FYTA MCP Server Integration for IP-Symcon
 * Script: FYTA_WebFront
 *
 * Display FYTA data in WebFront
 * This script should be embedded in a WebFront page
 */

// Style
echo "<style>
.fyta-container { font-family: Arial, sans-serif; }
.fyta-header { background: #4CAF50; color: white; padding: 15px; border-radius: 5px; }
.fyta-summary { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
.fyta-alert { background: #ffebee; border-left: 4px solid #f44336; padding: 10px; margin: 10px 0; }
.fyta-ok { background: #e8f5e9; border-left: 4px solid #4CAF50; padding: 10px; margin: 10px 0; }
.fyta-plant { background: white; padding: 15px; margin: 10px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.fyta-metric { display: inline-block; margin: 5px 10px; }
.fyta-status-ok { color: #4CAF50; }
.fyta-status-warning { color: #FF9800; }
.fyta-status-critical { color: #f44336; }
</style>";

echo "<div class='fyta-container'>";

// Header
echo "<div class='fyta-header'>";
echo "<h2>🌱 FYTA Pflanzen-Monitor</h2>";
echo "</div>";

// Get event summary
$rootId = IPS_GetObject(0)['ObjectID'];
$eventsCategoryId = @IPS_GetObjectIDByIdent("FYTA_Events", $rootId);

if ($eventsCategoryId !== false) {
    $eventCount = GetValue(IPS_GetObjectIDByIdent("EventCount", $eventsCategoryId));
    $criticalCount = GetValue(IPS_GetObjectIDByIdent("CriticalCount", $eventsCategoryId));
    $warningCount = GetValue(IPS_GetObjectIDByIdent("WarningCount", $eventsCategoryId));
    $lastCheck = GetValue(IPS_GetObjectIDByIdent("Last_Check", $eventsCategoryId));

    // Summary
    $bgClass = $criticalCount > 0 ? "fyta-alert" : "fyta-ok";
    echo "<div class='$bgClass'>";
    echo "<strong>Status:</strong> ";
    if ($eventCount == 0) {
        echo "✓ Alle Pflanzen sind gesund";
    } else {
        echo "⚠️ $eventCount Ereignis(se) aktiv";
        if ($criticalCount > 0) {
            echo " ($criticalCount kritisch!)";
        }
    }
    echo "<br><small>Letzte Prüfung: $lastCheck</small>";
    echo "</div>";

    // Event list
    if ($eventCount > 0) {
        $eventList = GetValue(IPS_GetObjectIDByIdent("EventList", $eventsCategoryId));
        if (!empty($eventList)) {
            echo "<div class='fyta-summary'>";
            echo "<h3>⚠️ Aktive Warnungen</h3>";
            echo "<pre>" . htmlspecialchars($eventList) . "</pre>";
            echo "</div>";
        }
    }
}

// Plant list
echo "<h3>Alle Pflanzen</h3>";

$allObjects = IPS_GetChildrenIDs($rootId);
foreach ($allObjects as $objectId) {
    $obj = IPS_GetObject($objectId);

    // Check if it's a plant category
    if ($obj['ObjectType'] == 0 && strpos($obj['ObjectIdent'], 'FYTA_Plant_') === 0) {
        $plantName = $obj['ObjectName'];
        $plantId = str_replace('FYTA_Plant_', '', $obj['ObjectIdent']);

        // Get values
        $temp = @GetValue(IPS_GetObjectIDByIdent("Temperature", $objectId));
        $moisture = @GetValue(IPS_GetObjectIDByIdent("Moisture", $objectId));
        $light = @GetValue(IPS_GetObjectIDByIdent("Light", $objectId));
        $nutrients = @GetValue(IPS_GetObjectIDByIdent("Nutrients", $objectId));
        $status = @GetValue(IPS_GetObjectIDByIdent("Status", $objectId));
        $lastUpdate = @GetValue(IPS_GetObjectIDByIdent("Last_Update", $objectId));

        // Status colors
        $statusClass = "fyta-status-ok";
        if (strpos($status, "niedrig") !== false || strpos($status, "hoch") !== false) {
            $statusClass = "fyta-status-warning";
        }
        if (strpos($status, "Kritisch") !== false) {
            $statusClass = "fyta-status-critical";
        }

        // Display plant card
        echo "<div class='fyta-plant'>";
        echo "<h4>$plantName <span class='$statusClass'>($status)</span></h4>";

        echo "<div class='fyta-metric'>";
        echo "🌡️ <strong>Temperatur:</strong> " . number_format($temp, 1) . "°C";
        echo "</div>";

        echo "<div class='fyta-metric'>";
        echo "💧 <strong>Feuchtigkeit:</strong> " . number_format($moisture, 0) . "%";
        echo "</div>";

        echo "<div class='fyta-metric'>";
        echo "☀️ <strong>Licht:</strong> " . number_format($light, 0) . " µmol";
        echo "</div>";

        echo "<div class='fyta-metric'>";
        echo "🌿 <strong>Nährstoffe:</strong> " . number_format($nutrients, 2);
        echo "</div>";

        echo "<br><small>Aktualisiert: $lastUpdate</small>";
        echo "</div>";
    }
}

echo "</div>"; // fyta-container

?>
