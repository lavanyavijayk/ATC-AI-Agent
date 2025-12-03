"""
Safety Checks and Collision Detection for ATC Agent
"""
import math
from typing import Dict, List, Optional, Tuple

# Constants
KNOT_TO_NM_PER_MIN = 1 / 60.0  # 1 knot = 1 NM/hr = 1/60 NM/min

# Landing pattern waypoints
LANDING_PATTERN_WAYPOINTS = ["DOWNWIND", "BASE", "FINAL", "RUNWAY"]


def heading_to_vector(heading_deg: float) -> Tuple[float, float]:
    """
    Convert aviation heading to (dx, dy) vector.
    0° = north, 90° = east, 180° = south, 270° = west.
    """
    r = math.radians(heading_deg)
    dx = math.sin(r)
    dy = math.cos(r)
    return dx, dy


def state_after_time(flight: Dict, t_min: float) -> Tuple[float, float, float]:
    """
    Propagate aircraft position assuming constant speed & heading.
    
    Args:
        flight: Flight data dictionary with position, speed, heading, altitude
        t_min: Time in minutes to project forward
        
    Returns:
        Tuple of (x, y, altitude) at time t_min
    """
    x0 = flight["position"]["x"]
    y0 = flight["position"]["y"]
    speed = flight["speed"]
    heading = flight["heading"]
    
    dx, dy = heading_to_vector(heading)
    nm_per_min = speed * KNOT_TO_NM_PER_MIN
    
    x = x0 + dx * nm_per_min * t_min
    y = y0 + dy * nm_per_min * t_min
    alt = flight["altitude"]
    
    return x, y, alt


def predict_conflict(
    f1: Dict,
    f2: Dict,
    horizon_min: float = 2.0,
    horizontal_threshold_nm: float = 5.0,
    vertical_threshold_ft: float = 1000.0,
    dt: float = 0.1,
) -> Dict:
    """
    Predict loss of separation or collision within next horizon minutes.
    
    Args:
        f1, f2: Flight dictionaries
        horizon_min: Time horizon to check (minutes)
        horizontal_threshold_nm: Horizontal separation threshold (NM)
        vertical_threshold_ft: Vertical separation threshold (feet)
        dt: Time step for simulation (minutes)
        
    Returns:
        Dictionary with conflict prediction results
    """
    min_h = float("inf")
    min_v = float("inf")
    min_t = 0

    t = 0.0
    while t <= horizon_min:
        x1, y1, a1 = state_after_time(f1, t)
        x2, y2, a2 = state_after_time(f2, t)

        h_sep = math.hypot(x1 - x2, y1 - y2)
        v_sep = abs(a1 - a2)

        if h_sep < min_h:
            min_h = h_sep
            min_v = v_sep
            min_t = t

        if h_sep <= horizontal_threshold_nm and v_sep < vertical_threshold_ft:
            return {
                "will_conflict": True,
                "time_of_conflict_min": t,
                "min_horizontal_nm": min_h,
                "min_vertical_ft": min_v
            }

        t += dt

    return {
        "will_conflict": False,
        "time_of_closest_approach_min": min_t,
        "min_horizontal_nm": min_h,
        "min_vertical_ft": min_v,
    }


def check_takeoff_safety(
    command: Dict,
    current_flight: Dict,
    other_flights: List[Dict]
) -> Tuple[bool, Optional[str]]:
    """
    Check if takeoff clearance is safe.
    
    Returns:
        Tuple of (is_safe, reason_if_not_safe)
    """
    if not command.get("cleared_for_takeoff"):
        return True, None
    
    for flight in other_flights:
        flight_passed = flight.get("passed_waypoints", [])
        flight_last = flight_passed[-1] if flight_passed else ""
        flight_status = flight.get("status", "")
        
        is_conflict = (
            flight_last in ["FINAL", "RUNWAY"] or
            flight_status in ["taking_off", "landing"]
        )
        
        if is_conflict:
            return False, f"Runway conflict with {flight.get('callsign', 'unknown')}"
    
    return True, None


def check_landing_safety(
    command: Dict,
    current_flight: Dict,
    other_flights: List[Dict]
) -> Tuple[bool, Optional[str]]:
    """
    Check if landing clearance is safe.
    
    Returns:
        Tuple of (is_safe, reason_if_not_safe)
    """
    if not command.get("clear_to_land"):
        return True, None
    
    for flight in other_flights:
        flight_passed = flight.get("passed_waypoints", [])
        flight_last = flight_passed[-1] if flight_passed else ""
        flight_status = flight.get("status", "")
        
        is_conflict = (
            flight_last in ["FINAL", "RUNWAY"] or
            flight_status in ["taking_off", "landing"]
        )
        
        if is_conflict:
            return False, f"Landing conflict with {flight.get('callsign', 'unknown')}"
    
    return True, None


def check_pattern_safety(
    command: Dict,
    current_flight: Dict,
    other_flights: List[Dict]
) -> Tuple[bool, Optional[str]]:
    """
    Check if routing through landing pattern is safe.
    
    Returns:
        Tuple of (is_safe, reason_if_not_safe)
    """
    passed = current_flight.get("passed_waypoints", [])
    last_checkpoint = passed[-1] if passed else ""
    
    if last_checkpoint not in LANDING_PATTERN_WAYPOINTS:
        return True, None
    
    target = command.get("waypoint", "")
    
    for flight in other_flights:
        flight_passed = flight.get("passed_waypoints", [])
        flight_last = flight_passed[-1] if flight_passed else ""
        flight_target = flight.get("target_waypoint", "")
        
        if flight_last == last_checkpoint and flight_target == target:
            return False, f"Route conflict with {flight.get('callsign', 'unknown')}"
    
    return True, None


def check_enroute_safety(
    command: Dict,
    current_flight: Dict,
    other_flights: List[Dict],
    horizon_min: float = 2.0
) -> Tuple[bool, Optional[str]]:
    """
    Check for collision risks with en-route aircraft.
    
    Returns:
        Tuple of (is_safe, reason_if_not_safe)
    """
    for flight in other_flights:
        flight_status = flight.get("status", "")
        flight_passed = flight.get("passed_waypoints", [])
        flight_last = flight_passed[-1] if flight_passed else ""
        
        # Skip flights in landing pattern
        if flight_status in ["landing", "on_final"] or flight_last in LANDING_PATTERN_WAYPOINTS:
            continue
        
        result = predict_conflict(
            current_flight,
            flight,
            horizon_min=horizon_min,
            horizontal_threshold_nm=5.0,
            vertical_threshold_ft=1000.0
        )
        
        if result.get("will_conflict"):
            return False, f"Collision risk with {flight.get('callsign', 'unknown')}"
    
    return True, None

