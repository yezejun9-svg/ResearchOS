"""Record a real read-only check of current W04 execution evidence."""
from pathlib import Path
import datetime as dt, hashlib, json, subprocess, sys
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[5]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p): return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
validator=HERE.parent/'formal_validator_codex/validate.py'
assert sha(validator)=='5add6b0044da783d009b52cdaac3402be053303006691ec337eac767d247e894'
argv=[sys.executable,'-B','-X','utf8',str(validator),'--repo',str(ROOT),'--state',str(ROOT/'execution/v2.4/step_state.json'),
    '--spec',str(ROOT/'.local/worktrees/v24-continuation/spec/v2.4'),'--current-index',str(HERE/'current_context_codex.json'),'--phase','execution']
start=dt.datetime.now(dt.timezone.utc).isoformat(); r=subprocess.run(argv,cwd=ROOT,capture_output=True)
(HERE/'execution_integrity.stdout.json').write_bytes(r.stdout); (HERE/'execution_integrity.stderr.txt').write_bytes(r.stderr)
record={'schema':'researchos.root-readonly-integrity-invocation.v1','actual_argv':argv,'cwd':str(ROOT),'started_at':start,'ended_at':dt.datetime.now(dt.timezone.utc).isoformat(),
    'exit_code':r.returncode,'validator':ref(validator),'executable_sha256':sha(Path(sys.executable)),'stdout':ref(HERE/'execution_integrity.stdout.json'),
    'stderr':ref(HERE/'execution_integrity.stderr.txt'),'current_context':ref(HERE/'current_context_codex.json'),'product_go_reexecutions':0,'formal_case_count_delta':0}
with (HERE/'execution_integrity_invocation_codex.json').open('x',encoding='utf8') as f: json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
assert r.returncode==0,(r.stdout.decode('utf8','replace'),r.stderr.decode('utf8','replace'))
report=json.loads(r.stdout); assert report['integrity']=='PASS' and report['formal_accepted_count']==0
print(json.dumps(report,ensure_ascii=False))
