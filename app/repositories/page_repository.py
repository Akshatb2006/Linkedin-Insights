from typing import List, Optional, Tuple

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.page import Page
from app.schemas.page import PageSearchParams
from app.database import Database


class PageRepository:
    
    @staticmethod
    async def create(page: Page, session: Optional[AsyncSession] = None) -> Page:
        if session is None:
            session = await Database.get_session()
            try:
                session.add(page)
                await session.commit()
                await session.refresh(page)
                return page
            finally:
                await session.close()
        else:
            session.add(page)
            await session.flush()
            await session.refresh(page)
            return page
    
    @staticmethod
    async def get_by_page_id(page_id: str, session: Optional[AsyncSession] = None) -> Optional[Page]:
        if session is None:
            session = await Database.get_session()
            try:
                result = await session.execute(
                    select(Page).where(Page.page_id == page_id)
                )
                return result.scalar_one_or_none()
            finally:
                await session.close()
        else:
            result = await session.execute(
                select(Page).where(Page.page_id == page_id)
            )
            return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_id(id: int, session: Optional[AsyncSession] = None) -> Optional[Page]:
        if session is None:
            session = await Database.get_session()
            try:
                result = await session.execute(
                    select(Page).where(Page.id == id)
                )
                return result.scalar_one_or_none()
            finally:
                await session.close()
        else:
            result = await session.execute(
                select(Page).where(Page.id == id)
            )
            return result.scalar_one_or_none()
    
    @staticmethod
    async def update(page: Page, session: Optional[AsyncSession] = None) -> Page:
        page.update_timestamp()
        if session is None:
            session = await Database.get_session()
            try:
                session.add(page)
                await session.commit()
                await session.refresh(page)
                return page
            finally:
                await session.close()
        else:
            session.add(page)
            await session.flush()
            await session.refresh(page)
            return page
    
    @staticmethod
    async def delete(page_id: str, session: Optional[AsyncSession] = None) -> bool:
        if session is None:
            session = await Database.get_session()
            try:
                page = await PageRepository.get_by_page_id(page_id, session)
                if page:
                    await session.delete(page)
                    await session.commit()
                    return True
                return False
            finally:
                await session.close()
        else:
            page = await PageRepository.get_by_page_id(page_id, session)
            if page:
                await session.delete(page)
                await session.flush()
                return True
            return False
    
    @staticmethod
    async def exists(page_id: str, session: Optional[AsyncSession] = None) -> bool:
        if session is None:
            session = await Database.get_session()
            try:
                result = await session.execute(
                    select(func.count()).select_from(Page).where(Page.page_id == page_id)
                )
                return result.scalar() > 0
            finally:
                await session.close()
        else:
            result = await session.execute(
                select(func.count()).select_from(Page).where(Page.page_id == page_id)
            )
            return result.scalar() > 0
    
    @staticmethod
    async def search(
        params: PageSearchParams,
        skip: int = 0,
        limit: int = 10,
        session: Optional[AsyncSession] = None
    ) -> Tuple[List[Page], int]:
        if session is None:
            session = await Database.get_session()
            should_close = True
        else:
            should_close = False
        
        try:
            conditions = []
            
            if params.name:
                conditions.append(Page.name.ilike(f"%{params.name}%"))
            
            if params.industry:
                conditions.append(Page.industry.ilike(params.industry))
            
            if params.min_followers is not None:
                conditions.append(Page.follower_count >= params.min_followers)
            if params.max_followers is not None:
                conditions.append(Page.follower_count <= params.max_followers)
            
            base_query = select(Page)
            count_query = select(func.count()).select_from(Page)
            
            if conditions:
                base_query = base_query.where(and_(*conditions))
                count_query = count_query.where(and_(*conditions))
            
            total_result = await session.execute(count_query)
            total = total_result.scalar()
            
            query = base_query.offset(skip).limit(limit).order_by(Page.created_at.desc())
            result = await session.execute(query)
            pages = list(result.scalars().all())
            
            return pages, total
        finally:
            if should_close:
                await session.close()
    
    @staticmethod
    async def get_all(
        skip: int = 0, 
        limit: int = 10,
        session: Optional[AsyncSession] = None
    ) -> Tuple[List[Page], int]:
        if session is None:
            session = await Database.get_session()
            should_close = True
        else:
            should_close = False
        
        try:
            count_result = await session.execute(
                select(func.count()).select_from(Page)
            )
            total = count_result.scalar()
            
            result = await session.execute(
                select(Page).offset(skip).limit(limit).order_by(Page.created_at.desc())
            )
            pages = list(result.scalars().all())
            
            return pages, total
        finally:
            if should_close:
                await session.close()
    
    @staticmethod
    async def upsert(page: Page, session: Optional[AsyncSession] = None) -> Page:
        if session is None:
            session = await Database.get_session()
            should_close = True
        else:
            should_close = False
        
        try:
            existing = await PageRepository.get_by_page_id(page.page_id, session)
            if existing:
                existing.linkedin_id = page.linkedin_id
                existing.name = page.name
                existing.url = page.url
                existing.profile_picture_url = page.profile_picture_url
                existing.description = page.description
                existing.website = page.website
                existing.industry = page.industry
                existing.follower_count = page.follower_count
                existing.headcount = page.headcount
                existing.specialities = page.specialities
                existing.founded = page.founded
                existing.headquarters = page.headquarters
                existing.company_type = page.company_type
                existing.scraped_at = page.scraped_at
                existing.update_timestamp()
                
                session.add(existing)
                if should_close:
                    await session.commit()
                    await session.refresh(existing)
                else:
                    await session.flush()
                    await session.refresh(existing)
                return existing
            else:
                session.add(page)
                if should_close:
                    await session.commit()
                    await session.refresh(page)
                else:
                    await session.flush()
                    await session.refresh(page)
                return page
        finally:
            if should_close:
                await session.close()
