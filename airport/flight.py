"""
Flight Module
=============
Defines flight-related data structures for air traffic control operations.

This module provides:
- FlightStatus enum for tracking flight operation types
- Flight class representing individual aircraft in the system
"""

from enum import Enum
from typing import Optional


class FlightStatus(Enum):
    """
    Enumeration of possible flight operation statuses.
    
    Used to categorize flights based on their current operation type
    in the air traffic control system.
    
    Attributes:
        LANDING: Flight is approaching for landing.
        TAKEOFF: Flight is scheduled for departure.
        MAYDAY: Flight has declared an emergency (highest priority).
    """
    LANDING = "landing"
    TAKEOFF = "takeoff"
    MAYDAY = "mayday"


class Flight:
    """
    Represents a unique flight in the air traffic control system.
    
    Each flight has identifiers, route information, and timing data
    for scheduling and tracking purposes.
    
    Attributes:
        flight_id (str): Internal unique identifier for the flight.
        flight_number (str): Public flight number (e.g., 'AA101', 'UA202').
        origin (str): ICAO/IATA code of departure airport.
        destination (str): ICAO/IATA code of arrival airport.
        scheduled_time (Optional[int]): Scheduled operation time (Unix timestamp).
        actual_time (Optional[int]): Actual operation time (Unix timestamp).
    
    Example:
        >>> flight = Flight("F001", "AA101", "LAX", "JFK")
        >>> print(flight)
        Flight(AA101, LAX->JFK)
    """
    
    def __init__(
        self,
        flight_id: str,
        flight_number: str,
        origin: str,
        destination: str
    ) -> None:
        """
        Initialize a Flight instance.
        
        Args:
            flight_id: Internal unique identifier for the flight.
            flight_number: Public-facing flight number (e.g., 'AA101').
            origin: ICAO/IATA code of the departure airport.
            destination: ICAO/IATA code of the arrival airport.
        """
        self.flight_id = flight_id
        self.flight_number = flight_number
        self.origin = origin
        self.destination = destination
        
        # Timing attributes (set during scheduling)
        self.scheduled_time: Optional[int] = None
        self.actual_time: Optional[int] = None
    
    def __repr__(self) -> str:
        """Return string representation of the flight."""
        return f"Flight({self.flight_number}, {self.origin}->{self.destination})"


# =============================================================================
# Example Usage / Module Testing
# =============================================================================
if __name__ == "__main__":
    # Create sample flights
    arrival = Flight("F001", "AA101", "LAX", "JFK")
    departure = Flight("F002", "DL303", "JFK", "MIA")
    emergency = Flight("F003", "BA999", "LHR", "JFK")
    
    # Display flight information
    print(f"Arrival: {arrival}")
    print(f"Departure: {departure}")
    print(f"Emergency: {emergency}")
    
    # Display available flight statuses
    print("\nAvailable flight statuses:")
    for status in FlightStatus:
        print(f"  - {status.name}: {status.value}")
