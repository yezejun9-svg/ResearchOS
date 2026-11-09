from pathlib import Path
import datetime, hashlib, json
O=Path(__file__).parent
R=Path('D:/作品集/ResearchOS/research-os')
W=R/'.local/worktrees/codex-w1303-desktop-http-r311'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def put(name,v):
 with (O/name).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
audit=read(O/'collect-audit.json');sup=read(O/'supplement-audit.json');matrix=read(O/'input-finite-matrix.json');handoff=read(O/'input-handoff.json')
assert not sup['failed_checks']
assert len(audit['failed_checks'])==5
assert all(x['check'].startswith('raw TAP ') for x in audit['failed_checks'])
source_map={x['path']:x['current'] for x in sup['final_source_rows']}
def sr(p,lines):return {'source_ref':source_map[p],'lines':lines}

counterexamples=[
 {'id':'W13-SR-01-C1','suggested_selector':'desktop-http/revision/ack-before-concurrent-get','status':'NOT_RUN',
  'file':'tests/ui/desktop/http-wire-boundary.test.mjs','prerequisites':'Fresh fixed session state; valid full frozen attach ACK and full GET snapshot; no model or actual Host. Use explicit server/deferred promise ordering, never a timing sleep.',
  'raw_sequence':[
   'Capture immutable original attach A envelope and command_id before dispatch. A requests write ownership, writer_epoch=null and correct expected_revision.',
   'Hold the actual loopback A response after POST receipt. Start GET B using the same state object before A response completes. B must be enqueued/issued; do not await A first.',
   'Release schema-valid A ACKNOWLEDGED/PendingResult. Record the original A result and current command barrier independently of presentation ticket.',
   'Release schema-valid B COMPLETED snapshot showing advanced revision and requested local writer/epoch. B cannot finalize A or create write authority from an uncompleted A.',
   'Attempt a different SEND. It must refuse locally with the original command still pending, zero additional HTTP or child process.',
   'Positive completion leg: explicit replay of A uses the exact original command_id and request bytes, receives valid same-command COMPLETED; only then allow one dependent SEND. Record all wire hashes/state transitions.'
  ],'expected_caps':{'loopback_http_max':4,'pure_validator_children_max':8,'external_http':0,'model':0,'SDK':0,'paid':0},
  'must_assert':['A remains ACKNOWLEDGED and never becomes synthetic COMPLETED','GET/read presentation generation does not erase pending A','No adoption from GET captured pending=null','Other project/session responses cannot mutate selected context','Exact original A replay identity and unchanged protected legacy paths'],
  'actual_exit':None,'actual_http':None,'actual_children':None},
 {'id':'W13-SR-02-C1','suggested_selector':'desktop-http/revision/private-six-key-types','status':'NOT_RUN',
  'files':['apps/desktop/validator/main_test.go','tests/ui/desktop/http-wire-boundary.test.mjs'],
  'raw_sequence':['Take a complete valid REQUEST packet with fixed nonce, canonical base64 full host.status envelope and response_raw_base64=""; preserve bytes before each child invocation.',
                  'Variant A replaces the one literal key "schema" with "Schema", preserving exactly six members. Expect private-packet refusal, no network.',
                  'Variant B retains all exact keys but replaces response_raw_base64 empty string with JSON null. Expect private-packet refusal, no network.'],
  'required_table':'Every required key is an exact decoded JSON member name; reject case aliases, missing/extra/duplicate decoded names. All schema/phase/nonce/request_raw_base64/response_raw_base64 are non-null strings; REQUEST http_status is null and response string empty; RESPONSE http_status is integral 100..599. Keep Unicode, base64, byte/depth limits and phase/hash identity checks.',
  'expected_caps':{'loopback_http_max':0,'pure_validator_children_max':2,'external_http':0,'model':0,'SDK':0,'paid':0},
  'actual_exit':None,'actual_http':None,'actual_children':None},
 {'id':'W13-SR-02-C2','suggested_selector':'desktop-http/revision/private-json-whitespace','status':'NOT_RUN',
  'files':['apps/desktop/main/lib/http-wire.js','apps/desktop/build-validator.py','tests/ui/desktop/http-wire-boundary.test.mjs'],
  'raw_sequence':['Use an explicitly synthetic fault child emitting an otherwise valid correlated REQUEST verdict prefixed by UTF-8 NBSP (C2 A0), then EOF/clean full close. Preserve original stdout bytes.',
                  'REQUEST consumer must refuse PRIVATE_JSON before POST; JSON whitespace is only SP/HT/LF/CR. Never strip BOM, NBSP, VT or FF as if valid JSON framing.'],
  'expected_caps':{'loopback_http_max':0,'pure_validator_children_max':1,'external_http':0,'model':0,'SDK':0,'paid':0},
  'actual_exit':None,'actual_http':None,'actual_children':None}
]
put('proposed-counterexamples.NOT_RUN.json',{'status':'READONLY_PROPOSAL_REQUIRES_ROOT_SCOPE','original159_and7':'Preserve selectors, original assertions and historical raw. Supplemental cases are separate and not executed.',
 'cases':counterexamples,'aggregate_proposed_caps':{'new_node_leaves':3,'loopback_http_max':4,'pure_validator_children_max':11,'external_http':0,'model':0,'SDK':0,'paid':0},
 'go_unit_boundary':'Extend existing main_test.go tables within the same source path; existing two Go tests were only compiled by author. Any actual Go unit execution needs the future explicit finite grant; no unit PASS is claimed here.'})

