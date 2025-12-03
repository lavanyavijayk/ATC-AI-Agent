#!/bin/bash
# Get airport information
# Returns: icao, name, elevation, runway, runway_heading, runway_length

curl -s http://localhost:8000/api/airport | python -m json.tool

