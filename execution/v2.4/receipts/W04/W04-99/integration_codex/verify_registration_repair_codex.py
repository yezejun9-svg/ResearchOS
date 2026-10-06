"""Check changed integrity code against immutable actual current registration."""
from pathlib import Path
import datetime as dt, hashlib, json, subprocess, sys
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[5]; CARD=HERE.parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p): return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
validator=CARD/'formal_validator_codex/validate.py'
assert sha(validator)=='008759e428d993da3a277cb915818ebcac67fd4b73027d732413271d6e81cb96'
state=ROOT/'execution/v2.4/step_state.json'; before=state.read_bytes()
argv=[sys.executable,'-B','-X','utf8',str(validator),'--repo',str(ROOT),'--state',str(state),
    '--spec',str(ROOT/'.local/worktrees/v24-continuation/spec/v2.4'),
    '--current-index',str(HERE/'current_context_codex.json'),
    '--independent-review',str(CARD/'independent_review_codex.json'),
    '--root-observed-issuance',str(HERE/'independent_issuance_codex.json'),'--phase','reviewed']
start=dt.datetime.now(dt.timezone.utc).isoformat(); r=subprocess.run(argv,cwd=ROOT,capture_output=True)
for path,raw in [(HERE/'repair_reviewed_integrity.stdout.json',r.stdout),(HERE/'repair_reviewed_integrity.stderr.txt',r.stderr)]:
    with path.open('xb') as stream: stream.write(raw)
receipt={'schema':'researchos.root-readonly-integrity-invocation.v1','scope':'CHANGED_INTEGRITY_PREFLIGHT_NOT_CANONICAL_ACCEPTANCE',
    'actual_argv':argv,'cwd':str(ROOT),'started_at':start,'ended_at':dt.datetime.now(dt.timezone.utc).isoformat(),'exit_code':r.returncode,
    'executable_sha256':sha(Path(sys.executable)),'validator':ref(validator),'current_context':ref(HERE/'current_context_codex.json'),
    'stdout':ref(HERE/'repair_reviewed_integrity.stdout.json'),'stderr':ref(HERE/'repair_reviewed_integrity.stderr.txt'),
    'product_reexecutions':0,'dispatcher_reexecutions':0,'formal_count_delta':0,
    'independent_new_source_review':'PENDING_ROUND2_AFTER_FOCUSED_CONTROLS'}
with (HERE/'repair_reviewed_integrity_invocation_codex.json').open('x',encoding='utf8',newline='\n') as stream:
    json.dump(receipt,stream,ensure_ascii=False,indent=2); stream.write('\n')
assert state.read_bytes()==before
assert r.returncode==0,r.stdout.decode('utf8','replace')
report=json.loads(r.stdout); assert report['integrity']=='PASS' and report['formal_accepted_count']==0 and set(report['eligible_owned_cases'])=={'A01','C03','C04'}
print(json.dumps({'status':'PASS_CHANGED_INTEGRITY_PREFLIGHT','eligible_cases':report['eligible_owned_cases'],'formal_accepted':0,'canonical_state_unchanged':True}))
