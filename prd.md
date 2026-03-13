## PRD: Local-AI Automated Code Reviewer (CLI)

### 1. Product Overview

A CLI-based tool that performs deep-dive code audits using a multi-agent "Crew" powered by **Ollama**. It transforms a local folder into a comprehensive, versioned HTML security and quality report.

### 2. Objectives

* **Privacy:** 100% local execution (no code leaves the machine).
* **Intelligence:** Detect logical and structural flaws that standard linters (like Flake8) miss.
* **Traceability:** Maintain a historical record of code health within a single portable HTML file.
* **Efficiency:** Zero-cost API usage by leveraging local hardware (RTX 3050).

---

### 3. Crew & Agent Logic (The "Brain")

| Agent | Responsibility | Input | Output |
| --- | --- | --- | --- |
| **Summarizer** | Contextual Mapping | File Tree, README, File Content | Detailed JSON map: Logic, Purpose, Operation per file. |
| **API Finder** | External Surface Analysis | Codebase | List of endpoints, imports, hardcoded secrets, and integrations. |
| **Syntax Review** | Style & Modularity Audit | Codebase | Linter compliance, Naming convention analysis (Camel vs Snake), Modularity score. |
| **Logical Flaws** | Business Logic Red-Teamer | Summaries + API Map | Identification of race conditions, auth bypasses, or flow errors. |
| **Orchestrator** | Quality Control & Manager | All Agent Outputs | Refined, verified, and non-vague consolidated report. |
| **Reporter** | Frontend Architect | Orchestrator's Final Report | Integrated HTML file with versioning. |

---

### 4. Technical Requirements

#### **A. AI Infrastructure**

* **LLM Engine:** Ollama.
* **Primary Model:** `qwen2.5-coder:7b` (high speed/accuracy balance).
* **Heavy Reasoning (Logical Flaws):** `qwen2.5-coder:14b` (if VRAM allows).
* **Framework:** CrewAI for agent orchestration.

#### **B. Storage & Comparison Logic**

* **Input:** CLI Argument (Path to folder).
* **Hashing:** The tool must generate a SHA-256 hash of the codebase to detect if a re-scan is actually necessary.
* **Integration:** * If `foldername.html` exists: Parse existing HTML, move current data to "History," and inject new data into the "Latest" view.
* If no file exists: Create from a fresh Jinja2 template.



#### **C. UI/UX (Webpage)**

* **Tech:** Single-file HTML (Tailwind CSS via CDN).
* **Visuals:** * **Summary Dashboard:** High-level health score.
* **Style Consistency Chart:** Visualizing naming convention shifts.
* **Logical Flaw Severity:** Color-coded (Critical, Warning, Info).
* **Version Toggle:** A dropdown to view previous scan results.



---

### 5. User Workflow (The CLI Experience)

1. **Command:** `python main.py /home/nullsec/projects/my_app`
2. **Execution:** * CLI shows a progress bar as agents work (e.g., "Summarizer mapping files...", "Logical Flaws searching for vulnerabilities...").
* Orchestrator validates findings.


3. **Output:** * "Report generated: `my_app.html`"
* Auto-opens the browser to the report page.



---

### 6. Success Metrics

* **Accuracy:** Zero "vague" comments (enforced by the Orchestrator).
* **Performance:** Full scan of a medium-sized repo in < 2 minutes on local hardware.
* **Portability:** The output HTML must be viewable offline without external dependencies (except CDN).