findings=[
 {'id':'W13-SR-01','priority':'P1','category':'CORRECTNESS_COMMAND_COMPLETION_BARRIER','status':'STATIC_CONFIRMED_NOT_EXECUTED',
  'title':'Concurrent GET can discard an original ACK and adopt apparent writer authority before that command completes',
  'source':[sr('apps/desktop/main/lib/ipc.js',[59,119])],
  'cause':'callV2 captures pending at line66, increments a shared presentation ticket at88–89, then returns STALE_RESPONSE at98 before recording ACK at99–102. A later GET started while the original command is in flight has pending=null and a newer ticket; it can adopt a snapshot at109–114 while the original ACK was discarded. The transport serializes HTTP, not command lifecycle state admission.',
  'impact':'A fully valid ACK may lose the original command replay/completion barrier. A schema-valid GET writer snapshot can then enable another write even though the original attach/write never completed.',
  'existing_coverage_gap':'Current pending-takeover controls await the first ACK before GET. The late/atomic tuple tests do not place the newer GET between issuance of A and processing its ACK.',
  'required_change':['Maintain command-in-flight/pending identity independently of presentation/read tickets; reserve or serialize command admission before asynchronous exposure.',
                     'Validated ACK must preserve the exact original command/request barrier even when a newer read presentation is pending; never clear it based on GET.',
                     'At authority adoption commit, consult current command state rather than a stale captured pending variable. Only a validated terminal response for the original command may release its barrier.',
                     'Retain tuple/context generation protections: no stale command completion may mutate a newly selected project/session, and no blind resubmission/new command_id is allowed.'],
  'minimal_bounds':'Original ipc.js callV259–110 (current59–119) is already owned. Function-local state or a callV2-owned WeakMap can stay inside that function. Keep original protected1–8,11–58,163–191 byte exact; no first11/export/native/browser edits needed.',
  'future_case_ref':ref(O/'proposed-counterexamples.NOT_RUN.json'),'native_exit':None,'product_case_run':False},
 {'id':'W13-SR-02','priority':'P2','category':'STRICT_PRIVATE_PROTOCOL','status':'STATIC_CONFIRMED_NOT_EXECUTED',
  'title':'Private protocol accepts non-exact packet members/types and non-JSON framing whitespace',
  'source':[sr('apps/desktop/validator/main.go',[338,385]),sr('apps/desktop/main/lib/http-wire.js',[52,75])],
  'cause':'Go struct decoding is case-insensitive even with DisallowUnknownFields; the subsequent map checks only member count. A six-member packet using Schema instead of schema is accepted; null response_raw_base64 becomes the zero string and satisfies REQUEST. In the reverse direction privateJSON uses JavaScript /\\s/, admitting NBSP and other whitespace outside JSON grammar.',
  'stdlib_support_ref':ref(O/'go-json-decode.source'),
  'stdlib_lines':[47,48,94,96,702,898,908],
  'impact':'The declared strict six-key/type and single valid JSON packet boundary is weaker than its frozen private protocol. The normal producer emits valid bytes, but malformed private stream controls must fail closed rather than silently normalize.',
  'required_change':['Before struct projection, validate exact decoded key set and each raw JSON type. Five fields are non-null strings; http_status is null only for REQUEST or an integer in100..599 for RESPONSE. Keep strict duplicate/Unicode/base64/phase and raw byte limits.',
                     'Limit privateJSON insignificant whitespace to U+0020,U+0009,U+000A,U+000D. Keep duplicate decoded keys, invalid Unicode, unsafe numbers, trailing values, size and depth refusals.',
                     'Add fixed-byte negative controls without modifying frozen public schemas or relaxing existing 159+7 predicates.'],
  'minimal_bounds':'main.go/main_test.go/http-wire.js/http-wire-boundary.test.mjs are original NEW whole-file paths. If a fault mode is needed, only the already-owned synthetic fault child source in build-validator.py; do not alter its locked builder or add an unregistered file.',
  'future_case_ref':ref(O/'proposed-counterexamples.NOT_RUN.json'),'native_exit':None,'product_case_run':False}
]

