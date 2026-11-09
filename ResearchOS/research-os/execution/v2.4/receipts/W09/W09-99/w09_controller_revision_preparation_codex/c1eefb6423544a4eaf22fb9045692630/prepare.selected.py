"""Pure IO/AST construction; does not import any candidate or execute a target."""
import ast, difflib, hashlib, json
from pathlib import Path
OUT=Path(__file__).resolve().parent/'selected'
OUT.mkdir(exist_ok=False)
BASE=OUT.parent.parent.parent
OLD=BASE/'finite_controller_preparation_codex/2098f8232b5a4331b0cac70eccd32ce0'
REVIEW=BASE/'f08_controller_independent_review_codex/d16a4b150b4e4fa9836f852c4a2bc505'
inputs={}; edits={}; originals={}; candidates={}
def pin(p,raw=None):
 raw=p.read_bytes() if raw is None else raw
 return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def read(p):
 raw=p.read_bytes();inputs[str(p)]=pin(p,raw);return raw
def save(name,raw):
 p=OUT/name
 with p.open('xb') as f:f.write(raw)
 return pin(p,raw)
def doc(name,obj):return save(name,(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
def change(name,old,new):
 raw=candidates[name];newline=b'\r\n' if originals[name].count(b'\r\n')>originals[name].count(b'\n')//2 else b'\n'
 a=old.encode().replace(b'\n',newline);b=new.encode().replace(b'\n',newline)
 if raw.count(a)!=1:raise RuntimeError('Exact unique anchor required: '+name+' '+repr(a[:100]))
 candidates[name]=raw.replace(a,b,1);edits.setdefault(name,[]).append({'before':a.decode(),'after':b.decode()})
names=['controller_common.py','controller.py','case_worker.py','launch.py','seal_readonly.py','windows_debug_job_tree.py']
for n in names:originals[n]=read(OLD/n);candidates[n]=originals[n]
normal=read(OLD/'inputs/2-windows_owned_process.py')
for n in ['review.json','handoff.json','manifest.json','failure-origins.json']:read(REVIEW/n)
for n in ['handoff.json','manifest.json','spec.json','finite-roster.json','implementation-conditions.json','root-grant.UNAUTHORIZED.template.json']:read(OLD/n)

# C01: failure notification remains held until actual owned-Job termination succeeds.
change('windows_debug_job_tree.py','    generations = []','    generations = []\n    debug[\'process_generations\'] = generations  # Live partial observations, including failures.\n    debug[\'pending_failure_event\'] = None')
change('windows_debug_job_tree.py',"            event_fact = {'code':int(event.code), 'pid':int(event.pid), 'tid':int(event.tid)}", "            event_fact = {'code':int(event.code), 'pid':int(event.pid), 'tid':int(event.tid)}\n            event_owned = event.pid in processes and not processes[event.pid]['exit_continued']")
change('windows_debug_job_tree.py',"                    retained_process = HANDLE()", "                    event_owned = True  # Actual IsProcessInJob succeeded while event is held.\n                    retained_process = HANDLE()")
change('windows_debug_job_tree.py',"""                finally:
                    # Always release the received notification, even after capture failure.
                    require(continue_debug(event.pid, event.tid, status))
                    if event.code == 5 and event.pid in processes:
                        processes[event.pid]['exit_continued'] = True
                    if len(debug['events']) < 131072:
                        debug['events'].append(event_fact)
                    else:
                        record_error(RuntimeError('Debug event bound exceeded'))""", """                except BaseException as exc:
                    record_error(exc)
                finally:
                    if len(debug['events']) >= 131072:
                        record_error(RuntimeError('Debug event bound exceeded'))
                    failed = result['error'] is not None or result['timed_out']
                    may_continue = not failed
                    if failed:
                        pending = dict(event_fact, continuation_status=status, owned_event=event_owned)
                        debug['pending_failure_event'] = pending
                        # Never release an unqualified image/module before killing its owned Job.
                        try:
                            if not assigned:
                                raise RuntimeError('Failed event has no assigned exclusive Job')
                            cleanup['termination_code_requested'] = 0xE0000308
                            cleanup['termination_requested'] = True
                            cleanup['termination_succeeded'] = bool(terminate_job(job, 0xE0000308))
                            require(cleanup['termination_succeeded'])
                            event_fact['job_terminated_before_continue'] = True
                            may_continue = event_owned
                        except BaseException as exc:
                            record_error(exc)
                    try:
                        if may_continue:
                            require(continue_debug(event.pid, event.tid, status))
                            event_fact['continued'] = True
                            debug['pending_failure_event'] = None
                            if event.code == 5 and event.pid in processes:
                                processes[event.pid]['exit_continued'] = True
                        else:
                            event_fact['continued'] = False
                    except BaseException as exc:
                        record_error(exc)
                    finally:
                        if len(debug['events']) < 131072:
                            debug['events'].append(event_fact)""")
change('windows_debug_job_tree.py',"                    deadline = time.monotonic() + 5.0", """                    pending = debug['pending_failure_event']
                    if pending is not None:
                        if not assigned or not cleanup.get('termination_succeeded') or not pending['owned_event']:
                            raise RuntimeError('Held failed debug event cannot be safely continued')
                        require(continue_debug(pending['pid'], pending['tid'], pending['continuation_status']))
                        pending['cleanup_continued_after_job_termination'] = True
                        if pending['code'] == 5 and pending['pid'] in processes:
                            processes[pending['pid']]['exit_continued'] = True
                        debug['pending_failure_event'] = None
                    deadline = time.monotonic() + 5.0""")

# C03/C04: resource denial is never rewritten as exit zero or downgraded to HOLD.
change('controller.py','env=None,allow_nonzero=False):','env=None):')
change('controller.py',"""   if allow_nonzero and result and result.get('actual_exit')!=0:
    # Resource failure only. Still require actual exit/idle/handles and complete observed runtime.
    adjusted=dict(result);adjusted['actual_exit']=0
    require_job(adjusted,True)
   else:require_job(result,True)""",'   require_job(result,True)')
change('controller.py',"   except OSError as e:self.resource['symlink']='HOLD_RESOURCE';write_json(root/'failure.json',{'actual_native_exit':None,'exception_type':type(e).__name__,'message':str(e),'qualification':'NOT_RUN_RESOURCE_HOLD'})", """   except OSError as e:
    write_json(root/'failure.json',{'actual_native_exit':None,'exception_type':type(e).__name__,'message':str(e),'qualification':'STOP_UNEXPECTED_RESOURCE_FAILURE'})
    raise""")
change('controller.py',"""   d,result=self.run('junction-resource',[cmd['path'],'/D','/V:OFF','/S','/C',command],root,15,1,[cmd],allow_nonzero=True)
   if result['actual_exit']!=0:self.resource['junction']='HOLD_RESOURCE_UNEXPLAINED_NATIVE_FAILURE'
   else:
    s=link.lstat()
    if not getattr(s,'st_file_attributes',0)&0x400 or link.resolve()!=b.resolve():raise Stop('Wrong actual junction/target')
    self.resource['junction']='AVAILABLE';self.link=root""", """   d,result=self.run('junction-resource',[cmd['path'],'/D','/V:OFF','/S','/C',command],root,15,1,[cmd])
   s=link.lstat()
   if not getattr(s,'st_file_attributes',0)&0x400 or link.resolve()!=b.resolve():raise Stop('Wrong actual junction/target')
   self.resource['junction']='AVAILABLE';self.link=root""")
change('seal_readonly.py',"check_closed_evidence\n", "check_closed_evidence,validate_grant\n")
change('seal_readonly.py'," holds=[];scenario_pass=0;actual_leaf=0", """ started=raw_json((root/'started.json').read_bytes())
 grant,signed_spec,expected_root=validate_grant(started['grant_ref']['path'],started['grant_ref']['sha256'])
 if expected_root!=root or grant['spec_ref']!=spec_ref or signed_spec!=spec:raise Stop('Seal authority/spec/run substitution')
 holds=[];scenario_pass=0;actual_leaf=0""")
change('seal_readonly.py',"  if row['state']=='NOT_RUN_RESOURCE_HOLD':holds.append(row);continue", """  if row['state']=='NOT_RUN_RESOURCE_HOLD':
   required=planned['requires_resource']
   if not required or not any(grant['resources'][k] is False for k in required) or row['requirements']!=required or row['actual_native_exit'] is not None:raise Stop('Unjustified resource HOLD')
   holds.append(row);continue""")
change('seal_readonly.py',"""  if native==0:require_job(entry['owned_result'],True)
  elif 'junction-resource' not in p.parent.name:raise Stop('Unexpected failed native invocation')""", """  require_job(entry['owned_result'],True)
  if type(native) is not int or native!=0 or native!=entry['owned_result']['actual_exit']:raise Stop('Native exit fact mismatch')""")
change('controller_common.py'," if result.get('actual_exit')!=0", " if type(result.get('actual_exit')) is not int or result.get('actual_exit')!=0")

# C05/C06 are a proposed future Root protocol; missing actual binding refuses execution.
authority = '''def verified_raw(row):
 if not isinstance(row,dict) or set(row)!={'path','sha256','bytes'}:raise Stop('Exact file ref required')
 p=no_alias(row['path']);before=p.stat();raw=p.read_bytes();after=p.stat()
 if (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns):raise Stop('Pinned read drift')
 if str(p)!=row['path'] or type(row['bytes']) is not int or len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:raise Stop('Consumed raw pin mismatch')
 return raw

def root_authority(g,spec,grant_ref):
 # Proposed Root capsule. Its real producer/CAS adapter is an explicit OPEN prerequisite.
 binding=spec.get('root_binding')
 if not isinstance(binding,dict):raise Stop('UNBOUND: actual Root binding absent')
 consumed=[grant_ref,g['spec_ref']]
 def read(ref):
  raw=verified_raw(ref);consumed.append(ref);return raw_json(raw)
 def eq(a,b,label):
  if type(a) is not type(b) or json.dumps(a,sort_keys=True,allow_nan=False)!=json.dumps(b,sort_keys=True,allow_nan=False):raise Stop('Root authority mismatch: '+label)
 def pointer(obj,keys):
  if not isinstance(keys,list) or not keys:raise Stop('Explicit canonical field path required')
  for key in keys:obj=obj[key]
  return obj
 before=binding['before'];after=binding['after']
 if any(not isinstance(x,list) or len(x)!=3 or any(type(n) is not int or n<0 for n in x) for x in (before,after)):raise Stop('Explicit Root transition required')
 if after[0]!=before[0]+1 or after[1]!=before[1]+1 or after[2]<before[2]:raise Stop('Nonforward Root transition')
 capsule=read(g['registration_evidence_ref'])
 eq(capsule['schema'],'researchos.w09.root-registration-capsule.v1','capsule schema')
 eq(capsule['actor'],'codex:/root','registration actor')
 eq(capsule['before'],before,'before tuple');eq(capsule['after'],after,'after tuple')
 eq(capsule['registration_namespace'],binding['registration_namespace'],'registration namespace')
 root=no_alias(binding['registration_namespace'])
 for ref in [g['registration_evidence_ref'],capsule['manifest_ref'],capsule['audit_ref'],capsule['invocation_ref'],capsule['request_ref'],capsule['intent_ref']]:
  if not Path(ref['path']).is_relative_to(root):raise Stop('Foreign registration receipt')
 manifest=read(capsule['manifest_ref']);members=manifest['members']
 if not members or len({r['path'].casefold() for r in members})!=len(members):raise Stop('Registration manifest duplicate/empty')
 for ref in members:
  verified_raw(ref);consumed.append(ref)
 for key in ['audit_ref','invocation_ref','request_ref','intent_ref','registration_review_ref']:
  if capsule[key] not in members:raise Stop('Unsealed mandatory registration input '+key)
 audit=read(capsule['audit_ref']);invocation=read(capsule['invocation_ref']);request=read(capsule['request_ref']);intent=read(capsule['intent_ref'])
 eq(audit['status'],'REGISTRATION_COMPLETED','registration completion')
 eq(audit['actual_registration_executed'],True,'actual registration')
 eq(audit['before'],before,'audit before');eq(audit['after'],after,'audit after')
 eq(audit['intent_ref'],capsule['intent_ref'],'intent');eq(audit['invocation_ref'],capsule['invocation_ref'],'invocation')
 eq(invocation['request_ref'],capsule['request_ref'],'actual request')
 eq(invocation['actualargv'],request['argv'],'actual argv');eq(invocation['cwd'],request['cwd'],'actual cwd')
 for key in ['stdout_ref','stderr_ref']:
  verified_raw(invocation[key]);consumed.append(invocation[key])
  if invocation[key] not in members:raise Stop('Unsealed actual registration raw')
 if not request['argv'] or request['argv'][0]!=g['tools']['python']['path']:raise Stop('Registration Python substitution')
 require_job(invocation['owned_result'])
 if type(invocation['actual_native_exit']) is not int or invocation['actual_native_exit']!=0:raise Stop('Registration native completion absent')
 rr=read(capsule['registration_review_ref'])
 eq(rr['schema'],'researchos.w09.root-registration-review.v1','registration review schema')
 eq(rr['reviewer'],'codex:/root/w05_merge_review','registration nonauthor')
 eq(rr['decision'],'REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION','registration review decision')
 eq(rr['requested_changes'],[],'registration changes');eq(rr['actual_registration_executed'],False,'review timing')
 eq(rr['before'],before,'review before');eq(rr['after'],after,'review after')
 eq(rr['request_ref'],capsule['request_ref'],'reviewed actual request')
 for key in ['register_ref','wrapper_ref','prepared_ref']:
  eq(rr[key],request[key],'reviewed registration code');verified_raw(request[key]);consumed.append(request[key])
 if request['register_ref']['path'] not in request['argv'] and request['wrapper_ref']['path'] not in request['argv']:raise Stop('Reviewed code absent from actual registration argv')
 canonical=capsule['canonical_copies']
 if [r['role'] for r in canonical]!=['checkpoint','ownership','step_state','commands']:raise Stop('Ordered four canonical copies required')
 if len({r['original_path'].casefold() for r in canonical})!=4:raise Stop('Canonical original path collision')
 eq([r['original_path'] for r in canonical],binding['canonical_original_paths'],'actual canonical target paths')
 eq(canonical,intent['canonical_copies'],'intent desired/original pairs');eq(audit['canonical_copies'],canonical,'actual installed canonical pairs')
 documents=[]
 for item in canonical:
  for key in ['before_ref','after_ref']:
   if item[key] not in members:raise Stop('Unsealed canonical bytes')
  prior=read(item['before_ref']);current=read(item['after_ref']);documents.append((prior,current))
  if item['role'] in ('step_state','commands') and item['before_ref']['sha256']!=item['after_ref']['sha256']:raise Stop('Unrelated canonical bytes changed')
 fields=binding['canonical_fields']
 cp0,cp=documents[0];ow0,ow=documents[1]
 eq(pointer(cp0,fields['checkpoint_revision']),before[0],'original checkpoint');eq(pointer(cp,fields['checkpoint_revision']),after[0],'current checkpoint')
 eq(pointer(ow0,fields['ownership_revision']),before[1],'original ownership');eq(pointer(ow,fields['ownership_revision']),after[1],'current ownership')
 f0=pointer(cp0,fields['failure_origins']);f1=pointer(cp,fields['failure_origins'])
 if not isinstance(f0,list) or not isinstance(f1,list) or len(f0)!=before[2] or len(f1)!=after[2] or f1[:len(f0)]!=f0:raise Stop('Failure prefix/cut changed')
 eq(f1[len(f0):],binding['new_failure_origins'],'fixed new failure cut')
 eq(pointer(cp,fields['scope_ref']),g['spec_ref'],'current checkpoint scope')
 eq(pointer(cp,fields['review_ref']),g['controller_review_ref'],'current checkpoint nonauthor review')
 lease=pointer(ow,fields['lease'])
 eq(lease,{'owner':'codex:/root','status':'EXECUTION_AUTHORIZED_ONCE','scope_ref':g['spec_ref'],'run_nonce':g['run_nonce'],'source_commit':CANDIDATE},'current Root lease')
 payload={k:g[k] for k in ['source_commit','base_commit','run_nonce','output_parent','output_root','spec_ref','controller_refs','tools','normal_helper_ref','debug_helper_ref','caps','resources','resource_files','runtime_catalog_ref','goroot','module_cache','go_tool_images','repository']}
 review=read(g['controller_review_ref'])
 eq(str(no_alias(g['controller_review_ref']['path'])),str(no_alias(binding['controller_review_path'])),'predeclared review path')
 eq(review['schema'],'researchos.w09.finite-controller-bound-review.v1','controller review schema')
 eq(review['reviewer'],'codex:/root/w05_merge_review','controller nonauthor')
 eq(review['decision'],'READY_FOR_ROOT_W09_FINITE_ONCE','controller review decision')
 eq(review['requested_changes'],[],'controller review changes');eq(review['execution_binding'],payload,'full bound inputs')
 eq(review['scope_ref'],g['spec_ref'],'full reviewed spec')
 issuance=read(g['root_issuance_ref'])
 eq(issuance['schema'],'researchos.w09.root-once-issuance.v1','issuance schema');eq(issuance['actor'],'codex:/root','issuer')
 eq(issuance['actual_registration_completed'],True,'actual Root registration')
 eq(issuance['execution_binding'],payload,'issued inputs');eq(issuance['registration_evidence_ref'],g['registration_evidence_ref'],'issued registration')
 eq(issuance['controller_review_ref'],g['controller_review_ref'],'issued nonauthor review')
 eq(g['authority_refs'],[g['registration_evidence_ref'],g['root_issuance_ref']],'authority refs')
 eq(g['independent_review_refs'],[g['controller_review_ref'],capsule['registration_review_ref']],'review refs')
 return list({r['path']:r for r in consumed}.values())

'''
change('controller_common.py','def trusted_module(path,expected):\n verify(expected)','def trusted_module(path,expected):\n raw=verified_raw(expected)')
change('controller_common.py'," exec(compile(Path(path).read_bytes(),str(path),'exec'),mod.__dict__)"," exec(compile(raw,str(path),'exec'),mod.__dict__)")
change('controller_common.py','def validate_grant(path,expected_sha):',authority+'def validate_grant(path,expected_sha):')
change('controller_common.py'," g=raw_json(Path(path).read_bytes())"," g=raw_json(verified_raw(actual))")
change('controller_common.py'," spec=raw_json(Path(g['spec_ref']['path']).read_bytes())"," spec=raw_json(verified_raw(g['spec_ref']))")
change('controller_common.py'," for name,row in g['tools'].items():verify(row)",""" roles=['common_ref','controller_ref','case_worker_ref','launcher_ref','sealer_ref','normal_helper_ref','debug_helper_ref']
 if g['controller_refs']!=[spec[k] for k in roles] or len({r['path'].casefold() for r in g['controller_refs']})!=7:raise Stop('Exact reviewed mechanism closure required')
 if g['normal_helper_ref']!=spec['normal_helper_ref'] or g['debug_helper_ref']!=spec['debug_helper_ref']:raise Stop('Helper role substitution')
 if file_ref(Path(__file__).resolve())!=spec['common_ref']:raise Stop('Actual common module differs')
 main=file_ref(Path(sys.modules['__main__'].__file__).resolve())
 if main not in [spec[k] for k in ['controller_ref','case_worker_ref','launcher_ref','sealer_ref']]:raise Stop('Actual entry mechanism differs')
 if set(g['tools'])!={'python','go','git','cmd'}:raise Stop('Exact tool roles required')
 for name,row in g['tools'].items():verify(row)""")
change('controller_common.py'," return g,spec,out",""" g['_authorization_input_refs']=root_authority(g,spec,actual)
 g['_grant_ref']=actual
 return g,spec,out""")
change('controller.py',"  self.ledger.add([r['path'] for r in g['controller_refs']]+[g['spec_ref']['path']],'controller-spec')","  self.ledger.add([r['path'] for r in g['controller_refs']]+[r['path'] for r in g['_authorization_input_refs']],'controller-spec-actual-authority')")
change('controller.py',"'authorized_by_controller':True,'source_commit':CANDIDATE", "'authorized_by_controller':True,'root_grant_ref':self.g['_grant_ref'],'spec_ref':self.g['spec_ref'],'source_commit':CANDIDATE")
change('case_worker.py'," verify(r['self_ref']);verify(r['debug_helper_ref'])", """ g,s,out=validate_grant(r['root_grant_ref']['path'],r['root_grant_ref']['sha256'])
 if r['spec_ref']!=g['spec_ref'] or r['self_ref']!=s['case_worker_ref'] or r['debug_helper_ref']!=s['debug_helper_ref'] or r['python_ref']!=g['tools']['python']:raise Stop('Worker mechanism substitution')
 if not no_alias(r['output_dir']).is_relative_to(out/'native'):raise Stop('Case output outside authorized run')
 verify(r['self_ref']);verify(r['debug_helper_ref'])""")

checks=[]
for name,raw in candidates.items():
 ast.parse(raw,filename=name)
 inverse=raw
 for e in reversed(edits.get(name,[])):
  b=e['after'].encode();a=e['before'].encode()
  if inverse.count(b)!=1:raise RuntimeError('Inverse anchor not unique '+name)
  inverse=inverse.replace(b,a,1)
 if inverse!=originals[name]:raise RuntimeError('Whole byte inverse failed '+name)
 save(name,raw)
 save(name+'.inverse-original',inverse)
 save(name+'.patch.txt',''.join(difflib.unified_diff(originals[name].decode().splitlines(True),raw.decode().splitlines(True),fromfile='original/'+name,tofile='candidate/'+name)).encode())
 checks.append({'file':name,'AST':'PASS_STATIC_ONLY','whole_byte_inverse':True,'changes':len(edits.get(name,[]))})
normalref=save('windows_owned_process.py',normal)
spec=json.loads(inputs[str(OLD/'spec.json')] and (OLD/'spec.json').read_bytes())
spec['root_binding']=None
spec['status']='PREPARATION_ONLY_ROOT_BINDING_AND_NONAUTHOR_REVIEW_REQUIRED'
roles={'common_ref':'controller_common.py','controller_ref':'controller.py','case_worker_ref':'case_worker.py','launcher_ref':'launch.py','sealer_ref':'seal_readonly.py','normal_helper_ref':'windows_owned_process.py','debug_helper_ref':'windows_debug_job_tree.py'}
for role,name in roles.items():spec[role]=pin(OUT/name)
spec['controller_refs']=[spec[k] for k in roles]
spec['future_output_parent']=str(OUT/'future-root-bound-output-parent')
spec_ref=doc('spec.proposed.json',spec)
grant=json.loads((OLD/'root-grant.UNAUTHORIZED.template.json').read_bytes())
grant.update(authorized=False,spec_ref=spec_ref,controller_refs=spec['controller_refs'],normal_helper_ref=spec['normal_helper_ref'],debug_helper_ref=spec['debug_helper_ref'],root_issuance_ref=None,controller_review_ref=None,registration_evidence_ref=None)
doc('root-grant.UNAUTHORIZED.proposed.json',grant)
save('finite-roster.original.json',read(OLD/'finite-roster.json'))
doc('edits.json',edits)
# Business functions and frozen roster/caps are compared statically, never invoked.
for name,funcs in [('controller.py',['json_stream','test_facts']),('controller_common.py',['check_closed_evidence'])]:
 trees=[ast.parse(r) for r in (originals[name],candidates[name])]
 for fn in funcs:
  nodes=[next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==fn) for t in trees]
  if ast.dump(nodes[0])!=ast.dump(nodes[1]):raise RuntimeError('Protected function drift '+fn)
  checks.append({'protected_function':fn,'AST_equal':True})
oldspec=json.loads((OLD/'spec.json').read_bytes())
if spec['roster']!=oldspec['roster'] or spec['caps']!=oldspec['caps'] or len(spec['roster'])!=49:raise RuntimeError('Business/caps drift')
after=[pin(Path(p)) for p in inputs]
if after!=list(inputs.values()):raise RuntimeError('Input drift')
doc('inputs.before.json',list(inputs.values()));doc('inputs.after.json',after)
doc('static-audit.json',{'checks':checks,'inputs':len(inputs),'input_drift':[],'case_rows':49,'expected_only_events':89,'execution':{'candidate_imports':0,'helper_DLL':0,'Go':0,'SQL':0,'HTTP':0,'SDK':0,'tests':0},'new_failures':[],'original_os206':inputs[str(REVIEW/'failure-origins.json')],'native_exit_of_metadata_tool':None})
print(json.dumps({'output':str(OUT),'static_checks':len(checks),'changed_sources':[n for n in names if candidates[n]!=originals[n]],'spec_ref':spec_ref},ensure_ascii=False))
