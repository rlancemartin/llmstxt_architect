# LLMsTxt Architect

llms.txt is an emerging standard for communicating website contents to LLMs. This has potential to support RAG, allowing LLMs to reflect on llms.txt files [and then fetch pages](https://github.com/langchain-ai/mcpdoc) needed to accomplish tasks. However, there is a need to clearly design and build llms.txt files that communicate the purpose of each page to LLMs. 

This is a Python package that designs and builds [LLMs.txt](https://llmstxt.org/) files by extracting and summarizing web content using LLMs. Importantly, it gives the user control over the prompt to summarize pages, [the model provider and model](https://python.langchain.com/api_reference/langchain/chat_models/langchain.chat_models.base.init_chat_model.html) for summarization, the input pages to search, the search depth for recursive URL loader for each input page, and the website extractor (e.g., bs4, Markdownify, etc) for each page.

![llms_txt_architecture](https://github.com/user-attachments/assets/54e12c8d-ba6e-4739-aadb-07c1c5f028f0)

## Features

- [Recursively](https://python.langchain.com/docs/integrations/document_loaders/recursive_url/) crawl a user defined list of web sites to a user-defined depth
- Extract content from each page with a user-defined extractor
- Summarize content using user-defined LLM selected from this [list of providers](https://python.langchain.com/api_reference/langchain/chat_models/langchain.chat_models.base.init_chat_model.html)
- Robust fault tolerance with checkpoints to resume after interruptions or timeouts
- Periodic progress updates with intermediate results saved during processing
- Skip already processed pages to efficiently resume interrupted runs
- Generate a formatted LLMs.txt file containing all summaries sorted by URL
- Deduplicate summaries to ensure clean output

## Quickstart

```bash
# Clone the repository
git clone https://github.com/rlancemartin/llmstxt_architect.git
cd llmstxt-architect
```

You can run the package directly [with uvx](https://github.com/astral-sh/uv):

```bash
# On macOS and Linux.
curl -LsSf https://astral.sh/uv/install.sh | sh
# On Windows.
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# Run the command (with example parameters)
uvx --with-editable /path/to/llmstxt_architect llmstxt-architect \
    --urls https://langchain-ai.github.io/langgraph/concepts/ \
    --max-depth 2 \
    --llm-name claude-3-7-sonnet-latest \
    --llm-provider anthropic \
    --project-dir langgraph_docs
```

Without uvx, you can install the package in development mode:

```bash
# Install in development mode
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

```bash
# Basic usage
llmstxt-architect --urls https://example.com

# Advanced usage
llmstxt-architect \
    --urls https://example1.com https://example2.com \
    --max-depth 3 \
    --llm-name claude-3-7-sonnet-latest \
    --llm-provider anthropic \
    --project-dir my_project \
    --output-dir my_summaries \
    --output-file my_llms.txt
```

You can also use the Python API:

```python
import asyncio
from llmstxt_architect.main import generate_llms_txt

urls = [
    "https://langchain-ai.github.io/langgraph/concepts/",
    "https://langchain-ai.github.io/langgraph/how-tos/"
]

asyncio.run(generate_llms_txt(
    urls=urls,
    max_depth=1,
    llm_name="claude-3-7-sonnet-latest",
    llm_provider="anthropic",
    project_dir="langgraph_docs",
    output_dir="summaries",
    output_file="llms.txt"
))
```

## Resuming Interrupted Runs

If processing is interrupted (e.g., due to timeout or network issues), simply run the same command again. The tool will:

1. Skip already processed pages
2. Resume processing from where it left off
3. Periodically update the output file with all summaries (every 5 documents)
4. Generate a complete, sorted llms.txt file with all summaries at the end

This is particularly useful when processing large websites or using slower API-based LLMs where timeouts may occur:

```bash
# Run the same command after an interruption
llmstxt-architect \
    --urls https://example1.com https://example2.com \
    --max-depth 3 \
    --llm-name claude-3-7-sonnet-latest
```

## Fault Tolerance and Performance Enhancements

The tool includes several features to handle large-scale documentation processing:

- **Interruption Handling**: Even if the process is interrupted by timeouts or errors, progress is preserved
- **Incremental Updates**: The output file is updated periodically during processing (every 5 successful summaries)
- **URL Deduplication**: Summaries for pages that have already been processed are not regenerated
- **Content Deduplication**: Duplicate summaries are filtered out from the final output
- **Organized Output**: Summaries in the final llms.txt file are sorted by URL for better readability
- **Exception Handling**: Errors during summarization of individual pages don't halt the entire process
- **Progress Tracking**: Clear console output shows which pages have been processed and skipped

These enhancements make the tool suitable for processing large documentation websites with hundreds of pages, even when using rate-limited API-based LLM providers.

## License

MIT
