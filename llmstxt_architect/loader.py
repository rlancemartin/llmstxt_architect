"""
URL loading and document processing.
"""

import asyncio
import httpx
import re
import time
from collections import OrderedDict
from typing import Callable, Dict, List, Optional, Tuple, Set
from urllib.parse import urlparse

from langchain_community.document_loaders import RecursiveUrlLoader
from langchain.schema import Document


async def load_urls(
    urls: List[str],
    max_depth: int = 5,
    extractor: Callable[[str], str] = None,
    existing_llms_file: Optional[str] = None,
) -> List[Document]:
    """
    Load documents from URLs.
    
    Args:
        urls: List of URLs to load
        max_depth: Maximum recursion depth (only used for recursive loading)
        extractor: Function to extract content from HTML
        existing_llms_file: Path to an existing llms.txt file to extract URLs from (can be local path or URL)
        
    Returns:
        List of loaded documents
    """
    # If an existing llms.txt file is provided, extract URLs from it
    if existing_llms_file:
        urls_from_file = await extract_urls_from_llms_file(existing_llms_file)
        if urls_from_file:
            urls = urls_from_file
    
    docs = []
    processed_count = 0
    total_urls = len(urls)
    
    # Use direct URL loading for existing llms.txt files (more efficient)
    if existing_llms_file:
        docs = await load_urls_directly(urls, extractor)
    else:
        # Use recursive loader for standard URL crawling
        for url in urls:
            try:
                loader = RecursiveUrlLoader(
                    url,
                    max_depth=max_depth,
                    extractor=extractor,
                )

                # Load documents using lazy loading (memory efficient)
                docs_lazy = loader.lazy_load()

                # Load documents and track URLs
                url_docs = []
                for d in docs_lazy:
                    url_docs.append(d)
                    
                docs.extend(url_docs)
                
                # Update progress
                processed_count += 1
                if processed_count % 10 == 0 or processed_count == total_urls:
                    print(f"Progress: {processed_count}/{total_urls} URLs processed")
                    
            except Exception as e:
                print(f"Error loading URL {url}: {str(e)}")
                continue

    print(f"\nLoaded {len(docs)} documents.")
    
    return docs


async def load_urls_directly(urls: List[str], extractor: Callable[[str], str] = None) -> List[Document]:
    """
    Load URLs directly without recursion. More efficient for existing llms.txt files.
    
    Args:
        urls: List of URLs to load
        extractor: Function to extract content from HTML
        
    Returns:
        List of Document objects
    """
    docs = []
    errors = []
    successful = 0
    duplicates_avoided = 0
    
    # Track URLs we've already processed to avoid duplicates
    # Use normalized URLs for comparison
    processed_urls = set()
    
    # Configure client with reasonable defaults
    timeout = httpx.Timeout(30.0)  # 30 seconds
    limits = httpx.Limits(max_connections=10)  # Limit concurrent connections
    
    # Process URLs in batches to avoid overwhelming the system
    batch_size = 10
    
    # Deduplicate URLs before processing
    unique_batches = []
    for i in range(0, len(urls), batch_size):
        batch = urls[i:i+batch_size]
        unique_batch = []
        
        for url in batch:
            normalized_url = normalize_url(url)
            if normalized_url not in processed_urls:
                unique_batch.append(url)
                processed_urls.add(normalized_url)
            else:
                duplicates_avoided += 1
                
        if unique_batch:
            unique_batches.append(unique_batch)
    
    # Report deduplication results
    if duplicates_avoided > 0:
        print(f"Avoiding {duplicates_avoided} duplicate URLs during loading")
    
    print(f"Loading {len(processed_urls)} unique URLs (batch size: {batch_size})...")
    
    # Process each batch of unique URLs
    for batch in unique_batches:
        batch_docs = []
        
        # Create tasks to fetch URLs concurrently
        async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
            tasks = []
            for url in batch:
                tasks.append(fetch_url(client, url, extractor))
            
            # Process the batch concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result, url in zip(results, batch):
                if isinstance(result, Exception):
                    errors.append((url, str(result)))
                    continue
                
                if result:
                    batch_docs.append(result)
                    successful += 1
        
        # Add batch results to main list
        docs.extend(batch_docs)
        
        # Report progress
        processed_so_far = min(successful + len(errors), len(processed_urls))
        print(f"Progress: {processed_so_far}/{len(processed_urls)} unique URLs processed")
    
    # Report final results
    print(f"Successfully loaded {successful} URLs")
    if errors:
        print(f"Failed to load {len(errors)} URLs")
    if duplicates_avoided > 0:
        print(f"Avoided processing {duplicates_avoided} duplicate URLs (token saving)")
    
    return docs


async def fetch_url(client: httpx.AsyncClient, url: str, extractor: Callable[[str], str]) -> Optional[Document]:
    """
    Fetch a single URL and convert it to a Document.
    
    Args:
        client: HTTPX client to use
        url: URL to fetch
        extractor: Function to extract content from HTML
        
    Returns:
        Document object or None if failed
    """
    try:
        # Add a small delay to avoid hammering servers
        await asyncio.sleep(0.1)
        
        # Fetch URL
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()
        
        # Extract page title
        title = extract_title(response.text) or url.split('/')[-1]
        
        # Extract content
        if extractor:
            content = extractor(response.text)
        else:
            content = response.text
        
        # Create document
        return Document(
            page_content=content,
            metadata={
                "source": url,
                "title": title
            }
        )
    except Exception as e:
        print(f"Error fetching {url}: {str(e)}")
        return None


