import subprocess
import json
from pathlib import Path

def run_linter(directory: Path) -> dict:
    """
    Detects Python or JavaScript/TypeScript projects
    and runs the appropriate linter, returning the output.
    """
    results = {
        "python": [],
        "javascript": []
    }
    
    # Check for Python files
    py_files = list(directory.rglob("*.py"))
    py_files = [f for f in py_files if 'venv' not in f.parts and '.threatscope' not in f.parts and 'env' not in f.parts]
    
    if py_files:
        try:
            # We use subprocess to run flake8 natively on the whole directory
            # Excluding common virtual envs just in case
            cmd = ["flake8", "--exclude", "venv,env,.env,.threatscope", str(directory)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.stdout:
                # Flake8 returns output when it finds issues
                results["python"] = result.stdout.strip().split("\n")
        except FileNotFoundError:
            results["python"] = ["flake8 not installed globally or in current environment."]
            
    # Check for JS/TS files
    js_files = list(directory.rglob("*.js")) + list(directory.rglob("*.ts"))
    js_files = [f for f in js_files if 'node_modules' not in f.parts and '.threatscope' not in f.parts]
    
    if js_files:
        try:
            cmd = ["eslint", "--no-error-on-unmatched-pattern", str(directory)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.stdout:
                results["javascript"] = result.stdout.strip().split("\n")
        except FileNotFoundError:
            results["javascript"] = ["eslint not installed or not found in PATH."]
            
    return results

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        target_dir = Path(sys.argv[1]).resolve()
        res = run_linter(target_dir)
        print(json.dumps(res, indent=2))
