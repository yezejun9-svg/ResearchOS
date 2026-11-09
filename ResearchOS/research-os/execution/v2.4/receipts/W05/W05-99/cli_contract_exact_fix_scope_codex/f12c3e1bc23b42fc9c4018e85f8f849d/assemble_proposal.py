"""Readonly source/hash assembly. Does not execute product, SQL or tests."""
from pathlib import Path
import hashlib, json, re, subprocess, datetime

M=Path('D:/作品集/ResearchOS/research-os')
B=M/'execution/v2.4/receipts/W05/W05-99'
N=B/'cli_contract_exact_fix_scope_codex/f12c3e1bc23b42fc9c4018e85f8f849d'
I=B/'cli_contract_diagnostic_independent_review_codex/735595fc3d59460cab80916fbd7e2b54'
W=M/'.local/worktrees/codex-w0599-host-configuration-handler'
D=B/'cli_contract_failure_diagnostic_codex/92448a208996455da289e7682304296a'
COMMIT='22752a6a41732c8c158d7d7e1b8932ec958f8cb8'
def h(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def ref(p,loc=None):
 d={'path':str(p),'sha256':h(p.read_bytes()),'bytes':p.stat().st_size}
 if loc is not None:d['locator']=loc
 return d
def save(name,o):
 p=N/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(o,f,ensure_ascii=False,indent=2);f.write('\n')
 return ref(p)
assert h((I/'source_review.json').read_bytes())=='9a7fcc685afb2f3412be02cd72b1a921b8294e5afee9d5780a17efe785635805'
assert h((I/'scope_proposal.json').read_bytes())=='a8da795cdde9275899484ef51085278aec3bd18944863f4153b3eeb4a5e2d3d4'
paths=['apps/cli/cli_verbs.go','apps/cli/cli_v2.go','apps/cli/cli_stream.go','apps/cli/cli_sessions_test.go','apps/cli/cli_stream_test.go','tests/runtime/cli_contract/main.go','tests/runtime/cli_contract/v2verbs.go','apps/cli/cli_http_status_test.go']
extra=['apps/cli/cli_contract.go','apps/cli/cli_read_interrupt_test.go','apps/cli/cli_continuation_test.go','internal/domain/client_protocol.go','internal/api/contracts/client.protocol.schema.json','internal/api/contracts/domain.schema.json']
inputs=list(read(N/'inputs.before.json'))
for p in [D/'diagnostic_matrix.json',D/'capture_count_clarification.json',M/'AGENTS.md',M/'execution/project_identity.json']+[W/x for x in paths+extra]:
 if p.exists():inputs.append(ref(p))
save('inputs.assembly.before.json',inputs)
git=[];snap=[]
for rel in paths:
 p=W/rel;cp=subprocess.run(['git','show',COMMIT+':'+rel],cwd=M,capture_output=True)
 assert cp.returncode==0, (rel,cp.returncode)
 assert cp.stdout==p.read_bytes(),rel
 dst=N/'source_snapshots'/rel;dst.parent.mkdir(parents=True,exist_ok=True)
 with dst.open('xb') as f:f.write(cp.stdout)
 git.append({'path':rel,'source_ref':ref(p),'snapshot_ref':ref(dst),'git_argv':['git','show',COMMIT+':'+rel],'cwd':str(M),'exit':cp.returncode,'stdout_sha256':h(cp.stdout),'stderr':cp.stderr.decode('utf-8'),'git_blob_equals_frozen_worktree':True})
 snap.append(ref(dst))
save('frozen_source_binding.json',{'commit':COMMIT,'files':git,'scope':'8 proposed paths only; no clean-worktree or whole source acceptance claim'})

bounds=[
 ('apps/cli/cli_verbs.go',[(66,169),(224,321)],['verbSteps: interactive-origin create/get/attach sequencing only; resume target_id session branch remains P02 HOLD','cliInteractive: strict list failure classification, existing readonly attach before user writes, per-turn ownership preparation'],
  'No scanner/channel/multiline/slash/cancel-input regression; no implicit foreign-writer takeover. Do not change standalone run roster merely to satisfy interactive test.'),
 ('apps/cli/cli_v2.go',[(216,300),(304,367)],['v2Call/v2CallContext/transportWithCause: shared strict response validation; retain signatures and actual IO cause','adoptV2Snapshot: validate whole reply/snapshot then atomically adopt; adoptCLIGoal existing guards stay, only exact-number compatibility if necessary'],
  'v2EnvelopeFor configure branch118–198, protocol table, v2FlowCommandID and L01 HTTP/redirect/L02 IO cancellation precedence preserved. Add private validators in this file; domain.DecodeResponse is not the gate.'),
 ('apps/cli/cli_stream.go',[(96,111),(158,225),(241,244),(393,415),(483,504),(582,707),(759,780)],['cliFlow.call: ACK pending same original envelope, completed AttachResult barrier','cliInteger: exact json.Number integer support without weakening existing float guards','pages/followCLIExecution483–504: narrowly propagate typed-response exit1 instead of losing it in reason-only wrapper and remapping every error to3; valid resource/cursor recovery stays unchanged','runCLIVerb/summary: no write after attach ACK/invalid owner; no premature epoch reset; preserve valid prior context on later failure'],
  'No change to event consume/terminal Run+Task+artifact/children/queue proof, active cancel, S6 input producer, read-interrupt observer, budgets/timeouts. Response-schema failures stay exit1; legitimate resource/pending stays3. No P02 resume implementation.'),
 ('apps/cli/cli_sessions_test.go',[(132,228),(229,269)],['Extract/reuse real temporary API+SQLite setup for new appended compiled interactive ownership tests','Existing resume-tail229–269 preserved as historical P02 diagnostic; do not run it as current checkpoint recovery qualification'],
  'No fake runtime qualification. Synthetic metadata/binding port explicit; AdmitTurn resource refusal may yield Task BLOCKED and CLI3 after one real durable send; that is not successful MODEL execution. Existing assertions intact.'),
 ('apps/cli/cli_stream_test.go',[(32,350),(486,563)],['Typed fixture only: complete response/null/error/HostStatus/Attach/Pending/Control/Event payloads','Two old pending producers228–231 and325–329 become valid ACK+Pending on both attempts; exact three-send/replay assertions remain','Append new strict/attach/exit compiled CLI controls'],
  'Original S5 tests564–end and all value/terminal/replay assertions retained. If json.Number representation affects old numeric compares, prefer compatible checked representation at response boundary; any test assertion change needs exact additional bounds, never generic legacy-binding exemptions.'),
 ('tests/runtime/cli_contract/main.go',[(70,118),(254,285),(482,545)],['Exclusive run-owned temp config/discovery/bin/output and per-child untruncated actual raw/argv/exit/hash','Hostless init/config absent-vs-existing fixtures and interrupt display correction by old-ID ledger'],
  'ok/report/tableRowsProven counts and proven_by/IDs unchanged; no selector skip disguising full PASS. No new full harness execution while P02/F08 held entries unresolved. Distribution/cascade untouched; no shared .local deletion.'),
 ('tests/runtime/cli_contract/v2verbs.go',[(21,30),(48,246),(266,274),(289,693)],['Strict request schema and independent explicit CAS expectations; method-specific full typed responses','Per-case config/native/discovery isolation; one child result serves assertion and diagnostic; read all JSONL by command identity','Exact old-ID ledger corrections; add legal ACK and illegal-status controls; preserve resume-target assertion HOLD'],
  'No constant successful execution fabricated from method name. Pure protocol probe labelled FIXTURE only; real API owns interactive transactions. Neither fake Host bootstrap nor snapshots alone certify init/RESUME/cancel. All45 literal check IDs plus dynamic IDs retained.'),
 ('apps/cli/cli_http_status_test.go',[(136,147)],['TestW05HTTP2xxValidationRetained: replace valid reply constructor with full HostStatusResult and explicit revision/error fields; keep per-mode identity mutations'],
  'Exact additional eighth path. Keep seven mode strings, actual requests, valid0/invalid1 assertions124–161 and every non2xx/body/redirect test unchanged. No product file expansion.')]
scope=[]
for rel,spans,functions,protect in bounds:
 scope.append({'path':rel,'before_ref':ref(W/rel),'function_bounds':functions,'original_line_spans':[{'start':a,'end':b} for a,b in spans],'protection':protect,'new_helpers':'only private helpers or appended focused tests directly needed for listed behavior; no unrelated refactor'})

controls=[]
def c(i,name,case,expected,layer='COMPILED_CLI_LOOPBACK_TYPED_FIXTURE',held=False):
 controls.append({'id':i,'future_test':name,'subtest':case,'expected':expected,'layer':layer,'status':'HOLD_NOT_RUN' if held else 'NOT_RUN','raw_required':['actualargv/cwd/env_allowlist/tool+exe hash/time/outerexit','all stdout/stderr/request+response original bytes','context/config before-after bytes and observed method/command counts']})
for case,expect in [
 ('existing-open-readonly','list→attach(false), no claim/no send before input; real original owner/epoch/lease unchanged'),
 ('existing-self-send','readonly attach→explicit input→one original send; observed own writer epoch, same SID/project'),
 ('foreign-writer-input','read remains allowed; no hidden takeover/send; explicit blocked3 without changing owner'),
 ('new-create-attach-send','real create→attach(true) completed own snapshot→one send; scoped CAS derives only from completed snapshots'),
 ('new-two-multiline-turns','two complete logical inputs each once; no duplicate create; output before EOF; all JSONL grouped correctly'),
 ('invalid-list-no-context','foreign identity/malformed list exit1, no create/attach/send/config write'),
 ('list-other-item','legal other Session item does not select it; real new create remains sole selected SID'),
 ('slash-read-no-takeover','/status and /help never acquire writer or become MODEL text')]:c('P01-'+str(len(controls)+1).zfill(2),'TestCLIProtocolInteractiveAuthority',case,expect,'COMPILED_CLI_REAL_API_SQLITE_SYNTHETIC_RUNTIME' if case in ['existing-open-readonly','existing-self-send','foreign-writer-input','new-create-attach-send'] else 'COMPILED_CLI_LOOPBACK_TYPED_FIXTURE')
for j,(case,expect) in enumerate([
 ('ack-then-completed','same raw envelope/commandID replay; no send/control until valid completed AttachResult owner acquired'),
 ('permanent-ack','bounded test cancellation/deadline; nonzero pending/blocked, zero next write and no adopted owner'),
 ('ack-then-conflict','typed WRITER_BUSY/VERSION_CONFLICT stops; no revised CAS/new command retry'),
 ('ack-cancel','signal while waiting without admitted Run does not invent control or completed takeover'),
 ('false-acquired','claim true + write_owner_acquired false does not authorize subsequent write'),
 ('foreign-or-expired-writer','claim true completed snapshot with wrong client/expired lease fails before write'),
 ('caller-epoch-not-authority','--writer-epoch alone cannot substitute valid completed own-writer proof'),
 ('typed-cancel-ack','existing cancel independent settlement evidence retained; ACK never declares complete')],1):c(f'P03-A{j:02}','TestCLIProtocolAttachCompletionBarrier',case,expect)
for j,(case,expect) in enumerate([
 ('protocol-command-method','each mismatched identity rejected1 in generic and contextual paths; no context mutation'),
 ('null-missing-sid','explicit null remains distinct from missing; create derivedSID and projectGoal nulltopSID validated per method'),
 ('revision-null-and-exact','legal null revision accepted for applicable unscoped reply; missing/fraction/overflow rejected; large exact int preserved'),
 ('host-client-identity','full HostStatusResult but wrong client_id rejected1'),
 ('snapshot-scope','project/SID/top revision/nested revision/epoch mismatch refused atomically'),
 ('full-method-results','all23 method result mappings schema validated; no arbitrary method_confirmed success'),
 ('ack-pending-shape','legal PendingResult accepted only as pending; fake snapshot/resultnull/settled ACK rejected1'),
 ('rejected-error-coherence','resultnull/fullProtocolError/matching error_code required; invalid refusal cannot become resource3'),
 ('decoded-key-duplicates','top and nested literal/escaped duplicate keys rejected before map decoding'),
 ('unicode-single-json','invalid UTF8/surrogate/trailing second JSON rejected; benign Unicode preserved'),
 ('numeric-lexemes','1.0000000000000001 and integer-boundary adjacent values never round into valid identity/revision'),
 ('illegal-statuses','top IN_PROGRESS/NOT_IMPLEMENTED/unknown all invalid1; no enum mutation'),
 ('http-precedence','nonJSON401/403→3,503→1,redirect no credential forwarding, bounded body; existing L01 unchanged'),
 ('io-cancel-precedence','actual cancellation cause only130; unrelated earlier failure remains1/3 with later signal; L02 unchanged'),
 ('completed-goal-not-execution','valid goal/send response remains admission; original Task/Run/event/artifact terminal checks still required'),
 ('invalid-last-reply-local-bytes','invalid response does not write local config; earlier independently validated durable SID may remain as previously saved only')],1):c(f'P03-V{j:02}','TestCLIProtocolStrictResponse',case,expect)
for j,(case,expect) in enumerate([
 ('legal-not-implemented','full REJECTED NOT_IMPLEMENTED returns3 as pending Root capability-unavailable interpretation; no local write'),
 ('illegal-top-not-implemented','same words in illegal top status return1, never3'),
 ('resource-auth','existing legal resource/auth refusals3 and invalidinput2 retained'),
 ('execution-failed','legal INTERNAL_ERROR and real check failure remain1'),
 ('readonly-interrupt','actual compiled Windows CTRL_BREAK returns130 INTERRUPTED_READ_ONLY; no write/cancel')],1):c(f'P04-{j:02}','TestCLIProtocolExitClassification',case,expect)
for j,(case,expect) in enumerate([
 ('old49-traceability','all old literal IDs retained; original69 successful IDs and26 entries immutable; no runtime result inferred'),
 ('real-bootstrap-resource','same-user actual native choose/register/bootstrap proves opaque workspace ref; if no authorised temporary resource OPEN'),
 ('p02-resume-target','original target=session assertion is not valid checkpoint evidence; cannot pass full aggregate until separate Root scope'),
 ('full-harness','default complete original harness remains pending separate authorisation and P02 closure; no removal of held IDs')],1):c(f'HARNESS-{j:02}','TestCLIProtocolContractEvidence',case,expect,'FUTURE_HARNESS_OR_RESOURCE_GATE',True)
save('future_case_matrix.json',{'status':'ALL_NOT_RUN_NO_PRODUCT_ACCEPTANCE','count':len(controls),'immediate_count':len([x for x in controls if x['status']=='NOT_RUN']),'hold_count':len([x for x in controls if x['status']!='NOT_RUN']),'cases':controls})

diag=read(D/'diagnostic_matrix.json'); ledger=[]
held={5,6,7,10,11,19,20,26}
for row in diag['rows']:
 x={'ordinal':row['ordinal'],'id':row['id'],'original_failure_ref':row['original_raw_ref'],'old_assertion_ref':row['harness_locator'],'original_cause':row['actual_cause_and_inference_boundary'],'proposed_revision':row['minimal_compatible_proposal'],'disposition':'HOLD_NO_PASS_OR_WEAKENING' if row['ordinal'] in held else 'PROPOSED_FIXTURE_OR_PRODUCT_CONTROL_NOT_RUN','limits':row['unverified_boundary']}
 if row['ordinal']==18:
  x['proposed_revision']='Keep legacy ID in traceability; rewrite its assertion only upon Root/non-author approval to REQUIRE illegal IN_PROGRESS refusal1/no write, and add distinct ACKNOWLEDGED pending→completed control ID. Never keep a label whose success falsely implies IN_PROGRESS acceptance. P02 RESUME-based positive replaced by dedicated attach barrier control, original recovery assertions remain held.'
 if row['ordinal']==13:x['proposed_revision']='Legal REJECTED/ProtocolError NOT_IMPLEMENTED →3 (Root interpretation pending), reason HOST_REJECTED:NOT_IMPLEMENTED; retain separate illegal top NOT_IMPLEMENTED negative→1.'
 if row['ordinal']==6:x['limits']+=' No rewrite into usage-error success and no deletion; proposed nonmanual epoch attach gate is a separate new case until P02 whole-resume scope closes.'
 ledger.append(x)
save('old26_revision_ledger.json',{'original_success_ids':69,'original_failure_entries':26,'original_harness_exit':1,'rows':ledger,'aggregate':'Original aggregate remains FAIL. P01/P03/P04 scope cannot produce whole-harness PASS while P02/F08/native bootstrap held branches lack actual evidence.'})
raw_report=Path(diag['original_report_ref']['path']);assert h(raw_report.read_bytes())==diag['original_report_ref']['sha256']
report=json.loads(raw_report.read_text(encoding='utf-8'));assert len(report['assertion_ids'])==69 and len(report['failures'])==26
save('original_ids_preserved.json',{'original_report_ref':ref(raw_report),'successful_ids':report['assertion_ids'],'failure_ids':[x['id'] for x in report['failures']],'count_explanation':'assertions=69 counts successful ok() IDs, failures26 separate entries; neither is an independently accepted test count','no_old_id_deletion':True})

schema=read(I/'snapshots/package/contracts/client.protocol.schema.json')
save('typed_fixture_contract.json',{'authority_ref':ref(I/'snapshots/package/contracts/client.protocol.schema.json'),'method_result_map':schema['x-method-contracts'],'response_required':schema['$defs']['CommandResponse']['required'],'allowed_statuses':schema['$defs']['CommandResponse']['properties']['status']['enum'],'fixture_rules':[
 'A single shared fixture response factory must validate the ORIGINAL raw response against frozen schema before intentional one-fault mutation; raw parser must reject duplicate decoded keys/invalid Unicode and preserve json.Number lexemes.',
 'No domain.DecodeResponse: it accepts IN_PROGRESS/NOT_IMPLEMENTED and requires nonnull revision. ValidateResultAgainstMethod alone also redecodes through float64; use SchemaDoc.ValidateDef on preserved-number complete response/result directly.',
 'For scoped replies SID equals request SID, including REJECTED unknown-SID original identity; do not reject legitimate null revision for unavailable state. Unscoped non-create/non-goal cannot invent SID; session.create COMPLETED obtains sole SID from matched snapshot. goal.start preserves null top SID for original project-level request and its documented Goal revision, nested Session separately.',
 'HostStatus client_id matches requester; snapshot project+SID+revision and lease fields match validated response semantics. Completed attach requires write_owner_acquired appropriate to requested intent; true requires own current writer lease before writes. False attach must not renew/acquire host ownership.',
 'PendingResult all four fields; repeated original command/raw accepted_at/operation remain same identity. No fake IN_PROGRESS. ControlResult complete action/target/control_request/snapshot with action-specific settled fields.',
 'SessionEvents retain full frozen event/payload/reference schemas, sequence/replay/foreign/build/error checks. Fill fixture VersionRefs/Event fields; never weaken original consumer to admit incomplete fixture.',
 'Protocol tests may return explicit synthetic completed execution rows only as transport/follower fixtures. Actual API transaction tests use real caller auth/workspace/configure/create/journal and expose synthetic runtime refusal. Neither authorises LIVE/qualification.',
 'Reply→in-memory context/local config adoption happens only after all applicable identity/schema/numeric/binding guards; no fake local model/credential, no secret echo.'
 ]})

proposal={'schema':'researchos.readonly.cli-exact-fix-scope.v1','status':'PROPOSAL_PENDING_NONAUTHOR_SCOPE_REVIEW_AND_ROOT_LEASE','actor':'codex:/root/sources_parent_impl','role':'FUTURE_IMPLEMENTATION_AUTHOR_NOT_ACCEPTOR','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'input_reviews':[ref(I/'source_review.json'),ref(I/'scope_proposal.json')],'baseline':{'handler_frozen_commit':COMMIT,'main_expected':'2cdb0d43d5a600eef13c8f1735946a9adf52d079','future_isolated_worktree_required':True,'baseline_rule':'Root creates a new isolated branch from exact handler22752 or a reviewed composition retaining all frozen38 blobs. Do not use/alter current handler author WT. Any extra merged source is separately hashed and qualified.'},'exact_source_count':8,'production_count':3,'test_count':5,'paths':scope,'decisions':{
 'P01':'Open existing selected session list→readonly attach(false) before input. No foreign writer takeover from opening or ordinary text. Own writer may send after validated readonly snapshot; unowned session explicit write can request attach(true). New session first user message: create→attach(true)→COMPLETED own snapshot→send once. Existing explicit /resume takeover remains ACK-gated but actual recovery P02 held.',
 'P03':'All generic v2 call paths validate raw JSON, exact numbers, complete frozen response/method schema and identity. Retain return signatures; strictIdentity=false cannot disable validation. ACK is returned as pending to callers or same-command replayed by waiting flow; cannot adopt writer/create/control. Keep active CANCEL separate settled path. No change of public /2 schema/enums.',
 'P04':'Recommend legal typed REJECTED NOT_IMPLEMENTED maps to exit3 as capability unavailable; product.contract only defines category, not per-error mapping. This is PENDING_ROOT_CLASSIFICATION, not an inferred frozen rule. Illegal top statuses always1.',
 'P02':'HOLD entirely. CLI current RESUME target=session violates text target Goal/Run, and domain shortcut snapshot does not restore checkpoint. Do not edit domain, fake target/runtime completion, delete old resume tests, or call snapshot success recovery.'},'number_compatibility':{'validation':'raw jsontext strict validation + Decoder.UseNumber + SchemaDoc.ValidateDef fullresponse before numeric conversion; no canonical.JSON float roundtrip','integer':'reuse readonly configureExactInteger/domain.Num semantics; exact int64 revision/epoch and overflow refusal; preserve existing product caps, no new host policy','public_map_compatibility':'After exact validation, preserve prior float64 representation only for exactly representable safe numeric values if necessary for existing consumers/tests; retain json.Number for larger integers and use extended exact cliInteger. Never round fractional revision into integer or allow integer collision; no protected assertion edits to hide it.'},'atomic_context_rule':'Stage reply-derived SID/revision/epoch in private candidate context; commit once validated. Invalid response/pending cannot change fields or cause local file rewrite. Preserve a genuinely previously committed selected session; no destructive rollback of earlier accepted identity. No automatic stale-CAS refresh-and-retry write.',
 'guard_protection':['L01 status before body, no redirects, nonJSON401/4033 and5xx1','L02 errors.Is(actual IO cause,context.Canceled), oversize precedence, finish ordering','S5 real Goal/Task/Run/effect/event/Report/source binding; no generic ValidateLegacySession escape','S6 queue/consume/UNKNOWN/cancel receipts immutable; F08 held','handler38 config private original headers/globalidentity/metadata-only authority and exactref opaque model unchanged','all frozen schemas/SQL/SDK/provider/bundle source unchanged'],
 'extra_path_necessity':{'path':'apps/cli/cli_http_status_test.go','actual_source_locator':ref(W/'apps/cli/cli_http_status_test.go',{'line_start':124,'line_end':161}),'cause':'valid fixture136 missing revision,error_code,error and HostStatusResult fields; strict new full schema would correctly reject. Repair response constructor only, not original success/error assertions. Thus exact7 insufficient for this necessary old regression.'},'implementation_order':['non-author exact8+ID changes review; Root classification/lease; new WT from frozen38','implement private response gate preserving old IO transport ordering; typed fixture factory and new negative controls','stage context adoption + ACK replay/attach authority; P01 real API ownership controls','correct only approved old harness ID fixtures/reasons; leave P02/default full harness gated','freeze full compiler/source/SDK/exes; run finite reviewed targeted tests then approved regression; seal first failure+beforeafter','author handoff exact8 source commit + separate immutable receipts; independent source verification; Root serial integration'],
 'current_execution_counts':{'Go':0,'Node':0,'SQL':0,'HTTP':0,'model':0,'tests':0,'product_writes':0,'canonical_writes':0},'proof_limits':'Static/read/proposal only. No source acceptance, no handler acceptance, no W05/A04/current formal increment. Proposed test counts are not executed PASS counts.'}
