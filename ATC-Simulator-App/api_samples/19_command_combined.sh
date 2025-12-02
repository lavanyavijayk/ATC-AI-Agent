#!/bin/bash
# Command: Combined - Multiple parameters at once
# You can combine altitude, speed, and waypoint in a single command

CALLSIGN="${1:-UAL123}"

# Example: Direct to FINAL at 1000ft and 140kt
curl -s -X POST "http://localhost:8000/api/flights/${CALLSIGN}/command" \
  -H "Content-Type: application/json" \
  -d '{
    "waypoint": "FINAL",
    "altitude": 1000,
    "speed": 140
  }' | python -m json.tool

# Example: ./19_command_combined.sh UAL123

