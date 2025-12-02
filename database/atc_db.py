import sqlite3
import json
from typing import Dict, Any, Optional, List


DB_NAME = "atc.db"
TABLE_NAME = "atc_communication"


class ATCDatabase:
    def __init__(self, db_path: str = DB_NAME):
        self.db_path = db_path
        # Create table only if it doesn't exist
        if not self._table_exists(TABLE_NAME):
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

    # ---------------------------
    # Internal: Create table once
    # ---------------------------
    def _create_table(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            command TEXT,
            result TEXT,
            flight_id TEXT,
            flight_info TEXT,
            retry_count INTEGER,
            created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        conn.commit()
        conn.close()

    # ---------------------------
    # Insert a new communication
    # ---------------------------
    def insert_record(
        self,
        command: Dict[str, Any],
        result: Dict[str, Any],
        flight_id: str,
        flight_info: Dict[str, Any],
        retry_count: int = 0) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f""" INSERT INTO {TABLE_NAME} (command, result, flight_id, flight_info, retry_count)
            VALUES (?, ?, ?, ?, ?)""", (json.dumps(command),json.dumps(result),flight_id,json.dumps(flight_info),retry_count))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()

        return last_id


    def get_records(self, flight_id: Optional[str] = None, last_minutes: Optional[int] = None ) -> List[dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        query = f"SELECT * FROM {TABLE_NAME}"
        params = []

        clauses = []

        # Filter by flight_id if provided
        if flight_id:
            clauses.append("flight_id = ?")
            params.append(flight_id)

        # Filter by time window if provided
        if last_minutes is not None:
            clauses.append("created_time >= datetime('now', ?)")
            params.append(f"-{last_minutes} minutes")

        # Build WHERE clause
        if clauses:
            query += " WHERE " + " AND ".join(clauses)

        query += " ORDER BY created_time DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "command": json.loads(row[1]),
                "result": json.loads(row[2]),
                "flight_id": row[3],
                "flight_info": json.loads(row[4]),
                "retry_count": row[5],
                "created_time": row[6]
            })
        return results


    # ---------------------------
    # Update retry count
    # ---------------------------
    def update_retry_count(self, record_id: int, retry_count: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(f"""
            UPDATE {TABLE_NAME}
            SET retry_count = ?
            WHERE id = ?
        """, (retry_count, record_id))

        conn.commit()
        conn.close()


# ---------------------------
# Example usage
# ---------------------------
if __name__ == "__main__":
    db = ATCDatabase()

    # Insert sample data
    new_id = db.insert_record(
        command={"action": "descend", "altitude": 3000},
        result={"status": "ok"},
        flight_id="AI204",
        flight_info={"type": "A320", "origin": "DEL", "destination": "MAA"},
        retry_count=0
    )

    print(f"Inserted record with ID: {new_id}")

    # Fetch all
    all_data = db.get_records()
    print("All records:", all_data)

    # Fetch by flight_id
    ai_data = db.get_records(flight_id="AI204")
    print("AI204 Records:", ai_data)
