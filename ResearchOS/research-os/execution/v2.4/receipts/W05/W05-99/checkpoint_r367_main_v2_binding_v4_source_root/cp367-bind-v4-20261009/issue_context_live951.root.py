import sys,json,hashlib
from datetime import datetime,timezone
from pathlib import Path
sys.dont_write_bytecode=True
N=Path(__file__).resolve().parent
B=N.parent.parent
def pin(p):
 p=Path(p).resolve(strict=True);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
fr=pin(N/'checkpoint.execution.facts.json')
assert fr['sha256']=='f0e358383f6a8c9702a2ffe1770b8d2a76ce1390764383fd02102836014d333d' and fr['bytes']==32485
facts=json.loads(Path(fr['path']).read_bytes())
rp=B/'checkpoint_r367_main_v2_binding_v4_independent_review_codex/cp367v4r-01a11fad/HDF.json'
rr=pin(rp);assert rr['sha256']=='95ab93dfd77646bebcba75b1f2f38ea1b8fb38022a80e2c63961b80f671c43b0' and rr['bytes']==3495
assert json.loads(rp.read_bytes())['decision']=='SOURCE_ACCEPTED_PENDING_FRESH_ROOT_LIVE_CONTEXT_VALIDATION'
assert facts['highest_observed_ordinal']==950 and facts['next_failure_ordinal']==951 and [d['ordinal'] for d in facts['diagnostics']]==list(range(937,951))
stamp=datetime.now(timezone.utc)
assert stamp.timestamp()>rp.stat().st_mtime
out=N/'live951-post-v4-review.root';out.mkdir(exist_ok=False)
ctx=dict(schema='researchos.root-postseal-live-diagnostic-context.v1',issued_by='codex:/root',created_utc=stamp.isoformat(),source_cutoff=dict(highest_ordinal=950,next_failure_ordinal=951),next_original_failure_ordinal=951,pending=[])
with (out/'live-context.actual.root.json').open('xb') as f:f.write((json.dumps(ctx,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(json.dumps(dict(live_context_ref=pin(out/'live-context.actual.root.json'),source_review_ref=rr,next_original_failure_ordinal_live=951)),flush=True)
