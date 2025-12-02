# AI-ATC API Samples

This folder contains example scripts demonstrating all API endpoints and commands.

## Prerequisites

Make sure the server is running:
```bash
cd /home/para/study/AI-ATC
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Shell Scripts

Make scripts executable:
```bash
chmod +x *.sh
```

### GET Endpoints (Read Data)

| Script | Endpoint | Description |
|--------|----------|-------------|
| `01_get_airport.sh` | GET /api/airport | Airport info (KRNT) |
| `02_get_waypoints.sh` | GET /api/waypoints | All navigation waypoints |
| `03_get_landing_rules.sh` | GET /api/landing-rules | Landing clearance rules |
| `04_get_all_flights.sh` | GET /api/flights | All active flights |
| `05_get_landing_flights.sh` | GET /api/flights/landing | Arriving flights |
| `06_get_takeoff_flights.sh` | GET /api/flights/takeoff | Departing flights |
| `07_get_specific_flight.sh` | GET /api/flights/{callsign} | Single flight details |
| `08_get_simulation_status.sh` | GET /api/simulation/status | Simulation stats |

### POST Endpoints (Spawn Flights)

| Script | Endpoint | Description |
|--------|----------|-------------|
| `09_spawn_arrival.sh` | POST /api/simulation/spawn/arrival | Create inbound flight |
| `10_spawn_departure.sh` | POST /api/simulation/spawn/departure | Create outbound flight |

### Command Endpoints (Control Flights)

All command scripts accept callsign as first argument:
```bash
./11_command_set_altitude.sh UAL123 5000
```

| Script | Command | Description |
|--------|---------|-------------|
| `11_command_set_altitude.sh` | `{"altitude": N}` | Set target altitude (feet) |
| `12_command_set_speed.sh` | `{"speed": N}` | Set target speed (knots) |
| `13_command_set_heading.sh` | `{"heading": N}` | Set heading (0-360°), clears waypoint |
| `14_command_direct_to_waypoint.sh` | `{"waypoint": "NAME"}` | Navigate to waypoint |
| `15_command_clear_to_land.sh` | `{"clear_to_land": true}` | Clear for landing |
| `16_command_cancel_landing.sh` | `{"clear_to_land": false}` | Cancel landing clearance |
| `17_command_clear_for_takeoff.sh` | `{"clear_for_takeoff": true}` | Clear for takeoff |
| `18_command_cancel_takeoff.sh` | `{"clear_for_takeoff": false}` | Cancel takeoff clearance |
| `19_command_combined.sh` | Multiple params | Combine waypoint + altitude + speed |
| `20_command_full_approach.sh` | Sequence | Full approach demonstration |

## Python Example

Run the complete Python example:
```bash
pip install httpx
python python_example.py
```

## Available Waypoints

| Name | Position (nm) | Altitude | Purpose |
|------|---------------|----------|---------|
| NORTH | (0, 25) | 6000' | Entry point |
| SOUTH | (0, -25) | 6000' | Entry point |
| EAST | (25, 0) | 6000' | Entry point |
| WEST | (-25, 0) | 6000' | Entry point |
| DOWNWIND | (-4, -8) | 2000' | Traffic pattern |
| BASE | (-2, -6) | 1500' | Base turn |
| FINAL | (1.7, -4.7) | 1000' | Aligned with RWY 34 (HDG 340°) |

**Note:** FINAL is positioned so that flying heading 340° from FINAL leads directly to the runway.

## Landing Rules

To be cleared for landing, flight must meet ALL:
- Altitude < 1500 ft
- Speed: 100-180 kt
- Distance < 8 nm from runway
- Must have passed FINAL waypoint
- Heading within ±30° of runway (340°)

## Quick Test Sequence

```bash
# 1. Spawn a flight
./09_spawn_arrival.sh

# 2. Get the callsign from output, then:
./14_command_direct_to_waypoint.sh <CALLSIGN> DOWNWIND
./11_command_set_altitude.sh <CALLSIGN> 2000
./12_command_set_speed.sh <CALLSIGN> 180

# 3. Continue vectoring to FINAL
./14_command_direct_to_waypoint.sh <CALLSIGN> FINAL
./11_command_set_altitude.sh <CALLSIGN> 1000
./12_command_set_speed.sh <CALLSIGN> 140

# 4. Once at FINAL, clear to land
./15_command_clear_to_land.sh <CALLSIGN>
```

