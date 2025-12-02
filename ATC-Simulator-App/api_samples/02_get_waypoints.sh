#!/bin/bash
# Get all navigation waypoints
# Returns: Dictionary of waypoints with name, position, altitude_restriction, description

curl -s http://localhost:8000/api/waypoints | python -m json.tool

