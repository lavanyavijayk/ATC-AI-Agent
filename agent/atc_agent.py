"""
ATC Agent - AI-powered Air Traffic Controller
=============================================
Uses LangGraph for workflow management and Google Gemini for decision-making.
"""
import json
import re
import time
import requests
from typing import TypedDict, Literal, Optional, Dict, List

from langgraph.graph import StateGraph, END

from .llm import LLM
from .safety import (
    check_takeoff_safety,
    check_landing_safety,
    check_pattern_safety,
    check_enroute_safety,
)
from core import Airport, Flight, WeatherService
from database import ATCDatabase


# API Configuration
API_BASE_URL = "http://localhost:8000/api"


class ATCState(TypedDict):
    """State structure for the ATC workflow"""
    messages: list
    command: dict
    result: dict
    flight_id: str
    flight_info: dict
    retry_count: int
    prev_convo: list


class ATCAgent:
    """
    AI-powered Air Traffic Controller Agent.
    
    Handles landing and takeoff operations with built-in safety checks.
    
    Workflow: entry -> [landing|takeoff] -> safety_check -> [retry|end]
    """
    
    MAX_RETRIES = 3
    
    def __init__(self, airport: Airport, flight_id: str, flight_info: dict):
        """
        Initialize the ATC Agent.
        
        Args:
            airport: Airport object with runway configuration
            flight_id: Callsign of the flight to manage
            flight_info: Current flight data dictionary
        """
        print(f"[ATCAgent] Initializing for flight {flight_id}")
        
        self.airport = airport
        self.flight_id = flight_id
        self.flight_info = flight_info
        
        self.llm = LLM()
        self.weather = WeatherService()
        self.db = ATCDatabase()
        
        # Create Flight object for runway assignment
        self.flight_obj = Flight(
            flight_id,
            flight_info['aircraft_type'],
            flight_info['origin'],
            flight_info['destination']
        )
        
        # Build workflow
        self.workflow = self._build_workflow()
        
        # Initialize state
        self.state: ATCState = {
            "messages": [],
            "command": {},
            "result": {},
            "flight_id": flight_id,
            "flight_info": flight_info,
            "retry_count": 0,
            "prev_convo": []
        }
    
    def _build_workflow(self) -> StateGraph:
        """Build and compile the LangGraph workflow"""
        workflow = StateGraph(ATCState)
        
        # Add nodes
        workflow.add_node("entry_point", self._entry_point)
        workflow.add_node("landing_node", self._landing_node)
        workflow.add_node("takeoff_node", self._takeoff_node)
        workflow.add_node("safety_check", self._safety_check)
        
        # Set entry
        workflow.set_entry_point("entry_point")
        
        # Route from entry based on flight status
        workflow.add_conditional_edges(
            "entry_point",
            self._route_by_status,
            {"landing": "landing_node", "takeoff": "takeoff_node", "end": END}
        )
        
        # Connect operation nodes to safety check
        workflow.add_edge("landing_node", "safety_check")
        workflow.add_edge("takeoff_node", "safety_check")
        
        # Route after safety check
        workflow.add_conditional_edges(
            "safety_check",
            self._route_after_safety,
            {"retry_landing": "landing_node", "retry_takeoff": "takeoff_node", "end": END}
        )
        
        return workflow.compile()
    
    # =========================================================================
    # API Helper Methods
    # =========================================================================
    
    def _get_other_flights(self) -> List[Dict]:
        """Fetch all other flights in the airspace"""
        try:
            response = requests.get(f"{API_BASE_URL}/flights/", timeout=5)
            if response.status_code == 200 and response.text.strip():
                flights = response.json()
                return [f for f in flights if f["callsign"] != self.flight_id]
        except Exception as e:
            print(f"[API] Error fetching flights: {e}")
        return []
    
    def _get_landing_rules(self) -> Dict:
        """Fetch landing rules from simulator"""
        try:
            response = requests.get(f"{API_BASE_URL}/landing-rules", timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[API] Error fetching landing rules: {e}")
        
        # Default rules
        return {
            "max_altitude": 1500,
            "min_speed": 100,
            "max_speed": 180,
            "max_distance": 18,
            "required_waypoint": "FINAL"
        }
    
    def _get_waypoints(self) -> Dict:
        """Fetch waypoints from simulator"""
        try:
            response = requests.get(f"{API_BASE_URL}/waypoints", timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[API] Error fetching waypoints: {e}")
        return {}
    
    def _get_runway_status(self) -> List[str]:
        """Get runway status information"""
        return [runway.get_runway_details() for runway in self.airport.runways]
    
    # =========================================================================
    # Workflow Nodes
    # =========================================================================
    
    def _entry_point(self, state: ATCState) -> ATCState:
        """Entry node - initialize workflow state"""
        status = state["flight_info"].get("status", "")
        callsign = state["flight_info"].get("callsign", self.flight_id)
        
        print(f"[Entry] Processing {callsign} with status: {status}")
        
        state["messages"].append({
            "role": "system",
            "content": f"Flight {callsign} status: {status}"
        })
        
        # Load conversation history
        state["prev_convo"] = self.db.get_records(state['flight_id'], 30)
        
        return state
    
    def _route_by_status(self, state: ATCState) -> Literal["landing", "takeoff", "end"]:
        """Route based on flight status"""
        status = state["flight_info"].get("status", "")
        
        if status in ["approaching", "on_final", "landing"]:
            return "landing"
        if status in ["ready_for_takeoff", "taking_off"]:
            return "takeoff"
        return "end"
    
    def _landing_node(self, state: ATCState) -> ATCState:
        """Handle landing operations"""
        callsign = state["flight_info"].get("callsign", self.flight_id)
        print(f"[Landing] Processing {callsign}")
        
        # Gather context
        weather = self.weather.get_weather("KSEA")
        other_flights = self._get_other_flights()
        runway_details = self._get_runway_status()
        waypoints = self._get_waypoints()
        
        # Build prompt
        prompt = self._build_landing_prompt(
            state, callsign, weather, other_flights, runway_details, waypoints
        )
        
        # Get LLM response
        state["messages"].append({"role": "user", "content": prompt})
        
        try:
            response = self.llm.invoke(prompt)
            if response:
                command = self._parse_json(response)
                state["command"] = command
                state["result"] = command
                state["messages"].append({"role": "assistant", "content": response})
                print(f"[Landing] Generated command: {command}")
        except Exception as e:
            print(f"[Landing] Error: {e}")
            state["command"] = {"error": str(e)}
        
        return state
    
    def _takeoff_node(self, state: ATCState) -> ATCState:
        """Handle takeoff operations"""
        callsign = state["flight_info"].get("callsign", self.flight_id)
        print(f"[Takeoff] Processing {callsign}")
        
        # Gather context
        weather = self.weather.get_weather("KSEA")
        other_flights = self._get_other_flights()
        runway_details = self._get_runway_status()
        waypoints = self._get_waypoints()
        
        # Build prompt
        prompt = self._build_takeoff_prompt(
            state, callsign, weather, other_flights, runway_details, waypoints
        )
        
        state["messages"].append({"role": "user", "content": prompt})
        
        try:
            response = self.llm.invoke(prompt)
            if response:
                command = self._parse_json(response)
                state["command"] = command
                state["result"] = command
                state["messages"].append({"role": "assistant", "content": response})
                print(f"[Takeoff] Generated command: {command}")
        except Exception as e:
            print(f"[Takeoff] Error: {e}")
            state["command"] = {"error": str(e)}
        
        return state
    
    def _safety_check(self, state: ATCState) -> ATCState:
        """Validate command safety"""
        command = state["command"]
        if command.get("error"):
            return state
        
        flight_info = state["flight_info"]
        status = flight_info.get("status", "")
        other_flights = self._get_other_flights()
        
        print(f"[Safety] Validating: {command}")
        
        # Check based on operation type
        if status in ["ready_for_takeoff", "taking_off"]:
            is_safe, reason = check_takeoff_safety(command, flight_info, other_flights)
        elif command.get("clear_to_land"):
            is_safe, reason = check_landing_safety(command, flight_info, other_flights)
        else:
            # Check pattern and enroute safety
            is_safe, reason = check_pattern_safety(command, flight_info, other_flights)
            if is_safe:
                is_safe, reason = check_enroute_safety(command, flight_info, other_flights)
        
        if not is_safe:
            print(f"[Safety] FAILED: {reason}")
            state["messages"].append({
                "role": "user",
                "content": f"Safety check failed: {reason}"
            })
            state["result"] = {}
        else:
            print("[Safety] PASSED")
            state["result"] = command
            
            # Assign runway for landing clearance
            if command.get("clear_to_land"):
                try:
                    current_time = time.time()
                    self.airport.runway.assign_flight(
                        self.flight_obj, current_time, current_time + 300
                    )
                except Exception as e:
                    print(f"[Safety] Runway assignment failed: {e}")
        
        return state
    
    def _route_after_safety(self, state: ATCState) -> Literal["retry_landing", "retry_takeoff", "end"]:
        """Determine action after safety check"""
        if state.get("result"):
            return "end"
        
        if state.get("retry_count", 0) >= self.MAX_RETRIES:
            return "end"
        
        state["retry_count"] = state.get("retry_count", 0) + 1
        status = state["flight_info"].get("status", "")
        
        if status in ["approaching", "on_final", "landing"]:
            return "retry_landing"
        if status in ["ready_for_takeoff", "taking_off"]:
            return "retry_takeoff"
        
        return "end"
    
    # =========================================================================
    # Prompt Builders
    # =========================================================================
    
    def _build_landing_prompt(
        self, state, callsign, weather, other_flights, runway_details, waypoints
    ) -> str:
        """Build the landing decision prompt"""
        return f"""You are an expert Air Traffic Controller for Runway 34.
Your objective is to safely sequence flight {callsign} through the traffic pattern.

### CONTEXT DATA
<telemetry>
{json.dumps(state['flight_info'], indent=2)}
</telemetry>

<environment>
**Waypoints:** {json.dumps(waypoints, indent=2)}
**Weather:** {weather}
**Runway:** {runway_details}
**Traffic:** {json.dumps(other_flights, indent=2)}
</environment>

### LANDING PATTERN LOGIC
Move aircraft through these states in order. NEVER skip a state.

1. **ENTRY** (North, East, West) -> **DOWNWIND**
   * If at **SOUTH**, route to **EAST** first (South->Downwind cuts through Base->Final path)
2. **DOWNWIND** -> **BASE**
3. **BASE** -> **FINAL**
4. **FINAL** -> **LAND** (Only if cleared)

**Safety Interrupts:**
* If separation < 3nm: Hold or vector to SHORT_EAST
* If Go-Around needed: Vector from FINAL -> SHORT_EAST

### OUTPUT FORMAT
Return ONLY a JSON object:

**Vector to waypoint:**
{{"waypoint": "NAME", "altitude": INT, "speed": INT}}

**Landing clearance:**
{{"clear_to_land": true}}

Response (JSON only):"""

    def _build_takeoff_prompt(
        self, state, callsign, weather, other_flights, runway_details, waypoints
    ) -> str:
        """Build the takeoff decision prompt"""
        return f"""You are an Air Traffic Controller managing departures.
Determine if flight {callsign} can be cleared for takeoff.

### CONTEXT
<flight>
{json.dumps(state['flight_info'], indent=2)}
</flight>

<traffic>
{json.dumps(other_flights, indent=2)}
</traffic>

<runway>
{runway_details}
</runway>

### DECISION LOGIC
The runway is NOT CLEAR if ANY aircraft:
1. Has "RUNWAY" as last passed waypoint
2. Has status "taking_off" or "landing"
3. Has "FINAL" as last waypoint AND target_waypoint is "RUNWAY"

### OUTPUT FORMAT
Return ONLY JSON:

**Clearance granted:** {{"cleared_for_takeoff": true}}
**Clearance denied:** {{"cleared_for_takeoff": false}}

Response (JSON only):"""

    def _parse_json(self, response: str) -> Dict:
        """Extract JSON from LLM response"""
        # Try code block first
        match = re.search(r"```json(.*?)```", response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass
        
        # Try raw response
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            pass
        
        return {}
    
    # =========================================================================
    # Public API
    # =========================================================================
    
    def run(self) -> Dict:
        """Execute the ATC workflow"""
        print(f"\n{'='*60}")
        print(f"  ATC AGENT: {self.flight_id}")
        print(f"{'='*60}\n")
        
        result = self.workflow.invoke(self.state)
        
        print(f"\n{'='*60}")
        print(f"  RESULT: {result.get('result', {})}")
        print(f"{'='*60}\n")
        
        return result


def process_flight(flight_info: dict, airport: Airport) -> Optional[Dict]:
    """
    Process a single flight through the ATC agent.
    
    Args:
        flight_info: Flight data dictionary
        airport: Airport configuration
        
    Returns:
        Command dictionary or None
    """
    flight_id = flight_info['callsign']
    
    agent = ATCAgent(airport, flight_id, flight_info)
    result = agent.run()
    
    command = result.get('result', {})
    
    if command:
        print(f"[Process] Sending command: {command}")
        try:
            response = requests.post(
                f"{API_BASE_URL}/flights/{flight_id}/command",
                json=command,
                headers={"Content-Type": "application/json"}
            )
            print(f"[Process] Response: {response.status_code}")
        except Exception as e:
            print(f"[Process] Error: {e}")
    
    return command

