from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, BigInteger, Enum # type: ignore
from sqlalchemy.orm import relationship # type: ignore
from database.db import Base
import enum


class DifficultyLevel(enum.Enum):
    BEGINNER = "beginner"      # Courses 1-10
    INTERMEDIATE = "intermediate"  # Courses 11-20
    ADVANCED = "advanced"      # Courses 21-30
    EXPERT = "expert"         # Courses 31-40


class CourseType(Base):
    __tablename__ = "course_types"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)  # e.g., "Basic Russian Course"
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(BigInteger, nullable=False)  # Unix timestamp
    
    # Relationship with courses
    courses = relationship("Course", back_populates="course_type", cascade="all, delete-orphan")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Add course type relationship
    course_type_id = Column(Integer, ForeignKey('course_types.id', ondelete='CASCADE'), nullable=False)
    course_type = relationship("CourseType", back_populates="courses")
    
    # Basic information
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Course level and ordering
    difficulty_level = Column(Enum(DifficultyLevel), nullable=False, default=DifficultyLevel.BEGINNER)
    order_index = Column(Integer, nullable=False)  # For ordering courses within their difficulty level
    
    # Media content
    banner_file_id = Column(String(255), nullable=True)  # Telegram file_id for banner image
    video_file_id = Column(String(255), nullable=True)   # Telegram file_id for video content
    voice_file_id = Column(String(255), nullable=True)   # Telegram file_id for voice explanation
    
    # Practice images
    practice_images = Column(Text, nullable=True)  # Store as JSON string of file_ids
    
    # Text content
    text_explanation = Column(Text, nullable=True)
    
    # Poll information (for future implementation)
    has_poll = Column(Boolean, default=False)
    poll_question = Column(Text, nullable=True)
    poll_options = Column(Text, nullable=True)  # Store as JSON string
    
    # Course status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(BigInteger, nullable=False)  # Unix timestamp
    updated_at = Column(BigInteger, nullable=True)   # Unix timestamp
