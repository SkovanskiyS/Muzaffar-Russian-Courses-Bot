from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
from typing import Optional, List
import time

from database.models.courses import Course, CourseType, DifficultyLevel


# Course Type operations
async def create_course_type(db: AsyncSession, name: str, description: Optional[str] = None) -> CourseType:
    course_type = CourseType(
        name=name,
        description=description,
        created_at=int(time.time())
    )
    db.add(course_type)
    await db.commit()
    await db.refresh(course_type)
    return course_type

async def get_course_type(db: AsyncSession, course_type_id: int) -> Optional[CourseType]:
    query = select(CourseType).filter(CourseType.id == course_type_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_active_course_types(db: AsyncSession) -> List[CourseType]:
    query = select(CourseType).filter(CourseType.is_active == True)
    result = await db.execute(query)
    return result.scalars().all()

# Course operations
async def create_course(
    db: AsyncSession,
    course_type_id: int,
    title: str,
    description: str,
    difficulty_level: DifficultyLevel,
    order_index: int,
    banner_file_id: Optional[str] = None,
    video_file_id: Optional[str] = None,
    voice_file_id: Optional[str] = None,
    text_explanation: Optional[str] = None,
    practice_images: Optional[str] = None
) -> Course:
    course = Course(
        course_type_id=course_type_id,
        title=title,
        description=description,
        difficulty_level=difficulty_level,
        order_index=order_index,
        banner_file_id=banner_file_id,
        video_file_id=video_file_id,
        voice_file_id=voice_file_id,
        text_explanation=text_explanation,
        practice_images=practice_images,
        created_at=int(time.time())
    )
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course

async def get_course(db: AsyncSession, course_id: int) -> Optional[Course]:
    query = select(Course).filter(Course.id == course_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_courses_by_type_and_difficulty(
    db: AsyncSession,
    course_type_id: int,
    difficulty_level: Optional[DifficultyLevel] = None
) -> List[Course]:
    query = select(Course).filter(
        and_(
            Course.course_type_id == course_type_id,
            Course.is_active == True
        )
    )
    
    if difficulty_level:
        query = query.filter(Course.difficulty_level == difficulty_level)
    
    query = query.order_by(Course.order_index)
    result = await db.execute(query)
    return result.scalars().all()

async def update_course(
    db: AsyncSession,
    course_id: int,
    **kwargs
) -> Optional[Course]:
    course = await get_course(db, course_id)
    if not course:
        return None
    
    for key, value in kwargs.items():
        setattr(course, key, value)
    
    course.updated_at = int(time.time())
    await db.commit()
    await db.refresh(course)
    return course

async def delete_course(db: AsyncSession, course_id: int) -> bool:
    course = await get_course(db, course_id)
    if not course:
        return False
    
    await db.delete(course)
    await db.commit()
    return True 