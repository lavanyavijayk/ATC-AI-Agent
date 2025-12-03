#!/bin/bash
# Command: Cancel landing clearance

CALLSIGN="${1:-UAL123}"

curl -s -X POST "http://localhost:8000/api/flights/${CALLSIGN}/command" \
  -H "Content-Type: application/json" \
  -d '{"clear_to_land": false}' | python -m json.tool

# Example: ./16_command_cancel_landing.sh UAL123

