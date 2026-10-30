"""Audit installed third-party versions, normalizing the official Torch CPU suffix."""
import argparse
from datetime import datetime, timezone
from importlib.metadata import distributions, version
import json
from pathlib import Path
import subprocess
import sys
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, default=Path('results/dependency_audit.json'))
args = parser.parse_args()
requirements = []
normalizations = []
for dist in distributions():
    name = dist.metadata['Name']
    installed = dist.version
    if name.lower().replace('_', '-') == 'enterprise-rag-evaluation-lab':
        continue  # Local source is reviewed/tested separately; it has no PyPI advisory entry.
    audited = installed
    if name.lower() == 'torch' and installed.endswith('+cpu'):
        audited = installed.removesuffix('+cpu')
        normalizations.append(dict(package=name,installed_version=installed,audited_upstream_version=audited,
            limitation='Upstream-version advisory lookup; does not attest to vendor-wheel binary integrity. Wheel SHA-256 is separately locked.'))
    requirements.append(f'{name}=={audited}')
with tempfile.TemporaryDirectory() as temporary:
    folder = Path(temporary)
    inputs, report = folder/'requirements.txt', folder/'audit.json'
    inputs.write_text('\n'.join(sorted(requirements))+'\n')
    result = subprocess.run([sys.executable,'-m','pip_audit','--disable-pip','--no-deps','-r',str(inputs),
        '--format','json','--output',str(report)],capture_output=True,text=True)
    if not report.exists():
        raise SystemExit('Dependency auditor failed without a report; publication remains blocked.')
    raw = json.loads(report.read_text())
    skipped = [p['name'] for p in raw['dependencies'] if p.get('skip_reason')]
    findings = sum(len(p.get('vulns',[])) for p in raw['dependencies'])
    output = dict(audited_utc=datetime.now(timezone.utc).isoformat(),tool='pip-audit',tool_version=version('pip-audit'),
        source='Installed third-party package versions; PyPI vulnerability service',
        exit_code=result.returncode,package_count=len(raw['dependencies']),vulnerability_count=findings,
        skipped_packages=skipped,excluded_local_package='enterprise-rag-evaluation-lab',normalizations=normalizations,
        limitations='Known advisory lookup only; no guarantee of absence of unknown vulnerabilities. Local source and models require separate review.',
        report=raw)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(output,indent=2)+'\n')
    print(f'pip-audit: {len(raw["dependencies"])} packages; {findings} known findings; {len(skipped)} skipped; exit {result.returncode}')
    raise SystemExit(result.returncode or bool(skipped))
