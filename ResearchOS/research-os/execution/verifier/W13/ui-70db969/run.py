"""Independent invocation of frozen browser checks; only output destination changes."""
import os
from pathlib import Path
import subprocess
import sys

OUT = Path(__file__).resolve().parent
ROOT = Path(os.environ.get('REVIEW_SOURCE', str(OUT.parents[3] / '.local/worktrees/w13-ui-review')))
phase = sys.argv[1] if len(sys.argv) > 1 else 'contracts'
os.environ['RESEARCHOS_TASK_ID'] = 'W13'
os.environ['RESEARCHOS_UI_PHASE'] = phase
source = ROOT / 'tests/ui/browser_smoke.py'
sys.path.insert(0, str(source.parent))
text = source.read_text(encoding='utf-8')
old = "out = ROOT / 'execution/receipts/W13/frontend' / run_id"
assert text.count(old) == 1
text = text.replace(old, "out = Path(" + repr(str(OUT / os.environ.get('REVIEW_OUTPUT_PREFIX', '') / phase)) + ") / run_id")
if phase in ('independent', 'regression'):
    branch = "                if phase in ('workflow', 'plan', 'contracts'):"
    text = text.replace(branch, "                if phase in ('independent', 'regression'):\n                    from " + phase + " import probe\n                    probe(page, base, project_path, token, api_json, report, out)\n                elif phase in ('workflow', 'plan', 'contracts'):")
    sys.path.insert(0, str(OUT))
if phase == 'contracts':
    sys.path.insert(0, str(OUT))
    marker = "                report['http_responses'] = responses"
    text = text.replace(marker, "                from verify_chain import verify_chain\n                verify_chain(page, base, project_path, token, report, out)\n" + marker)
exec(compile(text, str(source), 'exec'), {'__name__': '__main__', '__file__': str(source)})
