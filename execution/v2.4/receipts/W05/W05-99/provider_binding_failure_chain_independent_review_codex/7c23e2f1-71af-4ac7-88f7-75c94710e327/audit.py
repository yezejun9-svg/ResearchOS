from pathlib import Path
import json,hashlib,sqlite3,datetime,subprocess,os
R=Path.cwd();W=R/'.local/worktrees/codex-w0599-provider-binding';P=W/'execution/v2.4/receipts/W05/W05-99/provider_binding_executor_codex/provider-39d6478d4a884156b0881788325e4c63';O=R/'execution/v2.4/receipts/W05/W05-99/provider_binding_failure_chain_independent_review_codex/7c23e2f1-71af-4ac7-88f7-75c94710e327';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(O/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
audit=[]
def read(p,snapshot=True):
 raw=p.read_bytes();e={'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
 if snapshot:
  q=O/'readraw'/str(len(audit));q.parent.mkdir(exist_ok=True);q.write_bytes(raw);e['snapshot']=q.relative_to(R).as_posix()
 audit.append(e);return raw
old=json.loads(read(P/'failure_origins.json'));new=json.loads(read(P/'failure_origins.v2.json'));seal=json.loads(read(P/'held_candidate_10_seal.json'));assert audit[0]['sha256']=='4ba98ed94fe1438f952a0bc792808f989a45a01a90203405578dbbb46dfdcd23';assert len(new['entries'])==9
failures=[]
for x in new['entries']:
 facts={}
 for k in ['origin','invocation','stdout','stderr']:
  e=x[k];q=W/e['path'];b=read(q);assert hashlib.sha256(b).hexdigest()==e['sha256'];facts[k]=str(q)
 j=json.loads((W/x['invocation']['path']).read_bytes());assert j.get('exit',j.get('actual_exit'))==1
 failures.append({'stage':x['stage'],'group':x['group'],'exit':1,'unique_origin':x['invocation'],'cause_reported':x['cause'],'files_verified':facts})
for group,base in [('source_and_audits',P/'sealed-candidate-10'),('actual_domain_run_evidence',P)]:
 for n,e in seal[group].items():
  q=base/n;b=read(q,snapshot=not q.suffix=='.sqlite');assert hashlib.sha256(b).hexdigest()==e['sha256'] and len(b)==e['bytes']
e=seal['candidate_source_vector_ref'];b=read(W/e['path']);assert hashlib.sha256(b).hexdigest()==e['sha256']
registration=json.loads(read(P/'authority-inputs/0-scope_registration.json'));read(P/'authority-inputs/2-source_scope_review.json')
sources=[]
for n in registration['paths']:
 p=W/n;b=read(p);sources.append({'path':n,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'snapshot':audit[-1]['snapshot']})
for n in ['08_AGENT_EXECUTION_GOAL.md','18_EXISTING_REPOSITORY_MIGRATION.md','21_EXECUTION_CARDS.md']:read(R/'.local/worktrees/v24-continuation/spec/v2.4'/n)
closure=P/'closure-f7bf47acb6f94c48b5a0095b200cc9e8';read(closure/'summary.json');counts={}
for lane in ['domain-test','bridge-test','cli-test','js']:
 p=closure/(lane+'.result.json');j=json.loads(read(p));raw=read(closure/(lane+'.stdout.raw'));read(closure/(lane+'.stderr.raw'));assert hashlib.sha256(raw).hexdigest()==j['stdout_sha256'];c={'pass':0,'fail':0,'skip':0};skips=[]
 if lane!='js':
  for line in raw.splitlines():
   try:x=json.loads(line)
   except:continue
   if x.get('Test') and x.get('Action') in c:
    c[x['Action']]+=1
    if x['Action']=='skip':skips.append(x['Test'])
 else:
  import re
  for label,k in [('pass','pass'),('fail','fail'),('skipped','skip')]:
   m=re.search(rb'^# '+label.encode()+rb' (\d+)',raw,re.M)
   c[k]=int(m.group(1)) if m else None
 counts[lane]={'exit':j['exit'],'counts':c,'skipped_tests':skips,'argv':j['argv']}
dbqueries={}
for n,e in seal['actual_domain_run_evidence'].items():
 if not n.endswith('final-fixture.sqlite'):continue
 p=P/n;before=sha(p);db=sqlite3.connect(p.resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
 try:
  kinds=dict(db.execute('SELECT kind,count(*) FROM domain_objects GROUP BY kind'))
  states=list(db.execute("SELECT json_extract(body,'$.state'),count(*) FROM resource_effects GROUP BY json_extract(body,'$.state')"))
  modes=[]
  for (s,) in db.execute('SELECT manifest FROM runtime_dispatches'):
   m=json.loads(s);modes.append(m.get('admission',{}).get('mode'))
  dbqueries[n]={'sha256':before,'kinds':kinds,'effect_state_row_counts':states,'dispatch_modes':modes,'readonly_immutable':True}
 finally:db.close()
 assert sha(p)==before
save('failure_chain_audit.json',failures);save('held_seal_audit.json',{'source_entries':len(seal['source_and_audits']),'domain_evidence_entries':len(seal['actual_domain_run_evidence']),'all_hashes_match':True,'current_source9':sources,'counts_current_nonheld_cohort':counts,'held_original_db_metadata':dbqueries,'held_positive_tests_not_executed':True,'cost_boundary':new['cost_boundary']})
save('actual_read_audit.json',audit);print(json.dumps({'audit_files':len(audit),'failure_origins':len(failures),'counts':counts,'held_dbs':len(dbqueries)}))
