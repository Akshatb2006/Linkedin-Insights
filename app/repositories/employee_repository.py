from typing import List, Optional, Tuple

from sqlalchemy import select, func, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.database import Database


class EmployeeRepository:
    
    @staticmethod
    async def create(employee: Employee, session: Optional[AsyncSession] = None) -> Employee:
        if session is None:
            session = await Database.get_session()
            try:
                session.add(employee)
                await session.commit()
                await session.refresh(employee)
                return employee
            finally:
                await session.close()
        else:
            session.add(employee)
            await session.flush()
            await session.refresh(employee)
            return employee
    
    @staticmethod
    async def create_many(employees: List[Employee], session: Optional[AsyncSession] = None) -> List[Employee]:
        if not employees:
            return []
        
        if session is None:
            session = await Database.get_session()
            try:
                session.add_all(employees)
                await session.commit()
                for employee in employees:
                    await session.refresh(employee)
                return employees
            finally:
                await session.close()
        else:
            session.add_all(employees)
            await session.flush()
            for employee in employees:
                await session.refresh(employee)
            return employees
    
    @staticmethod
    async def get_by_id(id: int, session: Optional[AsyncSession] = None) -> Optional[Employee]:
        if session is None:
            session = await Database.get_session()
            try:
                result = await session.execute(
                    select(Employee).where(Employee.id == id)
                )
                return result.scalar_one_or_none()
            finally:
                await session.close()
        else:
            result = await session.execute(
                select(Employee).where(Employee.id == id)
            )
            return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_page_id(
        page_id: str,
        skip: int = 0,
        limit: int = 10,
        session: Optional[AsyncSession] = None
    ) -> Tuple[List[Employee], int]:
        if session is None:
            session = await Database.get_session()
            should_close = True
        else:
            should_close = False
        
        try:
            count_result = await session.execute(
                select(func.count()).select_from(Employee).where(Employee.page_id == page_id)
            )
            total = count_result.scalar()
            
            result = await session.execute(
                select(Employee)
                .where(Employee.page_id == page_id)
                .order_by(Employee.name)
                .offset(skip)
                .limit(limit)
            )
            employees = list(result.scalars().all())
            
            return employees, total
        finally:
            if should_close:
                await session.close()
    
    @staticmethod
    async def get_by_name(
        page_id: str,
        name: str,
        session: Optional[AsyncSession] = None
    ) -> Optional[Employee]:
        if session is None:
            session = await Database.get_session()
            try:
                result = await session.execute(
                    select(Employee).where(
                        and_(Employee.page_id == page_id, Employee.name == name)
                    )
                )
                return result.scalar_one_or_none()
            finally:
                await session.close()
        else:
            result = await session.execute(
                select(Employee).where(
                    and_(Employee.page_id == page_id, Employee.name == name)
                )
            )
            return result.scalar_one_or_none()
    
    @staticmethod
    async def update(employee: Employee, session: Optional[AsyncSession] = None) -> Employee:
        if session is None:
            session = await Database.get_session()
            try:
                session.add(employee)
                await session.commit()
                await session.refresh(employee)
                return employee
            finally:
                await session.close()
        else:
            session.add(employee)
            await session.flush()
            await session.refresh(employee)
            return employee
    
    @staticmethod
    async def delete_by_page_id(page_id: str, session: Optional[AsyncSession] = None) -> int:
        if session is None:
            session = await Database.get_session()
            try:
                result = await session.execute(
                    delete(Employee).where(Employee.page_id == page_id)
                )
                await session.commit()
                return result.rowcount
            finally:
                await session.close()
        else:
            result = await session.execute(
                delete(Employee).where(Employee.page_id == page_id)
            )
            await session.flush()
            return result.rowcount
    
    @staticmethod
    async def upsert(employee: Employee, session: Optional[AsyncSession] = None) -> Employee:
        if session is None:
            session = await Database.get_session()
            should_close = True
        else:
            should_close = False
        
        try:
            existing = await EmployeeRepository.get_by_name(
                employee.page_id, 
                employee.name,
                session
            )
            if existing:
                existing.designation = employee.designation
                existing.location = employee.location
                existing.profile_url = employee.profile_url
                existing.profile_picture_url = employee.profile_picture_url
                existing.scraped_at = employee.scraped_at
                
                session.add(existing)
                if should_close:
                    await session.commit()
                    await session.refresh(existing)
                else:
                    await session.flush()
                    await session.refresh(existing)
                return existing
            else:
                session.add(employee)
                if should_close:
                    await session.commit()
                    await session.refresh(employee)
                else:
                    await session.flush()
                    await session.refresh(employee)
                return employee
        finally:
            if should_close:
                await session.close()
    
    @staticmethod
    async def upsert_many(employees: List[Employee], session: Optional[AsyncSession] = None) -> List[Employee]:
        if session is None:
            session = await Database.get_session()
            should_close = True
        else:
            should_close = False
        
        try:
            results = []
            for employee in employees:
                result = await EmployeeRepository.upsert(employee, session)
                results.append(result)
            
            if should_close:
                await session.commit()
            
            return results
        finally:
            if should_close:
                await session.close()
    
    @staticmethod
    async def count_by_page_id(page_id: str, session: Optional[AsyncSession] = None) -> int:
        if session is None:
            session = await Database.get_session()
            try:
                result = await session.execute(
                    select(func.count()).select_from(Employee).where(Employee.page_id == page_id)
                )
                return result.scalar()
            finally:
                await session.close()
        else:
            result = await session.execute(
                select(func.count()).select_from(Employee).where(Employee.page_id == page_id)
            )
            return result.scalar()
