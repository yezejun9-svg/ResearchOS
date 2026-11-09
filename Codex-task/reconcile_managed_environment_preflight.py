import hashlib,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=Path('D:/作品集/ResearchOS/research-os')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=HERE/'product-v1-integration-plans/managed-environment.json';assert sha(old)=='ee85ebea6948622251802098ae5eb62e1296795e2403921bba915f48343f2b29'
plan=json.loads(old.read_bytes());assert not (ROOT/plan['receipt_ref']/'root-integration-journal.json').exists()
cp=json.loads((ROOT/'execution/v2.4/checkpoint.json').read_bytes());assert cp['revision']==607 and len(cp['failure_counters'])==2461
index=subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','--no-optional-locks','diff','--cached','--name-only'],cwd=ROOT);assert not index.strip()
scope=json.loads((ROOT/plan['scope_ref']).read_bytes())
for ref,digest in scope['baseline_sha256'].items():assert (sha(ROOT/ref) if (ROOT/ref).is_file() else 'ABSENT_BEFORE')==digest
plan['diagnostic_events'].append(dict(origin_key='product-v1-root-node-sparse-gomod-preflight',classification='ROOT_INTEGRATION_PREFLIGHT',detail='First Node-only integration stopped before journal/copy/stage because generic Go checksum guard required intentionally absent sparse go.mod. Fixed guard to apply only to Go source slices. Original result and plan retained; no source/index/checkpoint effects.'))
dest=HERE/'product-v1-integration-plans/managed-environment.rev2.json';assert not dest.exists();dest.write_bytes((json.dumps(plan,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
print(json.dumps(dict(plan=str(dest),sha256=sha(dest),prior_attempt='KNOWN_PREFLIGHT_FAILURE_NO_SOURCE_WRITE',checkpoint=607)))
