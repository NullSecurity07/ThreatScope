import re
import json
import os
from pathlib import Path

def extract_apis_and_secrets(directory: Path) -> dict:
    """
    Scans the directory for hardcoded URLs, IP addresses, secrets, and routes.
    Uses regex for maximum deterministic extraction without LLM hallucinations.
    """
    ignore_dirs = {'.git', 'venv', 'env', 'node_modules', '__pycache__', '.threatscope'}
    
    # Common Patterns
    url_pattern = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+')
    ip_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
    route_pattern = re.compile(r'@[\w\.]*route\s*\([^)]*\)')
    secret_pattern = re.compile(r'(?i)(?:api_key|password|secret|token)\s*[:=]\s*[\'"]([^\'"]+)[\'"]')
    
    findings = {
        "urls": [],
        "ips": [],
        "routes": [],
        "secrets": []
    }
    
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            filepath = Path(root) / file
            if filepath.suffix not in ['.py', '.js', '.ts', '.env', '.json', '.yaml', '.yml', '.go', '.java', '.php', '.rb']:
                continue
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    for match in url_pattern.finditer(content):
                        findings["urls"].append({"file": str(filepath.relative_to(directory)), "match": match.group(0)})
                    for match in ip_pattern.finditer(content):
                        findings["ips"].append({"file": str(filepath.relative_to(directory)), "match": match.group(0)})
                    for match in route_pattern.finditer(content):
                        findings["routes"].append({"file": str(filepath.relative_to(directory)), "match": match.group(0)})
                    for match in secret_pattern.finditer(content):
                        findings["secrets"].append({"file": str(filepath.relative_to(directory)), "match": match.group(0)})
                        
            except (UnicodeDecodeError, IOError):
                pass
                
    return findings

if __name__ == "__main__":
    import sys
    import os
    if len(sys.argv) > 1:
        target_dir = Path(sys.argv[1]).resolve()
        res = extract_apis_and_secrets(target_dir)
        print(json.dumps(res, indent=2))
