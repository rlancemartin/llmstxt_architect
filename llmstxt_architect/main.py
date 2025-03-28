"""
Core functionality for generating LLMs.txt files.
"""

import asyncio
import time
from typing import Callable, Dict, List, Any, Optional

from llmstxt_architect.extractor import bs4_extractor, default_extractor
from llmstxt_architect.loader import load_urls, parse_existing_llms_file
from llmstxt_architect.styling import status_message, generate_summary_report
from llmstxt_architect.summarizer import Summarizer


async def generate_llms_txt(
    urls: List[str],
    max_depth: int = 5,
    extractor: Callable[[str], str] = None,
    llm_name: str = "claude-3-sonnet-20240229",
    llm_provider: str = "anthropic",
    summary_prompt: str = (
        "You will create a summary in EXACTLY this format, with NO deviation:\n"
        "Line 1: 'LLM should read this page when (2-3 specific scenarios based on page content)'\n"
        "Line 2: '(Direct summary of main topics with no preamble, under 100 words)'\n\n"
        "IMPORTANT: Total length must be under 150 words. No extra explanations or preambles. "
        "Do not start with phrases like 'Here is...' or 'This summary...'"
    ),
    project_dir: str = "llms_txt",
    output_dir: str = "summaries",
    output_file: str = "llms.txt",
    blacklist_file: str = None,
    existing_llms_file: Optional[str] = None,
    update_descriptions_only: bool = False,
) -> None:
    """
    Generate an llms.txt file from a list of URLs.
    
    Args:
        urls: List of URLs to process
        max_depth: Maximum recursion depth for URL loading
        extractor: Function to extract content from HTML
        llm_name: Name of the LLM model to use
        llm_provider: Provider of the LLM
        summary_prompt: Prompt to use for summarization
        project_dir: Main project directory to store all outputs
        output_dir: Directory within project_dir to save individual summaries
        output_file: File name for combined summaries (saved in project_dir)
        blacklist_file: Path to a file containing blacklisted URLs to exclude (one per line)
        existing_llms_file: Path to an existing llms.txt file to extract URLs and structure from
        update_descriptions_only: If True, preserve the existing file structure and only update descriptions
    """
    # Start timing
    start_time = time.time()
    
    # Stats to track
    stats: Dict[str, Any] = {
        "urls_processed": 0,
        "summaries_generated": 0,
        "failed_urls": [],
        "total_time": 0,
        "output_path": ""
    }
    
    # Use default extractor if none provided
    if extractor is None:
        extractor = default_extractor
    
    import os
    from pathlib import Path
    
    # Create project directory if it doesn't exist
    project_path = Path(project_dir)
    os.makedirs(project_path, exist_ok=True)
    
    # Construct paths relative to project directory
    summaries_path = project_path / output_dir
    output_file_path = project_path / output_file
    
    # Update stats with output path
    stats["output_path"] = str(output_file_path)
    
    # Parse existing llms.txt file if provided
    existing_file_structure = None
    if existing_llms_file and update_descriptions_only:
        if existing_llms_file.startswith(('http://', 'https://')):
            # For remote file, we need to fetch it first
            try:
                from llmstxt_architect.loader import fetch_llms_txt_from_url, parse_existing_llms_file_content
                content = await fetch_llms_txt_from_url(existing_llms_file)
                # Parse content directly without saving to file
                file_lines = content.splitlines(True)  # Keep line endings
                _, existing_file_structure = parse_existing_llms_file_content(file_lines)
            except Exception as e:
                print(status_message(f"Error fetching remote llms.txt file: {str(e)}", "error"))
                raise
        else:
            # For local file
            _, existing_file_structure = parse_existing_llms_file(existing_llms_file)
    
    # Load all documents
    print(status_message("Loading and processing URLs...", "processing"))
    docs = await load_urls(urls, max_depth, extractor, existing_llms_file)
    stats["urls_processed"] = len(docs)
    
    # Initialize summarizer
    print(status_message(f"Initializing summarizer with {llm_name} via {llm_provider}...", "info"))
    summarizer = Summarizer(
        llm_name=llm_name,
        llm_provider=llm_provider,
        summary_prompt=summary_prompt,
        output_dir=str(summaries_path),
        blacklist_file=blacklist_file,
        existing_llms_file=existing_llms_file if update_descriptions_only else None,
    )
    
    # Run async post-initialization
    await summarizer.__post_init__()
    
    # Generate summaries
    try:
        print(status_message("Generating summaries...", "processing"))
        summaries = await summarizer.summarize_all(docs)
        stats["summaries_generated"] = len(summaries)
    except Exception as e:
        print(status_message(f"Summarization process was interrupted: {str(e)}", "error"))
        summaries = []  # Use empty list if interrupted
        stats["failed_urls"] = [doc.metadata.get('source', '') for doc in docs 
                              if doc.metadata.get('source', '') not in [s.split('](')[1].split(')')[0] for s in summaries]]
    finally:
        # Always generate the final output file, even if interrupted
        print(status_message("Generating final llms.txt file from all available summaries...", "processing"))
        
        # Call the appropriate method based on whether we're preserving structure
        if update_descriptions_only and existing_file_structure:
            summarizer.generate_structured_llms_txt(
                summaries, 
                str(output_file_path), 
                existing_file_structure
            )
        else:
            summarizer.generate_llms_txt(
                summaries, 
                str(output_file_path)
            )
        
        # Calculate total time
        stats["total_time"] = time.time() - start_time
        
        # Display final report
        print("\n" + status_message("Process completed!", "success"))
        print(generate_summary_report(stats))