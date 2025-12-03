"""
Database Module for ATC System
"""
from .atc_db import ATCDatabase
from .flights_db import FlightDatabase

__all__ = ["ATCDatabase", "FlightDatabase"]