save('scope_proposal.json',proposal)

groups=sorted({x['future_test'] for x in controls if x['status']=='NOT_RUN'})
future={'status':'NOT_EXECUTED_PLAN_ONLY','tools':{'go':str(M/'.local/tools/go1.27.1/go/bin/go.exe'),'GoSHA256':'d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490','node':'C:/nvm4w/nodejs/node.exe','node_policy':'not needed for immediate typed/real API synthetic-runtime tests; if existing SDK regression authorised pin actual current bundle+source, never fallback W14bundle'},'environment':{'GOTOOLCHAIN':'local','GOENV':'off','GOROOT':str(M/'.local/tools/go1.27.1/go'),'GOPATH':str(M/'.local/gopath'),'GOCACHE':str(M/'.local/gocache'),'RESEARCHOS_GO':'explicit pinned absolute Go','RESEARCHOS_NODE':'explicit pinned Node only authorised SDK regression','RESEARCHOS_MU_BUNDLE':'explicit reviewed current bundle only authorised SDK regression'},'planned_argv':[
 ['<pinned-go>','list','-deps','-test','-json','./apps/cli','./tests/runtime/cli_contract'],
 ['<pinned-go>','build','-o','<new receipt namespace>/researchos-cli.exe','./apps/cli'],
 ['<pinned-go>','test','-c','-o','<new receipt namespace>/cli.test.exe','./apps/cli'],
 ['<pinned-go>','tool','test2json','-t','-p','researchos.local/research-os/apps/cli','<cli.test.exe>','-test.v','-test.count=1','-test.timeout=480s','-test.run=^('+'|'.join(groups)+')$'],
 ['<pinned-go>','tool','test2json','-t','-p','researchos.local/research-os/apps/cli','<cli.test.exe>','-test.v','-test.count=1','-test.timeout=480s','-test.run=^(TestW05HTTP.*|TestCLIRead.*|TestW05CLIFollow.*|TestW05CLIEventReplayIntegrity|TestW05CLIInteractiveBeforeEOFAndSlash|TestW05CLIGoal.*)$'],
 ],'compiled_cli_examples':[['<researchos-cli.exe>'],['<researchos-cli.exe>','--session','<actual SID>','--project','<actual project>'],['<researchos-cli.exe>','status','--session','<actual SID>'],['<researchos-cli.exe>','run','<one finite fixture text>','--session','<actual SID>','--project','<actual project>','--output','jsonl']],
 'full_harness_future_argv':['<pinned-go>','run','./tests/runtime/cli_contract'],'full_harness_gate':'DO_NOT_RUN under current readonly task or immediate P01/P03/P04 until Root expressly releases P02/F08/native-bootstrap held rows and actual finite scope. No new partial formal selector or aggregate demotion. Old26 raw remains historical unchanged.',
 'input_closure':['Git HEAD/index/dirty exact public truth; full compiled local package files including platform variants/tests/EmbedFiles/Asm/Cgo; actual go list invocation+raw','all transitive modules/SDK/vendor lock+manifest+bundle inputs, pinned tool bytes/buildinfo/environment, frozen contracts plus runtime mirrors','test exe/CLI exe/build invocation and hashes, own fixture public certificate if any, per-child exactargv/stdout/stderr/exit','closed SQLite snapshot or VACUUM INTO own new snapshot for real API authority/journal/state proofs; never copy private/user DB','before/after/current bytehash match; all source changes force new cohort, original failures remain'],
 'stopping':'first unexpected result stops dependent batch, preserves original raw/exit/source closure and reports scope. Same unchanged failing input not blindly retried; max2 only explicit causal progress. No auto rerun held provider history2/history5/generic1811/legacy14 or existing full26. No source outside exact approved bounds.',
 'numbers':{'new_case_rows':len(controls),'immediate_NOT_RUN':len([x for x in controls if x['status']=='NOT_RUN']),'hold_NOT_RUN':len([x for x in controls if x['status']!='NOT_RUN']),'future_test_groups':len(groups),'old_successful_ids':69,'old_failure_entries':26},'regression_exclusions':'P02 resume-tail remains held, original assertions not erased. Protected real S5 legacy runtime qualification failures separately held; broad TestW05CLI.* selector prohibited. Additional actual SDK/Windows scope requires separate explicit inputs/argv.'}
