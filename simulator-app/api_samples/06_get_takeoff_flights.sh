#!/bin/bash
# Get flights ready for takeoff
# Returns: Flights with status: ready_for_takeoff or taking_off

curl -s http://localhost:8000/api/flights/takeoff | python -m json.tool

