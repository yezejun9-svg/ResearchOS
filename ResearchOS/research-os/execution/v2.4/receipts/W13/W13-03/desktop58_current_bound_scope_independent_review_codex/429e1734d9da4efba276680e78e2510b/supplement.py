from pathlib import Path
import hashlib,json,re,ast
O=Path(__file__).parent;R=Path('D:/作品集/ResearchOS/research-os');N=R/('execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r335-'+O.name)
C=[];refs={}
def ck(n,v,d=None):C.append({'check':n,'passed':bool(v),'detail':d})
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def raw(p):
 p=path(p);b=p.read_bytes();refs[str(p)]={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b
def read(p):return json.loads(raw(p))
def pin(r):
 p=path(r['path']);b=raw(p);ck('actual pin '+str(p),refs[str(p)]['sha256']==r['sha256'] and len(b)==r['bytes']);return b
def const(p):
 d={}
 for x in ast.parse(raw(p)).body:
  if isinstance(x,ast.Assign):
   for t in x.targets:
    if isinstance(t,ast.Name):
     try:d[t.id]=ast.literal_eval(x.value)
     except (TypeError,ValueError):pass
 return d
s=read(N/'scope_registration.json');b=read(N/'binding.pre-review.json');a=read(O/'audit.json')
ck('complete independent main audit has no failed checks',not a['failed_checks'],len(a['checks']))
q=read(s['current58_CLI2_qualification_ref']['path']);qmf=read(s['current58_CLI2_manifest_ref']['path']);e=q['evidence_refs'];c=read(e['root_completion_ref']['path']);req=read(c['closure_request_ref']['path']);mf=read(e['root_closed_manifest_ref']['path']);wanted={}
def add(v):
 if isinstance(v,dict) and set(v)=={'path','sha256','bytes'}:
  rr=dict(v,path=str(path(v['path']).resolve()));key=rr['path'].casefold()
  if key in wanted:ck('duplicate READS same pin',wanted[key]==rr,key)
  wanted[key]=rr
add(c['closure_request_ref'])
for k,v in req.items():
 if k.endswith('_ref'):add(v)
for x in req['additional_sealed_refs']:add(x)
for k in ['executor_manifest_ref','launcher_manifest_ref']:
 for x in read(req[k]['path'])['files']:add(x)
grant=read(req['grant_ref']['path']);add(grant['scope_ref'])
for x in c['authorization_canonical_copy_refs']:add(x)
for k,v in read(req['caller_invocation_ref']['path']).items():
 if k.endswith('_ref'):add(v)
add(e['root_completion_ref']);actual={str(path(v['path']).resolve()).casefold():dict(v,path=str(path(v['path']).resolve())) for v in mf['members']}
ck('Root aggregate exact169 set and pins, no arbitrary multi-root',wanted==actual and len(actual)==169)
ck('aggregate current58 same execution',q['source_commit']==c['source_commit']==req['source_commit']==s['source_commit'] and q['run_uuid']==c['run_uuid']==req['run_uuid'])
ex=read(e['executor_manifest_ref']['path']);la=read(e['launcher_manifest_ref']['path']);result=read(e['result_ref']['path']);cli_scope=read(e['scope_ref']['path'])
ck('actual manifest cardinalities Q19 E125 L7 Root169',qmf['count']==len(qmf['entries'])==19 and ex['count']==len(ex['files'])==125 and la['count']==len(la['files'])==7 and len(actual)==169)
members={str(path(x['path']).resolve()):x for x in ex['files']};cases=[]
ck('exact14 stages',len(result['stages'])==result['native_calls']==14)
for i,f in enumerate(q['case_facts']):
 label='case-%02d'%i;stage=result['stages'][-2+i];p=path(f['invocation_ref']['path']);v=read(f['verified_ref']['path']);case=result['cases'][i]
 ck('stage/fact/invocation exact '+label,stage['label']==label and stage['result_ref']==f['invocation_ref'] and p.name==label+'.invocation.json' and path(f['verified_ref']['path'])==p.with_name(label+'.verified.json'))
 ck('verified exact result '+label,v==case)
 streams={}
 for stream in ('stdout','stderr'):
  rp=str(p.with_name(label+'.'+stream+'.raw').resolve());ck('sealed actual raw member '+label+'/'+stream,rp in members)
  streams[stream]=pin(members[rp]) if rp in members else b''
 events=[json.loads(line) for line in streams['stdout'].splitlines()];leaf='TestCLIProtocolInteractiveAuthority/'+f['case_id'];run=sum(x.get('Action')=='run' and x.get('Test')==leaf for x in events);passed=sum(x.get('Action')=='pass' and x.get('Test')==leaf for x in events)
 ck('actual leaf one RUN/PASS noFAIL/SKIP '+label,run==passed==1 and not any(x.get('Action') in ('fail','skip') for x in events))
 ck('expected native0 CLI0or3 '+label,f['native_test_exit']==0 and f['CLI_exit']==[0,3][i] and f['state']=='QUALIFIED')
 expected=path(cli_scope['new_export_root'])/'.cli43-build'/'case-evidence'/label/('TestCLIProtocolInteractiveAuthority_'+f['case_id'])/'closed-proof.json';ck('exact proof path '+label,path(case['proof_ref']['path'])==expected);pin(case['proof_ref'])
 cases.append({'case':f['case_id'],'raw_events':len(events),'leaf_run':run,'leaf_pass':passed,'stderr_bytes':len(streams['stderr'])})
for row in b['metadata_code_refs']:
 p=path(row['path']);co=const(p)
 if p.name in ('scope_builder.py','prepare.py','register.py','run.py','seal.py','grant_preflight.py'):
  tree=ast.parse(raw(p));paths=[n.args[0].value for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='Path' and n.args and isinstance(n.args[0],ast.Constant) and isinstance(n.args[0].value,str)]
  module_rows=[r for r in b['metadata_code_refs'] if paths and path(r['path'])==path(paths[0])]
  literals={n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str)}
  ck('Root wrapper module path+hash pinned in metadata8 '+p.name,len(paths)==1 and len(module_rows)==1 and module_rows[0]['sha256'] in literals)
