import heapq
import time
from enum import Enum
from datetime import datetime
from typing import Optional, List, Tuple
import time

class FlightStatus(Enum):
    LANDING = "landing"
    TAKEOFF = "takeoff"
    MAYDAY = "mayday"

class RunwayStatus(Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"

class Flight:
    """Represents a unique flight"""
    def __init__(self, flight_id: str, flight_number: str, origin: str, destination: str):
        self.flight_id = flight_id
        self.flight_number = flight_number
        self.origin = origin
        self.destination = destination
        self.scheduled_time: Optional[int] = None
        self.actual_time: Optional[int] = None
    
    def __repr__(self):
        return f"Flight({self.flight_number}, {self.origin}->{self.destination})"

class SlotInfo:
    """Contains time slot information for a flight operation"""
    def __init__(self, start_time: int, end_time: int):
        self.start_time = start_time
        self.end_time = end_time
    
    def __repr__(self):
        return f"SlotInfo({self.start_time}-{self.end_time})"

class ScheduleEntry:
    """Entry in the flight scheduler heap"""
    def __init__(self, value: int, flight: Flight, slot_info: SlotInfo, used_for: FlightStatus):
        self.value = value
        self.flight = flight
        self.slot_info = slot_info
        self.used_for = used_for
    
    def __lt__(self, other):
        """For heap comparison - lower value has higher priority"""
        return self.value < other.value
    
    def __repr__(self):
        return f"ScheduleEntry(value={self.value}, flight={self.flight.flight_number}, used_for={self.used_for.value})"

class FlightScheduler:
    """Manages flight schedules using a min-heap priority queue"""
    def __init__(self):
        self.schedule_heap: List[ScheduleEntry] = []
    
    def add_landing(self, flight: Flight, landing_time: int, slot_info: SlotInfo):
        """Add a landing flight to schedule (priority = landing_time)"""
        entry = ScheduleEntry(landing_time, flight, slot_info, FlightStatus.LANDING)
        heapq.heappush(self.schedule_heap, entry)
    
    def add_takeoff(self, flight: Flight, scheduled_time: int, slot_info: SlotInfo):
        """Add a takeoff flight to schedule (priority = scheduled_time)"""
        entry = ScheduleEntry(scheduled_time, flight, slot_info, FlightStatus.TAKEOFF)
        heapq.heappush(self.schedule_heap, entry)
    
    def add_mayday(self, flight: Flight, slot_info: SlotInfo):
        """Add a mayday/emergency flight (priority = -1, highest priority)"""
        entry = ScheduleEntry(-1, flight, slot_info, FlightStatus.MAYDAY)
        heapq.heappush(self.schedule_heap, entry)
    
    def get_next_flight(self) -> Optional[ScheduleEntry]:
        """Get the highest priority flight from schedule"""
        if self.schedule_heap:
            return heapq.heappop(self.schedule_heap)
        return None
    
    def peek_next_flight(self) -> Optional[ScheduleEntry]:
        """Peek at the highest priority flight without removing it"""
        if self.schedule_heap:
            return self.schedule_heap[0]
        return None
    
    def get_schedule_size(self) -> int:
        """Get the number of flights in schedule"""
        return len(self.schedule_heap)
    
    def delay_flights(self, delay_in_mins):
        # new start time after applying delay
        delay = time.time() + delay_in_mins    # int

        for flight in self.schedule_heap:
            start, end = flight.slot_info
            if start > delay:
                break

            interval = end - start
            new_start = delay + 2
            new_end = new_start + interval
            # update the slot_info
            flight.slot_info[0] = new_start
            flight.slot_info[1] = new_end
            # next delay is this flight’s end
            delay = new_end
        return


    def __repr__(self):
        return f"FlightScheduler(pending_flights={len(self.schedule_heap)})"

class Runway:
    """Represents a runway with its current status and usage"""
    def __init__(self, runway_id: str, runway_name: str, direction:str):
        self.runway_id = runway_id
        self.status = RunwayStatus.AVAILABLE
        self.current_flight: Optional[Flight] = None
        self.operation_start_time: Optional[int] = None
        self.operation_end_time: Optional[int] = None
        self.direction = direction
        # self.direction2 = direction2
        self.runway_name = runway_name
        # self.direction2_runway_name = direction2_runway_name
        # self.landed_flights: List[Flight] = []
        # self.departed_flights: List[Flight] = []
    
    def get_runway_details(self):
        if self.operation_end_time and self.operation_end_time <=time.time():
            self.complete_landing_or_takeoff()
        return f"""the runway name is
        {self.runway_name} with a heading {self.direction}, The current status of this runway is {self.status}.
        {"and prev aloted slot end time is"+str(self.operation_end_time) if self.operation_end_time else ""}"""


    def assign_flight(self, flight: Flight, start_time: int, end_time: int):
        """Assign a flight to this runway"""
        if self.status == RunwayStatus.AVAILABLE:
            self.status = RunwayStatus.OCCUPIED
            self.current_flight = flight
            self.operation_start_time = start_time
            self.operation_end_time = end_time
            return True
        return False
    
    def complete_landing_or_takeoff(self):
        """Mark landing operation as complete"""
        if self.current_flight:
            self.release_runway()
    
    def release_runway(self):
        """Release the runway after operation"""
        self.status = RunwayStatus.AVAILABLE
        self.current_flight = None
        self.operation_start_time = None
        self.operation_end_time = None
    
    def set_maintenance(self):
        """Set runway to maintenance mode"""
        self.status = RunwayStatus.MAINTENANCE
    
    def __repr__(self):
        return f"Runway({self.runway_id}, status={self.status.value}, current={self.current_flight})"

class Airport:
    """Represents an airport with runways and flight scheduler"""
    def __init__(self, airport_code: str, airport_name: str):
        self.airport_code = airport_code
        self.airport_name = airport_name
        self.runways: List[Runway] = []
        self.flight_scheduler = FlightScheduler()
    
    def add_runway(self, runway: Runway):
        """Add a runway to the airport"""
        self.runways.append(runway)
    
    def get_available_runway(self) -> Optional[Runway]:
        """Get an available runway for operations"""
        for runway in self.runways:
            if runway.status == RunwayStatus.AVAILABLE:
                return runway
        return None
    
    def schedule_landing(self, flight: Flight, landing_time: int, duration: int):
        """Schedule a landing flight"""
        slot_info = SlotInfo(landing_time, landing_time + duration)
        self.flight_scheduler.add_landing(flight, landing_time, slot_info)
    
    def schedule_takeoff(self, flight: Flight, takeoff_time: int, duration: int):
        """Schedule a takeoff flight"""
        slot_info = SlotInfo(takeoff_time, takeoff_time + duration)
        self.flight_scheduler.add_takeoff(flight, takeoff_time, slot_info)
    
    def schedule_mayday(self, flight: Flight, duration: int):
        """Schedule an emergency/mayday flight"""
        current_time = time.time()
        slot_info = SlotInfo(current_time, current_time + duration)
        self.flight_scheduler.add_mayday(flight, slot_info)
    
    def process_next_flight(self) -> bool:
        """Process the next flight in the schedule"""
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
            operation = next_entry.used_for.value
            print(f"Assigned {next_entry.flight.flight_number} to {runway.runway_id} for {operation}")
        
        return success
    
    def __repr__(self):
        return f"Airport({self.airport_code}, runways={len(self.runways)}, scheduled_flights={self.flight_scheduler.get_schedule_size()})"


# Example Usage
if __name__ == "__main__":
    # Create airport
    airport = Airport("JFK", "John F. Kennedy International Airport")
    
    # Add runways
    runway1 = Runway("R1", "3R", "21L", "30.8", "210.8")
    airport.add_runway(runway1)
    print(airport.runways[0].get_flight_details())
    # Create flights
    flight1 = Flight("F001", "AA101", "LAX", "JFK")
    flight2 = Flight("F002", "UA202", "ORD", "JFK")
    flight3 = Flight("F003", "DL303", "JFK", "MIA")
    emergency_flight = Flight("F004", "BA999", "LHR", "JFK")
    
    # Schedule flights
    airport.schedule_landing(flight1, 1000, 300)  # Landing at time 1000
    airport.schedule_takeoff(flight3, 1100, 200)  # Takeoff at time 1100
    airport.schedule_landing(flight2, 1050, 300)  # Landing at time 1050
    airport.schedule_mayday(emergency_flight, 400)  # Emergency - highest priority
    
    print(f"\n{airport}")
    print(f"Scheduled flights: {airport.flight_scheduler.get_schedule_size()}\n")
    
    # Process flights in priority order
    print("Processing flights:")
    while airport.flight_scheduler.get_schedule_size() > 0:
        airport.process_next_flight()
        print()