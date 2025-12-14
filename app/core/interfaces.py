from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class ICacheStrategy(Protocol):
    async def get(self, key: str) -> Optional[Any]:
        ...

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        ...

    async def delete(self, key: str) -> bool:
        ...

    async def exists(self, key: str) -> bool:
        ...

    async def clear_pattern(self, pattern: str) -> int:
        ...


@dataclass
class AIAnalysisResult:
    executive_summary: str
    company_profile: str
    engagement_analysis: str
    audience_insights: str
    recommendations: List[str]
    provider: str
    model: str
    tokens_used: Optional[int] = None


@runtime_checkable
class IAIProvider(Protocol):
    @property
    def provider_name(self) -> str:
        ...

    @property
    def model_name(self) -> str:
        ...

    async def generate_analysis(self, prompt: str) -> Optional[AIAnalysisResult]:
        ...

    def is_available(self) -> bool:
        ...


@runtime_checkable
class IRepository(Protocol):
    async def get_by_id(self, id: Any) -> Optional[Any]:
        ...

    async def create(self, entity: Any) -> Any:
        ...

    async def update(self, entity: Any) -> Any:
        ...

    async def delete(self, id: Any) -> bool:
        ...


class IPageRepository(IRepository, Protocol):
    async def get_by_page_id(self, page_id: str) -> Optional[Any]:
        ...

    async def search(
        self,
        params: Any,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[List[Any], int]:
        ...

    async def upsert(self, page: Any) -> Any:
        ...


class IPostRepository(IRepository, Protocol):
    async def get_by_page_id(
        self,
        page_id: str,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[List[Any], int]:
        ...


class IEmployeeRepository(IRepository, Protocol):
    async def get_by_page_id(
        self,
        page_id: str,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[List[Any], int]:
        ...


@dataclass
class ScrapedPage:
    page_id: str
    name: str
    url: str
    industry: Optional[str] = None
    follower_count: int = 0
    description: Optional[str] = None
    headquarters: Optional[str] = None
    founded: Optional[str] = None
    headcount: Optional[str] = None
    company_type: Optional[str] = None
    specialities: List[str] = field(default_factory=list)
    website: Optional[str] = None
    profile_picture_url: Optional[str] = None


class IScraper(Protocol):
    async def scrape_page(self, page_id: str) -> Optional[ScrapedPage]:
        ...

    async def scrape_posts(self, page_id: str, limit: int = 10) -> List[Any]:
        ...

    async def scrape_employees(self, page_id: str, limit: int = 10) -> List[Any]:
        ...

    def close(self) -> None:
        ...


@dataclass
class PageResult:
    success: bool
    page: Optional[Any] = None
    source: str = "unknown"
    error_message: Optional[str] = None
    is_login_wall: bool = False
    retryable: bool = True


class IPageService(Protocol):
    async def get_page(
        self,
        page_id: str,
        force_refresh: bool = False,
    ) -> PageResult:
        ...

    async def search_pages(
        self,
        params: Any,
        page: int = 1,
        limit: int = 10,
    ) -> tuple[List[Any], int]:
        ...

    async def get_posts(
        self,
        page_id: str,
        page: int = 1,
        limit: int = 10,
    ) -> tuple[List[Any], int]:
        ...

    async def get_employees(
        self,
        page_id: str,
        page: int = 1,
        limit: int = 10,
    ) -> tuple[List[Any], int]:
        ...
