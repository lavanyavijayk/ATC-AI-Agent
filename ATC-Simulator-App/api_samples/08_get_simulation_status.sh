#!/bin/bash
# Get simulation status and statistics
# Returns: running, total_flights, arrivals, departures

curl -s http://localhost:8000/api/simulation/status | python -m json.tool

