from pathlib import Path
import ast,copy,hashlib,json,traceback
R=Path('D:/作品集/ResearchOS/research-os'); P=R/'execution/v2.4/receipts/W05/W05-99'; O=Path(__file__).parent
N=P/'integration_codex/cli43-fresh-held2-r329-246c20b781664b0e80fae7fd29b9b2b4'
checks=[]; refs={}
def path(x):
 p=Path(x); return p if p.is_absolute() else R/p
def ref(x):
 p=path(x); b=p.read_bytes(); a={'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}; refs[a['path']]=a; return a
def ck(n,v): checks.append({'check':n,'passed':bool(v)})
def verify(x):
 p=path(x['path']); a=ref(p); ck('pin '+a['path'],a['sha256']==x['sha256'] and a['bytes']==x['bytes']); return p
def read(x): ref(x); return json.loads(path(x).read_bytes())
def save(n,x):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f: json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False); f.write('\n')
try:
 ck('supplied draft MF',ref(N/'registration-draft.manifest.json')['sha256']=='1324e4a7d39dd9159d3786db8909e1385a64b9e0ae7f91db170294fc4864d631')
 ck('supplied binding',ref(N/'binding.json')['sha256']=='eadf1441e39953749d9cf36780eaf75ce8a2bec45815a0543328c90d9aa9c2b6')
 mf=read(N/'registration-draft.manifest.json')
 for x in mf['entries']: verify(x)
 ck('62 unique MF members',len(mf['entries'])==62 and len({path(x['path']) for x in mf['entries']})==62 and mf['self_excluded'] is True)
 b=read(N/'binding.json'); pb=read(N/'binding.pre-review.json'); p=read(N/'prepared_refs.json'); s=read(N/'scope_registration.json')
 ck('final binding only inserted actual controller review',b.keys()==pb.keys() and {k for k in b if b[k]!=pb[k]}=={'controller_review_ref'} and b['controller_review_ref']['sha256']=='efcef49a86c812b42cd4dee045184c62c8a66bebcb7e427cddb187149f579eb5')
 rv=read(verify(b['controller_review_ref'])); ck('actual scope review actor decision',rv['schema']=='researchos.cli43-compiler-controller-static-review.v1' and rv['reviewer']=='codex:/root/w05_merge_review' and rv['decision']=='READY_FOR_ROOT_CURRENT43_HELD2_ONCE' and rv['requested_changes']==[])
 ck('prepared exact binding tuples',p['binding']==b and p['expected_before']==b['before']==[328,156,469] and p['expected_after']==b['after']==[329,157,481] and p['actual_registration_executed'] is False)
 verify(p['scope_ref']); ck('Root relative scope spelling',p['scope_ref']['path']==(N/'scope_registration.json').relative_to(R).as_posix() and p['scope_ref']['sha256']==rv['scope_sha256'])
 original=[verify(x).read_bytes() for x in p['original_refs']]; desired=[verify(x).read_bytes() for x in p['desired_refs']]
 ck('four ordered canonical paths',[x['path'] for x in p['canonical_before']]==['execution/v2.4/'+n+'.json' for n in ['checkpoint','path_ownership','step_state','commands']])
 copied=[]
 for i,x in enumerate(p['canonical_before']):
  q=verify(x); ck('current equals original '+str(i),q.read_bytes()==original[i]); dest=O/(Path(x['path']).stem+'.before.raw')
  with dest.open('xb') as f: f.write(original[i])
  copied.append(ref(dest))
 oldcp,oldow=map(json.loads,original[:2]); cp,ow=map(json.loads,desired[:2]); cut=read(verify(b['origin_cut_ref']))
 ck('original actual tuple', [oldcp['revision'],oldow['revision'],len(oldcp['failure_counters'])]==b['before'])
 ck('desired actual tuple',[cp['revision'],ow['revision'],len(cp['failure_counters'])]==b['after'])
 ck('complete469 prefix plus exact12',p['origins']==cut['origins'] and len(p['origins'])==12 and cp['failure_counters']==oldcp['failure_counters']+p['origins'])
 for i,x in enumerate(p['origins']):
  ck('origin original payload '+str(i),read(verify(x['evidence_ref']))==x['original_payload'])
  if 'original_container_ref' in x:
   container=read(verify(x['original_container_ref'])); ck('mapped full original container and row '+str(i),container==x['original_container_payload'] and container['new_origins'][x['original_origin_index']]==x['original_origin_row']==x['original_payload'])
 module=next(x for x in b['metadata_code_refs'] if 'metadata_pipeline.v7.proposed.py' in x['path']); raw=verify(module).read_bytes(); tree=ast.parse(raw)
 wip=None
 for node in tree.body:
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='WIP_KEYS' for t in node.targets): wip=ast.literal_eval(node.value)
 ck('actual three WIP keys parsed',isinstance(wip,tuple) and len(wip)==3)
 restored=copy.deepcopy(cp); restoredow=copy.deepcopy(ow)
 for k in ['revision','expected_previous_revision','updated_at','updated_by','failure_counters']:
  if k in oldcp: restored[k]=oldcp[k]
  else: restored.pop(k,None)
 for k in wip:
  if k in oldcp['work_in_progress']: restored['work_in_progress'][k]=oldcp['work_in_progress'][k]
  else: restored['work_in_progress'].pop(k,None)
 for k in ['revision','amended_at','amended_by']:
  if k in oldow: restoredow[k]=oldow[k]
  else: restoredow.pop(k,None)
 ck('every other CP and OW field preserved',restored==oldcp and restoredow==oldow)
 ck('STCM bytes preserved',original[2:]==desired[2:])
 ck('WIP exact authority refs',[cp['work_in_progress'][k] for k in wip]==[p['scope_ref'],b['current43_authority_ref'],b['controller_review_ref']])
 ck('head remains a510',oldcp['head']==cp['head']==s['source_commit'])
 allowed={}
 for name in ['runtime_resources_ref','compiler_resources_ref']:
  for x in read(verify(s[name]))['files']: allowed[path(x['path'])]=(x['sha256'],x['bytes'])
 for x in read(verify(b['source_inputs_ref']))['files']: allowed[path(x['path'])]=(x['sha256'],x['bytes'])
 inherited=0; freshly=0
 for x in p['verified_refs']:
  q=path(x['path'])
  if q in allowed:
   ck('prepared inherited approved row '+str(q),allowed[q]==(x['sha256'],x['bytes'])); inherited+=1
  else: verify(x); freshly+=1
 ck('verified refs unique',len({path(x['path']) for x in p['verified_refs']})==len(p['verified_refs']))
 observation=read(N/'prepare.runtime.json'); rtmap={path(x['path']):(x['sha256'],x['bytes']) for x in read(verify(s['runtime_resources_ref']))['files']}
 for k in ['runner_ref','launcher_ref','authorization_gate_ref','owned_process_helper_ref','debug_tree_helper_ref']:
  x=s[k]; rtmap[path(x['path'])]=(x['sha256'],x['bytes'])
 ck('runtime strict marker and limitation',observation['all_observed_inputs_pre_pinned'] is True and observation['point_in_time_only'] is True and observation['Python_lifecycle_proof'] is False)
 for x in observation['files']: ck('actual pointtime allowed '+x['path'],rtmap.get(path(x['path']))==(x['sha256'],x['bytes']))
 for kind in ['head','status','index']:
  inv=read(N/('prepare.'+kind+'.invocation.json')); stdout=verify(inv['stdout_ref']).read_bytes(); verify(inv['stderr_ref']); rr=inv['result']; j=rr['job_cleanup']
  ck('owned Git complete '+kind,inv['actual_stage_native_exit']==0 and inv['wrapper_error'] is None and rr['actual_exit']==0 and rr['error'] is None and rr['timed_out'] is False and rr['resumed'] is True and all(j[x] is True for x in ['unnamed_exclusive_job','assigned_before_resume','job_idle_confirmed','primary_exit_confirmed','handles_closed']) and j['active_processes_last_observed']==0 and j['errors']==[])
  if kind=='head': ck('actual prepare HEAD',stdout.decode().strip()==s['source_commit'])
  if kind=='status': ck('actual prepare status13 old11D',hashlib.sha256(stdout).hexdigest()==b['main_git']['status_sha256'] and len(stdout)==894 and len([x for x in stdout.splitlines() if x])==13 and sum(x.startswith(b' D ') for x in stdout.splitlines())==11)
  if kind=='index': ck('actual prepare index empty',stdout==b'')
 for name in ['binding-final.invocation.json','metadata-prepare.invocation.json']:
  x=read(N/name); verify(x['stdout_ref']); verify(x['stderr_ref']); ck('metadata phase actual0 '+name,x['actual_native_exit']==0 and 'wrapper_error' in x and x['wrapper_error'] is None and x['product_cases_executed'] is False)
 roots=[s[x] for x in ['new_output_root','new_wrapper_root','new_export_root','new_authorization_root','new_grant_preflight_root']]
 ck('all five execution roots absent',all(not path(x).exists() for x in roots)); ck('register not started',not (N/'canonical-write.intent.json').exists() and not (N/'invocation.json').exists())
 ck('static forward only and four immediate guards',b"'all-four immediately before replace CAS'" in raw and b"'post-source-guard final four CAS'" in raw and b"FORWARD_ONLY_REQUIRES_SEPARATE_ROOT_DECISION; NEVER RESET/ROLLBACK" in raw and b"safe(copied['path']).parent==safe(r['path']).parent" in raw)
 head=(R/'.git/HEAD').read_text().strip(); hp=R/'.git'/head[5:] if head.startswith('ref: ') else None; ck('direct current HEAD',(hp.read_text().strip() if hp else head)==s['source_commit'])
 for x in list(refs.values()):
  rawnow=path(x['path']).read_bytes(); ck('after same '+x['path'],hashlib.sha256(rawnow).hexdigest()==x['sha256'] and len(rawnow)==x['bytes'])
 save('audit.json',{'checks':checks,'failed_checks':[x for x in checks if not x['passed']],'input_refs':list(refs.values()),'copied_canonical_before_refs':copied,'facts':{'prepared_verified_count':len(p['verified_refs']),'approved_catalog_rows_compared_without_backing_rehash':inherited,'other_prepared_refs_hashed':freshly,'runtime_observed_count':len(observation['files']),'manifest_members':len(mf['entries']),'scope_review_ref':b['controller_review_ref'],'before':b['before'],'after':b['after'],'new_failure_origins':[]},'actual_registration_executed':False,'target_executions':0})
 print(json.dumps({'checks':len(checks),'failed_checks':[x for x in checks if not x['passed']],'audit_ref':ref(O/'audit.json')},ensure_ascii=False))
except BaseException as e:
 save('audit.failure.json',{'error':repr(e),'traceback':traceback.format_exc(),'checks':checks,'input_refs':list(refs.values()),'target_executions':0}); raise
