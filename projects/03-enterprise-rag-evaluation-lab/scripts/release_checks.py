"""Scoped pattern/privacy/artifact audit. Not a substitute for a secret scanner."""
from pathlib import Path
import re

root=Path(__file__).resolve().parents[1]
patterns={
    'personal path':r'/(?:Users|home)/[^\s/]+/',
    'private key':r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    'credential token':r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16}|sk-[A-Za-z0-9]{24,})\b',
    'credential URL':r'[a-z]+://[^\s/:]+:[^\s/@]+@',
    'email':r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
    'private IP':r'\b(?:10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+)\b',
}
files=[p for p in root.rglob('*') if p.is_file() and not any(part in {'.venv','.cache','__pycache__','.pytest_cache'} or part.endswith('.egg-info') for part in p.relative_to(root).parts)]
findings=[]
for path in files:
    text=path.read_text()
    for label,pattern in patterns.items():
        if re.search(pattern,text): findings.append((str(path.relative_to(root)),label))
    if path.stat().st_size>1_000_000: findings.append((str(path.relative_to(root)),'artifact >1 MB'))
if findings:
    # Never print matched secret values.
    raise SystemExit('Review required: '+repr(findings))
print(f'PASS: scoped pattern/privacy/size checks; {len(files)} files; {sum(p.stat().st_size for p in files)} bytes. Dedicated scanner and historical repository audit NOT performed.')
