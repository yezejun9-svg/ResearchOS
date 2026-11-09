import ast,hashlib,json,os
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99';N=P/'integration_codex/cli43-fresh-held2-r325-975b85d8c2384852a834cc07d5b3cb90';O=Path(__file__).parent
reads={};checks=[]
def ck(x,n):checks.append({'check':n,'pass':bool(x)})
def ap(p):
 p=Path(p);return p if p.is_absolute() else R/p
def read(p):
 p=ap(p);z=p.read_bytes();k=str(p)
 if k in reads:ck(reads[k]==z,'stable read '+k)
 reads[k]=z;return z
def ref(p):
 p=ap(p);z=read(p);return {'path':str(p),'sha256':hashlib.sha256(z).hexdigest(),'bytes':len(z)}
def vr(r):
 z=read(r['path']);ck(len(z)==r['bytes'] and hashlib.sha256(z).hexdigest()==r['sha256'],'pin '+r['path']);return z
def doc(p):return json.loads(read(p))
def rd(r):return json.loads(vr(r))
def put(n,d):
 with (O/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
s=doc(N/'scope_registration.v2.json');old=doc(N/'scope_registration.json');b=doc(N/'binding.pre-review.v2.json');ob=doc(N/'binding.pre-review.json');mf=doc(N/'bound-scope.v2.manifest.json')
ck(ref(N/'scope_registration.v2.json')['sha256']=='ce591233d917afe8e2e16128385ca4ef0a113ab26541eaf92f6397cfa3928ca0','actual scopev2 pin')
ck(ref(N/'bound-scope.v2.manifest.json')['sha256']=='6a81a98e15f3fa3b9ec30d82ef9a406503961af1513e3785fa404f461f0aad1d','boundMFv2 pin')
for row in mf['entries']:vr(row)
ck({k for k in set(s)|set(old) if s.get(k)!=old.get(k)}=={'runtime_resources_ref','controller_review_path'},'scope exact two-field delta')
ck({k for k in set(b)|set(ob) if b.get(k)!=ob.get(k)}=={'runtime_resources_ref','controller_review_path'},'binding exact two-field delta')
ck(Path(s['controller_review_path'])==O/'review.json' and b['controller_review_ref'] is None,'acyclic fixed review path')
rt=rd(s['runtime_resources_ref']);ort=rd(old['runtime_resources_ref']);codes=b['metadata_code_refs']
ck(len(rt['files'])==1250 and rt['files'][:1242]==ort['files'],'old1242 exact prefix plus8')
expected=[]
for row in codes:
 vr(row);expected.append({'path':str(ap(row['path'])),'sha256':row['sha256'],'bytes':row['bytes']})
ck(rt['files'][1242:]==expected,'exact8 actual metadata absolute refs appended')
ck(len({os.path.normcase(x['path']) for x in rt['files']})==1250,'no runtime duplicate paths')
for row in rt['files'][1242:]:vr(row)
for key in ['runner_ref','launcher_ref','authorization_gate_ref','compiler_resources_ref','catalog_ref','instrumentation_ref','instrumented_source_ref','instrumentation_helper_ref','current43_authority_ref']:
 ck(s[key]==old[key],'unchanged '+key);vr(s[key])
ra=doc(N/'resource-overlay.audit.json');scope_inv={'path':(N/'scope_registration.v2.json').relative_to(R).as_posix(),'sha256':ref(N/'scope_registration.v2.json')['sha256'],'bytes':len(read(N/'scope_registration.v2.json'))}
ck(ra['scope_invocation_ref']==scope_inv,'Root invocation exact ROOT-relative scope dictionary')
driver=read(N/'root-metadata-phase.v2.py');old_driver=read(N/'root-metadata-phase.py');ast.parse(driver)
inverse=driver.replace(b'root-inputs.runtime-bound.v2.json',b'root-inputs.runtime-bound.json').replace(b'scope_registration.v2.json',b'scope_registration.json').replace(b'binding.pre-review.v2.json',b'binding.pre-review.json').replace(scope_inv['sha256'].encode(),ref(N/'scope_registration.json')['sha256'].encode())
line=b"scope_ref['path'] = (OUT / 'scope_registration.json').relative_to(ROOT).as_posix()\n"
ck(inverse.count(line)==1 and inverse.replace(line,b'')==old_driver,'outerdriver exact bounded inverse')
gate=vr(s['authorization_gate_ref']).decode();runner=vr(s['runner_ref']).decode();module_ref=codes[6];module=vr(module_ref).decode()
ck("'path': p.relative_to(ROOT).as_posix()" in gate or "p.relative_to(ROOT).as_posix()" in gate,'Gate Reader produces ROOT-relative ref')
ck("wip['cli43_fresh_compiler_held2_scope_ref'] == scope_ref" in gate and "grant['scope_ref'] == scope_ref" in gate,'CP and grant exact scope identities enforced')
ck("wipvalues=[scope_ref,b['current43_authority_ref'],b['controller_review_ref']]" in module and "'actual_registration_completed':True,'scope_ref':scope_ref" in module,'metadata preserves supplied scope spelling into CP/grant')
expectedmap={os.path.normcase(str(Path(x['path']).absolute())):x for x in rt['files']}
for row in expected:ck(expectedmap[os.path.normcase(row['path'])]==row,'gate expected runtime contains actual metadata '+row['path'])
rtree=ast.parse(runner);gtree=ast.parse(gate);mtree=ast.parse(module)
fn=next(x for x in rtree.body if isinstance(x,ast.FunctionDef) and x.name=='module_observation')
return_dicts=[x.value for x in ast.walk(fn) if isinstance(x,ast.Return) and isinstance(x.value,ast.Dict)]
keys=[k.value for k in return_dicts[0].keys if isinstance(k,ast.Constant)]
ck(keys==['files','point_in_time_only','Python_lifecycle_proof'],'actual module observation producer schema exact')
ck("observed['all_observed_inputs_pre_pinned'] is True" in gate,'gate requires absent producer field')
runtime=next(x for x in mtree.body if isinstance(x,ast.FunctionDef) and x.name=='runtime');runtime_text=ast.get_source_segment(module,runtime)
grant=next(x for x in mtree.body if isinstance(x,ast.FunctionDef) and x.name=='grant');grant_text=ast.get_source_segment(module,grant)
ck("observation=util.module_observation(allowed,helper)" in runtime_text and "save(output/(label+'.json'),observation)" in runtime_text and 'all_observed_inputs_pre_pinned' not in module,'runtime saves raw producer shape without required flag')
ck("observed=[copy_fact(safe(r['path'])) for r in (first_observed,final_observed,after_observed)]" in grant_text and "'runtime_observation_refs':observed" in grant_text,'grant copies original observation unchanged into final gate')
can=rd(b['canonical_before_ref']);docs=[]
for row in can['entries']:
 z=vr(row['ref']);ck(z==vr(row['live_original_ref']),'current4 unchanged '+row['canonical_path']);docs.append(json.loads(z))
ck([docs[0]['revision'],docs[1]['revision'],len(docs[0]['failure_counters'])]==[324,152,430] and b['after']==[325,153,442],'actual before/proposed after')
ck(not(N/'binding.json').exists() and not(N/'prepare.started.json').exists() and not Path(s['new_authorization_root']).exists(),'no preparation/grant already executed')
prior=ref(P/'cli43_current_bound_scope_independent_review_codex/7ef71c4ad3b14fd6a2d83ed1887894fa/review.json');ck(prior['sha256']=='557b989502da3a7ca15aeef7236cc6d272cfd93ae44223a44174626933880f84','prior review unchanged')
def function_source(tree,source,name):
 f=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name==name)
 return f,ast.get_source_segment(source,f)
