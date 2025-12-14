from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import String, Integer, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.post import Post
    from app.models.employee import Employee


class Page(Base):
    
    __tablename__ = "pages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    page_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    linkedin_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    profile_picture_url: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    follower_count: Mapped[int] = mapped_column(Integer, default=0, index=True)
    headcount: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    specialities: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    founded: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    headquarters: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    company_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    posts: Mapped[List["Post"]] = relationship("Post", back_populates="page", cascade="all, delete-orphan")
    employees: Mapped[List["Employee"]] = relationship("Employee", back_populates="page", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Page(page_id='{self.page_id}', name='{self.name}')>"
    
    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()
