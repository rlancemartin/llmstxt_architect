#!/usr/bin/env python
"""Cleanup script to remove all test directories"""

import os
import shutil
from pathlib import Path


def cleanup_test_dirs():
    """Remove all test directories"""
    # List of directories to clean up
    dirs_to_clean = [
        "tmp",
        "test_script",
        "test_api_output",
        "test_api",
        "test_uvx",
    ]
    
    # Count of directories cleaned
    cleaned = 0
    
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists() and dir_path.is_dir():
            try:
                shutil.rmtree(dir_path)
                print(f"Cleaned up directory: {dir_path}")
                cleaned += 1
            except Exception as e:
                print(f"Error cleaning up {dir_path}: {e}")
    
    if cleaned > 0:
        print(f"\nSuccessfully cleaned up {cleaned} test directories")
    else:
        print("\nNo test directories found to clean up")


if __name__ == "__main__":
    cleanup_test_dirs()