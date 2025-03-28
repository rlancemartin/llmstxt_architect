# LLMsTxt Architect

`llms.txt` is an emerging standard for communicating website contents to LLMs. It is a markdown file listing URLs within a site and their *descriptions*, giving LLMs a guide [to help fetch and read pages](https://github.com/langchain-ai/mcpdoc) in order to accomplish tasks. LLMsTxt Architect is a Python package that builds [LLMs.txt](https://llmstxt.org/) automatically, using LLMs to automate the process. It can start with a list of URLs or an existing `llms.txt` file, and a user can specify the LLM provider, model, prompt used to generate description along with other options.

![llms_txt_architecture](https://github.com/user-attachments/assets/54e12c8d-ba6e-4739-aadb-07c1c5f028f0)

## Quickstart

Test with Anthropic's Claude 3.7 Sonnet (be sure `ANTHROPIC_API_KEY` is set):
```shell
$ curl -LsSf https://astral.sh/uv/install.sh | sh
$ uvx --from llmstxt-architect llmstxt-architect --urls https://langchain-ai.github.io/langgraph/concepts --max-depth 1 --llm-name claude-3-7-sonnet-latest --llm-provider anthropic --project-dir tmp
```

Test with a local model e.g., Llama 3.2 via Ollama (be sure [Ollama is installed](https://ollama.com/download) and the model is pulled):
```shell
$ ollama pull llama3.2:latest
$ uvx --from llmstxt-architect llmstxt-architect --urls https://langchain-ai.github.io/langgraph/concepts --max-depth 1 --llm-name llama3.2:latest --llm-provider ollama --project-dir tmp
```

Both will use [RecursiveURLLoader](https://python.langchain.com/docs/integrations/document_loaders/recursive_url/) to recursively crawl the URLs to a depth of 1 and use an LLM to summarize all of the resulting pages. The results will be saved to the `tmp` directory in the current working directory with a resulting `llms.txt` file along with a `summaries` folder of individual page summaries and a `summarized_urls.json` checkpoint file with the URLs that have already been processed.

### Pip  

You can also install the package with pip.

#### CLI

```bash
$ python3 -m venv .venv
$ source .venv/bin/activate  # On Windows: .venv\Scripts\activate
$ pip install llmstxt-architect
$ llmstxt-architect --urls https://langchain-ai.github.io/langgraph/concepts --max-depth 1 --llm-name claude-3-7-sonnet-latest --llm-provider anthropic --project-dir test
```

#### Python API (Jupyter/IPython notebooks, etc.)

```python
import asyncio
from llmstxt_architect.main import generate_llms_txt

await generate_llms_txt(
      urls=["https://langchain-ai.github.io/langgraph/concepts"],
      max_depth=1,
      llm_name="claude-3-7-sonnet-latest",
      llm_provider="anthropic",
      project_dir="test",
  )
```

#### Python API in a script

```python
import asyncio
from llmstxt_architect.main import generate_llms_txt

async def main():
      await generate_llms_txt(
          urls=["https://langchain-ai.github.io/langgraph/concepts"],
          max_depth=1,
          llm_name="claude-3-7-sonnet-latest",
          llm_provider="anthropic",
          project_dir="test_script",
      )

if __name__ == "__main__":
      asyncio.run(main())
``` 

## Configurations

The full list of configurations is available in the [CLI help](https://github.com/langchain-ai/llmstxt-architect/blob/main/llmstxt_architect/cli.py).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--urls` | List[str] | (Required if not using `--existing-llms-file`) | List of URLs to process |
| `--existing-llms-file` | str | (Required if not using `--urls`) | Path to an existing llms.txt file to extract URLs from and update |
| `--update-descriptions-only` | flag | False | Update only descriptions in existing llms.txt while preserving structure and URL order |
| `--max-depth` | int | 5 | Maximum recursion depth for URL crawling |
| `--llm-name` | str | "claude-3-sonnet-20240229" | LLM model name |
| `--llm-provider` | str | "anthropic" | LLM provider |
| `--project-dir` | str | "llms_txt" | Main project directory to store all outputs |
| `--output-dir` | str | "summaries" | Directory within project-dir to save individual summaries |
| `--output-file` | str | "llms.txt" | Output file name for combined summaries |
| `--summary-prompt` | str | "You are creating a summary..." | Prompt to use for summarization |
| `--blacklist-file` | str | None | Path to a file containing blacklisted URLs to exclude (one per line) |
| `--extractor` | str | "default" | HTML content extractor to use (choices: "default" (Markdownify), "bs4" (BeautifulSoup)) |

### URLs

You can pass multiple URLs that you want to use as the basis for the `llms.txt` file. The [RecursiveURLLoader](https://python.langchain.com/docs/integrations/document_loaders/recursive_url/) will crawl *each* URL to the maximum depth as specified by `--max-depth` and use an LLM to summarize all of the resulting pages.

```bash
---urls https://langchain-ai.github.io/langgraph/concepts https://langchain-ai.github.io/langgraph/tutorials
`--max-depth 1
```

### Existing llms.txt File

If you have an existing `llms.txt` file (locally or remotely), you can extract the URLs from it and generates a completely new `llms.txt` with freshly generated descriptions. The original file's structure (headers, ordering, etc.) is *not preserved* by default. 

```bash
# Use a local file
llmstxt-architect --existing-llms-file path/to/llms.txt

# Or use a remote file
llmstxt-architect --existing-llms-file https://example.com/llms.txt
```

### Preserving llms.txt Structure While Updating Descriptions

If you have an `llms.txt` file that you want to preserve the structure of, you can use the `--update-descriptions-only` flag. This will preserve all structural elements (headers, subheaders, newlines) and the exact ordering of URLs while only updating the descriptions. It also maintains the exact ordering of URLs, preserves titles from the original file, and only updates the descriptions for each URL. This is particularly useful when the existing `llms.txt` file has a carefully curated structure that you want to maintain and you want to improve descriptions without changing the organization.

```bash
# Use a local file
llmstxt-architect --existing-llms-file path/to/llms.txt --update-descriptions-only

# Or use a remote file
llmstxt-architect --existing-llms-file https://example.com/llms.txt --update-descriptions-only
```

### Model

The package uses LLMs for generating descriptions for each URL in the `llms.txt` file. By default, it's configured for Anthropic's Claude models, but you can easily select from many different [LLM providers](https://python.langchain.com/api_reference/langchain/chat_models/langchain.chat_models.base.init_chat_model.html):

#### Hosted LLMs (OpenAI, Anthropic, etc.):
1. Install the corresponding package (e.g., `pip install langchain-openai`)
2. Set the appropriate API key (e.g., `export OPENAI_API_KEY=your_api_key_here`)
3. Specify the provider and model with the `--llm-provider` and `--llm-name` options, e.g., using the [LLM provider names as shown here](https://python.langchain.com/api_reference/langchain/chat_models/langchain.chat_models.base.init_chat_model.html)
```
--llm-provider openai --llm-name gpt-4o
```

#### Local Models with Ollama:
1. [Install Ollama](https://ollama.com/download)
2. Pull your desired model (e.g., `ollama pull llama3.2:latest`)
3. Install the package: `pip install langchain-ollama`
4. Specify the provider and model with the `--llm-provider` and `--llm-name` options, e.g.,
```
--llm-provider ollama --llm-name llama3.2:latest
```

### Prompt

By default, it uses this prompt (see [llmstxt_architect/cli.py](https://github.com/langchain-ai/llmstxt-architect/blob/main/llmstxt_architect/cli.py)):
```bash
"You are creating a summary for a webpage to be used in a llms.txt file "
"to help LLMs in the future know what is on this page. Produce a concise "
"summary of the key items on this page and when an LLM should access it."
```

You can override this prompt with the `--summary-prompt` option, e.g.,
```bash
--summary-prompt "You are creating a summary for a webpage to be used in a llms.txt file ..."
```

### Extractor

You can specify which built-in extractor to use with the `--extractor` CLI option:

```bash
# Use BeautifulSoup extractor
llmstxt-architect --urls https://example.com --extractor bs4

# Use default Markdownify extractor
llmstxt-architect --urls https://example.com --extractor default
```

For advanced use cases, you can override the default extractor in the Python API with your own custom extractor function, e.g.,
```python 

def my_extractor(html: str) -> str:
    """
    Extract content from HTML using xxx.
    
    Args:
        html (str): The HTML content to extract from
        
    Returns:
        content (str): Extracted text content
    """
    
    # TODO: Implement your custom extractor here
    
    return content

import asyncio
from llmstxt_architect.main import generate_llms_txt

await generate_llms_txt(
      urls=["https://langchain-ai.github.io/langgraph/concepts"],
      max_depth=1,
      llm_name="claude-3-7-sonnet-latest",
      llm_provider="anthropic",
      project_dir="test",
      extractor=my_extractor
  )
```

### Project directory, output directory, and output file

LLMsTxt Architect provides checkpoint functionality to handle interruptions during processing. It creates a project directory to store all outputs. While running, it saves each page's summary to the output directory and updates a checkpoint file (summarized_urls.json) to track which pages have been processed. If the process is interrupted, you can simply run the same command again to resume from where it left off.

- **Progress tracker**: `<project_dir>/<output_dir>/summarized_urls.json`
- **Individual summaries**: `<project_dir>/<output_dir>/<url>.txt`
- **Combined output llms.txt file**: `<project_dir>/<output_file>`

All paths are configurable with: 
```bash
--project-dir, --output-dir, --output-file      
```

If processing is interrupted (timeout, network issues, etc.), simply run the same command again. The tool will:

1. Skip already processed pages using the checkpoint file
2. Resume processing from where it left off
3. Update the output file periodically (every 5 documents)
4. Generate a complete, sorted llms.txt file upon completion

This is particularly valuable when processing large websites or when using rate-limited API-based LLMs.

### URL Blacklisting

You can exclude specific URLs from your `llms.txt` file by providing a blacklist file:

```bash
# Create a blacklist file
cat > blacklist.txt << EOF
# Deprecated pages
https://example.com/old-version/
https://example.com/beta-feature

# Pages with known issues
https://example.com/broken-page
EOF
```

The name of the blacklist file is configurable with the `--blacklist-file` option.

The blacklist file should contain one URL per line. Empty lines and lines starting with `#` are ignored. The tool will:

1. Skip summarization of blacklisted URLs during crawling
2. Filter out blacklisted URLs from the final llms.txt file
3. Report how many blacklisted URLs were excluded

This is useful for excluding deprecated documentation, beta features, or pages with known issues.
 
## License

MIT
