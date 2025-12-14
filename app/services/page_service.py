from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from app.models.page import Page
from app.models.post import Post
from app.models.comment import Comment
from app.models.employee import Employee
from app.repositories.page_repository import PageRepository
from app.repositories.post_repository import PostRepository
from app.repositories.comment_repository import CommentRepository
from app.repositories.employee_repository import EmployeeRepository
from app.services.scraper_service import (
    LinkedInScraper,
    ScrapedPageData,
    ScrapedPostData,
    ScrapedEmployeeData,
    LoginWallException,
    ScrapingException,
)
from app.schemas.page import PageSearchParams


@dataclass
class ScrapingResult:
    success: bool
    page: Optional[Page] = None
    source: str = "error"
    error_message: Optional[str] = None
    is_login_wall: bool = False
    retryable: bool = True


class PageService:
    @staticmethod
    async def get_page(
        page_id: str, 
        force_refresh: bool = False
    ) -> ScrapingResult:
        if not force_refresh:
            existing_page = await PageRepository.get_by_page_id(page_id)
            if existing_page:
                return ScrapingResult(
                    success=True,
                    page=existing_page,
                    source="database",
                )
        
        try:
            result = await PageService._scrape_and_store(page_id)
            if result and result.get("page"):
                page = await PageRepository.get_by_page_id(page_id)
                return ScrapingResult(
                    success=True,
                    page=page,
                    source="scraped",
                )
            else:
                return ScrapingResult(
                    success=False,
                    source="error",
                    error_message="Failed to scrape page data",
                    retryable=True,
                )
        
        except LoginWallException as e:
            return ScrapingResult(
                success=False,
                source="login_wall",
                error_message=e.message,
                is_login_wall=True,
                retryable=False,
            )
        
        except ScrapingException as e:
            return ScrapingResult(
                success=False,
                source="scraper_error",
                error_message=e.message,
                is_login_wall=e.is_login_wall,
                retryable=e.retryable,
            )
        
        except Exception as e:
            return ScrapingResult(
                success=False,
                source="error",
                error_message=str(e),
                retryable=True,
            )
    
    @staticmethod
    async def _scrape_and_store(page_id: str) -> Optional[Dict[str, Any]]:
        scraper = LinkedInScraper()
        
        try:
            scraped_data = await scraper.scrape_all(
                page_id,
                posts_limit=20,
                employees_limit=20
            )
            
            if not scraped_data["page"]:
                raise ScrapingException("No page data returned", retryable=True)
            
            page = await PageService._store_page(scraped_data["page"])
            
            posts_count = await PageService._store_posts(scraped_data["posts"])
            
            employees_count = await PageService._store_employees(scraped_data["employees"])
            
            return {
                "page": page.page_id if page else None,
                "posts_count": posts_count,
                "employees_count": employees_count,
            }
            
        finally:
            scraper.close()
    
    @staticmethod
    async def _store_page(page_data: ScrapedPageData) -> Page:
        page = Page(
            page_id=page_data.page_id,
            name=page_data.name,
            url=page_data.url,
            linkedin_id=page_data.linkedin_id,
            profile_picture_url=page_data.profile_picture_url,
            description=page_data.description,
            website=page_data.website,
            industry=page_data.industry,
            follower_count=page_data.follower_count,
            headcount=page_data.headcount,
            specialities=page_data.specialities,
            founded=page_data.founded,
            headquarters=page_data.headquarters,
            company_type=page_data.company_type,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            scraped_at=datetime.utcnow(),
        )
        
        return await PageRepository.upsert(page)
    
    @staticmethod
    async def _store_posts(posts_data: List[ScrapedPostData]) -> int:
        posts = []
        for post_data in posts_data:
            post = Post(
                post_id=post_data.post_id,
                page_id=post_data.page_id,
                content=post_data.content,
                like_count=post_data.like_count,
                comment_count=post_data.comment_count,
                share_count=post_data.share_count,
                media_url=post_data.media_url,
                media_type=post_data.media_type,
                post_url=post_data.post_url,
                posted_at=post_data.posted_at,
                scraped_at=datetime.utcnow(),
            )
            posts.append(post)
        
        if posts:
            await PostRepository.upsert_many(posts)
        
        return len(posts)
    
    @staticmethod
    async def _store_employees(employees_data: List[ScrapedEmployeeData]) -> int:
        employees = []
        for emp_data in employees_data:
            employee = Employee(
                page_id=emp_data.page_id,
                name=emp_data.name,
                designation=emp_data.designation,
                location=emp_data.location,
                profile_url=emp_data.profile_url,
                profile_picture_url=emp_data.profile_picture_url,
                scraped_at=datetime.utcnow(),
            )
            employees.append(employee)
        
        if employees:
            await EmployeeRepository.upsert_many(employees)
        
        return len(employees)
    
    @staticmethod
    async def search_pages(
        params: PageSearchParams,
        page: int = 1,
        limit: int = 10
    ) -> Tuple[List[Page], int]:
        skip = (page - 1) * limit
        return await PageRepository.search(params, skip=skip, limit=limit)
    
    @staticmethod
    async def get_posts(
        page_id: str,
        page: int = 1,
        limit: int = 10
    ) -> Tuple[List[Post], int]:
        skip = (page - 1) * limit
        return await PostRepository.get_by_page_id(page_id, skip=skip, limit=limit)
    
    @staticmethod
    async def get_employees(
        page_id: str,
        page: int = 1,
        limit: int = 10
    ) -> Tuple[List[Employee], int]:
        skip = (page - 1) * limit
        return await EmployeeRepository.get_by_page_id(page_id, skip=skip, limit=limit)
    
    @staticmethod
    async def get_comments(
        page_id: str,
        page: int = 1,
        limit: int = 10
    ) -> Tuple[List[Comment], int]:
        skip = (page - 1) * limit
        return await CommentRepository.get_by_page_id(page_id, skip=skip, limit=limit)
    
    @staticmethod
    async def delete_page(page_id: str) -> bool:
        await CommentRepository.delete_by_page_id(page_id)
        await PostRepository.delete_by_page_id(page_id)
        await EmployeeRepository.delete_by_page_id(page_id)
        
        return await PageRepository.delete(page_id)