def extract_title(html_content: str) -> Optional[str]:
    """Extract title from HTML content."""
    title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
    if title_match:
        return title_match.group(1).strip()
    return None


async def extract_urls_from_llms_file(file_path: str) -> List[str]:
    """
    Extract URLs from an existing llms.txt file, removing duplicates while preserving order.
    Can handle both local file paths and URLs.
    
    Args:
        file_path: Path to the llms.txt file or URL
        
    Returns:
        List of URLs found in the file, deduplicated but order preserved
    """
    # Use OrderedDict to preserve order while deduplicating
    unique_urls = OrderedDict()
    url_pattern = re.compile(r'\[(.*?)\]\((https?://[^\s)]+)\)')
    
    try:
        # Check if the input is a URL or a local file path
        if file_path.startswith(('http://', 'https://')):
            # Handle URL
            content = await fetch_llms_txt_from_url(file_path)
            source_desc = f"remote URL: {file_path}"
        else:
            # Handle local file
            with open(file_path, 'r') as f:
                content = f.read()
            source_desc = f"local file: {file_path}"
        
        # Parse URLs from content
        matches = url_pattern.findall(content)
        
        # Process URLs, normalizing and deduplicating
        for match in matches:
            url = match[1]
            normalized_url = normalize_url(url)
            if normalized_url not in unique_urls:
                unique_urls[normalized_url] = url
        
        deduplicated_urls = list(unique_urls.values())
        
        # Report results
        total_urls = len(matches)
        unique_count = len(deduplicated_urls)
        print(f"Extracted {total_urls} URLs from existing llms.txt ({source_desc})")
        if total_urls > unique_count:
            print(f"Removed {total_urls - unique_count} duplicate URLs, {unique_count} unique URLs remaining")
            
    except Exception as e:
        print(f"Error reading existing llms.txt: {str(e)}")
        deduplicated_urls = []
        
    return deduplicated_urls


async def fetch_llms_txt_from_url(url: str) -> str:
    """
    Fetch llms.txt content from a URL.
    
    Args:
        url: URL to fetch llms.txt from
        
    Returns:
        Content of the llms.txt file as string
    """
    try:
        print(f"Fetching llms.txt from remote URL: {url}")
        timeout = httpx.Timeout(30.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            return response.text
    except Exception as e:
        raise Exception(f"Failed to fetch llms.txt from URL {url}: {str(e)}")


def normalize_url(url: str) -> str:
    """
    Normalize URL for comparison and deduplication.
    
    Args:
        url: URL to normalize
        
    Returns:
        Normalized URL
    """
    # Remove trailing slash if present
    normalized = url.rstrip('/')
    
    # Convert to lowercase for better matching
    normalized = normalized.lower()
    
    # Further normalization can be added here (e.g., removing www, query params, etc.)
    
    return normalized


def parse_existing_llms_file(file_path: str) -> Tuple[Dict[str, str], List[str]]:
    """
    Parse an existing llms.txt file to extract URLs, their descriptions,
    and overall file structure (headers, newlines, etc.).
    
    Args:
        file_path: Path to the llms.txt file
        
    Returns:
        Tuple containing:
            - Dictionary mapping URLs to their descriptions
            - List of file content lines to preserve structure
    """
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        return parse_existing_llms_file_content(lines, f"local file: {file_path}")
    except Exception as e:
        print(f"Error parsing existing llms.txt file: {str(e)}")
        return {}, []


def parse_existing_llms_file_content(lines: List[str], source_desc: str = "content") -> Tuple[Dict[str, str], List[str]]:
    """
    Parse content of an llms.txt file to extract URLs, their descriptions,
    and overall file structure (headers, newlines, etc.).
    
    Args:
        lines: List of lines from the llms.txt content
        source_desc: Description of the source for reporting
        
    Returns:
        Tuple containing:
            - Dictionary mapping URLs to their descriptions
            - List of file content lines to preserve structure
    """
    url_to_description = {}
    file_structure = []
    url_pattern = re.compile(r'\[(.*?)\]\((https?://[^\s)]+)\)')
    
    for line in lines:
        file_structure.append(line)
        line_stripped = line.strip()
        
        # Skip empty lines
        if not line_stripped:
            continue
            
        # Check if line contains a URL
        match = url_pattern.search(line_stripped)
        if match:
            title = match.group(1)
            url = match.group(2)
            
            # Extract description (everything after the URL and colon)
            description_start = line_stripped.find(':', match.end())
            if description_start != -1:
                description = line_stripped[description_start + 1:].strip()
                url_to_description[url] = description
    
    print(f"Parsed {len(url_to_description)} URL descriptions from existing llms.txt ({source_desc})")
    
    return url_to_description, file_structure