"""
Runway Module
=============
Manages runway operations and status tracking for air traffic control.

This module provides:
- RunwayStatus enum for tracking runway availability
- Runway class for managing individual runway operations
"""

import time
from enum import Enum
from typing import Optional

from airport.flight import Flight


class RunwayStatus(Enum):
    """
    Enumeration of possible runway statuses.
    
    Used to track the current operational state of a runway
    in the air traffic control system.
    
    Attributes:
        AVAILABLE: Runway is free and can accept flight operations.
        OCCUPIED: Runway is currently in use by a flight.
        MAINTENANCE: Runway is closed for maintenance activities.
    """
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"


class Runway:
    """
    Represents a runway with its current status and usage tracking.
    
    Manages runway operations including flight assignments, status tracking,
    and automatic completion of landing/takeoff operations.
    
    Attributes:
        runway_id (str): Unique identifier for the runway.
        runway_name (str): Human-readable runway designation (e.g., '3R', '21L').
        direction (str): Runway heading in degrees (e.g., '030', '210').
        status (RunwayStatus): Current operational status of the runway.
        current_flight (Optional[Flight]): Flight currently using the runway.
        operation_start_time (Optional[int]): Start time of current operation.
        operation_end_time (Optional[int]): End time of current operation.
    
    Example:
        >>> runway = Runway("R1", "3R", "030")
        >>> print(runway)
        Runway(R1, status=available, current=None)
    """
    
    def __init__(self, runway_id: str, runway_name: str, direction: str) -> None:
        """
        Initialize a Runway instance.
        
        Args:
            runway_id: Unique identifier for the runway.
            runway_name: Human-readable runway designation.
            direction: Runway heading in degrees.
        """
        self.runway_id = runway_id
        self.runway_name = runway_name
        self.direction = direction
        
        # Operational state
        self.status = RunwayStatus.AVAILABLE
        self.current_flight: Optional[Flight] = None
        
        # Time slot tracking
        self.operation_start_time: Optional[int] = None
        self.operation_end_time: Optional[int] = None
    
    def get_runway_details(self) -> str:
        """
        Get detailed information about the runway's current state.
        
        Automatically completes any expired operations before
        returning the runway details.
        
        Returns:
            Formatted string with runway name, heading, status,
            and slot end time if applicable.
        """
        # Auto-complete expired operations
        if self.operation_end_time and self.operation_end_time <= time.time():
            self.complete_landing_or_takeoff()
        
        # Build details string
        details = (
            f"Runway {self.runway_name} with heading {self.direction}. "
            f"Current status: {self.status.value}."
        )
        
        # Add slot end time if runway is occupied
        if self.operation_end_time:
            details += f" Slot end time: {self.operation_end_time}."
        
        return details
    
    def assign_flight(
        self,
        flight: Flight,
        start_time: int,
        end_time: int
    ) -> bool:
        """
        Assign a flight to this runway for operation.
        
        Only succeeds if the runway is currently available.
        
        Args:
            flight: Flight to assign to the runway.
            start_time: Unix timestamp for operation start.
            end_time: Unix timestamp for operation end.
        
        Returns:
            True if assignment succeeded, False if runway not available.
        """
        if self.status != RunwayStatus.AVAILABLE:
            return False
        
        # Update runway state
        self.status = RunwayStatus.OCCUPIED
        self.current_flight = flight
        self.operation_start_time = start_time
        self.operation_end_time = end_time
        
        return True
    
    def complete_landing_or_takeoff(self) -> None:
        """
        Mark the current landing or takeoff operation as complete.
        
        Releases the runway if there is a flight currently assigned.
        """
        if self.current_flight:
            self.release_runway()
    
    def release_runway(self) -> None:
        """
        Release the runway after operation completion.
        
        Resets all operational state to default values,
        making the runway available for new assignments.
        """
        self.status = RunwayStatus.AVAILABLE
        self.current_flight = None
        self.operation_start_time = None
        self.operation_end_time = None
    
    def set_maintenance(self) -> None:
        """
        Set runway to maintenance mode.
        
        Marks the runway as unavailable for flight operations
        due to maintenance activities.
        """
        self.status = RunwayStatus.MAINTENANCE
    
    def __repr__(self) -> str:
        """Return string representation of the runway."""
        return (
            f"Runway({self.runway_id}, "
            f"status={self.status.value}, "
            f"current={self.current_flight})"
        )


# =============================================================================
# Example Usage / Module Testing
# =============================================================================
if __name__ == "__main__":
    from airport.flight import Flight
    
    # Create runway
    runway = Runway("R1", "3R", "030")
    print(f"Initial state: {runway}")
    print(f"Details: {runway.get_runway_details()}")
    
    # Create and assign a flight
    flight = Flight("F001", "AA101", "LAX", "JFK")
    current_time = int(time.time())
    
    success = runway.assign_flight(flight, current_time, current_time + 300)
    print(f"\nAssignment successful: {success}")
    print(f"After assignment: {runway}")
    print(f"Details: {runway.get_runway_details()}")
    
    # Release runway
    runway.release_runway()
    print(f"\nAfter release: {runway}")
    
    # Set maintenance
    runway.set_maintenance()
    print(f"After maintenance: {runway}")
    
    # Display available statuses
    print("\nAvailable runway statuses:")
    for status in RunwayStatus:
        print(f"  - {status.name}: {status.value}")
