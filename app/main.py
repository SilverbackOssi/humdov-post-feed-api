from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .database import engine
from . import models, routes, schemas, frontend_routes, seed_data

# Create FastAPI instance
app = FastAPI(
    title="Humdov Post Feed API",
    description="A simple API for posts, users, and interactions",
    version="0.1.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/frontend/static"), name="static")

# Include API routes
app.include_router(routes.users_router)
app.include_router(routes.posts_router)
app.include_router(routes.interactions_router)
app.include_router(routes.feed_router)
app.include_router(routes.analytics_router)

# Include frontend routes
app.include_router(frontend_routes.frontend_router)

# Health check endpoint
@app.get("/health", response_model=schemas.HealthResponse)
def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    """Seed database tables on startup"""
    # seed_data.seed_database()
