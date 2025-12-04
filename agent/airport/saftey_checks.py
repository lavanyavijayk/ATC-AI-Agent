"""
Safety Checks Module
====================
Provides conflict detection and prediction utilities for air traffic control.

This module implements algorithms to:
- Convert aviation headings to movement vectors
- Propagate aircraft positions over time
- Predict potential conflicts between aircraft pairs

Standard separation minimums used:
- Horizontal: 5 nautical miles (NM)
- Vertical: 1000 feet (ft)
"""

import math
from typing import Dict, Tuple

# =============================================================================
# Constants
# =============================================================================

# Conversion factor: 1 knot = 1 NM/hour = 1/60 NM/minute
KNOT_TO_NM_PER_MIN = 1 / 60.0


# =============================================================================
# Utility Functions
# =============================================================================

def heading_to_vector(heading_deg: float) -> Tuple[float, float]:
    """
    Convert an aviation heading (degrees) to a unit direction vector.
    
    Aviation headings use compass directions where:
    - 0° (360°) = North
    - 90° = East
    - 180° = South
    - 270° = West
    
    Args:
        heading_deg: Heading in degrees (0-360).
    
    Returns:
        Tuple (dx, dy) representing the unit direction vector where:
        - dx: East-West component (positive = East)
        - dy: North-South component (positive = North)
    
    Example:
        >>> heading_to_vector(0)    # North
        (0.0, 1.0)
        >>> heading_to_vector(90)   # East
        (1.0, 0.0)
    """
    radians = math.radians(heading_deg)
    dx = math.sin(radians)  # East-West component
    dy = math.cos(radians)  # North-South component
    return dx, dy


def state_after_time(flight: Dict, time_minutes: float) -> Tuple[float, float, float]:
    """
    Propagate aircraft position forward in time assuming constant velocity.
    
    Uses dead reckoning to estimate future position based on
    current speed and heading.
    
    Args:
        flight: Dictionary containing aircraft state with keys:
            - position: Dict with 'x' and 'y' in nautical miles
            - speed: Ground speed in knots
            - heading: Heading in degrees (0-360)
            - altitude: Altitude in feet
        time_minutes: Time to propagate forward (in minutes).
    
    Returns:
        Tuple (x, y, altitude) representing predicted position:
        - x: East-West position in NM
        - y: North-South position in NM
        - altitude: Altitude in feet (unchanged)
    
    Note:
        This assumes constant speed, heading, and altitude.
        Does not account for turns, climbs, or descents.
    """
    # Extract current state
    x0 = flight["position"]["x"]
    y0 = flight["position"]["y"]
    speed = flight["speed"]
    heading = flight["heading"]
    altitude = flight["altitude"]
    
    # Calculate movement vector
    dx, dy = heading_to_vector(heading)
    distance_per_minute = speed * KNOT_TO_NM_PER_MIN
    
    # Propagate position
    x = x0 + dx * distance_per_minute * time_minutes
    y = y0 + dy * distance_per_minute * time_minutes
    
    return x, y, altitude


# =============================================================================
# Conflict Detection
# =============================================================================

def predict_conflict(
    flight_1: Dict,
    flight_2: Dict,
    horizon_min: float = 1.0,
    horizontal_threshold_nm: float = 5.0,
    vertical_threshold_ft: float = 1000.0,
    time_step: float = 0.1,
) -> Dict:
    """
    Predict potential loss of separation between two aircraft.
    
    Simulates both aircraft trajectories forward in time and checks
    if separation standards will be violated.
    
    A conflict occurs when BOTH conditions are met:
    - Horizontal separation < horizontal_threshold_nm
    - Vertical separation < vertical_threshold_ft
    
    Args:
        flight_1: First aircraft state dictionary.
        flight_2: Second aircraft state dictionary.
        horizon_min: Look-ahead time horizon in minutes (default: 1.0).
        horizontal_threshold_nm: Minimum horizontal separation in NM (default: 5.0).
        vertical_threshold_ft: Minimum vertical separation in feet (default: 1000.0).
        time_step: Simulation time step in minutes (default: 0.1).
    
    Returns:
        Dictionary containing:
        - will_conflict (bool): True if separation loss predicted
        - time_of_conflict_min (float): Time until conflict (if conflict)
        - time_of_closest_approach_min (float): Time of closest approach (if no conflict)
        - min_horizontal_nm (float): Minimum horizontal separation found
        - min_vertical_ft (float): Vertical separation at closest approach
    
    Example:
        >>> result = predict_conflict(flight_a, flight_b, horizon_min=2.0)
        >>> if result['will_conflict']:
        ...     print(f"Conflict in {result['time_of_conflict_min']:.1f} minutes")
    """
    # Track minimum separation found during simulation
    min_horizontal_sep = float("inf")
    min_vertical_sep = float("inf")
    time_of_minimum = 0.0
    
    # Simulate forward in time
    current_time = 0.0
    while current_time <= horizon_min:
        # Get predicted positions for both aircraft
        x1, y1, alt1 = state_after_time(flight_1, current_time)
        x2, y2, alt2 = state_after_time(flight_2, current_time)
        
        # Calculate separations
        horizontal_sep = math.hypot(x1 - x2, y1 - y2)
        vertical_sep = abs(alt1 - alt2)
        
        # Update minimum if this is the closest approach so far
        if horizontal_sep < min_horizontal_sep:
            min_horizontal_sep = horizontal_sep
            min_vertical_sep = vertical_sep
            time_of_minimum = current_time
        
        # Check for immediate separation violation
        is_horizontal_violation = horizontal_sep <= horizontal_threshold_nm
        is_vertical_violation = vertical_sep < vertical_threshold_ft
        
        if is_horizontal_violation and is_vertical_violation:
            return {
                "will_conflict": True,
                "time_of_conflict_min": current_time,
                "min_horizontal_nm": min_horizontal_sep,
                "min_vertical_ft": min_vertical_sep,
            }
        
        current_time += time_step
    
    # No conflict found within horizon
    return {
        "will_conflict": False,
        "time_of_closest_approach_min": time_of_minimum,
        "min_horizontal_nm": min_horizontal_sep,
        "min_vertical_ft": min_vertical_sep,
    }


