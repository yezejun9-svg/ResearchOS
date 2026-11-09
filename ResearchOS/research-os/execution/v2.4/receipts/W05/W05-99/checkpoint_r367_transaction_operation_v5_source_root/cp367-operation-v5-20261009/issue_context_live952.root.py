import sys,json,hashlib
from datetime import datetime,timezone
from pathlib import Path
sys.dont_write_bytecode=True
N=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve(strict=True);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
assert len(sys.argv)==4
rr=dict(path=sys.argv[1],sha256=sys.argv[2],bytes=int(sys.argv[3]));assert pin(rr['path'])==rr
assert json.loads(Path(rr['path']).read_bytes())['decision']=='SOURCE_ACCEPTED_PENDING_FRESH_ROOT_LIVE_CONTEXT_VALIDATION'
fr=pin(N/'checkpoint.execution.facts.json');assert fr['sha256']=='fa7eaa0b9cbc30e18324e3fae122318f23e2f58243b8be6cfb306f93491d5c7c' and fr['bytes']==33802
facts=json.loads(Path(fr['path']).read_bytes());assert facts['highest_observed_ordinal']==951 and facts['next_failure_ordinal']==952 and [d['ordinal'] for d in facts['diagnostics']]==list(range(937,952))
stamp=datetime.now(timezone.utc);assert stamp.timestamp()>Path(rr['path']).stat().st_mtime
out=N/'live952-post-v5-review.root';out.mkdir(exist_ok=False)
ctx=dict(schema='researchos.root-postseal-live-diagnostic-context.v1',issued_by='codex:/root',created_utc=stamp.isoformat(),source_cutoff=dict(highest_ordinal=951,next_failure_ordinal=952),next_original_failure_ordinal=952,pending=[])
with (out/'live-context.actual.root.json').open('xb') as f:f.write((json.dumps(ctx,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(json.dumps(dict(live_context_ref=pin(out/'live-context.actual.root.json'),source_review_ref=rr,next_original_failure_ordinal_live=952)),flush=True)
