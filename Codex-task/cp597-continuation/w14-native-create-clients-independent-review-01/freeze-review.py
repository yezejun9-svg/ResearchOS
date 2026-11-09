from pathlib import Path
import hashlib, json, re

OUT=Path(__file__).parent
C=Path('C:/Users/yqyyds/Documents/Codex/2026-11-04/task/cp598-w14-clients-author/freeze-01')
BASE=Path('D:/作品集/ResearchOS/research-os')
D=BASE/'execution/v2.4/receipts/W05/W05-99/continue-cp597-20261104/clients/author/freeze-01'
expected='4b0adde5874c424eb43b1414cdfe36d6d919888f4c3fa69ecd41e4704e8a1c02'
def digest(path):
    b=path.read_bytes()
    return dict(path=str(path),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def readj(path): return json.loads(path.read_text(encoding='utf-8-sig'))
assert digest(C/'MANIFEST.json')['sha256']==expected
assert digest(D/'MANIFEST.json')['sha256']==expected
m=readj(C/'MANIFEST.json')
archive_checks=[]
for root in (C,D):
    for item in m['raw_and_support_files']:
        row=digest(root/item['path'])
        row['expected']=item['sha256'];row['match']=row['sha256']==item['sha256']
        assert row['match']
        archive_checks.append(row)
(OUT/'post-review-frozen-archive-check.json').write_text(json.dumps(dict(status='ALL_MATCH',checks=len(archive_checks),rows=archive_checks),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
go=readj(OUT/'go-independent-checks.json')
node=readj(OUT/'node-independent-checks-attempt-02.json')
assert go['test_exit']==1 and go['vet_exit']==0
assert node['checks']==38 and node['passed']==35 and node['failed']==3 and node['denied_boundary_calls']==[]
golog=(OUT/'go-independent-tests.log').read_text(encoding='utf-8-sig')
assert golog.count('CLOSED_KEY_COUNTEREXAMPLE:')==4
diagnostics=[
  dict(origin='reviewer read-only git discovery',category='HARNESS_ENVIRONMENT_DIAGNOSTIC_NOT_PRODUCT_FAILURE',tool_chunk='488427',
       detail='Both git status and git diff printed fatal: this operation must be run in a work tree. The wrapper ended exit0 after reading the frozen interface, so no git success is inferred. No mutation or blind retry occurred. .git was read back in e42622; no GIT_DIR/GIT_WORK_TREE override was printed. Exact pinned Main/candidate files were compared with difflib instead.',
       replacement_evidence=str(OUT/'production-and-test.diff')),
  dict(origin='reviewer Node mock validator response',category='HARNESS_FIXTURE_ERROR_NOT_PRODUCT_FAILURE',tool_chunk='009d44',
       detail='One of the four first Node failures was a plain mock ACK object where actual wire-values.reify requires a typed tree. Readbacks a8d920/2806bd/99efb6 established the mismatch. The original fixture, log and result remain intact. A separate attempt02 changes only the child mock output to a typed ACK tree; replay then passes and all three source counterexamples still fail.',
       corrected_terminal='c0fb6a',evidence=str(OUT/'node-reviewer-harness-diagnostic.json')),
  dict(origin='independent Go closed-key regression',category='PRODUCT_SOURCE_FAILURE',tool_chunk='21ca24',
       detail='Four malformed exact-key/case-variant replies were accepted and each reached one fake HTTP send. These are intentional negative assertions exposing a source bug, not test-harness failures.'),
  dict(origin='independent frozen Node stream and final-send regressions',category='PRODUCT_SOURCE_FAILURE',tool_chunk='c0fb6a',
       detail='Two trailing-chunk cases and one post-proof Host-origin microtask case remained reproducible after the harness response correction. No live candidate was read during author revision02 edits.')
]
(OUT/'review-diagnostics.json').write_text(json.dumps(diagnostics,indent=2)+'\n',encoding='utf-8')
names=['preparation.json','pin-and-stage.py','pin-verification.json','production-and-test.diff',
       'independent-go-extra.txt','combined_native_attestation_test.go','go-overlay.json',
       'go-independent-tests.log','go-independent-vet.log','go-independent-checks.json','node-author-fixture.log',
       'stage-frozen-node.py','frozen-node-staging.json','independent-node.cjs','node-independent.log','node-independent-checks.json',
       'prepare-node-attempt-02.py','independent-node-attempt-02.cjs','node-independent-attempt-02.log',
       'node-independent-checks-attempt-02.json','node-reviewer-harness-diagnostic.json',
       'post-review-frozen-archive-check.json','review-diagnostics.json']
artifacts={name:digest(OUT/name) for name in names}
def source_ref(rel,line):return dict(path=str(C/'source-snapshot'/rel),line=line)
report=dict(
 schema='researchos.independent-w14-native-create-clients-source-review/1',
 reviewer='codex:/root/resource_controller_review',scope_id=m['scope_id'],
 decision='REQUIRES_CHANGES_CLIENT_WIRING_NOT_ACCEPTED',
 client_wiring_approved=False,native_execution_authorized=False,model_qualification=False,
 W14_business_acceptance=False,formal_pass_issued=False,formal_increment=0,counter_reset=False,
 base_head=m['base_head'],
 author_manifest=digest(C/'MANIFEST.json'),author_manifest_D=digest(D/'MANIFEST.json'),
 source_sha256={p['path']:p['sha256'] for p in m['source_pins'] if p['changed']},
 unchanged_source_sha256={p['path']:p['sha256'] for p in m['source_pins'] if not p['changed']},
 author_scope_sha256=m['scope_sha256'],
 core_interface=dict(path=str(C/'core-interface.v1.json'),sha256='0a544c964ddd0dd1d4a29e3af75725a0acb1a2e71560c08543a624dd21a87393',mutable_core_source_read=False),
 evidence_integrity=dict(pre_review_pin_checks=77,pre_review_all_match=True,pre_review_live_paths=9,
   archive_support_files_per_copy=29,post_review_archive_checks=58,post_review_archive_all_match=True,
   live_candidate_read_after_author_started_revision02=False,
   candidate_sources_and_historical_evidence_modified_by_reviewer=False,
   diff_limit='Scoped exact nine files; whole-worktree git inventory was unavailable in this tool environment.'),
 findings=[
  dict(id='CLIENT-P1-001',severity='P1',status='BLOCKING',title='CLI privileged closed JSON accepts case aliases and alias pairs',
   references=[source_ref('apps/cli/cli_native.go',30),source_ref('apps/cli/cli_native.go',35),source_ref('apps/cli/cli_native.go',75),source_ref('apps/cli/cli_native.go',86)],
   trigger='Native reply uses Kind instead of kind, SCHEMA_VERSION instead of schema_version, or both canonical and case-variant names in one object.',
   observed='All four forms passed cliClosedNativeJSON and reached fake HTTP exactly once; each should have returned NOT_SENT before any HTTP send. jsontext rejects exact/escaped-equivalent duplicates, but encoding/json DisallowUnknownFields still matches struct fields case-insensitively.',
   required_repair='After strict syntax/UTF8/duplicate/trailing validation, require the exact case-sensitive top and payload key sets with every key present before typed decoding. Keep old three Native actions unchanged.',
   regression=str(OUT/'independent-go-extra.txt'),raw=str(OUT/'go-independent-tests.log'),terminal='21ca24'),
  dict(id='CLIENT-P1-002',severity='P1',status='BLOCKING',title='Desktop new raw Native reply resolves a valid JSON prefix before later trailing chunks',
   references=[source_ref('apps/desktop/main/lib/native.js',30),source_ref('apps/desktop/main/lib/native.js',46),source_ref('apps/desktop/main/lib/native.js',53),source_ref('apps/desktop/main/lib/native.js',151)],
   trigger='Fake socket emits complete valid proof JSON as one data event and a second data event containing {} or garbage.',
   observed='Actual new rawReply path resolves and destroys the socket at the first parseable prefix; createClientAttestor accepts the proof before the suffix can be read. Both later-chunk cases fail while fragmented valid JSON and same-chunk trailing controls behave as expected.',
   required_repair='Give only the new strict raw-reply profile a bounded complete-stream/frame boundary, retaining its 5s deadline and 8192-byte cap. Reject all trailing bytes after the complete frame. Do not change legacy early-completion behavior as an incidental repair.',
   transport_context='Read-only baseline Host sends one WriteFile, then FlushFileBuffers, DisconnectNamedPipe and CloseHandle (bc8b59). No actual Native pipe was exercised; the actual OS/packaged path remains outside qualification.',
   regression=str(OUT/'independent-node-attempt-02.cjs'),raw=str(OUT/'node-independent-checks-attempt-02.json'),terminal='c0fb6a'),
  dict(id='CLIENT-P1-003',severity='P1',status='BLOCKING',title='A queued Host-origin change can occur after proof check and before final Desktop post',
   references=[source_ref('apps/desktop/main/lib/ipc.js',160),source_ref('apps/desktop/main/lib/ipc.js',165),source_ref('apps/desktop/main/lib/ipc.js',171),source_ref('apps/desktop/main/lib/http-wire.js',179),source_ref('apps/desktop/main/lib/http-wire.js',182),source_ref('apps/desktop/main/lib/http-wire.js',191)],
   trigger='Attestor returns an already resolved promise and schedules a nested microtask changing discovery PID. IPC resumes and checks the old identity; the mutation runs before the transport resumes for its final POST.',
   observed='The frozen actual transport/post control flow invokes fake HTTP once after discovery changes. Changing origin inside the proof itself correctly blocks, so the counterexample isolates the later scheduling gap.',
   required_repair='Perform a final synchronous full-origin guard immediately before post, after all await boundaries and after request/header/resource revalidation. Cache pure stringify dependencies before proof so the final guard-to-post sequence has no asynchronous yield. Preserve exact raw/final bearer and pending lifetimes.',
   boundary='This is a deterministic in-process scheduling regression. It does not claim that a client can atomically lock external OS discovery changes or that a selector bypasses the independent trusted Host consumer.',
   regression=str(OUT/'independent-node-attempt-02.cjs'),raw=str(OUT/'node-independent-checks-attempt-02.json'),terminal='c0fb6a')
 ],
 pending_blockers=['CLIENT-P1-001','CLIENT-P1-002','CLIENT-P1-003'],
 tests=dict(
  independent_go=dict(command='locked go test -overlay go-overlay.json ./apps/cli -run ^(TestNativeCreate|TestIndependentGo) -count=1 -vet=off -v',
   started='099679',session=58311,terminal='21ca24',exit_code=go['test_exit'],
   top_tests=6,subcases=25,test_records=31,passed_test_records=26,failed_test_records=5,
   substantive_counterexamples=4,author_original_top_plus_sub=15,author_original_all_pass=True,
   log=artifacts['go-independent-tests.log']),
  independent_vet=dict(command='locked go vet -overlay go-overlay.json ./apps/cli',exit_code=go['vet_exit'],terminal='21ca24',log=artifacts['go-independent-vet.log']),
  independently_rerun_author_node=dict(terminal='fd1488',exit_code=0,checks=22,log=artifacts['node-author-fixture.log']),
  independent_node_attempt01=dict(started='0c3249',session=22890,terminal='009d44',exit_code=1,checks=38,passed=34,failed=4,harness_only_failures=1,source_failures=3,log=artifacts['node-independent.log']),
  independent_node_attempt02=dict(started='8ed8ee',session=50599,terminal='c0fb6a',exit_code=1,checks=38,passed=35,failed=3,harness_only_failures=0,source_failures=3,log=artifacts['node-independent-attempt-02.log'],results=artifacts['node-independent-checks-attempt-02.json']),
  environment=dict(go_exe='D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe',go_sha256='d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490',node_exe='C:/nvm4w/nodejs/node.exe',node_sha256='5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6',GOTOOLCHAIN='local',GOPROXY='off',GOSUMDB='off',GOENV='off',GOFLAGS='-mod=readonly -p=2',GOMAXPROCS='2',GOCACHE=str(OUT/'gocache'),GOTMPDIR=str(OUT/'tmp'))),
 verified_controls=[
  'Default-off CLI six flag variants preserve independently fixed legacy raw bytes and Authorization, with zero Native calls and no selector.',
  'Default-off Desktop exact body/headers/validator-phase sequence equals pinned Main baseline; legacy transport arity remains four.',
  'CLI and Desktop replay use the same command raw with a fresh proof for the newly selected bearer.',
  'Desktop pending/renderer/record output does not retain bearer or proof reference in the exercised paths.',
  'Body/header synchronous and asynchronous changes, resource drift, proof refusal and malformed proof prevent fake HTTP.',
  'Existing possibly-sent and ACK barriers survive later NOT_SENT/proof failure.',
  'Closed Node parsing rejects top/payload unknown and case aliases, escaped duplicate, same-buffer trailing, wrong type/ref/Host, expiry/calendar/time, malformed UTF8/surrogate and oversize replies.',
  'Other methods do not sign, and original Native actions/doctor files are not changed by the scoped diff.'
 ],
 proof_limits=[
  'Pure Go RoundTripper/fake Native dial and Node fake sockets/HTTP only; no real listener, HTTP request, Native peer, GUI, model, provider, old DB or user-token file was used.',
  'Node resource lookup/validator child are injected fixtures; actual production raw capture, proof callback, header checks and post function are exercised. The fixture now uses the real stringify/reify module and typed ACK tree.',
  'Client selector remains untrusted. Trusted Host witness/HTTP transaction/schema adoption is Core review scope and is not accepted by this client report.',
  'Current Root source prepared addon remains unsupported until separately adopted; no Native runtime or W14 business/formal acceptance is inferred.',
  'Old metadata receipt report f639dba66c00226fad644472f76349eab4bd669045cc7096f35687e0f00deda4 remains frozen; consumed resource scope is permanently no-replay.'
 ],
 prohibited_operations=dict(real_native=0,real_HTTP=0,real_GUI=0,real_model=0,real_child_validator=0,user_token_file_reads=0,existing_DB_access=0,network=0,old_probe_replays=0),
 diagnostics=diagnostics,artifacts=artifacts)
target=OUT/'source-review.json'
assert not target.exists(), 'Never overwrite a frozen independent report'
target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status='FROZEN',report=digest(target),decision=report['decision'],pending_blockers=report['pending_blockers'],formal_increment=0)))
