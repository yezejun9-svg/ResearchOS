from pathlib import Path
import hashlib,json,re
O=Path(__file__).parent;R=Path('D:/作品集/ResearchOS/research-os');N=R/('execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r335-'+O.name)
def ref(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p):return json.loads(Path(p).read_bytes())
checks=[]
def ck(n,v):checks.append({'name':n,'passed':bool(v)})
s=read(N/'scope_registration.json');b=read(N/'binding.pre-review.json');a=read(O/'audit.json')
ck('49751 actual independent checks passed',len(a['checks'])==49751 and not a['failed_checks'])
refs=[];shapes=[]
def shape(v):
 if isinstance(v,dict):return {k:shape(x) for k,x in v.items()}
 if isinstance(v,list):return [shape(x) for x in v]
 if isinstance(v,str) and len(v)>300:return {'string_chars':len(v),'exit_markers':re.findall(r'ACTUAL_[A-Z_]*EXIT[=:]\s*-?\d+',v)}
 return v
for name,sha,size in [('tool-observations.scope-build.closed.json','12234937c37276571bc20af5c2ee92fba908a269f30fe8d9ec5337dc113feb57',9392),('tool-observations.binding-build.closed.json','265bbb83cdebaa1a2575b5d827ee240d804db772f494be5d4b79d69ff66cfe68',11415)]:
 r=ref(N/name);ck('original tool observation pin:'+name,r['sha256']==sha and r['bytes']==size);refs.append(r);shapes.append({'name':name,'shape':shape(read(N/name))})
entries=read(Path(b['canonical_before_ref']['path']))['entries']
for e in entries:ck('final live canonical:'+e['canonical_path'],(R/e['canonical_path']).read_bytes()==Path(e['ref']['path']).read_bytes())
for k in ['output_root','outer_output_root','export_root','new_authorization_root','new_grant_preflight_root']:ck('final fresh leaf:'+k,not Path(s[k]).exists())
for name in ['binding.json','prepare.started.json','prepared_refs.json','canonical-write.intent.json']:ck('actual preparation not executed:'+name,not (N/name).exists())
q=read(s['current58_CLI2_qualification_ref']['path']);e=q['evidence_refs'];c=read(e['root_completion_ref']['path']);req=read(c['closure_request_ref']['path']);mf=read(e['root_closed_manifest_ref']['path']);wanted={}
def add(v):
 if isinstance(v,dict) and set(v)=={'path','sha256','bytes'}:
  p=Path(v['path']);p=p if p.is_absolute() else R/p;row=dict(v,path=str(p.resolve()));key=row['path'].casefold()
  if key in wanted:ck('aggregate duplicate read samepin:'+key,wanted[key]==row)
  wanted[key]=row
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
add(e['root_completion_ref']);actual={str(Path(v['path']).resolve()).casefold():dict(v,path=str(Path(v['path']).resolve())) for v in mf['members']}
ck('CLI2 aggregate exact169 set+pins reconstructed anew',wanted==actual and len(actual)==169)
ck('CLI2 aggregate same actual current58 source/run',q['source_commit']==c['source_commit']==req['source_commit']==s['source_commit'] and q['run_uuid']==c['run_uuid']==req['run_uuid'])
data={'schema':'researchos.desktop58-bound-scope-final-readonly-supplement.v1','checks':checks,'failed':[x for x in checks if not x['passed']],'tool_observation_refs':refs,'tool_observation_shapes':shapes,'aggregate_member_count':len(actual),'candidate_executed':False,'new_failure_origins':[]}
with (O/'supplement.json').open('xb') as f:f.write((json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps({'checks':len(checks),'failed':data['failed'],'observation_shapes':shapes,'supplement_ref':ref(O/'supplement.json')},ensure_ascii=False))
