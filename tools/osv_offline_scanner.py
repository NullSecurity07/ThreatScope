import os
import re
import json
import xml.etree.ElementTree as ET
import urllib.request
import zipfile
import sqlite3
import time
from pathlib import Path

def build_sqlite_index(db_dir: Path):
    db_path = db_dir / "index.db"
    
    print("[*] Building SQLite index from OSV JSON files (this happens once)...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Ensure idempotency
    cursor.execute('DROP TABLE IF EXISTS vulnerabilities')
    
    cursor.execute('''
        CREATE TABLE vulnerabilities (
            package_name TEXT,
            vuln_id TEXT,
            aliases TEXT,
            summary TEXT,
            details TEXT
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_package_name ON vulnerabilities(package_name)')
    
    # Batch insert list
    records = []
    
    # Parsing JSONs
    for json_file in db_dir.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                vuln_id = data.get('id', 'Unknown')
                aliases = json.dumps(data.get('aliases', []))
                summary = data.get('summary', 'No summary available')
                details_full = data.get('details', '')
                details = details_full[:200] + "..." if len(details_full) > 200 else details_full
                
                for affected in data.get('affected', []):
                    pkg_name = affected.get('package', {}).get('name', '').lower()
                    if pkg_name:
                        records.append((pkg_name, vuln_id, aliases, summary, details))
        except Exception:
            pass
            
    cursor.executemany('''
        INSERT INTO vulnerabilities (package_name, vuln_id, aliases, summary, details)
        VALUES (?, ?, ?, ?, ?)
    ''', records)
    
    conn.commit()
    conn.close()
    
    print(f"[+] SQLite index built with {len(records)} records.")
    
    # Cleanup json files
    for json_file in db_dir.glob("*.json"):
        try:
            os.remove(json_file)
        except Exception:
            pass
    print("[+] Cleaned up raw JSON files.")

def download_and_extract_osv(ecosystem="PyPI"):
    threatscope_dir = Path(__file__).resolve().parent.parent / ".threatscope_data"
    vulndb_dir = threatscope_dir / "vulndb" / ecosystem
    vulndb_dir.mkdir(parents=True, exist_ok=True)
    
    db_path = vulndb_dir / "index.db"
    zip_path = vulndb_dir / "all.zip"
    url = f"https://osv-vulnerabilities.storage.googleapis.com/{ecosystem}/all.zip"
    
    if db_path.exists():
        age_seconds = time.time() - os.path.getmtime(db_path)
        if age_seconds < (24 * 60 * 60):
            return vulndb_dir
        else:
            print("[*] OSV database is older than 24 hours. Updating...")
            try:
                os.remove(db_path)
            except Exception:
                pass
        
    print(f"[*] Downloading offline vulnerability database for {ecosystem} (might take a minute)...")
    try:
        urllib.request.urlretrieve(url, zip_path)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(vulndb_dir)
        print(f"[+] Download and extraction complete for {ecosystem}.")
        
        # Build the SQLite Index
        build_sqlite_index(vulndb_dir)
        
    except Exception as e:
        print(f"[-] Failed to setup OSV DB for {ecosystem}: {e}")
        
    return vulndb_dir

def parse_requirements(target_dir: Path):
    req_file = target_dir / "requirements.txt"
    packages = []
    if req_file.exists():
        with open(req_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'): continue
                # Match simple package==version or package
                match = re.split(r'[=<>~]', line)
                if match:
                    packages.append({"name": match[0].strip(), "version": line.replace(match[0].strip(), "").strip("=<>~ ")})
    return packages

def parse_package_json(target_dir: Path):
    req_file = target_dir / "package.json"
    packages = []
    if req_file.exists():
        try:
            with open(req_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                deps = data.get("dependencies", {})
                dev_deps = data.get("devDependencies", {})
                all_deps = {**deps, **dev_deps}
                for name, ver in all_deps.items():
                    packages.append({"name": name, "version": ver})
        except Exception:
            pass
    return packages

def parse_go_mod(target_dir: Path):
    req_file = target_dir / "go.mod"
    packages = []
    if req_file.exists():
        try:
            with open(req_file, 'r', encoding='utf-8') as f:
                in_require_block = False
                for line in f:
                    line = line.strip()
                    if line.startswith("require ("):
                        in_require_block = True
                        continue
                    if in_require_block and line == ")":
                        in_require_block = False
                        continue
                    if line.startswith("require ") and not in_require_block:
                        parts = line.split()
                        if len(parts) >= 3:
                            packages.append({"name": parts[1], "version": parts[2]})
                    elif in_require_block and line:
                        parts = line.split()
                        if len(parts) >= 2:
                            packages.append({"name": parts[0], "version": parts[1]})
        except Exception:
            pass
    return packages

def parse_pom_xml(target_dir: Path):
    req_file = target_dir / "pom.xml"
    packages = []
    if req_file.exists():
        try:
            tree = ET.parse(req_file)
            root = tree.getroot()
            ns = {'mvn': 'http://maven.apache.org/POM/4.0.0'}
            # Handle default namespace if not prefixed
            match_ns = ""
            if root.tag.startswith("{"):
                match_ns = root.tag.split("}")[0] + "}"
                
            for dep in root.findall(f".//{match_ns}dependency"):
                group_id = dep.find(f"{match_ns}groupId")
                artifact_id = dep.find(f"{match_ns}artifactId")
                version = dep.find(f"{match_ns}version")
                if group_id is not None and artifact_id is not None:
                    name = f"{group_id.text}:{artifact_id.text}"
                    ver = version.text if version is not None else ""
                    packages.append({"name": name, "version": ver})
        except Exception:
            pass
    return packages

def parse_cargo_toml(target_dir: Path):
    req_file = target_dir / "Cargo.toml"
    packages = []
    if req_file.exists():
        try:
            with open(req_file, 'r', encoding='utf-8') as f:
                in_deps = False
                for line in f:
                    line = line.strip()
                    if line.startswith("[dependencies]") or line.startswith("[dev-dependencies]"):
                        in_deps = True
                        continue
                    if line.startswith("[") and not line.startswith("[dependencies") and not line.startswith("[dev-dependencies"):
                        in_deps = False
                        continue
                    if in_deps and "=" in line:
                        parts = line.split("=")
                        packages.append({"name": parts[0].strip(), "version": parts[1].strip()})
        except Exception:
            pass
    return packages

def execute_osv_query(db_path: Path, packages: list, ecosystem: str) -> list:
    findings = []
    if not packages:
        return findings
        
    if not db_path.exists():
        print(f"[-] OSV database for {ecosystem} not found. Please update the OSV databases from the main menu.")
        return findings
        
    print(f"[*] Querying {len(packages)} '{ecosystem}' dependencies against SQLite offline OSV database...")
    package_names = [p['name'].lower() for p in packages]
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Batching queries to avoid sqlite limits on placeholders
        batch_size = 900
        for i in range(0, len(package_names), batch_size):
            batch = package_names[i:i+batch_size]
            placeholders = ','.join('?' * len(batch))
            query = f"SELECT package_name, vuln_id, aliases, summary, details FROM vulnerabilities WHERE package_name IN ({placeholders})"
            
            cursor.execute(query, batch)
            rows = cursor.fetchall()
            
            for row in rows:
                pkg_name, vuln_id, aliases_str, summary, details = row
                try:
                    aliases = json.loads(aliases_str)
                except Exception:
                    aliases = []
                    
                findings.append({
                    "package": pkg_name,
                    "vulnerability_id": vuln_id,
                    "aliases": aliases,
                    "summary": summary,
                    "details": details,
                    "ecosystem": ecosystem
                })
                
        conn.close()
    except Exception as e:
        print(f"[-] Error querying SQLite db for {ecosystem}: {e}")
            
    return findings

def scan_for_vulnerabilities(target_dir: Path):
    all_findings = []
    threatscope_dir = Path(__file__).resolve().parent.parent / ".threatscope_data"
    
    # Define ecosystems mapping (Display Name, OSV DB Name, Parser Func)
    ecosystems = [
        ("PyPI", "PyPI", parse_requirements),
        ("npm", "npm", parse_package_json),
        ("Go", "Go", parse_go_mod),
        ("Maven", "Maven", parse_pom_xml),
        ("crates.io", "crates.io", parse_cargo_toml)
    ]
    
    for display_name, osv_name, parser_func in ecosystems:
        packages = parser_func(target_dir)
        if packages:
            db_path = threatscope_dir / "vulndb" / osv_name / "index.db"
            findings = execute_osv_query(db_path, packages, display_name)
            all_findings.extend(findings)
                
    return all_findings

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        target = Path(sys.argv[1]).resolve()
        res = scan_for_vulnerabilities(target)
        print(json.dumps(res, indent=2))