areas=[
 {'area':'All15 source and17 protected spans','result':'VERIFIED_BYTES','evidence':['source-only Git delta exactly15; receipt HEAD separate','all source blobs match current','17 original protected byte spans preserved including first11/native/credential/browser code']},
 {'area':'Full Go schema and exact numbers','result':'REVIEWED_WITH_PRIVATE_PACKET_FINDING','evidence':['Original raw jsontext validation and UseNumber; bounded numeric scanner before big.Rat; frozen API schema digests and SchemaDoc loader reused','integer tagging carries original lexeme and exact normalized integer beyond2^53/int64; decimal is display-only; no float authority coercion','Two Go unit functions compiled only; no independent unit execution']},
 {'area':'Request and response phases','result':'REVIEWED_WITH_PRIVATE_FRAMING_FINDING','evidence':['Separate nonce and exact request digest/phase binding; request child complete cleanup before HTTP; captured request unchanged before POST','Full original response bytes go to pure validator; identity/schema checked before adoption; no unsafe HTTP response JSON.parse','No actual Host >1MiB qualification']},
 {'area':'Child lifecycle and quarantine','result':'STATIC_AND_AUTHOR_FINITE_EVIDENCE_REVIEWED','evidence':['Retained ChildProcess, exit/stdio/full close gating, bounded deadlines, unresolved child blocks lane; no PID taskkill authority','Author current raw finite rows and module observations verified; sampled module observations do not prove every possible late-loaded module','Future independent runner must freeze real process resources and preserve actual timeout/nullable exits']},
 {'area':'Fixed resource authority','result':'DEVELOPMENT_BOUNDARY_REVIEWED','evidence':['Main chooses canonical app ROOT; no renderer/env arbitrary validator descriptor path','Descriptor schema/exe/module inventory and hash checks; no broad package installation','Same-user filesystem replacement/installed atomic release is not proven; release qualification remains HOLD']},
 {'area':'ACK and state authority','result':'REQUEST_CHANGES_W13_SR_01','evidence':['Sequential ACK retains pending identity and explicit completion checks','Concurrent newer GET bypasses recording branch; current barrier must be independent of presentation sequence']},
 {'area':'React and legacy renderers','result':'AUTHOR_OFFSCREEN_EVIDENCE_ONLY','evidence':['Main defaults actual React path; both renderers use exact numeric/display operations and completion barriers','Two actual offscreen renderer cases in current cohort; visible installed GUI/nativeframe/NVDA/browser continuity remain HOLD']},
 {'area':'Builder and closed inputs','result':'VERIFIED_RECORDED_BYTES','evidence':['Pinned local Go/Node/Electron, readonly module/no download; unique development output','6386 original build/cohort/current inputs match;2206 ZIP entries verified','Inherited environment is an author evidence limitation; future independent execution must specify/freeze its own environment/resources']},
 {'area':'Historical failures and current cohort','result':'PRESERVED_NO_COUNT_RESET','evidence':['159 finite plus7 regression units same current source/cohort;7units=5Node leaves+2legacy programs, not7Go tests','No summing old cohorts to fill current gaps; original failure/qualification-deviation records remain immutable','HTTP154current/302history are author observed/assertion-derived counts, not an independent network trace']}
]

diagnostics={'actual_product_execution':False,'new_actual_nonzero_failure_origins':[],
 'outer_zero_diagnostics':[{'tool':'fbe176','actual_outer_exit':0,'actual_native_product_exit':None,'raw_file':None,'raw_locator':'conversation tool fbe176',
 'detail':'Two PowerShell nonterminating Get-Content errors from resolving Main-only scope receipts under author worktree; same command overall0. Correct Main paths resolved by actual inventory a37715. No fabricated outer1 or product test failure.'}],
 'reader_correction':{'original_ref':ref(O/'collect-audit.json'),'actual_exit':0,'incorrect_check_count':5,'supplement_ref':ref(O/'supplement-audit.json'),'corrected_checks':5,'original_bytes_preserved':True},
 'readonly_invocations':[{'script_ref':ref(O/'collect.py'),'launch_tool':'21ca2f','session_id':59732,'completion_tool':'3bcd86','actual_exit':0,'raw_limit':'Direct tool outputs were not redirected; per-Git child raw and collect-audit persisted.'},
 {'script_ref':ref(O/'supplement.py'),'tool':'39978b','actual_exit':0,'stdout_ref':ref(O/'supplement.stdout.raw'),'stderr_ref':ref(O/'supplement.stderr.raw')}],
 'static_findings_are_not_native_failures':True}
