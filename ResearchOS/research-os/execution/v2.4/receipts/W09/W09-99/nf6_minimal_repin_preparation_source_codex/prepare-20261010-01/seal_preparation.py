"""Publish a conditional repin recipe; no NF6 Source or Root authority is issued."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,types

R=Path(r'D:\作品集\ResearchOS\research-os');W=R/'execution/v2.4/receipts/W09/W09-99';D=Path(__file__).resolve().parent
sp=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s=types.ModuleType('review_support');s.__file__=str(sp);exec(compile(sp.read_bytes(),str(sp),'exec'),s.__dict__);s.D=D

def observed(ref):
    raw=Path(ref['path']).read_bytes()
    if len(raw)!=ref['bytes'] or hashlib.sha256(raw).hexdigest()!=ref['sha256']:raise ValueError('PERSISTED_PREPARATION_DRIFT')
    return json.loads(raw)

extract_ref={'path':str(D/'repin-input-extract.json'),'sha256':'134ea0fcdb2b44d976bacfd28d136298359375a60518af4b8105515142d3a0a8','bytes':190111}
tail_ref={'path':str(D/'repin-finite-tail-extract.json'),'sha256':'e0c33631d3f9c03218c0130aca78c5bb2953c5e6e8b5d1026b9d1d8d313626d5','bytes':75069}
e=observed(extract_ref);tail=observed(tail_ref);guard=observed(e['guard_ref'])
if e['failure'] is not None or not guard['closed'] or guard['retained_handles_count'] or guard['errors']:raise ValueError('PREPARATION_SOURCE_GUARD_NOT_CLOSED')
author='codex:/root/full_w09_source_review';backend='/root/full_w09_source_review';thread=s.THREAD;root_thread='01a11007-5233-7ca1-b71f-9e9e5ce84c98';created=datetime.now(timezone.utc).isoformat()
choice=e['NF5_choice'];nf=e['NF5_HDF'];reg=e['REG5_HDF'];br=e['BR3_HDF'];refs=e['input_refs'];candidate=e['candidate_HDF']['sourcecandidate_ref'];before=e['candidate_HDF']['before_main_ref']
expected_after={'path':before['path'],'sha256':candidate['sha256'],'bytes':candidate['bytes']}
old_generation=choice['common']['generation'];new_generation='fullw09-20261010-06'
indices=[i for i,r in enumerate(choice['common']['source21']) if r==before]
if len(indices)!=1:raise ValueError('CONDITIONAL_SOURCE21_BEFORE_REF_NOT_UNIQUE')
hits=tail['blueprint_old_Main_pin_locations']
if len(hits)!=1 or hits[0]['ref']!=before or hits[0]['json_path']!=['stable_input_refs',3850]:raise ValueError('BLUEPRINT_REPIN_LOCATION_NOT_EXACT')
hosts={'source_read':s.capture('dc241f',0,0),'finite_tail':s.capture('03870a',0,0),'published_contract_shape_read':s.capture('84ac5a',0,0)}
by_name=lambda group,name:next(row for row in e['source_function_evidence'][group] if row['name']==name)
anchors={
    'private_environment':{'ref':refs['NF5_runtime'],'line':by_name('NF5_runtime','build_environment')['line']},
    'one_shot_prepare_run':{'ref':refs['NF5_runtime'],'line':by_name('NF5_runtime','stage')['line']},
    'exact_authority_and_vector':{'ref':refs['NF5_overrides'],'line':by_name('NF5_overrides','validate_authority')['line']},
    'pending_exact_once':{'ref':refs['REG5_core'],'line':by_name('REG5_core','merge_pending')['line']},
    'Root_lease_and_request':{'ref':refs['REG5_caller'],'line':by_name('REG5_caller','request_context')['line']},
    'four_scope_projection':{'ref':refs['REG5_core'],'line':by_name('REG5_core','make_native_scopes')['line']},
    'dynamic_registration':{'ref':refs['REG5_core'],'line':by_name('REG5_core','canonical_changes')['line']},
    'actual_scope_audits_before_requests':{'ref':refs['REG5_caller'],'line':by_name('REG5_caller','finalize_native_requests')['line']},
    'Main_current_Native_gate':{'ref':refs['BR3_source'],'line':by_name('BR3_source','native_inputs')['line']},
    'six_current_consumers':{'ref':refs['BR3_source'],'line':by_name('BR3_source','consumer_plan')['line']},
}

recipe={
    'schema':'researchos.w09-nf6-conditional-minimal-repin-recipe.v1',
    'source_author':author,'source_author_backend':backend,'source_author_thread_id':thread,'root_thread_id':root_thread,'created_utc':created,
    'status':'PREPARATION_ONLY_PENDING_MAIN_ADOPTION_AND_NEW_SOURCE_PUBLICATION',
    'Rootexecute':False,'currentMainqualified':False,'future_Source21_qualified':False,'execution_grant':False,'formal_acceptance':False,
    'actual_Main_observation':e['current_Main_observed_ref'],
    'candidate_is_current_Main_bytes_at_observation':e['candidate_is_current_Main_bytes'],
    'candidate_ref':candidate,'expected_after_Main_ref_is_conditional_not_current':expected_after,
    'publication_preconditions':[
        'Root adopts the independently reviewed candidate through its actual exclusive CAS and retains complete before bytes, call/result and closed0 evidence.',
        'After adoption, NF6 Source author freshly pins complete current Source21 and requires the target to equal expected_after_Main_ref; any additional Main/Source21 drift expands the review scope.',
        'A new immutable producer Source namespace is authored, signed by its real actor, and independently reviewed; no old Source namespace is edited.',
        'A new immutable registrar Source namespace repins that exact new producer, its own code and contract, with independent non-author review.',
    ],
    'producer_source_delta':{
        'base_hdf_ref':refs['NF5_HDF'],'base_manifest_ref':refs['NF5_MF'],
        'proposed_generation':new_generation,'generation_is_not_a_registered_Scope':True,
        'source.choice.json':{
            'generation_json_path':['common','generation'],'before':old_generation,'proposed_after':new_generation,
            'source21_repin':{'json_path':['common','source21',indices[0]],'before_ref':before,'conditional_after_ref':expected_after},
            'other_twenty_Source21_refs':'Preserve only when fresh after-adoption observation proves them unchanged; never infer current pins from this template.',
            'compiler_blueprint_ref':'Replace with the newly published blueprint exact 3-key ref.',
            'four_selectors':'All selected_tests, packages, go_test_argv_suffix, list_argv_suffix, expected_native_ids, assertion_owner and modes stay exact NF5 values; the Main candidate makes C19 match these already-correct expectations.',
            'run_roots':'Freeze four fresh distinct run UUIDs in the new Source; receipt_root uses new namespace, output_root uses fresh run-UUID, scratch_root uses fresh selector-UUID under unchanged physical C parent.',
            'resource_parent_owner_audit_refs':'Keep existing exact physical-C provenance only if actual Root reobservation still satisfies the unchanged predicates; this is resource-only provenance, never execution authority.',
        },
        'compiler-source-blueprint.json':{
            'before_ref':refs['NF5_blueprint'],
            'required_repin':{'json_path':hits[0]['json_path'],'before_ref':before,'conditional_after_ref':expected_after},
            'stable_input_ref_count':3905,'unchanged_stable_inputs':3904,
            'do_not_blindly_reuse_old_blueprint_bytes':True,
            'allowed_package_roster_count':353,'module_go_mod_ref_count':19,
            'required_packages':choice['selectors']['W09-G01']['packages'],
            'Go_source_module_toolchain_and_directory_roster':'No code delta expected from this Python-only adoption; retain exact unchanged bytes and inventories, and reobserve through the new actual prepare/run guards.',
            'lineage_and_changed_stable_source_refs':'Record true NF5 base provenance and the sole actual changed ref in newly authored metadata; no actual Go-list result or package count may be invented.',
            'compiler_3905_old_controls_rerun':False,
        },
        'full_w09_runtime.source.py':{
            'before_ref':refs['NF5_runtime'],
            'changes_only':'Replace generation-specific OWNER_KEY/SLICE and exact generation predicates from 05 to the proposed 06. Keep all authority, compiler, one-shot, path, Owned Job, FILETIME, argv and cleanup logic intact.',
            'new_runtime_sha':'Compute from actual newly authored bytes; no value supplied here.',
            'physical_parent':'Keep C:\\Users\\yqyyds\\.researchos\\w09-native-v5 for the minimal plan; generation 06 does not require renaming this resource parent.',
        },
        'runtime-overrides.source.py':{'before_ref':refs['NF5_overrides'],'changes_only':'Update matching generation predicates to 06 and preserve exact inverse of all remaining logic; retain as corresponding source artifact even where lifecycle functions are already installed into runtime.'},
        'prepare_full_w09.source.py':{'before_ref':refs['NF5_prepare'],'changes_only':'Update its literal pinned runtime SHA only; same main/stage/CLI body.'},
        'run_full_w09.source.py':{'before_ref':refs['NF5_run'],'changes_only':'Update its literal pinned runtime SHA only; same main/stage/CLI body.'},
        'full_w09_launcher.source.py':{'before_ref':refs['NF5_launcher'],'changes_only':'Update RUNTIME_SHA only; retain private UUID object, exact permit/runner/environment, and Main argv validation.'},
        'root-calling-contract.json':'Rebind new file paths/hashes/bytes, generation, canonical owner/worker strings and future CLI paths. Keep request schema, exact 54 Scope fields, seven Native request fields, false/zero boundaries and one-list/one-test budgets unchanged.',
        'HDF_and_MF':'Seal new actual actor/thread, namespace, Source21, selectors, file refs and controls/inverse lineage; independent review and actual Root peer observations are new, not copied old grants.',
    },
    'registrar_source_delta':{
        'base_hdf_ref':refs['REG5_HDF'],'base_manifest_ref':refs['REG5_MF'],'base_contract_ref':refs['REG5_contract'],
        'adoption_core.source.py':{'before_ref':refs['REG5_core'],'changes_only':'Change GENERATION, NKEY, NSLICE to 06. Keep merge_pending/lease/Scope construction/structural inverse/Root roles and historical old-three closure checks intact.'},
        'input-pins.json':{
            'before_ref':refs['REG5_inputs'],
            'repin_refs':['NF_hdf','NF_mf','NF_contract','NF_choice','NF_runtime','NF_prepare','NF_run','NF_launcher','NF_blueprint'],
            'retain_refs':'Historical Q/QR/profile/index/CM39/context programme qualification/shared TP/guard/locked and baseline archives remain original exact objects when their existing gates still pass.',
            'producer_review_refs':'NR_hdf/NR_mf/NR_decision are read dynamically from a new actual Root request, not fabricated in this recipe.',
            'historical_baseline_current_ref_objects':'Remain archival lineage. Do not relabel old CP/OW/SS/CM baseline hashes as current; before_canonical_refs in the future request supplies actual dynamic current4.',
        },
        'register_w09_adoption.source.py':{'before_ref':refs['REG5_caller'],'changes_only':'Update INPUT_PINS_SHA from newly published input-pins actual bytes. Keep all other execution predicates and Root CLI bodies unchanged.'},
        'root-calling-contract.source.json':'Repin new caller/core/input/producer contract refs and generation/CLI path. Keep v1 schemas, actual 36 registration-request fields, four selector set, Root-only TP and exact independent own-review gate unchanged.',
        'caller_own_review':'New exact HDF/MF/caller/core/contract refs must match the real non-author review and completed Root peer observations; old registrar review cannot authorize changed bytes.',
        'failure_ordinals':'No numeric next ordinal is issued by this Source. Root supplies immutable complete pending suffix from actual registered next to actual live next; original exits remain integers or NULL, never guessed/reset/reclassified.',
        'Canon':'Register generation06 as fresh append-only slots while preserving all prior scopes/owners/workers/failures and complete inverse. Root executes mandatory shared TP; no old Canon revision is frozen into the new Source.',
    },
    'bridge03_reuse':{
        'hdf_ref':refs['BR3_HDF'],'manifest_ref':refs['BR3_MF'],'source_ref':refs['BR3_source'],'consumer_launcher_ref':refs['BR3_launcher'],
        'source_bytes_change_required_for_this_plan':False,
        'conditions':'Keep the exact already-reviewed BR3 bytes, Main profile/index/dispatcher/CM40 pins and physical w09-native-v5 TEMP/TMP policy. Its context/request carries new Native/Mode refs and exact current formal vector dynamically.',
        'c19_policy':'RUN_CURRENT_CM40',
        'six_new_route_consumers_required':True,
        'old_C19_two_consumers':'Retain as historical bytes. They cannot qualify the changed current Source21 and cannot be substituted through REUSE_CURRENT_SOURCE21.',
        'if_resource_parent_moves':'Moving to a new v6 parent would require producer, registrar and BR3/launcher environment/resource provenance deltas plus new independent review; it is excluded from this minimal plan.',
    },
    'Root_parameters_not_issued_here':{
        'Root_registration_request':None,'Root_native_Scopes':None,'Root_request_actual_audit':None,'Root_current4':None,'Root_pending_ref':None,'Root_native_leases':None,'Root_native_requests':None,'Root_canonical_vector':None,'Source_non_author_review_refs':None,'Mode_decisions':None,
        'lease_rules':{'maximum_seconds':3600,'exactly_four_distinct_native_lease_ids':True,'native_expiry_within_Root_lease':True,'current_issued_not_future':True,'must_cover_actual_prepare_and_run':True},
        'Native_budget_rules':{'maximum_go_list_runs':1,'maximum_go_test_runs':1,'list_timeout_seconds':240,'producer_timeout_seconds':420,'inner_Go_timeout_seconds':180,'automatic_retry':False},
        'authority':'Only actual Root may issue request/Scopes, completed host observations, owner/worker records and execute TP. Source status or resource marker never substitutes for those gates.',
    },
    'code_anchors':anchors,
    'old_controls_rerun':False,'actual_Root_stages_Native_Go_SQL_model_TP_calls':0,
}
recipe_ref=s.write('conditional-repin-recipe.source.json',recipe)

concurrency={
    'schema':'researchos.w09-nf6-code-concurrency-readiness.v1','status':'SOURCE_INFERENCE_NOT_ACTUAL_PARALLEL_QUALIFICATION',
    'code_anchors':anchors,
    'producer_framework_forces_serial_execution':False,
    'read_shared_resources':['Locked GOROOT/tools','GOPATH pkg/mod stable inputs','exact Source/blueprint/current4/archive/peer refs under FILE_SHARE_READ_ONLY'],
    'selector_private_writes':['fresh receipt_root and producer subtree','fresh scratch profile/temp/gocache','fresh output run-UUID and owned test exports','unnamed exclusive Owned Job for each launched child'],
    'shared_GOCACHE_reuse_allowed':False,
    'private_GOCACHE_required_fresh_empty':True,
    'compiler_cache_serial_reason':'There is no outer shared writable Go compilation cache in the published framework. Each selector compiles through its own private GOCACHE; shared module/tool inputs are pinned read-only and network resolution is off.',
    'per_process_resource_controls':{'GOFLAGS':'-mod=readonly -p=1','GOMAXPROCS':'2','GOPROXY':'off','GOSUMDB':'off','GOWORK':'off','CGO_ENABLED':'0'},
    'four_way_framework_path_isolation_possible_from_code':True,
    'four_way_product_concurrency_tested':False,
    'four_way_execution_grant':False,
    'project_default_active_construction_task_limit':2,
    'project_policy_ref':s.pin(R/'AGENTS.md'),
    'recommended_existing_policy_schedule':[['W09-G01','W09-G02'],['A06','C19']],
    'schedule_is_execution_authority':False,
    'Root_preconditions_for_two_parallel_runs':[
        'Both exact Root Scopes/leases/requests are actually registered and finalised for one fixed current4.',
        'All four new UUID roots are distinct and absent before prepare; no shared mutable scratch or output.',
        'Root observes aggregate physical C free space for both private compiler caches, actual CPU/memory and lease headroom; no historic evidence deletion or junction workaround.',
        'No Main/Canon/role mutation while any selector holds current4/Source guards. A failed branch retains its original IO and pending ordinal without mutating that fixed vector.',
        'Each branch retains its own actual hostpair/inner exit/Owned Job/guard completion; first failure stops that branch with no retry.',
    ],
    'timing':'Each run has 240s list plus 420s producer caps. Two waves have a 1320s sum of these caps before prepare/observation/cleanup overhead; this is a configured budget, not a measured runtime or success guarantee.',
    'serial_fallback':'If aggregate cache/CPU/space/lease observation is insufficient, Root uses the same exact single-selector entries serially; do not alter budgets or borrow expired leases.',
    'Rootexecute':False,'currentMainqualified':False,'execution_grant':False,'formal_acceptance':False,
}
concurrency_ref=s.write('parallel-and-cache-readiness.source.json',concurrency)

order={
    'schema':'researchos.w09-nf6-shortest-safe-root-order.v1',
    'Rootexecute':False,'currentMainqualified':False,'execution_grant':False,'formal_acceptance':False,
    'steps':[
        {'stage':'close_previous_generation_and_adopt_Main','action':'Root first observes all four NF5 stages/Owned Jobs/guards closed and retains originals including C19 failure1156 and all pending failures. Root alone performs any needed closure TP and independently reviewed single-target candidate CAS, retaining immutable before/after/actual IO.'},
        {'stage':'publish_after_adoption_NF6_and_REG6','action':'Freshly observe current complete Source21; author new NF6 and registrar immutable Sources using only recipe deltas. Obtain real non-author reviews and real Root author/reviewer peer captures. Do not reinterpret historical NF5 qualification as current.'},
        {'stage':'Root_registration','action':'Root creates one real finite registration request with exact dynamic current4, complete pending suffix and four distinct native leases; observe it with a completed Root toolpair. Execute the existing registrar propose/check/activate serially through mandatory shared TP.'},
        {'stage':'Root_actual_scope_audits_and_finalize','action':'After actual activation, capture each of four actual Scope issuance hostpairs. Use finalize-native-requests to verify actual committed current4 and scope audits before publishing one exact canonical vector and four request refs. No future actual toolpair may be supplied.'},
        {'stage':'prepare_and_run_four_selectors','action':'Root uses identical sealed NF6 prepare/run CLI and exact selector/request3ref args for each one-shot branch. Keep that canonical vector fixed until all four branches finish and every guard/Owned Job closes. Two waves of up to two runs are code-feasible subject to actual Root resource/lease observations and project policy.'},
        {'stage':'new_Mode_qualification','action':'After four real complete PASS closures and exact current Source21/argv/Go/assertion/FILETIME/OwnedTemp facts are independently verified, the actual independent mode reviewer publishes six route-specific Mode proofs. No failed/inflight branch or Source HDF is a Mode PASS.'},
        {'stage':'formal_Bridge_current_six_routes','action':'Only after all Native closures, Root may change formal Canon/roles. Reuse unchanged BR3 Source with a new actual Root request/context/role Scope, RUN_CURRENT_CM40, six exact new mode/report/tool refs and actual backend role captures; execute all six consumers through the existing Main dispatcher and Main assembler/verifier gates.'},
    ],
    'Native_vector_vs_later_formal_vector':'All prepare/run within generation06 must share one unchanged actual vector. Later formal role/assembler transactions may advance current4 after all Native guards/jobs close; historical Native vector does not have to equal the later formal vector, but all existing Main provenance/Source/lease gates remain mandatory.',
    'no_second_formal_acceptance_engine':True,
    'known_registrar_limit':'Existing REG5 canonical_changes explicitly checks the older NF3 three scopes for closure and appends fresh generation slots. It does not by itself prove NF5 four stages closed; Root must establish and preserve those actual closure facts before a new generation and before any CAS.',
}
order_ref=s.write('shortest-safe-root-order.source.json',order)

decision_ref=s.write('repin-decision.json',{
    'schema':'researchos.w09-nf6-minimal-repin-preparation-decision.v1',
    'verdict':'REPINS_IDENTIFIED_NOT_EXECUTION_QUALIFIED','source_author':author,'source_author_backend':backend,'source_author_thread_id':thread,'root_thread_id':root_thread,'created_utc':created,
    'actual_Main_ref':e['current_Main_observed_ref'],'candidate_ref':candidate,'candidate_is_current_Main_bytes_at_observation':e['candidate_is_current_Main_bytes'],
    'input_extract_ref':extract_ref,'finite_tail_extract_ref':tail_ref,'guard_ref':e['guard_ref'],'actual_Source_read_hosts':hosts,
    'recipe_ref':recipe_ref,'concurrency_ref':concurrency_ref,'Root_order_ref':order_ref,
    'essential_repin_findings':{'choice_source21_index':indices[0],'blueprint_stable_input_index':3850,'other_blueprint_stable_inputs_unchanged_if_reobserved':3904,'current_54_Native_Scope_fields_retained':True,'current_36_registration_request_fields_retained':True,'all_four_new_Native_and_six_current_consumers_required':True,'BR3_Source_change_required_when_parent_unchanged':False,'private_GOCACHE_reuse_allowed':False},
    'new_read_inputs':25,'guard_closed':True,'guard_retained_handles_count':0,'compiler_3905_controls_rerun':False,'old_successful_controls_rerun':False,
    'new_failures':[],'Root_ordinal_issued_by_this_Source':False,'actual_Root_stages_Native_Go_SQL_model_TP_calls':0,'Main_Canon_NF5_Scope_written':False,
    'Rootexecute':False,'currentMainqualified':False,'future_Source21_qualified':False,'Source_independently_accepted':False,'execution_grant':False,'formal_acceptance':False,
})
members=[s.pin(p) for p in sorted(D.iterdir(),key=lambda p:p.name) if p.is_file() and p.name not in ('HDF.json','MF.json')]
mf_ref=s.write('MF.json',{'schema':'researchos.w09-nf6-minimal-repin-preparation-manifest.v1','source_author':author,'source_author_thread_id':thread,'created_utc':created,'members':members,'member_count':len(members),'handoff_excluded_to_avoid_circular_hash':True,'Rootexecute':False,'currentMainqualified':False,'execution_grant':False,'formal_acceptance':False})
hdf_ref=s.write('HDF.json',{
    'schema':'researchos.w09-nf6-minimal-repin-preparation-hdf.v1','status':'SOURCE_PREPARATION_ONLY_PENDING_MAIN_ADOPTION_AND_NEW_SOURCE_PUBLICATION',
    'source_author':author,'source_author_backend':backend,'source_author_thread_id':thread,'root_thread_id':root_thread,'created_utc':created,
    'manifest_ref':mf_ref,'decision_ref':decision_ref,'recipe_ref':recipe_ref,'concurrency_ref':concurrency_ref,'Root_order_ref':order_ref,
    'actual_Main_observed_ref':e['current_Main_observed_ref'],'candidate_ref':candidate,'candidate_is_current_Main_bytes_at_observation':e['candidate_is_current_Main_bytes'],
    'input_extract_ref':extract_ref,'finite_tail_extract_ref':tail_ref,'guard_ref':e['guard_ref'],'actual_Source_read_hosts':hosts,
    'input_refs':refs,'new_read_inputs':25,'guard_closed':True,'guard_retained_handles_count':0,
    'compiler_3905_controls_rerun':False,'old_successful_controls_rerun':False,'new_failures':[],
    'Source_independently_accepted':False,'Rootexecute':False,'currentMainqualified':False,'future_Source21_qualified':False,'execution_grant':False,'formal_acceptance':False,
    'actual_Root_stages_Native_Go_SQL_model_TP_calls':0,'Main_Canon_NF5_Scope_written':False,'STOP':True,
})
print(json.dumps({'schema':'researchos.w09-nf6-minimal-repin-preparation-delivery.v1','operation':'SOURCE_REPIN_PREPARATION','status':'SOURCE_PREPARATION_ONLY','source_author':author,'source_author_backend':backend,'source_author_thread_id':thread,'root_thread_id':root_thread,'source_refs':{'hdf':hdf_ref,'mf':mf_ref,'decision':decision_ref},'recipe_ref':recipe_ref,'concurrency_ref':concurrency_ref,'Root_order_ref':order_ref,'actual_Main_ref':e['current_Main_observed_ref'],'candidate_ref':candidate,'guard_ref':e['guard_ref'],'new_read_inputs':25,'guard_closed':True,'guard_retained_handles_count':0,'compiler_3905_controls_rerun':False,'old_successful_controls_rerun':False,'new_failures':[],'Rootexecute':False,'currentMainqualified':False,'future_Source21_qualified':False,'execution_grant':False,'formal_acceptance':False,'STOP':True},ensure_ascii=False))
