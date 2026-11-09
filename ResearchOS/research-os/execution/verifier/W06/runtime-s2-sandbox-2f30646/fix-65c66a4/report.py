from pathlib import Path
import json,hashlib
OUT=Path(__file__).resolve().parent;PRIOR=OUT.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def put(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
assertions=read(OUT/'assertions.json');assert len(assertions)==5 and all(r['status']=='PASS' for r in assertions)
assert read(OUT/'command.json')['exit_code']==0
assert read(OUT/'author-evidence/receipt.json')['exit_code']==0
indices=[]
for sub in ['', 'fix-678a68c','fix-a7608ad']:
 path=PRIOR/sub/'index.json';index=read(path)
 for row in index['files']:assert sha(path.parent/row['path'])==row['sha256']
 indices.append({'path':str(path),'sha256':sha(path),'files':len(index['files'])})
review={
 'artifact_kind':'INDEPENDENT_SANDBOX_START_CANCELLATION_REVIEW','verifier':'codex:/root/evolution_verifier','source_revision':'65c66a4707c3fe714899d9819a50d26b5dcce853',
 'verdict':'PASS_ASYNC_BOUNDARY_START_CANCEL_FIX','findings':[],
 'scope':'Only Start cancellation cleanup before returning no Process handle; not whole S2/coordinator/crash recovery or LIVE.',
 'validation':{'independent_assertions_pass':5,'command_exit_code':0,'author_targeted_test_also_replayed':True,'actual_owned_native_processes':2,'observations':['The independent test cancels inside BeforeResume while holding the callback open for 60ms; Start does not return prematurely.','After the callback is released, Start returns nil/context.Canceled within the bound.','A host-pinned process handle is already signalled, the exact owned staging path queried from that process is already removed, and no child output was ever emitted.']},
 'prior_indices_verified_unchanged':indices,
 'limits':['Callbacks remain trusted host code required to return; an indefinitely stuck callback has no demonstrated forced-unwind mechanism. Waiting for owned cleanup intentionally prevents returning an unobservable still-running process.','Only two fresh no-secret native fixtures were launched; no production process, database or provider was accessed.','This focused change does not accept the pending full runtime S2 coordinator, checkpoint/resume or crash matrix.'],
 'whole_S2_accepted':False,'LIVE_qualified':False,'BOUNDED_AUTO_granted':False,
}
put(OUT/'review.json',review)
(OUT/'review.md').write_text('# Start cancellation cleanup review\n\nVerdict: **PASS_ASYNC_BOUNDARY_START_CANCEL_FIX** at `65c66a4`.\n\nThe independent native probe cancelled while BeforeResume remained blocked for 60ms. Start waited; after callback release it returned nil/context.Canceled only after the held process handle was signalled, the actual staging directory was removed and child output remained empty. Five independent assertions and the author targeted test passed.\n\nEarlier review indices are unchanged. This accepts only the startup cancellation cleanup fix, not full runtime S2, crash recovery or LIVE behavior.\n',encoding='utf-8')
files=[{'path':p.relative_to(OUT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='index.json'];put(OUT/'index.json',{'source_revision':review['source_revision'],'files':files})
for row in files:assert sha(OUT/row['path'])==row['sha256']
print(json.dumps({'verdict':review['verdict'],'review_sha256':sha(OUT/'review.json'),'index_sha256':sha(OUT/'index.json'),'files':len(files)}))
