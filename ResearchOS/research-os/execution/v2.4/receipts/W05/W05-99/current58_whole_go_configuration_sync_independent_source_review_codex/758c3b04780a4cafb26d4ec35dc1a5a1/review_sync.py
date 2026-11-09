import ast,hashlib,json,difflib
from pathlib import Path
O=Path(__file__).parent
D=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/current58_whole_go_suite_configuration_sync_source_preparation_codex/4a8dca58606d4a4db695aa6dc9f082cb')
checks=[];refs=[]
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def ck(k,v):checks.append({'check':k,'passed':bool(v)})
def read(p):refs.append(pin(p));return json.loads(p.read_bytes())
def vr(r):
 p=Path(r['path']);actual=pin(p);ck('ref '+p.name,actual['sha256']==r['sha256'] and actual['bytes']==r['bytes']);refs.append(actual);return p
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
h=read(D/'handoff.selected.json')
ck('handoff expectedSHA',pin(D/'handoff.selected.json')['sha256']=='532e769ecd7b968b6cc32a94453ba5ed7b8f1c123bede764dc86a1d85095cbf1')
m=read(vr(h['manifest_ref']))
key=next(k for k in ['members','entries','files'] if isinstance(m.get(k),list))
ck('13 sealed members',len(m[key])==13)
if 'member_count' in m:ck('declared member_count13',m['member_count']==13)
elif 'count' in m:ck('declared count13',m['count']==13)
for r in m[key]:vr(r)
inv=read(vr(h['source_inverse_ref']))
sel={k:vr(r) for k,r in h['selected_source_refs'].items()}
olds={}
for pair in inv['pairs']:
 p=vr(pair['old']);q=vr(pair['new']);old=p.read_bytes();new=q.read_bytes();olds[pair['role']]=p
 if pair['role'] in ['gate','runner']:
  ck(pair['role']+' exact oldbytes',new==old);ck(pair['role']+' AST unchanged',ast.dump(ast.parse(new))==ast.dump(ast.parse(old)))
 else:
  if pair['role']=='execution_contract':
   oldj=json.loads(old);newj=json.loads(new)
   v=newj['go_hash_attestation_schema'];newj['go_hash_attestation_schema']=oldj['go_hash_attestation_schema']
   ck('execution onlyschema leaf',newj==oldj)
   ck('execution requiredv2',v=='researchos.current58-frozen-go-hash-attestation.v2')
   ck('execution fullbyte inverse',new.replace(v.encode(),oldj['go_hash_attestation_schema'].encode(),1)==old)
  else:
   oldj=json.loads(old);newj=json.loads(new)
   newhash=newj['actual_cap_preflight']['gate_raw_sha256_before_compile'];newname=newj['final_candidate_source_files'][3]
   oldhash=oldj['actual_cap_preflight']['gate_raw_sha256_before_compile'];oldname=oldj['final_candidate_source_files'][3]
   newj['actual_cap_preflight']['gate_raw_sha256_before_compile']=oldhash;newj['final_candidate_source_files'][3]=oldname
   ck('interface onlytwo leaves',newj==oldj)
   ck('interface fullbyte inverse',new.replace(newhash.encode(),oldhash.encode(),1).replace(newname.encode(),oldname.encode(),1)==old)
  actualpatch=vr(pair['diff_ref']).read_text('utf-8')
  expect=''.join(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True),fromfile=str(p),tofile=str(q)))
  ck(pair['role']+' exactpatch',actualpatch==expect)
rt=ast.parse(sel['runner'].read_bytes())
assigns={x.targets[0].id:x.value for x in rt.body if isinstance(x,ast.Assign) and isinstance(x.targets[0],ast.Name)}
ck('bootstrap actualgate SHA',ast.literal_eval(assigns['GATE_SHA256'])==pin(sel['gate'])['sha256'])
ck('bootstrap actualgate bytes',ast.literal_eval(assigns['GATE_BYTES'])==pin(sel['gate'])['bytes'])
for k,role in [('GATE','gate'),('EXECUTION','execution_contract')]:
 ck(k+' siblingselected',ast.literal_eval(assigns[k].args[0])==sel[role].name)
