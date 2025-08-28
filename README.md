# Humdov Post Feed API

A simple backend service using FastAPI that stores users and posts, records user-post interactions (likes and comments), and exposes a personalized feed endpoint.

## Project Structure

- `/app`: FastAPI application code
- `/tests/requests`: Request-based tests (requires running server)
- `/tests/pytest`: Pytest-based unit tests
- `/migrations`: Placeholder for future database migrations

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/MacOS
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and adjust settings if needed

## Running the Server

```
uvicorn app.main:app --reload
or
fastapi run app\main.py
```

The API will be available at `http://localhost:8000`.

API documentation (Swagger UI) will be available at `http://localhost:8000/docs`.

## Postman Collection

A Postman collection is available for testing the API endpoints. You can access it here:

- **Postman Documentation**: [Humdov Post Feed API Collection](https://documenter.getpostman.com/view/43614350/2sB3HgP3CE)

This collection includes pre-configured requests for all available endpoints, making it easy to explore and test the API functionality.

## Hosted API

A live version of the API is hosted on Render for demonstration purposes:

- **Base URL**: https://humdov-post-feed-api.onrender.com
- **API Documentation**: https://humdov-post-feed-api.onrender.com/docs
- **Frontend Interface**: https://humdov-post-feed-api.onrender.com

Note: The hosted version uses the same endpoints as the local version but may have limitations due to the free tier hosting (e.g., potential cold starts, limited concurrent connections).

## Frontend Interface

The project includes a complete frontend interface that provides an intuitive demonstration of the post feed functionality. After starting the server, you can access the frontend at:

**http://localhost:8000**

### Frontend Features

- **Modern Design**: Clean, modern UI with blue (#006CFF) accents and gray backgrounds/text inspired by Humdov landing page
- **User Selection**: Switch between different users to see personalized feeds
- **Interactive Feed**: View posts with like/comment counts and interactions
- **Create Posts**: Add new posts with tags through a user-friendly form
- **User Profiles**: View individual user profiles and their posts
- **Responsive Design**: Mobile-friendly layout that adapts to different screen sizes

### Frontend Structure

The frontend is built with:
- **Templates**: Jinja2 templates with inheritance for consistent layout
- **Static Assets**: CSS and JavaScript files served from `/static/`
- **API Integration**: Frontend communicates with the backend API endpoints
- **Real-time Updates**: Dynamic content loading and user interactions

Note: The frontend uses a bundled approach with all assets served from the FastAPI application, making it easy to demonstrate the complete functionality without separate deployment.

## Seed Data

To populate the database with sample data for testing and demonstration:

```
python app/seed_data.py
```

This will create:
- 20 users with unique usernames
- 100 posts with random titles, content, and tags
- 200-300 likes with appropriate user-post relationships
- 100-150 comments with realistic content

The seed data is designed to demonstrate the personalization algorithm by creating realistic user preferences and post interactions.

Note: The app DB comes prepopulated, so you can go ahead with testing

## Running Tests

### Unit Tests (Pytest)
```
pytest tests/pytest
```

### Integration Tests (Requires running server)
```
# Start the server first
uvicorn app.main:app --reload

# Then run integration tests in a separate terminal
python -m tests.requests.test_endpoints

# Run frontend integration tests
python -m tests.requests.test_frontend

# Optional: Run Selenium tests (requires ChromeDriver)
python -m tests.requests.test_frontend --selenium
```

## API Endpoints

### Health Check
```
curl -X GET http://localhost:8000/health
```

### Users
```
# Create a user
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"username": "user1"}'

# Get a user by ID
curl -X GET http://localhost:8000/api/v1/users/1
```

### Posts
```
# Create a post
curl -X POST http://localhost:8000/api/v1/posts \
  -H "Content-Type: application/json" \
  -d '{"title": "My First Post", "content": "Hello world!", "creator_id": 1, "tags": ["technology", "news"]}'

# Get a post by ID
curl -X GET http://localhost:8000/api/v1/posts/1
```

### Likes
```
# Like a post
curl -X POST http://localhost:8000/api/v1/likes \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "post_id": 1}'

# Unlike a post
curl -X DELETE http://localhost:8000/api/v1/likes \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "post_id": 1}'

# Get all posts liked by a user
curl -X GET http://localhost:8000/api/v1/likes/1
```

### Comments
```
# Create a comment
curl -X POST http://localhost:8000/api/v1/comments \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "post_id": 1, "content": "Great post!"}'

# Get all comments for a post
curl -X GET http://localhost:8000/api/v1/comments/1
```

### Personalized Feed
```
# Get personalized feed for a user
curl -X GET http://localhost:8000/api/v1/feed/1

# Get personalized feed with a limit
curl -X GET http://localhost:8000/api/v1/feed/1?limit=10
```

## Recommendation Approach

The API implements a content-based filtering strategy for post recommendations:

1. **User Profile Building**:
   - Analyzes a user's liked posts (weight=1.0) and commented posts (weight=0.5)
   - Extracts tags and calculates their frequencies in the user's interactions
   - Normalizes tag frequencies to create a weighted user preference profile

2. **Post Scoring**:
   - For each candidate post (not yet interacted with by the user):
     - Calculates a base score by matching post tags with user profile
     - Applies a recency boost using a decay factor (0.01 per day)
     - Combines tag matching and recency into a final relevance score

3. **Feed Generation**:
   - Sorts posts by score (descending) and then by creation date (descending)
   - Returns a configurable number of top-ranked posts (default: 20)
   - Falls back to recent posts for new users with no interaction history

4. **Trade-offs**:
   - **Pros**: Simple implementation, interpretable results, privacy-friendly (uses only user's own data)
   - **Cons**: Limited diversity, cold-start problems for new content
   - **Future Enhancements**: Could add TF-IDF for content analysis, collaborative filtering for cross-user recommendations, or ML-based embeddings for better content understanding

## Project Trade-offs

This project makes several design decisions that prioritize simplicity and rapid development over production readiness and scalability. Below are some key trade-offs:

### Security and Authentication
- **No Authentication or Authorization**: The API does not implement user authentication or authorization mechanisms. All endpoints are publicly accessible, which is suitable for development and demonstration but unsuitable for production environments where user data protection is required.
- **No Rate Limiting or Security Policies**: There are no measures to prevent abuse, such as rate limiting, input validation beyond basic Pydantic models, or security headers. This could lead to vulnerabilities like denial-of-service attacks or data injection.

### Database Design
- **Simple Integer IDs Instead of UUIDs**: User and post IDs are simple integers, which are easier to work with in development but can lead to enumeration attacks and are less secure for public APIs.
- **Manual Database Management**: The application explicitly drops and recreates tables on startup rather than using proper migration tools like Alembic. This is convenient for development but risks data loss and makes version control of database schema changes difficult.

### Content Management
- **Manual Tag Assignment**: Post tags are manually assigned by users rather than being automatically detected through natural language processing or machine learning. This ensures accuracy but requires more effort from users and may lead to inconsistent tagging.

### Other Trade-offs
- **SQLite Database**: Uses SQLite for simplicity and ease of setup, but it lacks the performance, concurrency, and features of production databases like PostgreSQL.
- **In-Memory Frontend**: The frontend is served directly by FastAPI using Jinja2 templates, which is simple but may not scale well and lacks the interactivity of modern SPA frameworks.
- **Limited Testing**: While unit tests are provided, there are no comprehensive integration tests for the frontend, and testing coverage may not be complete.
- **No Caching or Optimization**: No caching mechanisms are implemented, which could lead to performance issues with larger datasets.
- **No Containerization**: The project does not include Docker or similar containerization, making deployment and environment consistency harder.

These trade-offs reflect the project's focus on being a proof-of-concept or development tool rather than a production-ready application.

## Database Schema

The API uses SQLAlchemy with SQLite and includes the following models:

- `User`: Application users with unique usernames
- `Post`: User posts with title, content, creator reference, and creation timestamp
- `Tag`: Categories/tags for posts with unique names
- `PostTag`: Association table for post-tag many-to-many relationships
- `Like`: User likes on posts with unique constraint to prevent duplicates
- `Comment`: User comments on posts with content and timestamp

Note: While primarily designed for local development, a hosted version is available on Render for demonstration purposes.
