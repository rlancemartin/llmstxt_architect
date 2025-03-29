#!/usr/bin/env python3
"""
Test script to test CLI argument parsing.
"""

import argparse
import sys

def parse_args(test_args=None):
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Test CLI parser"
    )
    
    # Create mutually exclusive group for URL input sources
    url_group = parser.add_mutually_exclusive_group(required=True)
    
    url_group.add_argument(
        "--urls", 
        nargs="+", 
        help="List of URLs to process"
    )
    
    url_group.add_argument(
        "--existing-llms-file",
        help="Path to an existing llms.txt file to extract URLs from and update"
    )
    
    parser.add_argument(
        "--update-descriptions-only",
        action="store_true",
        help="Update only descriptions in existing llms.txt"
    )
    
    # If test_args is provided, parse those instead of sys.argv
    if test_args:
        return parser.parse_args(test_args)
    return parser.parse_args()

def test_url_args():
    """Test with URL arguments."""
    try:
        test_args = ["--urls", "https://example.com", "https://example.org"]
        args = parse_args(test_args)
        
        # Check if arguments were parsed correctly
        assert args.urls == ["https://example.com", "https://example.org"], "URLs not parsed correctly"
        assert args.existing_llms_file is None, "existing_llms_file should be None"
        assert args.update_descriptions_only is False, "update_descriptions_only should be False"
        
        print("✅ URL args test passed!")
        return True
    except Exception as e:
        print(f"❌ URL args test failed: {e}")
        return False

def test_existing_file_args():
    """Test with existing-llms-file argument."""
    try:
        test_args = ["--existing-llms-file", "path/to/llms.txt", "--update-descriptions-only"]
        args = parse_args(test_args)
        
        # Check if arguments were parsed correctly
        assert args.urls is None, "urls should be None"
        assert args.existing_llms_file == "path/to/llms.txt", "existing_llms_file not parsed correctly"
        assert args.update_descriptions_only is True, "update_descriptions_only should be True"
        
        print("✅ Existing file args test passed!")
        return True
    except Exception as e:
        print(f"❌ Existing file args test failed: {e}")
        return False

def run_tests():
    """Run all parser tests."""
    # Track test results
    results = {}
    
    # Test 1: URL arguments
    print("\nTesting URL arguments...")
    results["url_args"] = test_url_args()
    
    # Test 2: Existing file arguments
    print("\nTesting existing file arguments...")
    results["existing_file_args"] = test_existing_file_args()
    
    # Print summary
    print("\nTest Summary:")
    for test_name, result in results.items():
        print(f"{test_name}: {'✅ PASSED' if result else '❌ FAILED'}")
    
    # Return overall success (True if all tests passed)
    return all(results.values())

def main():
    """Main test function."""
    success = run_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()