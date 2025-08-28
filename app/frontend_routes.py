"""
Frontend routes for the Humdov Post Feed API.
These routes serve HTML pages and handle frontend functionality.
"""
from typing import List
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import models
from .database import get_db

# Create router for frontend routes
frontend_router = APIRouter(tags=["Frontend"])

# Set up Jinja2 templates
templates = Jinja2Templates(directory="app/frontend/templates")


@frontend_router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page with the personalized feed"""
    return templates.TemplateResponse("index.html", {"request": request})


@frontend_router.get("/analytics", response_class=HTMLResponse)
async def analytics(request: Request):
    """Render the analytics page"""
    return templates.TemplateResponse("analytics.html", {"request": request})


@frontend_router.get("/profile/{user_id}", response_class=HTMLResponse)
async def profile(request: Request, user_id: int, db: Session = Depends(get_db)):
    """Render the profile page for a specific user"""
    # Check if user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": user
    })


@frontend_router.get("/new_post", response_class=HTMLResponse)
async def new_post(request: Request):
    """Render the new post creation form"""
    return templates.TemplateResponse("new_post.html", {"request": request})


# Additional API route to get all users for the frontend user selector
@frontend_router.get("/api/v1/users", response_model=List[dict])
async def get_all_users(db: Session = Depends(get_db)):
    """Get all users for the frontend user selector"""
    users = db.query(models.User).all()
    return [{"id": user.id, "username": user.username} for user in users]
