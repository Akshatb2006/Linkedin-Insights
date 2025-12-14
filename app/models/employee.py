from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.page import Page


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    page_id: Mapped[str] = mapped_column(String(255), ForeignKey("pages.page_id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    designation: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    profile_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    profile_picture_url: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    page: Mapped["Page"] = relationship("Page", back_populates="employees")

    def __repr__(self) -> str:
        return f"<Employee(name='{self.name}', page_id='{self.page_id}')>"
