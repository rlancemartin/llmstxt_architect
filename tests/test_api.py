#!/usr/bin/env python
"""Test API functionality"""

import asyncio
import shutil
import sys
from pathlib import Path

from llmstxt_architect.main import generate_llms_txt


async def test_api():
    """Test API functionality"""
    # Set the project directory
    project_dir = Path("tmp/test_api_output")
    
    try:
        await generate_llms_txt(
            urls=["https://langchain-ai.github.io/langgraph/concepts"],
            max_depth=1,
            llm_name="claude-3-7-sonnet-latest",
            llm_provider="anthropic",
            project_dir=str(project_dir),
        )
        
        # Check if the llms.txt file was created
        assert (project_dir / "llms.txt").exists(), "llms.txt was not created"
        
        # Check if the summaries directory was created
        assert (project_dir / "summaries").exists(), "summaries directory was not created"
        
        # Check if the summarized_urls.json file was created
        assert (project_dir / "summaries" / "summarized_urls.json").exists(), "summarized_urls.json was not created"
        
        print("✅ API test passed!")
        return True
    except Exception as e:
        print(f"❌ API test failed with error: {e}")
        return False
    finally:
        # Clean up the test directory
        if project_dir.exists():
            shutil.rmtree(project_dir)
            print(f"Cleaned up test directory: {project_dir}")


if __name__ == "__main__":
    success = asyncio.run(test_api())
    sys.exit(0 if success else 1)