from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


def get_async_database_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


class Base(DeclarativeBase):
    pass


class Database:
    engine = None
    async_session_factory = None

    @classmethod
    async def connect(cls) -> None:
        settings = get_settings()
        database_url = get_async_database_url(settings.database_url)

        connect_args = {}
        if settings.is_sqlite:
            connect_args["check_same_thread"] = False

        cls.engine = create_async_engine(
            database_url,
            echo=settings.debug,
            connect_args=connect_args if settings.is_sqlite else {},
        )

        cls.async_session_factory = async_sessionmaker(
            bind=cls.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with cls.engine.begin() as conn:
            from app.models import Page, Post, Comment, Employee
            await conn.run_sync(Base.metadata.create_all)

        print(f"✅ Connected to database: {settings.database_url.split('@')[-1] if '@' in settings.database_url else settings.database_url}")

    @classmethod
    async def disconnect(cls) -> None:
        if cls.engine:
            await cls.engine.dispose()
            print("🔌 Disconnected from database")

    @classmethod
    async def get_session(cls) -> AsyncSession:
        if cls.async_session_factory is None:
            raise RuntimeError("Database not initialized. Call Database.connect() first.")
        return cls.async_session_factory()


async def get_db() -> AsyncSession:
    async with Database.async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    await Database.connect()


async def close_db() -> None:
    await Database.disconnect()
