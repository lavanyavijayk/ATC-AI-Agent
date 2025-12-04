import sqlite3
import json
from typing import Dict, Any, Optional, List

DB_NAME = "atc.db"

class FlightDatabase:
    def __init__(self, db_path: str = DB_NAME):
        self.db_path = db_path
        if not self._table_exists("flights"):
            self._create_table()

    def _table_exists(self, table_name: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name=?;
        """, (table_name,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def _create_table(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE flights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                callsign TEXT,
                flight_type TEXT,
                status TEXT,
                position_x REAL,
                position_y REAL,
                altitude INTEGER,
                speed REAL,
                heading REAL,
                target_altitude INTEGER,
                target_speed REAL,
                target_heading REAL,
                target_waypoint TEXT,
                aircraft_type TEXT,
                origin TEXT,
                destination TEXT,
                cleared_to_land INTEGER,
                cleared_for_takeoff INTEGER,
                passed_waypoints TEXT,
                clearance_denial_reason TEXT,
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        conn.close()

    # ---------------------------
    # Insert a new flight
    # ---------------------------
    def insert_flight(self, flight: dict) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO flights (
                callsign, flight_type, status,
                position_x, position_y,
                altitude, speed, heading,
                target_altitude, target_speed, target_heading,
                target_waypoint,
                aircraft_type, origin, destination,
                cleared_to_land, cleared_for_takeoff,
                passed_waypoints, clearance_denial_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            flight.get("callsign"),
            flight.get("flight_type"),
            flight.get("status"),
            flight.get("position", {}).get("x") if flight.get("position") else None,
            flight.get("position", {}).get("y") if flight.get("position") else None,
            flight.get("altitude"),
            flight.get("speed"),
            flight.get("heading"),
            flight.get("target_altitude"),
            flight.get("target_speed"),
            flight.get("target_heading"),
            flight.get("target_waypoint"),
            flight.get("aircraft_type"),
            flight.get("origin"),
            flight.get("destination"),
            int(flight.get("cleared_to_land", False)),
            int(flight.get("cleared_for_takeoff", False)),
            json.dumps(flight.get("passed_waypoints", [])),
            flight.get("clearance_denial_reason")
        ))

        conn.commit()
        flight_id = cursor.lastrowid
        conn.close()
        return flight_id


    # ---------------------------
    # Fetch flights optionally by callsign or status
    # ---------------------------
    def get_flights(self, callsign: Optional[str] = None, status: Optional[str] = None) -> list:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM flights"
        params = []
        clauses = []

        if callsign:
            clauses.append("callsign = ?")
            params.append(callsign)
        if status:
            clauses.append("status = ?")
            params.append(status)

        if clauses:
            query += " WHERE " + " AND ".join(clauses)

        query += " ORDER BY created_time DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        flights = []
        for row in rows:
            flights.append({
                "id": row[0],
                "callsign": row[1],
                "flight_type": row[2],
                "status": row[3],
                "position": {"x": row[4], "y": row[5]},
                "altitude": row[6],
                "speed": row[7],
                "heading": row[8],
                "target_altitude": row[9],
                "target_speed": row[10],
                "target_heading": row[11],
                "target_waypoint": row[12],
                "aircraft_type": row[13],
                "origin": row[14],
                "destination": row[15],
                "cleared_to_land": bool(row[16]),
                "cleared_for_takeoff": bool(row[17]),
                "passed_waypoints": json.loads(row[18]) if row[18] else [],
                "clearance_denial_reason": row[19],
                "created_time": row[20]
            })
        return flights
    
    def update_status(self, flight_id: int, status: str):
        """
        Update the status of a flight.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE flights
            SET status = ?
            WHERE id = ?
        """, (status, flight_id))

        conn.commit()
        conn.close()

    # ---------------------------
    # Update flight clearance
    # ---------------------------
    def update_clearance(self, flight_id: int, cleared_to_land: Optional[bool] = None, cleared_for_takeoff: Optional[bool] = None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        updates = []
        params = []

        if cleared_to_land is not None:
            updates.append("cleared_to_land = ?")
            params.append(int(cleared_to_land))
        if cleared_for_takeoff is not None:
            updates.append("cleared_for_takeoff = ?")
            params.append(int(cleared_for_takeoff))

        if updates:
            query = f"UPDATE flights SET {', '.join(updates)} WHERE id = ?"
            params.append(flight_id)
            cursor.execute(query, params)
            conn.commit()

        conn.close()

    def update_flight(self, flight_id: int, updates: Dict[str, Any]):
        """
        Dynamically update any field(s) using a dict.
        Special handling for:
        - position.x / position.y
        - passed_waypoints (stored as JSON)
        """

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        set_parts = []
        params = []

        mapping = {
            "flight_type": "flight_type",
            "status": "status",
            "aircraft_type": "aircraft_type",
            "origin": "origin",
            "destination": "destination",
            "cleared_to_land": "cleared_to_land",
            "cleared_for_takeoff": "cleared_for_takeoff",
            "altitude": "altitude",
            "speed": "speed",
            "heading": "heading",
            "target_altitude": "target_altitude",
            "target_speed": "target_speed",
            "target_heading": "target_heading",
            "target_waypoint": "target_waypoint",
            "clearance_denial_reason": "clearance_denial_reason",
        }

        for key, col in mapping.items():
            if key in updates:
                value = updates[key]
                if key in ["cleared_to_land", "cleared_for_takeoff"]:
                    value = int(value)
                set_parts.append(f"{col}=?")
                params.append(value)

        # position
        if "position" in updates:
            set_parts.append("position_x=?")
            params.append(updates["position"].get("x"))
            set_parts.append("position_y=?")
            params.append(updates["position"].get("y"))

        # passed_waypoints
        if "passed_waypoints" in updates:
            set_parts.append("passed_waypoints=?")
            params.append(json.dumps(updates["passed_waypoints"]))

        if set_parts:
            query = "UPDATE flights SET " + ", ".join(set_parts) + " WHERE id=?"
            params.append(flight_id)
            cursor.execute(query, params)
            conn.commit()

        conn.close()

if __name__ == "__main__":

    db = FlightDatabase()

    # Insert flight
    flight_id = db.insert_flight({
        "callsign": "UAL4527",
        "flight_type": "arrival",
        "status": "approaching",
        "aircraft_type": "B738",
        "origin": "KSEA",
        "destination": "KRNT",
        "cleared_to_land": False,
        "cleared_for_takeoff": False
    })

    print("Inserted flight ID:", flight_id)

    # Get all flights
    flights = db.get_flights()
    print(flights)

    # Update clearance
    db.update_clearance(flight_id, cleared_to_land=True)

    # Get flight again
    updated_flight = db.get_flights(callsign="UAL4527")
    print(updated_flight)
