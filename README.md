# 🛫 ATC AI Agent

An AI-powered Air Traffic Control system that uses Google Gemini LLM to manage aircraft landing and takeoff operations in a real-time flight simulator.

![Python](https://img.shields.io/badge/python-3.10+-blue?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?style=flat-square)
![Gemini](https://img.shields.io/badge/Gemini-2.5--flash-orange?style=flat-square)
![LangGraph](https://img.shields.io/badge/LangGraph-workflow-purple?style=flat-square)

## Overview

This project consists of two main components:

1. **ATC Simulator** - A real-time flight simulation with radar display, waypoint navigation, and REST API
2. **AI Agent** - An intelligent controller using LangGraph workflow and Gemini LLM for decision-making

The AI agent continuously monitors the simulator, making real-time decisions to:
- Guide arriving aircraft through the landing pattern (DOWNWIND → BASE → FINAL → LAND)
- Clear departing aircraft for takeoff when runway is safe
- Detect and prevent collisions through safety checks

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Installation

```bash
# Clone the repository
git clone https://github.com/lavanyavijayk/ATC-AI-Agent
cd ATC-AI-Agent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### Running the System

**Terminal 1 - Start the Simulator:**
```bash
cd simulator-app
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 - Start the AI Agent:**
```bash
cd agent
python main.py
```

**Browser:**
Open http://localhost:8000 to view the radar display

## 📁 Project Structure

```
ATC-AI-Agent/
├── requirements.txt            # Python dependencies
├── .env                        # API keys (create from .env.example)
│
├── agent/                      # AI Agent Module
│   ├── main.py                 # Main entry point - runs the AI agent loop
│   ├── config.py               # Configuration settings (loads .env)
│   ├── atc_agent.py            # LangGraph workflow & ATCAgent class
│   │
│   ├── airport/                # Airport Domain Models
│   │   ├── airport.py          # Airport class - runway management
│   │   ├── flight.py           # Flight class - aircraft representation
│   │   ├── runway.py           # Runway class - runway status & assignment
│   │   ├── scheduler.py        # FlightScheduler - priority queue management
│   │   └── saftey_checks.py    # Collision detection & conflict prediction
│   │
│   ├── database/               # Database Layer
│   │   ├── atc_db.py           # ATC communication history (SQLite)
│   │   └── flights_db.py       # Flight tracking database
│   │
│   ├── prompts/                # LLM Prompts
│   │   ├── landing_prompt.py   # Prompt template for landing decisions
│   │   └── take_off_prompt.py  # Prompt template for takeoff decisions
│   │
│   └── utils/                  # Utility Modules
│       ├── llm.py              # Gemini LLM wrapper with retry logic
│       ├── weather_data.py     # NOAA weather service integration
│       ├── communication.py    # Communication utilities
│       ├── common.py           # Common helper functions
│       └── singleton.py        # Singleton pattern implementation
│
└── simulator-app/              # Flight Simulator
    ├── app/
    │   ├── main.py             # FastAPI application + WebSocket
    │   ├── api.py              # REST API endpoints
    │   ├── models.py           # Pydantic data models
    │   └── simulation.py       # Flight physics engine
    ├── static/
    │   ├── index.html          # Radar display UI
    │   ├── style.css           # Dark theme styling
    │   └── app.js              # Frontend logic
    └── README.md               # Detailed simulator docs
```

## 🎮 How It Works

### AI Agent Workflow

The agent uses LangGraph to implement a state machine workflow:

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────┐
│ Entry Point │ ──▶ │ Landing Node │ ──▶ │ Safety Check │ ──▶ │ End │
└─────────────┘     │   or         │     └──────────────┘     └─────┘
                    │ Takeoff Node │            │
                    └──────────────┘            │ retry (max 3)
                           ▲                    │
                           └────────────────────┘
```

1. **Entry Point**: Load flight data and conversation history from SQLite database
2. **Landing/Takeoff Node**: LLM generates appropriate command using contextual prompts
3. **Safety Check**: Validate command for runway conflicts and collision risks
4. **Retry or End**: Retry with safety context or send validated command to simulator

### Main Loop (`agent/main.py`)

The agent continuously polls the simulator API and processes flights:

1. Fetch all landing flights from `/api/flights/landing/`
2. Track flight state changes in local SQLite database
3. Invoke the LangGraph workflow when:
   - Flight passes a waypoint
   - Flight is ready for takeoff and not cleared
   - Flight has no target waypoint assigned
4. Send validated commands back to simulator via REST API

### Landing Pattern

Aircraft must follow this sequence to land at KRNT (Renton Municipal):

```
                    NORTH (departure exit)
                      │
    WEST ─────────────┼─────────────── EAST
                      │
              ┌───────┴───────┐
              │   DOWNWIND    │ (2000')
              │       │       │
              │       ▼       │
              │     BASE      │ (1500')
              │       │       │
              │       ▼       │
              │     FINAL     │ (1000')
              │       │       │
              │       ▼       │
              │    RUNWAY     │ (Heading 340°)
              └───────────────┘
                    SOUTH
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | Required |

### LLM Configuration (`agent/utils/llm.py`)

| Setting | Value | Description |
|---------|-------|-------------|
| Model | `gemini-2.5-flash` | Fast, efficient model |
| Temperature | `0.1` | Low for deterministic outputs |
| Max Retries | `3` | Retry attempts on API failure |
| Retry Delay | `60s` | Wait between retries |

### Landing Rules

| Rule | Value |
|------|-------|
| Max Altitude | 1500 ft |
| Speed Range | 100-180 kt |
| Max Distance | 18 nm |
| Required Waypoint | FINAL |

## 📡 API Reference

### Simulator Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/flights` | All active flights |
| GET | `/api/flights/landing` | Approaching flights |
| GET | `/api/flights/takeoff` | Departing flights |
| GET | `/api/flights/history` | Completed flights |
| GET | `/api/waypoints` | Navigation waypoints |
| GET | `/api/landing-rules` | Landing requirements |
| POST | `/api/flights/{callsign}/command` | Send command |
| POST | `/api/simulation/spawn/arrival` | Spawn arrival |
| POST | `/api/simulation/spawn/departure` | Spawn departure |

### Flight Commands

```json
// Vector to waypoint
{"waypoint": "FINAL", "altitude": 1000, "speed": 140}

// Clear to land
{"clear_to_land": true}

// Clear for takeoff
{"cleared_for_takeoff": true}
```

## 🛡️ Safety Features

The safety check node (`atc_agent.py`) validates all commands:

- **Takeoff Conflicts**: Blocks takeoff if any aircraft is on FINAL, RUNWAY, or actively landing/taking off
- **Clear to Land Conflicts**: Blocks landing clearance if runway is occupied
- **Pattern Conflicts**: Prevents two aircraft from targeting the same waypoint from the same position
- **Collision Prediction**: Uses `saftey_checks.py` to predict conflicts 2 minutes ahead
  - Horizontal threshold: 5 nm
  - Vertical threshold: 1000 ft

## 📊 Waypoints

### Entry Points (6000')
- NORTH, SOUTH, EAST, WEST, SHORT_EAST

### Traffic Pattern
- DOWNWIND (2000') → BASE (1500') → FINAL (1000') → RUNWAY

### AI Sequencing Points
- ALPHA, BRAVO (5000') - North sequencing
- CHARLIE, DELTA (4000') - South sequencing  
- ECHO (2500') - Extended final
- HOTEL (3500') - Holding point

## 🗄️ Database

The agent uses SQLite databases stored locally:

- **`atc.db`**: Stores ATC communication history
  - Commands sent to flights
  - LLM responses and retry counts
  - Used for conversation context in prompts

- **Flight tracking**: Monitors flight state changes to determine when to invoke the LLM

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License
