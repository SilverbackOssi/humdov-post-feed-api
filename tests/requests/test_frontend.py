"""
Integration tests for the frontend functionality.
These tests require a running server and test the complete frontend workflow.
"""
import requests
import unittest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

class TestFrontendIntegration(unittest.TestCase):
    """Integration tests for the frontend (requires server to be running)"""
    
    BASE_URL = "http://localhost:8000"
    
    def setUp(self):
        """Set up test environment"""
        # Check if server is running
        try:
            response = requests.get(f"{self.BASE_URL}/health", timeout=5)
            if response.status_code != 200:
                self.skipTest("Server is not running or not responding correctly")
        except requests.exceptions.RequestException:
            self.skipTest("Server is not running at localhost:8000")
    
    def test_home_page_accessible(self):
        """Test that the home page is accessible and contains expected content"""
        response = requests.get(f"{self.BASE_URL}/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Humdov Post Feed", response.text)
        self.assertIn("Home", response.text)
        self.assertIn("Profile", response.text)
        self.assertIn("New Post", response.text)
    
    def test_profile_page_accessible(self):
        """Test that profile pages are accessible"""
        # Try to access profile page for user ID 1
        response = requests.get(f"{self.BASE_URL}/profile/1")
        
        # If users exist, should be 200, otherwise might be 404
        # Both are acceptable depending on whether data has been seeded
        self.assertIn(response.status_code, [200, 404])
        
        if response.status_code == 200:
            self.assertIn("Profile", response.text)
    
    def test_new_post_page_accessible(self):
        """Test that the new post page is accessible and contains the form"""
        response = requests.get(f"{self.BASE_URL}/new_post")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Create New Post", response.text)
        self.assertIn("Title", response.text)
        self.assertIn("Content", response.text)
        self.assertIn("Tags", response.text)
        self.assertIn('<form id="postForm"', response.text)
    
    def test_static_files_serve_correctly(self):
        """Test that static files are served correctly"""
        # Test CSS file
        css_response = requests.get(f"{self.BASE_URL}/static/css/style.css")
        self.assertEqual(css_response.status_code, 200)
        self.assertIn("--primary-blue: #006CFF", css_response.text)
        
        # Test JavaScript file
        js_response = requests.get(f"{self.BASE_URL}/static/js/script.js")
        self.assertEqual(js_response.status_code, 200)
        self.assertIn("PostFeedApp", js_response.text)
    
    def test_api_endpoints_accessible_from_frontend(self):
        """Test that API endpoints used by the frontend are accessible"""
        # Test users endpoint for user selector
        response = requests.get(f"{self.BASE_URL}/api/v1/users")
        self.assertEqual(response.status_code, 200)
        users = response.json()
        self.assertIsInstance(users, list)
        
        # Test feed endpoint (might be empty but should not error)
        if users:  # Only test if users exist
            user_id = users[0]["id"]
            feed_response = requests.get(f"{self.BASE_URL}/api/v1/feed/{user_id}")
            self.assertEqual(feed_response.status_code, 200)
            feed = feed_response.json()
            self.assertIsInstance(feed, list)
    
    def test_create_user_and_post_workflow(self):
        """Test creating a user and then creating a post"""
        # Create a test user
        user_data = {"username": f"test_frontend_user_{int(time.time())}"}
        user_response = requests.post(f"{self.BASE_URL}/api/v1/users", json=user_data)
        self.assertEqual(user_response.status_code, 200)
        user = user_response.json()
        
        # Create a test post
        post_data = {
            "title": "Frontend Test Post",
            "content": "This is a test post created from frontend testing",
            "creator_id": user["id"],
            "tags": ["test", "frontend"]
        }
        post_response = requests.post(f"{self.BASE_URL}/api/v1/posts", json=post_data)
        self.assertEqual(post_response.status_code, 200)
        post = post_response.json()
        
        # Verify the post was created
        self.assertEqual(post["title"], "Frontend Test Post")
        self.assertEqual(post["creator_id"], user["id"])
        self.assertIn("test", post["tags"])
        self.assertIn("frontend", post["tags"])
        
        # Test retrieving the post
        get_post_response = requests.get(f"{self.BASE_URL}/api/v1/posts/{post['id']}")
        self.assertEqual(get_post_response.status_code, 200)
        retrieved_post = get_post_response.json()
        self.assertEqual(retrieved_post["id"], post["id"])
    
    def test_like_and_comment_workflow(self):
        """Test the like and comment functionality"""
        # First, ensure we have users and posts
        users_response = requests.get(f"{self.BASE_URL}/api/v1/users")
        if not users_response.ok:
            self.skipTest("No users available for testing")
        
        users = users_response.json()
        if len(users) < 2:
            self.skipTest("Need at least 2 users for testing")
        
        user1_id = users[0]["id"]
        user2_id = users[1]["id"]
        
        # Create a test post
        post_data = {
            "title": "Post for Like/Comment Test",
            "content": "Testing likes and comments",
            "creator_id": user1_id,
            "tags": ["test"]
        }
        post_response = requests.post(f"{self.BASE_URL}/api/v1/posts", json=post_data)
        self.assertEqual(post_response.status_code, 200)
        post = post_response.json()
        
        # Test liking the post
        like_data = {"user_id": user2_id, "post_id": post["id"]}
        like_response = requests.post(f"{self.BASE_URL}/api/v1/likes", json=like_data)
        self.assertEqual(like_response.status_code, 200)
        self.assertEqual(like_response.json()["message"], "liked")
        
        # Test commenting on the post
        comment_data = {
            "user_id": user2_id,
            "post_id": post["id"],
            "content": "This is a test comment from frontend testing"
        }
        comment_response = requests.post(f"{self.BASE_URL}/api/v1/comments", json=comment_data)
        self.assertEqual(comment_response.status_code, 200)
        comment = comment_response.json()
        self.assertEqual(comment["content"], "This is a test comment from frontend testing")
        
        # Test retrieving comments
        comments_response = requests.get(f"{self.BASE_URL}/api/v1/comments/{post['id']}")
        self.assertEqual(comments_response.status_code, 200)
        comments = comments_response.json()
        self.assertTrue(len(comments) >= 1)
        self.assertTrue(any(c["content"] == "This is a test comment from frontend testing" for c in comments))


