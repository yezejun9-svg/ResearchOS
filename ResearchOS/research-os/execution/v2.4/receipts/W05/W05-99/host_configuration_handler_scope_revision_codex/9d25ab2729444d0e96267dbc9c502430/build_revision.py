import pathlib, json, hashlib, datetime, subprocess, sys, copy, re
R=pathlib.Path('D:/作品集/ResearchOS/research-os'); O=pathlib.Path(__file__).resolve().parent
B=R/'execution/v2.4/receipts/W05/W05-99'; P=B/'host_configuration_handler_scope_revision_codex/8f972b92afae45c5ac96ca679d623975'
D=B/'integration_codex/handler-interface-decisions-r286/interface_decisions.json'
V=B/'host_configuration_handler_scope_independent_review_codex/639403fd-baf9-41d5-8568-3568300f9e11/scope_review.json'
def sha(b): return hashlib.sha256(b).hexdigest()
def ref(p): return {'path':p.relative_to(R).as_posix(),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def put(n,x):
 p=O/n; p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f: f.write(x if isinstance(x,bytes) else (json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
 return ref(p)
started=now(); calls=[]
def call(n,args,cwd=R):
 a=now(); q=subprocess.run(args,cwd=cwd,capture_output=True)
 calls.append({'actualargv':args,'cwd':str(cwd),'started_at':a,'ended_at':now(),'exit':q.returncode,'stdout_ref':put('raw/'+n+'.stdout',q.stdout),'stderr_ref':put('raw/'+n+'.stderr',q.stderr)})
 return q
assert sha(D.read_bytes())=='b9a60230076710dd1907572fea5095d23c28a0ce6bb137df101fdb4bf70d7ff9'
assert sha(V.read_bytes())=='91c8f8aaa9739f09bf067678d196cc170c77f07eee481a40e8ffce8000b4ae90'
decision=json.loads(D.read_bytes()); review=json.loads(V.read_bytes()); proposal=json.loads((P/'scope_proposal.json').read_bytes()); matrix=json.loads((P/'case_matrix30.json').read_bytes())
head=call('main-head',['git','rev-parse','HEAD']).stdout.decode().strip()
call('main-tracked-before',['git','status','--short','--untracked-files=no'])
call('protected-wt-before',['git','status','--short','--untracked-files=no'],R/'.local/worktrees/codex-w0599-host-configuration-upgrade')
files=call('actual-test-files',['rg','--files','internal/domain','internal/api','internal/host','apps/cli','tests/runtime']).stdout.decode().splitlines()
testpaths=[s.replace('\\','/') for s in files if s.endswith('_test.go')]
call('test-contract-occurrences',['rg','-n','authenticated_principal_ref|host\\.status|host\\.configure|principal:|idempotency.*headers','internal/domain','internal/api','internal/host','apps/cli','tests/runtime','--glob','*.go'])
call('execute-callers',['rg','-n','Execute\\(|ClientService\\{|DecodeEnvelope|func Test','internal/domain','internal/api','--glob','*test.go'])
entries=[]; seen=set()
def capture(path,group='main',rel=None,prior=None):
 p=pathlib.Path(path); rel=rel or p.relative_to(R).as_posix(); k=(group,rel)
 if k in seen:return
 seen.add(k); b=p.read_bytes(); s=put('snapshots/'+group+'/'+rel,b)
 entries.append({'group':group,'path':rel,'original_absolute':str(p),'sha256':sha(b),'bytes':len(b),'snapshot_ref':s,'equal_prior':None if prior is None else sha(b)==prior})
for e in json.loads((P/'input.before.json').read_bytes())['entries']:capture(e['original_absolute'],e['group'],e['path'],e['sha256'])
for p in [D,V,P/'scope_proposal.json',P/'case_matrix30.json']:capture(p,'evidence')
extra=['internal/domain/backup_host_configuration_test.go','internal/domain/http.go','internal/canonical/jcs.go','internal/domain/backup.go','migrations/sqlite/0002_domain.sql']
for p in extra+testpaths:capture(R/p)
before=put('input.before.json',{'at':now(),'entries':entries,'scope':'Public repository source/tests and frozen contracts only. Tests captured as potential-impact inventory, not executed.'})
index={e['path']:e for e in entries if e['group']=='main'}
def ev(p,a,z):
 e=index[p]; lines=(R/p).read_text(encoding='utf8').splitlines(); assert 0<a<=z<=len(lines)
 return {**e['snapshot_ref'],'locator':{'lines':[a,z]}}
scope=copy.deepcopy(review['proposed_exact18'])
for s in scope:
 p=R/s['path']; s['implementation_authorized']=False; s['expected_absent']=not p.exists()
 if p.exists():
  old=s.get('source_before'); assert old is None or old['sha256']==sha(p.read_bytes())
  s['source_before']=ref(p)
 else:s['source_before']=None
 if 'bounds' in s:s['allowed_function_boundaries']=[s.pop('bounds')]
scope[0]['allowed_function_boundaries']+=['Retain a defensive copy of original DecodeEnvelope bytes; new sole journal INSERT gets private exact-base64 record. No reconstructed raw fallback. Existing session-scoped goal.start gets this Session causal-binding check before protected goal handler; no current-head authorization for existing Session.']
scope[3]['allowed_function_boundaries']+=['Private bounded canonical three-key header writer/strict reader; decoded exact original request validates existing ContentHash against identity and sole journal; same helper for replay and backup. New malformed records fail; old empty/unrelated headers follow old rules, no backfill.']
put('exact18.source_before.json',scope)
record=copy.deepcopy(review['private_original_request_record'])
record['writer_serialization']='UTF-8 compact JSON, exact key order schema,encoding,raw_envelope_base64; no whitespace/newline. Fixed literal first two string values and standard padded base64 third value. Reader strict-decodes then regenerates identical serialization and compares full bytes; this private format does not replace Envelope.ContentHash canonicalization.'
record['fixed_empty_record']='{"schema":"researchos.private-command-envelope.v1","encoding":"base64","raw_envelope_base64":""}'
assert len(record['fixed_empty_record'].encode())==96
record['raw_retention']='Unexported immutable []byte copy on Envelope from actual DecodeEnvelope input; typed helper decoder retains input likewise. Execute refuses missing or changed original raw for new records. Never Marshal RawMessage/map/Envelope and call the result original bytes.'
record['equivalent_retry']='Whitespace/key-order equivalent valid retry may have same existing ContentHash. Replay returns original response and preserves FIRST raw/base64/header/timestamp bytes; no equality-to-retry-raw requirement, no update.'
record['legacy_rules']='Empty or unrelated preexisting headers retain original strict legacy reader; no missing-Session exception. Recognized private-schema malformed record is corruption, not legacy. Existing historical host.configure can still reconstruct its already-supported scope/payload proof with original strict logic. Removing a new header never creates an exemption.'
record['http_isolation']='v2 response path returns typed body only; never emit stored private headers. Keep v1 HTTP replay headers/operation namespace byte behavior. Test v2 fresh+replay response headers for absence and existing v1 headers for preservation.'
record['evidence']=[ev('internal/domain/backup_host_configuration.go',207,253),ev('internal/domain/client_command_identity.go',140,186),ev('internal/domain/client_protocol.go',791,800),ev('migrations/sqlite/0002_domain.sql',31,36),ev('internal/domain/http.go',215,235)]
endpoint=proposal['endpoint_policy']; endpoint.pop('root_policy_pending_edge_spelling',None)
endpoint['lexical_decisions']={
 'scheme':'Require literal lowercase https:// prefix and url.Parse absolute https scheme/nonempty authority; reject opaque URL, backslash/control/space, userinfo, query even lone ?, fragment even lone #.',
 'host':'ASCII DNS hostname spelling/case preserved; host case-insensitive comparison may validate hostname identity but cannot rewrite original baseURL or relax exact profile endpoint binding. Valid IPv4 and localhost-style ASCII host accepted with HTTPS. Unicode IDN refused because no pinned conversion dependency; preencoded valid ASCII xn-- hostname accepted without DNS/network lookup.',
 'port':'Absent allowed; present must be nonempty ASCII decimal digits and numeric1..65535 (no sign). Preserve supplied digits including leading zeros; do not infer/rewrite explicit443 into absent port.',
 'ipv6':'IPv6 only bracketed and parseable by net.ParseIP; optional valid numeric port. Reject unbracketed literal, malformed brackets, zone identifiers including %25zone; no DNS or address reachability probe. Preserve valid input IPv6 spelling, no address rewrite.',
 'path':'Root/empty or unencoded normal segments and at most one trailing slash. Reject raw percent escape/RawPath, dot or dotdot segment, double slash, backslash and control/space. Reject case-insensitive final /chat/completions with optional trailing slash. No host/base/path normalization.',
 'derive':'Trim exactly one accepted trailing slash then append /chat/completions. Config stores original baseURL; runtime profile endpoint must equal this derived string byte-for-byte.'}
endpoint['positive_examples']=['https://fixture.invalid','https://Fixture.INVALID/','https://fixture.invalid/v1/','https://fixture.invalid:443/v1','https://fixture.invalid:00443/v1','https://127.0.0.1:8443/v1','https://[::1]:8443/v1','https://xn--bcher-kva.example/v1']
endpoint['negative_examples']=['HTTPS://fixture.invalid','http://fixture.invalid','https://fixture.invalid:','https://fixture.invalid:0','https://fixture.invalid:65536','https://fixture.invalid:+443','https://::1/v1','https://[fe80::1%25eth0]/v1','https://书.example/v1','https://user@fixture.invalid/v1','https://fixture.invalid/v1?','https://fixture.invalid/v1#','https://fixture.invalid/v1//','https://fixture.invalid/%76%31','https://fixture.invalid/a/../v1','https://fixture.invalid/CHAT/Completions/']
prov=proposal['session_provenance']; prov.pop('explicit_open_context_gate',None)
prov['PC01']=copy.deepcopy(review['PC01_caller_scope_decision'])
prov['PC01']['status']='ROOT_DECIDED_BRANCH_REFUSAL_NOT_GLOBAL_HANDLER_BLOCKER'
prov['PC01']['required_behavior']=decision['pc01_legacy']
prov['PC01']['explicit_refusal']='Known unproved old draft/noRun execution or new valid but unavailable head returns MODEL_UNAVAILABLE before MODEL/effect dispatch; known-typed corrupt/missing history refuses, never legacy fallback. Read/exact old replay remains; explicit rebind creates future typed authority only.'
prov['existing_goal_guard']='In owned client_protocol.go dispatch, before invoking protected startClientGoal for an existing scoped Session, validate that exact Session/principal/original creation/binding provenance. sessionModel(project,ref) remains a resolver; another Session with same ref proves nothing for this Session.'
transaction=proposal['transaction_order']
transaction[0]['action']+='; raw must be retained, complete and strict, before normalization. Decode/schema/auth errors produce no reserved identity.'
transaction[4]['action']+='; new journal.headers is the fixed private original-byte record. Recompute existing normalized ContentHash and validate derived SID only after original session/journal durable facts exist in callerTx.'
transaction[5]['guard']+='; legal unknown/cross-project SID REJECTED keeps requested SID and full original request header. Only backup Session existence check is exempt after complete proof; successful/ACK paths stay strict.'
counter=matrix['counter_profiles']; counter['LEGAL_REJECTED']['headers']='one private canonical raw record in that original journal; no extra row/table'; counter['EXACT_REPLAY']['headers']='first stored raw/header/time/body/status unchanged even semantically equivalent JSON retry'
augment={
 'C02':['Header outer exact three keys/stringtypes/version/encoding/UTF8/duplicate/unknown strict; byte ceiling1398200 BEFORE parsing, base64chars1398104, raw1..1048576. Exact compact regeneration; reject CRLF/URL-safe/unpadded/excesspad/nonzero tailbits/escapealiases.','Original JSON spacing/key order retained as bytes, semantically equivalent requests keep original ContentHash and first original header; altered payload/scope/client changes ContentHash. Never use rawSHA as protocolhash.'],
 'C03':['New firstheader/body/status/timestamp byte-identical after exact/equivalentJSON retry and restart; legacy prefixedstatus/emptyheader replay adds0identity and writes0header.'],
 'C04':['Original raw field mutation client/SID/project/command/method/payload vs unchanged hashes rejected; entire principal+command original namespace scanned; old crosslocator ambiguity no sorted winner.'],
 'C05':['Failure before/after headers INSERT and commit deferredFK preserves full outer rollback; authenticated legal unknownSID/crossprojectSID rejection commits identity1+journal1 only, all business0. Schema/IO errors all0.'],
 'C08':['Unknown Session and other-project real Session rejected with ORIGINAL requestSID retained. Their new private request record validates yet grants no Session/owner authority.'],
 'C09':['Explicit legacy rebind requires real creationprincipal/OWNER/workspace/currentwriter/lease/CAS and full actual settled state. Older associated UNKNOWN effects, pending Task/noRun, pendingqueue/control/permissions block. Empty draft/noTask distinguished.'],
 'C12':['DerivedSID exception only successful session.create after sameTx actual unique creationjournal/project/principal/realSession. REJECTED create keeps null requestedSID.'],
 'C13':['goal.start project request/response topSIDnull; nested successful real Session creation verified. Existing-session goal retains requestSID; cannot borrow sharedref Session proof.'],
 'C14':['Anchored legacy vs unanchored olddraft/noRun vs known-typed missing/corrupt row tested separately. Unanchored read/replay unchanged, execution MODEL_UNAVAILABLE; corrupttyped never rescued by rebind/legacy fallback that conceals history corruption.'],
 'C15':['Authorized explicit legacy unanchored->typed scopedconfigure succeeds only genuinecreation/workspace/settlement/CAS; later execute needs actualqualification; never rewrites oldprofile/Task/UNKNOWN/history.'],
 'C16':['New project default validhead selects exacttypedref; nullcredential/unqualified head MODEL_UNAVAILABLE and0legacyfallthrough. True nohead original route selection preserved; newly created noRun draft cannot later execute by treating currenthead as historicalproof.'],
 'C18':['Existing session-scoped goal.start through owned dispatch proves exact Session, not anotherSession sharingref; current profile/route hash exact and ordinary admission unchanged.'],
 'C22':['Run every endpoint positive/negative example and exact derivedbytes above; include port1/65535, empty/sign/nonnumeric, IPv6zone/brackets, UnicodeIDN vs ASCII punycode; network0.'],
 'C23':['All 0/1/99/100/101/201 histories; unselected corruptold row must refuse before head+99 projection; newrawprincipal identity vs oldprefixed unlinkedreplay.'],
 'C24':['Oldref beyond100 stays authorized exactref readable/selectable where otherwise valid; bounded status does not prune stored rows or claim fullhistoryAPI.'],
 'C25':['v2 fresh/replay never exports private stored headers; originalv1responseheaders unchanged and namespace-separated. Old unrelated/emptyheader retains stricter legacy behavior.'],
 'C26':['Actual public CreateBackup->isolated Restore->exact replay->rebackup of default/scoped/nonconfignewrecords, legal unknownSID/crossprojectSID rejection and full201history. Preserve original header/raw/SID/body/status/timestamp and historicalfences; no direct SQL copy counts as publicroundtrip.'],
 'C27':['On separate copies alter savedrequestSID/client/project/method/command/payload, raw/header/identity/journal hashes, responseSID or Status; strictreject. REJECTED lacking validnewrecord gets noSessionexception; COMPLETED/ACKNOWLEDGED/derivedcreate without actualSession alwaysreject. No claim protection against wholesale adversarial rewrite of alltrustedrows.'],
 'C29':['Existing CANCEL ACK exactreplay still enters original finalizer; no earlyglobalreturn. Original1811 remains open; no F08 repairedclaim; originalheader/body unchanged unless original authorized finalize succeeds.'],
 'C30':['Exact18 implementation then fresh focused+oldregressions+publicbackup+compiledclosure; prior444 not inherited. Preserve unknown deletes/oldfails; only old test608-613 presently in scope. Additional fixture findings below require separate scope before edits.']}
for c in matrix['cases']:
 c['exact18_additions']=augment.get(c['id'],[])
 if c['id']=='C14':c['precise_cases']=[x.replace('legacy originalprofile anchorabsent markedPC01 branchblocked','legacy originalprofile anchorabsent explicitly execution-refused; read/replay/rebind rules retained') for x in c['precise_cases']]
 if c['id']=='C16':c['precise_cases']=[x.replace('legacydraft PC01 separatelyreported, not silentlycountedclosed','legacydraft PC01 Root-approved missing-anchor execution refusal, no fabricated history') for x in c['precise_cases']]
 if c['id']=='C30':c['precise_cases']=[x.replace('exact16sources','exact18sources') for x in c['precise_cases']]
matrix['schema']='researchos.host-config.handler-case-matrix.v2';matrix['endpoint_policy']=endpoint
matrix['independent_findings_ref']=ref(V);matrix['root_decision_ref']=ref(D)
matrix['coverage_note']='30 primary case groups, expanded subcases. Design expectations only; no test result or source acceptance.'
matrix['final_scope_note']='Root requested potential old fixture inventory after initial18 design: final proposal is18 handler/backup paths plus9 precise test-only fixture paths (27 total), all pending nonauthor review/Root registration. C30 uses final27; earlier exact18 references identify the core handler/backup subset only.'
put('case_matrix30.json',matrix)
impacts=[
 {'path':'internal/domain/client_configuration_test.go','function':'TestClientConfigurationStrictPayloadAndUnwiredSession','lines':[608,613],'classification':'EXACT18_ALREADY_PROPOSED_OLD_ASSERTION','old':'Public default all-null host.configure Decode expected refusal while unwired','new':'All-null valid payload Decode succeeds; new separate nilauthority handler refusal. Preserve every other byte/assertion.'},
 {'path':'internal/domain/client_protocol_atomic_test.go','function':'TestClientTypedRejectionRollsBackBusinessWrites','lines':[30,34],'classification':'ADDITIONAL_FIXTURE_SCOPE_NEEDED','old':'Doc:nil direct Envelope, no retained raw; tests post-write rejection and exact replay','new':'Same original assertions; initialize actual frozen SchemaDoc and Decode actual fully formed request bytes in test fixture. No production synthetic raw fallback.'},
 {'path':'internal/domain/client_protocol_control_windows_test.go','function':'TestClientCancelChangesCanonicalRun/TestClientSameWriterRenewsExpiredLease/TestClientResumeNeverRestartsPreviousRun','lines':[21,25],'classification':'ADDITIONAL_FIXTURE_SCOPE_NEEDED','old':'Direct Envelope->Execute at25/55/75/106, no retained original bytes; second call mutates CommandID','new':'Decode complete test bytes before each distinct command; preserve CANCEL/lease/RESUME and old1811 assertions. Re-decode after CommandID mutation; no stale retainedraw reuse.'},
 {'path':'internal/domain/client_transcript_test.go','function':'transcriptSend; TestClientTranscriptFullRecoveryAndBothProducers','lines':[65,67],'classification':'ADDITIONAL_FIXTURE_SCOPE_NEEDED','old':'Direct Envelope returned to Execute, immutable transcript assertions','new':'Fixture Decode actualbytes retaining full request; inspect send fixture missing legacyprofile separately, preserve all prefix/history/replay assertions.'},
 {'path':'internal/domain/client_workspace_test.go','function':'workspaceTestEnvelope/executeWorkspaceTest','lines':[120,131],'classification':'ADDITIONAL_FIXTURE_SCOPE_NEEDED','old':'Direct Envelope->Execute helper','new':'Decode original complete fixture request before Execute; all old workspace authority/physical I/O/replay/epoch assertions unchanged.'},
 {'path':'internal/domain/runtime_tool_integration_windows_test.go','function':'muClientCall','lines':[31,42],'classification':'ADDITIONAL_FIXTURE_SCOPE_NEEDED','old':'Direct caller Envelope->Execute helper shared by SDK tool/permission controls','new':'Decode complete bytes before Execute; preserve actual SDK/Task/profile provenance and all tool assertions; no fixture qualification promoted.'},
 {'path':'internal/domain/runtime_model_windows_test.go','function':'typed cancel branch of model broker cancel fixture','lines':[198,205],'classification':'ADDITIONAL_FIXTURE_SCOPE_NEEDED','old':'Direct typed CANCEL Envelope passed Execute without retainedraw','new':'Decode complete request in fixture branch; preserve actual model cancel/UNKNOWN effects and finalization open gate.'},
 {'path':'internal/api/v2_sessions_test.go','function':'newSessionHTTPFixture; TestW14SessionHTTPCreateSendEventsAndReplay','lines':[24,37],'classification':'POTENTIAL_PROVENANCE_FIXTURE_CONFLICT_NOT_EXECUTED','old':'model-test custom port has no original frozen config/profile proof; send148-180 expects real BLOCKED Task +4events','new':'Need scoped test fixture establishment of legitimate original typedconfig/creation chain if stricter execution gate makes this obsolete; retain all original send/Task/event/replay assertions. Do not grant trust to label/portboolean.'},
 {'path':'internal/domain/client_protocol_history_test.go','function':'sendHistoryTurn','lines':[31,48],'classification':'POTENTIAL_INTERNAL_HELPER_PROVENANCE_IMPACT','old':'Direct sendClientMessage bypasses Execute, synthetic Session/model fixture','new':'Audit under new exact Session provenance; no automatic edit. If legitimate anchored fixture required, propose helper-only changes preserving all recovery assertions.'},
 {'path':'internal/domain/runtime_sessions_windows_test.go','function':'nextSessionTurn/sessionProjectionMapping','lines':[22,54],'classification':'POTENTIAL_INTERNAL_HELPER_PROVENANCE_IMPACT','old':'Synthetic Session mapping + direct send helper','new':'Same as history fixture; original actual Task/Runprofile may supply valid anchor, inspect exact causal link rather than assume failure.'},
 {'path':'internal/domain/runtime_session_events_windows_test.go','function':'TestW05RuntimeEventBrokerBeforeIOAndRollback','lines':[474,478],'classification':'POTENTIAL_DIRECT_ENVELOPE_CALLER','old':'ClientService direct fixture call inside actual broker control','new':'Inspect actual command helper origin; if retainedraw absent, smallest fixture Decode with old event/billing assertions preserved.'},
 {'path':'internal/domain/backup_configuration_upgrade_test.go','function':'configurationUpgradeCommand/configurationUpgradeFixture','lines':[117,141],'classification':'PROVENANCE_AND_BACKUP_REGRESSION_REQUIRED','old':'Decode exists; storage-only runtime port with no qualification; fixture legacy draft/Task behavior','new':'Keep source22->23 guards/sourcebinary/rollback all unchanged; raw retention should propagate. Missing anchor branch potential only; any fixture adjustment separately registered.'}
]
for i in impacts:i['source_ref']=ref(R/i['path']);i['evidence']=ev(i['path'],*i['lines']);i['authorized_to_edit_now']=False
impact={'status':'STATIC_POTENTIAL_IMPACT_ONLY_NO_TEST_EXECUTION','items':impacts,'additional_path_count':11,'not_found':'internal/domain/client_protocol_test.go does not exist in actual rg inventory; do not invent this path.','other_search_findings':['No literal new host.status principal: expectation found in actual domain/API/Host tests. Backup fixture rawprincipal already compatible; old emptyheader config fixtures deliberately remain supported by legacy rules.','CLI doctor/read fixtures have their own legal typed host.status responses and do not assert production prefixed principal. CLI contract host.configure mocked payload remains independently frozen; do not change it here.','Goal command helper already calls DecodeEnvelope. Project draft/nohead original creation stays supported; existing-session goal new guard may reveal missinganchor fixtures, not permission to change protected goal tests.','Queue command helper and shared muClientCall usage must be traced; call graph listing preserved. No broad alltests rewrite authorized.'],'policy':'Exact18 production/design scope remains proposed; identified fixture-only amendments are separately reviewable and NOT silently added. Do not weaken new public strictraw, schema, origin or profile gates to keep obsolete fixture green; do not delete/relax old assertions.'}
impact['items']=[i for i in impact['items'] if i['path']!='internal/domain/runtime_session_events_windows_test.go']
impact['other_search_findings'].append('runtime_session_events_windows_test.go:475 uses muClientCall; its strict Decode fix is inherited from runtime_tool_integration_windows_test.go. No event test source edit needed. Internal direct send helpers remain unit fixtures; source enforcement must be at authorized public/session-context and actual runtime boundaries, not classify unitmock labels as historical production proof.')
fixture_scopes=[
 ('internal/domain/client_protocol_atomic_test.go','TestClientTypedRejectionRollsBackBusinessWrites plus rejectingClientPort',[11,51],'Replace request fixture with legitimate typed configure+offline Session through actual Execute using explicit metadata unit port and original journal; then session.send execution ValidateBinding writes probe and returns typed MODEL_UNAVAILABLE. Observe portcall1 and successful intermediate INSERT/count1 in callerTx, eventual business/probe0, identity+journal1 for refused command, replay same/no second port call. Preserve every original rollback/replay/rows assertion. NORMAL AdmitTurn refusal is COMPLETED/BLOCKED and is NOT this rejection stimulus. No production callback/offline runtime dependency. Add Doc+Decode before every new command. Any fixture import addition solely needed by this setup.'),
 ('internal/domain/client_protocol_control_windows_test.go','TestClientCancelChangesCanonicalRun, TestClientSameWriterRenewsExpiredLease, TestClientResumeNeverRestartsPreviousRun',[11,106],'Decode original full fixture bytes immediately before each Execute; second mutated CommandID re-decodes separately. Preserve original control/lease/replay/UNKNOWN/Run/outbox assertions and existing finalization failure. No new scope of cancellation behavior.'),
 ('internal/domain/client_transcript_test.go','transcriptSend (all callers inherit)',[59,68],'Return strict Decode of complete generated fixture bytes with original request retained; preserve every caller transcript/prefix/recovery/rollback assertion. No forged profile/Session provenance; unit fixture evidence remains synthetic.'),
 ('internal/domain/client_workspace_test.go','executeWorkspaceTest (all callers inherit)',[123,132],'Strict Decode of complete request bytes before callerTx Execute; fields mutated by caller are serialized BEFORE Decode. Preserve all physical I/O, authorization, replay/epoch, output artifact assertions.'),
 ('internal/domain/runtime_tool_integration_windows_test.go','muClientCall (all SDK tool/permission/event callers inherit)',[31,42],'Strict Decode full request fixture bytes immediately before Execute; retain existing actual qualification/profile/effect inputs and all downstream assertions. No own method-specific production bypass.'),
 ('internal/domain/runtime_model_windows_test.go','runtimeMuCancelStopsTransport typed branch only',[198,212],'Strict Decode the existing typed CANCEL request before Execute, keep all actual transport/UNKNOWN/ACK/cost assertions; no worker/model control change.'),
 ('internal/domain/runtime_permission_windows_test.go','runtimePermissionToolCycle stale permission.respond branch only',[320,335],'Strict Decode stale request bytes before Execute; preserve original refusal and physicalWrites assertions. Other calls inherit muClientCall; no permission policy change.'),
 ('internal/domain/client_command_queue_test.go','TestClientQueueEnqueueCommitBoundary only direct Execute setup',[124,136],'Decode queueClientEnvelope complete bytes locally before direct Execute. Existing goalCommand callers already decode and remain untouched. Preserve actual transaction rollback, queue, original effect/receipt assertions.'),
 ('internal/api/v2_sessions_test.go','newSessionHTTPFixture/sessionHTTPFixture.create + fixture model-ref member and sessionBindingFixture input expectation',[24,134],'Use owned new v2_configuration_windows_test.go test helper with actual temporary Host/SID/stableDir, legitimate bound OWNER and real metadata-only composition. Via authenticated /v2/command host.configure credential=null obtain immutable typed ref and original identity/journal; store returnedref in fixture and use exactref in create and binding-port equality. No rawSQL fake config/journal, no credential decrypt/network/qualification. Retain all original send Task/BLOCKED/noRun/four-events/replay/writer/permission assertions. Runtime fixture AdmitTurn remains explicit unqualified RESOURCE_UNAVAILABLE; no model-test-prefix exemption.')]
fixture_rows=[]
for p,fn,span,bound in fixture_scopes:
 fixture_rows.append({'path':p,'action':'MODIFY_TEST_ONLY','source_before':ref(R/p),'expected_absent':False,'allowed_function_boundaries':[fn+': '+bound],'original_locator':ev(p,*span),'assertion_protection':'No original assertion deleted, relaxed or relabeled. Minimal setup/helper/import edits only; exact before/after diff reviewed. No production authority established by synthetic unit metadata ports.','implementation_authorized':False})
assert len(fixture_rows)==9
scope+=fixture_rows
put('exact27.source_before.json',scope)
impact['additional_path_count']=9; impact['exact_test_only_scope']=fixture_rows
impact['atomic_causal_refinement']=fixture_rows[0]
impact['status']='PROPOSED_18_PLUS_9_TEST_FIXTURE_PATHS_PENDING_NONAUTHOR_REVIEW_NO_TEST_EXECUTION'
for i in impact['items']:
 for f in fixture_rows:
  if i['path']==f['path']:
   i['classification']='PROPOSED_TEST_ONLY_AMENDMENT_PENDING_REVIEW';i['new']=f['allowed_function_boundaries'][0]
put('potential_test_impacts.json',impact)
mapping=[{'finding':f['id'],'resolution':'exact18 backup strict original request + status-specific Sessionproof' if f['id']=='HCFG-SCOPE-01' else 'private bounded solejournal headers with original ContentHash; canonical outer writer and exact Base64 reader' if f['id']=='HCFG-SCOPE-02' else 'Root decided missing-anchor execution refusal; original reads/replay and authorized future typed rebind; scoped goal dispatch guard','cases': ['C05','C08','C26','C27'] if f['id']=='HCFG-SCOPE-01' else ['C02','C03','C04','C05','C12','C13','C25','C29'] if f['id']=='HCFG-SCOPE-02' else ['C09','C14','C15','C16','C18']} for f in review['findings']]
proposal.update({'schema':'researchos.host-config-handler.exact18-scope-proposal.v3','status':'PROPOSED_EXACT18_PENDING_NONAUTHOR_REVIEW_WITH_EXPLICIT_FIXTURE_SCOPE_GAPS','created_at':now(),'source_main_head':head,'source_before_ref':before,'prior_exact16_proposal_ref':ref(P/'scope_proposal.json'),'root_decision_ref':ref(D),'independent_exact16_findings_ref':ref(V),'exact_source_count':18,'exact_scope':scope,'original_request_record':record,'session_provenance':prov,'endpoint_policy':endpoint,'case_matrix_ref':ref(O/'case_matrix30.json'),'potential_test_impacts_ref':ref(O/'potential_test_impacts.json'),'finding_resolution':mapping})
proposal.pop('root_decision_record_ref',None)
proposal['protected_paths']=[x for x in proposal['protected_paths'] if x!='internal/domain/backup_host_configuration.go']
proposal['implementation_order']=[
 '1 Independent nonauthor reviews THIS18 revision and explicit fixture impacts; Root registers exactsource lease in freshWT. No implementation authorized by this proposal. Fixture changes outside18 need separate precise registration before edits.',
 '2 Implement common metadata authority/endpoint parser, Host metadata-only adapter and two actual composition points. No credentials open/DPAPI decrypt/qualification/network.',
 '3 Strict retain actual raw, global lookup before CAS, sameTx identity reservation before business savepoint, fixed privateheader writer/reader and original response validation. Exactlegacy replay skips reservation; preserve original ACK finalizer route.',
 '4 Foundation defaultwrapper/scoped staging/read proof + public configure/status. Atomic config/head/Session CAS and typedrejection counters; header validation and backup status-specific Sessionproof land together before candidate publicroundtrip.',
 '5 Offline create, exact Sessiontyped/legacy provenance, owned existing goal dispatch and runtime Task-context checks; currenthead projectGoal behavior and strict unavailablehead refusal. Missing PC01anchor execution refuses without changing reads/history.',
 '6 Add30 expandedcontrols + only registered oldfixture amendments. Execute legalreject publicbackup/restore/replay/rebackup, raw/hash tamper, base64bounds, 201history, rollback/concurrency and unchanged22->23/oldjournalguards.',
 '7 Fresh actual focused/full relevantregression with complete source/tool/compiled closure before-after-current, source diffbounds (608-613 exact), closedfixtureDBs/raw/failureorigin. Freeze candidate, no selfacceptance.',
 '8 Nonauthor SOURCE review then Root serialintegration/currentchecks. F08 only after handler owner releases shared client_protocol.go; schema24/provider/CLI UX remain separate.']
proposal['limits']=['Exact18 is proposed scope, not source acceptance/execution authorization. Additional old-fixture setup paths identified in potential_test_impacts require explicit review/registration; no allgreen claim before actual implementation/regression.','PC01 is an explicit Root compatibility decision: original read/history/replay preserved, unproved binding execution refuses; not global handler blocker. No synthetic anchor.','Existing SQL0002/0023, schemas, migrations, original1811 and all protected old asserts stay immutable except specifically registered testspan.','Integrity checks are internal relational provenance, not tamperproof protection against adversarial rewriting all trusted DB rows.','No external/provider/MODEL/nativequalification proof is performed by this design or by local save.']
proposal['schema']='researchos.host-config-handler.exact27-scope-proposal.v3'
proposal['status']='PROPOSED_EXACT27_18_HANDLER_BACKUP_PLUS_9_FIXTURE_PATHS_PENDING_NONAUTHOR_REVIEW'
proposal['exact_source_count']=27;proposal['base_handler_backup_scope_count']=18;proposal['additional_test_only_scope_count']=9
proposal['exact_scope']=scope
proposal['scope_evolution']='Original16 + Root backup2 =18. Subsequent Root request to inventory obsolete fixtures produced9 exact existing test-only paths. All27 are proposed, not authorized source edits. Lower-level unit helpers/protected goal/upgrade/event tests remain outside changes and are regression inputs.'
proposal['implementation_order']=[s.replace('THIS18 revision','THIS27 revision (18 handler/backup +9 test-only)').replace('Fixture changes outside18 need separate precise registration before edits.','The9 fixture paths require explicit nonauthor review and Root registration with the18; any additional path needs another exact amendment.') for s in proposal['implementation_order']]
proposal['limits'][0]='All27 paths await nonauthor scope review and Root registration.9 additional test-only paths have exact function/line bounds; no allgreen claim before actual implementation/regression. Any newly discovered affected helper outside27 requires narrow reviewed amendment.'
proposal['atomic_rollback_fixture_causality']=fixture_rows[0]
put('scope_proposal.json',proposal)
put('lookup_diagnostics.json',{'product_failures':0,'tool_read_diagnostics':[{'tool_chunk':'314a43','exit':1,'reason':'PowerShell literal rg input internal/domain/*test.go invalid Windows path; partial other-directory search returned; corrected actual directory + --glob search ceec33 exit0.'},{'tool_chunk':'12a8cc','exit':1,'reason':'Root-suggested client_protocol_test.go actual nonexistent; rg --files38e58f confirmed actual filenames; other named files read successfully.'}],'prior_lookup_diagnostics_preserved':['da8654','f27297'],'no_counters_reset':True})
after=[]
for e in entries:
 b=pathlib.Path(e['original_absolute']).read_bytes();after.append({'group':e['group'],'path':e['path'],'sha256':sha(b),'same':sha(b)==e['sha256']})
assert all(x['same'] for x in after)
put('input.after.json',{'at':now(),'entries':after,'drift':0})
call('main-tracked-after',['git','status','--short','--untracked-files=no'])
call('protected-wt-after',['git','status','--short','--untracked-files=no'],R/'.local/worktrees/codex-w0599-host-configuration-upgrade')
put('actual_invocations.json',{'started_at':started,'ended_at':now(),'actualargv':[sys.executable,*sys.orig_argv[1:]],'cwd':str(pathlib.Path.cwd()),'calls':calls,'product_tests':0,'sql':0,'HTTP':0,'worker':0,'MODEL':0,'private_reads':0,'source_mutations':0,'state_mutations':0})
put('handoff.json',{'status':proposal['status'],'author_id':'codex:/root/sources_parent_impl','proposal_ref':ref(O/'scope_proposal.json'),'case_matrix_ref':ref(O/'case_matrix30.json'),'test_impacts_ref':ref(O/'potential_test_impacts.json'),'root_decision_ref':ref(D),'independent_findings_ref':ref(V),'source_before_ref':before,'source_after_ref':ref(O/'input.after.json'),'exact_paths':27,'handler_backup_paths':18,'test_only_extra_paths':9,'primary_case_groups':30,'public_input_count':len(entries),'drift':0,'remaining_gate':'Nonauthor revised27 scope review including9 exact fixture paths, then Root registration/freshWT. No sourceacceptance.','tests':0,'new_product_failures':0,'formal_increment':0})
put('manifest.json',{'schema':'researchos.receipt-manifest.v1','files':[ref(p) for p in sorted(O.rglob('*')) if p.is_file()],'excludes_self':True})
print(json.dumps({k:ref(O/k) for k in ['scope_proposal.json','case_matrix30.json','potential_test_impacts.json','handoff.json','manifest.json']},ensure_ascii=False))
