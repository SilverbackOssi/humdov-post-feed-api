from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from .database import engine, get_db
from . import models, routes, schemas

# Create FastAPI instance
app = FastAPI(
    title="Humdov Post Feed API",
    description="A simple API for posts, users, and interactions",
    version="0.1.0"
)

# Include routes
app.include_router(routes.users_router)
app.include_router(routes.posts_router)
app.include_router(routes.interactions_router)
app.include_router(routes.feed_router)

# Health check endpoint
@app.get("/health", response_model=schemas.HealthResponse)
def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    """Create all database tables on startup"""
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
