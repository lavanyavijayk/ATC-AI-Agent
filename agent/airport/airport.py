"""
Airport Module
==============
Manages airport operations including runway allocation and flight scheduling.

This module provides the Airport class which serves as the central coordinator
for managing runways and scheduling flights for landing, takeoff, and emergency
operations.
"""

import time
from typing import Optional, List

from airport.runway import Runway, RunwayStatus
from airport.scheduler import FlightScheduler, SlotInfo
from airport.flight import Flight, FlightStatus


class Airport:
    """
    Represents an airport with runways and flight scheduling capabilities.
    
    The Airport class manages:
    - Multiple runways and their availability
    - Flight scheduling for landings, takeoffs, and emergencies
    - Runway assignment based on priority queues
    
    Attributes:
        airport_code (str): ICAO/IATA airport identifier (e.g., 'JFK').
        airport_name (str): Full name of the airport.
        runways (List[Runway]): List of runways available at the airport.
        flight_scheduler (FlightScheduler): Scheduler managing flight priorities.
    
    Example:
        >>> airport = Airport("JFK", "John F. Kennedy International Airport")
        >>> runway = Runway("R1", "3R", "030")
        >>> airport.add_runway(runway)
    """
    
    def __init__(self, airport_code: str, airport_name: str) -> None:
        """
        Initialize an Airport instance.
        
        Args:
            airport_code: ICAO/IATA airport identifier.
            airport_name: Full name of the airport.
        """
        self.airport_code = airport_code
        self.airport_name = airport_name
        self.runways: List[Runway] = []
        self.flight_scheduler = FlightScheduler()
    
    def add_runway(self, runway: Runway) -> None:
        """
        Add a runway to the airport.
        
        Args:
            runway: Runway instance to add to the airport.
        """
        self.runways.append(runway)
    
    def get_available_runway(self) -> Optional[Runway]:
        """
        Find and return an available runway for operations.
        
        Iterates through all runways and returns the first one
        with AVAILABLE status.
        
        Returns:
            An available Runway instance, or None if all runways are occupied.
        """
        for runway in self.runways:
            if runway.status == RunwayStatus.AVAILABLE:
                return runway
        return None
    
    def schedule_landing(self, flight: Flight, landing_time: int, duration: int) -> None:
        """
        Schedule a flight for landing.
        
        Creates a time slot and adds the flight to the landing queue
        with priority based on landing time.
        
        Args:
            flight: Flight instance to schedule for landing.
            landing_time: Unix timestamp for scheduled landing.
            duration: Duration in seconds for the landing operation.
        """
        slot_info = SlotInfo(landing_time, landing_time + duration)
        self.flight_scheduler.add_landing(flight, landing_time, slot_info)
    
    def schedule_takeoff(self, flight: Flight, takeoff_time: int, duration: int) -> None:
        """
        Schedule a flight for takeoff.
        
        Creates a time slot and adds the flight to the takeoff queue
        with priority based on takeoff time.
        
        Args:
            flight: Flight instance to schedule for takeoff.
            takeoff_time: Unix timestamp for scheduled takeoff.
            duration: Duration in seconds for the takeoff operation.
        """
        slot_info = SlotInfo(takeoff_time, takeoff_time + duration)
        self.flight_scheduler.add_takeoff(flight, takeoff_time, slot_info)
    
    def schedule_mayday(self, flight: Flight, duration: int) -> None:
        """
        Schedule an emergency (MAYDAY) flight with highest priority.
        
        Emergency flights are scheduled immediately with the current time
        and receive the highest priority in the queue.
        
        Args:
            flight: Flight instance declaring emergency.
            duration: Duration in seconds for the emergency operation.
        """
        current_time = int(time.time())
        slot_info = SlotInfo(current_time, current_time + duration)
        self.flight_scheduler.add_mayday(flight, slot_info)
    
    def process_next_flight(self) -> bool:
        """
        Process the next highest priority flight in the schedule.
        
        Retrieves the next flight from the scheduler, finds an available
        runway, and assigns the flight to it.
        
        Returns:
            True if flight was successfully assigned to a runway,
            False if no flights pending or no runway available.
        """
        # Get next flight from priority queue
        next_entry = self.flight_scheduler.get_next_flight()
        if not next_entry:
            return False
        
        # Find available runway
        runway = self.get_available_runway()
        if not runway:
            print(f"[WARNING] No available runway for {next_entry.flight.flight_number}")
            return False
        
        # Assign flight to runway
        success = runway.assign_flight(
            next_entry.flight,
            next_entry.slot_info.start_time,
            next_entry.slot_info.end_time
        )
        
        if success:
            operation = next_entry.used_for.value
            print(f"[INFO] Assigned {next_entry.flight.flight_number} "
                  f"to {runway.runway_id} for {operation}")
        
        return success
    
    def __repr__(self) -> str:
        """Return string representation of the airport."""
        return (
            f"Airport({self.airport_code}, "
            f"runways={len(self.runways)}, "
            f"scheduled_flights={self.flight_scheduler.get_schedule_size()})"
        )


# =============================================================================
# Example Usage / Module Testing
# =============================================================================
if __name__ == "__main__":
    # Create airport instance
    airport = Airport("JFK", "John F. Kennedy International Airport")
    
    # Add runway (runway_id, name, direction)
    runway1 = Runway("R1", "3R", "030")
    airport.add_runway(runway1)
    print(f"Runway details: {airport.runways[0].get_runway_details()}")
    
    # Create sample flights
    flight1 = Flight("F001", "AA101", "LAX", "JFK")      # Arrival from LA
    flight2 = Flight("F002", "UA202", "ORD", "JFK")      # Arrival from Chicago
    flight3 = Flight("F003", "DL303", "JFK", "MIA")      # Departure to Miami
    emergency_flight = Flight("F004", "BA999", "LHR", "JFK")  # Emergency
    
    # Schedule flights with different priorities
    airport.schedule_landing(flight1, 1000, 300)   # Landing at time 1000
    airport.schedule_takeoff(flight3, 1100, 200)   # Takeoff at time 1100
    airport.schedule_landing(flight2, 1050, 300)   # Landing at time 1050
    airport.schedule_mayday(emergency_flight, 400) # Emergency - highest priority
    
    # Display airport status
    print(f"\n{airport}")
    print(f"Scheduled flights: {airport.flight_scheduler.get_schedule_size()}\n")
    
    # Process all flights in priority order
    print("Processing flights in priority order:")
    print("-" * 50)
    while airport.flight_scheduler.get_schedule_size() > 0:
        airport.process_next_flight()
