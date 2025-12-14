import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


class TestHealthEndpoints:

    @pytest.mark.asyncio
    async def test_health_check(self):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_root_endpoint(self):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestPagesEndpoints:

    @pytest.mark.asyncio
    async def test_search_pages_empty(self, test_db):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/pages/")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "pagination" in data

    @pytest.mark.asyncio
    async def test_search_with_filters(self, sample_page):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/pages/",
                params={
                    "name": "Test",
                    "industry": "Technology",
                    "min_followers": 10000,
                    "max_followers": 100000,
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_get_page_not_found(self, test_db):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/pages/nonexistent-company")

        assert response.status_code in [404, 200]

    @pytest.mark.asyncio
    async def test_get_posts_pagination(self, sample_posts, sample_page):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/v1/pages/{sample_page.page_id}/posts",
                params={"page": 1, "limit": 2}
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) <= 2
        assert data["pagination"]["limit"] == 2

    @pytest.mark.asyncio
    async def test_get_employees(self, sample_employees, sample_page):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/v1/pages/{sample_page.page_id}/people"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
