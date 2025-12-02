#!/bin/bash
# Get all active flights
# Returns: List of all flights with full state

curl -s http://localhost:8000/api/flights | python -m json.tool

