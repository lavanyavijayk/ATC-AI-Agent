# Mock Landing Sequence - API Calls with JSON Responses

Complete example of landing an aircraft from spawn to touchdown.

---

## Step 1: Spawn Arrival

**Request:**
```bash
curl -X POST http://localhost:8000/api/simulation/spawn/arrival
```

**Response:**
```json
{
  "callsign": "UAL4527",
  "flight_type": "arrival",
  "status": "approaching",
  "position": {"x": 28.3, "y": 19.7},
  "altitude": 9500,
  "speed": 315,
  "heading": 225,
  "target_altitude": 6000,
  "target_speed": 250,
  "target_heading": 225,
  "target_waypoint": "NORTH",
  "aircraft_type": "B738",
  "origin": "KSEA",
  "destination": "KRNT",
  "cleared_to_land": false,
  "cleared_for_takeoff": false,
  "passed_waypoints": [],
  "clearance_denial_reason": null
}drink# Flight Status

**Request:**
```bash
curl http://localhost:8000/api/flights/UAL4527
```

**Response:**
```json
{
  "callsign": "UAL4527",
  "flight_type": "arrival",
  "status": "approaching",
  "position": {"x": 22.1, "y": 15.4},
  "altitude": 8200,
  "speed": 298,
  "heading": 218,
  "target_altitude": 6000,
  "target_speed": 250,
  "target_heading": 218,
  "target_waypoint": "NORTH",
  "aircraft_type": "B738",
  "origin": "KSEA",
  "destination": "KRNT",
  "cleared_to_land": false,
  "cleared_for_takeoff": false,
  "passed_waypoints": ["NORTH"],
  "clearance_denial_reason": null
}
```

---

## Step 3: Direct to DOWNWIND

**Request:**
```bash
curl -X POST http://localhost:8000/api/flights/UAL4527/command \
  -H "Content-Type: application/json" \
  -d '{"waypoint": "DOWNWIND", "altitude": 2000, "speed": 200}'
```

**Response:**
```json
{
  "status": "ok",
  "callsign": "UAL4527",
  "command": {
    "waypoint": "DOWNWIND",
    "altitude": 2000,
    "speed": 200
  },
  "result": {
    "success": true,
    "message": "Command accepted"
  }
}
```

---

## Step 4: Direct to BASE

**Request:**
```bash
curl -X POST http://localhost:8000/api/flights/UAL4527/command \
  -H "Content-Type: application/json" \
  -d '{"waypoint": "BASE", "altitude": 1500, "speed": 160}'
```

**Response:**
```json
{
  "status": "ok",
  "callsign": "UAL4527",
  "command": {
    "waypoint": "BASE",
    "altitude": 1500,
    "speed": 160
  },
  "result": {
    "success": true,
    "message": "Command accepted"
  }
}
```

---

## Step 5: Direct to FINAL

**Request:**
```bash
curl -X POST http://localhost:8000/api/flights/UAL4527/command \
  -H "Content-Type: application/json" \
  -d '{"waypoint": "FINAL", "altitude": 1000, "speed": 140}'
```

**Response:**
```json
{
  "status": "ok",
  "callsign": "UAL4527",
  "command": {
    "waypoint": "FINAL",
    "altitude": 1000,
    "speed": 140
  },
  "result": {
    "success": true,
    "message": "Command accepted"
  }
}
```

---

## Step 6: Check Status Before Landing (FINAL passed)

**Request:**
```bash
curl http://localhost:8000/api/flights/UAL4527
```

**Response:**
```json
{
  "callsign": "UAL4527",
  "flight_type": "arrival",
  "status": "on_final",
  "position": {"x": 0.2, "y": -10.5},
  "altitude": 1150,
  "speed": 142,
  "heading": 340,
  "target_altitude": 1000,
  "target_speed": 140,
  "target_heading": 340,
  "target_waypoint": null,
  "aircraft_type": "B738",
  "origin": "KSEA",
  "destination": "KRNT",
  "cleared_to_land": false,
  "cleared_for_takeoff": false,
  "passed_waypoints": ["NORTH", "DOWNWIND", "BASE", "FINAL"],
  "clearance_denial_reason": null
}
```

---

## Step 7a: Clear to Land - DENIED (altitude too high)

**Request:**
```bash
curl -X POST http://localhost:8000/api/flights/UAL4527/command \
  -H "Content-Type: application/json" \
  -d '{"clear_to_land": true}'
```

**Response (DENIED):**
```json
{
  "status": "error",
  "callsign": "UAL4527",
  "command": {
    "clear_to_land": true
  },
  "result": {
    "success": false,
    "message": "Cannot clear to land: Altitude 2500ft exceeds max 1500ft"
  }
}
```

---

## Step 7b: Clear to Land - DENIED (waypoint not passed)

**Response (DENIED):**
```json
{
  "status": "error",
  "callsign": "UAL4527",
  "command": {
    "clear_to_land": true
  },
  "result": {
    "success": false,
    "message": "Cannot clear to land: Must pass FINAL waypoint first"
  }
}
```

---

## Step 7c: Clear to Land - DENIED (heading not aligned)

**Response (DENIED):**
```json
{
  "status": "error",
  "callsign": "UAL4527",
  "command": {
    "clear_to_land": true
  },
  "result": {
    "success": false,
    "message": "Cannot clear to land: Heading 90° not aligned with runway 340°"
  }
}
```

---

## Step 7d: Clear to Land - SUCCESS

**Request:**
```bash
curl -X POST http://localhost:8000/api/flights/UAL4527/command \
  -H "Content-Type: application/json" \
  -d '{"clear_to_land": true}'
