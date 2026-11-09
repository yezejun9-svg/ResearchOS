from pathlib import Path
import json,hashlib,re
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent
N=R/('execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r337-'+O.name)
L=R/'execution/v2.4/receipts/W13/W13-03/desktop58_old_failed_lease_closure_cas_codex/5e2a75ea3da546b28b20975cc6a4d18f'
C=[];refs=[]
def path(v):
 p=Path(v);return p if p.is_absolute() else R/p
def ck(n,v,d=None):C.append({'check':n,'passed':bool(v),'detail':d})
def pin(p):
 p=path(p);raw=p.read_bytes();r={'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)};refs.append(r);return r
def verify(r):
 a=pin(r['path']);ck('pin '+r['path'],a['sha256']==r['sha256'] and a['bytes']==r['bytes']);return path(r['path']).read_bytes()
def doc(p):pin(p);return json.loads(path(p).read_bytes())
v=doc(L/'canonical-write.verified.json');ck('actualCASverifiedSHA',pin(L/'canonical-write.verified.json')['sha256']=='d753faf0c4259a91fb4f4c8eed4278efe0997abf046f074aaaa1640ce8874437')
mf=doc(L/'manifest.closed.json')
for r in mf['members']:verify(r)
rv=json.loads(verify(v['review_ref']))
ck('closureReviewF08',rv.get('reviewer',rv.get('actor'))=='codex:/root/f08_whole_scope_review')
ck('actualclosedOldlease',v['after']==[336,164,614] and v['old_lease_closed_failed'] is True and v['execution_grant'] is False)
for r in v['canonical_refs']:verify(r)
b=doc(N/'binding.pre-review.json');s=doc(N/'scope_registration.json');ow=doc(R/'execution/v2.4/path_ownership.json');cp=doc(R/'execution/v2.4/checkpoint.json')
lease=ow['card_path_bindings']['W13-03']['subtasks']['desktop58_finite_validation']
ck('actualpipelineactiveleasepredicate',lease['state'] not in ('REGISTERED_PENDING_ONCE_EXECUTION','RUNNING') and lease['state']=='FAILED_EXECUTION_CLOSED_QUALIFICATION_WITHHELD')
ck('closedcurrentbeforetuple',[cp['revision'],ow['revision'],len(cp['failure_counters'])]==b['before']==v['after'])
ck('oldfailedrowpreserved',lease['run_uuid']=='72ff32d0d24a42c4a8effd849d54f882' and lease['current_source_writer'] is None)
git=[]
for r in mf['members']:
 if path(r['path']).name.endswith('.invocation.json') and path(r['path']).name.startswith('commit.'):
  x=doc(r['path']);z=x['result'];cl=z['job_cleanup']
  ck('oldCAS ownedGitclosed '+path(r['path']).name,z['actual_exit']==0 and z['timed_out'] is False and z['error'] is None and x['wrapper_error'] is None and cl['job_idle_confirmed'] and cl['handles_closed'] and not cl['errors'])
  verify(x['stdout_ref']);verify(x['stderr_ref']);git.append(r)
ck('oldCAS12boundedGitrecords',len(git)==12)
ob=doc(N/'tool-observations.sixth-construction.closed.original.json');ck('closedobservationSHA',pin(N/'tool-observations.sixth-construction.closed.original.json')['sha256']=='d023dfdbec882f5df13e8af2dbb533dbe3490fb78917a5a868f4b6dc5daba4ac')
facts=[]
for record in ob['records']:
 rows=[]
 def walk(x):
  if isinstance(x,dict):
   if 'chunk_id' in x and 'output' in x:
    rows.append({'chunk_id':x['chunk_id'],'session_id':x.get('session_id'),'exit_code':x.get('exit_code'),'markers':re.findall(r'ACTUAL_[A-Z_]*EXIT[=:]\\s*(-?\\d+)',x['output'])})
   for z in x.values():walk(z)
  elif isinstance(x,list):
   for z in x:walk(z)
 walk(record['result']);facts.append({'kind':record['kind'],'tools':rows})
def phase(k):return next(x for x in facts if x['kind']==k)
ck('original16toolrecords',len(ob['records'])==16)
ck('actualscopeclosed0',ob['actual_scope_builder_outer_exit']==ob['actual_scope_builder_python_exit']==0 and any(t['exit_code']==0 for t in phase('scope-poll3')['tools']))
ck('actualcaptureclosed0',ob['actual_capture_outer_exit']==ob['actual_capture_python_exit']==0 and any(t['exit_code']==0 for t in phase('capture-poll3')['tools']))
ck('precallfailurekeptseparate',bool(phase('scope-precall-failed')['tools']) and ob['original_precall_errors_preserved'] is not None)
ck('capturecasecountsnotqualification',ob['product_native_calls']==ob['canonical_writes']==ob['formal_increment']==0 and ob['qualification'] is False)
for k in ('output_root','outer_output_root','export_root','new_authorization_root','new_grant_preflight_root'):ck('still absent '+k,not path(s[k]).exists())
data={'schema':'researchos.desktop58-lease-and-tool-closure-supplement.v1','checks':C,'failed':[x for x in C if not x['passed']],'refs':refs,'actual_tool_facts':facts,'closed_lease':lease,'qualification':False,'new_failure_origins':[]}
with (O/'lease-tool-closure.json').open('xb') as f:f.write((json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps({'checks':len(C),'failed':data['failed'],'tool_facts':facts},ensure_ascii=False))

