from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.services.page_service import PageService
from app.schemas.common import (
    APIResponse,
    create_pagination_meta,
)
from app.schemas.page import (
    PageResponse,
    PageDetailResponse,
    PageListResponse,
    PageSearchParams,
)
from app.schemas.post import PostResponse, PostListResponse
from app.schemas.employee import EmployeeResponse, EmployeeListResponse
from app.schemas.comment import CommentResponse, CommentListResponse

router = APIRouter(prefix="/pages", tags=["Pages"])


@router.get(
    "/{page_id}",
    response_model=PageDetailResponse,
    summary="Get page details",
    description="Get details of a LinkedIn company page. If the page doesn't exist in the database, it will be scraped from LinkedIn.",
)
async def get_page(
    page_id: str,
    force_refresh: bool = Query(
        False,
        description="If true, re-scrape the page even if it exists in the database"
    ),
):
    result = await PageService.get_page(page_id, force_refresh=force_refresh)
    
    if not result.success:
        # Handle login wall specifically
        if result.is_login_wall:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "LinkedIn login wall detected",
                    "message": result.error_message or "Page requires authentication to access full data",
                    "page_id": page_id,
                    "url": f"https://www.linkedin.com/company/{page_id}/",
                    "retryable": result.retryable,
                    "note": "LinkedIn aggressively gates company pages. Consider adding page data manually or using LinkedIn API."
                }
            )
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Scraping failed",
                "message": result.error_message or f"Could not fetch page '{page_id}'",
                "page_id": page_id,
                "retryable": result.retryable,
            }
        )
    
    return PageDetailResponse(
        success=True,
        data=PageResponse.model_validate(result.page),
        source=result.source
    )



@router.get(
    "/",
    response_model=PageListResponse,
    summary="Search pages",
    description="Search for pages in the database with optional filters. This endpoint only searches the database and does NOT scrape LinkedIn.",
)
async def search_pages(
    name: Optional[str] = Query(
        None,
        description="Partial match on page name"
    ),
    industry: Optional[str] = Query(
        None,
        description="Filter by industry"
    ),
    min_followers: Optional[int] = Query(
        None,
        ge=0,
        description="Minimum follower count"
    ),
    max_followers: Optional[int] = Query(
        None,
        ge=0,
        description="Maximum follower count"
    ),
    page: int = Query(
        1,
        ge=1,
        description="Page number (1-indexed)"
    ),
    limit: int = Query(
        10,
        ge=1,
        le=100,
        description="Items per page"
    ),
):
    search_params = PageSearchParams(
        name=name,
        industry=industry,
        min_followers=min_followers,
        max_followers=max_followers,
    )
    
    pages, total = await PageService.search_pages(
        params=search_params,
        page=page,
        limit=limit
    )
    
    return PageListResponse(
        success=True,
        data=[PageResponse.model_validate(p) for p in pages],
        pagination=create_pagination_meta(page, limit, total)
    )


@router.get(
    "/{page_id}/posts",
    response_model=PostListResponse,
    summary="Get page posts",
    description="Get posts from a LinkedIn company page with pagination.",
)
async def get_page_posts(
    page_id: str,
    page: int = Query(
        1,
        ge=1,
        description="Page number (1-indexed)"
    ),
    limit: int = Query(
        10,
        ge=1,
        le=50,
        description="Items per page (max 50)"
    ),
):
    posts, total = await PageService.get_posts(
        page_id=page_id,
        page=page,
        limit=limit
    )
    
    return PostListResponse(
        success=True,
        data=[PostResponse.model_validate(p) for p in posts],
        pagination=create_pagination_meta(page, limit, total)
    )


@router.get(
    "/{page_id}/people",
    response_model=EmployeeListResponse,
    summary="Get page employees",
    description="Get employees/people working at a LinkedIn company page with pagination.",
)
async def get_page_employees(
    page_id: str,
    page: int = Query(
        1,
        ge=1,
        description="Page number (1-indexed)"
    ),
    limit: int = Query(
        10,
        ge=1,
        le=50,
        description="Items per page (max 50)"
    ),
):
    employees, total = await PageService.get_employees(
        page_id=page_id,
        page=page,
        limit=limit
    )
    
    return EmployeeListResponse(
        success=True,
        data=[EmployeeResponse.model_validate(e) for e in employees],
        pagination=create_pagination_meta(page, limit, total)
    )


@router.get(
    "/{page_id}/comments",
    response_model=CommentListResponse,
    summary="Get page comments",
    description="Get all comments from a LinkedIn company page's posts with pagination.",
)
async def get_page_comments(
    page_id: str,
    page: int = Query(
        1,
        ge=1,
        description="Page number (1-indexed)"
    ),
    limit: int = Query(
        10,
        ge=1,
        le=50,
        description="Items per page (max 50)"
    ),
):
    comments, total = await PageService.get_comments(
        page_id=page_id,
        page=page,
        limit=limit
    )
    
    return CommentListResponse(
        success=True,
        data=[CommentResponse.model_validate(c) for c in comments],
        pagination=create_pagination_meta(page, limit, total)
    )


@router.delete(
    "/{page_id}",
    response_model=APIResponse,
    summary="Delete page",
    description="Delete a page and all its related data (posts, comments, employees).",
)
async def delete_page(page_id: str):
    deleted = await PageService.delete_page(page_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page '{page_id}' not found"
        )
    
    return APIResponse(
        success=True,
        message=f"Page '{page_id}' and all related data deleted successfully"
    )
