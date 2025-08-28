from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime,timezone, timedelta
from collections import Counter

from . import models, schemas
from .database import get_db
from .recommendation import calculate_tag_weights, get_user_interactions, calculate_post_score


# Different routers for different resources to allow better developer experience
users_router = APIRouter(prefix="/api/v1", tags=["Users"])
posts_router = APIRouter(prefix="/api/v1", tags=["Posts"])
interactions_router = APIRouter(prefix="/api/v1", tags=["Interactions"])
feed_router = APIRouter(prefix="/api/v1", tags=["Feed"])


@users_router.post("/users", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    # Check if user with the same username already exists
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Create new user
    new_user = models.User(username=user.username)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@users_router.get("/users/{user_id}", response_model=schemas.UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """Get a user by ID"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@posts_router.post("/posts", response_model=schemas.PostResponse)
def create_post(post: schemas.PostCreate, db: Session = Depends(get_db)):
    """Create a new post with optional tags"""
    # Verify the creator exists
    creator = db.query(models.User).filter(models.User.id == post.creator_id).first()
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found")
    
    # Create new post
    new_post = models.Post(
        title=post.title,
        content=post.content,
        creator_id=post.creator_id
    )
    
    # Process tags
    for tag_name in post.tags:
        # Check if tag exists, create if not
        db_tag = db.query(models.Tag).filter(models.Tag.name == tag_name).first()
        if not db_tag:
            db_tag = models.Tag(name=tag_name)
            db.add(db_tag)
            db.flush()
        
        # Add tag to post
        new_post.tags.append(db_tag)
    
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    
    # Convert response to match expected schema
    return {
        "id": new_post.id,
        "title": new_post.title,
        "content": new_post.content,
        "created_at": new_post.created_at,
        "creator_id": new_post.creator_id,
        "tags": [tag.name for tag in new_post.tags]
    }


@posts_router.get("/posts/{post_id}", response_model=schemas.PostResponse)
def read_post(post_id: int, db: Session = Depends(get_db)):
    """Get a post by ID"""
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Convert response to match expected schema
    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "created_at": post.created_at,
        "creator_id": post.creator_id,
        "tags": [tag.name for tag in post.tags]
    }


# Like endpoints
@interactions_router.post("/likes", response_model=schemas.MessageResponse)
def create_like(like: schemas.LikeCreate, db: Session = Depends(get_db)):
    """Create a like for a post by a user"""
    # Check if user exists
    user = db.query(models.User).filter(models.User.id == like.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if post exists
    post = db.query(models.Post).filter(models.Post.id == like.post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check if like already exists
    existing_like = db.query(models.Like).filter(
        models.Like.user_id == like.user_id,
        models.Like.post_id == like.post_id
    ).first()
    
    if existing_like:
        raise HTTPException(status_code=400, detail="User has already liked this post")
    
    # Create like
    new_like = models.Like(user_id=like.user_id, post_id=like.post_id)
    db.add(new_like)
    db.commit()
    
    return {"message": "liked"}


@interactions_router.delete("/likes", response_model=schemas.MessageResponse)
def delete_like(like: schemas.LikeDelete, db: Session = Depends(get_db)):
    """Remove a like from a post by a user"""
    # Find the like
    db_like = db.query(models.Like).filter(
        models.Like.user_id == like.user_id,
        models.Like.post_id == like.post_id
    ).first()
    
    if not db_like:
        raise HTTPException(status_code=404, detail="Like not found")
    
    # Delete the like
    db.delete(db_like)
    db.commit()
    
    return {"message": "unliked"}


@interactions_router.get("/likes/{user_id}", response_model=List[schemas.LikeResponse])
def get_user_likes(user_id: int, db: Session = Depends(get_db)):
    """Get all posts liked by a user"""
    # Check if user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get all likes by the user
    likes = db.query(models.Like).filter(models.Like.user_id == user_id).all()
    
    return likes


# Comment endpoints
@interactions_router.post("/comments", response_model=schemas.CommentResponse)
def create_comment(comment: schemas.CommentCreate, db: Session = Depends(get_db)):
    """Create a comment on a post by a user"""
    # Check if user exists
    user = db.query(models.User).filter(models.User.id == comment.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if post exists
    post = db.query(models.Post).filter(models.Post.id == comment.post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Create comment
    new_comment = models.Comment(
        user_id=comment.user_id,
        post_id=comment.post_id,
        content=comment.content
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    return new_comment


@interactions_router.get("/comments/{post_id}", response_model=List[schemas.CommentResponse])
def get_post_comments(post_id: int, db: Session = Depends(get_db)):
    """Get all comments for a post"""
    # Check if post exists
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Get all comments for the post
    comments = db.query(models.Comment).filter(models.Comment.post_id == post_id).all()
    
    return comments


# User top tags endpoint
@users_router.get("/users/{user_id}/top_tags", response_model=List[str])
def get_user_top_tags(user_id: int, limit: int = 5, db: Session = Depends(get_db)):
    """Get the top tags for a user based on their posts, likes, and comments"""
    # Check if user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get all tags from posts the user has created
    user_posts = db.query(models.Post).filter(models.Post.creator_id == user_id).all()
    post_tags = [tag.name for post in user_posts for tag in post.tags]
    
    # Get all tags from posts the user has liked
    liked_posts = (
        db.query(models.Post)
        .join(models.Like)
        .filter(models.Like.user_id == user_id)
        .all()
    )
    liked_tags = [tag.name for post in liked_posts for tag in post.tags]
    
    # Get all tags from posts the user has commented on
    commented_posts = (
        db.query(models.Post)
        .join(models.Comment)
        .filter(models.Comment.user_id == user_id)
        .all()
    )
    commented_tags = [tag.name for post in commented_posts for tag in post.tags]
    
    # Count occurrences of each tag
    tag_counts = Counter()
    
    # Posts created by the user (weight: 3)
    for tag in post_tags:
        tag_counts[tag] += 3
    
    # Posts liked by the user (weight: 2)
    for tag in liked_tags:
        tag_counts[tag] += 2
    
    # Posts commented by the user (weight: 1)
    for tag in commented_tags:
        tag_counts[tag] += 1
    
    # Return the top tags by frequency
    top_tags = [tag for tag, _ in tag_counts.most_common(limit)] if tag_counts else []
    return top_tags


# User comments endpoint
@users_router.get("/users/{user_id}/comments", response_model=List[dict])
def get_user_comments(user_id: int, limit: int = 10, db: Session = Depends(get_db)):
    """Get comments made by a user"""
    # Check if user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get the user's comments with associated post details
    comments = (
        db.query(models.Comment, models.Post.title.label("post_title"))
        .join(models.Post, models.Comment.post_id == models.Post.id)
        .filter(models.Comment.user_id == user_id)
        .order_by(desc(models.Comment.timestamp))
        .limit(limit)
        .all()
    )
    
    # Format the results
    results = []
    for comment, post_title in comments:
        results.append({
            "id": comment.id,
            "content": comment.content,
            "post_id": comment.post_id,
            "post_title": post_title,
            "timestamp": comment.timestamp
        })
    
    return results


# User detailed posts endpoint
@users_router.get("/users/{user_id}/detailed_posts", response_model=List[dict])
def get_user_detailed_posts(user_id: int, limit: int = 10, db: Session = Depends(get_db)):
    """Get detailed posts created by a user, including comment and like counts"""
    # Check if user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's posts with comment and like counts
    posts = (
        db.query(
            models.Post,
            func.count(models.Like.id).label("like_count"),
            func.count(models.Comment.id).label("comment_count")
        )
        .outerjoin(models.Like, models.Post.id == models.Like.post_id)
        .outerjoin(models.Comment, models.Post.id == models.Comment.post_id)
        .filter(models.Post.creator_id == user_id)
        .group_by(models.Post.id)
        .order_by(desc(models.Post.created_at))
        .limit(limit)
        .all()
    )
    
    # Format the results
    results = []
    for post, like_count, comment_count in posts:
        results.append({
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "created_at": post.created_at,
            "tags": [tag.name for tag in post.tags],
            "like_count": like_count,
            "comment_count": comment_count
        })
    
    return results


# Enhanced user profile endpoint
@users_router.get("/users/{user_id}/profile", response_model=dict)
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    """Get comprehensive profile data for a user"""
    # Check if user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get post count
    post_count = db.query(func.count(models.Post.id)).filter(
        models.Post.creator_id == user_id
    ).scalar()
    
    # Get like count (posts user has liked)
    like_count = db.query(func.count(models.Like.id)).filter(
        models.Like.user_id == user_id
    ).scalar()
    
    # Get comment count
    comment_count = db.query(func.count(models.Comment.id)).filter(
        models.Comment.user_id == user_id
    ).scalar()
    
    # Get likes received count (likes on user's posts)
    likes_received = db.query(func.count(models.Like.id)).join(
        models.Post, models.Like.post_id == models.Post.id
    ).filter(models.Post.creator_id == user_id).scalar()
    
    # Get top tags (reusing logic from top_tags endpoint but with a smaller limit)
    user_posts = db.query(models.Post).filter(models.Post.creator_id == user_id).all()
    post_tags = [tag.name for post in user_posts for tag in post.tags]
    
    liked_posts = (
        db.query(models.Post)
        .join(models.Like)
        .filter(models.Like.user_id == user_id)
        .all()
    )
    liked_tags = [tag.name for post in liked_posts for tag in post.tags]
    
    tag_counts = Counter()
    for tag in post_tags:
        tag_counts[tag] += 3  # Higher weight for own posts
    for tag in liked_tags:
        tag_counts[tag] += 2  # Lower weight for liked posts
    
    # Handle empty tag counts (if user has no posts or likes)
    top_tags = [tag for tag, _ in tag_counts.most_common(3)] if tag_counts else []
    
    # Build and return the profile
    return {
        "id": user.id,
        "username": user.username,
        "created_at": user.created_at,
        "stats": {
            "post_count": post_count,
            "like_count": like_count,
            "comment_count": comment_count,
            "likes_received": likes_received
        },
        "top_tags": top_tags
    }


# Feed endpoint
@feed_router.get("/feed/{user_id}", response_model=List[schemas.FeedPostResponse])
def get_personalized_feed(user_id: int, limit: int = 20, db: Session = Depends(get_db)):
    """
    Get a personalized feed for a user based on their interactions
    
    The feed algorithm uses content-based filtering:
    1. Build a user profile based on tags from liked and commented posts
    2. Score candidate posts based on tag matching and recency
    3. Sort by score and return the top results
    """

    # Check if user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's tag preferences
    tag_weights = calculate_tag_weights(user_id, db)
    
    # Get posts the user has already interacted with
    liked_post_ids, commented_post_ids = get_user_interactions(user_id, db)
    excluded_post_ids = liked_post_ids.union(commented_post_ids)
    
    # Get all candidate posts that the user hasn't interacted with
    query = db.query(models.Post)
    if excluded_post_ids:
        query = query.filter(models.Post.id.notin_(excluded_post_ids))
    
    # Limit to a reasonable number of candidates for scoring
    candidate_posts = query.order_by(desc(models.Post.created_at)).limit(100).all()
    
    # Calculate score for each candidate post
    now = datetime.now(timezone.utc)
    scored_posts = []
    
    if tag_weights:  # User has interactions, use personalized scoring
        for post in candidate_posts:
            score = calculate_post_score(post, tag_weights, now)
            scored_posts.append({
                "id": post.id,
                "title": post.title,
                "content": post.content,
                "created_at": post.created_at,
                "creator_id": post.creator_id,
                "tags": [tag.name for tag in post.tags],
                "score": score
            })
        
        # Sort by score (descending) and then by creation date (descending)
        scored_posts.sort(key=lambda p: (p["score"], p["created_at"]), reverse=True)
    else:
        # Fallback for users with no interactions: sort by recency
        for post in candidate_posts:
            scored_posts.append({
                "id": post.id,
                "title": post.title,
                "content": post.content,
                "created_at": post.created_at,
                "creator_id": post.creator_id,
                "tags": [tag.name for tag in post.tags],
                "score": 0.0  # No personalization score for new users
            })
        
        # Sort by creation date (descending)
        scored_posts.sort(key=lambda p: p["created_at"], reverse=True)
    
    # Return limited number of posts
    return scored_posts[:limit]
