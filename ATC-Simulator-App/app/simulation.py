"""Flight simulation engine with physics."""
import math
import random
import asyncio
import json
from datetime import datetime
from typing import Optional
from pathlib import Path
from .models import (
    FlightData, FlightStatus, FlightType, Position, FlightCommand, Waypoint
)


# Aircraft types with characteristics
AIRCRAFT_TYPES = {
    "B738": {"cruise_speed": 450, "approach_speed": 140, "min_approach_speed": 130, "max_approach_speed": 160, "climb_rate": 2500, "descent_rate": 1500},
    "A320": {"cruise_speed": 450, "approach_speed": 137, "min_approach_speed": 125, "max_approach_speed": 155, "climb_rate": 2400, "descent_rate": 1400},
    "B77W": {"cruise_speed": 490, "approach_speed": 150, "min_approach_speed": 140, "max_approach_speed": 170, "climb_rate": 2000, "descent_rate": 1200},
    "A359": {"cruise_speed": 480, "approach_speed": 145, "min_approach_speed": 135, "max_approach_speed": 165, "climb_rate": 2200, "descent_rate": 1300},
    "E190": {"cruise_speed": 430, "approach_speed": 130, "min_approach_speed": 120, "max_approach_speed": 150, "climb_rate": 2800, "descent_rate": 1600},
    "C172": {"cruise_speed": 120, "approach_speed": 65, "min_approach_speed": 55, "max_approach_speed": 80, "climb_rate": 700, "descent_rate": 500},
}

AIRLINES = ["UAL", "DAL", "AAL", "SWA", "JBU", "ASA", "FFT", "SKW"]

# Airport configuration - Renton style single runway
AIRPORT = {
    "icao": "KRNT",
    "name": "Renton Municipal Airport",
    "elevation": 32,
    "runway": "34",
    "runway_heading": 340,
    "runway_length": 1.0,
}

# Waypoints - distances increased 3x for DOWNWIND, BASE, FINAL
WAYPOINTS: dict[str, Waypoint] = {
    "NORTH": Waypoint(
        name="NORTH",
        position=Position(x=0, y=25),
        altitude_restriction=6000,
        description="Northern departure/entry point"
    ),
    "SOUTH": Waypoint(
        name="SOUTH",
        position=Position(x=0, y=-25),
        altitude_restriction=6000,
        description="Southern entry point"  
    ),
    "EAST": Waypoint(
        name="EAST",
        position=Position(x=25, y=0),
        altitude_restriction=6000,
        description="Eastern entry point"
    ),
    "SHORT_EAST": Waypoint(
        name="SHORT_EAST",
        position=Position(x=15, y=0),
        altitude_restriction=4000,
        description="Short eastern entry point"
    ),
    "WEST": Waypoint(
        name="WEST",
        position=Position(x=-25, y=0),
        altitude_restriction=6000,
        description="Western entry point"
    ),
    # U-shaped traffic pattern - 3x distance from runway
    "DOWNWIND": Waypoint(
        name="DOWNWIND",
        position=Position(x=-9, y=6),
        altitude_restriction=2000,
        description="Downwind leg - west of runway"
    ),
    "BASE": Waypoint(
        name="BASE",
        position=Position(x=-9, y=-12),
        altitude_restriction=1500,
        description="Base turn point"
    ),
    "FINAL": Waypoint(
        name="FINAL",
        position=Position(x=0, y=-15),
        altitude_restriction=1000,
        description="Final approach - aligned with RWY 34"
    ),
    "RUNWAY": Waypoint(
        name="RUNWAY",
        position=Position(x=0, y=0),
        altitude_restriction=32,
        description="Runway 34 threshold"
    ),
    # Additional waypoints for AI agent traffic management
    "ALPHA": Waypoint(
        name="ALPHA",
        position=Position(x=-15, y=15),
        altitude_restriction=5000,
        description="Northwest sequencing point"
    ),
    "BRAVO": Waypoint(
        name="BRAVO",
        position=Position(x=15, y=15),
        altitude_restriction=5000,
        description="Northeast sequencing point"
    ),
    "CHARLIE": Waypoint(
        name="CHARLIE",
        position=Position(x=-15, y=-15),
        altitude_restriction=4000,
        description="Southwest approach setup"
    ),
    "DELTA": Waypoint(
        name="DELTA",
        position=Position(x=15, y=-15),
        altitude_restriction=4000,
        description="Southeast approach setup"
    ),
    "ECHO": Waypoint(
        name="ECHO",
        position=Position(x=0, y=-22),
        altitude_restriction=2500,
        description="Extended final approach fix"
    ),
    "HOTEL": Waypoint(
        name="HOTEL",
        position=Position(x=-18, y=0),
        altitude_restriction=3500,
        description="Western holding point"
    ),
}