def saved_shape(name,filename,required):
 f,txt=function_source(mtree,module,name);found=[]
 for node in ast.walk(f):
  if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='save' and len(node.args)>=2 and isinstance(node.args[1],ast.Dict):
   if filename in ast.get_source_segment(module,node.args[0]):
    found.append({k.value for k in node.args[1].keys if isinstance(k,ast.Constant)})
 ck(len(found)==1 and set(required)<=found[0],name+' producer shape '+filename)
 return {'producer_function':name,'output':filename,'required_keys':required,'actual_literal_keys':sorted(found[0]) if len(found)==1 else [],'status':'STATIC_COMPATIBLE' if len(found)==1 and set(required)<=found[0] else 'STATIC_MISMATCH'}
compat=[]
for name,filename,required in [
 ('prepare','prepared_refs.json',['binding','scope_ref','canonical_before','original_refs','desired_refs','origins','audit_ref','verified_refs','expected_before','expected_after','actual_registration_executed']),
 ('register','canonical-write.intent.json',['actor','Main_head','transition','metadata','unchanged','review_ref','automatic_retry','recovery']),
 ('register','canonical-write.verified.json',['checkpoint','ownership','failure_origins','intent_ref','step_state_commands_unchanged']),
 ('run_registration','invocation.json',['actor','argv','cwd','actual_exit','result','wrapper_error','review_ref','runner_sha256','wrapper_sha256','stdout_sha256','stderr_sha256','automatic_retry','counter_reset','actual_outer_tool_exit']),
 ('seal','registration-audit.json',['actor','status','before','after','actual_registration_exit','invocation_ref','intent_ref','verified_ref','review_ref','formal_increment']),
 ('seal','manifest.json',['entries','count','excluded_only_self']),
 ('grant','prelaunch.json',['runtime_resources_ref','toolchain_lock_ref','git','source_round','time_window_ref','admission_ref','point_in_time_only','raw_reference_semantics']),
 ('grant','authorization.execute.json',['schema','actor','status','actual_registration_completed','scope_ref','binding','canonical_copies','registration_refs','authority_review_refs','prelaunch_evidence_ref','runtime_observation_refs'])]:
 compat.append(saved_shape(name,filename,required))
