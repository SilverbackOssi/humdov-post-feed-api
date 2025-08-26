from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table, UniqueConstraint
from sqlalchemy.orm import relationship

from .database import Base

# Association table for Post-Tag many-to-many relationship
PostTag = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("posts.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True)
)


class User(Base):
    """User model representing application users"""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    
    # Relationships
    likes = relationship("Like", back_populates="user")
    comments = relationship("Comment", back_populates="user")


class Post(Base):
    """Post model representing user posts"""
    
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    content = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    creator = relationship("User", backref="posts")
    tags = relationship("Tag", secondary=PostTag, back_populates="posts")
    likes = relationship("Like", back_populates="post")
    comments = relationship("Comment", back_populates="post")


class Tag(Base):
    """Tag model representing post categories/tags"""
    
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    
    # Relationships
    posts = relationship("Post", secondary=PostTag, back_populates="tags")


class Like(Base):
    """Like model representing user likes on posts"""
    
    __tablename__ = "likes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    post_id = Column(Integer, ForeignKey("posts.id"))
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="likes")
    post = relationship("Post", back_populates="likes")
    
    # Composite unique constraint to prevent duplicate likes
    __table_args__ = (UniqueConstraint("user_id", "post_id"),)


class Comment(Base):
    """Comment model representing user comments on posts"""
    
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    post_id = Column(Integer, ForeignKey("posts.id"))
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")
