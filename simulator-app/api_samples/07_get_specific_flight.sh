#!/bin/bash
# Get details for a specific flight
# Replace CALLSIGN with actual callsign (e.g., UAL123)

CALLSIGN="${1:-UAL123}"

curl -s "http://localhost:8000/api/flights/${CALLSIGN}" | python -m json.tool

