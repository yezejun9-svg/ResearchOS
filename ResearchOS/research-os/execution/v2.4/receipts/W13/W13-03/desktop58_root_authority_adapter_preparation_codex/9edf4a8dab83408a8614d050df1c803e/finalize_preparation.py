import ast,hashlib,json,difflib
from pathlib import Path
OUT=Path(__file__).parent
ROOT=Path('D:/作品集/ResearchOS/research-os')
P13=ROOT/'execution/v2.4/receipts/W13/W13-03'
def pin(p):
    p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,v):
    with (OUT/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def put(n,b):
    with (OUT/n).open('xb') as f:f.write(b)
old=(OUT/'authorization_adapter.proposed.py').read_bytes()
needle=b"    same_ref(reader, scope['Root_forward_head_seal_ref'], authority['forward_head_manifest_ref'])\n"
addition=b'''    forward_review = reader.doc(scope['Root_forward_head_review_ref'])
    require(scope['Root_forward_head_review_ref']['sha256'] == 'f14dcdf6cfa2676db6022e7a852abd38e2095bc45a0529566b10997001a03624' and
            scope['Root_forward_head_review_ref']['bytes'] == 7591 and
            forward_review['schema'] == 'researchos.desktop58-source-head-registration-closed-review.v1' and
            forward_review['reviewer'] == 'codex:/root/w05_merge_review' and
            forward_review['decision'] == 'SOURCE_HEAD_REGISTRATION_EVIDENCE_CLOSED' and
            forward_review['requested_changes'] == [] and forward_review['actual_registration_evidence_closed'] is True and
            forward_review['actual_head'] == SOURCE and forward_review['actual_parent'] == PARENT and
            forward_review['source_acceptance'] is False and forward_review['formal_increment'] == 0,
            'Historical source-head forward independent closure missing')
    same_ref(reader, forward_review['post_registration_audit_ref'], authority['forward_head_audit_ref'])
    same_ref(reader, forward_review['registration_manifest_ref'], authority['forward_head_manifest_ref'])
'''
assert old.count(needle)==1
new=old.replace(needle,needle+addition,1)
assert new.replace(needle+addition,needle,1)==old
ast.parse(new)
put('authorization_adapter.final.proposed.py',new)
save('final-addition.inverse.json',{'baseline_ref':pin(OUT/'authorization_adapter.proposed.py'),'candidate_ref':pin(OUT/'authorization_adapter.final.proposed.py'),'old':needle.decode(),'new':(needle+addition).decode(),'whole_inverse':True})
base=json.loads((OUT/'whole-inverse.json').read_bytes())
save('whole-inverse.final.json',{'baseline_ref':base['baseline_ref'],'candidate_ref':pin(OUT/'authorization_adapter.final.proposed.py'),'old':base['old'],'new':new.decode(),'reused_definitions':['require','strict_json','bounded_path','Reader','registration_refs','validate_current58_source']})
scope=json.loads((OUT/'scope.proposed.json').read_bytes())
scope['authorization_verifier_ref']=pin(OUT/'authorization_adapter.final.proposed.py')
scope['Root_forward_head_review_ref']=None
save('scope.final.proposed.json',scope)
fr=P13/'desktop58_forward_registration_evidence_independent_review_codex/b3d1bdad7b514ee592faa041db1576f3/review.json'
assert pin(fr)['sha256']=='f14dcdf6cfa2676db6022e7a852abd38e2095bc45a0529566b10997001a03624'
inputs=json.loads((OUT/'inputs.before.json').read_bytes())+[pin(fr)]
save('inputs.final.before.json',inputs)
assert inputs==[pin(x['path']) for x in inputs]
save('inputs.final.after.json',[pin(x['path']) for x in inputs])
names={n.name:n for n in ast.parse(new).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
base_source=base['old'];bl=base_source.splitlines(True);nl=new.decode().splitlines(True)
unchanged=[]
for n in ast.parse(base_source).body:
    if getattr(n,'name',None) in ['require','strict_json','bounded_path','Reader','registration_refs','validate_current58_source']:
        other=names[n.name]
        assert ''.join(bl[n.lineno-1:n.end_lineno])==''.join(nl[other.lineno-1:other.end_lineno])
        assert ast.dump(n,include_attributes=False)==ast.dump(other,include_attributes=False)
        unchanged.append(n.name)
save('static.final.json',{'AST_parsed':True,'candidate_imported':False,'candidate_executed':False,'unchanged_whole_definitions':unchanged,
    'original_controller_and_launcher_changed':False,'input_count':len(inputs),'input_drift':0,
    'future_controls':'NOT_RUN','source_acceptance':False,'native_product_Go_SQL_Node_DLL_HTTP_SDK_model_calls':0})
save('contract.json',{
 'schema':'researchos.desktop58-authority-adapter-source-contract.v1','state':'SOURCE_PREPARATION_ONLY','author':'codex:/root/command_queue_impl',
 'interface':'validate_grant(scope_path, scope_sha256, grant_path, grant_sha256) -> scope, source_commit, fresh_current58_CLI2_qualified, original_CLI2_case_count, registered_Root_scope_and_grant_verified, authorization_input_refs (all ABS)',
 'existing_consumers':{'controller_ref':scope['controller_ref'],'launcher_ref':scope['launcher_ref'],'byte_changes':0},
 'source_predicate':{'original_ref':base['baseline_ref'],'definition':'validate_current58_source','whole_bytes_unchanged':True},
 'registration_contract_status':'PROPOSED naming only; Root must implement/freeze matching actual metadata and independent review. This adapter never writes registrations or grants.',
 'proposed_CP_WIP_keys':['desktop58_finite_validation_scope_ref','desktop58_finite_validation_controller_review_ref','desktop58_finite_validation_current_source_authority_ref','desktop58_finite_validation_CLI2_qualification_ref','desktop58_finite_validation_state'],
 'proposed_OW_lease_path':'card_path_bindings.W13-03.subtasks.desktop58_finite_validation',
 'lease_required':{'owner':'codex:/root','current_source_writer':None,'state':'REGISTERED_PENDING_ONCE_EXECUTION','scope_ref':'actual full scope ref','run_uuid':'same run UUID','source_commit':scope['source_commit']},
 'controller_review':{'schema':'researchos.desktop58-controller-static-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'READY_FOR_ROOT_CURRENT58_DESKTOP169_GO3_ONCE','requested_changes':[],'pins':['controller_sha256','launcher_sha256','gate_sha256','scope_sha256'],'lookup':'actual sealed CP WIP ref; scope stores only predetermined controller_review_path to avoid scope/review SHA cycle'},
 'registration_review':{'schema':'researchos.root-registration-source-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION','actual_registration_executed':False},
 'registration_layout':'Original 6ff actual manifest/audit/invocation/intent/verified plus register.py/run.py/prepared_refs.json/audit.json/stdout.raw/stderr.raw and per-canonical done files. Root explicit 2 or 4 metadata intent; original failure prefix and unchanged ST/CM verified. No live canon freeze during long execution.',
 'grant_contract':{'schema':'researchos.desktop58-finite-authorization.v1','status':'ROOT_REGISTERED_EXECUTION_AUTHORIZED','actual_registration_completed':True,'binding':'ENTIRE exact scope dict','scope_ref':'ROOT-relative canonical ref','location':'new_authorization_root/authorization.execute.json','canonical_copies':'four ordered {canonical_path,ref}, each inside grant root; raw equal actual sealed desired/unchanged facts','registration_refs':'actual five sealed registration refs','authority_review_refs':'return from adapted validate_authority plus CLI2_qualification_ref/CLI2_review_ref/CLI2_manifest_ref','prelaunch_evidence_ref':'inside grant root, original pinned toolchain + complete owned head/status/index proofs','runtime_observation_refs':'inside grant root; all_observed_inputs_pre_pinned true and every actual file pre-pinned; point-in-time only','fresh_roots_observed_absent':'ordered output_root/outer_output_root/export_root names; statement alone is NOT proof of absence; launcher+controller perform actual exclusive allocation','automatic_retry':False,'counter_reset':False},
 'CLI_prerequisite':{'qualification_ref':None,'review_ref':None,'manifest_ref':None,'wire_schema':'Known r331 cli43 wire is supported ONLY with source_commit=e2 and actual same-head current639 catalog; new schema must get separate explicit adaptation','native_calls':14,'cases':['real-existing-open-readonly','real-existing-self-send'],'CLI_exits':[0,3],'no_old_a510_inheritance':True,'review_is_bounded_evidence_authority':'The adapter hashes/pairs sealed actual artifacts and trusts exact nonauthor closed adjudication for full fixture/compiled/OS semantics; it does not rerun tests or invent tool event authentication.'},
 'resources':'Root supplies resource_catalog with files/tools/images/GOMODCACHE/web_modules/complete_public_roots_frozen + exact runtime_resources_ref and compiler_resources_ref; both documents have nonempty files exact subsets. This is an explicit proposed normalization contract; original resource payload shape must not be guessed. Actual generated Go graph/WORK/archives are added and verified by existing controller after build; not known in preparation.',
 'source_catalog':{'commit':scope['source_commit'],'file_count':639,'all_platform_Go_count':559,'actual_ref':None},
 'fresh_roots':'Root supplies unique run UUID and exact disjoint roots. Both gate calls require inner output/export absent; outer root may already exist on the inner call because launcher exclusively creates it. Grant is immutable; live canon may later progress.',
 'alias_contract':'Exact original20 cases/ordinals/modes/path/max_creates Root-declared before launch, 15 executable aliases, unreaped exact path may create <=2. No prebuilt aliases, no wildcard or same-hash path authorization. Fresh negative binary pins are derived by existing controller before first case and tied to predeclared paths.',
 'budgets':{'Root_actual_values':None,'required':['inner_seconds','outer_seconds','builder_seconds','controller_evidence_reserve_seconds','launcher_evidence_reserve_seconds'],'no_allocation_here':True,'helper_finalization':25,'cleanup':5,'outer_relation':'outer > inner+25+5+launcherEvidenceReserve','inner_relation':'stage <= remaining-25-5-controllerEvidenceReserve'},
 'known_limits':{k:scope[k] for k in ['node_cases','Go_top_cases','native_top_command_cap','loopback_HTTP_max','offscreen_Electron_controls','installed_visible_GUI_calls','SDK_model_external_paid_calls','process_cap','active_job_processes','image_cap','cleanup_seconds']},
 'OPEN':['Actual same-head fresh current58 CLI2 qualification/review/manifest do not exist in this preparation; old r331 is a schema witness only.','Actual current639 catalog/resource union and missing DLL inputs must be completed and independently frozen by Root.','Root Desktop scope, numerical allocation, actual CP/OW lease/registration review/CAS seal and grant producer are NOT implemented or executed here.','Proposed registration WIP/lease names and Desktop review schema need Root adoption and nonauthor review; changing actual producer schema requires explicit reconciliation.','Pure read/hash preflight does not prove OS lifecycle or prevent all concurrent mutations; exclusive once launcher and owned outer bound plus repeated runtime vectors remain required.','All 169 Node + independent Go3 + two hidden/offscreen renderer controls are NOT_RUN; installed visible GUI/SDK/model remain0.'],
 'acceptance':False,'formal_increment':0,'candidate_or_native_execution':0})
save('future-controls.NOT_RUN.json',{'status':'NOT_RUN','cases':[
 'reject preparation scope or any required NULL ref/tuple/budget','reject old a510 qualification even with 14 passes','reject e2 qualifier from different catalogue/run or unsealed case fact',
 'reject wrong nonauthor reviewer/fullscopeSHA/code pin or review path','reject missing actual registration or changed failure prefix/STCM','reject unordered copies or copies differing from sealed desired',
 'reject current58 source substitution outside exact38+8+15 union','reject future tuple including failure-count component','reject absent compiler/runtime member or unpinned tool/image',
 'reject nonexact169/Go3 roster, alias wildcard/path/max_creates changes','reject overlapping/existing export or inner roots','allow inner validation after outer exclusive root exists, with same immutable grant',
 'reject insufficient Root IO/finalization reserve','reject missing owned Git result/cleanup or status/index mismatch','reject fabricated runtime observation member','same actual schema/current58 closed chain plus actual Root grants is a future positive, not run here']})
print(json.dumps({'adapter':pin(OUT/'authorization_adapter.final.proposed.py'),'scope':pin(OUT/'scope.final.proposed.json'),'contract':pin(OUT/'contract.json'),'inputs':len(inputs)},ensure_ascii=False))
