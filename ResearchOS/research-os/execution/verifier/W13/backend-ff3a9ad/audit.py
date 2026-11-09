from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();O=R/'execution/verifier/W13/backend-ff3a9ad';D=R/'execution/receipts/W13/backend/f2f5b2a1-29f2-4d41-bc10-a61b9baa0cf8'
load=lambda p:json.loads(p.read_text(encoding='utf8'));sha=lambda b:hashlib.sha256(b).hexdigest();hf=lambda p:sha(p.read_bytes());checks=[]
def ck(k,ok,detail=None):
 checks.append({'id':k,'pass':bool(ok),'detail':detail})
 if not ok:print('FAIL',k)
index=load(R/'execution/receipts/W13/backend/evidence-index-0629719.json');before=load(D/'before.json');report=load(D/'report.json');deltas=[]
for path,h in index['files'].items():ck('author_index:'+path,hf(R/path)==h.removeprefix('sha256:'))
for path,h in report['raw_evidence_hashes'].items():ck('author_raw:'+path,hf(D/path)==h.removeprefix('sha256:'))
for path,h in before['source_manifest'].items():
 old=subprocess.check_output(['git','show','0629719:'+path],cwd=R);new=subprocess.check_output(['git','show','ff3a9ad:'+path],cwd=R)
 ck('author_source:'+path,sha(old)==h.removeprefix('sha256:'))
 if old!=new:deltas.append({'path':path,'author_sha256':sha(old),'current_sha256':sha(new)})
for path in ['internal/domain/workbench.go','internal/domain/workbench_stream.go','internal/domain/milestones.go','internal/domain/http.go','internal/domain/store.go','internal/domain/workbench_test.go','internal/domain/workbench_stream_test.go','internal/domain/workbench_security_test.go']:
 ck('stable_scope:'+path,not any(x['path']==path for x in deltas))
raw=[json.loads(x[len('W13_ASSERTION '):]) for x in (D/'stdout.txt').read_text(encoding='utf8').splitlines() if x.startswith('W13_ASSERTION ')]
parsed=[json.loads(x) for x in (D/'assertions.jsonl').read_text(encoding='utf8').splitlines()]
ck('raw_parser_exact',raw==parsed==[{k:v for k,v in a.items() if k!='raw_evidence'} for a in report['assertions']]);ck('author_22_inventory',len(raw)==22 and [x['assertion_id'] for x in raw]==report['assertion_ids'] and set(report['assertion_ids'])==set(before['expected_assertion_ids']))
for a in report['assertions']:
 rr=a['raw_evidence'];line=(D/rr['path']).read_text(encoding='utf8').splitlines()[rr['line']-1];ck('raw_line:'+a['assertion_id'],json.loads(line[len('W13_ASSERTION '):])=={k:v for k,v in a.items() if k!='raw_evidence'} and hf(D/rr['path'])==rr['sha256'].removeprefix('sha256:'))
for a in raw:ck('author_assertion:'+a['assertion_id'],a['expected']==a['actual'] and a['status']=='PASS')
ck('author_status',report['backend_status']=='PASS' and report['exit_code']==0 and not report['missing'] and not report['malformed'] and not report['changed_during_run'])
a={x['assertion_id']:x for x in raw};ck('author_heartbeat_raw',14_000<=a['W13-SSE-HEARTBEAT']['evidence']['elapsed_ms']<20_000)
own=[json.loads(x[len('INDEPENDENT_W13 '):]) for x in (O/'independent-run.stdout.txt').read_text(encoding='utf8').splitlines() if x.startswith('INDEPENDENT_W13 ')]
for x in own:ck('independent:'+x['id'],x['pass'] and x['expected']==x['actual'])
proof=load(O/'raw/TestIndependentW13TaskReleaseAndRealInvalidation/real-invalidation.json');old=next(x for x in proof['receipt']['input_refs'] if x['entity_type']=='Requirement')
ck('real_change_requirement_advanced',proof['changed_requirement']['revision']>old['revision'])
ck('real_change_independent_original',proof['receipt']['verdict']=='PASS' and proof['receipt']['verifier_principal_id'] not in proof['receipt']['executor_principal_ids'])
ck('real_change_new_publication_rejected',400<=proof['rejected_status']<500 and sum(x['accepted'] for x in proof['projection']['stages'])==0)
gap=load(O/'raw/TestIndependentW13SSEBoundaries/gap-recovery.json');ck('gap_recovery_exact_watermark',gap['status']==410 and gap['next']['sequence']==gap['snapshot']['as_of_event_sequence']+1)
sourcepaths=['internal/domain/workbench.go','internal/domain/workbench_stream.go','internal/domain/milestones.go','internal/domain/http.go','internal/domain/store.go','internal/domain/acceptance.go','internal/domain/acceptance_goal.go','internal/domain/orchestration_recovery.go','internal/domain/context.go','migrations/sqlite/0002_domain.sql']
sources=[{'path':p,'sha256':sha(subprocess.check_output(['git','show','ff3a9ad:'+p],cwd=R))} for p in sourcepaths]
(O/'source-hashes.json').write_text(json.dumps(sources,indent=2),encoding='utf8');(O/'independent-checks.json').write_text(json.dumps(own,indent=2),encoding='utf8')
result={'author_execution_base_revision':before['code_revision'],'author_committed_implementation':'06297197be5f8433ee85425874095029f11e208c','review_revision':subprocess.check_output(['git','rev-parse','ff3a9ad'],cwd=R,text=True).strip(),'author_index_files':len(index['files']),'author_sources':len(before['source_manifest']),'author_assertions':len(raw),'independent_assertions':len(own),'changed_sources':deltas,'checks':checks,'total':len(checks),'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks)}
(O/'audit.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in result.items() if k not in ['checks','changed_sources']}))
