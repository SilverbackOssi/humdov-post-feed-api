"""
Unit tests for the frontend functionality of the Humdov Post Feed API.
These tests verify template rendering and frontend logic.
"""
import pytest
from fastapi.testclient import TestClient
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models import Base, User, Post, Tag
from app.database import get_db

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


@pytest.fixture
def client():
    return TestClient(app)


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
def sample_user(db_session):
    """Create a sample user for testing"""
    user = User(username="testuser")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_post(db_session, sample_user):
    """Create a sample post for testing"""
    # Create a tag
    tag = Tag(name="technology")
    db_session.add(tag)
    db_session.commit()
    
    # Create a post
    post = Post(
        title="Test Post",
        content="This is a test post",
        creator_id=sample_user.id
    )
    post.tags.append(tag)
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)
    return post


def test_home_page_renders(client, sample_user):
    """Test that the home page renders successfully"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Humdov Post Feed" in response.text
    assert "Home" in response.text


def test_profile_page_renders(client, sample_user):
    """Test that the profile page renders successfully"""
    response = client.get(f"/profile/{sample_user.id}")
    assert response.status_code == 200
    assert "Profile" in response.text
    assert sample_user.username in response.text


def test_profile_page_not_found(client):
    """Test that accessing a non-existent user profile returns 404"""
    response = client.get("/profile/9999")
    assert response.status_code == 404


def test_new_post_page_renders(client, sample_user):
    """Test that the new post page renders successfully"""
    response = client.get("/new_post")
    assert response.status_code == 200
    assert "Create New Post" in response.text
    assert "Title" in response.text
    assert "Content" in response.text
    assert "Tags" in response.text


def test_get_all_users_endpoint(client, sample_user):
    """Test the users endpoint for the frontend user selector"""
    response = client.get("/api/v1/users")
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 1
    assert any(user["username"] == sample_user.username for user in users)


def test_static_files_accessible(client):
    """Test that static files can be accessed"""
    # Test CSS file
    response = client.get("/static/css/style.css")
    assert response.status_code == 200
    assert "text/css" in response.headers.get("content-type", "")
    
    # Test JavaScript file
    response = client.get("/static/js/script.js")
    assert response.status_code == 200
    assert "application/javascript" in response.headers.get("content-type", "") or \
           "text/javascript" in response.headers.get("content-type", "")


def test_template_context_variables():
    """Test that templates can access the required context variables"""
    templates = Jinja2Templates(directory="app/frontend/templates")
    
    # Test base template variables
    from fastapi import Request
    
    class MockRequest:
        def __init__(self):
            self.url = type('obj', (object,), {'path': '/'})
    
    mock_request = MockRequest()
    
    # This test ensures that our template structure is correct
    # The actual rendering with context variables is tested in integration tests
    assert templates.get_template("base.html") is not None
    assert templates.get_template("index.html") is not None
    assert templates.get_template("profile.html") is not None
    assert templates.get_template("new_post.html") is not None


def test_template_inheritance():
    """Test that templates properly extend the base template"""
    templates = Jinja2Templates(directory="app/frontend/templates")
    
    # Read template files to check for inheritance
    with open("app/frontend/templates/index.html", "r") as f:
        index_content = f.read()
        assert 'extends "base.html"' in index_content
        assert '{% block content %}' in index_content
    
    with open("app/frontend/templates/profile.html", "r") as f:
        profile_content = f.read()
        assert 'extends "base.html"' in profile_content
        assert '{% block content %}' in profile_content
    
    with open("app/frontend/templates/new_post.html", "r") as f:
        new_post_content = f.read()
        assert 'extends "base.html"' in new_post_content
        assert '{% block content %}' in new_post_content


def test_css_variables_defined():
    """Test that the required CSS variables are defined"""
    with open("app/frontend/static/css/style.css", "r") as f:
        css_content = f.read()
        # Check for the required color variables
        assert "--primary-blue: #006CFF" in css_content
        assert "--background-gray" in css_content
        assert "--light-gray: #D3D3D3" in css_content


def test_javascript_class_defined():
    """Test that the PostFeedApp class is properly defined in JavaScript"""
    with open("app/frontend/static/js/script.js", "r") as f:
        js_content = f.read()
        assert "class PostFeedApp" in js_content
        assert "loadFeed()" in js_content
        assert "handleLike(" in js_content
        assert "handleCommentSubmit(" in js_content
