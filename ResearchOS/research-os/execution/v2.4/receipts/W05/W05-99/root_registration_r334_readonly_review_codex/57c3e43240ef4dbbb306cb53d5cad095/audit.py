import ast,copy,hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent;P=R/'execution/v2.4/receipts/W05/W05-99';N=P/'integration_codex/cli58-fresh-held2-r334-v2-0e298790cd484ec9ba319a379e7e34ed'
C=[];INPUTS={}
def ck(k,v):C.append({'check':k,'passed':bool(v)})
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def ref(p):
 p=path(p);raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def pin(r):
 p=path(r['path']);raw=p.read_bytes();a=ref(p);INPUTS[str(p)]=a;ck('pin '+str(p),a['sha256']==r['sha256'] and a['bytes']==r['bytes']);return raw
def load(p):
 p=path(p);INPUTS[str(p)]=ref(p);return json.loads(p.read_bytes())
def rd(r):return json.loads(pin(r))
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def allrefs(v):
 if isinstance(v,dict):
  if {'path','sha256','bytes'}<=v.keys():yield v
  else:
   for x in v.values():yield from allrefs(x)
 elif isinstance(v,list):
  for x in v:yield from allrefs(x)
expected={'binding.json':'f325744ede3bb1a7460d1d9989c3a0eee93c5590c623822d50e22d36636e641f','prepared_refs.json':'44b0116139c2208391779511c04c9a45fc1e7b5166dd6caa8a4ad3116ef58ba7','audit.json':'7bc8904e2d63f71b929c08eeb023d210a409d9aace38ecf0607b1b9ef8e1dedf','prepare.tool-observations.closed.json':'be5106175d66dfba3926d27da17ad7a8de9de980a2adb17b28a7b21c780cd1e7'}
for n,h in expected.items():ck('expected '+n,ref(N/n)['sha256']==h)
p=load(N/'prepared_refs.json');b=load(N/'binding.json');s=rd(p['scope_ref']);beforebind=load(N/'binding.pre-review.json');q=rd(b['controller_review_ref']);draftaudit=rd(p['audit_ref'])
ck('binding inserted only actual review',set(k for k in b if b[k]!=beforebind[k])=={'controller_review_ref'} and beforebind['controller_review_ref'] is None and p['binding']==b)
ck('actual scope review',q['schema']=='researchos.cli43-compiler-controller-static-review.v1' and q['reviewer']=='codex:/root/w05_merge_review' and q['decision']=='READY_FOR_ROOT_CURRENT43_HELD2_ONCE' and q['requested_changes']==[])
for k,r in [('scope_sha256',p['scope_ref']),('runner_sha256',s['runner_ref']),('launcher_sha256',s['launcher_ref']),('gate_sha256',s['authorization_gate_ref'])]:ck('review pin '+k,q[k]==r['sha256'])
ck('Root relative scope exact serialization',p['scope_ref']=={'path':(N/'scope_registration.json').relative_to(R).as_posix(),'sha256':q['scope_sha256'],'bytes':8853})
ck('tuple',p['expected_before']==b['before']==[333,161,524] and p['expected_after']==b['after']==[334,162,532] and p['actual_registration_executed'] is False)
canon=['execution/v2.4/'+n+'.json' for n in ['checkpoint','path_ownership','step_state','commands']]
ck('ordered4',len(p['original_refs'])==len(p['desired_refs'])==4 and [r['path'] for r in p['canonical_before']]==canon)
oldraw=[pin(r) for r in p['original_refs']];newraw=[pin(r) for r in p['desired_refs']];copies=[]
for i,(c,r,raw) in enumerate(zip(canon,p['canonical_before'],oldraw)):
 ck('live before '+c,pin(r)==raw and path(c).read_bytes()==raw)
 name=f'canonical-before-{i}-{Path(c).name}'
 with (O/name).open('xb') as f:f.write(raw)
 copies.append(ref(O/name));ck('own immutable copy '+c,(O/name).read_bytes()==raw)
