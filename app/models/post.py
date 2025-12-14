from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.page import Page
    from app.models.comment import Comment


class Post(Base):
    __tablename__ = "posts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    page_id: Mapped[str] = mapped_column(String(255), ForeignKey("pages.page_id", ondelete="CASCADE"), nullable=False, index=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    share_count: Mapped[int] = mapped_column(Integer, default=0)
    media_url: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    media_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    post_url: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    page: Mapped["Page"] = relationship("Page", back_populates="posts")
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Post(post_id='{self.post_id}', page_id='{self.page_id}')>"
