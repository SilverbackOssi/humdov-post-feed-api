"""
Feed recommendation logic for personalized content.
"""
from typing import Dict, List, Set, Tuple
from datetime import datetime, timedelta
from collections import Counter
from sqlalchemy.orm import Session

from . import models


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
    
    # Extract tags from commented posts (weight = 0.5)
    commented_tags = [tag.name for post in commented_posts for tag in post.tags]
    
    # Count tag occurrences with appropriate weights
    tag_weights = Counter()
    for tag in liked_tags:
        tag_weights[tag] += 1.0
    
    for tag in commented_tags:
        tag_weights[tag] += 2.0

    # Normalize weights if there are any interactions
    total_weight = sum(tag_weights.values())
    if total_weight > 0:
        for tag in tag_weights:
            tag_weights[tag] /= total_weight
    
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
    liked_post_ids = set(
        db.query(models.Like.post_id)
        .filter(models.Like.user_id == user_id)
        .scalar_all()
    )
    
    # Get all post IDs commented on by the user
    commented_post_ids = set(
        db.query(models.Comment.post_id)
        .filter(models.Comment.user_id == user_id)
        .scalar_all()
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
    
    # Apply recency boost
    days_old = (now - post.created_at).days
    decay_factor = 0.01  # 1% decay per day
    recency_multiplier = max(0.1, 1 - (decay_factor * days_old))
    
    # Combine base score with recency
    final_score = score * recency_multiplier
    
    return final_score
