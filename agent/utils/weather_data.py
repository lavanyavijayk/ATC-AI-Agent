import requests


class WeatherInfo:
    def __init__(self):
        pass

    def get_noaa_weather(self, icao_code: str):
        """
        Fetches METAR and TAF data for a given ICAO airport code from NOAA Aviation Weather Center.

        Args:
            icao_code (str): 4-letter ICAO airport code (e.g., 'KSFO', 'KJFK', 'VOMM')

        Returns:
            dict: A dictionary containing current METAR and TAF details if available
        """
        base_url = "https://aviationweather.gov/api/data"
        
        # Get current METAR
        metar_url = f"{base_url}/metar?ids={icao_code.upper()}&format=json"
        taf_url = f"{base_url}/taf?ids={icao_code.upper()}&format=json"
        
        try:
            metar_response = requests.get(metar_url, timeout=10)
            taf_response = requests.get(taf_url, timeout=10)
            
            metar_data = metar_response.json() if metar_response.ok else {}
            taf_data = taf_response.json() if taf_response.ok else {}
            
            result = {
                "icao": icao_code.upper(),
                "metar": metar_data[0] if metar_data else None,
                "taf": taf_data[0] if taf_data else None
            }
            return result
        
        except Exception as e:
            print(f"Error fetching weather for {icao_code}: {e}")
            return None


# print(WeatherInfo().get_noaa_weather("KSEA"))