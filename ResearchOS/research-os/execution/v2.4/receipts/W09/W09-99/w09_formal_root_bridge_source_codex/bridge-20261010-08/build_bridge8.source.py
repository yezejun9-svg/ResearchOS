from pathlib import Path
import ast, copy, datetime, difflib, hashlib, json, ntpath, re, types, uuid

R=Path(r'D:/作品集/ResearchOS/research-os')
W=R/'execution/v2.4/receipts/W09/W09-99'
D=Path(__file__).resolve().parent
BASE=W/'w09_formal_root_bridge_source_codex/bridge-20261010-07'
DIAG=W/'w09_br7_activation_resource_boundary_diagnosis_codex/diagnose-20261010-01'
HELPER=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s=types.ModuleType('receipt_support');s.__file__=str(HELPER)
exec(compile(HELPER.read_bytes(),str(HELPER),'exec'),s.__dict__);s.D=D
expected={
    BASE/'HDF.json':('1da577805839fb3f96f20bb5282020d7f909e466278aa1df3713f758d977d06c',13966),
    BASE/'MF.json':('8a61ed6cd3d846201fa832e305cb0d002690605c3ca80c867d113ba6283cefd3',6388),
    BASE/'w09_root_bridge.source.py':('16b9f425efcbe2f7f9155cd7be54c3fe4faf10e327a2800ce6edb89d13fa1668',54832),
    DIAG/'HDF.json':('aff7da148dde74c82b4ebeb9aef14b808691a95bf42b1dacc9524d4595e6ce45',4393),
    DIAG/'MF.json':('d3fb1163b3bdb5ca7f33f56e2fcd2c54a1c61ff7060989335f09b5818cb6d7a4',5520),
    DIAG/'decision.json':('ae5283a8495d6528bde6148f086b8a023cc6a3f98e277c05c118c121825da25a',6870),
    DIAG/'diagnosis-facts.v2.json':('1fa070348ac8ffc774e54eb7f10f406743a71d630de60d21d6a851fcdc46cbf1',33800),
    R/'execution/v2.4/formal_case_index.py':('e08a7f605ca12d79c672b6af0360a02b26e2231d2a602207d0ea6a37f24f7b0b',71844)}
base=json.loads((BASE/'HDF.json').read_bytes())
diagnosis=json.loads((DIAG/'decision.json').read_bytes())
refs=[s.pin(p) for p in expected]
refs += [s.pin(__file__),s.pin(HELPER),s.GREF,base['source_ref'],base['consumer_launcher_ref'],
    base['contract_ref'],base['root_calling_contract_ref'],base['source_inputs_ref'],
    base['retained_successful_prefix_ref'],base['delta_controls_ref'],
    *diagnosis['actual_guard_refs'],diagnosis['proposal_ref'],diagnosis['original_diagnostic_failure_ref']]
refs=list({str(Path(v['path']).resolve(strict=True)):s.pin(v['path']) for v in refs}.values())
g=s.guard();checks=[];failure=None;created=None
def check(name,value,detail=None):
    checks.append(dict(name=name,passed=bool(value),detail=detail))
    if not value:raise ValueError(name)
def identity(path):
    value=str(path)
    if not ntpath.isabs(value):value=ntpath.join(str(R),value)
    return ntpath.normcase(ntpath.normpath(value))