# Landing rules
LANDING_RULES = {
    "max_altitude": 1500,
    "min_speed": 100,
    "max_speed": 180,
    "max_distance": 18,  # Increased for larger pattern
    "required_waypoint": "FINAL",
}

# Separation minimums (in nautical miles)
# Note: These are in nm for horizontal, feet for vertical
NEAR_MISS_DISTANCE_NM = 0.5      # ~3000ft horizontal - triggers warning
NEAR_MISS_ALTITUDE = 1000        # 1000ft vertical for near miss
COLLISION_DISTANCE_NM = 0.15     # ~900ft horizontal - collision
COLLISION_ALTITUDE = 500         # 500ft vertical for collision


class Flight:
    """Represents a single flight with physics simulation."""
    
    def __init__(self, callsign: str, flight_type: FlightType, aircraft_type: str,
                 position: Position, altitude: float, speed: float, heading: float,
                 origin: Optional[str] = None, destination: Optional[str] = None):
        self.callsign = callsign
        self.flight_type = flight_type
        self.aircraft_type = aircraft_type
        self.position = position
        self.altitude = altitude
        self.speed = speed
        self.heading = heading
        self.origin = origin
        self.destination = destination
        
        self.target_altitude = altitude
        self.target_speed = speed
        self.target_heading = heading
        self.target_waypoint: Optional[str] = None
        
        self.status = (FlightStatus.APPROACHING if flight_type == FlightType.ARRIVAL 
                      else FlightStatus.AT_GATE)
        self.cleared_to_land = False
        self.cleared_for_takeoff = False
        
        self.passed_waypoints: list[str] = []
        self.current_waypoint: Optional[str] = None
        
        self.characteristics = AIRCRAFT_TYPES.get(aircraft_type, AIRCRAFT_TYPES["B738"])
        
        self.created_at = datetime.now()
        self.gate_time = 0
        self.completed_at: Optional[datetime] = None
        
        self.clearance_denial_reason: Optional[str] = None
    
    def is_on_ground(self) -> bool:
        """Check if flight is on the ground."""
        return self.status in [
            FlightStatus.LANDED, 
            FlightStatus.AT_GATE, 
            FlightStatus.READY_FOR_TAKEOFF,
            FlightStatus.TAXIING_TO_GATE,
            FlightStatus.TAXIING_TO_RUNWAY
        ]
    
    def is_airborne_active(self) -> bool:
        """Check if flight is airborne and should be checked for separation."""
        return self.status in [
            FlightStatus.APPROACHING,
            FlightStatus.ON_FINAL,
            FlightStatus.LANDING,
            FlightStatus.TAKING_OFF,
            FlightStatus.DEPARTING,
        ]
    
    def apply_command(self, command: FlightCommand) -> dict:
        """Apply an ATC command to the flight."""
        result = {"success": True, "message": "Command accepted"}
        
        if command.altitude is not None:
            self.target_altitude = command.altitude
        if command.speed is not None:
            self.target_speed = command.speed
        if command.heading is not None:
            self.target_heading = command.heading % 360
            self.target_waypoint = None  # Clear waypoint when given direct heading
        if command.waypoint is not None:
            if command.waypoint in WAYPOINTS:
                self.target_waypoint = command.waypoint
                self.current_waypoint = command.waypoint
            else:
                result = {"success": False, "message": f"Unknown waypoint: {command.waypoint}"}
        if command.clear_for_takeoff is not None:
            self.cleared_for_takeoff = command.clear_for_takeoff
        if command.clear_to_land is not None:
            if command.clear_to_land:
                can_clear, reason = self._check_landing_rules()
                if can_clear:
                    self.cleared_to_land = True
                    self.clearance_denial_reason = None
                    self.target_waypoint = "RUNWAY"
                    self.current_waypoint = "RUNWAY"
                    self.target_altitude = AIRPORT["elevation"]
                    self.target_speed = self.characteristics.get("approach_speed", 140)
                else:
                    self.clearance_denial_reason = reason
                    result = {"success": False, "message": f"Cannot clear to land: {reason}"}
            else:
                self.cleared_to_land = False
                self.clearance_denial_reason = None
        
        return result
    
    def _check_landing_rules(self) -> tuple[bool, Optional[str]]:
        """Check if flight meets landing clearance rules."""
        rules = LANDING_RULES
        
        if self.altitude > rules["max_altitude"]:
            return False, f"Altitude {int(self.altitude)}ft exceeds max {rules['max_altitude']}ft"
        
        if self.speed < rules["min_speed"]:
            return False, f"Speed {int(self.speed)}kt below min {rules['min_speed']}kt"
        if self.speed > rules["max_speed"]:
            return False, f"Speed {int(self.speed)}kt exceeds max {rules['max_speed']}kt"
        
        distance = math.sqrt(self.position.x**2 + self.position.y**2)
        if distance > rules["max_distance"]:
            return False, f"Distance {distance:.1f}nm exceeds max {rules['max_distance']}nm"
        
        if rules["required_waypoint"] not in self.passed_waypoints:
            return False, f"Must pass {rules['required_waypoint']} waypoint first"
        
        return True, None
    
    def update(self, dt: float) -> None:
        """Update flight physics for dt seconds."""
        if self.status in [FlightStatus.LANDED, FlightStatus.DEPARTED, FlightStatus.AT_GATE]:
            if self.status == FlightStatus.AT_GATE and self.flight_type == FlightType.DEPARTURE:
                self.gate_time += dt
                if self.gate_time > 60:
                    self.status = FlightStatus.READY_FOR_TAKEOFF
            return
        
        # Navigate to waypoint if set
        if self.target_waypoint:
            self._navigate_to_waypoint()
        
        # Update altitude
        if abs(self.altitude - self.target_altitude) > 10:
            if self.altitude < self.target_altitude:
                climb_rate = self.characteristics["climb_rate"]
                self.altitude += climb_rate * (dt / 60)
            else:
                descent_rate = self.characteristics["descent_rate"]
                self.altitude -= descent_rate * (dt / 60)
            self.altitude = max(0, self.altitude)
        
        # Update speed
        speed_change_rate = 5
        if abs(self.speed - self.target_speed) > 1:
            if self.speed < self.target_speed:
                self.speed = min(self.speed + speed_change_rate * dt, self.target_speed)
            else:
                self.speed = max(self.speed - speed_change_rate * dt, self.target_speed)
        
        # Update heading
        turn_rate = 3
        heading_diff = (self.target_heading - self.heading + 540) % 360 - 180
        if abs(heading_diff) > 0.5:
            turn_amount = min(abs(heading_diff), turn_rate * dt)
            self.heading += turn_amount if heading_diff > 0 else -turn_amount
            self.heading = self.heading % 360
        
        # Update position
        distance = (self.speed / 3600) * dt
        heading_rad = math.radians(self.heading)
        
        self.position.x += distance * math.sin(heading_rad)
        self.position.y += distance * math.cos(heading_rad)
        
        # Check waypoint passage
        self._check_waypoint_passage()
        
        # Update status
        self._update_status()
    
    def _navigate_to_waypoint(self) -> None:
        """Calculate heading to target waypoint."""
        if not self.target_waypoint or self.target_waypoint not in WAYPOINTS:
            return
        
        waypoint = WAYPOINTS[self.target_waypoint]
        dx = waypoint.position.x - self.position.x
        dy = waypoint.position.y - self.position.y
        
        bearing = math.degrees(math.atan2(dx, dy)) % 360
        self.target_heading = bearing
    
    def _check_waypoint_passage(self) -> None:
        """Check if we've passed any waypoints."""
        for name, waypoint in WAYPOINTS.items():
            if name in self.passed_waypoints:
                continue
            
            dx = waypoint.position.x - self.position.x
            dy = waypoint.position.y - self.position.y
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < 0.5:
                self.passed_waypoints.append(name)
                if self.target_waypoint == name:
                    # Continue on current heading after passing waypoint
                    # (don't circle - just clear the waypoint target)
                    self.target_waypoint = None
                    # Keep the current heading as target
                    self.target_heading = self.heading
    
    def _update_status(self) -> None:
        """Update flight status based on current conditions."""
        distance_to_airport = math.sqrt(self.position.x**2 + self.position.y**2)
        
        if self.flight_type == FlightType.ARRIVAL:
            if self.status == FlightStatus.APPROACHING:
                if "FINAL" in self.passed_waypoints and self.altitude < 2000:
                    self.status = FlightStatus.ON_FINAL
            elif self.status == FlightStatus.ON_FINAL:
                if self.cleared_to_land and distance_to_airport < 0.5 and self.altitude < 300:
                    self.status = FlightStatus.LANDING
            elif self.status == FlightStatus.LANDING:
                if distance_to_airport < 0.1 or self.altitude <= AIRPORT["elevation"] + 20:
                    self.altitude = AIRPORT["elevation"]
                    self.speed = 0
                    self.status = FlightStatus.LANDED
                    self.completed_at = datetime.now()
        
        elif self.flight_type == FlightType.DEPARTURE:
            if self.status == FlightStatus.READY_FOR_TAKEOFF:
                if self.cleared_for_takeoff:
                    self.status = FlightStatus.TAKING_OFF
                    self.target_speed = 180
                    self.target_altitude = 6000
                    self.target_heading = AIRPORT["runway_heading"]
                    # Auto-route to NORTH waypoint
                    self.target_waypoint = "NORTH"
                    self.current_waypoint = "NORTH"
            elif self.status == FlightStatus.TAKING_OFF:
                if self.speed > 140:
                    self.status = FlightStatus.DEPARTING
            elif self.status == FlightStatus.DEPARTING:
                # Depart when reached NORTH waypoint AND 6000ft
                if "NORTH" in self.passed_waypoints and self.altitude >= 5900:
                    self.status = FlightStatus.DEPARTED
                    self.completed_at = datetime.now()
    
    def to_data(self) -> FlightData:
        """Convert to FlightData model."""
        return FlightData(
            callsign=self.callsign,
            flight_type=self.flight_type,
            status=self.status,
            position=self.position,
            altitude=self.altitude,
            speed=self.speed,
            heading=self.heading,
            target_altitude=self.target_altitude,
            target_speed=self.target_speed,
            target_heading=self.target_heading,
            target_waypoint=self.target_waypoint,
            aircraft_type=self.aircraft_type,
            origin=self.origin,
            destination=self.destination,
            cleared_to_land=self.cleared_to_land,
            cleared_for_takeoff=self.cleared_for_takeoff,
            passed_waypoints=self.passed_waypoints,
            clearance_denial_reason=self.clearance_denial_reason,
        )
    
    def to_history_data(self) -> dict:
        """Convert to history record."""
        return {
            "callsign": self.callsign,
            "flight_type": self.flight_type.value,
            "aircraft_type": self.aircraft_type,
            "origin": self.origin,
            "destination": self.destination,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class ATCSimulator:
    """Main ATC simulation engine."""
    
    def __init__(self):
        self.flights: dict[str, Flight] = {}
        self.flight_counter = 0
        self.running = False
        self.failed = False
        self.failure_reason: Optional[str] = None
        self.update_callbacks: list = []
        
        self.speed_multiplier = 1.0
        
        # Statistics
        self.landed_count = 0
        self.departed_count = 0
        self.near_miss_count = 0
        self.collision_pair: Optional[tuple[str, str]] = None
        
        # Flight history (completed flights)
        self.landed_flights: list[dict] = []
        self.departed_flights: list[dict] = []
        
        self.active_near_misses: set[tuple[str, str]] = set()
        
        self.session_start = datetime.now()
        
        self.scores_file = Path(__file__).parent.parent / "scores.json"
    
    def reset(self) -> None:
        """Reset the simulation."""
        self.flights.clear()
        self.flight_counter = 0
        self.failed = False
        self.failure_reason = None
        self.landed_count = 0
        self.departed_count = 0
        self.near_miss_count = 0
        self.collision_pair = None
        self.landed_flights.clear()
        self.departed_flights.clear()
        self.active_near_misses.clear()
        self.session_start = datetime.now()
        self.running = True
    
    def set_speed(self, multiplier: float) -> None:
        """Set simulation speed multiplier."""
        self.speed_multiplier = max(0.5, min(10.0, multiplier))
    
    def generate_callsign(self) -> str:
        """Generate a unique flight callsign."""
        airline = random.choice(AIRLINES)
        number = random.randint(100, 9999)
        return f"{airline}{number}"
    
    def spawn_arrival(self) -> Optional[Flight]:
        """Spawn a new arriving flight."""
        if self.failed:
            return None
            
        entry_waypoints = ["NORTH", "SOUTH", "EAST", "WEST"]
        entry = random.choice(entry_waypoints)
        waypoint = WAYPOINTS[entry]
        
        offset_angle = random.uniform(0, 2 * math.pi)
        offset_dist = random.uniform(3, 8)
        spawn_x = waypoint.position.x + offset_dist * math.cos(offset_angle)
        spawn_y = waypoint.position.y + offset_dist * math.sin(offset_angle)
        
        heading = math.degrees(math.atan2(
            waypoint.position.x - spawn_x,
            waypoint.position.y - spawn_y
        )) % 360
        
        aircraft_type = random.choice(list(AIRCRAFT_TYPES.keys()))
        
        callsign = self.generate_callsign()
        while callsign in self.flights:
            callsign = self.generate_callsign()
        
        flight = Flight(
            callsign=callsign,
            flight_type=FlightType.ARRIVAL,
            aircraft_type=aircraft_type,
            position=Position(x=spawn_x, y=spawn_y),
            altitude=random.randint(8000, 12000),
            speed=AIRCRAFT_TYPES[aircraft_type]["cruise_speed"] * 0.7,
            heading=heading,
            origin=random.choice(["KSEA", "KPDX", "KBFI", "KPAE", "KOLM"]),
            destination=AIRPORT["icao"],
        )
        
        flight.target_waypoint = entry
        flight.current_waypoint = entry
        flight.target_altitude = waypoint.altitude_restriction
        flight.target_speed = 250
        
        self.flights[callsign] = flight
        return flight
    
    def spawn_departure(self) -> Optional[Flight]:
        """Spawn a new departing flight at gate."""
        if self.failed:
            return None
            
        aircraft_type = random.choice(list(AIRCRAFT_TYPES.keys()))
        
        callsign = self.generate_callsign()
        while callsign in self.flights:
            callsign = self.generate_callsign()
        
        flight = Flight(
            callsign=callsign,
            flight_type=FlightType.DEPARTURE,
            aircraft_type=aircraft_type,
            position=Position(x=0.1, y=-0.2),
            altitude=AIRPORT["elevation"],
            speed=0,
            heading=AIRPORT["runway_heading"],
            origin=AIRPORT["icao"],
            destination=random.choice(["KSEA", "KPDX", "KBFI", "KPAE", "KOLM"]),
        )
        
        self.flights[callsign] = flight
        return flight
    
    def get_flight(self, callsign: str) -> Optional[Flight]:
        return self.flights.get(callsign)
    
    def get_all_flights(self) -> list[FlightData]:
        return [f.to_data() for f in self.flights.values()]
    
    def get_landing_flights(self) -> list[FlightData]:
        landing_statuses = [
            FlightStatus.APPROACHING,
            FlightStatus.ON_FINAL,
            FlightStatus.LANDING,
        ]
        return [f.to_data() for f in self.flights.values() 
                if f.status in landing_statuses]
    
    def get_takeoff_flights(self) -> list[FlightData]:
        takeoff_statuses = [
            FlightStatus.READY_FOR_TAKEOFF,
            FlightStatus.TAKING_OFF,
        ]
        return [f.to_data() for f in self.flights.values()
                if f.status in takeoff_statuses]
    
    def get_flight_history(self) -> dict:
        """Get completed flight history."""
        return {
            "landed": self.landed_flights[-50:],  # Last 50
            "departed": self.departed_flights[-50:],
        }
    
    def get_waypoints(self) -> dict[str, Waypoint]:
        return WAYPOINTS
    
    def get_landing_rules(self) -> dict:
        return LANDING_RULES
    
    def get_airport(self) -> dict:
        return AIRPORT
    
    def get_stats(self) -> dict:
        return {
            "landed": self.landed_count,
            "departed": self.departed_count,
            "near_misses": self.near_miss_count,
            "failed": self.failed,
            "failure_reason": self.failure_reason,
            "collision_pair": self.collision_pair,
            "speed_multiplier": self.speed_multiplier,
            "session_duration": (datetime.now() - self.session_start).total_seconds(),
        }
    
    def get_near_misses(self) -> list[dict]:
        near_misses = []
        for pair in self.active_near_misses:
            f1 = self.flights.get(pair[0])
            f2 = self.flights.get(pair[1])
            if f1 and f2:
                mid_x = (f1.position.x + f2.position.x) / 2
                mid_y = (f1.position.y + f2.position.y) / 2
                near_misses.append({
                    "callsigns": pair,
                    "position": {"x": mid_x, "y": mid_y}
                })
        return near_misses
    
    def command_flight(self, callsign: str, command: FlightCommand) -> dict:
        if self.failed:
            return {"success": False, "message": "Simulation has failed"}
        flight = self.flights.get(callsign)
        if flight:
            return flight.apply_command(command)
        return {"success": False, "message": f"Flight {callsign} not found"}
    
    def check_separations(self) -> None:
        """Check for near misses and collisions between airborne flights."""
        if self.failed:
            return
            
        airborne = [f for f in self.flights.values() if f.is_airborne_active()]
        current_near_misses: set[tuple[str, str]] = set()
        
        for i, f1 in enumerate(airborne):
            for f2 in airborne[i+1:]:
                dx = f1.position.x - f2.position.x
                dy = f1.position.y - f2.position.y
                horizontal_dist = math.sqrt(dx**2 + dy**2)
                vertical_dist = abs(f1.altitude - f2.altitude)
                
                pair = tuple(sorted([f1.callsign, f2.callsign]))
                
                # Collision: within ~900ft horizontal AND 500ft vertical
                if horizontal_dist < COLLISION_DISTANCE_NM and vertical_dist < COLLISION_ALTITUDE:
                    self.failed = True
                    self.failure_reason = f"COLLISION: {f1.callsign} and {f2.callsign}"
                    self.collision_pair = pair
                    self.save_score()  # Auto-save on collision
                    return
                
                # Near miss: within ~3000ft horizontal AND 1000ft vertical
                if horizontal_dist < NEAR_MISS_DISTANCE_NM and vertical_dist < NEAR_MISS_ALTITUDE:
                    current_near_misses.add(pair)
                    if pair not in self.active_near_misses:
                        self.near_miss_count += 1
        
        self.active_near_misses = current_near_misses
    
    def cleanup_flights(self) -> None:
        to_remove = []
        for callsign, flight in self.flights.items():
            if flight.status == FlightStatus.LANDED:
                if not hasattr(flight, '_counted'):
                    self.landed_count += 1
                    self.landed_flights.append(flight.to_history_data())
                    flight._counted = True
                    flight._landed_time = datetime.now()
                elif (datetime.now() - flight._landed_time).total_seconds() > 3:
                    to_remove.append(callsign)
            elif flight.status == FlightStatus.DEPARTED:
                if not hasattr(flight, '_counted'):
                    self.departed_count += 1
                    self.departed_flights.append(flight.to_history_data())
                    flight._counted = True
                    flight._departed_time = datetime.now()
                elif (datetime.now() - flight._departed_time).total_seconds() > 3:
                    to_remove.append(callsign)
        
        for callsign in to_remove:
            del self.flights[callsign]
    
    def save_score(self) -> dict:
        """Save the current score to file."""
        score = {
            "datetime": datetime.now().isoformat(),
            "landed": self.landed_count,
            "departed": self.departed_count,
            "near_misses": self.near_miss_count,
            "failed": self.failed,
            "failure_reason": self.failure_reason,
            "duration_seconds": (datetime.now() - self.session_start).total_seconds(),
        }
        
        scores = []
        if self.scores_file.exists():
            try:
                with open(self.scores_file, 'r') as f:
                    scores = json.load(f)
            except:
                scores = []
        
        scores.append(score)
        scores = scores[-100:]
        
        with open(self.scores_file, 'w') as f:
            json.dump(scores, f, indent=2)
        
        return score
    
    def update(self, dt: float) -> None:
        if self.failed:
            return
            
        dt *= self.speed_multiplier
        
        for flight in self.flights.values():
            flight.update(dt)
        
        self.check_separations()
        self.cleanup_flights()
    
    async def run(self) -> None:
        self.running = True
        last_update = datetime.now()
        
        while self.running:
            now = datetime.now()
            dt = (now - last_update).total_seconds()
            last_update = now
            
            self.update(dt)
            
            for callback in self.update_callbacks:
                await callback(
                    self.get_all_flights(), 
                    self.get_stats(), 
                    self.get_near_misses(),
                    self.get_flight_history()
                )
            
            await asyncio.sleep(0.1)
    
    def stop(self) -> None:
        self.running = False


# Global simulator instance
simulator = ATCSimulator()
