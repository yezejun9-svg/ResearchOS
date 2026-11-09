from pathlib import Path
import ast,hashlib,json,difflib
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent
B=R/'execution/v2.4/receipts/W13/W13-03/desktop15_root_parameters_codex/8792799f829a23452ae5d89a59e1b0cf'
Q=R/'execution/v2.4/receipts/W05/W05-99/root_registration_r332_readonly_review_codex/491c746101784dceae0e0e923bc685fc'
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,d):
 with (O/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
 return pin(O/n)
checks=[]
def ck(v,k):checks.append({'check':k,'passed':bool(v)})
old=(B/'root-metadata-phases.py').read_bytes();new=(B/'root-metadata-phases.v2.py').read_bytes()
ck(hashlib.sha256(old).hexdigest()=='4c72cb2065b5bdc845aea008676f02e1c79723f9d605eb03e7707f1779a67f23' and len(old)==5082,'old unchanged')
ck(hashlib.sha256(new).hexdigest()=='6ae5a1655ca465d3475e441b30f8bda635817dfd99792513f3f8ffa10fb2dd2a' and len(new)==6364,'v2 fixed pin')
a=ast.parse(old);b=ast.parse(new);oldtext=old.decode('utf-8');newtext=new.decode('utf-8')
an=next(x for x in a.body if isinstance(x,ast.FunctionDef) and x.name=='invoke');bn=next(x for x in b.body if isinstance(x,ast.FunctionDef) and x.name=='invoke')
ab=ast.get_source_segment(oldtext,an);bb=ast.get_source_segment(newtext,bn)
reverse=newtext.replace(bb,ab,1).replace('import argparse,hashlib,json,os,subprocess,traceback','import argparse,hashlib,json,os,subprocess',1).replace("invoke('metadata-'+a.phase,command,env,1500)","invoke('metadata-'+a.phase,command,env,900)",1)
ck(reverse.encode('utf-8')==old,'wholebyte inverse exactly three authorized changes')
af={x.name:ast.dump(x,include_attributes=False) for x in a.body if isinstance(x,ast.FunctionDef)};bf={x.name:ast.dump(x,include_attributes=False) for x in b.body if isinstance(x,ast.FunctionDef)}
ck({k:v for k,v in af.items() if k!='invoke'}=={k:v for k,v in bf.items() if k!='invoke'},'other function AST byte semantics unchanged')
calls=[x for x in ast.walk(bn) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and isinstance(x.func.value,ast.Name) and x.func.value.id=='subprocess' and x.func.attr=='run'];ck(len(calls)==1,'single subprocess call no retry')
maintry=next(x for x in bn.body if isinstance(x,ast.Try));ck(len(maintry.handlers)==1 and not any(isinstance(x,ast.Raise) for x in ast.walk(maintry.handlers[0])),'first exception held no immediate raise')
ck("phase='request'" in bb and "phase='open-raw'" in bb and "phase='native-launch'" in bb and "phase='native-completed'" in bb,'all invoke phases explicit')
ck("refs={'stdout_ref':None,'stderr_ref':None}" in bb and "for field,suffix in [('stdout_ref','.stdout.raw'),('stderr_ref','.stderr.raw')]" in bb,'raw refs separately nullable')
ck("secondary.append({'phase':'seal-'+field" in bb and "'phase':'save-invocation'" in bb,'raw and invocation save secondary retention')
ck("'actual_native_exit':result.returncode if result is not None else None" in bb and "'actual_native_exit':result.returncode}" in bb,'real child native integer or NULL')
ck("file=sys.stderr" in bb and "raise SystemExit(1)" in bb and "'source_metadata_may_be_partial':True" in bb,'failure diagnostics before exit1 partial preserved')
ck("'outer_OS_lifecycle_qualification':False" in bb and "'automatic_retry':False" in bb and "'counter_reset':False" in bb,'no lifecycle/retry/reset claim')
ck("invoke('metadata-'+a.phase,command,env,1500)" in newtext,'outer1500 metadata only')
code=ast.literal_eval(next(x.value for x in b.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CODE_REFS' for t in x.targets)))
for name,r in code.items():
 current=pin(Path(r['path']));ck(current['sha256']==r['sha256'] and current['bytes']==r['bytes'],'code pin current '+name)
ck(pin(Q/'review.json')['sha256']=='9d27b07ea4681f01b67c654e7423bc700395895bd5c06bf03ad64b9ca17e3a66','registration READY unchanged')
ck(pin(Q/'outer-caller-review.json')['sha256']=='0ca19f6b266480e1073b7b846dec421843e846e1ed931cbccd6a547b7a5e9be5','old REQUEST retained')
for phase in ['run','seal','grant']:
 for suffix in ['request.json','stdout.raw','stderr.raw','invocation.json']:ck(not (B/('metadata-'+phase+'.'+suffix)).exists(),'unused '+phase+'.'+suffix)
with (O/'source.diff').open('xb') as f:f.write(''.join(difflib.unified_diff(oldtext.splitlines(True),newtext.splitlines(True),fromfile='original-v1',tofile='candidate-v2')).encode('utf-8'))
audit=save('audit.json',{'checks':checks,'count':len(checks),'failed':[x for x in checks if not x['passed']],'target_executions':0,'module_imports':0,'new_failure_origins':[]})
assert all(x['passed'] for x in checks)
rr=save('review.json',{'schema':'researchos.metadata-outer-caller-static-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'READY_FOR_ROOT_ONCE_ONLY_PINNED_METADATA_PHASE_CALLS','requested_changes':[],'caller_ref':pin(B/'root-metadata-phases.v2.py'),'caller_sha256':hashlib.sha256(new).hexdigest(),'original_caller_ref':pin(B/'root-metadata-phases.py'),'original_REQUEST_ref':pin(Q/'outer-caller-review.json'),'registration_review_ref':pin(Q/'review.json'),'audit_ref':audit,'source_diff_ref':pin(O/'source.diff'),'checks_passed':len(checks),'actual_caller_executed':False,'actual_registration_executed':False,'new_failure_origins':[],'closure':'R332-OUTER-01 resolved statically: request/raw-open/subprocess first error retained; each raw ref nullable and independently captured; invocation save failure secondary or first if sole error; actual child native exit retained separately; stderr reports first and secondary before caller exit1.','semantics_preserved':['Only invoke body, traceback import and metadata outer1500 timeout changed; whole-byte inverse and all other function ASTs match original.','Exactly pinned run/seal/grant and prepared refs; exact review schema/actor/tuple remain; public environment four keys; no retry.','No change to source controller900/outer1200, metadata engine1200 or internal owned Jobs. Outer subprocess provides observation, not lifecycle qualification.','Timeout may leave partial metadata; preserve intent/raw and stop.1500 does not promise execution will fit.','Root may invoke each fresh metadata phase once; source controller execution still requires separate reviewed owned caller and actual grant.'],'status':'STOPPED'})
hr=save('handoff.json',{'schema':'researchos.public-review-handoff.v1','review_ref':rr,'decision':'READY_FOR_ROOT_ONCE_ONLY_PINNED_METADATA_PHASE_CALLS','manifest_path':str(O/'manifest.json'),'checks_passed':len(checks),'new_failure_origins':[],'status':'STOPPED'})
mr=save('manifest.json',{'schema':'researchos.public-review-manifest.v1','count':len(list(O.iterdir())),'entries':[pin(x) for x in sorted(O.iterdir()) if x.is_file()],'self_excluded':True})
print(json.dumps({'review':rr,'manifest':mr,'handoff':hr,'checks':len(checks),'new_failures':0},ensure_ascii=False))
