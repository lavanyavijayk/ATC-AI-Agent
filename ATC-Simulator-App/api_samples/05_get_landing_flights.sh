#!/bin/bash
# Get flights approaching for landing
# Returns: Flights with status: approaching, on_final, or landing

curl -s http://localhost:8000/api/flights/landing | python -m json.tool

