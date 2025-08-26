"""
Unit tests for the business logic of the Humdov Post Feed API.
These tests verify that the core logic works independently of the API endpoints.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base, User, Post, Tag, Like, Comment
from app.recommendation import calculate_tag_weights, get_user_interactions, calculate_post_score


# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_data(db_session):
    """Create sample data for testing"""
    # Create users
    user1 = User(username="testuser1")
    user2 = User(username="testuser2")
    db_session.add_all([user1, user2])
    db_session.commit()
    
    # Create tags
    tech_tag = Tag(name="technology")
    sports_tag = Tag(name="sports")
    news_tag = Tag(name="news")
    db_session.add_all([tech_tag, sports_tag, news_tag])
    db_session.commit()
    
    # Create posts with staggered creation dates
    now = datetime.utcnow()
    
    post1 = Post(
        title="Tech Post", 
        content="About technology", 
        creator_id=user1.id,
        created_at=now - timedelta(days=10)
    )
    post1.tags.append(tech_tag)
    
    post2 = Post(
        title="Sports Post", 
        content="About sports", 
        creator_id=user1.id,
        created_at=now - timedelta(days=8)
    )
    post2.tags.append(sports_tag)
    
    post3 = Post(
        title="Tech and Sports", 
        content="Tech and sports combined", 
        creator_id=user2.id,
        created_at=now - timedelta(days=5)
    )
    post3.tags.append(tech_tag)
    post3.tags.append(sports_tag)
    
    post4 = Post(
        title="News Post", 
        content="Latest news", 
        creator_id=user2.id,
        created_at=now - timedelta(days=2)
    )
    post4.tags.append(news_tag)
    
    db_session.add_all([post1, post2, post3, post4])
    db_session.commit()
    
    # Return the created objects for reference
    return {
        "users": [user1, user2],
        "tags": [tech_tag, sports_tag, news_tag],
        "posts": [post1, post2, post3, post4]
    }


def test_like_creation(db_session, sample_data):
    """Test creating a like and ensuring it's added to the database"""
    user = sample_data["users"][0]
    post = sample_data["posts"][2]  # Tech and Sports post
    
    # Create a like
    like = Like(user_id=user.id, post_id=post.id)
    db_session.add(like)
    db_session.commit()
    
    # Check that the like exists in the database
    db_like = db_session.query(Like).filter(
        Like.user_id == user.id,
        Like.post_id == post.id
    ).first()
    
    assert db_like is not None
    assert db_like.user_id == user.id
    assert db_like.post_id == post.id


def test_like_uniqueness(db_session, sample_data):
    """Test that a user cannot like the same post twice"""
    user = sample_data["users"][0]
    post = sample_data["posts"][2]  # Tech and Sports post
    
    # Create the first like
    like1 = Like(user_id=user.id, post_id=post.id)
    db_session.add(like1)
    db_session.commit()
    
    # Try to create a second like (should fail due to unique constraint)
    like2 = Like(user_id=user.id, post_id=post.id)
    db_session.add(like2)
    
    with pytest.raises(Exception):
        db_session.commit()
    
    # Rollback to clean up
    db_session.rollback()


def test_comment_creation(db_session, sample_data):
    """Test creating a comment and ensuring it's added to the database"""
    user = sample_data["users"][1]
    post = sample_data["posts"][0]  # Tech post
    
    # Create a comment
    comment = Comment(
        user_id=user.id,
        post_id=post.id,
        content="Great tech post!",
        timestamp=datetime.utcnow()
    )
    db_session.add(comment)
    db_session.commit()
    
    # Check that the comment exists in the database
    db_comment = db_session.query(Comment).filter(
        Comment.user_id == user.id,
        Comment.post_id == post.id
    ).first()
    
    assert db_comment is not None
    assert db_comment.user_id == user.id
    assert db_comment.post_id == post.id
    assert db_comment.content == "Great tech post!"


