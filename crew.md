

## 1. The Hybrid Architecture

We will split the tasks into **Deterministic Tools** (Scripts/Regex) and **Cognitive Agents** (LLM).

| Crew Member | Type | Responsibility | Efficiency Gain |
| --- | --- | --- | --- |
| **Summarizer** | **AI** | |
| **API Finder** | **Regex Tool** | Uses a Python script with regex to extract all URLs, IP addresses, and `@route` decorators. | 100% accurate; no AI hallucinations. |
| **Syntax Review** | **Script + AI** | **Script:** Runs `flake8` or `eslint`. **AI:** Compares casing styles (Camel vs Snake) and rates modularity. | Fast linting + smart style analysis. |
| **Logical Flaws** | **Pure AI** | Analyzes the *relationship* between the Summarizer's map and the API Finder's list. | High-value reasoning only. |
| **Orchestrator** | **Pure AI** | The "Quality Gate." Checks if the Logical Flaw agent found something the Regex missed. | Prevents vaugeness. |

---

## 2. Memory Management (32GB RAM Setup)

Running multiple agents on **Ollama** can saturate your VRAM. You need a **"Context-Handoff"** strategy.

### A. Short-Term Memory (Task Chaining)

CrewAI has built-in `memory=True`. This creates a local **LanceDB** vector store (stored in `~/.crewai/memory`).

* **The Flow:** The Summarizer stores its "Map" in memory. When the Logical Flaws agent starts, it queries that memory rather than re-reading the whole folder.

### B. VRAM Optimization

Since you have 32GB of RAM but 4GB of VRAM (RTX 3050):

* **Keep only one model loaded:** Use `qwen2.5-coder:7b` for all agents. It handles both coding and reasoning well.
* **Sequential Process:** Use `Process.sequential` in your Crew. This ensures only one agent is active at a time, keeping your GPU from choking.
* **Context Window:** Set `num_ctx` to `8192` or `16384` in your Ollama Modelfile to handle larger code snippets without losing the "top" of the file.

---

## 3. Collaboration Logic (The "Shared Brain")

The agents shouldn't just talk; they should **augment** a shared state file.

1. **The State Object:** A single `report_state.json`.
2. **Summarizer:** Writes the "Skeleton" to the JSON.
3. **API Finder:** Appends the "Endpoints" list to the JSON.
4. **Logical Flaws Agent:** Reads the JSON, finds a contradiction (e.g., an endpoint with no auth logic), and adds a "Critical Finding."
5. **Reporter:** Reads the final JSON and builds the HTML.

