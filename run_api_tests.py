import subprocess
import time
import unittest
import sys
import os
import signal
import requests
import argparse

def is_server_running():
    """Check if the server is already running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def run_tests(test_type="api", run_concurrent=False, verbose=False):
    """Run the specified tests"""
    # Check if server is already running
    server_already_running = is_server_running()
    server_process = None
    
    if not server_already_running:
        print("Starting FastAPI server...")
        # Start server as a subprocess
        server_process = subprocess.Popen(
            ["uvicorn", "app.main:app", "--reload"],
            stdout=subprocess.PIPE if not verbose else None,
            stderr=subprocess.PIPE if not verbose else None,
            text=True
        )
        
        # Wait for server to start
        print("Waiting for server to start...")
        start_time = time.time()
        max_wait = 10  # seconds
        while time.time() - start_time < max_wait:
            if is_server_running():
                print(f"Server started successfully after {time.time() - start_time:.2f} seconds")
                break
            time.sleep(0.5)
        else:
            print(f"Failed to start server after {max_wait} seconds")
            if server_process:
                # Print any server output that might help diagnose the issue
                if server_process.stdout and server_process.stderr:
                    stdout, stderr = server_process.communicate(timeout=1)
                    print("\nServer stdout:")
                    print(stdout or "No stdout output")
                    print("\nServer stderr:")
                    print(stderr or "No stderr output")
                server_process.terminate()
            return 1
    
    print("Server is running. Running tests...")
    
    try:
        # Run the tests
        test_loader = unittest.TestLoader()
        test_suite = unittest.TestSuite()
        
        if test_type in ["api", "all"]:
            api_tests = test_loader.discover('tests', pattern='test_api_requests.py')
            test_suite.addTest(api_tests)
            
        if run_concurrent or test_type in ["concurrent", "all"]:
            concurrent_tests = test_loader.discover('tests', pattern='test_concurrent_requests.py')
            test_suite.addTest(concurrent_tests)
        
        test_runner = unittest.TextTestRunner(verbosity=2)
        result = test_runner.run(test_suite)
        
        # Check test results
        if result.wasSuccessful():
            print("\nAll tests passed!")
            return 0
        else:
            print(f"\nTests failed: {len(result.failures)} failures, {len(result.errors)} errors")
            return 1
    finally:
        # Stop the server if we started it
        if server_process:
            print("Shutting down server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate gracefully
                if sys.platform == "win32":
                    os.kill(server_process.pid, signal.SIGTERM)
                else:
                    os.kill(server_process.pid, signal.SIGKILL)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run API tests for Humdov Post Feed API')
    parser.add_argument('--test-type', choices=['api', 'concurrent', 'all'], default='api',
                        help='Type of tests to run (api, concurrent, or all)')
    parser.add_argument('--concurrent', action='store_true', help='Run concurrent tests')
    parser.add_argument('--verbose', '-v', action='store_true', 
                        help='Show verbose output including server logs')
    
    args = parser.parse_args()
    sys.exit(run_tests(args.test_type, args.concurrent, args.verbose))
