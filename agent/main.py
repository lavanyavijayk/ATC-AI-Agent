import requests
import time
from database.flights_db import FlightDatabase
from airport.airport import Airport
from airport.runway import Runway
from atc_agent import main
from config import API_BASE_URL


db = FlightDatabase()

URL = f"{API_BASE_URL}/flights/"
SLEEP_SECONDS = 5

airport = Airport("JFK", "John F. Kennedy International Airport")
runway1 = Runway("R1", "21L", "340")
airport.add_runway(runway1)

while True:
    try:
        response = requests.get(URL)

        if response.status_code == 200:
            flights_data = response.json()

            for flight in flights_data:
                callsign = flight.get("callsign")
                existing = db.get_flights(callsign=callsign)

                updated = False

                if not existing:
                    db.insert_flight(flight)
                    updated = True

                else:
                    db_data = existing[0]

                    if (
                        db_data["status"] != flight["status"] or
                        db_data["passed_waypoints"] != flight["passed_waypoints"]
                    ):
                        updated = True

                    db.update_flight(db_data["id"], flight)
                if flight['passed_waypoints'] and flight['passed_waypoints'][-1] == flight['target_waypoint']:
                    updated = True
                else:
                    updated = False

                if flight["status"] in ["landing", "takeoff"]:
                    continue

                if updated or (flight['status']=="ready_for_takeoff" and not flight['cleared_for_takeoff']) or not flight['target_waypoint']:
                    main(flight, airport)

        else:
            print("Error fetching flights:", response.status_code)

    except Exception as e:
        print("Error:", e)

    time.sleep(SLEEP_SECONDS)
