from pathlib import Path
import json,hashlib,base64,traceback
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99';U='c4f309c5528f5d42be5e7eeb146a20aa';O=Path(__file__).parent;N=P/'integration_codex'/('cli43-fresh-held2-r331-'+U);E=P/'cli43_fresh_compiler_executor_codex'/U;L=P/'cli43_fresh_compiler_launcher_codex'/U
checks=[];refs={}; mismatches=[];raw_count=0
def path(x):
 p=Path(x);return p if p.is_absolute() else R/p
def ref(x):
 p=path(x);h=hashlib.sha256();length=0
 with p.open('rb') as f:
  while b:=f.read(1024*1024):h.update(b);length+=len(b)
 a={'path':p.as_posix(),'sha256':h.hexdigest(),'bytes':length};refs[a['path']]=a;return a
def ck(n,v):checks.append({'check':n,'passed':bool(v)})
def verify(x):
 p=path(x['path']);a=refs.get(p.as_posix()) or ref(p);ck('pin '+str(p),a['sha256']==x['sha256'] and a['bytes']==x['bytes']);return p
def read(x):ref(x);return json.loads(path(x).read_bytes())
def save(n,x):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def rowmap(rows):return {path(x['path']):(x['sha256'],x['bytes']) for x in rows}
def job(rr):
 j=rr['job_cleanup'];return rr['actual_exit']==0 and rr['error'] is None and rr['timed_out'] is False and all(j[k] is True for k in ['assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed']) and j['active_processes_last_observed']==0 and j['errors']==[]
def rawscan(value,pointer,file):
 global raw_count
 if isinstance(value,dict):
  if all(k in value for k in ['raw_base64','bytes','sha256']):
   actual=b'' if value['raw_base64'] is None and value['bytes']==0 else base64.b64decode(value['raw_base64'],validate=True);raw_count+=1;dh=hashlib.sha256(actual).hexdigest()
   if len(actual)!=value['bytes'] or dh!=value['sha256']:mismatches.append({'file_ref':ref(file),'json_pointer':pointer,'recorded_bytes':value['bytes'],'recorded_sha256':value['sha256'],'derived_bytes':len(actual),'derived_sha256':dh,'raw_base64_is_null':value['raw_base64'] is None,'decoded_prefix_utf8':actual[:100].decode('utf-8',errors='replace')})
  for k,v in value.items():rawscan(v,pointer+'/'+k,file)
 elif isinstance(value,list):
  for i,v in enumerate(value):rawscan(v,pointer+'/'+str(i),file)

s=read(N/'scope_registration.json');a=read(O/'audit.json');supp=read(O/'supplement.json');X=Path(s['new_export_root']);plan=read(verify(s['instrumentation_ref']));raw=verify(s['instrumented_source_ref']).read_text(encoding='utf-8');anchors=[]
for i,c in reversed(list(enumerate(plan['changes']))):
 count=raw.count(c['new']);ck('actual runner inverse block '+str(i),count==1);anchors.append({'index':i,'count':count});raw=raw.replace(c['new'],c['old'],1)
ck('full eight change inverse matches currentMain',raw.encode()==(R/plan['original_path']).read_bytes())
ck('prior supplemental falsepredicates exactly seven redundant inline inverses',len(supp['failed_checks'])==7 and all(x['check']=='wholeblock inverse anchor exact' for x in supp['failed_checks']))
runner=verify(s['runner_ref']).read_text(encoding='utf-8');ck('producer inverses changes only',"for c in reversed(plan['changes']):" in runner and "plan['exact_scoped_inline_edits']" not in runner)
g=read(Path(s['new_authorization_root'])/'authorization.execute.json');authority=read(verify(s['current43_authority_ref']));sourceproof=[]
for r in authority['sealed_integration_refs']:verify(r);sourceproof.append(r)
result=read(E/'result.json');closure=read(E/'compiled-closure.json');casefacts=[]
for ci,leaf in enumerate(s['ordered_cases']):
 inv=read(E/f'case-{ci:02d}.invocation.json');d=inv['result']['debug_capture'];gen=d['process_generations'];expected=[closure['test2json'],closure['testexe'],closure['cli']]
 ck('case process generations exact executable hashes '+leaf,len(gen)==3 and all(x['image']['before']=={'sha256':y['sha256'],'bytes':y['bytes']} and x['image']['after']==x['image']['before'] and x['job_membership_observed'] is True for x,y in zip(gen,expected)))
 ck('case primary lifecycle no rejection '+leaf,d['complete'] is True and d['rejected_load_facts']==[] and len({(x['pid'],x['creation_time_100ns']) for x in gen})==3 and [x['independent_exit'] for x in gen]==([0,0,0] if ci==0 else [0,0,3]))
 casefacts.append({'case_id':leaf,'state':'QUALIFIED','native_test_exit':0,'CLI_exit':0 if ci==0 else 3,'generations':[{'pid':x['pid'],'creation_time_100ns':x['creation_time_100ns'],'independent_exit':x['independent_exit'],'image':x['image']} for x in gen],'invocation_ref':ref(E/f'case-{ci:02d}.invocation.json'),'verified_ref':ref(E/f'case-{ci:02d}.verified.json'),'stdout_ref':ref(E/f'case-{ci:02d}.stdout.raw'),'stderr_ref':ref(E/f'case-{ci:02d}.stderr.raw')})
for c in g['canonical_copies']:ck('final live canonical byte match '+c['canonical_path'],verify(c['ref']).read_bytes()==(R/c['canonical_path']).read_bytes());ref(R/c['canonical_path'])
head=(R/'.git/HEAD').read_text().strip();resolved=(R/'.git'/head[5:]).read_text().strip() if head.startswith('ref: ') else head;ck('final direct Main HEAD',resolved==s['source_commit'])
save('final-corrections.json',{'checks':checks,'failed_checks':[c for c in checks if not c['passed']],'input_refs':list(refs.values()),'inverse_block_counts':anchors,'case_facts':casefacts,'source_import_proof_refs':sourceproof,'correction':'Supplement audit incorrectly applied explanatory inline list and complete replacement list twice. Actual runner applies only complete changes; eight unique anchors reverse exactly. Prior seven predicate failures preserved, tool0; no product change or rerun.','new_native_or_product_failure':False,'target_executions':0})
print(json.dumps({'checks':len(checks),'failed_checks':[c for c in checks if not c['passed']],'ref':ref(O/'final-corrections.json')},ensure_ascii=False))