def test_tag_weight_calculation(db_session, sample_data):
    """Test calculating tag weights based on user interactions"""
    user = sample_data["users"][0]
    
    # Create likes and comments for the user to build a profile
    like1 = Like(user_id=user.id, post_id=sample_data["posts"][0].id)  # Tech post
    like2 = Like(user_id=user.id, post_id=sample_data["posts"][2].id)  # Tech and Sports post
    comment = Comment(
        user_id=user.id,
        post_id=sample_data["posts"][3].id,  # News post
        content="Nice news!",
        timestamp=datetime.utcnow()
    )
    
    db_session.add_all([like1, like2, comment])
    db_session.commit()
    
    # Calculate tag weights
    tag_weights = calculate_tag_weights(user.id, db_session)
    
    # Check that the weights reflect the interactions
    # Like weights should be higher than comment weights
    assert 'technology' in tag_weights
    assert 'sports' in tag_weights
    assert 'news' in tag_weights
    
    # Technology should have the highest weight (appears in two liked posts)
    assert tag_weights['technology'] > tag_weights['sports']
    assert tag_weights['technology'] > tag_weights['news']
    
    # News should have the lowest weight (only from a comment)
    assert tag_weights['news'] < tag_weights['sports']


def test_post_score_calculation():
    """Test calculating post scores based on tag weights and recency"""
    # Create mock posts with different tags and creation dates
    now = datetime.utcnow()
    
    class MockTag:
        def __init__(self, name):
            self.name = name
    
    class MockPost:
        def __init__(self, tags, created_at):
            self.tags = tags
            self.created_at = created_at
    
    # Create posts with different tag combinations and dates
    tech_post_old = MockPost([MockTag("technology")], now - timedelta(days=30))
    tech_post_new = MockPost([MockTag("technology")], now - timedelta(days=1))
    sports_post = MockPost([MockTag("sports")], now - timedelta(days=5))
    mixed_post = MockPost([MockTag("technology"), MockTag("sports")], now - timedelta(days=10))
    
    # Define tag weights (technology > sports > news)
    tag_weights = {"technology": 0.6, "sports": 0.3, "news": 0.1}
    
    # Calculate scores
    tech_post_old_score = calculate_post_score(tech_post_old, tag_weights, now)
    tech_post_new_score = calculate_post_score(tech_post_new, tag_weights, now)
    sports_post_score = calculate_post_score(sports_post, tag_weights, now)
    mixed_post_score = calculate_post_score(mixed_post, tag_weights, now)
    
    # Verify score ordering
    # New tech post should score higher than old tech post due to recency
    assert tech_post_new_score > tech_post_old_score
    
    # Mixed post should score higher than sports post due to tag weights
    assert mixed_post_score > sports_post_score
    
    # Check if recency impacts scores
    # Even though tech has higher weight, a very old tech post might score lower than a newer sports post
    newer_sports_post = MockPost([MockTag("sports")], now - timedelta(hours=1))
    newer_sports_post_score = calculate_post_score(newer_sports_post, tag_weights, now)
    
    assert newer_sports_post_score > tech_post_old_score


def test_feed_ranking_logic(db_session, sample_data):
    """Test the complete feed ranking logic with mock data"""
    user = sample_data["users"][0]
    
    # Create likes to establish tag preferences
    like1 = Like(user_id=user.id, post_id=sample_data["posts"][0].id)  # Tech post
    db_session.add(like1)
    db_session.commit()
    
    # Get user's tag weights
    tag_weights = calculate_tag_weights(user.id, db_session)
    
    # Get interactions to exclude from feed
    liked_post_ids, commented_post_ids = get_user_interactions(user.id, db_session)
    
    # Get candidate posts excluding interactions
    candidate_posts = db_session.query(Post).filter(
        Post.id.notin_(list(liked_post_ids))
    ).all()
    
    # Calculate scores
    now = datetime.utcnow()
    scored_posts = []
    
    for post in candidate_posts:
        score = calculate_post_score(post, tag_weights, now)
        scored_posts.append({
            "id": post.id,
            "title": post.title,
            "score": score,
            "created_at": post.created_at,
            "tags": [tag.name for tag in post.tags]
        })
    
    # Sort posts by score (descending) and then by creation date
    scored_posts.sort(key=lambda p: (p["score"], p["created_at"]), reverse=True)
    
    # Tech posts should be ranked higher due to user preference
    for i in range(len(scored_posts) - 1):
        if "technology" in scored_posts[i]["tags"] and "technology" not in scored_posts[i+1]["tags"]:
            assert scored_posts[i]["score"] >= scored_posts[i+1]["score"]
    
    # Verify post with both tech and sports is ranked highest (if it exists)
    for post in scored_posts:
        if "technology" in post["tags"] and "sports" in post["tags"]:
            # This should be the post with ID 3 (Tech and Sports)
            assert post["id"] == sample_data["posts"][2].id
            # It should be the first post in the list
            assert scored_posts[0]["id"] == post["id"]
            break
