from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class AIProvider(ABC):
    @abstractmethod
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate a response based on the message history."""
        pass

class MockAIProvider(AIProvider):
    """A mock provider for testing or when API keys are not set."""
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: Optional[str] = None
    ) -> str:
        last_message = messages[-1]['content'] if messages else ""
        return f"[Mock AI] You said: {last_message}"

class GeminiProvider(AIProvider):
    """Google Gemini AI Provider with automatic fallback across supported model versions."""
    def __init__(self, api_key: str):
        from google import genai
        self.client = genai.Client(api_key=api_key)
        self.candidate_models = [
            'gemini-2.5-flash',
            'gemini-flash-latest',
            'gemini-2.0-flash',
            'gemini-1.5-flash',
            'gemini-2.5-pro'
        ]
        self.preferred_model = 'gemini-2.5-flash'
        
    async def generate_response(
        self, 
        messages: List[Dict[str, Any]], 
        system_prompt: Optional[str] = None
    ) -> str:
        try:
            from PIL import Image
            contents = []
            if system_prompt:
                contents.append(f"System Instructions: {system_prompt}")
                
            for msg in messages:
                role = "user" if msg.get("role") == "user" else "model"
                parts = [f"{role.capitalize()}: {msg.get('content', '')}"]
                
                # Load images if any
                if "images" in msg:
                    for img_path in msg["images"]:
                        try:
                            img = Image.open(img_path)
                            parts.append(img)
                        except Exception as img_err:
                            print(f"Failed to load image {img_path}: {img_err}")
                
                contents.extend(parts)
            
            # Try candidate models
            last_error = None
            models_to_try = [self.preferred_model] + [m for m in self.candidate_models if m != self.preferred_model]
            
            for model_name in models_to_try:
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=contents,
                    )
                    if response and response.text:
                        self.preferred_model = model_name
                        return response.text
                except Exception as model_err:
                    last_error = model_err
                    continue
            
            raise last_error or Exception("All Gemini models failed.")
        except Exception as e:
            print(f"Gemini API Error: {e}")
            raise Exception(f"Failed to generate response from AI Provider: {e}")

def get_ai_provider(api_key: str = "") -> AIProvider:
    if not api_key or api_key.strip() in ["", "your_ai_api_key_here", "your_api_key_here"]:
        print("Warning: No valid AI_API_KEY provided, using MockAIProvider")
        return MockAIProvider()
    return GeminiProvider(api_key)