texts={name:function_source(mtree,module,name)[1] for name in ['prepare','prepared','registration_review','register','run_registration','seal','grant','git_guard','job_ok','main']}
gtexts={name:function_source(gtree,gate,name)[1] for name in ['binding','load_scope','registration_refs','validate_authority','validate_grant']}
checks_by_stage=[
 ('prepare -> reviewed desired files',texts['prepare'],["gate.load_scope", "review['requested_changes']==[]", "pin(output/name)==known[output/name]", "wipvalues=[scope_ref,b['current43_authority_ref'],b['controller_review_ref']]", "rawdesired=[encoded(desiredcp),encoded(desiredow),*before[2:]]"]),
 ('prepared -> register/run/seal',texts['prepared'],["p['binding']==b", "original[2:]==desired[2:]", "oldcp['failure_counters']+origins(b,oldcp)", "protectedcp==oldcp and protectedow==oldow", "p['scope_ref'],b['current43_authority_ref'],b['controller_review_ref']"]),
 ('independent registration review',texts['registration_review'],["'codex:/root/w05_merge_review'", "d['actual_registration_executed'] is False", "d['canonical_before']==p['canonical_before']", "len(d['copied_canonical_before_refs'])==4", "safe(copied['path']).parent==safe(r['path']).parent"]),
 ('register guarded writes',texts['register'],["'all-four immediately before replace CAS'", "os.replace(temp,target)", "expected[i]=desired[i]", "READS.pop(str(target),None)", "'post-source-guard final four CAS'", "'automatic_retry':False", "FORWARD_ONLY_REQUIRES_SEPARATE_ROOT_DECISION"]),
 ('owned register actual exits',texts['run_registration'],["helper.run_owned", "finally:", "result['actual_exit'] if result else None", "'actual_outer_tool_exit':None", "job_ok(result)"]),
 ('seal -> immutable registration consumer',texts['seal'],["job_ok(inv['result'])", "inv['actual_exit']==0", "'actual raw mismatch'", "'post-source-guard seal four CAS'", "ACTUAL_CANONICAL_REGISTRATION_CLOSED_NO_CASE_ACCEPTANCE", "x.name!='manifest.json'"]),
 ('gate registration links',gtexts['validate_authority'],["audit['invocation_ref'] == registration['invocation']", "audit['intent_ref'] == registration['intent']", "audit['verified_ref'] == registration['verified']", "audit['review_ref'] == inv['review_ref']", "'Registration independent review'", "'Failure history prefix changed'"]),
 ('grant exact identities/copies',texts['grant'],["gate.validate_authority(reader,scope,scope_ref,preliminary,rr)", "first_records,first_observed=facts('admission')", "root.mkdir()", "gate.validate_authority(reader,scope,scope_ref,copies,rr)", "final_records,final_observed=facts('grant-final')", "'immediate pre-grant live four CAS'", "'binding':gate.binding(scope)", "gate.validate_grant"]),
 ('gate actual grant consumer',gtexts['validate_grant'],["grant['scope_ref'] == scope_ref", "grant['binding'] == binding(scope)", "grant['authority_review_refs'] == authority", "prelaunch['runtime_resources_ref'] == scope['runtime_resources_ref']", "['head','status','index']", "observed['all_observed_inputs_pre_pinned'] is True"]),
]
for label,txt,needles in checks_by_stage:
 for needle in needles:ck(needle in txt,label+' exact source guard '+needle)
 compat.append({'stage':label,'status':'STATIC_SOURCE_REVIEWED_NOT_EXECUTED','source_guards':needles})
grant_order=["gate.validate_authority(reader,scope,scope_ref,preliminary,rr)","first_records,first_observed=facts('admission')","root.mkdir()","gate.validate_authority(reader,scope,scope_ref,copies,rr)","final_records,final_observed=facts('grant-final')","'immediate pre-grant live four CAS'","gr=save(root/'authorization.execute.json'","gate.validate_grant"]
positions=[grant_text.find(x) for x in grant_order]
ck(all(x>=0 for x in positions) and positions==sorted(positions),'sealed authority/admission/own auth leaf/copied originals/final Git/live4/grant/consumer actual source order')
producer_fields={'prepare':{},'register':{},'run_registration':{},'seal':{},'grant':{}}
for name in producer_fields:
 f,_=function_source(mtree,module,name)
 for node in ast.walk(f):
  if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='save' and len(node.args)>=2 and isinstance(node.args[1],ast.Dict):
   producer_fields[name][ast.get_source_segment(module,node.args[0])]=[k.value for k in node.args[1].keys if isinstance(k,ast.Constant)]
