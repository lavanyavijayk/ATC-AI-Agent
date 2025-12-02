#!/usr/bin/env python3
"""
AI-ATC API Python Examples
Complete example showing all API endpoints and commands
"""

import httpx
import asyncio
import json

BASE_URL = "http://localhost:8000/api"


async def main():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        
        # ============================================
        # GET ENDPOINTS - Retrieve Information
        # ============================================
        
        print("=" * 60)
        print("GET ENDPOINTS")
        print("=" * 60)
        
        # 1. Get airport info
        print("\n1. GET /airport")
        response = await client.get("/airport")
        print(json.dumps(response.json(), indent=2))
        
        # 2. Get all waypoints
        print("\n2. GET /waypoints")
        response = await client.get("/waypoints")
        waypoints = response.json()
        print(f"Available waypoints: {list(waypoints.keys())}")
        
        # 3. Get landing rules
        print("\n3. GET /landing-rules")
        response = await client.get("/landing-rules")
        rules = response.json()
        print(json.dumps(rules, indent=2))
        
        # 4. Get simulation status
        print("\n4. GET /simulation/status")
        response = await client.get("/simulation/status")
        print(json.dumps(response.json(), indent=2))
        
        # 5. Get all flights
        print("\n5. GET /flights")
        response = await client.get("/flights")
        flights = response.json()
        print(f"Total flights: {len(flights)}")
        
        # 6. Get landing flights
        print("\n6. GET /flights/landing")
        response = await client.get("/flights/landing")
        print(f"Landing flights: {len(response.json())}")
        
        # 7. Get takeoff flights
        print("\n7. GET /flights/takeoff")
        response = await client.get("/flights/takeoff")
        print(f"Takeoff flights: {len(response.json())}")
        
        # ============================================
        # POST ENDPOINTS - Spawn Flights
        # ============================================
        
        print("\n" + "=" * 60)
        print("SPAWN ENDPOINTS")
        print("=" * 60)
        
        # 8. Spawn an arrival
        print("\n8. POST /simulation/spawn/arrival")
        response = await client.post("/simulation/spawn/arrival")
        arrival = response.json()["flight"]
        callsign = arrival["callsign"]
        print(f"Spawned arrival: {callsign} at {arrival['position']}")
        
        # 9. Spawn a departure
        print("\n9. POST /simulation/spawn/departure")
        response = await client.post("/simulation/spawn/departure")
        departure = response.json()["flight"]
        dep_callsign = departure["callsign"]
        print(f"Spawned departure: {dep_callsign}")
        
        # 10. Get specific flight
        print(f"\n10. GET /flights/{callsign}")
        response = await client.get(f"/flights/{callsign}")
        print(json.dumps(response.json(), indent=2))
        
        # ============================================
        # COMMAND ENDPOINTS - Control Flights
        # ============================================
        
        print("\n" + "=" * 60)
        print("COMMAND ENDPOINTS")
        print("=" * 60)
        
        # 11. Set altitude
        print(f"\n11. Set altitude to 5000ft")
        response = await client.post(
            f"/flights/{callsign}/command",
            json={"altitude": 5000}
        )
        print(json.dumps(response.json(), indent=2))
        
        # 12. Set speed
        print(f"\n12. Set speed to 200kt")
        response = await client.post(
            f"/flights/{callsign}/command",
            json={"speed": 200}
        )
        print(f"Result: {response.json()['result']}")
        
        # 13. Set heading
        print(f"\n13. Set heading to 270°")
        response = await client.post(
            f"/flights/{callsign}/command",
            json={"heading": 270}
        )
        print(f"Result: {response.json()['result']}")
        
        # 14. Direct to waypoint
        print(f"\n14. Direct to FINAL waypoint")
        response = await client.post(
            f"/flights/{callsign}/command",
            json={"waypoint": "FINAL"}
        )
        print(f"Result: {response.json()['result']}")
        
        # 15. Combined command
        print(f"\n15. Combined: waypoint + altitude + speed")
        response = await client.post(
            f"/flights/{callsign}/command",
            json={
                "waypoint": "FINAL",
                "altitude": 1000,
                "speed": 140
            }
        )
        print(f"Result: {response.json()['result']}")
        
        # 16. Clear to land (will likely fail - rules not met)
        print(f"\n16. Clear to land (expects failure - rules not met)")
        response = await client.post(
            f"/flights/{callsign}/command",
            json={"clear_to_land": True}
        )
        result = response.json()
        print(f"Status: {result['status']}")
        print(f"Message: {result['result']['message']}")
        
        # 17. Clear for takeoff (for departure)
        print(f"\n17. Clear for takeoff: {dep_callsign}")
        response = await client.post(
            f"/flights/{dep_callsign}/command",
            json={"clear_for_takeoff": True}
        )
        print(f"Result: {response.json()['result']}")
        
        print("\n" + "=" * 60)
        print("ALL API EXAMPLES COMPLETE")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

