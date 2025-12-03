#!/bin/bash
# Full approach sequence example
# This script demonstrates vectoring an aircraft for landing

CALLSIGN="${1:-UAL123}"

echo "=== Full Approach Sequence for ${CALLSIGN} ==="
echo ""

echo "Step 1: Direct to DOWNWIND at 2000ft, 200kt"
curl -s -X POST "http://localhost:8000/api/flights/${CALLSIGN}/command" \
  -H "Content-Type: application/json" \
  -d '{"waypoint": "DOWNWIND", "altitude": 2000, "speed": 200}' | python -m json.tool
sleep 2

echo ""
echo "Step 2: Direct to BASE at 1500ft, 160kt"
curl -s -X POST "http://localhost:8000/api/flights/${CALLSIGN}/command" \
  -H "Content-Type: application/json" \
  -d '{"waypoint": "BASE", "altitude": 1500, "speed": 160}' | python -m json.tool
sleep 2

echo ""
echo "Step 3: Direct to FINAL at 1000ft, 140kt"
curl -s -X POST "http://localhost:8000/api/flights/${CALLSIGN}/command" \
  -H "Content-Type: application/json" \
  -d '{"waypoint": "FINAL", "altitude": 1000, "speed": 140}' | python -m json.tool
sleep 2

echo ""
echo "Step 4: Attempt to clear for landing"
curl -s -X POST "http://localhost:8000/api/flights/${CALLSIGN}/command" \
  -H "Content-Type: application/json" \
  -d '{"clear_to_land": true}' | python -m json.tool

echo ""
echo "=== Sequence Complete ==="