put('diagnostics.json',diagnostics)
review={'schema':'researchos.desktop-exact15-source-independent-review.v1','reviewer':'codex:/root/w05_merge_review','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'decision':'REQUEST_CHANGES','source_commit':handoff['source_commit'],'evidence_head':'0f708eaf0c624fb721f7c9a00d5465ef5f13a68c','base':handoff['base'],
 'author_handoff_ref':ref(O/'input-handoff.json'),'author_original_handoff_ref':audit['input_refs'][0],
 'source_paths':source_map,'source_path_count':15,'protected_span_count':17,
 'evidence_summary':{'manifest_files_hashed':4525,'compiled_resource_inputs_hashed':6386,'zip_entries_hashed':2206,
   'author_current_finite_leaves':159,'author_current_regression_units':7,'regression_breakdown':{'node_test_leaves':5,'legacy_programs':2},
   'author_current_native_failure':0,'author_current_skip':0,'current_http_reported':154,'all_history_http_reported':302,'all_history_http_cap':386,
   'offscreen_renderers':2,'process_module_snapshots':13,'unique_observed_process_files_checked':92,
   'independent_product_cases_executed':0,'source_or_canonical_mutations':0,
   'network_counts_basis':'Inspected fixture sources, original invocations/observation JSON and original legacy assertions. No independent product/network execution.',
   'author_reported_external_model_SDK_paid':{'external':0,'model':0,'SDK':0,'paid':0},
   'author_original_failure_index_records':sup['author_failure_index_count'],'author_history_result_count':sup['author_history_result_count']},
 'findings':findings,'all_source_area_review':areas,
 'minimal_future_revision':{'within_original15':True,'expected_touched_paths':['apps/desktop/main/lib/ipc.js','apps/desktop/validator/main.go','apps/desktop/validator/main_test.go','apps/desktop/main/lib/http-wire.js','tests/ui/desktop/http-wire-boundary.test.mjs'],
  'optional_existing_path':'apps/desktop/build-validator.py only a synthetic invalid-output fixture mode if required for whitespace counterexample',
  'ipc_original_function_bounds':[59,110],'ipc_candidate_function_bounds':[59,119],
  'protected_span_rule':'All17 original hashes unchanged. Original ipc1–8/11–58/163–191 must remain exact; no new outside-bound edit proposed.',
  'execution':'No implementation or test permission is granted by this review. Root registers candidate revision and any new controls before execution.',
  'counterexample_ref':ref(O/'proposed-counterexamples.NOT_RUN.json')},
 'evidence_refs':{name:ref(O/name) for name in ['collect-audit.json','supplement-audit.json','author-manifest-verification.json','inputs.independent-current.json','archive-independent.json','case-independent.json','protected-independent.json','path_bounds_ref.json','preflight_supplement_ref.json','diagnostics.json']},
 'limitations':handoff['not_run_or_hold']+[
  'Independent159+7 replay is not authorized or started; Root replay draft remains HOLD pending fixes.',
  'Read-only static counterexamples are NOT_RUN, not actual native failures. Original840bc6/0f708 author evidence remains historical and is not edited.',
  'Source-only review does not confer Main integration, installed release, W13 parent,42formal gates, actual Host completion or provider qualification.',
  'The five original audit false entries reflect default reporter recognition only; preserved original audit exit0 and separate correction388checks0failed provide the precise interpretation.'
 ],'source_acceptance':False,'main_integration_acceptance':False,'formal_acceptance_increment':0,'actual_registration_executed':False}
put('source_review.json',review)
files=[ref(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in ['manifest.json','handoff.json','seal.stdout.raw','seal.stderr.raw']]
put('manifest.json',{'schema':'researchos.independent-receipt-manifest.v1','root':str(O),'files':files,'listed_count':len(files),'excludes':['manifest.json','handoff.json','seal.stdout.raw','seal.stderr.raw'],'immutable_inputs_only':True})
put('handoff.json',{'schema':'researchos.independent-review-handoff.v1','decision':'REQUEST_CHANGES','reviewer':'codex:/root/w05_merge_review',
 'review_ref':ref(O/'source_review.json'),'manifest_ref':ref(O/'manifest.json'),'counterexamples_ref':ref(O/'proposed-counterexamples.NOT_RUN.json'),
 'diagnostics_ref':ref(O/'diagnostics.json'),'author_source_commit':handoff['source_commit'],'author_evidence_head':'0f708eaf0c624fb721f7c9a00d5465ef5f13a68c',
 'findings':['W13-SR-01 P1 concurrent ACK lifecycle barrier','W13-SR-02 P2 exact private packet/types and JSON whitespace'],
 'new_actual_nonzero_failure_origins':[],'new_product_execution':False,'source_or_canonical_changes':False,'source_acceptance':False,'formal_increment':0})
print(json.dumps({'review':ref(O/'source_review.json'),'manifest':ref(O/'manifest.json'),'handoff':ref(O/'handoff.json'),'listed':len(files)},ensure_ascii=False))
