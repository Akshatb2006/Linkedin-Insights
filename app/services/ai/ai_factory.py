from app.config import get_settings
from app.services.ai.base import BaseAIProvider
from app.services.ai.gemini_provider import GeminiAIProvider

from typing import Optional

class AIProviderFactory:
    _instance: Optional[BaseAIProvider] = None
    
    _providers = {
        "gemini": GeminiAIProvider,
    }
    
    @classmethod
    async def get_provider(cls, provider_type: Optional[str] = None) -> Optional[BaseAIProvider]:
        settings = get_settings()
        
        if cls._instance is not None and cls._instance.is_available():
            return cls._instance
        
        if provider_type is None:
            if settings.gemini_api_key:
                provider_type = "gemini"
            else:
                print("⚠️ No AI provider configured (GEMINI_API_KEY not set)")
                return None
        
        provider_class = cls._providers.get(provider_type)
        if not provider_class:
            print(f"❌ Unknown AI provider type: {provider_type}")
            return None
        
        try:
            if provider_type == "gemini":
                provider = GeminiAIProvider(
                    api_key=settings.gemini_api_key,
                    model=settings.ai_model
                )
            else:
                print(f"❌ Provider {provider_type} not implemented")
                return None
            
            await provider.initialize()
            cls._instance = provider
            return provider
            
        except Exception as e:
            print(f"❌ Failed to create AI provider: {e}")
            return None
    
    @classmethod
    def is_available(cls) -> bool:
        settings = get_settings()
        return bool(settings.gemini_api_key)
    
    @classmethod
    def get_configured_provider_type(cls) -> Optional[str]:
        settings = get_settings()
        if settings.gemini_api_key:
            return "gemini"
        return None
    
    @classmethod
    def register_provider(cls, name: str, provider_class: type) -> None:
        cls._providers[name] = provider_class
        print(f"📝 Registered AI provider: {name}")
