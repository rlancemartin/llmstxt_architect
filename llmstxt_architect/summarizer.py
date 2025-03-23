"""
LLM-based summarization of web page content.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

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
    ) -> None:
        """
        Initialize the summarizer.
        
        Args:
            llm_name: Name of the LLM model to use
            llm_provider: Provider of the LLM
            summary_prompt: Prompt to use for summarization
            output_dir: Directory to save summaries
            blacklist_file: Path to a file containing blacklisted URLs (one per line)
        """
        self.llm_name = llm_name
        self.llm_provider = llm_provider
        self.summary_prompt = summary_prompt
        self.output_dir = Path(output_dir)
        self.log_file = self.output_dir / "summarized_urls.json"
        self.blacklist_file = blacklist_file
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize the LLM
        self.llm = self._init_llm()
        
        # Load the log of already summarized URLs
        self.summarized_urls = self._load_log()
        
        # Load blacklisted URLs
        self.blacklisted_urls = self._load_blacklist()
        
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
                    "Line 1: 'LLM should read this page when [2-3 specific scenarios]'\n"
                    "Line 2: '[Direct summary of main topics]'\n\n"
                    "FOLLOW THIS FORMAT PRECISELY. No additional text."
                )}
            ])
            
            summary = summary_response.content
            
            # Extract page title or use URL as fallback
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
        
        for doc in docs:
            try:
                summary = await self.summarize_document(doc)
                if summary:
                    summaries.append(summary)
                    # Periodically update llms.txt after each successful summary
                    if len(summaries) % 5 == 0:
                        print(f"Progress: {len(summaries)} documents summarized. Updating llms.txt...")
                        # Use a temporary path to avoid conflicts with the final output
                        temp_output = os.path.join(os.path.dirname(self.output_dir), "llms.txt")
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
        import re
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
            
        print(f"Generated {output_file} with {len(sorted_entries)} unique summaries sorted by URL.")
        if duplicates_removed > 0:
            print(f"Removed {duplicates_removed} duplicate entries (same URL with/without trailing slash or identical content).")
        if blacklisted_count > 0:
            print(f"Excluded {blacklisted_count} blacklisted URL entries.")