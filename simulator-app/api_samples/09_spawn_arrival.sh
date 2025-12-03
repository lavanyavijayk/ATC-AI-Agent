#!/bin/bash
# Spawn a new arrival flight
# Creates inbound flight at random entry waypoint (NORTH, SOUTH, EAST, or WEST)

curl -s -X POST http://localhost:8000/api/simulation/spawn/arrival | python -m json.tool

