from pathlib import Path
import ast,copy,hashlib,json,types
O=Path(__file__).resolve().parent;R=O.parents[6];W=R/'execution/v2.4/receipts/W09/W09-99'
B=W/'w09_formal_root_bridge_source_codex/bridge-20261010-07'
S=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
Q=W/'full_w09_nf6_actual_independent_review_codex/review-actual-nf6-20261010-01'
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def ref(p,size=True):
 x=pin(p);x['path']=Path(p).relative_to(R).as_posix()
 if not size:del x['bytes']
 return x
def doc(p):return json.loads(Path(p).read_bytes())
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(O/n)
def literals(p,names):
 return {n.targets[0].id:ast.literal_eval(n.value) for n in ast.parse(Path(p).read_bytes()).body
  if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in names}
profile=R/'execution/v2.4/formal_profile_w09.py';api=R/'execution/v2.4/formal_case_index.py'
assert pin(profile)['sha256']=='1e04865beef37fdbffa06d649d072721d7b6eb0ef5e525d87bb867da414e4087' and pin(profile)['bytes']==71403
bh=doc(B/'HDF.json');assert pin(B/'HDF.json')['sha256']=='1da577805839fb3f96f20bb5282020d7f909e466278aa1df3713f758d977d06c'
assert pin(B/'w09_root_bridge.source.py')==bh['source_ref']
assert pin(B/'w09_root_bridge.source.py')['sha256']=='16b9f425efcbe2f7f9155cd7be54c3fe4faf10e327a2800ce6edb89d13fa1668'
constants=literals(profile,{'SOURCE_PREFIX','ROOT_ORIGIN_PREFIX','ROOT_SOURCE_AUDIT_LOG','ROOT_THREAD_ID','ROOT_CAPTURE_PREFIX','ROLE_POLICY_SCHEMA','ROUTES'})
role_path=constants['ROOT_CAPTURE_PREFIX']+'execution-roles.json'
peerpaths={'SOURCE_AUTHOR':S/'w09.bridge07-source-author.actual-audit.root.json',
 'VERIFIER':S/'w09.br6-formal-review-preparation-and-six-mode-delivery.actual-audit.root.json'}
peers={k:doc(p) for k,p in peerpaths.items()}
modepaths=sorted((Q/'modes').glob('*.mode-decision.json'));assert len(modepaths)==6
files=[profile,api,B/'w09_root_bridge.source.py',B/'HDF.json',B/'MF.json',B/'root-calling-contract.source.json',B/'ROOT_CALL_CONTRACT.md',
 *peerpaths.values(),*[Path(v['original_capture_ref']['path']) for v in peers.values()],*modepaths]
