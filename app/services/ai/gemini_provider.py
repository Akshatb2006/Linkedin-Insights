from typing import Optional

from app.services.ai.base import BaseAIProvider


class GeminiAIProvider(BaseAIProvider):
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        super().__init__(api_key, model)
        self._genai = None
        self._model_instance = None
    
    @property
    def provider_name(self) -> str:
        return "gemini"
    
    async def initialize(self) -> None:
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=self._api_key)
            self._genai = genai
            self._model_instance = genai.GenerativeModel(self._model)
            self._initialized = True
            
            print(f"✅ Initialized Gemini provider with model: {self._model}")
            
        except Exception as e:
            print(f"❌ Failed to initialize Gemini: {e}")
            self._initialized = False
            raise
    
    async def generate_content(self, prompt: str) -> Optional[str]:
        if not self._model_instance:
            print("⚠️ Gemini model not initialized")
            return None
        
        try:
            response = self._model_instance.generate_content(prompt)
            return response.text
            
        except Exception as e:
            print(f"❌ Gemini generation error: {e}")
            return None
