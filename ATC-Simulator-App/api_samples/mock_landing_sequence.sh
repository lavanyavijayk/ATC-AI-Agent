#!/bin/bash
# Mock Landing Sequence - Demonstrates complete aircraft landing flow
# This script spawns an aircraft and guides it through the full landing pattern

BASE_URL="http://localhost:8000/api"

echo "=========================================="
echo "  AI-ATC Mock Landing Sequence"
echo "=========================================="
echo ""

# Step 1: Spawn an arrival
echo "Step 1: Spawning arrival aircraft..."
SPAWN_RESULT=$(curl -s -X POST "$BASE_URL/simulation/spawn/arrival")
echo "$SPAWN_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  Aircraft: {d[\"callsign\"]} ({d[\"aircraft_type\"]})')"
CALLSIGN=$(echo "$SPAWN_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['callsign'])")
echo "  Callsign: $CALLSIGN"
echo ""

sleep 2

# Step 2: Get initial flight status
echo "Step 2: Getting initial flight status..."
curl -s "$BASE_URL/flights/$CALLSIGN" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'  Position: ({d[\"position\"][\"x\"]:.1f}, {d[\"position\"][\"y\"]:.1f}) nm')
print(f'  Altitude: {d[\"altitude\"]:.0f} ft')
print(f'  Speed: {d[\"speed\"]:.0f} kt')
print(f'  Heading: {d[\"heading\"]:.0f}°')
print(f'  Status: {d[\"status\"]}')
print(f'  Target WPT: {d[\"target_waypoint\"]}')
"
echo ""

sleep 2

# Step 3: Direct to DOWNWIND
echo "Step 3: Directing to DOWNWIND waypoint..."
curl -s -X POST "$BASE_URL/flights/$CALLSIGN/command" \
  -H "Content-Type: application/json" \
  -d '{"waypoint": "DOWNWIND", "altitude": 2000, "speed": 200}' | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'  Command: {d[\"command\"]}')
print(f'  Result: {d[\"result\"][\"message\"]}')
"
echo ""

sleep 3

# Step 4: Check status after DOWNWIND command
echo "Step 4: Flight status (heading to DOWNWIND)..."
curl -s "$BASE_URL/flights/$CALLSIGN" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'  Position: ({d[\"position\"][\"x\"]:.1f}, {d[\"position\"][\"y\"]:.1f}) nm')
print(f'  Altitude: {d[\"altitude\"]:.0f} ft')
print(f'  Speed: {d[\"speed\"]:.0f} kt')
print(f'  Heading: {d[\"heading\"]:.0f}°')
print(f'  Target WPT: {d[\"target_waypoint\"]}')
print(f'  Passed WPTs: {d[\"passed_waypoints\"]}')
"
echo ""

sleep 2

# Step 5: Direct to BASE
echo "Step 5: Directing to BASE waypoint..."
curl -s -X POST "$BASE_URL/flights/$CALLSIGN/command" \
  -H "Content-Type: application/json" \
  -d '{"waypoint": "BASE", "altitude": 1500, "speed": 160}' | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'  Command: {d[\"command\"]}')
print(f'  Result: {d[\"result\"][\"message\"]}')
"
echo ""

sleep 3

# Step 6: Direct to FINAL
echo "Step 6: Directing to FINAL waypoint..."
curl -s -X POST "$BASE_URL/flights/$CALLSIGN/command" \
  -H "Content-Type: application/json" \
  -d '{"waypoint": "FINAL", "altitude": 1000, "speed": 140}' | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'  Command: {d[\"command\"]}')
print(f'  Result: {d[\"result\"][\"message\"]}')
"
echo ""

sleep 3

# Step 7: Check status before landing clearance
echo "Step 7: Flight status (on approach)..."
curl -s "$BASE_URL/flights/$CALLSIGN" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'  Position: ({d[\"position\"][\"x\"]:.1f}, {d[\"position\"][\"y\"]:.1f}) nm')
print(f'  Altitude: {d[\"altitude\"]:.0f} ft')
print(f'  Speed: {d[\"speed\"]:.0f} kt')
print(f'  Heading: {d[\"heading\"]:.0f}°')
print(f'  Status: {d[\"status\"]}')
print(f'  Passed WPTs: {d[\"passed_waypoints\"]}')
"
echo ""

sleep 2

# Step 8: Clear to land
echo "Step 8: Clearing for landing..."
LAND_RESULT=$(curl -s -X POST "$BASE_URL/flights/$CALLSIGN/command" \
  -H "Content-Type: application/json" \
  -d '{"clear_to_land": true}')
echo "$LAND_RESULT" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'  Status: {d[\"status\"]}')
print(f'  Result: {d[\"result\"][\"message\"]}')
if d['result'].get('success') == False:
    print(f'  ⚠️  Landing denied! Waiting for conditions to be met...')
"
echo ""

# If landing was denied, keep trying
CLEARED=$(echo "$LAND_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['result'].get('success', False))")
RETRIES=0
while [ "$CLEARED" != "True" ] && [ $RETRIES -lt 10 ]; do
    sleep 3
    echo "  Retrying landing clearance (attempt $((RETRIES+2)))..."
    LAND_RESULT=$(curl -s -X POST "$BASE_URL/flights/$CALLSIGN/command" \
      -H "Content-Type: application/json" \
      -d '{"clear_to_land": true}')
    CLEARED=$(echo "$LAND_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['result'].get('success', False))")
    echo "$LAND_RESULT" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'    Result: {d[\"result\"][\"message\"]}')
"
    RETRIES=$((RETRIES+1))
done

if [ "$CLEARED" == "True" ]; then
    echo "  ✅ Aircraft cleared to land!"
fi
echo ""

# Step 9: Monitor landing
echo "Step 9: Monitoring landing progress..."
for i in {1..10}; do
    sleep 2
    STATUS=$(curl -s "$BASE_URL/flights/$CALLSIGN" 2>/dev/null)
    if [ -z "$STATUS" ] || [ "$STATUS" == "null" ]; then
        echo "  ✅ Aircraft has landed and cleared the runway!"
        break
    fi
    echo "$STATUS" | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    dist = (d['position']['x']**2 + d['position']['y']**2)**0.5
    print(f'  [{$i}/10] Status: {d[\"status\"]} | Alt: {d[\"altitude\"]:.0f}ft | Dist: {dist:.2f}nm')
except:
    print('  Aircraft no longer in system')
"
done

echo ""
echo "=========================================="
echo "  Landing Sequence Complete!"
echo "=========================================="

# Final stats
echo ""
echo "Final simulation stats:"
curl -s "$BASE_URL/simulation/status" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'  Landed: {d[\"landed\"]}')
print(f'  Departed: {d[\"departed\"]}')
print(f'  Near Misses: {d[\"near_misses\"]}')
"

