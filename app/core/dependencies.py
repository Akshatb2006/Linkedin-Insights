from typing import Optional

from fastapi import Depends

from app.config import get_settings, Settings
from app.services.cache import CacheManager, BaseCacheStrategy
from app.services.ai import AIProviderFactory, BaseAIProvider
from app.repositories.page_repository import PageRepository
from app.repositories.post_repository import PostRepository
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.comment_repository import CommentRepository
from app.services.page_service import PageService


def get_config() -> Settings:
    return get_settings()


async def get_cache_strategy(
    config: Settings = Depends(get_config)
) -> BaseCacheStrategy:
    return await CacheManager.get_strategy()


async def get_cache_manager() -> type[CacheManager]:
    await CacheManager.get_strategy()
    return CacheManager


async def get_ai_provider(
    config: Settings = Depends(get_config)
) -> Optional[BaseAIProvider]:
    if not config.is_ai_enabled:
        return None
    return await AIProviderFactory.get_provider()


def is_ai_available(
    config: Settings = Depends(get_config)
) -> bool:
    return config.is_ai_enabled and AIProviderFactory.is_available()


def get_page_repository() -> type[PageRepository]:
    return PageRepository


def get_post_repository() -> type[PostRepository]:
    return PostRepository


def get_employee_repository() -> type[EmployeeRepository]:
    return EmployeeRepository


def get_comment_repository() -> type[CommentRepository]:
    return CommentRepository


def get_page_service() -> type[PageService]:
    return PageService


class AIAnalysisContext:
    def __init__(
        self,
        ai_provider: Optional[BaseAIProvider],
        cache: BaseCacheStrategy,
        page_service: type[PageService],
        config: Settings,
    ):
        self.ai_provider = ai_provider
        self.cache = cache
        self.page_service = page_service
        self.config = config

    @property
    def is_ai_available(self) -> bool:
        return self.ai_provider is not None and self.ai_provider.is_available()


async def get_ai_analysis_context(
    ai_provider: Optional[BaseAIProvider] = Depends(get_ai_provider),
    cache: BaseCacheStrategy = Depends(get_cache_strategy),
    page_service: type[PageService] = Depends(get_page_service),
    config: Settings = Depends(get_config),
) -> AIAnalysisContext:
    return AIAnalysisContext(
        ai_provider=ai_provider,
        cache=cache,
        page_service=page_service,
        config=config,
    )
