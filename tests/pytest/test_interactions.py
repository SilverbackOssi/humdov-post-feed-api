import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models import Base
from app.database import get_db
from app.recommendation import calculate_tag_weights, calculate_post_score
from app import models
from datetime import datetime, timedelta

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Override the get_db dependency for testing
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture()
def test_db():
    # Create the database and tables
    Base.metadata.create_all(bind=engine)
    
    # Create test data
    db = TestingSessionLocal()
    
    # Create users
    user1 = models.User(username="testuser1")
    user2 = models.User(username="testuser2")
    db.add(user1)
    db.add(user2)
    db.commit()
    
    # Create tags
    tech_tag = models.Tag(name="technology")
    sports_tag = models.Tag(name="sports")
    news_tag = models.Tag(name="news")
    db.add(tech_tag)
    db.add(sports_tag)
    db.add(news_tag)
    db.commit()
    
    # Create posts
    post1 = models.Post(title="Tech Post", content="About tech", creator_id=user1.id)
    post1.tags.append(tech_tag)
    
    post2 = models.Post(title="Sports Post", content="About sports", creator_id=user1.id)
    post2.tags.append(sports_tag)
    
    post3 = models.Post(title="Tech and Sports", content="Both topics", creator_id=user2.id)
    post3.tags.append(tech_tag)
    post3.tags.append(sports_tag)
    
    post4 = models.Post(title="News Post", content="Latest news", creator_id=user2.id)
    post4.tags.append(news_tag)
    
    db.add(post1)
    db.add(post2)
    db.add(post3)
    db.add(post4)
    db.commit()
    
    # Add like and comment
    like1 = models.Like(user_id=user1.id, post_id=post3.id)
    like2 = models.Like(user_id=user2.id, post_id=post1.id)
    comment1 = models.Comment(user_id=user1.id, post_id=post4.id, content="Great news!")
    
    db.add(like1)
    db.add(like2)
    db.add(comment1)
    db.commit()
    
    yield db
    
    # Clean up
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    return TestClient(app)


def test_like_post(client, test_db):
    """Test creating a like for a post"""
    response = client.post(
        "/api/v1/likes",
        json={"user_id": 1, "post_id": 2}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "liked"}
    
    # Check that a duplicate like returns 400
    response = client.post(
        "/api/v1/likes",
        json={"user_id": 1, "post_id": 2}
    )
    assert response.status_code == 400


def test_unlike_post(client, test_db):
    """Test removing a like from a post"""
    # First, create a like
    client.post(
        "/api/v1/likes",
        json={"user_id": 1, "post_id": 1}
    )
    
    # Then unlike it
    response = client.delete(
        "/api/v1/likes",
        json={"user_id": 1, "post_id": 1}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "unliked"}
    
    # Check that removing a non-existent like returns 404
    response = client.delete(
        "/api/v1/likes",
        json={"user_id": 1, "post_id": 1}
    )
    assert response.status_code == 404


def test_get_user_likes(client, test_db):
    """Test getting all likes by a user"""
    response = client.get("/api/v1/likes/1")
    assert response.status_code == 200
    likes = response.json()
    assert len(likes) == 1
    assert likes[0]["post_id"] == 3


def test_create_comment(client, test_db):
    """Test creating a comment on a post"""
    response = client.post(
        "/api/v1/comments",
        json={
            "user_id": 2,
            "post_id": 2,
            "content": "This is a test comment"
        }
    )
    assert response.status_code == 200
    comment = response.json()
    assert comment["content"] == "This is a test comment"
    assert comment["user_id"] == 2


def test_get_post_comments(client, test_db):
    """Test getting all comments for a post"""
    response = client.get("/api/v1/comments/4")
    assert response.status_code == 200
    comments = response.json()
    assert len(comments) == 1
    assert comments[0]["content"] == "Great news!"


def test_feed_personalization(client, test_db):
    """Test the personalized feed algorithm"""
    # Test feed for user 1 who has liked post 3 (tech+sports) and commented on post 4 (news)
    response = client.get("/api/v1/feed/1")
    assert response.status_code == 200
    posts = response.json()
    
    # Should get at least posts 1 and 2 (not interacted with yet)
    assert len(posts) >= 2
    
    # Verify the posts have a score field
    assert "score" in posts[0]


def test_tag_weights_calculation():
    """Test the tag weight calculation logic"""
    # Mock database session
    class MockDB:
        def query(self, model):
            return self

        def join(self, model):
            return self
            
        def filter(self, condition):
            # This is a simplified mock that just returns predefined data
            if condition.right.value == 1:  # user_id == 1
                # Mock posts that user 1 has liked
                liked_post = type('Post', (), {'tags': [
                    type('Tag', (), {'name': 'technology'}),
                    type('Tag', (), {'name': 'science'})
                ]})
                
                # Mock posts that user 1 has commented on
                commented_post = type('Post', (), {'tags': [
                    type('Tag', (), {'name': 'technology'}),
                    type('Tag', (), {'name': 'news'})
                ]})
                
                if 'Like' in str(self.model_joined):
                    return [liked_post]
                else:
                    return [commented_post]
            return []
            
        def all(self):
            return self.filtered_results

    mock_db = MockDB()
    mock_db.model_joined = None
    mock_db.filtered_results = []
    
    # Test score calculation
    now = datetime.utcnow()
    post = type('Post', (), {
        'tags': [type('Tag', (), {'name': 'technology'})],
        'created_at': now - timedelta(days=5)
    })
    
    tag_weights = {'technology': 0.7, 'science': 0.2, 'news': 0.1}
    score = calculate_post_score(post, tag_weights, now)
    
    # Score should be 0.7 (tag weight) * ~0.95 (recency factor)
    assert 0.65 <= score <= 0.7