```

**Response (SUCCESS):**
```json
{
  "status": "ok",
  "callsign": "UAL4527",
  "command": {
    "clear_to_land": true
  },
  "result": {
    "success": true,
    "message": "Command accepted"
  }
}
```

---

## Step 8: Flight Status - LANDING

**Request:**
```bash
curl http://localhost:8000/api/flights/UAL4527
```

**Response:**
```json
{
  "callsign": "UAL4527",
  "flight_type": "arrival",
  "status": "landing",
  "position": {"x": 0.05, "y": -2.1},
  "altitude": 450,
  "speed": 138,
  "heading": 340,
  "target_altitude": 32,
  "target_speed": 140,
  "target_heading": 340,
  "target_waypoint": "RUNWAY",
  "aircraft_type": "B738",
  "origin": "KSEA",
  "destination": "KRNT",
  "cleared_to_land": true,
  "cleared_for_takeoff": false,
  "passed_waypoints": ["NORTH", "DOWNWIND", "BASE", "FINAL"],
  "clearance_denial_reason": null
}
```

---

## Step 9: Flight Status - LANDED

**Request:**
```bash
curl http://localhost:8000/api/flights/UAL4527
```

**Response:**
```json
{
  "callsign": "UAL4527",
  "flight_type": "arrival",
  "status": "landed",
  "position": {"x": 0.0, "y": 0.0},
  "altitude": 32,
  "speed": 0,
  "heading": 340,
  "target_altitude": 32,
  "target_speed": 140,
  "target_heading": 340,
  "target_waypoint": "RUNWAY",
  "aircraft_type": "B738",
  "origin": "KSEA",
  "destination": "KRNT",
  "cleared_to_land": true,
  "cleared_for_takeoff": false,
  "passed_waypoints": ["NORTH", "DOWNWIND", "BASE", "FINAL", "RUNWAY"],
  "clearance_denial_reason": null
}
```

---

## Step 10: Flight Removed (after 3 seconds)

**Request:**
```bash
curl http://localhost:8000/api/flights/UAL4527
```

**Response:**
```json
null
```

---

## Step 11: Check History

**Request:**
```bash
curl http://localhost:8000/api/flights/history
```

**Response:**
```json
{
  "landed": [
    {
      "callsign": "UAL4527",
      "flight_type": "arrival",
      "aircraft_type": "B738",
      "origin": "KSEA",
      "destination": "KRNT",
      "completed_at": "2024-01-15T14:32:45.123456"
    }
  ],
  "departed": []
}
```

---

## Step 12: Simulation Status

**Request:**
```bash
curl http://localhost:8000/api/simulation/status
```

**Response:**
```json
{
  "running": true,
  "failed": false,
  "failure_reason": null,
  "collision_pair": null,
  "total_flights": 0,
  "arrivals": 0,
  "departures": 0,
  "landed": 1,
  "departed": 0,
  "near_misses": 0,
  "speed_multiplier": 1.0,
  "session_duration": 245.67
}
```

---

## Alternative: Set Heading Instead of Waypoint

**Request:**
```bash
curl -X POST http://localhost:8000/api/flights/UAL4527/command \
  -H "Content-Type: application/json" \
  -d '{"heading": 340, "altitude": 1000, "speed": 140}'
```

**Response:**
```json
{
  "status": "ok",
  "callsign": "UAL4527",
  "command": {
    "heading": 340,
    "altitude": 1000,
    "speed": 140
  },
  "result": {
    "success": true,
    "message": "Command accepted"
  }
}
```

---

## Landing Rules Reference

**Request:**
```bash
curl http://localhost:8000/api/landing-rules
```

**Response:**
```json
{
  "max_altitude": 1500,
  "min_speed": 100,
  "max_speed": 180,
  "max_distance": 18,
  "required_waypoint": "FINAL",
  "aligned_heading_tolerance": 30
}
```

---

## Waypoints Reference

**Request:**
```bash
curl http://localhost:8000/api/waypoints
```

**Response:**
```json
{
  "NORTH": {
    "name": "NORTH",
    "position": {"x": 0, "y": 25},
    "altitude_restriction": 6000,
    "description": "Northern departure/entry point"
  },
  "SOUTH": {
    "name": "SOUTH",
    "position": {"x": 0, "y": -25},
    "altitude_restriction": 6000,
    "description": "Southern entry point"
  },
  "EAST": {
    "name": "EAST",
    "position": {"x": 25, "y": 0},
    "altitude_restriction": 6000,
    "description": "Eastern entry point"
  },
  "WEST": {
    "name": "WEST",
    "position": {"x": -25, "y": 0},
    "altitude_restriction": 6000,
    "description": "Western entry point"
  },
  "DOWNWIND": {
    "name": "DOWNWIND",
    "position": {"x": -9, "y": 6},
    "altitude_restriction": 2000,
    "description": "Downwind leg - west of runway"
  },
  "BASE": {
    "name": "BASE",
    "position": {"x": -9, "y": -12},
    "altitude_restriction": 1500,
    "description": "Base turn point"
  },
  "FINAL": {
    "name": "FINAL",
    "position": {"x": 0, "y": -15},
    "altitude_restriction": 1000,
    "description": "Final approach - aligned with RWY 34"
  },
  "RUNWAY": {
    "name": "RUNWAY",
    "position": {"x": 0, "y": 0},
    "altitude_restriction": 32,
    "description": "Runway 34 threshold"
  }
}
```

