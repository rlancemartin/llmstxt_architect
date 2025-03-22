"""
Command-line interface for LLMsTxt Architect.
"""

import argparse
import asyncio
import sys
from typing import List, Optional

from llmstxt_architect.main import generate_llms_txt


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate LLMs.txt from web content using LLMs for summarization"
    )
    
    parser.add_argument(
        "--urls", 
        nargs="+", 
        required=True,
        help="List of URLs to process"
    )
    
    parser.add_argument(
        "--max-depth", 
        type=int, 
        default=5,
        help="Maximum recursion depth for URL crawling (default: 5)"
    )
    
    parser.add_argument(
        "--llm-name", 
        default="claude-3-sonnet-20240229",
        help="LLM model name (default: claude-3-sonnet-20240229)"
    )
    
    parser.add_argument(
        "--llm-provider", 
        default="anthropic",
        help="LLM provider (default: anthropic)"
    )
    
    parser.add_argument(
        "--project-dir",
        default="llms_txt",
        help="Main project directory to store all outputs (default: llms_txt)"
    )
    
    parser.add_argument(
        "--output-dir", 
        default="summaries",
        help="Directory within project-dir to save individual summaries (default: summaries)"
    )
    
    parser.add_argument(
        "--output-file", 
        default="llms.txt",
        help="Output file name for combined summaries (default: llms.txt)"
    )
    
    parser.add_argument(
        "--summary-prompt",
        default=(
            "You are creating a summary for a webpage to be used in a llms.txt file "
            "to help LLMs in the future know what is on this page. Produce a concise "
            "summary of the key items on this page and when an LLM should access it."
        ),
        help="Prompt to use for summarization"
    )
    
    return parser.parse_args()


def main() -> None:
    """Main entry point for the CLI."""
    args = parse_args()
    
    try:
        asyncio.run(generate_llms_txt(
            urls=args.urls,
            max_depth=args.max_depth,
            llm_name=args.llm_name,
            llm_provider=args.llm_provider,
            project_dir=args.project_dir,
            output_dir=args.output_dir,
            output_file=args.output_file,
            summary_prompt=args.summary_prompt,
        ))
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    

if __name__ == "__main__":
    main()