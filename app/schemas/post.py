from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import PaginationMeta


class PostResponse(BaseModel):
    post_id: str = Field(..., description="Unique post ID")
    page_id: str = Field(..., description="Reference to Page")
    content: Optional[str] = Field(None, description="Post text content")
    like_count: int = Field(default=0, description="Number of likes")
    comment_count: int = Field(default=0, description="Number of comments")
    share_count: int = Field(default=0, description="Number of shares")
    media_url: Optional[str] = Field(None, description="Media attachment URL")
    media_type: Optional[str] = Field(None, description="Type of media")
    post_url: Optional[str] = Field(None, description="Direct post URL")
    posted_at: Optional[datetime] = Field(None, description="Publication date")
    scraped_at: datetime = Field(..., description="When data was scraped")
    
    class Config:
        from_attributes = True


class PostListResponse(BaseModel):
    success: bool = True
    data: List[PostResponse]
    pagination: PaginationMeta


class PostCreateRequest(BaseModel):
    post_id: str
    page_id: str
    content: Optional[str] = None
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    post_url: Optional[str] = None
    posted_at: Optional[datetime] = None
