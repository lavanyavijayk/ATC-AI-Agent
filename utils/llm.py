from config import GEMINI_API_KEY
import google.generativeai as genai
import time
 

# Configure Google Gemini API key
genai.configure(api_key=GEMINI_API_KEY)


class LLM:
    """
    Wrapper class for Google's Gemini Language Model.
    
    Provides a simple interface to invoke the Gemini model with
    configured generation parameters for ATC decision-making.
    Includes automatic retry logic with configurable delays.
    """
    
    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 60  # 1 minute between retries
    
    def __init__(self):
        """Initialize the LLM wrapper."""
        self.model_name = 'gemini-2.5-flash'
        print(f"[LLM] Initialized with model: {self.model_name}")
        print(f"[LLM] Retry config: max_retries={self.MAX_RETRIES}, delay={self.RETRY_DELAY_SECONDS}s")

    def invoke(self, prompt: str) -> str:
        """
        Send a prompt to the Gemini model and get a response.
        
        Implements retry logic with 1-minute delay between attempts
        in case of API failures or rate limiting.
        
        Args:
            prompt: The text prompt to send to the model
            
        Returns:
            The model's response text, or None if all retries failed
        """
        last_error = None
        
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                print(f"[LLM] Invoking Gemini model (attempt {attempt}/{self.MAX_RETRIES})...")
                model = genai.GenerativeModel(self.model_name)
                
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,  # Low temperature for consistent, deterministic outputs
                        top_p=0.95,
                    )
                )
                
                # Check if we got a valid response
                if response and response.text:
                    response_preview = response.text[:200] if len(response.text) > 200 else response.text
                    print(f"[LLM] Response received: {response_preview}...")
                    return response.text
                else:
                    print(f"[LLM] WARNING: Empty response received on attempt {attempt}")
                    last_error = "Empty response from model"
                
            except Exception as e:
                last_error = str(e)
                print(f"[LLM] ERROR on attempt {attempt}: {e}")
            
            # If this wasn't the last attempt, wait before retrying
            if attempt < self.MAX_RETRIES:
                print(f"[LLM] Waiting {self.RETRY_DELAY_SECONDS} seconds before retry...")
                time.sleep(self.RETRY_DELAY_SECONDS)
        
        # All retries exhausted
        print(f"[LLM] FAILED: All {self.MAX_RETRIES} attempts exhausted. Last error: {last_error}")
        return None