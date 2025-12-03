"""
Configuration for ATC AI Agent
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Simulator Configuration
SIMULATOR_HOST = os.getenv("SIMULATOR_HOST", "localhost")
SIMULATOR_PORT = int(os.getenv("SIMULATOR_PORT", "8000"))
SIMULATOR_URL = f"http://{SIMULATOR_HOST}:{SIMULATOR_PORT}"

# Agent Configuration
AGENT_POLL_INTERVAL = int(os.getenv("AGENT_POLL_INTERVAL", "5"))
AGENT_MAX_RETRIES = int(os.getenv("AGENT_MAX_RETRIES", "3"))

# Database
DATABASE_PATH = os.getenv("DATABASE_PATH", "atc.db")
