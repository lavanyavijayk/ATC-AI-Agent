#!/bin/bash
# Spawn a new departure flight
# Creates outbound flight at gate

curl -s -X POST http://localhost:8000/api/simulation/spawn/departure | python -m json.tool

