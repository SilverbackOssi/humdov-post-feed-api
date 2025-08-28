import requests
import threading
import unittest
import random
import string
import time
import concurrent.futures

# Base URL for API
BASE_URL = "http://localhost:8000/api/v1"

def random_string(length=8):
    """Generate a random string for test data"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

class TestApiConcurrentRequests(unittest.TestCase):
    """
    Test concurrent requests to the API to ensure stability.
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
        
        # Create test users for concurrent tests
        cls.test_users = []
        for i in range(10):
            username = f"concurrentuser_{random_string()}"
            response = requests.post(f"{BASE_URL}/users", json={"username": username})
            if response.status_code == 200:
                cls.test_users.append(response.json())
        
        if not cls.test_users:
            raise Exception("Failed to create test users for concurrent tests")
    
    def test_concurrent_post_creation(self):
        """Test creating multiple posts concurrently"""
        num_posts = 20
        user_ids = [user["id"] for user in self.test_users]
        
        def create_post():
            user_id = random.choice(user_ids)
            post_data = {
                "title": f"Concurrent Post - {random_string()}",
                "content": f"This is concurrent test content - {random_string(20)}",
                "creator_id": user_id,
                "tags": ["concurrent", "test", random_string()]
            }
            response = requests.post(f"{BASE_URL}/posts", json=post_data)
            return response.status_code == 200
        
        # Create posts concurrently using thread pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(lambda _: create_post(), range(num_posts)))
        
        # All requests should succeed
        self.assertTrue(all(results), f"{results.count(False)} of {num_posts} concurrent post creations failed")
    
    def test_concurrent_likes(self):
        """Test creating likes concurrently"""
        # Create a test post that will receive likes
        post_data = {
            "title": f"Concurrent Like Test - {random_string()}",
            "content": "This post will receive many concurrent likes",
            "creator_id": self.test_users[0]["id"],
            "tags": ["likes", "concurrent"]
        }
        response = requests.post(f"{BASE_URL}/posts", json=post_data)
        self.assertEqual(response.status_code, 200, "Failed to create test post")
        post_id = response.json()["id"]
        
        # Function to like the post
        def like_post(user_id):
            like_data = {
                "user_id": user_id,
                "post_id": post_id
            }
            response = requests.post(f"{BASE_URL}/likes", json=like_data)
            return response.status_code == 200
        
        # Like post concurrently with different users
        user_ids = [user["id"] for user in self.test_users]
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(like_post, user_ids))
        
        # Count successful likes
        successful_likes = results.count(True)
        
        # Get all likes for each user and check if they include the post
        likes_count = 0
        for user in self.test_users:
            response = requests.get(f"{BASE_URL}/likes/{user['id']}")
            if response.status_code == 200:
                user_likes = response.json()
                likes_count += sum(1 for like in user_likes if like['post_id'] == post_id)
        
        # Should match the number of successful concurrent likes
        self.assertEqual(likes_count, successful_likes)
    
    def test_concurrent_reads(self):
        """Test reading posts concurrently"""
        # Create some test posts first
        post_ids = []
        for i in range(5):
            post_data = {
                "title": f"Read Test Post {i} - {random_string()}",
                "content": f"Content for concurrent reading test {i}",
                "creator_id": self.test_users[0]["id"],
                "tags": ["read", "test"]
            }
            response = requests.post(f"{BASE_URL}/posts", json=post_data)
            if response.status_code == 200:
                post_ids.append(response.json()["id"])
        
        # Function to read a random post
        def read_random_post():
            if not post_ids:
                return True  # Skip if no posts were created
            
            post_id = random.choice(post_ids)
            response = requests.get(f"{BASE_URL}/posts/{post_id}")
            return response.status_code == 200
        
        # Perform concurrent reads
        num_reads = 50
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            results = list(executor.map(lambda _: read_random_post(), range(num_reads)))
        
        # All reads should succeed
        self.assertTrue(all(results), f"{results.count(False)} of {num_reads} concurrent reads failed")
    
    def test_mixed_concurrent_operations(self):
        """Test mixed operations (create, read, like) concurrently"""
        user_ids = [user["id"] for user in self.test_users]
        
        # Create a shared list for post IDs created during the test
        shared_post_ids = []
        
        # Create lock for thread-safe access to shared_post_ids
        lock = threading.Lock()
        
        def random_operation():
            """Perform a random API operation"""
            operation = random.choice(["create", "read", "like", "comment"])
            
            if operation == "create":
                # Create a post
                user_id = random.choice(user_ids)
                post_data = {
                    "title": f"Mixed Concurrent - {random_string()}",
                    "content": f"Mixed concurrent test content - {random_string(10)}",
                    "creator_id": user_id,
                    "tags": ["mixed", "concurrent"]
                }
                response = requests.post(f"{BASE_URL}/posts", json=post_data)
                
                # If successful, add to shared list
                if response.status_code == 200:
                    post_id = response.json()["id"]
                    with lock:
                        shared_post_ids.append(post_id)
                
                return response.status_code == 200
                
            elif operation == "read":
                # Read a post - either from our shared list or a static ID
                with lock:
                    post_ids_copy = shared_post_ids.copy()
                
                if post_ids_copy:
                    post_id = random.choice(post_ids_copy)
                else:
                    # If no posts created yet, read from API posts/1 (assuming it exists)
                    post_id = 1
                    
                response = requests.get(f"{BASE_URL}/posts/{post_id}")
                return response.status_code in [200, 404]  # 404 is acceptable if post doesn't exist
                
            elif operation == "like":
                # Like a post
                with lock:
                    post_ids_copy = shared_post_ids.copy()
                
                if not post_ids_copy:
                    return True  # Skip if no posts created yet
                    
                post_id = random.choice(post_ids_copy)
                user_id = random.choice(user_ids)
                
                like_data = {
                    "user_id": user_id,
                    "post_id": post_id
                }
                response = requests.post(f"{BASE_URL}/likes", json=like_data)
                return response.status_code in [200, 400]  # 400 is acceptable for duplicate likes
                
            elif operation == "comment":
                # Comment on a post
                with lock:
                    post_ids_copy = shared_post_ids.copy()
                
                if not post_ids_copy:
                    return True  # Skip if no posts created yet
                    
                post_id = random.choice(post_ids_copy)
                user_id = random.choice(user_ids)
                
                comment_data = {
                    "user_id": user_id,
                    "post_id": post_id,
                    "content": f"Mixed concurrent test comment - {random_string(10)}"
                }
                response = requests.post(f"{BASE_URL}/comments", json=comment_data)
                return response.status_code == 200
        
        # Perform mixed concurrent operations
        num_operations = 100
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            results = list(executor.map(lambda _: random_operation(), range(num_operations)))
        
        # Most operations should succeed
        success_rate = results.count(True) / len(results)
        self.assertGreaterEqual(success_rate, 0.8, 
                              f"Concurrent operations success rate too low: {success_rate:.2f}")


if __name__ == "__main__":
    unittest.main()
