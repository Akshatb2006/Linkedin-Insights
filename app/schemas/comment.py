from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import PaginationMeta


class CommentResponse(BaseModel):
    comment_id: str = Field(..., description="Unique comment ID")
    post_id: str = Field(..., description="Reference to Post")
    page_id: str = Field(..., description="Reference to Page")
    author_name: str = Field(..., description="Comment author name")
    author_profile_url: Optional[str] = Field(None, description="Author profile URL")
    author_headline: Optional[str] = Field(None, description="Author headline")
    content: str = Field(..., description="Comment text")
    like_count: int = Field(default=0, description="Number of likes")
    commented_at: Optional[datetime] = Field(None, description="Comment timestamp")
    scraped_at: datetime = Field(..., description="When data was scraped")
    
    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    success: bool = True
    data: List[CommentResponse]
    pagination: PaginationMeta


class CommentCreateRequest(BaseModel):
    comment_id: str
    post_id: str
    page_id: str
    author_name: str
    content: str
    author_profile_url: Optional[str] = None
    author_headline: Optional[str] = None
    like_count: int = 0
    commented_at: Optional[datetime] = None
