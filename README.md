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

## Running Tests

Pytest-based tests:
```
pytest tests/pytest
```

Request-based tests (requires server to be running):
```
python -m tests.requests.test_endpoints
```

## API Endpoints

- `GET /health`: Health check endpoint
- `POST /users`: Create a user
- `GET /users/{user_id}`: Get a user by ID
- `POST /posts`: Create a post with tags
- `GET /posts/{post_id}`: Get a post by ID

## Database Schema

The API uses SQLAlchemy with SQLite and includes the following models:

- `User`: Application users
- `Post`: User posts with title and content
- `Tag`: Categories/tags for posts
- `PostTag`: Association table for post-tag relationships
- `Like`: User likes on posts
- `Comment`: User comments on posts