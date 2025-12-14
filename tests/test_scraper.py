import pytest
from app.services.scraper_service import LinkedInScraper


class TestLinkedInScraper:

    def test_parse_follower_count_millions(self):
        scraper = LinkedInScraper()

        assert scraper._parse_follower_count("1.5M followers") == 1500000
        assert scraper._parse_follower_count("2M followers") == 2000000

    def test_parse_follower_count_thousands(self):
        scraper = LinkedInScraper()

        assert scraper._parse_follower_count("50K followers") == 50000
        assert scraper._parse_follower_count("1.5K followers") == 1500

    def test_parse_follower_count_plain(self):
        scraper = LinkedInScraper()

        assert scraper._parse_follower_count("1000 followers") == 1000
        assert scraper._parse_follower_count("500") == 500

    def test_parse_follower_count_invalid(self):
        scraper = LinkedInScraper()

        assert scraper._parse_follower_count("") == 0
        assert scraper._parse_follower_count("invalid") == 0
        assert scraper._parse_follower_count(None) == 0

    def test_parse_engagement_count(self):
        scraper = LinkedInScraper()

        assert scraper._parse_engagement_count("1,234 likes") == 1234
        assert scraper._parse_engagement_count("5.2K") == 5200
        assert scraper._parse_engagement_count("1M") == 1000000

    def test_generate_post_id(self):
        scraper = LinkedInScraper()

        id1 = scraper._generate_post_id("company1", "content1", 0)
        id2 = scraper._generate_post_id("company1", "content2", 0)
        id3 = scraper._generate_post_id("company1", "content1", 1)

        assert id1 != id2
        assert id1 != id3

    def test_generate_comment_id(self):
        scraper = LinkedInScraper()

        id1 = scraper._generate_comment_id("post1", "author1", "content1", 0)
        id2 = scraper._generate_comment_id("post1", "author2", "content1", 0)

        assert id1 != id2


class TestScraperIntegration:

    @pytest.mark.skip(reason="Requires network access and may be rate-limited")
    @pytest.mark.asyncio
    async def test_scrape_page(self):
        scraper = LinkedInScraper()

        try:
            page = await scraper.scrape_page("microsoft")

            assert page is not None
            assert page.page_id == "microsoft"
            assert page.name is not None
        finally:
            scraper.close()
