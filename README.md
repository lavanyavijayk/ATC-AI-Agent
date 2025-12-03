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
python main.py
```

**Browser:**
Open http://localhost:8000 to view the radar display

## 📁 Project Structure

```
ATC-AI-Agent/
├── main.py                 # Main entry point - runs the AI agent
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
├── .env                    # API keys (create from .env.example)
│
├── agent/                  # AI Agent Module
│   ├── __init__.py
│   ├── atc_agent.py        # Main agent with LangGraph workflow
│   ├── llm.py              # Gemini LLM wrapper
│   └── safety.py           # Safety checks & collision detection
│
├── core/                   # Core Domain Models
│   ├── __init__.py
│   ├── models.py           # Flight, Airport, Runway classes
│   └── weather.py          # NOAA weather service
│
├── database/               # Database Layer
│   ├── __init__.py
│   ├── atc_db.py           # ATC communication history
│   └── flights_db.py       # Flight tracking database
│
└── simulator-app/          # Flight Simulator
    ├── app/
    │   ├── main.py         # FastAPI application
    │   ├── api.py          # REST API endpoints
    │   ├── models.py       # Pydantic data models
    │   └── simulation.py   # Flight physics engine
    ├── static/
    │   ├── index.html      # Radar display UI
    │   ├── style.css       # Dark theme styling
    │   └── app.js          # Frontend logic
    └── README.md           # Detailed simulator docs
```

## 🎮 How It Works

### AI Agent Workflow

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────┐
│ Entry Point │ ──▶ │ Landing Node │ ──▶ │ Safety Check │ ──▶ │ End │
└─────────────┘     │   or         │     └──────────────┘     └─────┘
                    │ Takeoff Node │            │
                    └──────────────┘            │ retry
                           ▲                   │
                           └───────────────────┘
```

1. **Entry Point**: Load flight data and conversation history
2. **Landing/Takeoff Node**: LLM generates appropriate command
3. **Safety Check**: Validate command for conflicts
4. **Retry or End**: Retry with new context or send command

### Landing Pattern

Aircraft must follow this sequence to land:

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
              │    RUNWAY     │
              └───────────────┘
                    SOUTH
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `SIMULATOR_HOST` | Simulator hostname | `localhost` |
| `SIMULATOR_PORT` | Simulator port | `8000` |
| `AGENT_POLL_INTERVAL` | Polling interval (seconds) | `5` |

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

- **Collision Detection**: Predicts conflicts up to 2 minutes ahead
- **Separation Monitoring**: Maintains 3nm horizontal / 1000ft vertical
- **Runway Conflict Prevention**: Checks for aircraft on final, landing, or taking off
- **Pattern Protection**: Validates landing sequence progression

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

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License
