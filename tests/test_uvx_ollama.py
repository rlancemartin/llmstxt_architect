#!/usr/bin/env python
"""Test UVX execution with Ollama LLM"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def test_uvx_ollama():
    """Test UVX execution with Ollama LLM"""
    # Set the project directory
    project_dir = Path("tmp/uvx_ollama_test")
    
    # Create the project directory if it doesn't exist
    os.makedirs(project_dir, exist_ok=True)
    
    # Run the UVX command
    cmd = [
        "uvx",
        "--from", "llmstxt-architect",
        "llmstxt-architect",
        "--urls", "https://langchain-ai.github.io/langgraph/concepts",
        "--max-depth", "1",
        "--llm-name", "llama3.2:latest",
        "--llm-provider", "ollama",
        "--project-dir", str(project_dir),
    ]
    
    try:
        # Run the command and capture the output
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        
        # Check if the llms.txt file was created
        assert (project_dir / "llms.txt").exists(), "llms.txt was not created"
        
        # Check if the summaries directory was created
        assert (project_dir / "summaries").exists(), "summaries directory was not created"
        
        # Check if the summarized_urls.json file was created
        assert (project_dir / "summaries" / "summarized_urls.json").exists(), "summarized_urls.json was not created"
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False
    finally:
        # Clean up the test directory
        if project_dir.exists():
            shutil.rmtree(project_dir)
            print(f"Cleaned up test directory: {project_dir}")


if __name__ == "__main__":
    success = test_uvx_ollama()
    sys.exit(0 if success else 1)