def body_map(tree):
    return {node.name:ast.dump(node,include_attributes=False) for node in tree.body
        if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
def rejects(call,code=None):
    try:call()
    except (ValueError,TypeError,KeyError) as exc:return code is None or str(exc)==code
    return False
try:
    g.acquire(refs)
    for path,(digest,size) in expected.items():
        raw=g.get_buffer(str(path))
        assert hashlib.sha256(raw).hexdigest()==digest and len(raw)==size
    before=g.get_buffer(base['source_ref']['path'])
    launcher=g.get_buffer(base['consumer_launcher_ref']['path'])
    base_contract=json.loads(g.get_buffer(base['root_calling_contract_ref']['path']))
    proposal=json.loads(g.get_buffer(str(Path(diagnosis['proposal_ref']['path']))))
    original_ranges=proposal['dependency_snapshot']['audit_ranges']
    check('exact_published_BR7_and_independent_diagnosis_inputs',
        diagnosis['original_root_failure']['ordinal']==1224
        and diagnosis['first_rejected_reference']['json_pointer']=='/dependency_snapshot/audit_ranges/0'
        and len(original_ranges)==diagnosis['actual_total_audit_ranges']
        and all(json.loads(g.get_buffer(str(Path(v['path']))))['closed'] is True
            for v in diagnosis['actual_guard_refs']),
        dict(actual_observed_range_count=len(original_ranges),count_is_not_a_runtime_gate=True,
            ordinary_Source_only=True,Root_stage_executed=False))
    old_tree=ast.parse(before)
    old_node=next(x for x in old_tree.body if isinstance(x,ast.FunctionDef) and x.name=='historical_dependency_refs')
    text=before.decode('utf-8');lines=text.splitlines(keepends=True)
    old_func=''.join(lines[old_node.lineno-1:old_node.end_lineno])
    new_func='''def historical_dependency_refs(value, ref, req, name):
    """Archive-covered current4 and typed audit ranges retain their dedicated checks."""
    cleaned = copy.deepcopy(value)
    archives = []
    if name == "proposal_ref":
        archives = proposal_archive_refs(value, ref, req)
        del cleaned["current4"]
        del cleaned["historical_current4"]
    if "dependency_snapshot" in cleaned:
        data = validate_persistent_snapshot(cleaned["dependency_snapshot"])
        if "audit_ranges" in data:
            ranges = data["audit_ranges"]
            need(type(ranges) is list, "HISTORICAL_AUDIT_RANGES_REQUIRED")
            for item in ranges:
                need(type(item) is dict and set(item) == {"path", "offset", "bytes", "sha256"}
                     and type(item["path"]) is str and Path(item["path"]).is_absolute()
                     and type(item["offset"]) is int and item["offset"] >= 0
                     and type(item["bytes"]) is int and item["bytes"] > 0
                     and type(item["sha256"]) is str
                     and re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) is not None,
                     "HISTORICAL_AUDIT_RANGE_SHAPE")
                need(canonical_identity(item["path"]) not in CANON,
                     "UNDECLARED_HISTORICAL_CANONICAL_REFERENCE")
            del data["audit_ranges"]
    refs = list(references(cleaned))
    need(not any(canonical_identity(item["path"]) in CANON for item in refs),
         "UNDECLARED_HISTORICAL_CANONICAL_REFERENCE")
    return refs + archives
'''
    newline='\r\n' if '\r\n' in old_func else '\n'
    new_func=new_func.replace('\n',newline)
    old_gen=b'BRIDGE_GENERATION = "bridge-20261010-07"'
    new_gen=b'BRIDGE_GENERATION = "bridge-20261010-08"'
    assert before.count(old_func.encode())==1 and before.count(old_gen)==1
    after=before.replace(old_func.encode(),new_func.encode()).replace(old_gen,new_gen)
    restored=after.replace(new_func.encode(),old_func.encode()).replace(new_gen,old_gen)
    new_tree=ast.parse(after)
    old_map=body_map(old_tree);new_map=body_map(new_tree)
    changed=[name for name in old_map if old_map[name]!=new_map[name]]
    check('one_business_helper_generation_only_complete_byte_inverse',
        restored==before and changed==['historical_dependency_refs']
        and hashlib.sha256(launcher).hexdigest()=='c64deb904e746fd2d5df6775e0b96375ce36741315109d47ab86408360de5011'
        and len(launcher)==1493,
        dict(changed_functions=changed,launcher_unchanged=True,all_other_function_class_AST_unchanged=True))
    chosen=[x for x in new_tree.body if isinstance(x,ast.FunctionDef)
        and x.name in ('need','references','validate_persistent_snapshot','historical_dependency_refs')]
    env=dict(copy=copy,re=re,Path=Path,CANON=[identity(R/'execution/v2.4'/f'{name}.json')
        for name in ('checkpoint','path_ownership','step_state','commands')],
        canonical_identity=identity,proposal_archive_refs=lambda value,ref,req:copy.deepcopy(value['historical_current4']['archive_refs']))
    exec(compile(ast.Module(body=chosen,type_ignores=[]),'<Source-only-helper-controls>','exec'),env)
    run=env['historical_dependency_refs']
    original=copy.deepcopy(proposal)
    got=run(proposal,diagnosis['proposal_ref'],{},'proposal_ref')
    literal_paths={x['path'] for x in original_ranges}
    check('actual_twelve_mixed_spelling_ranges_clone_only_no_whole_file_promotion',
        proposal==original and len(literal_paths)==2
        and len({identity(x['path']) for x in original_ranges})==1
        and not any(identity(x['path'])==identity(original_ranges[0]['path']) for x in got)
        and all(x in got for x in proposal['historical_current4']['archive_refs']),
        dict(actual_total=len(original_ranges),literal_spellings=sorted(literal_paths),
            original_snapshot_and_range_objects_unchanged=True,archive_proof_function_unmodified=True))
    ordinary={'path':str(Path(r'C:/Windows/System32/kernel32.dll')),'sha256':'a'*64,'bytes':3}
    fixture={'dependency_snapshot':{'files':{},'audit_ranges':copy.deepcopy(original_ranges)},'ordinary':ordinary}
    observed=run(fixture,{}, {},'publication_ref')
    check('ordinary_foreign_whole_file_ref_remains_for_unchanged_physical_gate',
        ordinary in observed and old_map['physical']==new_map['physical']
        and old_map['checked']==new_map['checked'] and old_map['references']==new_map['references'],
        dict(general_C_exception_added=False,RESOURCE_OWNER_change=False))
    misplaced={'extra':{'audit_ranges':copy.deepcopy(original_ranges)},'dependency_snapshot':{'files':{}}}
    misplaced_refs=run(misplaced,{}, {},'role_registry_input_ref')
    pseudo=[{'dependency_snapshot':{'audit_ranges':[]}}, {'dependency_snapshot':{'files':[],'audit_ranges':[]}},
        {'dependency_snapshot':'audit_ranges'}]
    check('pseudo_snapshot_rejected_misplaced_typed_branch_never_skipped',
        all(rejects(lambda v=v:run(v,{}, {},'publication_ref')) for v in pseudo)
        and any(identity(x['path'])==identity(original_ranges[0]['path']) for x in misplaced_refs))
    template=copy.deepcopy(original_ranges[0]);bad=[]
    for key,value in [('offset',True),('offset',-1),('offset','0'),('bytes',True),('bytes',0),('bytes',-1),
                      ('sha256','a'*63),('sha256','G'*64),('sha256',None),('path','relative/audit.jsonl'),('path',None)]:
        item=copy.deepcopy(template);item[key]=value;bad.append(item)
    item=copy.deepcopy(template);del item['offset'];bad.append(item)
    item=copy.deepcopy(template);item['whole_file']=True;bad.append(item)
    def bad_range(item):return {'dependency_snapshot':{'files':{},'audit_ranges':[item]}}
    check('strict_range_shape_bool_integer_missing_extra_bad_digest_path_refusals',
        all(rejects(lambda item=item:run(bad_range(item),{}, {},'publication_ref'),'HISTORICAL_AUDIT_RANGE_SHAPE') for item in bad)
        and rejects(lambda:run({'dependency_snapshot':{'files':{},'audit_ranges':False}}, {},{},'publication_ref'),
            'HISTORICAL_AUDIT_RANGES_REQUIRED'),dict(new_counterexamples=len(bad)+1))
    canon_range_bad=[]
    for name in ('checkpoint','path_ownership','step_state','commands'):
        for spelling in [str(R/'execution/v2.4'/f'{name}.json'),
                         str(R/'execution/v2.4/../v2.4'/f'{name}.json').replace('\\','/'),
                         str(R/'execution/v2.4'/f'{name}.json').upper()]:
            item=copy.deepcopy(template);item['path']=spelling;canon_range_bad.append(item)
    check('all_four_Canon_direct_case_separator_and_traversal_range_aliases_refused',
        all(rejects(lambda item=item:run(bad_range(item),{}, {},'publication_ref'),
            'UNDECLARED_HISTORICAL_CANONICAL_REFERENCE') for item in canon_range_bad),
        dict(new_counterexamples=len(canon_range_bad),fixture_identity='ntpath normcase/normpath Source-only mock',
            production_canonical_identity_AST_unchanged=True))
    api_tree=ast.parse(g.get_buffer(str(R/'execution/v2.4/formal_case_index.py')))
    api_map=body_map(api_tree)
    check('dedicated_range_rechecks_fresh_authority_TP_and_all_route_identity_gates_unmodified',
        all(old_map[name]==new_map[name] for name in old_map if name!='historical_dependency_refs')
        and '_audit_range' in api_map and 'recheck_inputs' in api_map
        and 'proposal["dependency_snapshot"]' in ast.get_source_segment(text,next(x for x in old_tree.body if isinstance(x,ast.FunctionDef) and x.name=='registration')),
        dict(existing_dedicated_Main_input_ref=s.pin(R/'execution/v2.4/formal_case_index.py'),
            snapshot_registration_publish_Main_unchanged=True,Source21_Native_Mode_changes=False,
            mutable_authority_current4_and_TP_CAS_unchanged=True))
    for path,raw in [(D/'w09_root_bridge.source.py',after),(D/'consumer_launch.source.py',launcher)]:
        with path.open('xb') as f:f.write(raw)
    patch=''.join(difflib.unified_diff(text.splitlines(keepends=True),after.decode().splitlines(keepends=True),
        fromfile=str(BASE/'w09_root_bridge.source.py'),tofile=str(D/'w09_root_bridge.source.py')))
    with (D/'bridge08.patch').open('xb') as f:f.write(patch.encode())
    created=dict(source_ref=s.pin(D/'w09_root_bridge.source.py'),consumer_launcher_ref=s.pin(D/'consumer_launch.source.py'))
    s.write('exact-inverse.json',dict(base_source_ref=base['source_ref'],new_source_ref=created['source_ref'],
        inverse_sha256=hashlib.sha256(restored).hexdigest(),complete_byte_inverse=True,
        changed_business_functions=changed,changed_bindings=['BRIDGE_GENERATION'],
        other_functions_classes_AST_unchanged=True,consumer_launcher_unchanged=True,
        general_references_physical_checked_Main_TP_unchanged=True,Source_only=True))
except BaseException as exc:
    failure=dict(type=type(exc).__name__,message=str(exc));raise
finally:
    guard_ref=s.write('source-guard.closed.json',g.close())
    controls_ref=s.write('delta-controls.json',dict(checks=checks,count=len(checks),passed=sum(x['passed'] for x in checks),
        failure=failure,source_guard_ref=guard_ref,held_count=len(refs),created=created,
        old_successful_controls_replayed=False,Source_only=True,self_acceptance=False,
        execution_grant=False,formal_acceptance=False,actual_product_calls=0))

created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')
revision=uuid.uuid4().hex
notes='''# Bridge08 Root calling contract

Actual Source author: codex:/root/full_w09_source_review, backend /root/full_w09_source_review; formal verifier /root/backup_regression_resources. SOURCE_PREPARED only; a new nonauthor Source review and actual Root issuance remain required.

Only historical_dependency_refs changes: validate the typed dependency_snapshot.audit_ranges branch, retain normalized refusal of all four Canon identities including aliases, and omit that branch solely from a deepcopy used to enumerate whole-file dependencies. Exact original snapshot, offsets, paths, lengths and range digests remain immutable. Current Root evidence has twelve ranges with both Windows slash spellings; the implementation imposes no range-count gate or raw spelling equality. Original1224 is retained: a range header digest was promoted to a whole-file ref; RESOURCE_OWNER was not the first rejected item.

The original Main _audit_range/recheck_inputs and registration/publication pre-TP snapshot rechecks remain unchanged and mandatory. No physical()/checked()/general references() C-drive exception is introduced. Ordinary foreign whole-file refs or misplaced typed-looking data still pass to the unchanged rejecting repo path gate; malformed typed ranges or historical Canon references are refused. The four archive proof, exact proposal identity, fresh request current4, Root owner/worker/finite lease, Source peer offsets, six routes, five roles, Mode/Native inputs, TEMP and exclusive TP CAS gates remain unchanged.

Generation bridge-20261010-08 and Source selfrefs are new. Main profile TRUSTED stays actual 1e04865beef37fdbffa06d649d072721d7b6eb0ef5e525d87bb867da414e4087/71403. Sealed launcher bytes remain identical. Root must not relabel an old Scope/proposal as BR8 authority. This preparation does not execute Root stages, Native, Go, SQL, dispatcher, TP or model, and does not write Main/Canon/Scope/Registry. Existing Source controls, Main47, four NF6 Native reports and six Mode decisions are retained without replay; their current acceptance remains subject to the unchanged Main gates.
'''
with (D/'ROOT_CALL_CONTRACT.md').open('xb') as f:f.write(notes.encode())
contract=copy.deepcopy(base_contract)
contract.update(generation='bridge-20261010-08',source_revision_uuid=revision,
    source_ref=created['source_ref'],consumer_launcher_ref=created['consumer_launcher_ref'],
    contract_ref=s.pin(D/'ROOT_CALL_CONTRACT.md'),base_hdf_ref=s.pin(BASE/'HDF.json'),
    base_mf_ref=s.pin(BASE/'MF.json'),base_source_ref=base['source_ref'])
contract['CLI_prefix'][-1]=created['source_ref']['path']
contract['business_delta_from_BR7']='historical_dependency_refs typed audit-range clone isolation plus generation only; all other function/class AST unchanged.'
contract['BR8_audit_range_boundary']={
    'typed_branch':'dependency_snapshot.audit_ranges','exact_keys':['path','offset','bytes','sha256'],
    'cloned_scan_only':True,'original_snapshot_ranges_unchanged':True,'range_count_fixed':False,
    'Canon_identity_and_alias_refusal_preserved':True,'slash_spellings_preserved':True,
    'dedicated_Main_range_recheck_unchanged':True,'general_foreign_path_exception':False,
    'malformed_typed_range':'REJECTED','ordinary_or_misplaced_foreign_ref':'UNCHANGED_REPO_PATH_GATE'}
contract['independent_BR7_boundary_diagnosis_ref']=s.pin(DIAG/'decision.json')
contract['original1224']='FAILED_RETAINED_TYPED_RANGE_PROMOTED_TO_WHOLE_FILE_REFERENCE'
calling_ref=s.write('root-calling-contract.source.json',contract)
inputs_ref=s.write('source-inputs.json',dict(schema='researchos.w09-bridge08-source-inputs.v1',
    base_hdf_ref=s.pin(BASE/'HDF.json'),base_mf_ref=s.pin(BASE/'MF.json'),base_source_ref=base['source_ref'],
    base_source_inputs_ref=base['source_inputs_ref'],protected_Base_member_refs=json.loads((BASE/'MF.json').read_bytes())['members'],
    diagnosis_hdf_ref=s.pin(DIAG/'HDF.json'),diagnosis_mf_ref=s.pin(DIAG/'MF.json'),
    diagnosis_decision_ref=s.pin(DIAG/'decision.json'),diagnosis_facts_ref=s.pin(DIAG/'diagnosis-facts.v2.json'),
    diagnosed_actual_proposal_ref=diagnosis['proposal_ref'],current_source_ref=created['source_ref'],
    current_consumer_launcher_ref=created['consumer_launcher_ref'],Main_required_ref=base['Main_required_ref'],
    Main_adoption_closed_ref=base['Main_root_adoption_closed_ref'],Main_independent_review_ref=base['Main_independent_accepted_review_ref'],
    retained_original_author_contribution=base['base_source_contribution'],original1224=diagnosis['original_root_failure'],
    original1225_origin_ref=diagnosis['original_diagnostic_failure_ref'],historical_original1218_io=base['original1218_io'],
    retained_BR7_controls_refs=[base['retained_successful_prefix_ref'],base['delta_controls_ref']],
    old_successful_controls_replayed=False,current_CP_OW_SS_not_read=True,live_audit_log_not_held=True,
    future_Root_grant=None,execution_grant=False,formal_acceptance=False))
s.write('preparation-metadata.json',dict(created_utc=created_utc,source_revision_uuid=revision,generation='bridge-20261010-08',
    source_ref=created['source_ref'],consumer_launcher_ref=created['consumer_launcher_ref'],
    contract_ref=s.pin(D/'ROOT_CALL_CONTRACT.md'),root_calling_contract_ref=calling_ref,source_inputs_ref=inputs_ref,
    delta_controls_ref=controls_ref,source_guard_ref=guard_ref,base_hdf_ref=s.pin(BASE/'HDF.json'),
    base_mf_ref=s.pin(BASE/'MF.json'),base_source_ref=base['source_ref'],
    independent_boundary_diagnosis_ref=s.pin(DIAG/'decision.json'),
    diagnosis_hdf_ref=s.pin(DIAG/'HDF.json'),diagnosis_mf_ref=s.pin(DIAG/'MF.json'),
    diagnosis_facts_ref=s.pin(DIAG/'diagnosis-facts.v2.json'),Main_required_ref=base['Main_required_ref'],
    retained_original_author_contribution=base['base_source_contribution'],original1224=diagnosis['original_root_failure'],
    original1225_origin_ref=diagnosis['original_diagnostic_failure_ref'],historical_original1218_io=base['original1218_io'],
    independent_source_review_required=True,Source_author_self_acceptance=False))
print(json.dumps(dict(status='SOURCE_PREPARED_UNSEALED',checks=len(checks),passed=sum(x['passed'] for x in checks),
    source_ref=created['source_ref'],consumer_launcher_ref=created['consumer_launcher_ref'],
    root_calling_contract_ref=calling_ref,source_guard_ref=guard_ref,products=0,
    execution_grant=False,formal_acceptance=False),ensure_ascii=False))
