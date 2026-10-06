from pathlib import Path
import hashlib,json,subprocess
OUT=Path(__file__).resolve().parent;PRIOR=OUT.parent;ROOT=PRIOR.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def put(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
old=read(PRIOR/'index.json');assert sha(PRIOR/'index.json')=='ec5729b5bd65247383025e244a7351e43fa4d70f24e9bc93554006b1a64c0e14'
for row in old['files']:assert sha(PRIOR/row['path'])==row['sha256']
audit=read(OUT/'source-audit.json')
for row in audit['sources']:
 raw=subprocess.check_output(['git','show',audit['source_revision']+':'+row['path']],cwd=ROOT)
 assert hashlib.sha256(raw).hexdigest()==row['sha256']==sha(OUT/'source'/Path(row['path']).name)
assert read(OUT/'command.json')['exit_code']==0
assertions=read(OUT/'assertions.json');assert len(assertions)==21 and all(row['status']=='PASS' for row in assertions)
assert read(OUT/'author-evidence/receipt.json')['exit_code']==0
report={
 'artifact_kind':'INDEPENDENT_ASYNC_BOUNDARY_FIX_REVIEW','verifier':'codex:/root/evolution_verifier',
 'verdict':'PASS_ASYNC_BOUNDARY_SLICE','source_revision':audit['source_revision'],
 'prior_source_revision':'2f30646a57c0c18a022c2080ec3aeb2e9d9d559e',
 'prior_review_reference':'../review.json','prior_review_sha256':sha(PRIOR/'review.json'),
 'prior_index_reference':'../index.json','prior_index_sha256':sha(PRIOR/'index.json'),
 'prior_index_files_verified_unchanged':len(old['files']),
 'findings':[], 'resolved_findings':[{'id':'S2-ASYNC-001','priority':'P2','resolution':'Context-aware single writer gate replaces the uninterruptible mutex. The bounded context begins before queue admission; already-cancelled and process-stopped writes refuse before writing. Expired queued callers do not cancel the active writer, while in-flight blocked write expiry still cancels the job.', 'evidence':'native/queued-write-fixed.json','observed_deadline_ms':40,'observed_return_ms':40,'active_writer_preserved':True}],
 'validation':{'command_exit_code':0,'independent_assertion_instances_pass':21,'independent_assertion_instances_fail':0,'test_results':read(OUT/'test-results.json'),'author_fix_evidence_exit_code':0,'prior_failed_probe_preserved':True},
 'inherited_validation':'Original frozen review retains 34 passing primary assertions, two passing cleanup assertions and one reproduced queued-deadline failure. The failure is resolved only for the new revision by this separate review; no earlier failed command is relabelled as passing.',
 'limits':['Only the native asynchronous AppContainer boundary at original source 2f30646 plus the targeted repair at 678a68c is reviewed. No complete S2 coordinator/domain/typed-bridge/workbench acceptance, construction gate, LIVE or BOUNDED_AUTO qualification is granted.']+read(PRIOR/'review.json')['limits'][1:],
 'whole_S2_accepted':False,'LIVE_qualified':False,'BOUNDED_AUTO_granted':False,
 'scope':'Native asynchronous sandbox boundary only. No coordinator/domain/bridge implementation or formal owned case is accepted.'
}
put(OUT/'review.json',report)
(OUT/'review.md').write_text('# S2 async boundary fix review\n\nVerdict: **PASS_ASYNC_BOUNDARY_SLICE** at `678a68c`. The previously reproduced P2 S2-ASYNC-001 is resolved.\n\nThe queued 40ms write returned in 40ms with `context deadline exceeded`, while the active writer and child remained alive until explicit cancellation. An already-cancelled frame was never sent, and a subsequent valid frame completed. Eight concurrent frames remained atomic; the in-flight 100ms blocked-write deadline still stopped the job and released resources. All 21 independent assertion instances and two related author test groups passed.\n\nThe original 37-file review index and its failing command were rehashed unchanged. This separate report supersedes only the finding for the repaired revision. It grants no whole-S2, coordinator/bridge, LIVE or BOUNDED_AUTO acceptance.\n',encoding='utf-8')
files=[{'path':p.relative_to(OUT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='index.json']
put(OUT/'index.json',{'source_revision':audit['source_revision'],'files':files})
for row in files:assert sha(OUT/row['path'])==row['sha256']
print(json.dumps({'verdict':report['verdict'],'review_sha256':sha(OUT/'review.json'),'index_sha256':sha(OUT/'index.json'),'files':len(files)}))