class TestFrontendWithSelenium(unittest.TestCase):
    """Frontend tests using Selenium (optional - requires Chrome/ChromeDriver)"""
    
    BASE_URL = "http://localhost:8000"
    
    def setUp(self):
        """Set up Selenium WebDriver"""
        try:
            # Check if server is running
            response = requests.get(f"{self.BASE_URL}/health", timeout=5)
            if response.status_code != 200:
                self.skipTest("Server is not running")
                
            # Set up Chrome options for headless testing
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            # Try to create WebDriver
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            
        except WebDriverException:
            self.skipTest("Chrome WebDriver not available")
        except requests.exceptions.RequestException:
            self.skipTest("Server is not running")
    
    def tearDown(self):
        """Clean up WebDriver"""
        if hasattr(self, 'driver'):
            self.driver.quit()
    
    def test_home_page_loads_and_displays_content(self):
        """Test that the home page loads and displays expected elements"""
        self.driver.get(f"{self.BASE_URL}/")
        
        # Check page title
        self.assertIn("Humdov Post Feed", self.driver.title)
        
        # Check for main navigation elements
        self.assertTrue(self.driver.find_element(By.CLASS_NAME, "logo"))
        self.assertTrue(self.driver.find_element(By.CLASS_NAME, "sidebar"))
        self.assertTrue(self.driver.find_element(By.CLASS_NAME, "main-content"))
        
        # Check for user selector
        self.assertTrue(self.driver.find_element(By.ID, "userSelector"))
    
    def test_navigation_links_work(self):
        """Test that navigation links work correctly"""
        self.driver.get(f"{self.BASE_URL}/")
        
        # Test New Post link
        new_post_link = self.driver.find_element(By.XPATH, "//a[@href='/new_post']")
        new_post_link.click()
        
        # Should navigate to new post page
        self.assertIn("new_post", self.driver.current_url)
        self.assertIn("Create New Post", self.driver.page_source)
        
        # Test Home link
        home_link = self.driver.find_element(By.XPATH, "//a[@href='/']")
        home_link.click()
        
        # Should navigate back to home
        self.assertEqual(self.driver.current_url.rstrip('/'), self.BASE_URL)


if __name__ == "__main__":
    # Run only the basic tests by default (without Selenium)
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestFrontendIntegration))
    
    # Only add Selenium tests if explicitly requested
    import sys
    if "--selenium" in sys.argv:
        suite.addTest(unittest.makeSuite(TestFrontendWithSelenium))
    
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
