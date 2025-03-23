"""
URL loading and document processing.
"""

from typing import Callable, List

from langchain_community.document_loaders import RecursiveUrlLoader
from langchain.schema import Document


async def load_urls(
    urls: List[str],
    max_depth: int = 5,
    extractor: Callable[[str], str] = None,
) -> List[Document]:
    """
    Load documents from URLs recursively.
    
    Args:
        urls: List of URLs to load
        max_depth: Maximum recursion depth
        extractor: Function to extract content from HTML
        
    Returns:
        List of loaded documents
    """
    docs = []
    
    for url in urls:
        loader = RecursiveUrlLoader(
            url,
            max_depth=max_depth,
            extractor=extractor,
        )

        # Load documents using lazy loading (memory efficient)
        docs_lazy = loader.lazy_load()

        # Load documents and track URLs
        for d in docs_lazy:
            docs.append(d)

    print(f"Loaded {len(docs)} documents from URLs.")
    print("\nLoaded URLs:")
    for i, doc in enumerate(docs):
        print(f"{i+1}. {doc.metadata.get('source', 'Unknown URL')}")
        
    return docs