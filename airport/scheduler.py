from airport.flight import Flight, FlightStatus
from typing import List, Optional
import heapq
import time


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

