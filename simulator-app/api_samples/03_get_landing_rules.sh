#!/bin/bash
# Get landing clearance rules
# Returns: max_altitude, min_speed, max_speed, max_distance, required_waypoint, aligned_heading_tolerance

curl -s http://localhost:8000/api/landing-rules | python -m json.tool

