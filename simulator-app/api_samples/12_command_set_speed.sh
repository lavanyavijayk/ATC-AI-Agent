#!/bin/bash
# Command: Set target speed
# Aircraft will accelerate or decelerate to reach this speed

CALLSIGN="${1:-UAL123}"
SPEED="${2:-180}"

curl -s -X POST "http://localhost:8000/api/flights/${CALLSIGN}/command" \
  -H "Content-Type: application/json" \
  -d "{\"speed\": ${SPEED}}" | python -m json.tool

# Example: ./12_command_set_speed.sh UAL123 140

