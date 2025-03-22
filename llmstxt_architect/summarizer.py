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
    ) -> None:
        """
        Initialize the summarizer.
        
        Args:
            llm_name: Name of the LLM model to use
            llm_provider: Provider of the LLM
            summary_prompt: Prompt to use for summarization
            output_dir: Directory to save summaries
        """
        self.llm_name = llm_name
        self.llm_provider = llm_provider
        self.summary_prompt = summary_prompt
        self.output_dir = Path(output_dir)
        self.log_file = self.output_dir / "summarized_urls.json"
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize the LLM
        self.llm = self._init_llm()
        
        # Load the log of already summarized URLs
        self.summarized_urls = self._load_log()
        
    def _init_llm(self):
        """Initialize the LLM based on provider and model name."""
        return init_chat_model(model=self.llm_name, model_provider=self.llm_provider)
        
    def _load_log(self) -> Dict[str, str]:
        """Load the log of already summarized URLs."""
        if not self.log_file.exists():
            return {}
            
        with open(self.log_file, 'r') as f:
            return json.load(f)
            
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
            summary = await self.summarize_document(doc)
            if summary:
                summaries.append(summary)
                
        return summaries
        
    def generate_llms_txt(self, summaries: List[str], output_file: str = "llms.txt") -> None:
        """
        Generate the final llms.txt file from summaries.
        
        Args:
            summaries: List of summaries to include
            output_file: File to save to
        """
        with open(output_file, 'w') as f:
            f.writelines(summaries)
            
        print(f"Generated {output_file} with {len(summaries)} summaries.")