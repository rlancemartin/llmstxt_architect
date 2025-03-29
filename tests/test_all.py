#!/usr/bin/env python
"""Run all tests"""

import asyncio
import os
import subprocess
import sys

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from test_script_claude import test_script_claude
from cleanup import cleanup_test_dirs


async def run_all_tests():
    """Run all tests"""
    # First, clean up any existing test directories
    print("\nCleaning up existing test directories...")
    cleanup_test_dirs()
    
    # Track test results
    results = {}
    
    # Test 1: UVX with Claude
    print("\nRunning Test 1: UVX with Claude...")
    try:
        result = subprocess.run(
            ["python", os.path.join(current_dir, "test_uvx_claude.py")],
            check=True,
            capture_output=True,
            text=True,
        )
        results["uvx_claude"] = True
        print("✅ Test 1 passed!")
    except subprocess.CalledProcessError as e:
        results["uvx_claude"] = False
        print("❌ Test 1 failed:")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
    
    # Test 2: UVX with Ollama
    print("\nRunning Test 2: UVX with Ollama...")
    try:
        result = subprocess.run(
            ["python", os.path.join(current_dir, "test_uvx_ollama.py")],
            check=True,
            capture_output=True,
            text=True,
        )
        results["uvx_ollama"] = True
        print("✅ Test 2 passed!")
    except subprocess.CalledProcessError as e:
        results["uvx_ollama"] = False
        print("❌ Test 2 failed:")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
    
    # Test 3: Script import
    print("\nRunning Test 3: Script import...")
    try:
        success = await test_script_claude()
        results["script_claude"] = success
        if success:
            print("✅ Test 3 passed!")
        else:
            print("❌ Test 3 failed!")
    except Exception as e:
        results["script_claude"] = False
        print(f"❌ Test 3 failed with error: {e}")
        
    # Test 4: API usage
    print("\nRunning Test 4: API usage...")
    try:
        result = subprocess.run(
            ["python", os.path.join(current_dir, "test_api.py")],
            check=True,
            capture_output=True,
            text=True,
        )
        results["api"] = True
        print("✅ Test 4 passed!")
    except subprocess.CalledProcessError as e:
        results["api"] = False
        print("❌ Test 4 failed:")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        
    # Test 5: CLI argument parsing
    print("\nRunning Test 5: CLI argument parsing...")
    try:
        result = subprocess.run(
            ["python", os.path.join(current_dir, "test_cli.py")],
            check=True,
            capture_output=True,
            text=True,
        )
        results["cli"] = True
        print("✅ Test 5 passed!")
    except subprocess.CalledProcessError as e:
        results["cli"] = False
        print("❌ Test 5 failed:")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
    
    # Print summary
    print("\nTest Summary:")
    for test_name, result in results.items():
        print(f"{test_name}: {'✅ PASSED' if result else '❌ FAILED'}")
    
    # Run final cleanup to ensure a clean environment
    print("\nRunning final cleanup...")
    cleanup_test_dirs()
    
    # Return overall success (True if all tests passed)
    return all(results.values())


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
