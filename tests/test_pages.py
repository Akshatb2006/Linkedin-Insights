import pytest
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Page, Post, Employee


class TestPageModel:

    @pytest.mark.asyncio
    async def test_create_page(self, session: AsyncSession):
        page = Page(
            page_id="new-company",
            name="New Company",
            url="https://www.linkedin.com/company/new-company/",
            industry="Technology",
            follower_count=10000,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            scraped_at=datetime.utcnow(),
        )

        session.add(page)
        await session.commit()
        await session.refresh(page)

        assert page.id is not None
        assert page.page_id == "new-company"
        assert page.name == "New Company"
        assert page.follower_count == 10000

    @pytest.mark.asyncio
    async def test_get_page_by_id(self, session: AsyncSession, sample_page: Page):
        result = await session.execute(
            select(Page).where(Page.page_id == "test-company")
        )
        page = result.scalar_one_or_none()

        assert page is not None
        assert page.page_id == "test-company"
        assert page.name == "Test Company"

    @pytest.mark.asyncio
    async def test_page_relationships(self, session: AsyncSession, sample_page: Page, sample_posts: list):
        await session.refresh(sample_page)

        result = await session.execute(
            select(func.count()).select_from(Post).where(Post.page_id == sample_page.page_id)
        )
        post_count = result.scalar()

        assert post_count == 5


class TestPostModel:

    @pytest.mark.asyncio
    async def test_get_posts_by_page_id(self, session: AsyncSession, sample_posts: list, sample_page: Page):
        result = await session.execute(
            select(Post).where(Post.page_id == sample_page.page_id)
        )
        posts = result.scalars().all()

        assert len(posts) == 5
        assert all(p.page_id == sample_page.page_id for p in posts)

    @pytest.mark.asyncio
    async def test_post_pagination(self, session: AsyncSession, sample_posts: list, sample_page: Page):
        result = await session.execute(
            select(Post)
            .where(Post.page_id == sample_page.page_id)
            .offset(0)
            .limit(2)
        )
        posts = result.scalars().all()

        assert len(posts) == 2


class TestEmployeeModel:

    @pytest.mark.asyncio
    async def test_get_employees_by_page_id(self, session: AsyncSession, sample_employees: list, sample_page: Page):
        result = await session.execute(
            select(Employee).where(Employee.page_id == sample_page.page_id)
        )
        employees = result.scalars().all()

        assert len(employees) == 3
        assert all(e.page_id == sample_page.page_id for e in employees)