ck('ROOT fixed seven parent depth',sel['runner'].resolve().parents[7]==Path('D:/作品集/ResearchOS/research-os').resolve())
inter=read(sel['authority_interface']);execution=read(sel['execution_contract']);template=read(vr(h['root_source_members_template_ref']))
ck('interface gate hash actual',inter['actual_cap_preflight']['gate_raw_sha256_before_compile']==pin(sel['gate'])['sha256'])
ck('interface self selectedname',inter['final_candidate_source_files'][3]==sel['authority_interface'].name)
ck('all4 selected names',set(inter['final_candidate_source_files'])=={p.name for p in sel.values()})
ck('source template schema',template['schema']=='researchos.current58-whole-go-source-preparation-manifest.v1')
ck('source template future registration null',template['root_registration_ref'] is None)
tm=template['members']
for x in tm:vr(x)
ck('source templateexact5',len(tm)==5)
for p in sel.values():ck('template selected '+p.name,pin(p) in tm)
finite=[x for x in tm if Path(x['path']).name=='whole58-finite.contract.proposed.json']
ck('old finite unchanged',len(finite)==1 and finite[0]['sha256']=='52828991f4f23d6957a3f7aa6343b50d8840efbe0ca42121871aa6bc8ce8c904')
ck('unallocated actualRootmanifest',inter['registered_source_manifest']['manifest_ref_before_actual_root_registration'] is None)
ck('cap producer still null',inter['actual_cap_preflight']['controller_code_and_non_author_cap_review_ref'] is None)
ck('no actualsourceaccept',template['source_acceptance'] is False and execution['qualification']['source_acceptance'] is False)
prior=read(vr(h['prior_non_author_review_ref']))
ck('prior expectedREQUEST',prior['decision']=='REQUEST_CHANGES')
decision='READY_SOURCE_PREPARATION_ONLY' if all(x['passed'] for x in checks) else 'REQUEST_CHANGES'
save('audit.json',{'schema':'researchos.source-configuration-sync-static-audit.v1','checks':checks,'count':len(checks),'passed':sum(x['passed'] for x in checks),'actual_read_refs':refs,'candidate_imported':False,'candidate_executed':False})
save('review.json',{'schema':'researchos.current58-whole-go-revision-independent-source-review.v1','actor_id':'codex:/root/w05_merge_review','reviewer':'codex:/root/w05_merge_review','non_author':True,'source_author':'codex:/root/f08_whole_scope_review','decision':decision,'requested_changes':[x for x in checks if not x['passed']],'stage':'SOURCE_PREPARATION_ONLY','status':'STOPPED','selected_source_refs':h['selected_source_refs'],'prior_review_ref':h['prior_non_author_review_ref'],'audit_ref':pin(O/'audit.json'),'disposition':{'GO58-R2-CONTRACT-ATTESTATION-VERSION':'CLOSED_STATIC: selected contract v2 matches gate v2.','GO58-R2-AUTHORITY-SELECTED-PINS':'CLOSED_STATIC: actual selected gate SHA and rev9 self filename synchronized.','previousR1R2R3_code':'Reused previous90 effective checks after exact gate/runner byte andAST comparison; no runtime evidence inherited.'},'dependency_order':['nativeGoHashResult -> Rootattestation -> independent attestationReview -> scope dualpins','sourceManifest(no registration backref) -> Rootregistration -> independent scope/sourceReview -> grant -> authorityBundle'],'new_tool_failure_origins':[],'new_failure_count':0,'candidate_imported_or_executed':False,'Go_calls':0,'source_acceptance':False,'whole58_test_suite_qualified':False,'formal_case_accepted_delta':0,'remaining_open':['Actual Root WindowsJob/process/HTTP/model-zero cap producer and non-author cap review do not yet exist.','New Root scope/exact budgets/lease/cwd/runtime/tree/native attestation/source manifest/CAS/grant and external authority remain required.','58 roster probes and136 planned local invocations/743 selected sourceIDs are NOT_RUN;2 modelIDs remainHOLD.','No source/parent/whole-suite/formal acceptance.']})
save('report.json',{'schema':'researchos.configuration-sync-independent-report.v1','review_ref':pin(O/'review.json'),'source_changes':'Only three JSON leaves changed. Gate and runner byteexact; template selects new4paths/hash values plus original finite contract.','path_reachability':'Runner ROOT parents[7] resolves current repository; sibling GATE/EXECUTION basenames exist in selectedNS, embedded hash/bytes match.','immutable_cycles':'No new hash cycle: source manifest root_registration_ref remainsNULL, attestation omits review backreference; scope pins attestation and review.','verification':'PureIO/hash/AST/whole-byte inverse only; no candidate import/execution.','new_failure_count':0})
save('handoff.json',{'schema':'researchos.source-independent-review-handoff.v1','actor_id':'codex:/root/w05_merge_review','decision':decision,'review_ref':pin(O/'review.json'),'report_ref':pin(O/'report.json'),'audit_ref':pin(O/'audit.json'),'new_failure_count':0,'new_tool_failure_origins':[],'actual_execution_authorized':False,'status':'STOPPED'})
rows=[pin(p) for p in sorted(O.iterdir()) if p.is_file()]
save('manifest.json',{'schema':'researchos.public-review-manifest.v1','entries':rows,'count':len(rows),'self_excluded':True})
print(json.dumps({'checks':len(checks),'passed':sum(x['passed'] for x in checks),**{n:pin(O/n) for n in ['review.json','report.json','handoff.json','manifest.json']}},ensure_ascii=False))