# =============================================================================
# Example Usage / Module Testing
# =============================================================================

def _print_test_result(test_name: str, flight_a: Dict, flight_b: Dict, result: Dict) -> None:
    """Helper function to print formatted test results."""
    # Calculate initial separations
    init_h_sep = math.hypot(
        flight_a["position"]["x"] - flight_b["position"]["x"],
        flight_a["position"]["y"] - flight_b["position"]["y"]
    )
    init_v_sep = abs(flight_a["altitude"] - flight_b["altitude"])
    
    print(f"Initial horizontal separation: {init_h_sep:.2f} NM")
    print(f"Initial vertical separation: {init_v_sep} ft")
    print(f"Conflict detected: {result['will_conflict']}")
    
    if result["will_conflict"]:
        print(f"Time of conflict: {result['time_of_conflict_min']:.2f} min")
    else:
        print(f"Time of closest approach: {result['time_of_closest_approach_min']:.2f} min")
    
    print(f"Minimum horizontal separation: {result['min_horizontal_nm']:.2f} NM")
    print(f"Minimum vertical separation: {result['min_vertical_ft']:.0f} ft")


if __name__ == "__main__":
    # =========================================================================
    # TEST 1: Diverging flights (should be NO conflict)
    # =========================================================================
    print("=" * 60)
    print("TEST 1: Flights DIVERGING (expected: NO conflict)")
    print("=" * 60)
    
    flight_a = {
        "callsign": "UAL4527",
        "flight_type": "arrival",
        "status": "approaching",
        "position": {"x": 10.0, "y": 10.0},
        "altitude": 9500,
        "speed": 315,
        "heading": 225,  # Southwest (away from B)
    }
    
    flight_b = {
        "callsign": "DAL123",
        "flight_type": "departure",
        "status": "climb",
        "position": {"x": 20.0, "y": 20.0},
        "altitude": 9000,
        "speed": 320,
        "heading": 45,  # Northeast (away from A)
    }
    
    result_1 = predict_conflict(flight_a, flight_b, horizon_min=2.0)
    _print_test_result("Diverging", flight_a, flight_b, result_1)
    
    # =========================================================================
    # TEST 2: Converging flights (should detect conflict)
    # =========================================================================
    print("\n" + "=" * 60)
    print("TEST 2: Flights CONVERGING (expected: conflict detected)")
    print("=" * 60)
    
    flight_c = {
        "callsign": "AAL100",
        "flight_type": "arrival",
        "status": "approaching",
        "position": {"x": 10.0, "y": 10.0},
        "altitude": 9500,
        "speed": 300,
        "heading": 45,  # Northeast (toward D)
    }
    
    flight_d = {
        "callsign": "SWA200",
        "flight_type": "departure",
        "status": "climb",
        "position": {"x": 20.0, "y": 20.0},
        "altitude": 9000,
        "speed": 300,
        "heading": 225,  # Southwest (toward C)
    }
    
    result_2 = predict_conflict(flight_c, flight_d, horizon_min=2.0)
    _print_test_result("Converging", flight_c, flight_d, result_2)
    
    # =========================================================================
    # TEST 3: Close horizontally but sufficient vertical separation
    # =========================================================================
    print("\n" + "=" * 60)
    print("TEST 3: Close but VERTICAL separation OK (expected: NO conflict)")
    print("=" * 60)
    
    flight_e = {
        "callsign": "JBU300",
        "flight_type": "arrival",
        "status": "cruise",
        "position": {"x": 15.0, "y": 15.0},
        "altitude": 10000,  # 2000 ft above F
        "speed": 280,
        "heading": 90,  # East
    }
    
    flight_f = {
        "callsign": "UAL400",
        "flight_type": "arrival",
        "status": "cruise",
        "position": {"x": 15.5, "y": 15.5},
        "altitude": 8000,  # 2000 ft below E (> 1000 ft threshold)
        "speed": 280,
        "heading": 90,  # East (parallel)
    }
    
    result_3 = predict_conflict(flight_e, flight_f, horizon_min=2.0)
    _print_test_result("Vertical separation", flight_e, flight_f, result_3)
