import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from bs4 import BeautifulSoup
from datetime import datetime

def parse_existing_history(html_path: Path) -> list:
    """Extracts the hidden history JSON blob from the existing HTML report."""
    if not html_path.exists():
        return []
    
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            history_node = soup.find('textarea', id='history_data')
            if history_node and history_node.string:
                return json.loads(history_node.string)
    except Exception:
        pass
    
    return []

def generate_report(report_data: dict, target_dir: Path, template_dir: Path):
    """
    Renders the HTML report using Jinja2, appending current run to history.
    """
    repo_name = target_dir.name
    output_path = target_dir / f"{repo_name}_threatscope_report.html"
    
    # 1. Get History
    history = parse_existing_history(output_path)
    
    # 2. Add current to history
    report_data['timestamp'] = datetime.now().isoformat()
    history.insert(0, report_data) # Prepend
    
    # 3. Render
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template('report.html')
    
    html_content = template.render(
        report=report_data,
        target_folder=repo_name,
        current_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
        history_json=json.dumps(history)
    )
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    return output_path