put('compatibility-matrix.json',{'method':'Static complete producer/consumer source reading plus AST literal schemas and explicit ref/guard/order checks. No target import or execution.','stages':compat,'producer_saved_dictionary_shapes':producer_fields,'confirmed_remaining_code_blockers':['CLI43-BS-OBS-02'],'input_fixes_closed':['ROOT-relative scope ref exact-dictionary identity','1242+8 metadata ABS runtime membership'],'not_claimed':['successful future preparation/registration/seal/grant','full future Go graph','actual OS lifecycle','runtime1250 sufficient for all future loads','time budget fit','product or formal acceptance']})
for p,z in list(reads.items()):ck(Path(p).read_bytes()==z,'after stable '+p)
finding={'id':'CLI43-BS-OBS-02','priority':'BLOCKER','kind':'STATIC_PRODUCER_CONSUMER_SCHEMA_MISMATCH_NOT_EXECUTED','producer_ref':s['runner_ref'],'adapter_ref':module_ref,'consumer_ref':s['authorization_gate_ref'],'locations':['current43_runner.v4.proposed.py:151-166 module_observation return','metadata_pipeline.v6.proposed.py:runtime saves observation; grant copies3 observations unchanged','authorization_gate.v5.proposed.py:300 observed all_observed_inputs_pre_pinned'],'actual_return_keys':keys,'required_key':'all_observed_inputs_pre_pinned','reason':'The producer checks every observed row but returns only files/point_in_time_only/Python_lifecycle_proof. The adapter saves and copies this shape unchanged. Final gate direct-indexes absent all_observed_inputs_pre_pinned, so even with valid1250 membership it cannot close grant validation.','minimal_fix':'In a new immutable metadata adapter revision, only after module_observation returns successfully from all resource checks, add the exact derived boolean all_observed_inputs_pre_pinned=True to its saved observation. Preserve files and point-time/non-lifecycle fields and all unknown-resource rejection; do not predeclare success before the call. Independently review new code/scope before actualprepare.','verification':'Static producer→savedJSON→copiedfacts→consumer key/type agreement, whole-file inverse for only this addition, failed observation cannot reach save/flag, no change to gate/resource acceptance/CAS/roster/time.','actual_product_or_grant_run':0}
put('audit.json',{'checks':checks,'failed_audit_checks':[x for x in checks if not x['pass']],'input_refs':[{'path':p,'sha256':hashlib.sha256(z).hexdigest(),'bytes':len(z)} for p,z in reads.items()],'static_finding':finding,'target_execution':0})
review={'schema':'researchos.cli43-compiler-controller-static-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'REQUEST_CHANGES','requested_changes':[finding],'scope_sha256':scope_inv['sha256'],'runner_sha256':s['runner_ref']['sha256'],'launcher_sha256':s['launcher_ref']['sha256'],'gate_sha256':s['authorization_gate_ref']['sha256'],'scope_ref':ref(N/'scope_registration.v2.json'),'scope_invocation_ref':scope_inv,'bound_manifest_ref':ref(N/'bound-scope.v2.manifest.json'),'audit_ref':ref(O/'audit.json'),'prior_review_ref':prior,'verified_input_fixes':['Root-relative scope dictionary now matches Gate.Reader.ref and is preserved into CP/grant.','Runtime1250 retains old1242 exact prefix and appends only eight byte-verified ABS metadata refs; finalgate expected map contains these wrapper identities.','Scope onlyruntime_ref/reviewpath changed; actualUID/roots/source/two cases/caps/proposed442 remain unchanged.'],'expected_before':b['before'],'expected_after':b['after'],'actual_registration_executed':False,'actual_product_execution':False,'review_itself_grants_execution':False,'reused_limits':'Prior597-source/22138compiler/1242partialruntime review reused; only8metadata added-file hashes were independently read. No fresh graph/lifecycle/timefit/source/formal claim.','new_failure_origins':[],'status':'STOPPED'}
review['compatibility_matrix_ref']=ref(O/'compatibility-matrix.json')
review['complete_chain_static_conclusion']='Full prepare/prepared/registration_review/register/run/seal/grant and gate load_scope/validate_authority/validate_grant reviewed. One confirmed remaining code blocker: CLI43-BS-OBS-02. Other mapped output keys, exact refs and ordering are statically compatible subject to fresh actual Root binding, independent registration review, actual CAS/seal, strict observations and unchanged inputs; this is not execution proof.'
review['audit_failed_checks']=[x for x in checks if not x['pass']]
put('review.json',review);print(json.dumps({'review_ref':ref(O/'review.json'),'checks':len(checks),'failed_audit_checks':sum(not x['pass'] for x in checks),'requests':1},ensure_ascii=False))
