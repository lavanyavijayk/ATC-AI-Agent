"""
LLM Wrapper for Google Gemini API
"""
import time
import google.generativeai as genai
from config import GEMINI_API_KEY

# Configure API
genai.configure(api_key=GEMINI_API_KEY)


class LLM:
    """
    Wrapper class for Google's Gemini Language Model.
    
    Provides a simple interface to invoke the Gemini model with
    configured generation parameters for ATC decision-making.
    """
    
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 60
    
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        """Initialize the LLM wrapper."""
        self.model_name = model_name
        print(f"[LLM] Initialized with model: {self.model_name}")

    def invoke(self, prompt: str) -> str:
        """
        Send a prompt to the Gemini model and get a response.
        
        Implements retry logic with delay between attempts.
        
        Args:
            prompt: The text prompt to send to the model
            
        Returns:
            The model's response text, or None if all retries failed
        """
        last_error = None
        
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                print(f"[LLM] Invoking model (attempt {attempt}/{self.MAX_RETRIES})...")
                model = genai.GenerativeModel(self.model_name)
                
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,
                        top_p=0.95,
                    )
                )
                
                if response and response.text:
                    preview = response.text[:200] if len(response.text) > 200 else response.text
                    print(f"[LLM] Response received: {preview}...")
                    return response.text
                else:
                    print(f"[LLM] WARNING: Empty response on attempt {attempt}")
                    last_error = "Empty response from model"
                
            except Exception as e:
                last_error = str(e)
                print(f"[LLM] ERROR on attempt {attempt}: {e}")
            
            if attempt < self.MAX_RETRIES:
                print(f"[LLM] Waiting {self.RETRY_DELAY_SECONDS}s before retry...")
                time.sleep(self.RETRY_DELAY_SECONDS)
        
        print(f"[LLM] FAILED: All {self.MAX_RETRIES} attempts exhausted. Last error: {last_error}")
        return None

