from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.config import Settings
from app.core.dependencies import (
    get_config,
    get_ai_provider,
    get_cache_manager,
    get_page_service,
    get_ai_analysis_context,
    AIAnalysisContext,
)
from app.services.ai import BaseAIProvider, AIProviderFactory
from app.services.cache import CacheManager
from app.services.page_service import PageService
from app.schemas.ai import PageSummaryResponse, PageWithSummaryResponse, CacheStatsResponse

router = APIRouter(prefix="/ai", tags=["AI & Analytics"])


@router.get(
    "/summary/{page_id}",
    response_model=PageWithSummaryResponse,
    summary="Get AI-powered page summary",
    description="Get a LinkedIn page with AI-generated insights using Google Gemini.",
)
async def get_page_with_ai_summary(
    page_id: str,
    include_posts: bool = Query(True, description="Include posts data in AI analysis"),
    include_employees: bool = Query(True, description="Include employees data in AI analysis"),
    skip_cache: bool = Query(False, description="Skip cache and regenerate summary"),
    context: AIAnalysisContext = Depends(get_ai_analysis_context),
):
    if not context.is_ai_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "AI features not available",
                "message": "GEMINI_API_KEY is not configured. Set it in .env file.",
                "hint": "Get your API key from https://makersuite.google.com/app/apikey"
            }
        )
    
    cache_key = f"{page_id}:{'posts' if include_posts else 'no_posts'}:{'emp' if include_employees else 'no_emp'}"
    
    if not skip_cache:
        cached_response = await CacheManager.get("ai_summary", cache_key)
        if cached_response:
            return PageWithSummaryResponse(
                success=True,
                data=cached_response["page_data"],
                source=cached_response["source"],
                ai_summary=PageSummaryResponse(**cached_response["ai_summary"]),
                cached=True
            )
    
    result = await context.page_service.get_page(page_id)
    
    if not result.success or not result.page:
        if result.is_login_wall:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "LinkedIn login wall detected",
                    "message": result.error_message,
                    "page_id": page_id,
                }
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Page not found", "page_id": page_id}
        )
    
    page_data = {
        "page_id": result.page.page_id,
        "name": result.page.name,
        "url": result.page.url,
        "industry": result.page.industry,
        "follower_count": result.page.follower_count,
        "company_type": result.page.company_type,
        "headquarters": result.page.headquarters,
        "founded": result.page.founded,
        "headcount": result.page.headcount,
        "specialities": result.page.specialities or [],
        "description": result.page.description,
    }
    
    posts_data = None
    employees_data = None
    
    if include_posts:
        posts, _ = await context.page_service.get_posts(page_id, page=1, limit=10)
        posts_data = [
            {
                "content": p.content,
                "like_count": p.like_count,
                "comment_count": p.comment_count,
                "share_count": p.share_count,
            }
            for p in posts
        ]
    
    if include_employees:
        employees, _ = await context.page_service.get_employees(page_id, page=1, limit=10)
        employees_data = [
            {
                "name": e.name,
                "designation": e.designation,
            }
            for e in employees
        ]
    
    ai_result = await context.ai_provider.generate_page_analysis(
        page_data=page_data,
        posts_data=posts_data,
        employees_data=employees_data,
    )
    
    if not ai_result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "AI summary generation failed"}
        )
    
    summary_response = PageSummaryResponse(
        executive_summary=ai_result.executive_summary,
        company_profile=ai_result.company_profile,
        engagement_analysis=ai_result.engagement_analysis,
        audience_insights=ai_result.audience_insights,
        recommendations=ai_result.recommendations,
        generated_by=f"{ai_result.provider}/{ai_result.model}",
    )
    
    cache_data = {
        "page_data": page_data,
        "source": result.source,
        "ai_summary": summary_response.model_dump(),
    }
    await CacheManager.set("ai_summary", cache_key, cache_data)
    
    return PageWithSummaryResponse(
        success=True,
        data=page_data,
        source=result.source,
        ai_summary=summary_response,
        cached=False
    )


@router.get(
    "/cache/stats",
    response_model=CacheStatsResponse,
    summary="Get cache statistics",
    description="Get statistics about the caching system.",
)
async def get_cache_stats():
    stats = await CacheManager.get_stats()
    return CacheStatsResponse(**stats)


@router.delete(
    "/cache/clear",
    summary="Clear cache",
    description="Clear all cached data or specific prefix.",
)
async def clear_cache(
    prefix: Optional[str] = Query(None, description="Optional prefix to clear")
):
    count = await CacheManager.clear_all(prefix)
    return {
        "success": True,
        "message": f"Cleared {count} cache entries",
        "prefix": prefix or "all"
    }


@router.get(
    "/providers",
    summary="Get available AI providers",
    description="Get information about configured AI providers.",
)
async def get_ai_providers(
    config: Settings = Depends(get_config),
):
    return {
        "available": AIProviderFactory.is_available(),
        "configured_provider": AIProviderFactory.get_configured_provider_type(),
        "model": config.ai_model if config.is_ai_enabled else None,
        "supported_providers": ["gemini"],  # Extensible list
    }
