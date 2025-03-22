# LLMsTxt Architect

llms.txt is an emerging standard for communicating website contents to LLMs. This has great potential to support RAG, [allowing LLMs to reflect on llms.txt files](https://github.com/langchain-ai/mcpdoc) to find pages needed to  answer questions or accomplish tasks. However, there is a need to clearly design and build llms.txt files that communicate the purpose of each page to LLMs. 

This is a simple Python package that designs and builds [LLMs.txt](https://llmstxt.org/) files by extracting and summarizing web content using LLMs. It features 
an easily configurable prompt, allowing the user to control how each page is summarized, and can be configured to [use many different LLMs](https://python.langchain.com/api_reference/langchain/chat_models/langchain.chat_models.base.init_chat_model.html) as well as custom extractors.

## Features

- [Recursively](https://python.langchain.com/docs/integrations/document_loaders/recursive_url/) crawl a user defined list of web sites to a user-defined depth
- Extract content from each page with a user-defined extractor
- Summarize content using using user-defined LLM selected from this [list of providers](https://python.langchain.com/api_reference/langchain/chat_models/langchain.chat_models.base.init_chat_model.html)
- Track progress with checkpoints to resume after interruptions
- Generate a formatted LLMs.txt file containing all summaries

## Installation

```bash
# Clone the repository
git clone https://github.com/username/llmstxt-architect.git
cd llmstxt-architect

# Install in development mode
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

## Usage

### Command Line

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

### Using with uvx

You can also run the package directly with uvx without installing it:

```bash
uvx --with-editable /path/to/llmstxt_architect llmstxt-architect \
    --urls https://langchain-ai.github.io/langgraph/concepts/ \
    --max-depth 2 \
    --llm-name claude-3-7-sonnet-latest \
    --llm-provider anthropic \
    --project-dir langgraph_docs
```

### Python API

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

## License

MIT