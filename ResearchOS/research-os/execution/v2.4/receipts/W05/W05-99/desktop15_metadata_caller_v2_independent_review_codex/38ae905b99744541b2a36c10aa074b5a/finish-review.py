from pathlib import Path
import ast,json,hashlib
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent
B=R/'execution/v2.4/receipts/W13/W13-03/desktop15_root_parameters_codex/8792799f829a23452ae5d89a59e1b0cf'
Q=R/'execution/v2.4/receipts/W05/W05-99/root_registration_r332_readonly_review_codex/491c746101784dceae0e0e923bc685fc'
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
 return pin(O/n)
a=(B/'root-metadata-phases.py').read_bytes();b=(B/'root-metadata-phases.v2.py').read_bytes();at=a.decode();bt=b.decode()
assert hashlib.sha256(a).hexdigest()=='4c72cb2065b5bdc845aea008676f02e1c79723f9d605eb03e7707f1779a67f23'
assert hashlib.sha256(b).hexdigest()=='6ae5a1655ca465d3475e441b30f8bda635817dfd99792513f3f8ffa10fb2dd2a'
def function(s):return next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name=='invoke')
oldfunc=ast.get_source_segment(at,function(at));newfunc=ast.get_source_segment(bt,function(bt))
tail="\nneed(sys.flags.isolated and sys.flags.no_site"
assert bt.count(newfunc+'\n'+tail)==1 and at.count(oldfunc+tail)==1
inverse=bt.replace(newfunc+'\n'+tail,oldfunc+tail,1).replace('import argparse,hashlib,json,os,subprocess,traceback','import argparse,hashlib,json,os,subprocess',1).replace("invoke('metadata-'+a.phase,command,env,1500)","invoke('metadata-'+a.phase,command,env,900)",1)
assert inverse.encode()==a
oldaudit=json.loads((O/'audit.json').read_bytes());assert len(oldaudit['failed'])==1 and oldaudit['failed'][0]['check']=='wholebyte inverse exactly three authorized changes'
checks=[dict(x) for x in oldaudit['checks']]
for x in checks:
 if not x['passed']:x.update(passed=True,check='wholebyte inverse: invoke including exactly one following LF, traceback import, timeout1500')
assert all(x['passed'] for x in checks)
origin=pin(O/'failure-origin.0b6dbd.json')
ar=save('audit.corrected.json',{'checks':checks,'count':len(checks),'failed':[],'reused_prior_successful_checks':30,'original_audit_ref':pin(O/'audit.json'),'original_audit_actual_outer_exit':1,'original_audit_explicit_Python_exit':1,'correction':'Only exact function separator LF is included in inverse; no trim/rstrip or generic normalization. Existing raw source unchanged.','new_failure_origin_refs':[origin],'candidate_executions':0})
rr=save('review.json',{'schema':'researchos.metadata-outer-caller-static-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'READY_FOR_ROOT_ONCE_ONLY_PINNED_METADATA_PHASE_CALLS','requested_changes':[],'caller_ref':pin(B/'root-metadata-phases.v2.py'),'caller_sha256':hashlib.sha256(b).hexdigest(),'original_caller_ref':pin(B/'root-metadata-phases.py'),'original_REQUEST_ref':pin(Q/'outer-caller-review.json'),'registration_review_ref':pin(Q/'review.json'),'audit_ref':ar,'source_diff_ref':pin(O/'source.diff'),'checks_passed':31,'actual_caller_executed':False,'actual_registration_executed':False,'new_failure_origins':[origin],'closure':'R332-OUTER-01 statically resolved: request/raw-open/subprocess first error retained without immediate reraise; raw refs nullable independently; raw/invocation-save secondary errors preserved; original stderr prints first and secondary, child native integer/NULL remains distinct from caller exit1.','exact_delta':'invoke body plus exactly one separator LF; traceback import; metadata outer900→1500. Whole inverse equals original bytes. All other function ASTs and downstream mode/ref/tuple/env conditions unchanged.','limits':['Each run/seal/grant phase once, pinned script/prepared/review; no automatic retry.','1500 is outer metadata observation timeout, no change to internal engine1200 or source integration900/1200 budgets. Timeout can leave partial metadata; preserve forward-only intent and stop. No runtime-fit guarantee.','Outer subprocess is not owned Job or OS lifecycle proof; actual inner Jobs remain required.','No source import/Go/SQL/HTTP/SDK/model/formal acceptance. Source integration still needs actual registration/seal/grant and separately reviewed owned launcher.'],'audit_failure_accounting':'Original0b6dbd actualouter1/Python1 preserved once outside fixed516. False audit predicate does not erase tool failure or become a candidate runtime failure. Changed pure readonly finalizer only; no old audit rerun.','status':'STOPPED'})
hr=save('handoff.json',{'schema':'researchos.public-review-handoff.v1','review_ref':rr,'decision':'READY_FOR_ROOT_ONCE_ONLY_PINNED_METADATA_PHASE_CALLS','manifest_path':str(O/'manifest.json'),'checks_passed':31,'new_failure_origins':[origin],'status':'STOPPED'})
rows=[pin(p) for p in sorted(O.iterdir()) if p.is_file()]
mr=save('manifest.json',{'schema':'researchos.public-review-manifest.v1','count':len(rows),'entries':rows,'self_excluded':True})
print(json.dumps({'review':rr,'manifest':mr,'handoff':hr,'failure_origin':origin},ensure_ascii=False))
