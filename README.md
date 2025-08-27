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
```

The API will be available at `http://localhost:8000`.

API documentation (Swagger UI) will be available at `http://localhost:8000/docs`.

## Frontend Interface

The project includes a complete frontend interface that provides an intuitive demonstration of the post feed functionality. After starting the server, you can access the frontend at:

**http://localhost:8000**

### Frontend Features

- **Twitter-inspired Design**: Clean, modern UI with blue (#006CFF) accents and gray backgrounds/text inspired by Humdov landing page
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

## Database Schema

The API uses SQLAlchemy with SQLite and includes the following models:

- `User`: Application users with unique usernames
- `Post`: User posts with title, content, creator reference, and creation timestamp
- `Tag`: Categories/tags for posts with unique names
- `PostTag`: Association table for post-tag many-to-many relationships
- `Like`: User likes on posts with unique constraint to prevent duplicates
- `Comment`: User comments on posts with content and timestamp

Note: This API is designed for local development only and is not hosted externally.