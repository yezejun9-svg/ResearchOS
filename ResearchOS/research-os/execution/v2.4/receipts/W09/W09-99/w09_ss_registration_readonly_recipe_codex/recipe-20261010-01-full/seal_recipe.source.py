from pathlib import Path
import datetime, hashlib, json, types

R=Path(r'D:/作品集/ResearchOS/research-os');V=R/'execution/v2.4'
W=V/'receipts/W09/W09-99';B=V/'receipts/W05/W05-99'
D=Path(__file__).resolve().parent
SUPPORT=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
raw=SUPPORT.read_bytes()
assert len(raw)==4940 and hashlib.sha256(raw).hexdigest()=='567f53cadfab3781d6345ed1c6b04b52b85135e0843ce3c217e2f7fadf2a021a'
s=types.ModuleType('ss_recipe_support');s.__file__=str(SUPPORT)
exec(compile(raw,str(SUPPORT),'exec'),s.__dict__);s.D=D
assert not (D/'registration-recipe.json').exists()
atomic_ref=s.exact_ref(V/'receipts/W04/W04-99/integration_codex/revalidation-82783db86d8a4a49a287c371c72f156d/register.py','a7cc4305c90209271428d2c95769b515e36a949a1ae13b3d1dc7eef1756cf850',82251)
w07_ref=s.exact_ref(V/'receipts/W07/W07-99/integration_codex/issue_reviewed_current.py','b65d2a363c513e0bbdec8659f96a0f19f3fe140a39d28f39e5590170b62bb250',34384)
api_ref=s.exact_ref(V/'formal_case_index.py','e08a7f605ca12d79c672b6af0360a02b26e2231d2a602207d0ea6a37f24f7b0b',71844)
profile_ref=s.exact_ref(V/'formal_profile_w09.py','1e04865beef37fdbffa06d649d072721d7b6eb0ef5e525d87bb867da414e4087',71403)
RUN=W/'w09_br8_actual_root/actual-20261010-01'
owner_ref=s.exact_ref(RUN/'prospective-owner.actual.root.json','660d33240bba2e12a49da1c37c18153897e5fabd9cfa45f6e676c25ef1b83b36',1056)
capture_result_ref=s.exact_ref(RUN/'capture-a7067db724ce4a34a71a01055c9e00c8/result.json','8a9e3a2915c12bd67df0768f13696e9a087704fbf72f1c5ba22cef68ff1c884f',6058)
refs=[atomic_ref,w07_ref,api_ref,profile_ref,owner_ref,capture_result_ref,s.pin(SUPPORT),s.pin(Path(__file__))]
g=s.guard()
try:
 g.acquire(refs)
 owner=json.loads(g.get_buffer(owner_ref['path']))
 excerpts=[]
 for ref,ranges in [(atomic_ref,[(109,114),(987,993),(1194,1210)]),(w07_ref,[(158,165),(428,444),(479,495)]),(api_ref,[(943,966),(1089,1126),(1155,1161)]),(profile_ref,[(410,423),(1101,1110)])]:
  lines=g.get_buffer(ref['path']).decode('utf-8').splitlines()
  for lo,hi in ranges:excerpts.append({'source_ref':ref,'start_line':lo,'end_line':hi,'source':'\n'.join(lines[lo-1:hi])})
 source_facts={'schema':'researchos.w09-ss-registration-readonly-source-facts.v1','source_refs':refs[:6],
   'excerpts':excerpts,'observed_owner_ref':owner_ref,'owner_evidence_ref_shape':{k:type(v).__name__ for k,v in owner['evidence'][0].items()},
   'existing_atomic_state_fixed_target':'execution/v2.4/step_state.json','existing_whole_W04_and_W07_CLI_not_general_W09_registrars':True,
   'Source_tests_or_formal_checks_executed':False,'live_Canon_guard_handles':0}
finally:
 closed=g.close();guard_ref=s.write('recipe-read-guard.closed.json',closed)
