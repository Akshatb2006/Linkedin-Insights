from typing import List, Optional, Tuple

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment
from app.database import Database


class CommentRepository:
    
    @staticmethod
    async def create(comment: Comment, session: Optional[AsyncSession] = None) -> Comment:
        if session is None:
            session = await Database.get_session()
            try:
                session.add(comment)
                await session.commit()
                await session.refresh(comment)
                return comment
            finally:
                await session.close()
        else:
            session.add(comment)
            await session.flush()
            await session.refresh(comment)
            return comment
    
    @staticmethod
    async def create_many(comments: List[Comment], session: Optional[AsyncSession] = None) -> List[Comment]:
        if not comments:
            return []
        
        if session is None:
            session = await Database.get_session()
            try:
                session.add_all(comments)
                await session.commit()
                for comment in comments:
                    await session.refresh(comment)
                return comments
            finally:
                await session.close()
        else:
            session.add_all(comments)
            await session.flush()
            for comment in comments:
                await session.refresh(comment)
            return comments
    
    @staticmethod
    async def get_by_comment_id(comment_id: str, session: Optional[AsyncSession] = None) -> Optional[Comment]:
        if session is None:
            session = await Database.get_session()
            try:
                result = await session.execute(
                    select(Comment).where(Comment.comment_id == comment_id)
                )
                return result.scalar_one_or_none()
            finally:
                await session.close()
        else:
            result = await session.execute(
                select(Comment).where(Comment.comment_id == comment_id)
            )
            return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_id(id: int, session: Optional[AsyncSession] = None) -> Optional[Comment]:
        if session is None:
            session = await Database.get_session()
            try:
                result = await session.execute(
                    select(Comment).where(Comment.id == id)
                )
                return result.scalar_one_or_none()
            finally:
                await session.close()
        else:
            result = await session.execute(
                select(Comment).where(Comment.id == id)
            )
            return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_post_id(
        post_id: str,
        skip: int = 0,
        limit: int = 10,
        session: Optional[AsyncSession] = None
    ) -> Tuple[List[Comment], int]:
        if session is None:
            session = await Database.get_session()
            should_close = True
        else:
            should_close = False
        
        try:
            count_result = await session.execute(
                select(func.count()).select_from(Comment).where(Comment.post_id == post_id)
            )
            total = count_result.scalar()
            
            result = await session.execute(
                select(Comment)
                .where(Comment.post_id == post_id)
                .order_by(Comment.commented_at.desc().nulls_last())
                .offset(skip)
                .limit(limit)
            )
            comments = list(result.scalars().all())
            
            return comments, total
        finally:
            if should_close:
                await session.close()
    
    @staticmethod
    async def get_by_page_id(
        page_id: str,
        skip: int = 0,
        limit: int = 10,
        session: Optional[AsyncSession] = None
    ) -> Tuple[List[Comment], int]:
        if session is None:
            session = await Database.get_session()
            should_close = True
        else:
            should_close = False
        
        try:
            count_result = await session.execute(
                select(func.count()).select_from(Comment).where(Comment.page_id == page_id)
            )
            total = count_result.scalar()
            
            result = await session.execute(
                select(Comment)
                .where(Comment.page_id == page_id)
                .order_by(Comment.commented_at.desc().nulls_last())
                .offset(skip)
                .limit(limit)
            )
            comments = list(result.scalars().all())
            
            return comments, total
        finally:
            if should_close:
                await session.close()
    
    @staticmethod
    async def update(comment: Comment, session: Optional[AsyncSession] = None) -> Comment:
        if session is None:
            session = await Database.get_session()
            try:
                session.add(comment)
                await session.commit()
                await session.refresh(comment)
                return comment
            finally:
                await session.close()
        else:
            session.add(comment)
            await session.flush()
            await session.refresh(comment)
            return comment
    
    @staticmethod
    async def delete(comment_id: str, session: Optional[AsyncSession] = None) -> bool:
        if session is None:
            session = await Database.get_session()
            try:
                comment = await CommentRepository.get_by_comment_id(comment_id, session)
                if comment:
                    await session.delete(comment)
                    await session.commit()
                    return True
                return False
            finally:
                await session.close()
        else:
            comment = await CommentRepository.get_by_comment_id(comment_id, session)
            if comment:
                await session.delete(comment)
                await session.flush()
                return True
            return False
    
    @staticmethod
    async def delete_by_post_id(post_id: str, session: Optional[AsyncSession] = None) -> int:
        if session is None:
            session = await Database.get_session()
            try:
                result = await session.execute(
                    delete(Comment).where(Comment.post_id == post_id)
                )
                await session.commit()
                return result.rowcount
            finally:
                await session.close()
        else:
            result = await session.execute(
                delete(Comment).where(Comment.post_id == post_id)
            )
            await session.flush()
            return result.rowcount
    
    @staticmethod
    async def delete_by_page_id(page_id: str, session: Optional[AsyncSession] = None) -> int:
        if session is None:
            session = await Database.get_session()
            try:
                result = await session.execute(
                    delete(Comment).where(Comment.page_id == page_id)
                )
                await session.commit()
                return result.rowcount
            finally:
                await session.close()
        else:
            result = await session.execute(
                delete(Comment).where(Comment.page_id == page_id)
            )
            await session.flush()
            return result.rowcount
    
    @staticmethod
    async def upsert(comment: Comment, session: Optional[AsyncSession] = None) -> Comment:
        if session is None:
            session = await Database.get_session()
            should_close = True
        else:
            should_close = False
        
        try:
            existing = await CommentRepository.get_by_comment_id(comment.comment_id, session)
            if existing:
                existing.content = comment.content
                existing.author_name = comment.author_name
                existing.author_profile_url = comment.author_profile_url
                existing.author_headline = comment.author_headline
                existing.like_count = comment.like_count
                existing.commented_at = comment.commented_at
                existing.scraped_at = comment.scraped_at
                
                session.add(existing)
                if should_close:
                    await session.commit()
                    await session.refresh(existing)
                else:
                    await session.flush()
                    await session.refresh(existing)
                return existing
            else:
                session.add(comment)
                if should_close:
                    await session.commit()
                    await session.refresh(comment)
                else:
                    await session.flush()
                    await session.refresh(comment)
                return comment
        finally:
            if should_close:
                await session.close()
    
    @staticmethod
    async def upsert_many(comments: List[Comment], session: Optional[AsyncSession] = None) -> List[Comment]:
        if session is None:
            session = await Database.get_session()
            should_close = True
        else:
            should_close = False
        
        try:
            results = []
            for comment in comments:
                result = await CommentRepository.upsert(comment, session)
                results.append(result)
            
            if should_close:
                await session.commit()
            
            return results
        finally:
            if should_close:
                await session.close()
