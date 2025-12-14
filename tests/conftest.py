import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.database import Base
from app.models import Page, Post, Comment, Employee


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async_session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield async_session_factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def session(test_db) -> AsyncGenerator[AsyncSession, None]:
    async with test_db() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def sample_page(session: AsyncSession) -> Page:
    from datetime import datetime

    page = Page(
        page_id="test-company",
        name="Test Company",
        url="https://www.linkedin.com/company/test-company/",
        linkedin_id="12345",
        description="A test company for unit testing",
        website="https://test-company.com",
        industry="Technology",
        follower_count=50000,
        headcount="51-200",
        specialities=["Testing", "QA", "Automation"],
        founded="2020",
        headquarters="San Francisco, CA",
        company_type="Privately Held",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        scraped_at=datetime.utcnow(),
    )
    session.add(page)
    await session.commit()
    await session.refresh(page)
    return page


@pytest_asyncio.fixture(scope="function")
async def sample_posts(session: AsyncSession, sample_page: Page) -> list:
    from datetime import datetime

    posts = []
    for i in range(5):
        post = Post(
            post_id=f"post_{i}",
            page_id=sample_page.page_id,
            content=f"Test post content {i}",
            like_count=100 * (i + 1),
            comment_count=10 * (i + 1),
            share_count=5 * (i + 1),
            scraped_at=datetime.utcnow(),
        )
        session.add(post)
        posts.append(post)

    await session.commit()
    for post in posts:
        await session.refresh(post)

    return posts


@pytest_asyncio.fixture(scope="function")
async def sample_employees(session: AsyncSession, sample_page: Page) -> list:
    from datetime import datetime

    employees = []
    for i in range(3):
        employee = Employee(
            page_id=sample_page.page_id,
            name=f"Employee {i}",
            designation=f"Title {i}",
            location="San Francisco, CA",
            scraped_at=datetime.utcnow(),
        )
        session.add(employee)
        employees.append(employee)

    await session.commit()
    for employee in employees:
        await session.refresh(employee)

    return employees
