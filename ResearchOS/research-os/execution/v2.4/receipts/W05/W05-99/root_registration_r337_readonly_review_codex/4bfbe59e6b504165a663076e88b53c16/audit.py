import ast,copy,hashlib,json,traceback
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent;N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r337-b4d53db07f1e4ab8b9c0b37e291a6da5'
C=[];INPUTS={}
def ck(k,v,d=None):C.append({'check':k,'passed':bool(v),'detail':d})
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def read(p):
 p=path(p);raw=p.read_bytes();INPUTS[str(p)]={'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)};return raw
def ref(p):read(p);return INPUTS[str(path(p))]
def pin(r):
 raw=read(r['path']);ck('pin '+r['path'],len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256']);return raw
def doc(p):return json.loads(read(p))
def rd(r):return json.loads(pin(r))
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def constants(raw):
 d={}
 for x in ast.parse(raw).body:
  if isinstance(x,ast.Assign):
   for t in x.targets:
    if isinstance(t,ast.Name):
     try:d[t.id]=ast.literal_eval(x.value)
     except (TypeError,ValueError):pass
 return d
def main():
 expected={'prepared_refs.json':('79e1495bcbe3ac44baf03142bec2d260b117bec33bd0e7ce29c47d98423109b7',5111307),'audit.json':('8fe10d258e33569fbcb081284d5a2da3148a2e0b587d47ec58c12de5253adab6',410),'binding.json':('edf1a088cb36f178333132d5cbad395a7b052329969a649f5da26aa14edffdd6',22067)}
 for name,(sha,n) in expected.items():z=ref(N/name);ck('actual expected '+name,z['sha256']==sha and z['bytes']==n)
 p=doc(N/'prepared_refs.json');b=doc(N/'binding.json');s=rd(p['scope_ref']);pre=doc(N/'binding.pre-review.json');review=rd(b['controller_review_ref']);da=rd(p['audit_ref'])
 ck('only finalreview inserted',set(b)==set(pre) and {k for k in b if b[k]!=pre[k]}=={'controller_review_ref'} and pre['controller_review_ref'] is None and p['binding']==b)
 ck('actual scope reviewer verdict',review['schema']=='researchos.desktop58-controller-static-review.v1' and review['reviewer']=='codex:/root/w05_merge_review' and review['decision']=='READY_FOR_ROOT_CURRENT58_DESKTOP169_GO3_ONCE' and review['requested_changes']==[])
 for k,r in [('scope_sha256',p['scope_ref']),('controller_sha256',s['controller_ref']),('launcher_sha256',s['launcher_ref']),('gate_sha256',s['authorization_verifier_ref'])]:ck('scope review complete pin '+k,review[k]==r['sha256'])
 ck('scope exact ROOTrelative3key',p['scope_ref']=={'path':(N/'scope_registration.json').relative_to(R).as_posix(),'sha256':'0caa54d359072e7200b7cbbc9fb72742ffb325adc82ad3b4622310ac7549e9c1','bytes':25595})
 ck('tuple exact',p['expected_before']==b['before']==[336,164,614] and p['expected_after']==b['after']==[337,165,617] and p['actual_registration_executed'] is False)
 canon=['execution/v2.4/'+n+'.json' for n in ['checkpoint','path_ownership','step_state','commands']]
 ck('four canonical order',len(p['original_refs'])==len(p['desired_refs'])==4 and [r['path'] for r in p['canonical_before']]==canon)
 oldraw=[pin(r) for r in p['original_refs']];newraw=[pin(r) for r in p['desired_refs']];copies=[]
 for i,(name,r,raw) in enumerate(zip(canon,p['canonical_before'],oldraw)):
  ck('actual live canonical before '+name,pin(r)==raw and read(name)==raw)
  f=O/('canonical-before-'+str(i)+'-'+Path(name).name)
  with f.open('xb') as stream:stream.write(raw)
  copies.append(ref(f));ck('byteexact ownparent copy '+name,f.read_bytes()==raw and f.parent==O)
 oldcp,oldow=map(json.loads,oldraw[:2]);cp,ow=map(json.loads,newraw[:2]);cut=rd(b['origin_cut_ref']);prefix=rd(b['failure_prefix430_ref'])
 ck('all614 original prefix+3exact',len(oldcp['failure_counters'])==614 and len(cut['origins'])==3 and cp['failure_counters']==oldcp['failure_counters']+cut['origins'] and p['origins']==cut['origins'])
 ck('old430 intact',len(prefix['failure_counters'])==430 and oldcp['failure_counters'][:430]==prefix['failure_counters'])
 seen={r.get('evidence_ref',{}).get('sha256') for r in oldcp['failure_counters']}
 for row in cut['origins']:
  r=row['evidence_ref'];ck('unique opaque original payload '+r['sha256'],r['sha256'] not in seen and rd(r)==row['original_payload'] and row['counter_reset'] is False);seen.add(r['sha256'])
 module_rows=[r for r in b['metadata_code_refs'] if r['sha256']=='c0a085f9b720ebdb89a78fb5cf367bd262d2823fe15a9f2686545b99aebe7755'];ck('one exact reviewed pipeline',len(module_rows)==1)
 module=pin(module_rows[0]);con=constants(module);keys=con['WIP_KEYS'];text=module.decode()
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
 lease={'owner':'codex:/root','current_source_writer':None,'state':'REGISTERED_PENDING_ONCE_EXECUTION','scope_ref':p['scope_ref'],'run_uuid':b['run_uuid'],'source_commit':s['source_commit']}
 expectedcard=copy.deepcopy(oldow['card_path_bindings']['W13-03']);expectedcard['subtasks']['desktop58_finite_validation']=lease
 ck('only finite Desktop sublease',ow['card_path_bindings']['W13-03']==expectedcard)
 prior=oldow['card_path_bindings']['W13-03']['subtasks']['desktop58_finite_validation']
 ck('actual old lease closed before replacement',prior['state']=='FAILED_EXECUTION_CLOSED_QUALIFICATION_WITHHELD' and prior['run_uuid']=='72ff32d0d24a42c4a8effd849d54f882' and prior['state'] not in ('REGISTERED_PENDING_ONCE_EXECUTION','RUNNING'))
 restoredow['card_path_bindings']['W13-03']=oldow['card_path_bindings']['W13-03']
 ck('every other CP OW field unchanged',restored==oldcp and restoredow==oldow)
 ck('ST CM actual unchangedbytes',newraw[2:]==oldraw[2:])
 ck('five WIP exact values',[cp['work_in_progress'][k] for k in keys]==[p['scope_ref'],b['current43_authority_ref'],b['controller_review_ref'],b['desktop_scope_values']['current58_CLI2_qualification_ref'],'REGISTERED_PENDING_ONCE_EXECUTION'])
 ck('desired tuple/source/timestamp',[cp['revision'],ow['revision'],len(cp['failure_counters'])]==[337,165,617] and cp['head']==oldcp['head']==s['source_commit'] and cp['expected_previous_revision']==336 and cp['updated_at']==ow['amended_at'] and cp['updated_by']==ow['amended_by']=='codex:/root')
 ck('draft acceptance false',da['actual_registration_executed'] is False and da['formal_increment']==0 and da['source_acceptance'] is False)
 # Reuse actual fullscope resource hashes; new metadata/evidence bytes are read now.
 baseline=rd(review['audit_refs'][0]);approved={str(path(x['path'])).casefold():(x['sha256'],x['bytes']) for x in baseline['input_refs']};reuse=0;extra=[]
 for r in p['verified_refs']:
  key=str(path(r['path'])).casefold();v=(r['sha256'],r['bytes'])
  if approved.get(key)==v:reuse+=1;ck('prepared exact previouslyhashed pin '+key,True)
  else:pin(r);extra.append(r)
 ck('24394verified',len(p['verified_refs'])==24394)
 for r in b['metadata_code_refs']:ast.parse(pin(r))
 ck('registerwrapper reviewed SHA',ref(N/'register.py')['sha256']=='17070cff42cb12c8d4db1e38e7c465cda47024aaceb10ea571d488c525497550' and ref(N/'run.py')['sha256']=='d4e7bc3dfe8a77f1bfd7d71ef57273d64c574ab8a08a1bf52509d0f8e7f1209c')
 ck('all4 immediate CAS after long source guard',"unchanged_reads(); git_guard(b,output,'pre-replace-'+str(i))\n        need(all((ROOT/x).read_bytes()==r for x,r in zip(CANON,expected)),'all-four immediately before replace CAS')\n        os.replace(temp,target)" in text)
 ck('postguard final CAS',"git_guard(b,output,'register-after')\n    need(all((ROOT/x).read_bytes()==r for x,r in zip(CANON,desired))" in text)
 ck('owned wrapper600 once no retry',"helper.run_owned(argv,str(ROOT),dict(b['public_environment']),stdout,stderr,600)" in text and "'automatic_retry':False,'recovery':'FORWARD_ONLY_REQUIRES_SEPARATE_ROOT_DECISION; NEVER RESET/ROLLBACK'" in text)
 ck('review4copies sameParent demanded',"safe(copied['path']).parent==safe(r['path']).parent and verify(copied)==verify(original)" in text)
 runtime=doc(N/'prepare.runtime.json');rt=rd(b['runtime_resources_ref']);allowed={str(path(x['path'])).casefold():(x['sha256'],x['bytes']) for x in rt['files']}
 ck('runtime marker only pointtime',runtime['all_observed_inputs_pre_pinned'] is True and runtime['point_in_time_only'] is True and runtime['Python_lifecycle_proof'] is False)
 for r in runtime['files']:ck('actual observed runtimepin '+r['path'],allowed.get(str(path(r['path'])).casefold())==(r['sha256'],r['bytes']))
 jobs=[]
 for kind,args in [('head',['rev-parse','HEAD']),('status',['status','--porcelain=v1','--untracked-files=no']),('index',['diff','--cached','--name-only'])]:
  inv=doc(N/f'prepare.{kind}.invocation.json');z=inv['result'];jc=z['job_cleanup'];stdout=pin(inv['stdout_ref']);stderr=pin(inv['stderr_ref'])
  ck('actual ownedGit '+kind,inv['kind']==kind and inv['actual_stage_native_exit']==z['actual_exit']==0 and inv['wrapper_error'] is None and z['error'] is None and z['timed_out'] is False and z['resumed'] is True and type(z['owned_child_pid']) is int and z['owned_child_pid']>0 and type(z['creation_time_100ns']) is int and z['creation_time_100ns']>0 and all(jc[x] is True for x in ['unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','job_idle_confirmed','primary_exit_confirmed','handles_closed']) and jc['errors']==[] and jc['active_processes_last_observed']==0)
  ck('read-only Git argv/env '+kind,inv['argv'][1:]==args and path(inv['cwd'])==R and inv['environment']['GIT_OPTIONAL_LOCKS']=='0' and stderr==b'')
  if kind=='head':ck('actual Head E2',stdout.decode().strip()==s['source_commit'])
  if kind=='status':ck('actual status13/11D',hashlib.sha256(stdout).hexdigest()==s['main_git']['status_sha256'] and len(stdout)==894 and len(stdout.splitlines())==13 and sum(x[:2]==b' D' for x in stdout.splitlines())==11)
  if kind=='index':ck('actual indexempty',stdout==b'')
  jobs.append({'invocation_ref':ref(N/f'prepare.{kind}.invocation.json'),'stdout_ref':inv['stdout_ref'],'stderr_ref':inv['stderr_ref'],'result':z,'argv':inv['argv']})
 for k in ['output_root','outer_output_root','export_root','new_authorization_root','new_grant_preflight_root']:ck('fresh absent '+k,not path(s[k]).exists())
 for n in ['invocation.json','canonical-write.intent.json','registration-audit.json']:ck('registration not executed '+n,not (N/n).exists())
 for name,raw in zip(canon,oldraw):ck('final live4 '+name,read(name)==raw)
 save('audit.json',{'schema':'researchos.root-registration-draft-independent-audit.v1','checks':C,'failed':[x for x in C if not x['passed']],'input_refs':list(INPUTS.values()),'canonical_before':p['canonical_before'],'copied_canonical_before_refs':copies,'jobs':jobs,'scope_review_ref':b['controller_review_ref'],'resource_reuse':{'verified_refs':len(p['verified_refs']),'exact_reused_fullscope_actualhash_refs':reuse,'extra_metadata_refs_rehashed':extra,'full_resource_tree_rehashed_this_registration_review':False,'baseline_audit_ref':review['audit_refs'][0]},'candidate_calls':0,'native_Git_calls':0,'canonical_writes':0,'new_failure_origins':[]})
 print(json.dumps({'checks':len(C),'failed':[x for x in C if not x['passed']],'reused_verified':reuse,'new_metadata_hashed':len(extra),'audit_ref':ref(O/'audit.json')},ensure_ascii=False))
if __name__=='__main__':
 try:main()
 except BaseException as exc:save('audit.failure.json',{'error':repr(exc),'traceback':traceback.format_exc(),'checks':C,'input_refs':list(INPUTS.values())});raise