guardpath=R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
assert pin(guardpath)['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
files.append(guardpath);pins=[pin(p) for p in files]
g=types.ModuleType('role_input_guard');g.__file__=str(guardpath);exec(compile(guardpath.read_bytes(),str(guardpath),'exec'),g.__dict__)
guard=g.SourceReadGuard();closed=None
try:
 guard.acquire(pins)
 modes=[doc(p) for p in modepaths]
 assert {tuple([m['route'][0],m['route'][2],m['route'][3]]) for m in modes}==set(constants['ROUTES'])
 assert all(m['producer_id']=='codex:/root' and m['reviewer_id']=='/root/backup_regression_resources' and m['schema']=='researchos.w09-mode-decision.v2' and m['decision']=='QUALIFIED' for m in modes)
 mode01=ref(modepaths[0]);assert mode01['sha256']=='c7ca8206145c1c6bd0f85bcfbd878b398e5fdb4c45a9baa9817d0c8a046d614e'
 actors={'SOURCE_AUTHOR':'/root/full_w09_source_review','EXECUTOR':'codex:/root','EVIDENCE_ASSEMBLER':'codex:/root','VERIFIER':'/root/backup_regression_resources','ROOT_OBSERVER':'codex:/root'}
 kinds={'SOURCE_AUTHOR':('ROOT_SCOPE_REGISTRATION','/source_actor'),'EXECUTOR':('ACTUAL_MODE_DECISION','/producer_id'),
  'EVIDENCE_ASSEMBLER':('ROOT_OWNER_REGISTRATION','/selected_worker_id'),'VERIFIER':('ACTUAL_MODE_DECISION','/reviewer_id'),'ROOT_OBSERVER':('ROOT_SCOPE_REGISTRATION','/issued_by')}
 observed=[]
 for role,capture in peers.items():
  raw=Path(capture['original_capture_ref']['path']).read_bytes();assert len(raw)==capture['original_capture_ref']['bytes'] and hashlib.sha256(raw).hexdigest()==capture['original_capture_ref']['sha256']
  lines=raw.splitlines(keepends=True);assert len(lines)==3 and all(x.endswith(b'\n') for x in lines)
  header,call,result=[json.loads(x) for x in lines]
  assert header['payload']['id']==constants['ROOT_THREAD_ID'] and header['ordinal']==0
  assert call['type']=='inter_agent_communication_metadata' and result['payload']['type']=='agent_message'
  assert result['payload']['author']==actors[role] and result['payload']['recipient']=='/root' and result['metadata']['client_authored'] is False
  assert result['ordinal']==call['ordinal']+1 and call['timestamp']==result['timestamp']
  binding=pin(B/'HDF.json')['sha256'] if role=='SOURCE_AUTHOR' else mode01['sha256']
  assert binding in (lines[1]+lines[2]).decode()
  assert [hashlib.sha256(x).hexdigest() for x in lines]==capture['original_line_sha256']
  with Path(constants['ROOT_SOURCE_AUDIT_LOG']).open('rb') as f:
   for offset,line in zip(capture['source_line_offsets'],lines):
    assert offset+len(line)<=capture['source_prefix_size_observed'];f.seek(offset);assert f.readline()==line
  observed.append(dict(role=role,actual_actor=actors[role],capture_wrapper_ref=pin(peerpaths[role]),raw_ref=pin(capture['original_capture_ref']['path']),
   selected_allowed_binding=binding,actual_delivery_contains_binding=True,exact_original_ranges_verified=True,
   existing_wrapper_is_Main_role_audit=False,RootOriginPrefix_copy_created=False))
 null3=lambda:dict(path=None,sha256=None,bytes=None)
 proofs=[];audits={}
 for role,actor in actors.items():
  kind,pointer=kinds[role];rawref=dict(path=None,sha256=None,locator=dict(json_pointer=pointer))
  if kind=='ACTUAL_MODE_DECISION':rawref.update(path=mode01['path'],sha256=mode01['sha256'])
  proofs.append(dict(role=role,actor_id=actor,origin_kind=kind,raw_ref=rawref,actual_audit_ref=null3()))
  a=dict(schema='researchos.w09.actual-role-audit.v1',actor_id=actor,role=role,Root_thread_id=constants['ROOT_THREAD_ID'],
   source_audit_path=constants['ROOT_SOURCE_AUDIT_LOG'],source_line_offsets=None,original_line_sha256=None,
   source_prefix_size_observed=None,original_capture_ref=null3(),binding_sha256=None)
  if role in peers:
   old=peers[role]
   for key in ('source_line_offsets','original_line_sha256','source_prefix_size_observed'):a[key]=copy.deepcopy(old[key])
   a['original_capture_ref'].update(sha256=old['original_capture_ref']['sha256'],bytes=old['original_capture_ref']['bytes'])
   a['binding_sha256']=pin(B/'HDF.json')['sha256'] if role=='SOURCE_AUTHOR' else mode01['sha256']
  elif role=='EXECUTOR':a['binding_sha256']=mode01['sha256']
  audits[role]=a
 registry_input=dict(run_id=None,roles=dict(source_authors=[actors['SOURCE_AUTHOR']],executor=actors['EXECUTOR'],assembler=actors['EVIDENCE_ASSEMBLER'],verifier=actors['VERIFIER'],root_observer=actors['ROOT_OBSERVER']),
  provenance=proofs,route_execution_refs=[dict(command_key=r[0],check_id=r[1],case_id=r[2],scope_ref=null3(),owner_ref=null3()) for r in constants['ROUTES']])
 save('role-registry-input.template.json',registry_input)
 save('actual-role-audits.template.json',audits)
 save('context-role-policy.template.json',dict(role_policy=dict(schema=constants['ROLE_POLICY_SCHEMA'],registry_ref=dict(path=role_path,sha256=None,bytes=None)),
  version_vector=dict(input_files=[dict(path=role_path,sha256=None)])))
 save('role-stage-protection.template.json',dict(role_protection_refs=[copy.deepcopy(a['original_capture_ref']) for a in audits.values()]+[null3()]))
 save('known-role-evidence.json',dict(schema='researchos.w09-br7-role-input-known-evidence.v1',source_package=dict(hdf_ref=pin(B/'HDF.json'),mf_ref=pin(B/'MF.json'),source_ref=pin(B/'w09_root_bridge.source.py')),
  Main_ref=pin(profile),existing_peer_delivery_observations=observed,
  six_modes=[dict(route=[m['route'][0],m['route'][2],m['route'][3]],mode_ref=ref(p),producer_id=m['producer_id'],reviewer_id=m['reviewer_id'],
   origin_allowed_binding=[pin(p)['sha256'],m['report_sha256'],m['independent_review_ref']['sha256']]) for p,m in zip(modepaths,modes)],
  exact_role_schema_keys=list(audits['SOURCE_AUTHOR']),origin_allowed_binding_rule='raw_ref.sha256 plus origin source_hdf_ref/source_mf_ref/source_review_ref/scope_ref/independent_review_ref.sha256 and origin.report_sha256; selected hash must occur verbatim in actual call+result.',
  required_RootOriginPrefix=constants['ROOT_ORIGIN_PREFIX'],dynamic_scope_owner_grants_Root_observations_created=False,formal_acceptance=False))
 # Shape-only checks: these are templates, deliberately invalid until dynamic nulls are resolved.
 assert len(proofs)==5 and all(set(x)=={'role','actor_id','origin_kind','raw_ref','actual_audit_ref'} for x in proofs)
 assert len(registry_input['route_execution_refs'])==6 and all(set(x)=={'command_key','check_id','case_id','scope_ref','owner_ref'} for x in registry_input['route_execution_refs'])
 assert registry_input['run_id'] is None and all(x['scope_ref']==null3() and x['owner_ref']==null3() for x in registry_input['route_execution_refs'])
 assert all(audits[r]['source_line_offsets'] is None for r in ('EXECUTOR','EVIDENCE_ASSEMBLER','ROOT_OBSERVER'))
 save('input-pins.json',pins)
 assert all(pin(x['path'])==x for x in pins)
finally:
 closed=guard.close();save('SourceGuard.closed.json',closed)
assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
save('preparation-decision.json',dict(status='ROLE_INPUT_TEMPLATES_PREPARED_DYNAMIC_ROOT_FIELDS_NULL',Main_ref=pin(profile),BR7_source_ref=pin(B/'w09_root_bridge.source.py'),
 exact_pinned_contract_static_review=True,existing_peer_source_ranges_verified=True,template_shape_checks_pass=True,
 SourceGuard_closed=True,retained_handles_count=0,Main_modules_imported=False,Main_role_or_native_verification_run=False,
 Root_stages_Native_SQL_models_TP_calls=0,Main_Canon_Scope_Registry_writes=0,execution_grant=False,formal_acceptance=False,
 dynamic_inputs_not_ready_is_goal_block=False))
print(json.dumps(dict(status='PREPARED_UNSEALED',template_ref=pin(O/'role-registry-input.template.json'),decision_ref=pin(O/'preparation-decision.json'),SourceGuard_closed_zero=True),ensure_ascii=False))
