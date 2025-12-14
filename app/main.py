from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db, close_db
from app.routers import pages_router, health_router
from app.routers.ai import router as ai_router
from app.services.cache import CacheManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting LinkedIn Insights Microservice...")
    print("📐 Design Patterns: Repository, Strategy, Factory, DI")
    await init_db()
    await CacheManager.get_strategy()
    yield
    await CacheManager.close()
    await close_db()
    print("👋 LinkedIn Insights Microservice shutdown complete")


settings = get_settings()

app = FastAPI(
    title="LinkedIn Insights Microservice",
    description="A backend microservice to fetch, store, and query LinkedIn company page insights. Built with SOLID principles and modern design patterns.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(pages_router, prefix=settings.api_v1_prefix)
app.include_router(ai_router, prefix=settings.api_v1_prefix)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
