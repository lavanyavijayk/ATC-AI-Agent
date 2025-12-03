#!/bin/bash
# Command: Direct to waypoint
# Aircraft will navigate directly to the specified waypoint
# Available waypoints: NORTH, SOUTH, EAST, WEST, DOWNWIND, BASE, FINAL

CALLSIGN="${1:-UAL123}"
WAYPOINT="${2:-FINAL}"

curl -s -X POST "http://localhost:8000/api/flights/${CALLSIGN}/command" \
  -H "Content-Type: application/json" \
  -d "{\"waypoint\": \"${WAYPOINT}\"}" | python -m json.tool

# Example: ./14_command_direct_to_waypoint.sh UAL123 FINAL

