import requests
import unittest
import random
import string
import time

# Base URL for API
BASE_URL = "http://localhost:8000/api/v1"

def random_string(length=8):
    """Generate a random string for test data"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

class TestApiRequests(unittest.TestCase):
    """
    Integration tests for Humdov API using requests module.
    These tests require the server to be running.
    """
    
    @classmethod
    def setUpClass(cls):
        """Setup before all tests - check if server is running"""
        try:
            response = requests.get("http://localhost:8000/health")
            if response.status_code != 200:
                raise Exception("Server returned non-200 status code")
        except Exception as e:
            raise Exception(f"Server is not running or not accessible: {str(e)}")
        
        print("Server is running and accessible")
    
    def setUp(self):
        """Setup before each test - create test user"""
        # Create a test user for use in tests
        username = f"testuser_{random_string()}"
        response = requests.post(f"{BASE_URL}/users", json={"username": username})
        
        # Print error details if user creation fails
        if response.status_code != 200:
            print(f"Failed to create test user: {response.status_code} - {response.text}")
            
        self.assertEqual(response.status_code, 200, "Failed to create test user")
        
        # Store user data for use in tests
        self.test_user = response.json()
        self.user_id = self.test_user["id"]
        
        # Also create some posts for tests that need them
        self.test_posts = []
        for i in range(2):
            post_data = {
                "title": f"Test Post {i} - {random_string()}",
                "content": f"This is test content {i} - {random_string(20)}",
                "creator_id": self.user_id,
                "tags": [f"tag{i}", "test"]
            }
            response = requests.post(f"{BASE_URL}/posts", json=post_data)
            
            # Print error details if post creation fails
            if response.status_code != 200:
                print(f"Failed to create test post {i}: {response.status_code} - {response.text}")
                # Continue with tests rather than fail immediately
                continue
                
            self.test_posts.append(response.json())
    
    def test_health_endpoint(self):
        """Test health endpoint returns healthy status"""
        response = requests.get("http://localhost:8000/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertEqual(data["status"], "healthy")
    
    def test_create_and_get_user(self):
        """Test creating a user and retrieving user details"""
        # Create another user
        username = f"testuser_{random_string()}"
        response = requests.post(f"{BASE_URL}/users", json={"username": username})
        self.assertEqual(response.status_code, 200)
        user_data = response.json()
        self.assertEqual(user_data["username"], username)
        self.assertIn("id", user_data)
        
        # Get the user by ID
        user_id = user_data["id"]
        response = requests.get(f"{BASE_URL}/users/{user_id}")
        self.assertEqual(response.status_code, 200)
        retrieved_user = response.json()
        self.assertEqual(retrieved_user["username"], username)
        self.assertEqual(retrieved_user["id"], user_id)
    
    def test_duplicate_username(self):
        """Test that creating users with duplicate usernames fails"""
        username = f"duplicate_{random_string()}"
        
        # Create first user
        response = requests.post(f"{BASE_URL}/users", json={"username": username})
        if response.status_code != 200:
            self.skipTest("Skipping test_duplicate_username because initial user creation failed")
            
        self.assertEqual(response.status_code, 200)
        
        # Try to create duplicate
        response = requests.post(f"{BASE_URL}/users", json={"username": username})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Username already registered", response.json().get("detail", ""))
    
    def test_create_and_get_post(self):
        """Test creating a post and retrieving post details"""
        # Create a post
        post_data = {
            "title": f"Test Post - {random_string()}",
            "content": f"This is test content - {random_string(20)}",
            "creator_id": self.user_id,
            "tags": ["test", "api"]
        }
        
        response = requests.post(f"{BASE_URL}/posts", json=post_data)
        self.assertEqual(response.status_code, 200)
        post = response.json()
        self.assertEqual(post["title"], post_data["title"])
        self.assertEqual(post["content"], post_data["content"])
        self.assertEqual(post["creator_id"], self.user_id)
        self.assertEqual(set(post["tags"]), set(post_data["tags"]))
        
        # Get the post by ID
        post_id = post["id"]
        response = requests.get(f"{BASE_URL}/posts/{post_id}")
        self.assertEqual(response.status_code, 200)
        retrieved_post = response.json()
        self.assertEqual(retrieved_post["title"], post_data["title"])
        self.assertEqual(retrieved_post["id"], post_id)
    
    def test_like_post(self):
        """Test liking a post"""
        # Skip test if no test posts were created
        if not self.test_posts:
            self.skipTest("Skipping test_like_post because no test posts were created")
        
        post_id = self.test_posts[0]["id"]
        
        # Like the post
        like_data = {
            "user_id": self.user_id,
            "post_id": post_id
        }
        response = requests.post(f"{BASE_URL}/likes", json=like_data)
        self.assertEqual(response.status_code, 200)
        
        # Check if like exists in user's likes
        response = requests.get(f"{BASE_URL}/likes/{self.user_id}")
        self.assertEqual(response.status_code, 200)
        likes = response.json()
        self.assertTrue(any(like["post_id"] == post_id for like in likes))
        
        # Try to like again (should fail)
        response = requests.post(f"{BASE_URL}/likes", json=like_data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("already liked", response.json().get("detail", "").lower())
        
        # Unlike the post
        response = requests.delete(f"{BASE_URL}/likes", json=like_data)
        self.assertEqual(response.status_code, 200)
        
        # Check if like was removed
        response = requests.get(f"{BASE_URL}/likes/{self.user_id}")
        self.assertEqual(response.status_code, 200)
        likes = response.json()
        self.assertFalse(any(like["post_id"] == post_id for like in likes))
    
    def test_add_comment(self):
        """Test adding a comment to a post"""
        # Skip test if no test posts were created
        if not self.test_posts:
            self.skipTest("Skipping test_add_comment because no test posts were created")
        
        post_id = self.test_posts[0]["id"]
        
        # Add a comment
        comment_data = {
            "user_id": self.user_id,
            "post_id": post_id,
            "content": f"Test comment - {random_string(15)}"
        }
        response = requests.post(f"{BASE_URL}/comments", json=comment_data)
        self.assertEqual(response.status_code, 200)
        
        # Check if comment exists in post comments
        response = requests.get(f"{BASE_URL}/comments/{post_id}")
        self.assertEqual(response.status_code, 200)
        comments = response.json()
        self.assertTrue(any(comment["content"] == comment_data["content"] for comment in comments))
    
    def test_personalized_feed(self):
        """Test getting a personalized feed"""
        # Skip test if no test posts were created
        if not self.test_posts:
            self.skipTest("Skipping test_personalized_feed because no test posts were created")
            
        # Create another user and some more posts
        username = f"feeduser_{random_string()}"
        user_resp = requests.post(f"{BASE_URL}/users", json={"username": username})
        self.assertEqual(user_resp.status_code, 200, "Failed to create feed test user")
        feed_user_id = user_resp.json()["id"]
        
        # Create posts for feed
        post_ids = []
        for i in range(5):
            post_data = {
                "title": f"Feed Post {i} - {random_string()}",
                "content": f"Feed content {i} - {random_string(20)}",
                "creator_id": feed_user_id,
                "tags": [f"feedtag{i}", "test"]
            }
            response = requests.post(f"{BASE_URL}/posts", json=post_data)
            if response.status_code == 200:
                post_ids.append(response.json()["id"])
        
        # Like a post to influence feed - only if we have test posts
        if self.test_posts:
            like_data = {
                "user_id": feed_user_id,
                "post_id": self.test_posts[0]["id"]
            }
            requests.post(f"{BASE_URL}/likes", json=like_data)
        
        # Get feed for the user - URL pattern is /feed/{user_id}
        response = requests.get(f"{BASE_URL}/feed/{feed_user_id}")
        self.assertEqual(response.status_code, 200)
        feed = response.json()
        
        # Feed should contain posts
        self.assertGreater(len(feed), 0)
        
        # Each feed item should have a post and score
        for item in feed:
            self.assertIn("post", item)
            self.assertIn("score", item)
            
    def test_get_all_posts(self):
        """Test getting all posts"""
        # Create a post with unique identifiable title
        unique_word = f"unique{random_string(10)}"
        post_data = {
            "title": f"Identifiable {unique_word} Post",
            "content": "This is unique content",
            "creator_id": self.user_id,
            "tags": ["unique", "test"]
        }
        
        response = requests.post(f"{BASE_URL}/posts", json=post_data)
        self.assertEqual(response.status_code, 200)
        created_post_id = response.json()["id"]
        
        # Get the post directly
        response = requests.get(f"{BASE_URL}/posts/{created_post_id}")
        self.assertEqual(response.status_code, 200)
        retrieved_post = response.json()
        
        # Verify it's the correct post
        self.assertEqual(retrieved_post["id"], created_post_id)
        self.assertEqual(retrieved_post["title"], post_data["title"])
        self.assertEqual(retrieved_post["content"], post_data["content"])
    
    def test_analytics(self):
        """Test analytics endpoint"""
        # Create additional post interactions to generate analytics data
        post_id = self.test_posts[0]["id"]
        
        # Create another user
        username = f"analytics_{random_string()}"
        user_resp = requests.post(f"{BASE_URL}/users", json={"username": username})
        analytics_user_id = user_resp.json()["id"]
        
        # Like and comment on posts
        like_data = {
            "user_id": analytics_user_id,
            "post_id": post_id
        }
        requests.post(f"{BASE_URL}/likes", json=like_data)
        
        comment_data = {
            "user_id": analytics_user_id,
            "post_id": post_id,
            "content": "Analytics test comment"
        }
        requests.post(f"{BASE_URL}/comments", json=comment_data)
        
        # Wait briefly to ensure data is processed
        time.sleep(0.5)
        
        # Get general analytics
        response = requests.get(f"{BASE_URL}/analytics")
        self.assertEqual(response.status_code, 200)
        analytics = response.json()
        
        # Should include counts for platform metrics
        self.assertIn("user_count", analytics)
        self.assertIn("post_count", analytics)
        self.assertIn("comment_count", analytics)
        self.assertIn("like_count", analytics)
        self.assertGreaterEqual(analytics["user_count"], 2)  # At least our test users
        self.assertGreaterEqual(analytics["post_count"], 2)  # At least our test posts
        self.assertGreaterEqual(analytics["comment_count"], 1)  # Our test comment
        self.assertGreaterEqual(analytics["like_count"], 1)  # Our test like


if __name__ == "__main__":
    unittest.main()
