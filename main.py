"""
ThreatScope: Local AI-Powered Automated Code Auditing CLI

This module serves as the primary entry point for the ThreatScope application.
It orchestrates the execution of deterministic scanning tools (linters, regex scrapers, OSV)
and the probabilistic multi-agent CrewAI system powered by Ollama.
"""

import hashlib
import json
import os
import sys
import webbrowser
import urllib.request
import urllib.error
import secrets
from pathlib import Path

# Configure default Ollama embeddings provider
os.environ["EMBEDDINGS_PROVIDER"] = "ollama"
os.environ["EMBEDDINGS_OLLAMA_MODEL_NAME"] = "nomic-embed-text"
os.environ["EMBEDDINGS_OLLAMA_BASE_URL"] = "http://localhost:11434"

from crewai import Crew, Process, LLM

# Deterministic Tools
from tools.linter import run_linter
from tools.regex_finder import extract_apis_and_secrets
from tools.osv_offline_scanner import scan_for_vulnerabilities

# AI Agents & Tasks
from agents.summarizer import create_summarizer_agent
from tasks.summarizer_task import create_summarizer_task
from agents.security_guard import create_security_guard_agent
from tasks.security_guard_task import create_security_guard_task
from agents.syntax_reviewer import create_syntax_reviewer_agent
from tasks.syntax_reviewer_task import create_syntax_reviewer_task
from agents.logic_analyzer import create_logic_analyzer_agent
from tasks.logic_analyzer_task import create_logic_analyzer_task
from agents.orchestrator import create_orchestrator_agent
from tasks.orchestrator_task import create_orchestrator_task
from agents.reporter import generate_report

class Colors:
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def print_info(msg):
    print(f"{Colors.OKCYAN}[*] {msg}{Colors.ENDC}")

def print_success(msg):
    print(f"{Colors.OKGREEN}[+] {msg}{Colors.ENDC}")

def print_error(msg):
    print(f"{Colors.FAIL}[-] {msg}{Colors.ENDC}", file=sys.stderr)

def print_warning(msg):
    print(f"{Colors.WARNING}[!] {msg}{Colors.ENDC}")

def check_ollama(base_url="http://localhost:11434"):
    try:
        urllib.request.urlopen(base_url, timeout=2).read()
        return True
    except Exception:
        return False

