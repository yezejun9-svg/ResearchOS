"""Read-only final-head and integrated-source pin report for root review."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')
state = json.loads((ROOT / 'execution/product-v1/state.json').read_bytes())
cp = json.loads((ROOT / 'execution/v2.4/checkpoint.json').read_bytes())
head = subprocess.check_output(['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false',
                                '--no-optional-locks', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
pins = {ref: digest for item in state['integrated_source']
        for ref, digest in item['source_sha256'].items()}
ui_scope = 'PRODUCT_V1_WORKBENCH_ASSISTANT_REFINEMENT'
active = {row['scope_id']: row['status'] for row in state['active_scopes']}
print(json.dumps(dict(main_head=head, checkpoint_head=cp['current_Main_HEAD'],
                      checkpoint_revision=cp['revision'], source_count=len(pins),
                      source_union_sha256=hashlib.sha256(json.dumps(pins, sort_keys=True,
                                                                    separators=(',', ':')).encode()).hexdigest(),
                      ui_layout_sha256=pins.get('apps/web/src/components/workbench-layout.jsx'),
                      ui_integrated=any(row['scope_id'] == ui_scope for row in state['integrated_source']),
                      ui_status=active.get(ui_scope)), ensure_ascii=False, indent=2))
