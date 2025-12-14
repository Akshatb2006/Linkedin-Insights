from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import PaginationMeta


class EmployeeResponse(BaseModel):
    page_id: str = Field(..., description="Reference to Page")
    name: str = Field(..., description="Employee name")
    designation: Optional[str] = Field(None, description="Job title")
    location: Optional[str] = Field(None, description="Geographic location")
    profile_url: Optional[str] = Field(None, description="LinkedIn profile URL")
    profile_picture_url: Optional[str] = Field(None, description="Profile picture URL")
    scraped_at: datetime = Field(..., description="When data was scraped")
    
    class Config:
        from_attributes = True


class EmployeeListResponse(BaseModel):
    success: bool = True
    data: List[EmployeeResponse]
    pagination: PaginationMeta


class EmployeeCreateRequest(BaseModel):
    page_id: str
    name: str
    designation: Optional[str] = None
    location: Optional[str] = None
    profile_url: Optional[str] = None
    profile_picture_url: Optional[str] = None
