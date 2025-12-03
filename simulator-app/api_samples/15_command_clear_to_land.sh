#!/bin/bash
# Command: Clear for landing
# Will fail if landing rules are not met:
#   - Altitude must be < 1500 ft
#   - Speed must be 100-180 kt
#   - Distance must be < 8 nm from runway
#   - Must have passed FINAL waypoint
#   - Heading must be within ±30° of runway (340°)

CALLSIGN="${1:-UAL123}"

curl -s -X POST "http://localhost:8000/api/flights/${CALLSIGN}/command" \
  -H "Content-Type: application/json" \
  -d '{"clear_to_land": true}' | python -m json.tool

# Example: ./15_command_clear_to_land.sh UAL123

