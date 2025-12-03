#!/bin/bash
# Command: Cancel takeoff clearance

CALLSIGN="${1:-UAL123}"

curl -s -X POST "http://localhost:8000/api/flights/${CALLSIGN}/command" \
  -H "Content-Type: application/json" \
  -d '{"clear_for_takeoff": false}' | python -m json.tool

# Example: ./18_command_cancel_takeoff.sh DAL456

