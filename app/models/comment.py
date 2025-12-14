from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.post import Post


class Comment(Base):
    
    __tablename__ = "comments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    comment_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    post_id: Mapped[str] = mapped_column(String(255), ForeignKey("posts.post_id", ondelete="CASCADE"), nullable=False, index=True)
    page_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    author_name: Mapped[str] = mapped_column(String(500), nullable=False)
    author_profile_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    author_headline: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    commented_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    post: Mapped["Post"] = relationship("Post", back_populates="comments")
    
    def __repr__(self) -> str:
        return f"<Comment(comment_id='{self.comment_id}', post_id='{self.post_id}')>"
