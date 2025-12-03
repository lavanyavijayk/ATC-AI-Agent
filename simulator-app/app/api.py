"""FastAPI REST API endpoints for the ATC simulator."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from .models import FlightData, FlightCommand, AirportData, LandingRules, Waypoint
from .simulation import simulator

router = APIRouter(prefix="/api", tags=["flights"])


class SpeedRequest(BaseModel):
    multiplier: float


@router.get("/airport", response_model=AirportData)
async def get_airport():
    """Get airport information."""
    airport = simulator.get_airport()
    return AirportData(
        icao=airport["icao"],
        name=airport["name"],
        elevation=airport["elevation"],
        runway=airport["runway"],
        runway_heading=airport["runway_heading"],
        runway_length=airport["runway_length"],
    )


@router.get("/waypoints", response_model=dict[str, Waypoint])
async def get_waypoints():
    """Get all navigation waypoints."""
    return simulator.get_waypoints()


@router.get("/landing-rules", response_model=LandingRules)
async def get_landing_rules():
    """Get rules for landing clearance."""
    rules = simulator.get_landing_rules()
    return LandingRules(**rules)


@router.get("/flights", response_model=list[FlightData])
async def get_all_flights():
    """Get all flights currently in the simulation."""
    return simulator.get_all_flights()


@router.get("/flights/landing", response_model=list[FlightData])
async def get_landing_flights():
    """Get flights that are currently approaching for landing."""
    return simulator.get_landing_flights()


@router.get("/flights/takeoff", response_model=list[FlightData])
async def get_takeoff_flights():
    """Get flights that are ready for takeoff."""
    return simulator.get_takeoff_flights()


@router.get("/flights/{callsign}", response_model=FlightData)
async def get_flight(callsign: str):
    """Get details for a specific flight by callsign."""
    flight = simulator.get_flight(callsign)
    if not flight:
        raise HTTPException(status_code=404, detail=f"Flight {callsign} not found")
    return flight.to_data()


@router.post("/flights/{callsign}/command")
async def command_flight(callsign: str, command: FlightCommand):
    """Issue a command to a specific flight."""
    result = simulator.command_flight(callsign, command)
    if not result["success"] and "not found" in result["message"]:
        raise HTTPException(status_code=404, detail=result["message"])
    return {
        "status": "ok" if result["success"] else "error",
        "callsign": callsign,
        "command": command.model_dump(exclude_none=True),
        "result": result
    }


@router.post("/simulation/spawn/arrival")
async def spawn_arrival():
    """Manually spawn a new arriving flight."""
    flight = simulator.spawn_arrival()
    if not flight:
        return {"status": "error", "message": "Simulation has failed - restart required"}
    return {"status": "ok", "flight": flight.to_data()}


@router.post("/simulation/spawn/departure")
async def spawn_departure():
    """Manually spawn a new departing flight."""
    flight = simulator.spawn_departure()
    if not flight:
        return {"status": "error", "message": "Simulation has failed - restart required"}
    return {"status": "ok", "flight": flight.to_data()}


@router.get("/simulation/status")
async def get_simulation_status():
    """Get current simulation status and statistics."""
    flights = simulator.get_all_flights()
    stats = simulator.get_stats()
    return {
        "running": simulator.running,
        "failed": stats["failed"],
        "failure_reason": stats["failure_reason"],
        "collision_pair": stats["collision_pair"],
        "total_flights": len(flights),
        "arrivals": len([f for f in flights if f.flight_type.value == "arrival"]),
        "departures": len([f for f in flights if f.flight_type.value == "departure"]),
        "landed": stats["landed"],
        "departed": stats["departed"],
        "near_misses": stats["near_misses"],
        "speed_multiplier": stats["speed_multiplier"],
        "session_duration": stats["session_duration"],
    }


@router.get("/simulation/stats")
async def get_stats():
    """Get simulation statistics."""
    return simulator.get_stats()


@router.get("/simulation/near-misses")
async def get_near_misses():
    """Get current active near miss pairs."""
    return simulator.get_near_misses()


@router.post("/simulation/speed")
async def set_speed(request: SpeedRequest):
    """Set simulation speed multiplier (0.5 to 10.0)."""
    simulator.set_speed(request.multiplier)
    return {"status": "ok", "speed_multiplier": simulator.speed_multiplier}


@router.post("/simulation/restart")
async def restart_simulation():
    """Save score and restart the simulation."""
    score = simulator.save_score()
    simulator.reset()
    return {"status": "ok", "saved_score": score}


@router.post("/simulation/end")
async def end_simulation():
    """Save score and end the simulation."""
    score = simulator.save_score()
    return {"status": "ok", "saved_score": score}


@router.get("/scores")
async def get_scores():
    """Get saved scores history."""
    import json
    from pathlib import Path
    scores_file = Path(__file__).parent.parent / "scores.json"
    if scores_file.exists():
        with open(scores_file, 'r') as f:
            return json.load(f)
    return []


@router.get("/flights/history")
async def get_flight_history():
    """
    Get history of completed flights (landed and departed).
    
    Returns the last 50 landed and last 50 departed flights.
    """
    return simulator.get_flight_history()