oldcp,oldow=map(json.loads,oldraw[:2]);cp,ow=map(json.loads,newraw[:2]);cut=rd(b['origin_cut_ref']);prefix=rd(b['failure_prefix430_ref'])
ck('prefix430',len(prefix['failure_counters'])==430 and oldcp['failure_counters'][:430]==prefix['failure_counters'])
ck('entire524 and exactly8 preserved',len(oldcp['failure_counters'])==524 and cp['failure_counters']==oldcp['failure_counters']+cut['origins'] and p['origins']==cut['origins'] and len(cut['origins'])==8)
seen={r.get('evidence_ref',{}).get('sha256') for r in oldcp['failure_counters']}
for row in cut['origins']:
 r=row['evidence_ref'];ck('unique original payload '+r['sha256'],r['sha256'] not in seen and rd(r)==row['original_payload'] and row['counter_reset'] is False);seen.add(r['sha256'])
keys=('cli43_fresh_compiler_held2_scope_ref','cli43_fresh_compiler_current_source_authority_ref','cli43_fresh_compiler_controller_review_ref')
restored=copy.deepcopy(cp);restoredow=copy.deepcopy(ow)
for k in ['revision','expected_previous_revision','updated_at','updated_by','failure_counters']:
 if k in oldcp:restored[k]=oldcp[k]
 else:restored.pop(k,None)
for k in keys:
 if k in oldcp['work_in_progress']:restored['work_in_progress'][k]=oldcp['work_in_progress'][k]
 else:restored['work_in_progress'].pop(k,None)
for k in ['revision','amended_at','amended_by']:
 if k in oldow:restoredow[k]=oldow[k]
 else:restoredow.pop(k,None)
ck('all other canonical fields preserved',restored==oldcp and restoredow==oldow)
ck('ST CM byte identical',newraw[2:]==oldraw[2:])
ck('desired tuple and source',[cp['revision'],ow['revision'],len(cp['failure_counters'])]==[334,162,532] and cp['head']==oldcp['head']==s['source_commit'])
ck('exact three WIP values',[cp['work_in_progress'][k] for k in keys]==[p['scope_ref'],b['current43_authority_ref'],b['controller_review_ref']])
ck('timestamps actor consistent',cp['updated_at']==ow['amended_at'] and cp['updated_by']==ow['amended_by']=='codex:/root' and cp['expected_previous_revision']==333)
ck('draft no acceptance',draftaudit['actual_registration_executed'] is False and draftaudit['formal_increment']==0 and draftaudit['source_acceptance'] is False)
norm=lambda p:str(path(p)).casefold()
approved={}
for k in ['runtime_resources_ref','compiler_resources_ref','source_inputs_ref']:
 d=rd(b[k])
 for r in d['files']:
  key=norm(r['path']);v=(r['sha256'],r['bytes']);ck('resource overlapping pins '+key,key not in approved or approved[key]==v);approved[key]=v
inventory_rows=0;extra_rows=[]
for r in p['verified_refs']:
 key=norm(r['path']);v=(r['sha256'],r['bytes'])
 if key in approved:ck('verified frozen inventory '+key,approved[key]==v);inventory_rows+=1
 else:pin(r);extra_rows.append(r)
ck('24056 prepared verified refs',len(p['verified_refs'])==24056)
for r in b['metadata_code_refs']:ast.parse(pin(r))
module=path(b['metadata_code_refs'][-1]['path']);modulebytes=module.read_bytes()
ck('reviewed pipeline exact',hashlib.sha256(modulebytes).hexdigest()=='4a5913346f0fa83f65824861077a05087de9244530be2754f138063821f7aeb4')
text=modulebytes.decode();ck('perreplace immediate four guard',"unchanged_reads(); git_guard(b,output,'pre-replace-'+str(i))\n        need(all((ROOT/x).read_bytes()==r for x,r in zip(CANON,expected)),'all-four immediately before replace CAS')\n        os.replace(temp,target)" in text)
ck('post long guard four recheck',"git_guard(b,output,'register-after')\n    need(all((ROOT/x).read_bytes()==r for x,r in zip(CANON,desired))" in text)
ck('forward intent no retry',"'automatic_retry':False,'recovery':'FORWARD_ONLY_REQUIRES_SEPARATE_ROOT_DECISION; NEVER RESET/ROLLBACK'" in text)
runtime=load(N/'prepare.runtime.json');ck('runtime successful pointtime only',runtime['all_observed_inputs_pre_pinned'] is True and runtime['point_in_time_only'] is True and runtime['Python_lifecycle_proof'] is False)
rt=rd(b['runtime_resources_ref']);allowed={norm(x['path']):(x['sha256'],x['bytes']) for x in rt['files']}
for k in ['runner_ref','launcher_ref','authorization_gate_ref','owned_process_helper_ref','debug_tree_helper_ref']:
 r=s[k];allowed[norm(r['path'])]=(r['sha256'],r['bytes'])
