from typing import List, Optional, Tuple

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import Post
from app.database import Database


class PostRepository:
    
    @staticmethod
    async def create(post: Post, session: Optional[AsyncSession] = None) -> Post:
        if session is None:
            session = await Database.get_session()
            try:
                session.add(post)
                await session.commit()
                await session.refresh(post)
                return post
            finally:
                await session.close()
        else:
            session.add(post)
            await session.flush()
            await session.refresh(post)
            return post
    
    @staticmethod
    async def create_many(posts: List[Post], session: Optional[AsyncSession] = None) -> List[Post]:
        if not posts:
            return []
        
        if session is None:
            session = await Database.get_session()
            try:
                session.add_all(posts)
                await session.commit()
                for post in posts:
                    await session.refresh(post)
                return posts
            finally:
                await session.close()
        else:
            session.add_all(posts)
            await session.flush()
            for post in posts:
                await session.refresh(post)
            return posts
    
    @staticmethod
    async def get_by_post_id(post_id: str, session: Optional[AsyncSession] = None) -> Optional[Post]:
        if session is None:
            session = await Database.get_session()
            try:
                result = await session.execute(
                    select(Post).where(Post.post_id == post_id)
                )
                return result.scalar_one_or_none()
            finally:
                await session.close()
        else:
            result = await session.execute(
                select(Post).where(Post.post_id == post_id)
            )
            return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_id(id: int, session: Optional[AsyncSession] = None) -> Optional[Post]:
        if session is None:
            session = await Database.get_session()
            try:
                result = await session.execute(
                    select(Post).where(Post.id == id)
                )
                return result.scalar_one_or_none()
            finally:
                await session.close()
        else:
            result = await session.execute(
                select(Post).where(Post.id == id)
            )
            return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_page_id(
        page_id: str,
        skip: int = 0,
        limit: int = 10,
        session: Optional[AsyncSession] = None
    ) -> Tuple[List[Post], int]:
        if session is None:
            session = await Database.get_session()
            should_close = True
        else:
            should_close = False
        
        try:
            count_result = await session.execute(
                select(func.count()).select_from(Post).where(Post.page_id == page_id)
            )
            total = count_result.scalar()
            
            result = await session.execute(
                select(Post)
                .where(Post.page_id == page_id)
                .order_by(Post.posted_at.desc().nulls_last(), Post.scraped_at.desc())
                .offset(skip)
                .limit(limit)
            )
            posts = list(result.scalars().all())
            
            return posts, total
        finally:
            if should_close:
                await session.close()
    
    @staticmethod
    async def update(post: Post, session: Optional[AsyncSession] = None) -> Post:
        if session is None:
            session = await Database.get_session()
            try:
                session.add(post)
                await session.commit()
                await session.refresh(post)
                return post
            finally:
                await session.close()
        else:
            session.add(post)
            await session.flush()
            await session.refresh(post)
            return post
    
    @staticmethod
    async def delete(post_id: str, session: Optional[AsyncSession] = None) -> bool:
        if session is None:
            session = await Database.get_session()
            try:
                post = await PostRepository.get_by_post_id(post_id, session)
                if post:
                    await session.delete(post)
                    await session.commit()
                    return True
                return False
            finally:
                await session.close()
        else:
            post = await PostRepository.get_by_post_id(post_id, session)
            if post:
                await session.delete(post)
                await session.flush()
                return True
            return False
    
    @staticmethod
    async def delete_by_page_id(page_id: str, session: Optional[AsyncSession] = None) -> int:
        if session is None:
            session = await Database.get_session()
            try:
                result = await session.execute(
                    delete(Post).where(Post.page_id == page_id)
                )
                await session.commit()
                return result.rowcount
            finally:
                await session.close()
        else:
            result = await session.execute(
                delete(Post).where(Post.page_id == page_id)
            )
            await session.flush()
            return result.rowcount
    
    @staticmethod
    async def exists(post_id: str, session: Optional[AsyncSession] = None) -> bool:
        if session is None:
            session = await Database.get_session()
            try:
                result = await session.execute(
                    select(func.count()).select_from(Post).where(Post.post_id == post_id)
                )
                return result.scalar() > 0
            finally:
                await session.close()
        else:
            result = await session.execute(
                select(func.count()).select_from(Post).where(Post.post_id == post_id)
            )
            return result.scalar() > 0
    
    @staticmethod
    async def upsert(post: Post, session: Optional[AsyncSession] = None) -> Post:
        if session is None:
            session = await Database.get_session()
            should_close = True
        else:
            should_close = False
        
        try:
            existing = await PostRepository.get_by_post_id(post.post_id, session)
            if existing:
                existing.content = post.content
                existing.like_count = post.like_count
                existing.comment_count = post.comment_count
                existing.share_count = post.share_count
                existing.media_url = post.media_url
                existing.media_type = post.media_type
                existing.post_url = post.post_url
                existing.posted_at = post.posted_at
                existing.scraped_at = post.scraped_at
                
                session.add(existing)
                if should_close:
                    await session.commit()
                    await session.refresh(existing)
                else:
                    await session.flush()
                    await session.refresh(existing)
                return existing
            else:
                session.add(post)
                if should_close:
                    await session.commit()
                    await session.refresh(post)
                else:
                    await session.flush()
                    await session.refresh(post)
                return post
        finally:
            if should_close:
                await session.close()
    
    @staticmethod
    async def upsert_many(posts: List[Post], session: Optional[AsyncSession] = None) -> List[Post]:
        if session is None:
            session = await Database.get_session()
            should_close = True
        else:
            should_close = False
        
        try:
            results = []
            for post in posts:
                result = await PostRepository.upsert(post, session)
                results.append(result)
            
            if should_close:
                await session.commit()
            
            return results
        finally:
            if should_close:
                await session.close()
