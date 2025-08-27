"""
Feed recommendation logic for personalized content.
"""
from typing import Dict, List, Set, Tuple
from datetime import datetime, timedelta, timezone
from collections import Counter
from sqlalchemy.orm import Session
from sqlalchemy import select

from . import models


def _ensure_aware(dt: datetime) -> datetime:
    """Return a timezone-aware datetime in UTC.

    If dt is naive (tzinfo is None) assume UTC and attach timezone.utc.
    """
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def calculate_tag_weights(user_id: int, db: Session) -> Dict[str, float]:
    """
    Calculate tag weights based on user interactions (likes and comments).
    
    Args:
        user_id: The ID of the user
        db: Database session
        
    Returns:
        Dictionary mapping tag names to their weights for the user
    """
    # Get all posts liked by the user
    liked_posts = (
        db.query(models.Post)
        .join(models.Like)
        .filter(models.Like.user_id == user_id)
        .all()
    )
    
    # Get all posts commented on by the user
    commented_posts = (
        db.query(models.Post)
        .join(models.Comment)
        .filter(models.Comment.user_id == user_id)
        .all()
    )
    
    # Extract tags from liked posts (weight = 1.0)
    liked_tags = [tag.name for post in liked_posts for tag in post.tags]
    
    # Extract tags from commented posts (weight = 2.0)
    commented_tags = [tag.name for post in commented_posts for tag in post.tags]
    
    # Count tag occurrences with appropriate weights using float-friendly dict
    tag_weights: Dict[str, float] = {}
    for tag in liked_tags:
        tag_weights[tag] = tag_weights.get(tag, 0.0) + 1.0

    for tag in commented_tags:
        tag_weights[tag] = tag_weights.get(tag, 0.0) + 2.0

    # Normalize weights if there are any interactions
    total_weight = sum(tag_weights.values())
    if total_weight > 0:
        for tag in list(tag_weights.keys()):
            tag_weights[tag] = tag_weights[tag] / total_weight
    
    return dict(tag_weights)


def get_user_interactions(user_id: int, db: Session) -> Tuple[Set[int], Set[int]]:
    """
    Get sets of post IDs that the user has liked or commented on.
    
    Args:
        user_id: The ID of the user
        db: Database session
        
    Returns:
        Tuple of (liked_post_ids, commented_post_ids)
    """
    # Get all post IDs liked by the user
    # Use SQLAlchemy 2.0 style select + execute to get scalar results
    liked_post_ids = set(
        db.execute(
            select(models.Like.post_id).where(models.Like.user_id == user_id)
        ).scalars().all()
    )
    
    # Get all post IDs commented on by the user
    commented_post_ids = set(
        db.execute(
            select(models.Comment.post_id).where(models.Comment.user_id == user_id)
        ).scalars().all()
    )
    
    return liked_post_ids, commented_post_ids


def calculate_post_score(post, tag_weights: Dict[str, float], now: datetime) -> float:
    """
    Calculate a relevance score for a post based on user tag preferences and recency.
    
    Args:
        post: Post object
        tag_weights: Dictionary mapping tag names to their weights for the user
        now: Current datetime for recency calculation
        
    Returns:
        Relevance score for the post
    """
    # Base score from tag matching
    score = 0.0
    post_tags = [tag.name for tag in post.tags]
    
    # Calculate tag-based score
    for tag in post_tags:
        if tag in tag_weights:
            score += tag_weights[tag]
    
    # Apply recency boost (normalize datetimes to avoid naive/aware mismatch)
    now = _ensure_aware(now)
    post_created = _ensure_aware(post.created_at)
    days_old = (now - post_created).days
    decay_factor = 0.01  # 1% decay per day
    recency_multiplier = max(0.1, 1 - (decay_factor * days_old))
    
    # Combine base score with recency
    final_score = score * recency_multiplier
    
    return final_score
