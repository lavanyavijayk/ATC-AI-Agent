import math
from typing import Dict

KNOT_TO_NM_PER_MIN = 1/60.0   # 1 knot = 1 NM/hr = 1/60 NM/min

def heading_to_vector(heading_deg: float):
    """
    Convert aviation heading to (dx, dy):
    0° = north, 90° = east, 180° = south, 270° = west.
    """
    r = math.radians(heading_deg)
    dx = math.sin(r)
    dy = math.cos(r)
    return dx, dy


def state_after_time(f: Dict, t_min: float):
    """
    Propagate aircraft position assuming constant speed & heading.
    x,y in NM. speed in knots. heading deg.
    """
    x0 = f["position"]["x"]
    y0 = f["position"]["y"]

    speed = f["speed"]
    heading = f["heading"]

    dx, dy = heading_to_vector(heading)
    nm_per_min = speed * KNOT_TO_NM_PER_MIN

    x = x0 + dx * nm_per_min * t_min
    y = y0 + dy * nm_per_min * t_min

    alt = f["altitude"]

    return x, y, alt


def predict_conflict(
    f1: Dict, f2: Dict,
    horizon_min: float = 1.0,
    horizontal_threshold_nm: float = 5.0,
    vertical_threshold_ft: float = 1000.0,
    dt: float = 0.1,
):
    """
    Predict loss of separation or collision within next horizon minutes.
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

        # check immediate violation
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


if __name__=="__main__":

    print("=" * 50)
    print("TEST 1: Flights DIVERGING (should be NO conflict)")
    print("=" * 50)
    
    # Flight A: heading away to the southwest
    flight_A = {
        "callsign": "UAL4527",
        "flight_type": "arrival",
        "status": "approaching",
        "position": {"x": 10.0, "y": 10.0},
        "altitude": 9500,   # ft
        "speed": 315,       # knots
        "heading": 225      # degrees (toward southwest - away from B)
    }

    # Flight B: heading away to the northeast
    flight_B = {
        "callsign": "DAL123",
        "flight_type": "departure",
        "status": "climb",
        "position": {"x": 20.0, "y": 20.0},
        "altitude": 9000,   # ft
        "speed": 320,       # knots
        "heading": 45       # degrees (toward northeast - away from A)
    }

    # Calculate initial separation for reference
    init_h_sep = math.hypot(flight_A["position"]["x"] - flight_B["position"]["x"],
                            flight_A["position"]["y"] - flight_B["position"]["y"])
    init_v_sep = abs(flight_A["altitude"] - flight_B["altitude"])
    print(f"Initial horizontal separation: {init_h_sep:.2f} NM")
    print(f"Initial vertical separation: {init_v_sep} ft")

    # Run the conflict prediction with 2 min horizon
    res = predict_conflict(flight_A, flight_B, horizon_min=2.0)

    print(f"Conflict detected?: {res.get('will_conflict')}")
    if res.get("will_conflict"):
        print(f"Time of conflict (min): {res['time_of_conflict_min']:.2f}")
    else:
        print(f"Time of closest approach (min): {res['time_of_closest_approach_min']:.2f}")
    print(f"Minimum horizontal separation (NM): {res['min_horizontal_nm']:.2f}")
    print(f"Minimum vertical separation (ft): {res['min_vertical_ft']:.0f}")

    print("\n" + "=" * 50)
    print("TEST 2: Flights CONVERGING (should detect conflict)")
    print("=" * 50)
    
    # Flight C: heading northeast toward D
    flight_C = {
        "callsign": "AAL100",
        "flight_type": "arrival",
        "status": "approaching",
        "position": {"x": 10.0, "y": 10.0},
        "altitude": 9500,   # ft
        "speed": 300,       # knots
        "heading": 45       # degrees (toward northeast - toward D)
    }

    # Flight D: heading southwest toward C
    flight_D = {
        "callsign": "SWA200",
        "flight_type": "departure",
        "status": "climb",
        "position": {"x": 20.0, "y": 20.0},
        "altitude": 9000,   # ft
        "speed": 300,       # knots
        "heading": 225      # degrees (toward southwest - toward C)
    }

    init_h_sep2 = math.hypot(flight_C["position"]["x"] - flight_D["position"]["x"],
                             flight_C["position"]["y"] - flight_D["position"]["y"])
    init_v_sep2 = abs(flight_C["altitude"] - flight_D["altitude"])
    print(f"Initial horizontal separation: {init_h_sep2:.2f} NM")
    print(f"Initial vertical separation: {init_v_sep2} ft")

    res2 = predict_conflict(flight_C, flight_D, horizon_min=2.0)

    print(f"Conflict detected?: {res2.get('will_conflict')}")
    if res2.get("will_conflict"):
        print(f"Time of conflict (min): {res2['time_of_conflict_min']:.2f}")
    else:
        print(f"Time of closest approach (min): {res2['time_of_closest_approach_min']:.2f}")
    print(f"Minimum horizontal separation (NM): {res2['min_horizontal_nm']:.2f}")
    print(f"Minimum vertical separation (ft): {res2['min_vertical_ft']:.0f}")

    print("\n" + "=" * 50)
    print("TEST 3: Close but with sufficient VERTICAL separation")
    print("=" * 50)
    
    # Flight E and F are horizontally close but vertically well separated
    flight_E = {
        "callsign": "JBU300",
        "flight_type": "arrival",
        "status": "cruise",
        "position": {"x": 15.0, "y": 15.0},
        "altitude": 10000,  # ft - 2000 ft above F
        "speed": 280,
        "heading": 90       # heading east
    }

    flight_F = {
        "callsign": "UAL400",
        "flight_type": "arrival",
        "status": "cruise",
        "position": {"x": 15.5, "y": 15.5},
        "altitude": 8000,   # ft - 2000 ft below E (> 1000 ft threshold)
        "speed": 280,
        "heading": 90       # also heading east
    }

    init_h_sep3 = math.hypot(flight_E["position"]["x"] - flight_F["position"]["x"],
                             flight_E["position"]["y"] - flight_F["position"]["y"])
    init_v_sep3 = abs(flight_E["altitude"] - flight_F["altitude"])
    print(f"Initial horizontal separation: {init_h_sep3:.2f} NM")
    print(f"Initial vertical separation: {init_v_sep3} ft (>1000 ft, so OK)")

    res3 = predict_conflict(flight_E, flight_F, horizon_min=2.0)

    print(f"Conflict detected?: {res3.get('will_conflict')}")
    if res3.get("will_conflict"):
        print(f"Time of conflict (min): {res3['time_of_conflict_min']:.2f}")
    else:
        print(f"Time of closest approach (min): {res3['time_of_closest_approach_min']:.2f}")
    print(f"Minimum horizontal separation (NM): {res3['min_horizontal_nm']:.2f}")
    print(f"Minimum vertical separation (ft): {res3['min_vertical_ft']:.0f}")
