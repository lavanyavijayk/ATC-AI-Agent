"""
Core Domain Models: Flight, Airport, Runway
"""
import heapq
import time
from enum import Enum
from typing import Optional, List


class FlightStatus(Enum):
    """Flight operation status"""
    LANDING = "landing"
    TAKEOFF = "takeoff"
    MAYDAY = "mayday"


class RunwayStatus(Enum):
    """Runway availability status"""
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"


class Flight:
    """Represents a flight in the system"""
    
    def __init__(
        self,
        flight_id: str,
        flight_number: str,
        origin: str,
        destination: str
    ):
        self.flight_id = flight_id
        self.flight_number = flight_number
        self.origin = origin
        self.destination = destination
        self.scheduled_time: Optional[int] = None
        self.actual_time: Optional[int] = None
    
    def __repr__(self):
        return f"Flight({self.flight_number}, {self.origin}->{self.destination})"


class SlotInfo:
    """Time slot information for runway operations"""
    
    def __init__(self, start_time: int, end_time: int):
        self.start_time = start_time
        self.end_time = end_time
    
    def __repr__(self):
        return f"SlotInfo({self.start_time}-{self.end_time})"


class ScheduleEntry:
    """Entry in the flight scheduler heap"""
    
    def __init__(
        self,
        value: int,
        flight: Flight,
        slot_info: SlotInfo,
        used_for: FlightStatus
    ):
        self.value = value
        self.flight = flight
        self.slot_info = slot_info
        self.used_for = used_for
    
    def __lt__(self, other):
        return self.value < other.value
    
    def __repr__(self):
        return f"ScheduleEntry(value={self.value}, flight={self.flight.flight_number})"


class FlightScheduler:
    """Manages flight schedules using a min-heap priority queue"""
    
    def __init__(self):
        self.schedule_heap: List[ScheduleEntry] = []
    
    def add_landing(self, flight: Flight, landing_time: int, slot_info: SlotInfo):
        entry = ScheduleEntry(landing_time, flight, slot_info, FlightStatus.LANDING)
        heapq.heappush(self.schedule_heap, entry)
    
    def add_takeoff(self, flight: Flight, scheduled_time: int, slot_info: SlotInfo):
        entry = ScheduleEntry(scheduled_time, flight, slot_info, FlightStatus.TAKEOFF)
        heapq.heappush(self.schedule_heap, entry)
    
    def add_mayday(self, flight: Flight, slot_info: SlotInfo):
        entry = ScheduleEntry(-1, flight, slot_info, FlightStatus.MAYDAY)
        heapq.heappush(self.schedule_heap, entry)
    
    def get_next_flight(self) -> Optional[ScheduleEntry]:
        if self.schedule_heap:
            return heapq.heappop(self.schedule_heap)
        return None
    
    def peek_next_flight(self) -> Optional[ScheduleEntry]:
        if self.schedule_heap:
            return self.schedule_heap[0]
        return None
    
    def get_schedule_size(self) -> int:
        return len(self.schedule_heap)


class Runway:
    """Represents a runway with status and scheduling"""
    
    def __init__(self, runway_id: str, runway_name: str, direction: str):
        self.runway_id = runway_id
        self.runway_name = runway_name
        self.direction = direction
        self.status = RunwayStatus.AVAILABLE
        self.current_flight: Optional[Flight] = None
        self.operation_start_time: Optional[int] = None
        self.operation_end_time: Optional[int] = None
    
    def get_runway_details(self) -> str:
        if self.operation_end_time and self.operation_end_time <= time.time():
            self.complete_operation()
        
        details = f"Runway {self.runway_name} (HDG {self.direction}), Status: {self.status.value}"
        if self.operation_end_time:
            details += f", Slot ends: {self.operation_end_time}"
        return details
    
    def assign_flight(self, flight: Flight, start_time: int, end_time: int) -> bool:
        if self.status == RunwayStatus.AVAILABLE:
            self.status = RunwayStatus.OCCUPIED
            self.current_flight = flight
            self.operation_start_time = start_time
            self.operation_end_time = end_time
            return True
        return False
    
    def complete_operation(self):
        if self.current_flight:
            self.release_runway()
    
    def release_runway(self):
        self.status = RunwayStatus.AVAILABLE
        self.current_flight = None
        self.operation_start_time = None
        self.operation_end_time = None
    
    def set_maintenance(self):
        self.status = RunwayStatus.MAINTENANCE
    
    def __repr__(self):
        return f"Runway({self.runway_id}, {self.status.value})"


class Airport:
    """Represents an airport with runways and flight scheduling"""
    
    def __init__(self, airport_code: str, airport_name: str):
        self.airport_code = airport_code
        self.airport_name = airport_name
        self.runways: List[Runway] = []
        self.flight_scheduler = FlightScheduler()
    
    def add_runway(self, runway: Runway):
        self.runways.append(runway)
    
    @property
    def runway(self) -> Optional[Runway]:
        """Get the first runway (for single-runway airports)"""
        return self.runways[0] if self.runways else None
    
    def get_available_runway(self) -> Optional[Runway]:
        for runway in self.runways:
            if runway.status == RunwayStatus.AVAILABLE:
                return runway
        return None
    
    def schedule_landing(self, flight: Flight, landing_time: int, duration: int):
        slot_info = SlotInfo(landing_time, landing_time + duration)
        self.flight_scheduler.add_landing(flight, landing_time, slot_info)
    
    def schedule_takeoff(self, flight: Flight, takeoff_time: int, duration: int):
        slot_info = SlotInfo(takeoff_time, takeoff_time + duration)
        self.flight_scheduler.add_takeoff(flight, takeoff_time, slot_info)
    
    def process_next_flight(self) -> bool:
        next_entry = self.flight_scheduler.get_next_flight()
        if not next_entry:
            return False
        
        runway = self.get_available_runway()
        if not runway:
            print(f"No available runway for {next_entry.flight.flight_number}")
            return False
        
        success = runway.assign_flight(
            next_entry.flight,
            next_entry.slot_info.start_time,
            next_entry.slot_info.end_time
        )
        
        if success:
            print(f"Assigned {next_entry.flight.flight_number} to {runway.runway_id}")
        
        return success
    
    def __repr__(self):
        return f"Airport({self.airport_code}, runways={len(self.runways)})"

