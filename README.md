# 🔍 AiQuery
## A self-hosted (local) agentic AI with web search capability

A robust, autonomous web search assistant powered by **Ollama**, **DuckDuckGo**, and the **PocketFlow** framework [1]. It reasons, refines its queries, and critiques its own answers to ensure accuracy.

## Features

-   **Autonomous Query Generation**: The LLM formulates its own optimized search terms based on your question.
-   **Iterative Search Loop**: If initial results are insufficient, it automatically tries different keywords.
-   **Accumulative Memory**: Remembers results from previous search attempts to answer complex comparative questions.
-   **Self-Critique & Review**: Each answer is reviewed by a "critique bot" to ensure it meets quality standards.
-   **Multiple Interfaces**: Professional **CLI** with timing reports and a modern **Web GUI** with progress tracking.
-   **Local & Private**: Uses local LLMs via Ollama—no API keys required for the model.
-   **Clean & Silent**: Suppresses browser warnings and uses ranked snippets for better accuracy.

## Architecture vs. PocketFlow Examples

While the official PocketFlow repository includes a `tool-search` cookbook [2], this project takes a more advanced approach:

| Feature | PocketFlow Cookbook | AiQuery |
| :--- | :--- | :--- |
| **Workflow** | Linear (`Search -> Analyze`) | Iterative Loop (`QueryGen -> Search -> Rel -> Answer -> Review`) |
| **Search Tool** | SerpAPI (Paid API Key) | DuckDuckGo (Free & No Key) |
| **Logic** | Single-step extraction | Multi-step refinement with feedback loops |
| **Validation** | None (direct analysis) | Self-critique node with quality scoring |

## Installation

### 1. Prerequisite: Ollama
Ensure [Ollama](https://ollama.com/) is installed and the model is pulled:
```bash
ollama pull llama3.2:1B
```

### 2. Virtual Environment Setup
We recommend using a virtual environment for better dependency isolation:
```bash
# Create the environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Copy the template and configure your environment variables:
```bash
cp .env.template .env
```

| Parameter | Purpose | Necessity |
| :--- | :--- | :--- |
| `OLLAMA_HOST` | The API address of your Ollama server. | **Optional** (Defaults to `http://localhost:11434`) |
| `OLLAMA_MODEL` | The LLM model name (e.g., `llama3.2:1B`). | **Required** |

> [!NOTE]
> `OLLAMA_HOST` is primarily used to point to a remote server or a containerized instance of Ollama. If you visit this URL in your browser, you should see "Ollama is running".

## CLI Arguments

| Argument | Short | Description |
| :--- | :--- | :--- |
| `query` | (none) | Direct search query (skips interactive prompt). |
| `--gui` | `-g` | Launches the Web GUI interface (Gradio). |
| `--timestamp` | `-t` | Reports execution timestamps and total duration. |
| `--version` | `-V` | Displays the current version of AiQuery. |
| `--help` | `-h` | Shows the help message and exit. |

## Usage

### Terminal Mode (Interactive)
Simply run the main script:
```bash
./aiquery.py
```

### Terminal Mode (Direct Query)
Pass your question as an argument to skip the prompt:
```bash
./aiquery.py "Qual a capital da França?"
```

To see execution timing:
```bash
./aiquery.py -t "Qual a capital da França?"
```

### Web GUI Mode
Launch the interactive web interface:
```bash
./aiquery.py -g
```
Alternatively, you can still run `./app.py` directly.
Then open the local URL (usually `http://127.0.0.1:7860`) in your browser.

## Testing

```bash
# Run all tests
pytest test_memory.py test_timing.py test_aiquery.py
```

## Uninstallation

To remove the project and its environment:
```bash
# Deactivate environment
deactivate

# Remove the directory
rm -rf venv/
rm .env
```

## License
This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details. Note: The **PocketFlow** framework used in this project is also licensed under MIT by its original author.

## References
[1] **PocketFlow Framework License**  
    [github.com/The-Pocket/PocketFlow/blob/main/LICENSE](https://github.com/The-Pocket/PocketFlow/blob/main/LICENSE)  
    *AIQuery is built on top of the PocketFlow research project.*

[2] **Web Search with SERP Analysis (PocketFlow Cookbook)**  
    [github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-tool-search](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-tool-search)  
    *Our implementation extends the original cookbook with iterative loops and self-critique.*
