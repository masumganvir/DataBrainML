import os
import re
from pathlib import Path

ROOT = Path('.').resolve()
PATTERNS = {
    'API_KEY': re.compile(r'(?i)(api[_-]?key|apikey)\s*[:=]\s*[\'"]([A-Za-z0-9_\-]{16,})[\'"]'),
    'AWS_KEY': re.compile(r'(?i)(aws_access_key_id|aws_secret_access_key)\s*[:=]\s*[\'"]([A-Za-z0-9/+=]{16,})[\'"]'),
    'PRIVATE_KEY': re.compile(r'-----BEGIN\s+(RSA|EC|DSA|OPENSSH|PGP)?\s*PRIVATE\s+KEY'),
    'JWT_SECRET': re.compile(r'(?i)(jwt[_-]?secret)\s*[:=]\s*[\'"]([^\'"]{10,})[\'"]'),
    'PASSWORD': re.compile(r'(?i)(password|passwd|pwd)\s*[:=]\s*[\'"]([^\'"]{8,})[\'"]'),
    'GENERIC_SECRET': re.compile(r'(?i)(secret[_-]?key)\s*[:=]\s*[\'"]([^\'"]{12,})[\'"]'),
}

EXCLUDE_DIRS = {'.git', 'node_modules', '.venv', '__pycache__', 'dist', 'build', '.pytest_cache'}
EXCLUDE_FILES = {'.env', '.env.example', 'package-lock.json'}

findings = []

for root, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
    for file in files:
        if file in EXCLUDE_FILES or file.endswith(('.png', '.jpg', '.ico', '.woff2', '.db', '.coverage', '.pyc')):
            continue
        filepath = Path(root) / file
        relpath = filepath.relative_to(ROOT)
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line_no, line in enumerate(f, 1):
                    for stype, pat in PATTERNS.items():
                        m = pat.search(line)
                        if m:
                            line_content = line.strip()
                            is_placeholder = any(
                                ph in line_content.lower() for ph in [
                                    'changeme', 'your_', 'dummy', 'mock', 'fake', 'test',
                                    'example', 'placeholder', 'minioadmin', 'datawise_pass',
                                    'os.getenv', 'field(default=', 'default_secret_key'
                                ]
                            )
                            sev = 'INFO' if is_placeholder else 'CRITICAL'
                            findings.append((str(relpath).replace('\\', '/'), line_no, stype, sev))
        except Exception:
            pass

print(f"TOTAL_FINDINGS: {len(findings)}")
critical_findings = [f for f in findings if f[3] == 'CRITICAL']
print(f"CRITICAL_FINDINGS: {len(critical_findings)}")
for f in findings:
    print(f"FILE: {f[0]} | LINE: {f[1]} | TYPE: {f[2]} | SEVERITY: {f[3]}")
