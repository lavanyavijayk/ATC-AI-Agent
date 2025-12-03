# AI-ATC Simulator

An online Air Traffic Control simulator designed for integration with agentic AI systems. Features real-time radar display, waypoint navigation, collision detection, and comprehensive REST API.

![AI-ATC Simulator](https://img.shields.io/badge/version-3.0.0-22c55e?style=flat-square)
![Python](https://img.shields.io/badge/python-3.10+-blue?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?style=flat-square)

## Features

- 🛫 **Realistic Flight Simulation** - Aircraft with physics (climb, descent, turns)
- 🗺️ **Dark Radar Display** - Professional ATC-style interface
- 📍 **Waypoint Navigation** - Direct-to routing with automatic waypoint passage
- ✅ **Landing Rules** - Altitude, speed, and waypoint requirements for clearance
- 💥 **Collision Detection** - Near miss warnings and collision failure
- 📊 **Statistics Tracking** - Landed, departed, near misses counts
- 🔌 **REST API** - Full API for AI agent integration
- 🌐 **WebSocket Updates** - Real-time flight position updates (10 Hz)
- ⏱️ **Speed Control** - 1x, 2x, 5x, 10x simulation speed
- 📜 **Flight History** - Track completed arrivals and departures

## Quick Start

### Installation

```bash
cd /home/para/study/AI-ATC
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running the Simulator

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open your browser to `http://localhost:8000`

## Airport: KRNT (Renton Municipal)

- **Single Runway:** 34 (Heading 340°)
- **Elevation:** 32 ft

## Waypoints

### Entry Points
| Waypoint | Position (nm) | Altitude | Description |
|----------|---------------|----------|-------------|
| NORTH | (0, 25) | 6000' | Departure exit / Entry point |
| SOUTH | (0, -25) | 6000' | Entry point |
| EAST | (25, 0) | 6000' | Entry point |
| SHORT_EAST | (15, 0) | 4000' | Short eastern entry point |
| WEST | (-25, 0) | 6000' | Entry point |

### Traffic Pattern
| Waypoint | Position (nm) | Altitude | Description |
|----------|---------------|----------|-------------|
| DOWNWIND | (-9, 6) | 2000' | Downwind leg (west of runway) |
| BASE | (-9, -12) | 1500' | Base turn point |
| FINAL | (0, -15) | 1000' | Final approach (aligned with RWY 34) |
| RUNWAY | (0, 0) | 32' | Runway threshold |

### AI Sequencing Waypoints
| Waypoint | Position (nm) | Altitude | Description |
|----------|---------------|----------|-------------|
| ALPHA | (-15, 15) | 5000' | Northwest sequencing point |
| BRAVO | (15, 15) | 5000' | Northeast sequencing point |
| CHARLIE | (-15, -15) | 4000' | Southwest approach setup |
| DELTA | (15, -15) | 4000' | Southeast approach setup |
| ECHO | (0, -22) | 2500' | Extended final approach fix |
| HOTEL | (-18, 0) | 3500' | Western holding point |

**Traffic Pattern:** U-shaped - DOWNWIND → BASE → FINAL → RUNWAY

**AI Sequencing:** Use ALPHA, BRAVO, CHARLIE, DELTA, ECHO, HOTEL waypoints to manage traffic flow and aircraft separation before entering the traffic pattern.

## Landing Rules

A flight must meet ALL criteria to be cleared for landing:

| Rule | Requirement |
|------|-------------|
| Altitude | Below 1500 ft |
| Speed | Between 100-180 kt |
| Distance | Within 18 nm of runway |
| Waypoint | Must have passed FINAL |

## Collision & Separation

| Type | Distance | Altitude | Result |
|------|----------|----------|--------|
| **Near Miss** | < 1000 ft | Any | Warning + Counter |
| **Collision** | < 500 ft | < 500 ft | Simulation Failure |

## Departure Procedure

1. Spawn departure → appears at gate
2. After 60 seconds → status: `ready_for_takeoff`
3. Clear for takeoff → auto-routes to **NORTH** at **6000ft**
4. Reaches NORTH + 6000ft → `departed` (disappears)

## API Reference

### Base URL
```
http://localhost:8000/api
```

### GET Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/airport` | Airport information |
| `/api/waypoints` | All navigation waypoints |
| `/api/landing-rules` | Landing clearance rules |
| `/api/flights` | All active flights |
| `/api/flights/landing` | Flights approaching for landing |
| `/api/flights/takeoff` | Flights ready for takeoff |
| `/api/flights/history` | Completed flights (landed/departed) |
| `/api/flights/{callsign}` | Specific flight details |
| `/api/simulation/status` | Simulation status and stats |
| `/api/simulation/near-misses` | Active near miss alerts |
| `/api/scores` | Saved score history |

### POST Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/flights/{callsign}/command` | Send command to flight |
| `/api/simulation/spawn/arrival` | Spawn new arrival |
| `/api/simulation/spawn/departure` | Spawn new departure |
| `/api/simulation/speed` | Set speed multiplier |
| `/api/simulation/restart` | Save score & restart |
| `/api/simulation/end` | Save score & end |

### Flight Commands

```http
POST /api/flights/{callsign}/command
Content-Type: application/json
```

| Parameter | Type | Description |
|-----------|------|-------------|
| altitude | float | Target altitude in feet |
| speed | float | Target speed in knots |
| heading | float | Target heading in degrees (clears waypoint) |
| waypoint | string | Direct to waypoint (e.g., "FINAL") |
| clear_to_land | bool | Clear for landing (checks rules) |
| clear_for_takeoff | bool | Clear for takeoff |

**Note:** `heading` takes priority over `waypoint`. After passing a waypoint, flight continues on the same heading (no circling).

### Examples

**Direct to waypoint with altitude/speed:**
```bash
curl -X POST http://localhost:8000/api/flights/UAL123/command \
  -H "Content-Type: application/json" \
  -d '{"waypoint": "FINAL", "altitude": 1000, "speed": 140}'
```

**Set heading (instead of waypoint):**
```bash
curl -X POST http://localhost:8000/api/flights/UAL123/command \
  -H "Content-Type: application/json" \
  -d '{"heading": 340, "altitude": 1000}'
```

**Clear for landing:**
```bash
curl -X POST http://localhost:8000/api/flights/UAL123/command \
  -H "Content-Type: application/json" \
  -d '{"clear_to_land": true}'
```

**Set simulation speed:**
```bash
curl -X POST http://localhost:8000/api/simulation/speed \
  -H "Content-Type: application/json" \
  -d '{"multiplier": 5.0}'
```

### Response Format

**Success:**
```json
{
  "status": "ok",
  "callsign": "UAL123",
  "command": {"waypoint": "FINAL", "altitude": 1000},
  "result": {"success": true, "message": "Command accepted"}
}
```

**Error (landing rules not met):**
```json
{
  "status": "error",
  "callsign": "UAL123",
  "command": {"clear_to_land": true},
  "result": {
    "success": false,
    "message": "Cannot clear to land: Altitude 2500ft exceeds max 1500ft"
  }
}
```

## AI Agent Integration

```python
import httpx
import asyncio

async def ai_atc_controller():
    async with httpx.AsyncClient(base_url="http://localhost:8000/api") as client:
        waypoints = (await client.get("/waypoints")).json()
        rules = (await client.get("/landing-rules")).json()
        
        while True:
            flights = (await client.get("/flights")).json()
            
            for flight in flights:
                # Handle arrivals
                if flight["flight_type"] == "arrival":
                    if flight["status"] == "approaching":
                        # Guide through pattern: DOWNWIND → BASE → FINAL
                        if "DOWNWIND" not in flight["passed_waypoints"]:
                            await client.post(
                                f"/flights/{flight['callsign']}/command",
                                json={"waypoint": "DOWNWIND", "altitude": 2000, "speed": 200}
                            )
                        elif "BASE" not in flight["passed_waypoints"]:
                            await client.post(
                                f"/flights/{flight['callsign']}/command",
                                json={"waypoint": "BASE", "altitude": 1500, "speed": 160}
                            )
                        elif "FINAL" not in flight["passed_waypoints"]:
                            await client.post(
                                f"/flights/{flight['callsign']}/command",
                                json={"waypoint": "FINAL", "altitude": 1000, "speed": 140}
                            )
                    
                    elif flight["status"] == "on_final" and not flight["cleared_to_land"]:
                        await client.post(
                            f"/flights/{flight['callsign']}/command",
                            json={"clear_to_land": True}
                        )
                
                # Handle departures
                elif flight["flight_type"] == "departure":
                    if flight["status"] == "ready_for_takeoff" and not flight["cleared_for_takeoff"]:
                        await client.post(
                            f"/flights/{flight['callsign']}/command",
                            json={"clear_for_takeoff": True}
                        )
            
            await asyncio.sleep(1)

asyncio.run(ai_atc_controller())
```

## WebSocket

Connect to `/ws` for real-time updates:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // data.type === 'update'
  // data.flights === [<FlightData>, ...]
  // data.stats === {landed, departed, near_misses, failed, ...}
  // data.near_misses === [{callsigns, position}, ...]
  // data.history === {landed: [...], departed: [...]}
};

// Send commands via WebSocket
ws.send(JSON.stringify({
  type: 'command',
  callsign: 'UAL123',
  command: { altitude: 3000 }
}));

// Set speed
ws.send(JSON.stringify({ type: 'set_speed', multiplier: 5.0 }));

// Restart simulation
ws.send(JSON.stringify({ type: 'restart' }));
```

## Scoring

Scores are saved to `scores.json` on:
- Collision (automatic)
- Restart button
- End button

Score format:
```json
{
  "datetime": "2024-01-15T10:30:00",
  "landed": 5,
  "departed": 3,
  "near_misses": 1,
  "failed": false,
  "failure_reason": null,
  "duration_seconds": 300.5
}
```

## Project Structure

```
AI-ATC/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application + WebSocket
│   ├── api.py           # REST API endpoints
│   ├── models.py        # Pydantic data models
│   └── simulation.py    # Flight physics engine
├── static/
│   ├── index.html       # Radar display UI
│   ├── style.css        # Dark theme styling
│   └── app.js           # Frontend logic
├── api_samples/         # API usage examples
│   ├── *.sh             # Shell script examples
│   ├── python_example.py
│   └── README.md
├── scores.json          # Saved scores
├── requirements.txt
└── README.md
```

## UI Controls

| Control | Action |
|---------|--------|
| Click flight | Select and show details |
| + Zoom / - Zoom | Adjust map range |
| Speed buttons | 1x, 2x, 5x, 10x simulation speed |
| Spawn Arrival | Create new inbound flight |
| Spawn Departure | Create new outbound flight |
| Restart | Save score and reset simulation |
| Tabs | Active / Arrivals / Departures / History |

## License

MIT License
