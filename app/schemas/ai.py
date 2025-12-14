
from typing import List, Optional
from pydantic import BaseModel, Field


class PageSummaryResponse(BaseModel):
    executive_summary: str = Field(..., description="Brief overview of the company's LinkedIn presence")
    company_profile: str = Field(..., description="Analysis of company type and industry position")
    engagement_analysis: str = Field(..., description="Analysis of content engagement metrics")
    audience_insights: str = Field(..., description="Insights about the company's audience")
    recommendations: List[str] = Field(default_factory=list, description="Strategic recommendations")
    generated_by: str = Field(default="gemini-1.5-flash", description="AI model used")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "executive_summary": "Microsoft has a strong LinkedIn presence with 21M followers, indicating significant brand authority in the technology sector.",
                "company_profile": "As a Fortune 500 public company founded in 1975, Microsoft is a global leader in cloud computing, AI, and enterprise software.",
                "engagement_analysis": "Posts receive high engagement with an average of 15,000+ likes, suggesting strong audience interest in their content.",
                "audience_insights": "The 21M follower base likely includes IT professionals, developers, enterprise decision-makers, and tech enthusiasts.",
                "recommendations": [
                    "Continue focusing on AI and cloud computing content",
                    "Increase video content for higher engagement",
                    "Leverage employee advocacy for broader reach"
                ],
                "generated_by": "gemini-1.5-flash"
            }
        }
    }


class PageWithSummaryResponse(BaseModel):
    success: bool = True
    data: dict = Field(..., description="Page data")
    source: str = Field(..., description="Data source (database/scraped)")
    ai_summary: Optional[PageSummaryResponse] = Field(None, description="AI-generated summary")
    cached: bool = Field(False, description="Whether data was served from cache")


class CacheStatsResponse(BaseModel):
    backend: str = Field(..., description="Cache backend type (redis/memory)")
    entries: int = Field(0, description="Number of cached entries")
    ttl_seconds: int = Field(..., description="Default TTL in seconds")
    enabled: bool = Field(..., description="Whether caching is enabled")
    memory_used: Optional[str] = Field(None, description="Memory usage (Redis only)")
    error: Optional[str] = Field(None, description="Error message if any")
