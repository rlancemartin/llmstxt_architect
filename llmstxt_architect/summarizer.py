"""
LLM-based summarization of web page content.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from langchain.chat_models import init_chat_model

class Summarizer:
    """Handles the summarization of web page content using specified LLM."""
    
    def __init__(
        self,
        llm_name: str,
        llm_provider: str,
        summary_prompt: str,
        output_dir: str = "summaries",
        blacklist_file: str = None,
        existing_llms_file: str = None,
    ) -> None:
        """
        Initialize the summarizer.
        
        Args:
            llm_name: Name of the LLM model to use
            llm_provider: Provider of the LLM
            summary_prompt: Prompt to use for summarization
            output_dir: Directory to save summaries
            blacklist_file: Path to a file containing blacklisted URLs (one per line)
            existing_llms_file: Path to an existing llms.txt file to preserve structure from
        """
        self.llm_name = llm_name
        self.llm_provider = llm_provider
        self.summary_prompt = summary_prompt
        self.output_dir = Path(output_dir)
        self.log_file = self.output_dir / "summarized_urls.json"
        self.blacklist_file = blacklist_file
        self.existing_llms_file = existing_llms_file
        self.url_titles = {}  # Map of URLs to their titles from existing file
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize the LLM
        self.llm = self._init_llm()
        
        # Load the log of already summarized URLs
        self.summarized_urls = self._load_log()
        
        # Load blacklisted URLs
        self.blacklisted_urls = self._load_blacklist()
        
        # Parse existing llms.txt file if provided - handled in __post_init__
        self.existing_llms_file = existing_llms_file
        
    async def __post_init__(self):
        """Async initialization that runs after __init__."""
        # Parse existing llms.txt file if provided
        if self.existing_llms_file:
            await self._parse_existing_file_titles()
        
    def _init_llm(self):
        """Initialize the LLM based on provider and model name."""
        return init_chat_model(model=self.llm_name, model_provider=self.llm_provider)
        
    def _load_log(self) -> Dict[str, str]:
        """Load the log of already summarized URLs."""
        if not self.log_file.exists():
            return {}
            
        with open(self.log_file, 'r') as f:
            return json.load(f)
            
    def _load_blacklist(self) -> List[str]:
        """Load blacklisted URLs from a file."""
        blacklisted_urls = []
        
        if self.blacklist_file and os.path.exists(self.blacklist_file):
            with open(self.blacklist_file, 'r') as f:
                # Read lines and strip whitespace, filter out empty lines and comments
                urls = [line.strip() for line in f.readlines()]
                urls = [url for url in urls if url and not url.startswith('#')]
                
                # Normalize URLs by removing trailing slashes
                blacklisted_urls = [url.rstrip('/') for url in urls]
                
            print(f"Loaded {len(blacklisted_urls)} blacklisted URLs from {self.blacklist_file}")
        
        return blacklisted_urls
            
    def _save_log(self) -> None:
        """Save the log of summarized URLs."""
        with open(self.log_file, 'w') as f:
            json.dump(self.summarized_urls, f, indent=2)
            
    def _get_summary_filename(self, url: str) -> str:
        """Generate a filename for the summary based on the URL."""
        # Create a valid filename from the URL
        from urllib.parse import urlparse
        parsed = urlparse(url)
        filename = f"{parsed.netloc}{parsed.path}".replace("/", "_")
        if not filename.endswith('.txt'):
            filename += '.txt'
        return filename
    
    async def _parse_existing_file_titles(self) -> None:
        """
        Parse the existing llms.txt file to extract URL to title mapping.
        This helps preserve titles when updating only descriptions.
        Can handle both local files and remote URLs.
        """
        url_pattern = re.compile(r'\[(.*?)\]\((https?://[^\s)]+)\)')
        
        try:
            # Check if the input is a URL or a local file path
            if self.existing_llms_file.startswith(('http://', 'https://')):
                # Handle remote URL
                from llmstxt_architect.loader import fetch_llms_txt_from_url
                try:
                    content = await fetch_llms_txt_from_url(self.existing_llms_file)
                    source_desc = f"remote URL: {self.existing_llms_file}"
                except Exception as e:
                    print(f"Error fetching titles from remote llms.txt file: {str(e)}")
                    return
            else:
                # Handle local file
                with open(self.existing_llms_file, 'r') as f:
                    content = f.read()
                source_desc = f"local file: {self.existing_llms_file}"
            
            # Extract titles from content
            matches = url_pattern.findall(content)
            
            for title, url in matches:
                self.url_titles[url] = title
                
            print(f"Extracted {len(self.url_titles)} URL titles from llms.txt ({source_desc})")
        except Exception as e:
            print(f"Error parsing URL titles from existing file: {str(e)}")
            
    async def summarize_document(self, doc) -> Optional[str]:
        """
        Summarize a document.
        
        Args:
            doc: Document to summarize
            
        Returns:
            Summary of the document
        """
        url = doc.metadata.get('source', '')
        
        # Normalize URL for comparison
        normalized_url = url.rstrip('/')
        
        # Check if URL is blacklisted
        if normalized_url in self.blacklisted_urls:
            print(f"Skipping blacklisted URL: {url}")
            return None
        
        # Check if already summarized
        if url in self.summarized_urls:
            print(f"Already summarized: {url}")
            
            # Return the summary from file
            summary_path = self.output_dir / self.summarized_urls[url]
            if summary_path.exists():
                with open(summary_path, 'r') as f:
                    return f.read()
            return None
            
        try:
            print(f"Summarizing: {url}")
            
            # Generate summary
            summary_response = self.llm.invoke([
                {"role": "system", "content": self.summary_prompt},
                {"role": "human", "content": (
                    f"Read and analyze this content: {doc.page_content}\n\n"
                    "Now, provide a summary EXACTLY in this format:\n"
                    "Line 1: 'LLM should read this page when (2-3 specific scenarios)'\n"
                    "Line 2: '(Direct summary of main topics)'\n\n"
                    "FOLLOW THIS FORMAT PRECISELY. No additional text. Use parentheses () not square brackets []."
                )}
            ])
            
            summary = summary_response.content
            
            # Extract page title or use URL as fallback
            # If we have a title from existing file, use that instead to preserve it
            if url in self.url_titles:
                title = self.url_titles[url]
            else:
                title = doc.metadata.get('title', url.split('/')[-1])
            
            # Format summary entry - ensure no extra newlines within the summary
            clean_summary = summary.replace('\n\n', ' ').replace('\n', ' ').strip()
            formatted_summary = f"[{title}]({url}): {clean_summary}\n\n"
            
            # Save individual summary
            filename = self._get_summary_filename(url)
            with open(self.output_dir / filename, 'w') as f:
                f.write(formatted_summary)
                
            # Update log
            self.summarized_urls[url] = filename
            self._save_log()
            
            return formatted_summary
            
        except Exception as e:
            print(f"Error summarizing {url}: {str(e)}")
            return None
            
    async def summarize_all(self, docs) -> List[str]:
        """
        Summarize all documents.
        
        Args:
            docs: List of documents to summarize
            
        Returns:
            List of summaries
        """
        summaries = []
        preserve_structure = self.existing_llms_file is not None and hasattr(self, 'file_structure')
        
        for doc in docs:
            try:
                summary = await self.summarize_document(doc)
                if summary:
                    summaries.append(summary)
                    # Periodically update llms.txt after each successful summary
                    if len(summaries) % 5 == 0:
                        update_mode = "structure-preserving" if preserve_structure else "sorted"
                        print(f"Progress: {len(summaries)} documents summarized. Generating {update_mode} llms.txt...")
                        
                        # Use a temporary path to avoid conflicts with the final output
                        temp_output = os.path.join(os.path.dirname(self.output_dir), "llms.txt")
                        
                        if preserve_structure:
                            self.generate_structured_llms_txt(summaries, temp_output, self.file_structure)
                        else:
                            self.generate_llms_txt(summaries, temp_output)
            except Exception as e:
                url = doc.metadata.get('source', 'unknown')
                print(f"Failed to summarize document {url}: {str(e)}")
                # Continue with the next document
                continue
                
        return summaries
        
    def generate_llms_txt(self, summaries: List[str], output_file: str = "llms.txt") -> None:
        """
        Generate the final llms.txt file from all summaries.
        
        Args:
            summaries: List of summaries from current run
            output_file: File to save to
        """
        # Collect all available summaries from the output directory with their URLs
        summary_entries = []
        
        # Pattern to extract URL from summary
        url_pattern = re.compile(r'\[(.*?)\]\((https?://[^\s)]+)\)')
        
        # First add all summaries from files
        for filename in os.listdir(self.output_dir):
            if filename.endswith('.txt') and filename != os.path.basename(output_file):
                file_path = os.path.join(self.output_dir, filename)
                with open(file_path, 'r') as f:
                    summary_content = f.read()
                    
                    # Extract URL from summary content
                    match = url_pattern.search(summary_content)
                    url = match.group(2) if match else filename  # Use URL or filename as fallback
                    
                    # Normalize URL by removing trailing slash if present
                    normalized_url = url.rstrip('/')
                    
                    # Store tuple of (normalized_url, content)
                    summary_entries.append((normalized_url, summary_content))
        
        # Group entries by normalized URL
        url_to_entries = {}
        for url, content in summary_entries:
            # Skip blacklisted URLs
            if url in self.blacklisted_urls:
                continue
                
            if url not in url_to_entries:
                url_to_entries[url] = []
            url_to_entries[url].append(content)
        
        # For each URL, select the best/most recent content
        # (We'll use the longest summary as a heuristic for "best")
        unique_entries = []
        for url, contents in url_to_entries.items():
            # Sort by length in descending order (longest first)
            contents.sort(key=len, reverse=True)
            # Take the first (longest) entry
            unique_entries.append((url, contents[0]))
        
        # Additional deduplication based on content
        final_entries = []
        seen_content = set()
        for url, content in unique_entries:
            # Skip exact duplicate content
            if content not in seen_content:
                final_entries.append((url, content))
                seen_content.add(content)
                
        # Sort by URL
        sorted_entries = sorted(final_entries, key=lambda x: x[0])
        
        # Write the sorted summaries to the output file
        with open(output_file, 'w') as f:
            for _, content in sorted_entries:
                f.write(content)
        
        # Get counts for logging
        total_files = sum(1 for f in os.listdir(self.output_dir) 
                          if f.endswith('.txt') and f != os.path.basename(output_file))
        duplicates_removed = total_files - len(sorted_entries)
        
        # Count blacklisted URLs that were in the summary files
        blacklisted_count = sum(1 for url, _ in summary_entries if url in self.blacklisted_urls)
        
        # Customize message based on context - are we in progress or final output
        is_progress_update = not output_file.endswith(os.path.basename(output_file))
        message_prefix = "Progress update:" if is_progress_update else "Generated"
            
        print(f"{message_prefix} {output_file} with {len(sorted_entries)} unique summaries sorted by URL.")
        if duplicates_removed > 0:
            print(f"Removed {duplicates_removed} duplicate entries (same URL with/without trailing slash or identical content).")
        if blacklisted_count > 0:
            print(f"Excluded {blacklisted_count} blacklisted URL entries.")
            
    def generate_structured_llms_txt(self, summaries: List[str], output_file: str, file_structure: List[str]) -> None:
        """
        Generate an llms.txt file that preserves the structure of the original file but updates descriptions.
        
        Args:
            summaries: List of summaries from current run
            output_file: File to save to
            file_structure: Original file structure as a list of lines
        """
        # Build a map of URLs to their updated summaries
        url_pattern = re.compile(r'\[(.*?)\]\((https?://[^\s)]+)\)')
        url_to_summary = {}
        
        # From newly generated summaries
        for summary in summaries:
            match = url_pattern.search(summary)
            if match:
                url = match.group(2)
                url_to_summary[url] = summary.strip()
        
        # From summary files in the output directory
        for filename in os.listdir(self.output_dir):
            if filename.endswith('.txt') and filename != os.path.basename(output_file):
                file_path = os.path.join(self.output_dir, filename)
                with open(file_path, 'r') as f:
                    content = f.read()
                    match = url_pattern.search(content)
                    if match:
                        url = match.group(2)
                        if url not in url_to_summary:  # Don't overwrite newer summaries
                            url_to_summary[url] = content.strip()
        
        # Create a new file with preserved structure but updated descriptions
        output_lines = []
        updated_count = 0
        preserved_count = 0
        
        for line in file_structure:
            # Check if line contains a URL that needs to be updated
            match = url_pattern.search(line)
            if match:
                url = match.group(2)
                # If we have an updated summary for this URL, use it
                if url in url_to_summary:
                    output_lines.append(url_to_summary[url] + "\n")
                    updated_count += 1
                else:
                    # Keep the original line if no update available
                    output_lines.append(line)
                    preserved_count += 1
            else:
                # Keep the original line for structure (headers, blank lines, etc.)
                output_lines.append(line)
        
        # Write the updated file
        with open(output_file, 'w') as f:
            f.writelines(output_lines)
        
        # Customize message based on context - are we in progress or final output
        is_progress_update = not output_file.endswith(os.path.basename(output_file))
        message_prefix = "Progress update:" if is_progress_update else "Generated"
            
        print(f"{message_prefix} {output_file} with preserved structure:")
        print(f"  - {updated_count} descriptions updated")
        print(f"  - {preserved_count} descriptions preserved (no updates available)")
        print(f"  - Original structure maintained (headers, spacing, ordering)")        
        
        # Only show detailed stats for final output, not progress updates
        if not is_progress_update:
            # Identify URLs in original file that were not updated
            original_urls = []
            for line in file_structure:
                match = url_pattern.search(line)
                if match:
                    original_urls.append(match.group(2))
                    
            not_updated = [url for url in original_urls if url not in url_to_summary]
            if not_updated:
                print(f"Warning: {len(not_updated)} URLs from original file were not updated:")
                for url in not_updated[:5]:  # Show first 5 only
                    print(f"  - {url}")
                if len(not_updated) > 5:
                    print(f"  - ... and {len(not_updated) - 5} more")