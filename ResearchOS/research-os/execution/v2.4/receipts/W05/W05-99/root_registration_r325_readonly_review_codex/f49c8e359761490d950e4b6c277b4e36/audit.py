import ast,copy,hashlib,json,os
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99';O=Path(__file__).parent
N=P/'integration_codex/cli43-fresh-held2-r325-71b091d20d94443bbf4e732d201eeb29'
CANON=['execution/v2.4/'+x+'.json' for x in ['checkpoint','path_ownership','step_state','commands']]
reads={};checks=[]
def ck(ok,n):checks.append({'check':n,'pass':bool(ok)})
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def read(p):
 p=path(p);z=p.read_bytes()
 if str(p) in reads:ck(reads[str(p)]==z,'repeat stable '+str(p))
 reads[str(p)]=z;return z
def ref(p):
 p=path(p);z=read(p);return {'path':str(p),'sha256':hashlib.sha256(z).hexdigest(),'bytes':len(z)}
def vr(r):
 z=read(r['path']);ck(hashlib.sha256(z).hexdigest()==r['sha256'] and len(z)==r['bytes'],'pin '+r['path']);return z
def doc(p):return json.loads(read(p))
def rd(r):return json.loads(vr(r))
def save(n,d):
 with (O/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
ck(ref(N/'registration-draft.manifest.json')['sha256']=='952a0370bdee3672c6c18f5e378ba7df6b8e4f524ad612fa771d36c20ad242ca','draft manifest fixed hash')
ck(ref(N/'binding.json')['sha256']=='4a0474cde74e7793c50398f8143bdeb6a0f14b2f7981326c8f0c23f9174dff18','final binding fixed hash')
mf=doc(N/'registration-draft.manifest.json')
for row in mf['entries']:vr(row)
p=doc(N/'prepared_refs.json');b=doc(N/'binding.json');pre=doc(N/'binding.pre-review.json');s=rd(p['scope_ref']);a=doc(N/'audit.json')
ck(p['binding']==b,'prepared actual binding exact')
ck(dict(pre,controller_review_ref=b['controller_review_ref'])==b,'final binding only inserts sealed independent review')
sr=ref(N/'scope_registration.json');relative_sr=dict(sr,path=(N/'scope_registration.json').relative_to(R).as_posix())
ck(p['scope_ref']==relative_sr,'actual prepared scope exact ROOT-relative dictionary')
ck(p['expected_before']==b['before']==[324,152,430] and p['expected_after']==b['after']==[325,153,442],'exact before and after')
ck(p['actual_registration_executed'] is False and a['actual_registration_executed'] is False,'registration not yet performed')
ck(a['expected_before']==b['before'] and a['expected_after']==b['after'] and a['formal_increment']==0 and a['source_acceptance'] is False,'draft audit bounded semantics')
ck(p['audit_ref']['sha256']==ref(N/'audit.json')['sha256'],'actual prepared audit pin')
original=[vr(r) for r in p['original_refs']];desired=[vr(r) for r in p['desired_refs']]
ck(len(original)==len(desired)==4 and original[2:]==desired[2:],'four originals and unchanged ST/CM bytes')
ck([path(r['path']) for r in p['canonical_before']]==[R/x for x in CANON],'ordered current canonical refs exact')
for i,r in enumerate(p['canonical_before']):ck(vr(r)==original[i],'current actual before matches original '+CANON[i])
oldcp,oldow=map(json.loads,original[:2]);cp,ow=map(json.loads,desired[:2])
ck([oldcp['revision'],oldow['revision'],len(oldcp['failure_counters'])]==b['before'],'actual before tuple')
ck([cp['revision'],ow['revision'],len(cp['failure_counters'])]==b['after'],'actual desired tuple')
ck(cp['head']==oldcp['head']==s['source_commit'],'source head unchanged')
cut=rd(b['origin_cut_ref']);ck(p['origins']==cut['origins'] and len(p['origins'])==12,'exact twelve selected origins')
ck(cp['failure_counters']==oldcp['failure_counters']+cut['origins'],'entire430 prefix plus exact12')
ck(len({x['evidence_ref']['sha256'] for x in cut['origins']})==12,'twelve unique origin refs')
ck(not ({x['evidence_ref']['sha256'] for x in cut['origins']} & {x.get('evidence_ref',{}).get('sha256') for x in oldcp['failure_counters']}),'none already in old430')
for row in cut['origins']:ck(rd(row['evidence_ref'])==row['original_payload'],'origin original payload preserved '+row['evidence_ref']['path'])
wipkeys=['cli43_fresh_compiler_held2_scope_ref','cli43_fresh_compiler_current_source_authority_ref','cli43_fresh_compiler_controller_review_ref']
expectedcp=copy.deepcopy(oldcp);expectedow=copy.deepcopy(oldow)
expectedcp.update(revision=325,expected_previous_revision=324,updated_at=cp['updated_at'],updated_by='codex:/root',failure_counters=oldcp['failure_counters']+cut['origins'])
expectedcp['work_in_progress'].update(dict(zip(wipkeys,[relative_sr,b['current43_authority_ref'],b['controller_review_ref']])))
expectedow.update(revision=153,amended_at=cp['updated_at'],amended_by='codex:/root')
ck(cp==expectedcp,'all checkpoint fields unchanged except exact revision/stamp/origin/WIP allowlist')
ck(ow==expectedow,'all ownership fields unchanged except revision/stamp')
ck(a['registration_metadata_paths']==b['registration_metadata_paths']==CANON[:2],'only two canonical writes permitted')
controllerreview=rd(b['controller_review_ref']);ck(controllerreview['decision']=='READY_FOR_ROOT_CURRENT43_HELD2_ONCE' and controllerreview['requested_changes']==[] and controllerreview['reviewer']=='codex:/root/w05_merge_review','actual nonauthor bound scope review')
for key,actual in [('scope_sha256',relative_sr['sha256']),('runner_sha256',s['runner_ref']['sha256']),('launcher_sha256',s['launcher_ref']['sha256']),('gate_sha256',s['authorization_gate_ref']['sha256'])]:ck(controllerreview[key]==actual,'controller review binds '+key)
vh=doc(P/'cli43_root_binding_preparation_revision_codex/9fd9cbeb1343442aa6e34e41f3f2deea/handoff.json')
for r in vh['wrapper_refs']:
 name=Path(r['path']).name;raw=read(N/name);ck(raw==vr(r),'actual staged reviewed wrapper '+name);ast.parse(raw)
module=vr(vh['metadata_module_ref']).decode();ast.parse(module)
for needle in ["'all-four immediately before replace CAS'","os.replace(temp,target)","'post-source-guard final four CAS'","'post-source-guard seal four CAS'","d['reviewer']=='codex:/root/w05_merge_review'","safe(copied['path']).parent==safe(r['path']).parent","observation['all_observed_inputs_pre_pinned']=True"]:ck(needle in module,'retained reviewed producer guard '+needle)
lock=rd(b['toolchain_lock_ref'])['tools'];gitfacts=[]
for kind,args in [('head',['rev-parse','HEAD']),('status',['status','--porcelain=v1','--untracked-files=no']),('index',['diff','--cached','--name-only'])]:
 inv=doc(N/('prepare.'+kind+'.invocation.json'));r=inv['result'];c=r['job_cleanup'];out=vr(inv['stdout_ref']);vr(inv['stderr_ref'])
 ck(inv['kind']==kind and inv['argv']==[lock['git']['path']]+args and path(inv['cwd'])==R,'actual owned Git argv/cwd '+kind)
 ck(inv['actual_stage_native_exit']==0 and inv['wrapper_error'] is None and r['actual_exit']==0 and r['error'] is None and r['timed_out'] is False and r['resumed'] is True,'actual Git success '+kind)
 ck(r['owned_child_pid']>0 and r['creation_time_100ns']>0,'owned child identity '+kind)
 ck(c['errors']==[] and c['active_processes_last_observed']==0 and all(c[k] is True for k in ['unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed']),'full owned Job cleanup '+kind)
 ck(inv['environment']['GIT_OPTIONAL_LOCKS']=='0' and inv['environment']['GIT_NO_REPLACE_OBJECTS']=='1' and inv['environment']['GIT_CONFIG_NOSYSTEM']=='1' and inv['environment']['GIT_CONFIG_GLOBAL']=='nul','Git readonly/no replace/global override '+kind)
 if kind=='head':ck(out.decode('ascii').strip()==s['source_commit'],'actual prepare HEAD')
 if kind=='status':ck(hashlib.sha256(out).hexdigest()==s['main_git']['status_sha256'] and len(out)==s['main_git']['status_bytes'] and len(out.splitlines())==13 and sum(x.startswith(b' D ') for x in out.splitlines())==11,'actual status13/old11D')
 if kind=='index':ck(out==b'','actual empty index')
 gitfacts.append(ref(N/('prepare.'+kind+'.invocation.json')))
for label in ['binding-final','metadata-prepare']:
 inv=doc(N/(label+'.invocation.json'));ck(inv['actual_native_exit']==0 and inv['wrapper_error'] is None and inv['product_cases_executed'] is False and not inv['automatic_retry'] and not inv['counter_reset'],'actual metadata stage0 '+label);vr(inv['stdout_ref']);vr(inv['stderr_ref'])
request=doc(N/'metadata-prepare.request.json');argv=request['argv'];ck(json.loads(argv[argv.index('--scope-ref')+1])==relative_sr,'actual prepare argv relative scope')
ck(json.loads(argv[argv.index('--binding-ref')+1])==ref(N/'binding.json'),'actual prepare argv final binding')
runtime=doc(N/'prepare.runtime.json');inventory=rd(b['runtime_resources_ref']);allowed={os.path.normcase(str(path(r['path']))):r for r in inventory['files']}
for key in ['runner_ref','launcher_ref','authorization_gate_ref','owned_process_helper_ref','debug_tree_helper_ref']:
 r=s[key];allowed[os.path.normcase(str(path(r['path'])))]=r
ck(runtime['all_observed_inputs_pre_pinned'] is True and runtime['point_in_time_only'] is True and runtime['Python_lifecycle_proof'] is False and bool(runtime['files']),'actual strict-success marker and point-time limit')
for r in runtime['files']:
 key=os.path.normcase(str(path(r['path'])));prior=allowed.get(key)
 ck(prior is not None and prior['sha256']==r['sha256'] and prior['bytes']==r['bytes'],'observed runtime is pre-pinned '+r['path']);vr(r)
inventory_refs={}
for key in ['runtime_resources_ref','compiler_resources_ref','source_inputs_ref']:
 data=rd(b[key]);rows=data['files'] if 'files' in data else data['entries']
 for row in rows:
  k=os.path.normcase(str(path(row['path'])))
  if k in inventory_refs:ck((inventory_refs[k]['sha256'],inventory_refs[k]['bytes'])==(row['sha256'],row['bytes']),'overlapping inventory identity '+k)
  inventory_refs[k]=row
verified={os.path.normcase(str(path(r['path']))):r for r in p['verified_refs']}
ck(len(verified)==len(p['verified_refs']),'actual prepared verified input paths unique')
for k,r in inventory_refs.items():
 actual=verified.get(k);ck(actual is not None and (actual['sha256'],actual['bytes'])==(r['sha256'],r['bytes']),'prepared full-inventory declared pin membership '+k)
extra=[]
for k,r in verified.items():
 if k not in inventory_refs:vr(r);extra.append(r)
copied=[]
for canonical,raw in zip(CANON,original):
 name=Path(canonical).stem+'.before.raw'
 with (O/name).open('xb') as f:f.write(raw)
 rr=ref(O/name);ck(read(O/name)==raw and Path(rr['path']).parent==O,'own four snapshot exact '+name);copied.append(rr)
reused=[ref(P/'cli43_root_binding_static_independent_review_codex/c1a6b02b51ac427eb35ea000155db1c7/review.json'),ref(P/'cli43_current_bound_scope_independent_review_codex/46bfd2f723c84ad68e321774d6e08b30/compatibility-matrix.json'),b['controller_review_ref']]
for rr in reused:vr(rr)
ck(not(N/'run.started.json').exists() and not(N/'register.started.json').exists() and not(N/'canonical-write.intent.json').exists(),'actual registration still not run')
pending=ref(N/'failure-origin.94d3b3.json');ck(pending['sha256']=='98f25eed40e1227c292e7365d2fb8f5ec87aebaf45c2cb5069d754909b79a9be','explicit later Root locator origin retained outside fixed cut12')
for fp,raw in list(reads.items()):ck(Path(fp).read_bytes()==raw,'after unchanged '+fp)
failed=[x for x in checks if not x['pass']]
save('audit.json',{'checks':checks,'failed_checks':failed,'input_refs':[{'path':fp,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)} for fp,raw in reads.items()],'prepared_declared_verified_inputs':len(p['verified_refs']),'inventory_member_hashing':'No full resource-tree rehash. Declared catalogue rows compared to prepared verified refs; only actual observed runtime187 and non-inventory direct refs independently read.','actual_runtime_observed_files':len(runtime['files']),'verified_extra_refs':extra,'reused_reviews':reused,'target_execution':False,'new_failure_origins':[]})
review={'schema':'researchos.root-registration-source-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION' if not failed else 'REQUEST_CHANGES','requested_changes':failed,'actual_registration_executed':False,'expected_before':[324,152,430],'expected_after':[325,153,442],'register_sha256':ref(N/'register.py')['sha256'],'wrapper_sha256':ref(N/'run.py')['sha256'],'prepared_refs_sha256':ref(N/'prepared_refs.json')['sha256'],'audit_sha256':ref(N/'audit.json')['sha256'],'sealer_ref':ref(N/'seal.py'),'canonical_before':p['canonical_before'],'copied_canonical_before_refs':copied,'registration_draft_manifest_ref':ref(N/'registration-draft.manifest.json'),'binding_ref':ref(N/'binding.json'),'scope_ref':relative_sr,'review_audit_ref':ref(O/'audit.json'),'actual_prepare_git_refs':gitfacts,'runtime_observation_ref':ref(N/'prepare.runtime.json'),'reused_static_reviews':reused,'protected_facts':['Entire old430 failure prefix retained; exact12 original payloads appended once, no post-cut origins inserted.','Every unrelated checkpoint and ownership field preserved; step_state and commands exact original bytes.','Actual prepare Git reports source a510, status13/11D, empty index; each of three children has native0 and complete owned Job cleanup.','Runtime187 observations are pre-pinned and currently hash checked, point-in-time only; no Python/Git full lifecycle or product qualification.'],'actual_product_execution':False,'source_acceptance':False,'formal_increment':0,'new_failure_origins':[],'status':'STOPPED'}
review['later_pending_origin_refs']=[pending]
review['pending_boundary']='Root94d3b3 is preserved outside this fixed cut12; this review does not append it or infer native status. Other reported later Source origins are not independently enumerated here.'
save('review.json',review);print(json.dumps({'review_ref':ref(O/'review.json'),'checks':len(checks),'failed_checks':failed,'direct_read_files':len(reads),'prepared_verified_refs':len(p['verified_refs']),'runtime_observed':len(runtime['files'])},ensure_ascii=False))
