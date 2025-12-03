#!/usr/bin/env python3
"""
ATC AI Agent - Main Entry Point
================================
Continuously monitors flights from the simulator and processes them
through the AI-powered ATC agent.

Usage:
    python main.py

Requires:
    - ATC Simulator running at http://localhost:8000
    - GEMINI_API_KEY in .env file
"""
import time
import requests

from database import FlightDatabase
from core import Airport, Runway
from agent import ATCAgent


# Configuration
SIMULATOR_URL = "http://localhost:8000/api"
POLL_INTERVAL = 5  # seconds


def create_airport() -> Airport:
    """Create the airport configuration (KRNT - Renton Municipal)"""
    airport = Airport("KRNT", "Renton Municipal Airport")
    runway = Runway("R1", "34", "340")
    airport.add_runway(runway)
    return airport


def should_process_flight(flight: dict, db_record: dict | None) -> bool:
    """
    Determine if a flight needs processing.
    
    A flight should be processed if:
    - It's new (no DB record)
    - Its status changed
    - Its passed_waypoints changed
    - It reached its target waypoint
    - It's a departure waiting for takeoff clearance
    """
    # Skip flights actively landing or taking off
    if flight["status"] in ["landing", "takeoff"]:
        return False
    
    # New flight
    if not db_record:
        return True
    
    # Status or waypoints changed
    if (db_record["status"] != flight["status"] or
        db_record["passed_waypoints"] != flight["passed_waypoints"]):
        return True
    
    # Reached target waypoint
    if (flight['passed_waypoints'] and 
        flight['passed_waypoints'][-1] == flight['target_waypoint']):
        return True
    
    # Departure waiting for clearance
    if (flight['flight_type'] == "departure" and 
        not flight['cleared_for_takeoff']):
        return True
    
    return False


def process_flight(flight: dict, airport: Airport):
    """Process a single flight through the ATC agent"""
    from agent.atc_agent import process_flight as agent_process
    agent_process(flight, airport)


def main():
    """Main loop - poll simulator and process flights"""
    print("=" * 60)
    print("  ATC AI Agent Starting...")
    print("=" * 60)
    print(f"  Simulator URL: {SIMULATOR_URL}")
    print(f"  Poll Interval: {POLL_INTERVAL}s")
    print("=" * 60 + "\n")
    
    db = FlightDatabase()
    airport = create_airport()
    
    while True:
        try:
            # Fetch landing flights
            response = requests.get(f"{SIMULATOR_URL}/flights/landing/", timeout=10)
            
            if response.status_code == 200:
                flights = response.json()
                
                for flight in flights:
                    callsign = flight.get("callsign")
                    
                    # Check database for existing record
                    existing = db.get_flights(callsign=callsign)
                    db_record = existing[0] if existing else None
                    
                    # Update or insert DB record
                    if not db_record:
                        db.insert_flight(flight)
                    else:
                        db.update_flight(db_record["id"], flight)
                    
                    # Process if needed
                    if should_process_flight(flight, db_record):
                        print(f"\n[Main] Processing flight: {callsign}")
                        process_flight(flight, airport)
            else:
                print(f"[Main] Error fetching flights: {response.status_code}")
        
        except requests.exceptions.ConnectionError:
            print("[Main] Cannot connect to simulator. Is it running?")
        except Exception as e:
            print(f"[Main] Error: {e}")
        
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