save('future_execution_plan.json',future)
save('tool_diagnostics.json',{'executed_classes':['PowerShell/Python static reads+JSON/hash assembly','rg discovery','Git show frozen blobs'],'known_nonzero':[{'chunk_id':'0fc7f1','actual_outer_exit':1,'command':'rg -n func DecodeResponse|func ValidateResultAgainstMethod|... apps/cli internal/domain/client_protocol_decode.go','stderr':'rg: .../internal/domain/client_protocol_decode.go: 系统找不到指定的文件。 (os error 2)','cause':'guessed filename absent; source located afterwards by rg --files then rg directory, actual client_protocol.go481/604','subsequent_chunks':[{'chunk_id':'47d7f7','exit':0},{'chunk_id':'3b090e','exit':0}],'product_failure':False,'failure_origin_count':1}], 'other_read_chunks_outer_zero':['bb70f2','5cafe1','614f9d','2f57c2','a16b0b','929cd9','61cff8','e5626d','84de70','81f1e4','d3e01e','ab850f'],'truncated_outputs':['5cafe1','2f57c2','e5626d'],'truncation_handling':'targeted followup excerpts used; no claim full display from a truncated result','no_unknown_exit_invention':True})
after=[ref(Path(x['path'])) for x in inputs]
drift=[{'before':x,'after':y} for x,y in zip(inputs,after) if x['sha256']!=y['sha256']]
assert not drift,drift
save('inputs.after.json',after)
save('hashguard.json',{'input_count':len(inputs),'initial_review_namespace_count':len(read(N/'inputs.before.json')),'changed_inputs':drift,'frozen8_git_match':True,'capture_limit':'Initial input review namespace captured before current reading. Additional original-source inputs assembly before/after are a later static capture; no claim compiler closure or initial-start capture for those.'})
handoff={'status':'EXACT8_PROPOSAL_PENDING_NONAUTHOR_REVIEW_ROOT_LEASE','scope_ref':ref(N/'scope_proposal.json'),'cases_ref':ref(N/'future_case_matrix.json'),'old26_ref':ref(N/'old26_revision_ledger.json'),'future_argv_ref':ref(N/'future_execution_plan.json'),'hashguard_ref':ref(N/'hashguard.json'),'tools_ref':ref(N/'tool_diagnostics.json'),'actor':'codex:/root/sources_parent_impl','source_acceptance':False,'required_decisions':['Root P04 legal NOT_IMPLEMENTED resource/capability exit3 classification','Root/non-author exact eighth L01 fixture path and old18 IN_PROGRESS assertion inversion with distinct legal ACK positive','P02 holds original recovery/aggregate; no full formal harness execution or green promise from these8 files'],'product_source_changes':0,'formal_increment':0}
save('handoff.json',handoff)
manifest=[ref(p) for p in sorted(N.rglob('*')) if p.is_file() and p.name!='manifest.json']
save('manifest.json',{'schema':'researchos.public-receipt-manifest.v1','listed_count':len(manifest),'files':manifest,'self_excluded':True})
print(json.dumps({'scope':ref(N/'scope_proposal.json'),'handoff':ref(N/'handoff.json'),'manifest':ref(N/'manifest.json'),'counts':future['numbers'],'inputs':len(inputs),'drift':0},ensure_ascii=False))