assert closed['verification']=='PASSED' and closed['closed'] is True and closed['retained_handles_count']==0 and closed['failure'] is None and closed['errors']==[]
facts_ref=s.write('source-facts.json',source_facts)
recipe={
 'schema':'researchos.w09-ss-registration-readonly-recipe.v1',
 'status':'PREPARED_ROOT_APPROVAL_AND_MAIN_PRECHECK_REQUIRED',
 'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),
 'recipe_author':'codex:/root/full_w09_source_review','backend_actor_id':'/root/full_w09_source_review',
 'prospective_owner_ref':owner_ref,'new_independent_owner_approval_ref':None,'future_Root_Main_precheck_ref':None,
 'SS_observed_before_ref':{'path':str(V/'step_state.json'),'sha256':'fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149','bytes':257446},
 'SS_format':{'schema_version':'1.0','package_version':'2.4.0','plan_sha256':'a6669dd94b16bc833526f569c3c86ab08180ff6a39087ca9921ea898817eea17','steps_type':'list'},
 'owner_reference_contract':{'exact_keys':['path','sha256'],'path_base':str(V),'path_spelling':'V-relative POSIX, e.g. receipts/W09/W09-99/...; no execution/v2.4 prefix, bytes, absolute path or backslash in an owner.evidence ref',
   'exactly_one_each_schema':['researchos.w09.current-context.v1','researchos.w09.independent-review.v1','researchos.w09.root-observed-issuance.v1'],'source':{'ref':api_ref,'line':943}},
 'time_contract':{'format':'timezone-aware ISO8601; real Root-selected prospective accepted_at, never future time',
   'order':['review execution cutoff','original received_at','capture root_observed_at','issuance observed_at','owner accepted_at'],
   'issuer_identity':'/root/backup_regression_resources','Root_observer':'codex:/root','source':{'ref':profile_ref,'line':1101}},
 'Main_precheck_contract':{'entry':'formal_profile_w09.verify_owner(api._profile_api(), reader, prospective_owner, roots, plan_path)',
   'roots_entry':'formal_case_index._registered_roots(reader, prospective_owner, "W09")',
   'reader':'formal_case_index.Reader(repo_root)','meaning':'ACCEPTED is only the in-memory prospective field required by this Main API; no SS registration is created by the read-only precheck.',
   'required_actual_result':'Root actual precheck succeeds and its complete immutable dependency snapshot and host return are preserved; Source review/component qualification cannot stand in for this result.',
   'API_source_ref':api_ref,'profile_source_ref':profile_ref},
 'single_SS_atomic_mechanism':{'source_ref':atomic_ref,'entry':'atomic_state(repo, expected_hash, desired_SS_raw_bytes, out)',
   'definition_line':987,'fixed_target':'execution/v2.4/step_state.json','steps':['exclusive CREATE_NEW staging under out','flush and fsync staging','full current SS SHA equals expected_hash immediately before replacement','os.replace(staging, canonical_SS)','whole readback SS SHA equals desired raw bytes SHA'],
   'same_volume_requirement':'out/staging and canonical SS are on the same local D: volume',
   'writer_condition':'Actual Root holds the exclusive serial SS registration lease covering the write. All canonical writers must honor that lease; the hash-check and rename primitive alone is not an OS multi-writer compare-and-swap.',
   'do_not_invoke':'The enclosing historical W04 prepare/apply/recover CLI or W07 issue_current workflow has fixed card actors/schemas and cannot be passed W09 inputs.',
   'TP_policy':'Do not monkeypatch canonical_transactions.py; its CP/OW pair remains unchanged.'},
 'minimum_Root_registration_order':[
   'Retain the exact independently approved prospective owner ref and actual published capture/issuance; Main precheck must succeed before preparing a canonical SS acceptance write.',
   'Acquire Root exclusive serial SS writer lease; read complete original SS and archive its original bytes. Any unrelated SS update changes the full-state CAS and requires fresh preparation, rather than a merged silent overwrite.',
   'Append exactly the approved W09-99 row only if absent. Preserve every other row, order and top-level schema/package/plan metadata. If an owner row already exists, require an explicit reviewed transition instead of duplicate append.',
   'Save immutable desired SS bytes, original bytes, approval/owner/precheck refs, expected original SHA, desired SHA and PENDING_NOT_ACCEPTED intent journal. Never publish completion before replacement/readback/postcheck.',
   'Close retained SS read handles; recheck all precheck evidence and the expected complete SS SHA under the Root lease, then call only the SS atomic replacement primitive. CP/OW/CM are separate Root transactions; this write does not update them.',
   'Root invokes current formal_case_index.derive_formal_cases(repo, canonical_SS, frozen_plan) after replacement; W09 must derive VALID_ACCEPTED for its actual owned C19/A06 cases. Preserve all other derived owner states and existing failures; no 42-case or parent acceptance may be inferred from Source components.',
   'Recheck the new postwrite dependency snapshot and readback hashes. Only then append a durable success/registration marker. A postwrite failure preserves original/desired/actual bytes and journal and does not automatically roll back or claim completed registration.'
 ],
 'postwrite_cli_contract':{'python_flags':['-I','-S','-B','-X','utf8'],'script':str(V/'formal_case_index.py'),'arguments':['--repo',str(R),'--state',str(V/'step_state.json'),'--plan','<actual frozen execution.plan.json absolute path>'],'executed_by_this_recipe':False},
 'original_capture_proposal_retained':capture_result_ref,
 'known_pending_literal_issue':'The original capture proposal has a backslash source_audit_path while current Main requires its exact ROOT_SOURCE_AUDIT_LOG forward-slash literal. Root is preparing a new metadata capture helper and genuine new event; old proposal bytes are preserved and cannot be treated as a successful Main precheck.',
 'source_facts_ref':facts_ref,'guard_ref':guard_ref,
 'retained_handles_count':0,'live_Canon_guard_handles':0,'product_calls':0,'Canon_Main_Scope_writes':0,
 'new_native_runs':0,'Source_or_product_acceptance_issued':False,'execution_grant':False,'formal_acceptance':False,'STOP':True}
recipe_ref=s.write('registration-recipe.json',recipe)
print(json.dumps({'recipe_ref':recipe_ref,'source_facts_ref':facts_ref,'guard_ref':guard_ref,'retained_handles_count':0,'live_Canon_guard_handles':0,'product_calls':0},ensure_ascii=False))
