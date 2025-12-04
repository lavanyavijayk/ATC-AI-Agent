"""Data models for the ATC simulator."""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class FlightStatus(str, Enum):
    """Flight status enumeration."""
    APPROACHING = "approaching"      # Inbound, in the air
    ON_FINAL = "on_final"           # On final approach
    LANDING = "landing"             # Currently landing
    LANDED = "landed"               # Touched down
    TAXIING_TO_GATE = "taxiing_to_gate"
    AT_GATE = "at_gate"
    TAXIING_TO_RUNWAY = "taxiing_to_runway"
    READY_FOR_TAKEOFF = "ready_for_takeoff"
    TAKING_OFF = "taking_off"
    DEPARTING = "departing"         # Climbing out
    DEPARTED = "departed"           # Left airspace


class FlightType(str, Enum):
    """Type of flight."""
    ARRIVAL = "arrival"
    DEPARTURE = "departure"


class Position(BaseModel):
    """Geographic position."""
    x: float = Field(..., description="X position in nautical miles from airport")
    y: float = Field(..., description="Y position in nautical miles from airport")


class Waypoint(BaseModel):
    """Navigation waypoint."""
    name: str = Field(..., description="Waypoint identifier")
    position: Position = Field(..., description="Waypoint position")
    altitude_restriction: Optional[float] = Field(None, description="Altitude restriction in feet")
    description: Optional[str] = Field(None, description="Waypoint description")


class FlightData(BaseModel):
    """Complete flight data model."""
    callsign: str = Field(..., description="Flight callsign (e.g., UAL123)")
    flight_type: FlightType
    status: FlightStatus
    position: Position
    altitude: float = Field(..., description="Altitude in feet")
    speed: float = Field(..., description="Ground speed in knots")
    heading: float = Field(..., description="Heading in degrees (0-360)")
    target_altitude: Optional[float] = Field(None, description="Assigned altitude")
    target_speed: Optional[float] = Field(None, description="Assigned speed")
    target_heading: Optional[float] = Field(None, description="Assigned heading")
    target_waypoint: Optional[str] = Field(None, description="Target waypoint name")
    aircraft_type: str = Field(..., description="Aircraft type (e.g., B738)")
    origin: Optional[str] = Field(None, description="Origin airport ICAO")
    destination: Optional[str] = Field(None, description="Destination airport ICAO")
    cleared_to_land: bool = Field(False, description="Cleared for landing")
    cleared_for_takeoff: bool = Field(False, description="Cleared for takeoff")
    passed_waypoints: list[str] = Field(default_factory=list, description="Waypoints already passed")
    clearance_denial_reason: Optional[str] = Field(None, description="Reason landing clearance was denied")


class FlightCommand(BaseModel):
    """Command to issue to a flight."""
    altitude: Optional[float] = Field(None, description="New target altitude in feet")
    speed: Optional[float] = Field(None, description="New target speed in knots")
    heading: Optional[float] = Field(None, description="New target heading in degrees")
    waypoint: Optional[str] = Field(None, description="Direct to waypoint (clears heading)")
    clear_to_land: Optional[bool] = Field(None, description="Clear for landing")
    clear_for_takeoff: Optional[bool] = Field(None, description="Clear for takeoff")


class AirportData(BaseModel):
    """Airport configuration."""
    icao: str = Field(..., description="Airport ICAO code")
    name: str = Field(..., description="Airport name")
    elevation: float = Field(..., description="Airport elevation in feet")
    runway: str = Field(..., description="Active runway")
    runway_heading: float = Field(..., description="Runway magnetic heading")
    runway_length: float = Field(..., description="Runway length in nautical miles")


class LandingRules(BaseModel):
    """Rules for landing clearance."""
    max_altitude: float = Field(..., description="Maximum altitude for clearance")
    min_speed: float = Field(..., description="Minimum approach speed")
    max_speed: float = Field(..., description="Maximum approach speed")
    max_distance: float = Field(..., description="Maximum distance from runway")
    required_waypoint: str = Field(..., description="Required waypoint to pass")
