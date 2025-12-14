from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import PaginatedResponse, PaginationMeta


class PageResponse(BaseModel):
    
    page_id: str = Field(..., description="URL identifier")
    linkedin_id: Optional[str] = Field(None, description="LinkedIn platform ID")
    name: str = Field(..., description="Company name")
    url: str = Field(..., description="Full LinkedIn URL")
    profile_picture_url: Optional[str] = Field(None, description="Profile picture URL")
    description: Optional[str] = Field(None, description="About section")
    website: Optional[str] = Field(None, description="Company website")
    industry: Optional[str] = Field(None, description="Business industry")
    follower_count: int = Field(default=0, description="Number of followers")
    headcount: Optional[str] = Field(None, description="Employee count range")
    specialities: List[str] = Field(default_factory=list, description="Company specialities")
    founded: Optional[str] = Field(None, description="Year founded")
    headquarters: Optional[str] = Field(None, description="Headquarters location")
    company_type: Optional[str] = Field(None, description="Type of company")
    scraped_at: datetime = Field(..., description="Last scraped timestamp")
    
    class Config:
        from_attributes = True


class PageDetailResponse(BaseModel):
    
    success: bool = True
    data: PageResponse
    source: str = Field(..., description="Data source: 'database' or 'scraped'")


class PageListResponse(BaseModel):
    
    success: bool = True
    data: List[PageResponse]
    pagination: PaginationMeta


class PageSearchParams(BaseModel):
    
    name: Optional[str] = Field(None, description="Partial match on page name")
    industry: Optional[str] = Field(None, description="Filter by industry")
    min_followers: Optional[int] = Field(None, ge=0, description="Minimum follower count")
    max_followers: Optional[int] = Field(None, ge=0, description="Maximum follower count")


class PageCreateRequest(BaseModel):
    
    page_id: str
    name: str
    url: str
    linkedin_id: Optional[str] = None
    profile_picture_url: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    follower_count: int = 0
    headcount: Optional[str] = None
    specialities: List[str] = []
    founded: Optional[str] = None
    headquarters: Optional[str] = None
    company_type: Optional[str] = None
