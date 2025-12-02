#!/bin/bash
# Command: Set target heading (0-360 degrees)
# NOTE: This clears any waypoint navigation - aircraft will fly this heading

CALLSIGN="${1:-UAL123}"
HEADING="${2:-270}"

curl -s -X POST "http://localhost:8000/api/flights/${CALLSIGN}/command" \
  -H "Content-Type: application/json" \
  -d "{\"heading\": ${HEADING}}" | python -m json.tool

# Example: ./13_command_set_heading.sh UAL123 340

