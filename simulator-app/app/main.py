"""Main FastAPI application for AI-ATC simulator."""
import asyncio
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from . import api
from .api import router as api_router
from .simulation import simulator


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


async def broadcast_updates(flights, stats, near_misses, history):
    """Callback to broadcast flight updates to WebSocket clients."""
    if manager.active_connections:
        await manager.broadcast({
            "type": "update",
            "flights": [f.model_dump() for f in flights],
            "stats": stats,
            "near_misses": near_misses,
            "history": history,
        })


async def broadcast_atc_message(message: dict):
    """Broadcast an ATC message to all connected clients."""
    if manager.active_connections:
        await manager.broadcast(message)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    simulator.update_callbacks.append(broadcast_updates)
    
    # Wire up ATC message broadcast callback
    api.atc_message_callback = broadcast_atc_message
    
    simulation_task = asyncio.create_task(simulator.run())
    
    yield
    
    simulator.stop()
    simulation_task.cancel()
    try:
        await simulation_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="AI-ATC Simulator",
    description="An online Air Traffic Control simulator with API for AI agents",
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(api_router)

static_dir = Path(__file__).parent.parent / "static"


@app.get("/")
async def root():
    """Serve the main radar display page."""
    return FileResponse(static_dir / "index.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time flight updates."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "command":
                    from .models import FlightCommand
                    callsign = message.get("callsign")
                    command_data = message.get("command", {})
                    command = FlightCommand(**command_data)
                    simulator.command_flight(callsign, command)
                elif message.get("type") == "set_speed":
                    simulator.set_speed(message.get("multiplier", 1.0))
                elif message.get("type") == "restart":
                    simulator.save_score()
                    simulator.reset()
                elif message.get("type") == "end":
                    simulator.save_score()
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)


if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