obs=read(N/'tool-observations.third-scope.closed.original.json');ck('actual original observation SHA/bytes',refs[str(N/'tool-observations.third-scope.closed.original.json')]['sha256']=='2f5a4383983c36fa091b46983a100c5be85326c963cd5ec37bc8e5b4f8db6906' and refs[str(N/'tool-observations.third-scope.closed.original.json')]['bytes']==20662)
toolresults=[]
def walk(x):
 if isinstance(x,dict):
  if 'chunk_id' in x and 'output' in x:toolresults.append({'chunk_id':x['chunk_id'],'session_id':x.get('session_id'),'exit_code':x.get('exit_code'),'native_markers':re.findall(r'ACTUAL_[A-Z_]*EXIT[=:]\s*(-?\d+)',x['output'])})
  for v in x.values():walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
walk(obs);ck('all reported completion exits0',all(x['exit_code'] in (None,0) and all(y=='0' for y in x['native_markers']) for x in toolresults),toolresults)
before=read(b['canonical_before_ref']['path'])['entries']
for x in before:ck('final canonical copy '+x['canonical_path'],raw(x['canonical_path'])==raw(x['ref']['path']))
for k in ('output_root','outer_output_root','export_root','new_authorization_root','new_grant_preflight_root'):ck('still absent '+k,not path(s[k]).exists())
data={'schema':'researchos.desktop58-bound-scope-static-supplement.v1','checks':C,'failed':[x for x in C if not x['passed']],'cases':cases,'input_refs':list(refs.values()),'tool_completion_facts':toolresults,'main_git_frozen_shape':s['main_git'],'actual_candidate_execution':False,'actual_product_execution':False,'new_failure_origins':[]}
with (O/'supplement.json').open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'checks':len(C),'failed':data['failed'],'cases':cases,'main_git_frozen_shape':s['main_git'],'tools':toolresults},ensure_ascii=False))
