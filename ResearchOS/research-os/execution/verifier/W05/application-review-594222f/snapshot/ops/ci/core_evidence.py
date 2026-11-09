"""Recheck W01 archived evidence; never claim Paperclip has qualified."""
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[2]
result = subprocess.run([sys.executable, '-X', 'utf8', 'qualification/core/verify_evidence.py'],
                        cwd=root, capture_output=True, text=True, encoding='utf-8', timeout=30)
print(result.stdout, end='')
print(result.stderr, end='', file=sys.stderr)
if result.returncode:
    sys.exit(result.returncode)
report = json.loads(result.stdout)
assert report['status'] == 'PASS' and report['command_records'] > 0 and report['case_records'] == 16
print(json.dumps(dict(status='PASS', assertions=1, assertion_ids=['W01-ARCHIVED-EVIDENCE-INTEGRITY'],
                      scope='ARCHIVED_EVIDENCE_ONLY', paperclip_qualified=False, product_acceptance='NOT_RUN')))
