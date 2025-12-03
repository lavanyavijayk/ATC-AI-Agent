#!/usr/bin/env python3
"""
Mock Landing Demo - Automated aircraft landing sequence
Demonstrates complete flow from spawn to touchdown
"""

import requests
import time
import sys

BASE_URL = "http://localhost:8000/api"

def print_header(text):
    print(f"\n{'='*50}")
    print(f"  {text}")
    print(f"{'='*50}")

def print_step(num, text):
    print(f"\n[Step {num}] {text}")
    print("-" * 40)

def get_flight(callsign):
    """Get flight data, returns None if flight doesn't exist"""
    try:
        r = requests.get(f"{BASE_URL}/flights/{callsign}")
        if r.status_code == 200:
            data = r.json()
            if data and "callsign" in data:
                return data
    except:
        pass
    return None

def send_command(callsign, command):
    """Send command to flight"""
    r = requests.post(
        f"{BASE_URL}/flights/{callsign}/command",
        json=command
    )
    return r.json()

def print_flight_status(flight):
    """Pretty print flight status"""
    if not flight:
        print("  Flight not found")
        return
    
    pos = flight["position"]
    dist = (pos["x"]**2 + pos["y"]**2)**0.5
    
    print(f"  Callsign: {flight['callsign']} ({flight['aircraft_type']})")
    print(f"  Position: ({pos['x']:.1f}, {pos['y']:.1f}) nm | Distance: {dist:.1f} nm")
    print(f"  Altitude: {flight['altitude']:.0f} ft → {flight['target_altitude']:.0f} ft")
    print(f"  Speed: {flight['speed']:.0f} kt → {flight['target_speed']:.0f} kt")
    print(f"  Heading: {flight['heading']:.0f}°")
    print(f"  Status: {flight['status']}")
    print(f"  Target WPT: {flight.get('target_waypoint', 'None')}")
    print(f"  Passed WPTs: {flight.get('passed_waypoints', [])}")
    if flight.get('cleared_to_land'):
        print(f"  ✅ Cleared to land")
    if flight.get('clearance_denial_reason'):
        print(f"  ⚠️ Denial: {flight['clearance_denial_reason']}")

def wait_for_waypoint(callsign, waypoint, timeout=60):
    """Wait until flight passes a waypoint"""
    start = time.time()
    while time.time() - start < timeout:
        flight = get_flight(callsign)
        if flight and waypoint in flight.get('passed_waypoints', []):
            return True
        time.sleep(1)
    return False

def main():
    print_header("AI-ATC Mock Landing Demo")
    
    # Check server connection
    try:
        r = requests.get(f"{BASE_URL}/simulation/status")
        r.raise_for_status()
        print("✅ Connected to AI-ATC server")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("   Make sure the server is running: uvicorn app.main:app --port 8000")
        sys.exit(1)
    
    # Speed up simulation for demo
    print_step(0, "Setting simulation speed to 5x")
    requests.post(f"{BASE_URL}/simulation/speed", json={"multiplier": 5.0})
    print("  Speed set to 5x")
    
    # Step 1: Spawn arrival
    print_step(1, "Spawning arrival aircraft")
    r = requests.post(f"{BASE_URL}/simulation/spawn/arrival")
    spawn_data = r.json()
    callsign = spawn_data["callsign"]
    print(f"  Spawned: {callsign} ({spawn_data['aircraft_type']})")
    print(f"  Origin: {spawn_data.get('origin', 'Unknown')}")
    
    time.sleep(1)
    
    # Step 2: Initial status
    print_step(2, "Initial flight status")
    flight = get_flight(callsign)
    print_flight_status(flight)
    
    time.sleep(2)
    
    # Step 3: Direct to DOWNWIND
    print_step(3, "Directing to DOWNWIND (2000ft, 200kt)")
    result = send_command(callsign, {
        "waypoint": "DOWNWIND",
        "altitude": 2000,
        "speed": 200
    })
    print(f"  Command sent: {result['command']}")
    print(f"  Result: {result['result']['message']}")
    
    time.sleep(3)
    
    # Step 4: Direct to BASE
    print_step(4, "Directing to BASE (1500ft, 160kt)")
    result = send_command(callsign, {
        "waypoint": "BASE",
        "altitude": 1500,
        "speed": 160
    })
    print(f"  Command sent: {result['command']}")
    print(f"  Result: {result['result']['message']}")
    
    time.sleep(3)
    
    # Step 5: Direct to FINAL
    print_step(5, "Directing to FINAL (1000ft, 140kt)")
    result = send_command(callsign, {
        "waypoint": "FINAL",
        "altitude": 1000,
        "speed": 140
    })
    print(f"  Command sent: {result['command']}")
    print(f"  Result: {result['result']['message']}")
    
    # Wait for FINAL waypoint
    print("\n  Waiting for aircraft to reach FINAL...")
    if wait_for_waypoint(callsign, "FINAL", timeout=30):
        print("  ✅ Passed FINAL waypoint")
    else:
        print("  ⚠️ Timeout waiting for FINAL")
    
    time.sleep(2)
    
    # Step 6: Pre-landing check
    print_step(6, "Pre-landing status check")
    flight = get_flight(callsign)
    print_flight_status(flight)
    
    # Step 7: Clear to land (with retries)
    print_step(7, "Requesting landing clearance")
    
    cleared = False
    for attempt in range(10):
        result = send_command(callsign, {"clear_to_land": True})
        success = result['result'].get('success', False)
        
        print(f"  Attempt {attempt + 1}: {result['result']['message']}")
        
        if success:
            print("  ✅ CLEARED TO LAND!")
            cleared = True
            break
        
        time.sleep(2)
    
    if not cleared:
        print("  ❌ Could not get landing clearance")
        flight = get_flight(callsign)
        if flight:
            print(f"  Current altitude: {flight['altitude']:.0f} ft")
            print(f"  Current speed: {flight['speed']:.0f} kt")
            print(f"  Passed waypoints: {flight.get('passed_waypoints', [])}")
        return
    
    # Step 8: Monitor landing
    print_step(8, "Monitoring landing progress")
    
    for i in range(20):
        time.sleep(1)
        flight = get_flight(callsign)
        
        if not flight:
            print(f"\n  ✅ Aircraft {callsign} has landed and cleared the runway!")
            break
        
        pos = flight["position"]
        dist = (pos["x"]**2 + pos["y"]**2)**0.5
        status = flight["status"]
        alt = flight["altitude"]
        
        bar_len = int(max(0, min(20, 20 - dist)))
        bar = "█" * bar_len + "░" * (20 - bar_len)
        
        print(f"  [{bar}] {status:12} | Alt: {alt:5.0f}ft | Dist: {dist:.2f}nm")
        
        if status == "landed":
            print(f"\n  ✅ TOUCHDOWN! {callsign} has landed successfully!")
            time.sleep(3)  # Wait for cleanup
            break
    
    # Final stats
    print_step(9, "Final simulation statistics")
    r = requests.get(f"{BASE_URL}/simulation/status")
    stats = r.json()
    print(f"  Landed: {stats['landed']}")
    print(f"  Departed: {stats['departed']}")
    print(f"  Near Misses: {stats['near_misses']}")
    print(f"  Session Duration: {stats['session_duration']:.0f}s")
    
    # Reset speed
    requests.post(f"{BASE_URL}/simulation/speed", json={"multiplier": 1.0})
    print("\n  Speed reset to 1x")
    
    print_header("Demo Complete!")

if __name__ == "__main__":
    main()

