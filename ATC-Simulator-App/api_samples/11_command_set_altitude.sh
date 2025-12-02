#!/bin/bash
# Command: Set target altitude
# Aircraft will climb or descend to reach this altitude

CALLSIGN="${1:-UAL123}"
ALTITUDE="${2:-3000}"

curl -s -X POST "http://localhost:8000/api/flights/${CALLSIGN}/command" \
  -H "Content-Type: application/json" \
  -d "{\"altitude\": ${ALTITUDE}}" | python -m json.tool

# Example: ./11_command_set_altitude.sh UAL123 5000

