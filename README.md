# LLMsTxt Architect

llms.txt is an emerging standard for communicating website contents to LLMs, often as a markdown file listing URLs within a site and their descriptions. This has potential to support context retrieval, allowing LLMs to reflect on llms.txt files [and then fetch / read pages](https://github.com/langchain-ai/mcpdoc) needed to accomplish tasks. However, this means that llms.txt files must clearly communicate the purpose of each URL so that the LLM knows which pages to fetch.

LLMsTxt Architect is a Python package that designs and builds [LLMs.txt](https://llmstxt.org/) files by extracting and summarizing web content using LLMs. Importantly, it gives the user control over the prompt to summarize pages, [the model provider and model](https://python.langchain.com/api_reference/langchain/chat_models/langchain.chat_models.base.init_chat_model.html) for summarization, the input pages to search, the search depth for recursive URL loader for each input page, and the website extractor (e.g., bs4, Markdownify, etc) for each page.

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

### API Keys Setup

The package uses LLMs for summarization. By default, it's configured for Anthropic's Claude models:

```bash
# Set your Anthropic API key
export ANTHROPIC_API_KEY=your_api_key_here
# On Windows: $env:ANTHROPIC_API_KEY="your_api_key_here"
```

To use a different [LLM provider](https://python.langchain.com/api_reference/langchain/chat_models/langchain.chat_models.base.init_chat_model.html):

#### Hosted LLMs (OpenAI, Anthropic, etc.):
1. Install the corresponding package (e.g., `pip install langchain-openai`)
2. Set the appropriate API key (e.g., `OPENAI_API_KEY`)
3. Specify the provider and model with the `--llm-provider` and `--llm-name` options

#### Local Models with Ollama:
1. [Install Ollama](https://ollama.com/download)
2. Pull your desired model (e.g., `ollama pull llama3.2:latest`)
3. Install the package: `pip install langchain-ollama`
4. Run with these options:
   ```
   --llm-provider ollama --llm-name llama3.2:latest
   ```
   No API key is required for local models!

### Running with uvx

You can run the package directly [with uvx](https://github.com/astral-sh/uv) (recommended):

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

### Installing the Package

Without uvx, you can install the package in development mode:

```bash
# Install in development mode
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"  # This installs langchain-anthropic by default
```

To use a different LLM provider, install the additional packages:

```bash
# For OpenAI
pip install langchain-openai

# For Cohere
pip install langchain-cohere

# For other providers
# See: https://python.langchain.com/api_reference/langchain/chat_models/langchain.chat_models.base.init_chat_model.html
```

```bash
# Basic usage
llmstxt-architect --urls https://example.com

# Advanced usage with Anthropic
llmstxt-architect \
    --urls https://example1.com https://example2.com \
    --max-depth 3 \
    --llm-name claude-3-7-sonnet-latest \
    --llm-provider anthropic \
    --project-dir my_project \
    --output-dir my_summaries \
    --output-file my_llms.txt \
    --blacklist-file blacklist.txt
    
# Using with local Ollama models
llmstxt-architect \
    --urls https://example.com \
    --max-depth 2 \
    --llm-name llama3.2:latest \
    --llm-provider ollama \
    --project-dir local_model_summaries
```

You can also use the Python API:

```python
import asyncio
from llmstxt_architect.main import generate_llms_txt

urls = [
    "https://langchain-ai.github.io/langgraph/concepts/",
    "https://langchain-ai.github.io/langgraph/how-tos/"
]

# With Anthropic (requires ANTHROPIC_API_KEY)
asyncio.run(generate_llms_txt(
    urls=urls,
    max_depth=1,
    llm_name="claude-3-7-sonnet-latest",
    llm_provider="anthropic",
    project_dir="langgraph_docs",
    output_dir="summaries",
    output_file="llms.txt",
    blacklist_file="blacklist.txt" # Optional: path to file with URLs to exclude
))

# With Ollama (local models, no API key needed)
asyncio.run(generate_llms_txt(
    urls=urls,
    max_depth=1,
    llm_name="llama3.2:latest",
    llm_provider="ollama",
    project_dir="langgraph_docs_local"
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

## URL Blacklisting

You can exclude specific URLs from your llms.txt file by providing a blacklist file:

```bash
# Create a blacklist file
cat > blacklist.txt << EOF
# Deprecated pages
https://example.com/old-version/
https://example.com/beta-feature

# Pages with known issues
https://example.com/broken-page
EOF

# Run with blacklist
llmstxt-architect \
    --urls https://example.com \
    --blacklist-file blacklist.txt
```

The blacklist file should contain one URL per line. Empty lines and lines starting with `#` are ignored. The tool will:

1. Skip summarization of blacklisted URLs during crawling
2. Filter out blacklisted URLs from the final llms.txt file
3. Report how many blacklisted URLs were excluded

This is useful for excluding deprecated documentation, beta features, or pages with known issues.

## Fault Tolerance and Performance Enhancements

The tool includes several features to handle large-scale documentation processing:

- **Interruption Handling**: Even if the process is interrupted by timeouts or errors, progress is preserved
- **Incremental Updates**: The output file is updated periodically during processing (every 5 successful summaries)
- **URL Deduplication**: Summaries for pages that have already been processed are not regenerated
- **Content Deduplication**: Duplicate summaries are filtered out from the final output
- **Organized Output**: Summaries in the final llms.txt file are sorted by URL for better readability
- **URL Blacklisting**: Support for excluding specific URLs via a blacklist file
- **Exception Handling**: Errors during summarization of individual pages don't halt the entire process
- **Progress Tracking**: Clear console output shows which pages have been processed and skipped

These enhancements make the tool suitable for processing large documentation websites with hundreds of pages, even when using rate-limited API-based LLM providers.

## License

MIT
