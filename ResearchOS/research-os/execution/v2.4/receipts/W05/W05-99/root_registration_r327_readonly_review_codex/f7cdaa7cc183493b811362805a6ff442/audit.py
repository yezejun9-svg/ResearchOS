from pathlib import Path
import json,hashlib,ast,copy,traceback
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99';O=Path(__file__).parent;N=P/'integration_codex/cli43-fresh-held2-r327-efa7776ec48e4a7abaa92ce85eb0dace';OLD=P/'integration_codex/cli43-fresh-held2-r326-477e329b79944cb0b33f9ead24811760'
checks=[];refs={}
def path(x):
 p=Path(x);return p if p.is_absolute() else R/p
def ref(p):
 p=path(p);raw=p.read_bytes();v={'path':p.as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)};refs[v['path']]=v;return v
def ck(n,b):checks.append({'check':n,'passed':bool(b)})
def verify(x):
 p=path(x['path']);v=ref(p);ck('hash '+v['path'],v['sha256']==x['sha256'] and v['bytes']==x['bytes']);return p
def read(p):ref(p);return json.loads(path(p).read_text(encoding='utf-8'))
def write(n,x):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
try:
 ck('draft MF original pin',ref(N/'registration-draft.manifest.json')['sha256']=='554a9be7040d4e60cfd5fe95c0ec32cad5a3fa23f9afe58fcc565113bdd7e23c')
 ck('binding original pin',ref(N/'binding.json')['sha256']=='534bc4a188a503f94b1f7b1e993a25df1cc6193ae630fb0bd0042337226a7c7e')
 mf=read(N/'registration-draft.manifest.json')
 for x in mf['entries']:verify(x)
 p=read(N/'prepared_refs.json');b=read(N/'binding.json');ck('prepared exactbinding',p['binding']==b)
 pre=read(N/'binding.pre-review.json');bd={k for k in b if b[k]!=pre[k]};ck('finalbinding only actual controller review',b.keys()==pre.keys() and bd=={'controller_review_ref'} and pre['controller_review_ref'] is None)
 for v in [p['audit_ref'],p['scope_ref']]:verify(v)
 ck('draft manifest unique and self excluded',mf['self_excluded'] is True and len({path(x['path']) for x in mf['entries']})==len(mf['entries']))

 ck('tuple expected',p['expected_before']==b['before']==[326,154,450] and p['expected_after']==b['after']==[327,155,459] and p['actual_registration_executed'] is False)
 originals=[verify(x).read_bytes() for x in p['original_refs']];desired=[verify(x).read_bytes() for x in p['desired_refs']];copies=[]
 for i,(c,raw) in enumerate(zip(p['canonical_before'],originals)):
  ck('live four originals '+str(i),verify(c).read_bytes()==raw);q=O/('canonical-before-%02d.raw'%i)
  with q.open('xb') as f:f.write(raw)
  copies.append(ref(q))
 ck('ordered four',len(originals)==len(desired)==len(copies)==4 and [x['path'] for x in p['canonical_before']]==['execution/v2.4/checkpoint.json','execution/v2.4/path_ownership.json','execution/v2.4/step_state.json','execution/v2.4/commands.json'])
 cp,ow=map(json.loads,originals[:2]);dcp,dow=map(json.loads,desired[:2]);cut=read(N/'failure-origins.cut.json')
 ck('current and desired tuples',[cp['revision'],ow['revision'],len(cp['failure_counters'])]==b['before'] and [dcp['revision'],dow['revision'],len(dcp['failure_counters'])]==b['after'])
 ck('old450 plus exactly original9',dcp['failure_counters']==cp['failure_counters']+cut['origins'] and p['origins']==cut['origins'] and len(cut['origins'])==9)
 originhashes=[]
 for x in cut['origins']:
  verify(x['evidence_ref']);ck('payload '+x['evidence_ref']['sha256'],read(x['evidence_ref']['path'])==x['original_payload']);originhashes.append(x['evidence_ref']['sha256'])
 ck('unique new origins no duplicates',len(set(originhashes))==9 and all(h not in {x.get('evidence_ref',{}).get('sha256') for x in cp['failure_counters']} for h in originhashes))
 module=path(b['metadata_code_refs'][6]['path']);tree=ast.parse(module.read_bytes());wip=None
 for node in tree.body:
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='WIP_KEYS' for t in node.targets):wip=ast.literal_eval(node.value)
 ck('WIP keys present exactthree',isinstance(wip,list) and len(wip)==3)
 prot=copy.deepcopy(dcp);po=copy.deepcopy(dow)
 for k in ['revision','expected_previous_revision','updated_at','updated_by','failure_counters']:
  if k in cp:prot[k]=cp[k]
  else:prot.pop(k,None)
 for k in wip:
  if k in cp['work_in_progress']:prot['work_in_progress'][k]=cp['work_in_progress'][k]
  else:prot['work_in_progress'].pop(k,None)
 for k in ['revision','amended_at','amended_by']:
  if k in ow:po[k]=ow[k]
  else:po.pop(k,None)
 ck('all protected CP fields exact',prot==cp);ck('all protected OW fields exact',po==ow);ck('STCM originalbytes',originals[2:]==desired[2:])
 ck('only exact scope authority review WIP values',[dcp['work_in_progress'][k] for k in wip]==[p['scope_ref'],b['current43_authority_ref'],b['controller_review_ref']])
 ck('scope Rootrelative exact',p['scope_ref']=={'path':(N/'scope_registration.json').relative_to(R).as_posix(),'sha256':ref(N/'scope_registration.json')['sha256'],'bytes':ref(N/'scope_registration.json')['bytes']})
 for x in b['metadata_code_refs']:verify(x)
 for name in ['register.py','run.py','seal.py','prepare.py','grant_preflight.py']:
  ck('unchanged previously reviewed wrapper '+name,(N/name).read_bytes()==(OLD/name).read_bytes());ast.parse((N/name).read_bytes())
 review=read(verify(b['controller_review_ref']));ck('real independent bound review',review['reviewer']=='codex:/root/w05_merge_review' and review['decision']=='READY_FOR_ROOT_CURRENT43_HELD2_ONCE' and review['requested_changes']==[] and review['scope_sha256']==p['scope_ref']['sha256'])
 for name in ['binding-final.invocation.json','metadata-prepare.invocation.json']:
  x=read(N/name);verify(x['stdout_ref']);verify(x['stderr_ref']);ck('metadata actual0 '+name,x['actual_native_exit']==0 and 'wrapper_error' in x and x['wrapper_error'] is None and x['product_cases_executed'] is False)
 jobs=[]
 for kind in ['head','status','index']:
  x=read(N/('prepare.'+kind+'.invocation.json'));v=x['result'];j=v['job_cleanup'];out=verify(x['stdout_ref']).read_bytes();verify(x['stderr_ref']);ck('ownedGit0 complete '+kind,v['actual_exit']==x['actual_stage_native_exit']==0 and v['error'] is None and v['timed_out'] is False and v['resumed'] is True and all(j[k] is True for k in ['assigned_before_resume','job_idle_confirmed','primary_exit_confirmed','handles_closed']) and j['errors']==[])
  if kind=='head':ck('actual head',out.decode('utf-8').strip()==b['main_git']['head']==cp['head'])
  if kind=='status':ck('actual13rows11D status',hashlib.sha256(out).hexdigest()==b['main_git']['status_sha256'] and len(out)==b['main_git']['status_bytes'] and len(out.splitlines())==13 and sum(line[:2].strip()==b'D' for line in out.splitlines())==11)
  if kind=='index':ck('actual empty index',out==b'')
  jobs.append(ref(N/('prepare.'+kind+'.invocation.json')))
 # Compare prepared catalogue entries to sealed public catalogues, without rehashing their backing trees.
 catalogrows=[]
 for key in ['runtime_resources_ref','compiler_resources_ref','source_inputs_ref']:
  x=read(verify(b[key]));catalogrows+=x['files']
 catalog={str(path(x['path'])).casefold():(x['sha256'],x['bytes']) for x in catalogrows};reused=0;direct=0
 for x in p['verified_refs']:
  k=str(path(x['path'])).casefold()
  if k in catalog:ck('declared catalog row '+x['path'],catalog[k]==(x['sha256'],x['bytes']));reused+=1
  else:verify(x);direct+=1
 rt=read(N/'prepare.runtime.json');allowed={str(path(x['path'])).casefold():(x['sha256'],x['bytes']) for x in read(path(b['runtime_resources_ref']['path']))['files']}
 for x in b['metadata_code_refs']:allowed[str(path(x['path'])).casefold()]=(x['sha256'],x['bytes'])
 for x in rt['files']:verify(x);ck('observed runtime pin '+x['path'],allowed.get(str(path(x['path'])).casefold())==(x['sha256'],x['bytes']))
 ck('runtime marker and accurate limits',rt['all_observed_inputs_pre_pinned'] is True and rt['point_in_time_only'] is True and rt['Python_lifecycle_proof'] is False)
 roots=[b[k] for k in ['new_output_root','new_wrapper_root','new_export_root','new_authorization_root','new_grant_preflight_root']]
 ck('five leaves still absent',len(set(roots))==5 and all(not path(x).exists() for x in roots))
 ck('new original450 prospective prefix',dcp['failure_counters'][:450]==cp['failure_counters'] and len(dcp['failure_counters'])==459)
 ck('single r326 original native cause',originhashes.count('c28ce01137b787d3f1a331d2a738ada8310fa83ac7adeb9ef2c36d42b9ec74d5')==1)
 ck('registration audit actualfalse formal0',read(N/'audit.json')['actual_registration_executed'] is False and read(N/'audit.json')['formal_increment']==0)
 ck('main head protected',cp['head']==dcp['head']=='a510dbef4a7e08fb5c428df44c39b133f3ffa856')
 modraw=module.read_bytes();ck('unchanged v7 wholemodule',hashlib.sha256(modraw).hexdigest()=='095d4f4b86ad0432bd559d2df7221d7f26794eb484f07d313fcc67d3a54f3eed')
 ck('register all-four immediate after long guard',b"unchanged_reads(); git_guard(b,output,'pre-replace-'+str(i))\n        need(all((ROOT/x).read_bytes()==r for x,r in zip(CANON,expected)),'all-four immediately before replace CAS')\n        os.replace(temp,target)" in modraw.replace(b'\r\n',b'\n'))
 for i,r in enumerate(p['canonical_before']):ck('final current four unchanged '+str(i),verify(r).read_bytes()==originals[i])

 ck('not registered yet',not (N/'canonical-write.intent.json').exists() and not (N/'invocation.json').exists())
 write('audit.json',{'checks':checks,'failed_checks':[x for x in checks if not x['passed']],'input_refs':list(refs.values()),'facts':{'canonical_before':p['canonical_before'],'copied_canonical_before_refs':copies,'expected_before':b['before'],'expected_after':b['after'],'draft_manifest_members':len(mf['entries']),'prepared_refs_count':len(p['verified_refs']),'catalog_rows_compared_not_rehashed':reused,'other_prepared_refs_actual_hash_checked':direct,'runtime_observed_files_current_hashed':len(rt['files']),'actual_prepare_Git_ref':jobs,'reused_bound_scope_review_ref':b['controller_review_ref'],'WIP_KEYS':wip,'cut9_refs':[x['evidence_ref'] for x in cut['origins']]},'actual_registration_executed':False,'target_executions':0,'new_failure_origins':[]})
 print(json.dumps({'checks':len(checks),'failed':[x for x in checks if not x['passed']],'audit_ref':ref(O/'audit.json')},ensure_ascii=False))
except Exception as e:
 write('audit.failure.json',{'error':repr(e),'traceback':traceback.format_exc(),'completed_checks':checks,'input_refs':list(refs.values()),'target_executions':0});raise