def hash_file(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def hash_directory(directory: Path) -> str:
    ignore_dirs = {'.git', 'venv', 'env', 'node_modules', '__pycache__', '.threatscope'}
    ignore_files = {'.DS_Store'}
    file_hashes = []
    
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in sorted(files):
            if file in ignore_files:
                continue
            filepath = Path(root) / file
            if filepath.is_file():
                file_hashes.append(hash_file(filepath))
                
    file_hashes.sort()
    final_hasher = hashlib.sha256()
    for h in file_hashes:
        final_hasher.update(h.encode('utf-8'))
    return final_hasher.hexdigest()

def check_cache(target_dir: Path, current_hash: str) -> bool:
    threatscope_dir = target_dir / '.threatscope'
    state_file = threatscope_dir / 'state.json'
    
    if state_file.exists():
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
                if state.get('hash') == current_hash:
                    return True
        except (json.JSONDecodeError, IOError):
            pass
    return False

def update_cache(target_dir: Path, current_hash: str):
    threatscope_dir = target_dir / '.threatscope'
    threatscope_dir.mkdir(exist_ok=True)
    state_file = threatscope_dir / 'state.json'
    with open(state_file, 'w') as f:
        json.dump({'hash': current_hash}, f)

def main():
    class DummyArgs:
        def __init__(self):
            self.force = False
            self.verbose = False

    args = DummyArgs()
    
    while True:
        print("\n" + "="*40)
        print(" ThreatScope: Local AI Code Reviewer")
        print("="*40)
        print("1) Input codebase location")
        print("2) Update OSV Database")
        print("3) Exit")
        
        choice = input("\nSelect an option (1-3): ").strip()
        
        if choice == '1':
            path_input = input("Enter path to the repository/folder to scan: ").strip()
            if not path_input:
                print_error("Path cannot be empty.")
                continue
            target_dir = Path(path_input).resolve()
            run_scan(target_dir, args)
            
        elif choice == '2':
            print_info("Updating OSV Databases for all supported ecosystems...")
            from tools.osv_offline_scanner import download_and_extract_osv
            ecosystems = ["PyPI", "npm", "Go", "Maven", "crates.io"]
            for eco in ecosystems:
                download_and_extract_osv(eco)
            print_success("All OSV Databases updated successfully.")
            
        elif choice == '3':
            print_info("Exiting ThreatScope.")
            sys.exit(0)
            
        else:
            print_error("Invalid option. Please select 1, 2, or 3.")

def run_scan(target_dir: Path, args):
    if not target_dir.exists() or not target_dir.is_dir():
        print_error(f"Directory '{target_dir}' does not exist.")
        return
        
    print_info(f"Starting ThreatScope scan for {target_dir}")
    current_hash = hash_directory(target_dir)
    print_info(f"Codebase Hash: {current_hash}")
    
    report_path = target_dir / f"{target_dir.name}_threatscope_report.html"
    
    if not getattr(args, 'force', False) and check_cache(target_dir, current_hash) and report_path.exists():
        print_success("Codebase hasn't changed. Opening cached report...")
        webbrowser.open(f"file://{report_path.resolve()}")
        return
        
    print_info("Change detected or forced scan. Proceeding with analysis.")
    
    # 0. Pre-Flight Checks
    if not check_ollama():
        print_error("Ollama engine is not running or accessible at http://localhost:11434.")
        print_warning("Please start the Ollama service to proceed.")
        return
    
    # 1. Deterministic Tools
    print_info("Running deterministic tools (Linters & Regex Scrapers)...")
    try:
        linter_output = run_linter(target_dir)
        regex_findings = extract_apis_and_secrets(target_dir)
        osv_findings = scan_for_vulnerabilities(target_dir)
    except Exception as e:
        print_error(f"Failed executing deterministic tools: {str(e)}")
        return
    
    # 2. Setup Ollama
    print_info("Initializing AI Agents (Ollama: qwen2.5:7b)...")
    llm = LLM(model="ollama/qwen2.5:7b", base_url="http://localhost:11434")
    
    # 2.5 Security Guard Pre-Flight
    print_info("Running Pre-Flight Security Guard checks...")
    security_guard_agent = create_security_guard_agent(llm)
    
    raw_content_to_check = f"Linter:\n{linter_output}\nRegex:\n{regex_findings}\nOSV:\n{osv_findings}"
    try:
        from tasks.summarizer_task import get_file_contents
        raw_content_to_check += f"\nCode:\n{get_file_contents(str(target_dir))}"
    except Exception:
        pass
        
    security_task = create_security_guard_task(security_guard_agent, raw_content_to_check)
    security_crew = Crew(
        agents=[security_guard_agent],
        tasks=[security_task],
        process=Process.sequential,
        verbose=args.verbose
    )
    
    sec_result = security_crew.kickoff()
    if hasattr(security_task, 'output') and security_task.output and security_task.output.pydantic:
        sec_pyd = security_task.output.pydantic
        if not sec_pyd.is_safe:
            print_error(f"SECURITY ALERT: Prompt Injection detected!")
            print_error(f"Reason: {sec_pyd.reason}")
            return
        else:
            print_success("Security Guard cleared the input as safe.")
    else:
        print_warning("Security Guard failed to return a validated structure, proceeding with caution...")
    
    # Generate randomized XML Delimiter
    rand_delimiter = secrets.token_hex(6)
    
    # 3. Agents
    summarizer = create_summarizer_agent(llm)
    syntax_rev = create_syntax_reviewer_agent(llm)
    logic_anal = create_logic_analyzer_agent(llm)
    orchestra = create_orchestrator_agent(llm)
    
    # 4. Tasks (Sequential)
    task1 = create_summarizer_task(summarizer, str(target_dir), rand_delimiter)
    task2 = create_syntax_reviewer_task(syntax_rev, linter_output, rand_delimiter)
    task3 = create_logic_analyzer_task(logic_anal, regex_findings, osv_findings, rand_delimiter)
    task4 = create_orchestrator_task(orchestra)
    
    # Let task4 rely on context from task1, 2, 3
    task4.context = [task1, task2, task3]
    
    # 5. The Crew
    crew = Crew(
        agents=[summarizer, syntax_rev, logic_anal, orchestra],
        tasks=[task1, task2, task3, task4],
        memory=True,
        embedder={
            "provider": "ollama",
            "config": {
                "model": "nomic-embed-text",
                "base_url": "http://localhost:11434"
            }
        },
        process=Process.sequential,
        verbose=args.verbose
    )
    
    try:
        print_info("Starting the multi-agent CrewAI execution.")
        print_info("Agents are analyzing the repository. This may take a few minutes...")
        # Execute the crew
        result = crew.kickoff()
        
        # Pydantic Output Validation
        if not hasattr(task4, 'output') or not task4.output or not task4.output.pydantic:
            print_error("Orchestrator failed to produce the correctly formatted Pydantic JSON structure.")
            if getattr(args, 'verbose', False):
                print_error(f"Raw Result Dump:\n{result}")
            return
            
    except KeyboardInterrupt:
        print_warning("\nScan interrupted by user. Returning to menu.")
        return
    except Exception as e:
        print_error(f"A fatal error occurred during CrewAI execution: {str(e)}")
        return
        
    final_state = task4.output.pydantic.dict()
    
    print_info("Generating self-contained HTML Report...")
    template_dir = Path(__file__).parent / 'templates'
    final_report = generate_report(final_state, target_dir, template_dir)
    
    update_cache(target_dir, current_hash)
    
    print_success(f"Success! Report generated at: {final_report}")
    webbrowser.open(f"file://{final_report.resolve()}")

if __name__ == "__main__":
    main()
