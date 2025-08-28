from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class UserBase(BaseModel):
    """Base schema for user data"""
    username: str


class UserCreate(UserBase):
    """Schema for user creation requests"""
    pass


class UserResponse(UserBase):
    """Schema for user responses"""
    id: int
    created_at: Optional[datetime] = None  # User join date

    class Config:
        from_attributes = True


class TagBase(BaseModel):
    """Base schema for tag data"""
    name: str


class TagResponse(TagBase):
    """Schema for tag responses"""
    id: int

    class Config:
        from_attributes = True


class PostBase(BaseModel):
    """Base schema for post data"""
    title: str
    content: Optional[str] = None


class PostCreate(PostBase):
    """Schema for post creation requests"""
    tags: List[str] = []
    creator_id: int


class PostResponse(PostBase):
    """Schema for post responses"""
    id: int
    created_at: datetime
    creator_id: int
    tags: List[str] = []

    class Config:
        from_attributes = True


class LikeBase(BaseModel):
    """Base schema for like data"""
    user_id: int
    post_id: int


class LikeCreate(LikeBase):
    """Schema for like creation requests"""
    pass


class LikeDelete(LikeBase):
    """Schema for like deletion requests"""
    pass


class LikeResponse(BaseModel):
    """Schema for like responses"""
    post_id: int
    timestamp: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Schema for message responses"""
    message: str


class CommentBase(BaseModel):
    """Base schema for comment data"""
    content: str


class CommentCreate(CommentBase):
    """Schema for comment creation requests"""
    user_id: int
    post_id: int


class CommentResponse(BaseModel):
    """Schema for comment responses"""
    id: int
    user_id: int
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True


class FeedPostResponse(PostResponse):
    """Schema for feed post responses with personalization score"""
    score: float


class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str = "healthy"
