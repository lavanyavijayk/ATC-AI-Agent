from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
API_BASE_URL = "http://localhost:8000/api"