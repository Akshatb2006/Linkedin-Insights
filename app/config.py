from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  
    )
    
    database_url: str = "sqlite+aiosqlite:///./linkedin_insights.db"
    
    scraper_headless: bool = True
    scraper_timeout: int = 30
    scraper_page_load_timeout: int = 30
    scraper_implicit_wait: int = 10
    
    api_v1_prefix: str = "/api/v1"
    debug: bool = True
    
    gemini_api_key: Optional[str] = None
    ai_model: str = "gemini-1.5-flash"
    
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 300  
    cache_enabled: bool = True
    
    @property
    def is_sqlite(self) -> bool:
        return "sqlite" in self.database_url.lower()
    
    @property
    def is_mysql(self) -> bool:
        return "mysql" in self.database_url.lower()
    
    @property
    def is_ai_enabled(self) -> bool:
        return self.gemini_api_key is not None and len(self.gemini_api_key) > 0


@lru_cache()
def get_settings() -> Settings:
    return Settings()
