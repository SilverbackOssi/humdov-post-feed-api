import requests
import unittest

class TestEndpoints(unittest.TestCase):
    """Test endpoints using the requests library (requires server to be running)"""
    
    BASE_URL = "http://localhost:8000"
    
    def setUp(self):
        """Set up test data by creating users and posts"""
        # Create test users
        self.user1 = self.create_user("user1_test")
        self.user2 = self.create_user("user2_test")
        
        # Create test posts
        self.post1 = self.create_post("Test Post 1", "Content 1", self.user1["id"], ["tag1", "tag2"])
        self.post2 = self.create_post("Test Post 2", "Content 2", self.user2["id"], ["tag2", "tag3"])
    
    def create_user(self, username):
        """Helper method to create a user"""
        response = requests.post(
            f"{self.BASE_URL}/api/v1/users",
            json={"username": username}
        )
        return response.json()
    
    def create_post(self, title, content, creator_id, tags):
        """Helper method to create a post"""
        response = requests.post(
            f"{self.BASE_URL}/api/v1/posts",
            json={
                "title": title,
                "content": content,
                "creator_id": creator_id,
                "tags": tags
            }
        )
        return response.json()
    
    def test_health_endpoint(self):
        """Test that the health endpoint returns the expected response"""
        response = requests.get(f"{self.BASE_URL}/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "healthy"})
    
    def test_like_workflow(self):
        """Test the like creation and deletion workflow"""
        # Like a post
        like_data = {"user_id": self.user1["id"], "post_id": self.post2["id"]}
        response = requests.post(f"{self.BASE_URL}/api/v1/likes", json=like_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "liked"})
        
        # Try to like the same post again (should fail)
        response = requests.post(f"{self.BASE_URL}/api/v1/likes", json=like_data)
        self.assertEqual(response.status_code, 400)
        
        # Get user likes
        response = requests.get(f"{self.BASE_URL}/api/v1/likes/{self.user1['id']}")
        self.assertEqual(response.status_code, 200)
        likes = response.json()
        self.assertEqual(len(likes), 1)
        self.assertEqual(likes[0]["post_id"], self.post2["id"])
        
        # Unlike the post
        response = requests.delete(f"{self.BASE_URL}/api/v1/likes", json=like_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "unliked"})
        
        # Verify the like is gone
        response = requests.get(f"{self.BASE_URL}/api/v1/likes/{self.user1['id']}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)
    
    def test_comment_workflow(self):
        """Test the comment creation and retrieval workflow"""
        # Create a comment
        comment_data = {
            "user_id": self.user1["id"],
            "post_id": self.post2["id"],
            "content": "This is a test comment"
        }
        response = requests.post(f"{self.BASE_URL}/api/v1/comments", json=comment_data)
        self.assertEqual(response.status_code, 200)
        comment = response.json()
        self.assertEqual(comment["content"], "This is a test comment")
        
        # Get comments for the post
        response = requests.get(f"{self.BASE_URL}/api/v1/comments/{self.post2['id']}")
        self.assertEqual(response.status_code, 200)
        comments = response.json()
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0]["content"], "This is a test comment")
    
    def test_feed_endpoint(self):
        """Test the personalized feed endpoint"""
        # Like a post to create some interaction data
        like_data = {"user_id": self.user1["id"], "post_id": self.post2["id"]}
        requests.post(f"{self.BASE_URL}/api/v1/likes", json=like_data)
        
        # Add a comment to create more interaction data
        comment_data = {
            "user_id": self.user1["id"],
            "post_id": self.post2["id"],
            "content": "Feed test comment"
        }
        requests.post(f"{self.BASE_URL}/api/v1/comments", json=comment_data)
        
        # Get the feed for user1
        response = requests.get(f"{self.BASE_URL}/api/v1/feed/{self.user1['id']}")
        self.assertEqual(response.status_code, 200)
        feed = response.json()
        
        # Since we only have two posts and one is interacted with,
        # we should have at most one post in the feed
        self.assertLessEqual(len(feed), 1)
        
        # If there are posts, make sure they have the required fields
        if feed:
            self.assertIn("id", feed[0])
            self.assertIn("title", feed[0])
            self.assertIn("content", feed[0])
            self.assertIn("created_at", feed[0])
            self.assertIn("tags", feed[0])
            self.assertIn("score", feed[0])
            self.assertIn("creator_id", feed[0])


if __name__ == "__main__":
    unittest.main()
