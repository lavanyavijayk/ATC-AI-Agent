#!/bin/bash
# Command: Clear for takeoff
# Only works for departures with status "ready_for_takeoff"

CALLSIGN="${1:-UAL123}"

curl -s -X POST "http://localhost:8000/api/flights/${CALLSIGN}/command" \
  -H "Content-Type: application/json" \
  -d '{"clear_for_takeoff": true}' | python -m json.tool

# Example: ./17_command_clear_for_takeoff.sh DAL456