for r in runtime['files']:ck('observed runtime pin '+r['path'],allowed.get(norm(r['path']))==(r['sha256'],r['bytes']))
jobs=[]
for kind,argv_tail in [('head',['rev-parse','HEAD']),('status',['status','--porcelain=v1','-uno']),('index',['diff','--cached','--name-only'])]:
 inv=load(N/f'prepare.{kind}.invocation.json');z=inv['result'];jc=z['job_cleanup'];stdout=pin(inv['stdout_ref']);stderr=pin(inv['stderr_ref'])
 ck('Git '+kind+' closure',inv['kind']==kind and inv['actual_stage_native_exit']==z['actual_exit']==0 and inv['wrapper_error'] is None and z['error'] is None and z['timed_out'] is False and z['resumed'] is True and all(jc[x] is True for x in ['assigned_before_resume','job_idle_confirmed','primary_exit_confirmed','handles_closed']) and jc['errors']==[] and jc['active_processes_last_observed']==0)
 ck('Git '+kind+' cwd read-only',path(inv['cwd'])==R and inv['environment']['GIT_OPTIONAL_LOCKS']=='0' and stderr==b'')
 if kind=='head':ck('actual Git source HEAD',stdout.decode().strip()==s['source_commit'])
 if kind=='status':ck('actual Git old status13/11D',hashlib.sha256(stdout).hexdigest()==s['main_git']['status_sha256'] and len(stdout)==894 and len(stdout.splitlines())==13 and sum(x[:2]==b' D' for x in stdout.splitlines())==11)
 if kind=='index':ck('actual Git no staged delta',stdout==b'')
 jobs.append({'invocation_ref':ref(N/f'prepare.{kind}.invocation.json'),'argv':inv['argv'],'actual_exit':z['actual_exit'],'job_cleanup':jc})
for k in ['new_output_root','new_wrapper_root','new_export_root','new_authorization_root','new_grant_preflight_root']:ck('fresh absent '+k,not path(s[k]).exists())
for n in ['invocation.json','canonical-write.intent.json','registration-audit.json']:ck('not registered '+n,not (N/n).exists())
head=(R/'.git/HEAD').read_text().strip();head=(R/'.git'/head[5:]).read_text().strip() if head.startswith('ref: ') else head;ck('direct HEAD current',head==s['source_commit'])
obs=load(N/'prepare.tool-observations.closed.json');ck('prepare actual0 no CAS',obs['actual_outer_tool_exit']==obs['actual_python_exit']==0 and obs['canonical_registration_executed'] is False and obs['registered_before']==524 and obs['fixed_after']==532 and obs['known_observed']==537)
result={'checks':C,'failed':[x for x in C if not x['passed']],'input_refs':list(INPUTS.values()),'canonical_before':p['canonical_before'],'copied_canonical_before_refs':copies,'jobs':jobs,'scope_review_ref':b['controller_review_ref'],'resource_reuse':{'verified_refs':len(p['verified_refs']),'matched_inventory_rows':inventory_rows,'extra_control_refs_rehashed':len(extra_rows),'extra_control_refs':extra_rows,'all_inventory_rows_rehashed':False,'method':'Compare actual prepared pin rows to frozen descriptor rows; hash changed metadata, controls, evidence and canonical bytes only.'},'new_failure_origins':[],'candidate_calls':0,'canonical_writes':0,'native_Git_calls':0}
save('audit.json',result)
print(json.dumps({'checks':len(C),'failed':result['failed'],'inventory_rows':inventory_rows,'extra_rows':len(extra_rows),'audit_ref':ref(O/'audit.json')},ensure_ascii=False))
