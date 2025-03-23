"""
Content extraction utilities for web pages.
"""

import re

from bs4 import BeautifulSoup
from markdownify import markdownify

def bs4_extractor(html: str) -> str:
    """
    Extract content from HTML using BeautifulSoup.
    
    Args:
        html: The HTML content to extract from
        
    Returns:
        Extracted text content
    """
    soup = BeautifulSoup(html, "lxml")
    
    # Target the main article content for LangGraph documentation 
    main_content = soup.find("article", class_="md-content__inner")
    
    # If found, use that, otherwise fall back to the whole document
    content = main_content.get_text() if main_content else soup.text
    
    # Clean up whitespace
    content = re.sub(r"\n\n+", "\n\n", content).strip()
    
    return content


def default_extractor(html: str) -> str:
    """
    Extract content from HTML and convert to markdown.
    
    Args:
        html: The HTML content to extract from
        
    Returns:
        Markdown converted content
    """
    result = markdownify(html)
    return str(result)