"""
Seed data generation script for the Humdov Post Feed API.

This script populates the database with dummy data for testing and demonstration purposes.
It creates users, posts, tags, likes, and comments with realistic relationships.
"""
import sys
import os
import random
from datetime import datetime, timedelta, timezone
from faker import Faker
from sqlalchemy.exc import IntegrityError

# Add the parent directory to sys.path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models import Base, User, Post, Tag, Like, Comment

# Initialize Faker
fake = Faker()


def ensure_aware(dt):
    """Return a timezone-aware datetime in UTC.

    If dt is naive (tzinfo is None) we assume it's UTC and attach timezone.utc.
    If dt is already aware, return as-is.
    If dt is None, return the current UTC time.
    """
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

# Constants for data generation
NUM_USERS = 20
NUM_POSTS = 100
NUM_LIKES = 250  # Between 200-300
NUM_COMMENTS = 120  # Between 100-150
TAG_LIST = ['technology', 'sports', 'food', 'travel', 'news', 'health', 'science', 'art', 'music', 'gaming']

# User interest clusters for more realistic personalization
USER_INTERESTS = {
    # User group ids -> tag preferences
    'tech_enthusiasts': ['technology', 'science', 'gaming'],
    'fitness_buffs': ['sports', 'health', 'food'],
    'travelers': ['travel', 'food', 'art'],
    'news_readers': ['news', 'technology', 'science'],
    'artists': ['art', 'music', 'food'],
}

def create_users(db):
    """Create users with unique usernames"""
    print("Creating users...")
    users = []
    for _ in range(NUM_USERS):
        username = fake.unique.user_name()
        user = User(username=username)
        db.add(user)
        users.append(user)
        print(f"Created user: {username}")
    
    db.commit()
    return users


def create_tags(db):
    """Create tags from the predefined list"""
    print("Creating tags...")
    tags = []
    for tag_name in TAG_LIST:
        tag = Tag(name=tag_name)
        db.add(tag)
        tags.append(tag)
        print(f"Created tag: {tag_name}")
    
    db.commit()
    return tags


def create_posts(db, users, tags):
    """Create posts with random creators and tags"""
    print("Creating posts...")
    posts = []
    
    # Ensure all date times are unique and in sequence
    start_date = datetime.now(timezone.utc) - timedelta(days=60)  # Posts from last 60 days
    
    for i in range(NUM_POSTS):
        creator = random.choice(users)
        
        # Generate post with a random date within the past 60 days
        post_date = start_date + timedelta(
            days=random.randint(0, 60),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        # Create post with title, content, creator_id, and random creation date
        # Faker.paragraphs(...) returns a list; join into a single string for the DB text field
        paragraphs = fake.paragraphs(nb=random.randint(1, 3), ext_word_list=None)
        post_content = "\n\n".join(paragraphs)

        post = Post(
            title=fake.sentence(),
            content=post_content,
            creator_id=creator.id,
            created_at=post_date
        )
        
        # Assign 1-3 random tags to post
        num_tags = random.randint(1, 3)
        post_tags = random.sample(tags, num_tags)
        for tag in post_tags:
            post.tags.append(tag)
        
        db.add(post)
        posts.append(post)
    
    db.commit()
    return posts


def get_user_interest_group(user_id):
    """Assign a user to an interest group for realistic personalization"""
    # Evenly distribute users among interest groups
    groups = list(USER_INTERESTS.keys())
    return groups[user_id % len(groups)]


def create_likes(db, users, posts):
    """Create likes with user interests in mind for better personalization"""
    print("Creating likes...")
    likes_count = 0
    max_attempts = NUM_LIKES * 2  # To handle potential duplicates
    attempts = 0
    
    while likes_count < NUM_LIKES and attempts < max_attempts:
        attempts += 1
        
        # Select a random user
        user = random.choice(users)
        
        # Get the user's interest group
        interest_group = get_user_interest_group(user.id)
        preferred_tags = USER_INTERESTS[interest_group]
        
        # Find posts that match the user's interests
        matching_posts = []
        for post in posts:
            post_tags = [tag.name for tag in post.tags]
            # Check if any of the post's tags match the user's interests
            if any(tag in preferred_tags for tag in post_tags):
                matching_posts.append(post)
        
        # If no matching posts found, use any post
        target_posts = matching_posts if matching_posts else posts
        post = random.choice(target_posts)
        
        # Create the like
        like = Like(user_id=user.id, post_id=post.id)
        
        # Add with try-except to handle unique constraint violations
        try:
            db.add(like)
            db.flush()  # Check for conflicts without committing
            likes_count += 1
        except IntegrityError:
            db.rollback()  # Roll back the failed transaction
            continue  # Try again
    
    db.commit()
    print(f"Created {likes_count} likes")
    return likes_count


def create_comments(db, users, posts):
    """Create comments with user interests in mind"""
    print("Creating comments...")
    comments = []
    
    for _ in range(NUM_COMMENTS):
        # Select a random user
        user = random.choice(users)
        
        # Get the user's interest group
        interest_group = get_user_interest_group(user.id)
        preferred_tags = USER_INTERESTS[interest_group]
        
        # Find posts that match the user's interests (75% of the time)
        matching_posts = []
        if random.random() < 0.75:
            for post in posts:
                post_tags = [tag.name for tag in post.tags]
                # Check if any of the post's tags match the user's interests
                if any(tag in preferred_tags for tag in post_tags):
                    matching_posts.append(post)
        
        # If no matching posts found, use any post
        target_posts = matching_posts if matching_posts else posts
        post = random.choice(target_posts)
        
        # Generate a comment related to the post's content
        comment_content = fake.sentence()

        # Create the comment with a timestamp after the post's creation
        post_date = post.created_at
        # Ensure post_date is timezone-aware before arithmetic
        post_date = ensure_aware(post_date)
        comment_date = post_date + timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )

        # Ensure comment_date is aware and compare with aware now
        comment_date = ensure_aware(comment_date)
        now_aware = datetime.now(timezone.utc)
        comment = Comment(
            user_id=user.id,
            post_id=post.id,
            content=comment_content,
            timestamp=comment_date if comment_date < now_aware else now_aware
        )

        db.add(comment)
        comments.append(comment)
    
    db.commit()
    return comments


def seed_database():
    """Main function to seed the database with test data"""
    print("Starting database seeding...")
    
    # Reset the database
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Create data in order of dependencies
        users = create_users(db)
        tags = create_tags(db)
        posts = create_posts(db, users, tags)
        likes_count = create_likes(db, users, posts)
        comments = create_comments(db, users, posts)
        
        print(f"Successfully seeded database with:")
        print(f"- {len(users)} users")
        print(f"- {len(tags)} tags")
        print(f"- {len(posts)} posts")
        print(f"- {likes_count} likes")
        print(f"- {len(comments)} comments")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
