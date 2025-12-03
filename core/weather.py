"""
Weather Data Service using NOAA Aviation Weather API
"""
import requests
from typing import Optional, Dict, Any


class WeatherService:
    """Fetches weather data from NOAA Aviation Weather Center"""
    
    BASE_URL = "https://aviationweather.gov/api/data"
    TIMEOUT = 10
    
    def get_weather(self, icao_code: str) -> Optional[Dict[str, Any]]:
        """
        Fetch METAR and TAF data for a given ICAO airport code.
        
        Args:
            icao_code: 4-letter ICAO airport code (e.g., 'KSEA', 'KJFK')
            
        Returns:
            Dictionary with METAR and TAF data, or None on error
        """
        icao = icao_code.upper()
        metar_url = f"{self.BASE_URL}/metar?ids={icao}&format=json"
        taf_url = f"{self.BASE_URL}/taf?ids={icao}&format=json"
        
        try:
            metar_response = requests.get(metar_url, timeout=self.TIMEOUT)
            taf_response = requests.get(taf_url, timeout=self.TIMEOUT)
            
            metar_data = metar_response.json() if metar_response.ok else []
            taf_data = taf_response.json() if taf_response.ok else []
            
            return {
                "icao": icao,
                "metar": metar_data[0] if metar_data else None,
                "taf": taf_data[0] if taf_data else None
            }
        
        except Exception as e:
            print(f"[Weather] Error fetching weather for {icao}: {e}")
            return None
    
    def get_summary(self, icao_code: str) -> str:
        """Get a brief weather summary string"""
        data = self.get_weather(icao_code)
        if not data or not data.get("metar"):
            return "Weather data unavailable"
        
        metar = data["metar"]
        return metar.get("rawOb", "No METAR available")

