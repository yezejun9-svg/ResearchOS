from pathlib import Path
import hashlib,json,re

OUT=Path(__file__).parent
OLD=OUT.parent/'w14-native-create-clients-independent-review-01'
BASE=Path('D:/作品集/ResearchOS/research-os')
LIVE=BASE/'.local/worktrees/w14-native-create-clients-20261104'
C=Path('C:/Users/yqyyds/Documents/Codex/2026-11-04/task/cp598-w14-clients-author/freeze-02')
D=BASE/'execution/v2.4/receipts/W05/W05-99/continue-cp597-20261104/clients/author/freeze-02'
MF='12252ed255167a9a60398680145dd50c86ffef4dfcba7969b81f7edc32f61784'
def record(p):
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def readj(p):return json.loads(p.read_text(encoding='utf-8-sig'))
rows=[]
def pin(p,want):
 r=record(p);r['expected']=want;r['match']=r['sha256']==want;rows.append(r);assert r['match'],str(p)
pin(C/'MANIFEST.final.json',MF);pin(D/'MANIFEST.final.json',MF)
m=readj(C/'MANIFEST.final.json')
assert m['construction_frozen'] and not m['source_modification_permitted']
for f in m['raw_and_support_files']:
 for root in (C,D):pin(root/f['path'],f['sha256'])
for f in m['source_pins']:pin(LIVE/f['path'],f['sha256'])
for root in (C.parent/'freeze-01',D.parent/'freeze-01'):pin(root/'MANIFEST.json','4b0adde5874c424eb43b1414cdfe36d6d919888f4c3fa69ecd41e4704e8a1c02')
pin(OLD/'source-review.json','8215291ba3e98de8774132c042a4bc4228945fdf61a3fa516e9c554af31fc102')
pin(BASE/'.local/tools/go1.27.1/go/bin/go.exe','d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490')
pin(Path('C:/nvm4w/nodejs/node.exe'),'5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6')
pin(C.parent/'freeze-01/core-interface.v1.json','0a544c964ddd0dd1d4a29e3af75725a0acb1a2e71560c08543a624dd21a87393')
(OUT/'post-review-pin-verification.json').write_text(json.dumps(dict(status='ALL_MATCH',checks=len(rows),rows=rows),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
go=readj(OUT/'go-independent-checks.json');node=readj(OUT/'node-independent-checks.json')
assert go['test_exit']==0 and go['vet_exit']==0
assert node['checks']==54 and node['passed']==54 and node['failed']==0 and node['denied_boundary_calls']==[]
golog=(OUT/'go-independent-tests.log').read_text(encoding='utf-8-sig')
runs=re.findall(r'^=== RUN   (.+)$',golog,re.M)
top=sum('/' not in x for x in runs);sub=len(runs)-top
passes=len(re.findall(r'^\s*--- PASS:',golog,re.M))
assert top==7 and sub==40 and passes==47
author_node=readj(OUT/'node-author-fixture.log');assert author_node['checks']==29 and author_node['status']=='PASS'
source={f['path']:f['sha256'] for f in m['source_pins'] if f['changed']}
unchanged={f['path']:f['sha256'] for f in m['source_pins'] if not f['changed']}
assert len(source)==8 and len(unchanged)==1
diagnostics=[
 dict(origin='independent v2 harness preparation',category='PRE_EXECUTION_DEPENDENCY_ADAPTATION_NOT_FAILURE',tool_chunk='ef2565',detail='The reused v1 Native VM fixture was given setTimeout/clearTimeout before execution because the repaired source adds an absolute timer. Typed ACK mock correction from v1 was retained. New hard-timer/EOF/guard negatives were added. No failing or uncertain v2 harness attempt occurred.'),
 dict(origin='historical independent v1 source QA',category='PREVIOUS_PRODUCT_FAILURES_REPAIRED_NOT_RESET',tool_chunk='21ca24/c0fb6a',detail='Original CLIENT-P1-001/002/003 failures and report821529 remain unchanged. Their exact negative inputs now pass independently on final manifest12252; they remain historical origins and are not recounted or erased.'),
 dict(origin='historical independent v1 environment and harness',category='PREVIOUS_DIAGNOSTICS_PRESERVED',tool_chunk='488427/009d44',detail='Read-only git worktree errors and the independently corrected plain-object-versus-typed-tree mock are retained in v1 report/artifacts. No git retry or current source defect is inferred from those diagnostics.'),
 dict(origin='Root read-only replay hypothesis, supplied by parent',category='CORRECTED_HYPOTHESIS_NOT_A_PRODUCT_FAILURE',tool_chunk='55e2d8/596029',detail='An initial suspicion that replay skipped beforeSend was corrected by Root readback and this reviewer source inspection: the create/pilot condition is unconditional with respect to replay. Existing exact replay tests show repeated proof requests; ambiguous delivery separately retains its barrier. No new failure origin or source mutation was created from that hypothesis.')
]
(OUT/'review-diagnostics.json').write_text(json.dumps(diagnostics,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
names=['regression-inputs.json','pin-and-stage.py','pin-verification.json','repair.diff','additional-go-cases.txt',
 'combined_native_attestation_test.go','go-overlay.json','go-independent-tests.log','go-independent-vet.log','go-independent-checks.json',
 'augment-node.py','additional-node-cases.txt','independent-node.cjs','node-independent.log','node-independent-checks.json',
 'node-author-fixture.log','post-review-pin-verification.json','review-diagnostics.json']
artifacts={name:record(OUT/name) for name in names}
def ref(path,needle):
 lines=(C/'source-snapshot'/path).read_text(encoding='utf-8').splitlines()
 line=next(i for i,s in enumerate(lines,1) if needle in s)
 return dict(path=str(C/'source-snapshot'/path),line=line)
report=dict(
 schema='researchos.independent-w14-native-create-clients-source-review/2',
 reviewer='codex:/root/resource_controller_review',scope_id=m['scope_id'],scope_sha256=m['scope_sha256'],base_head=m['base_head'],
 decision='APPROVE_CLIENT_WIRING_ONLY_NOT_NATIVE_OR_W14_ACCEPTANCE',
 client_wiring_approved=True,root_source_integration_supported=True,pending_blockers=[],
 formal_increment=0,counter_reset=False,formal_pass_issued=False,native_execution_authorized=False,
 model_inference_qualification=False,W14_business_acceptance=False,Core_implementation_accepted=False,
 construction_frozen=True,source_modification_permitted=False,
 author_manifest_final=record(C/'MANIFEST.final.json'),author_manifest_final_D=record(D/'MANIFEST.final.json'),
 original_freeze02_manifest=record(C/'MANIFEST.json'),rejected_v1_report=record(OLD/'source-review.json'),
 source_sha256=source,unchanged_source_sha256=unchanged,
 integrity=dict(pre_review_pin_checks=136,pre_review_all_match=True,post_review_pin_checks=len(rows),post_review_all_match=True,
   live_source_paths_matched=9,actual_changed_paths=8,changed_production_paths=6,new_test_paths=2,
   new_C_support_pins=26,new_D_support_pins=26,old_C_support_pins_preserved=29,old_D_support_pins_preserved=29,
   scoped_repairs_only=True,author_sources_or_evidence_modified_by_reviewer=False,
   full_worktree_git_inventory='Not repeated; v1 environment diagnostic retained. Exact scope-nine sources and both manifest inventories were independently hashed.'),
 resolved_findings=[
  dict(id='CLIENT-P1-001',status='RESOLVED_FOR_CLIENT_SOURCE_SCOPE',
   repair='Strict syntax/UTF8/duplicate/trailing validation precedes exact case-sensitive required key-set validation and typed decoding.',
   references=[ref('apps/cli/cli_native.go','func cliClosedNativeJSON'),ref('apps/cli/cli_native.go','var fields map[string]json.RawMessage'),ref('apps/cli/cli_native.go','cliClosedNativeJSON(replyRaw'),ref('apps/cli/cli_native.go','cliClosedNativeJSON(reply.Payload')],
   evidence='All four original aliases/collisions now stop before fake HTTP; escaped-equivalent duplicate, malformed UTF8/surrogate, wrong type, invalid calendar/expiry, oversize reply and invalid credential/frame negatives pass. A single canonical Unicode-escaped key remains valid.',
   terminal='8588f9'),
  dict(id='CLIENT-P1-002',status='RESOLVED_FOR_CLIENT_SOURCE_SCOPE',
   repair='Only rawReply=true waits for complete EOF, accumulates at most8192 bytes, and has both the existing socket timeout and a separate absolute timeout. Premature close refuses; done prevents a post-end close from changing success. Legacy early object completion is retained.',
   references=[ref('apps/desktop/main/lib/native.js','if (rawReply) rawDeadline='),ref('apps/desktop/main/lib/native.js','if (rawReply) return;'),ref('apps/desktop/main/lib/native.js',"socket.on('end'"),ref('apps/desktop/main/lib/native.js',"socket.on('close'")],
   evidence='Both later trailing chunks now reject; fragmented valid JSON accepts only at end. Independent controlled scheduler tests prove registration and clearing of the absolute timer, partial-stream timeout, oversize close, premature close rejection, end-then-close success and legacy no-EOF completion.',
   terminal='28ac1c'),
  dict(id='CLIENT-P1-003',status='RESOLVED_FOR_CLIENT_SOURCE_SCOPE',
   repair='Main attaches a private synchronous full-origin verifier to beforeSend. Wire requires exactly true after all await/body/header/resource checks and enters post/http.request synchronously with no intervening await.',
   references=[ref('apps/desktop/main/lib/ipc.js','const verifyOrigin='),ref('apps/desktop/main/lib/ipc.js','beforeSend.verifyOrigin=verifyOrigin'),ref('apps/desktop/main/lib/http-wire.js',"typeof beforeSend.verifyOrigin!=='function'"),ref('apps/desktop/main/lib/http-wire.js','const reply=await post(url,raw,headers,record)')],
   evidence='Original PID microtask race and additional late Host-ID/URL/data-root changes all block before fake HTTP. False/missing/Promise/throw/string/undefined guard results refuse; true permits only the normal fixed raw/bearer send.',
   terminal='28ac1c')
 ],
 tests=dict(
  independent_go=dict(started='3fab4a',session=61481,terminal='8588f9',exit_code=0,top_tests=top,subcases=sub,total_test_records=passes,
   command='locked go test -overlay go-overlay.json ./apps/cli -run ^(TestNativeCreate|TestIndependentGo) -count=1 -vet=off -v',
   log=artifacts['go-independent-tests.log'],checks=artifacts['go-independent-checks.json']),
  independent_vet=dict(terminal='8588f9',exit_code=0,command='locked go vet -overlay go-overlay.json ./apps/cli',log=artifacts['go-independent-vet.log']),
  independent_node=dict(started='ef2565',session=1631,terminal='28ac1c',exit_code=0,checks=54,pass_count=54,fail_count=0,
   log=artifacts['node-independent.log'],results=artifacts['node-independent-checks.json'],script=artifacts['independent-node.cjs']),
  independently_rerun_author_node=dict(terminal='f2b3f7',exit_code=0,checks=29,source='Isolated C copy of exact final frozen source and test fixture; no live-source substitution',log=artifacts['node-author-fixture.log']),
  author_existing_pure_tests=dict(independent_rerun=False,author_terminal='98edd6',author_exit_code=0,author_tests=43,
   log=record(C/'node-existing-pure-01.log'),interpretation='Additional author evidence only; not counted among independent checks'),
  environment=dict(go_exe='D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe',go_sha256='d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490',
   node_exe='C:/nvm4w/nodejs/node.exe',node_sha256='5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6',
   GOTOOLCHAIN='local',GOPROXY='off',GOSUMDB='off',GOENV='off',GOFLAGS='-mod=readonly -p=2',GOMAXPROCS='2',
   GOMODCACHE=str(BASE/'.local/tools/gopath/pkg/mod'),GOCACHE=str(OLD/'gocache'),GOTMPDIR=str(OUT/'tmp'))),
 verified_behavior=[
  'Only explicit RESEARCHOS_NATIVE_CREATE_PILOT=1 and session.create acquire attestation. Six other CLI flag forms preserve exact independently fixed legacy bytes; Desktop default-off exact body/header/phase sequence matches pinned Main baseline and uses the four-argument legacy call.',
  'Production proof requests bind the actual final HTTP raw digest, final bearer, command/client/project/null-counter scope and full verified Host origin. The header is only an untrusted selector for the separate trusted Host consumer.',
  'Proof unsupported/refusal, strict reply failure, request or header mutation, validator resource drift, bad origin guard and current-origin changes remain NOT_SENT before fake HTTP.',
  'Desktop replay retains original command raw, obtains a current bearer and calls the producer again for that attempt; the exact wire replay test observes two proof requests with the respective bearers. Go repeats cliAttestCreate on every pilot create attempt.',
  'The create/pilot condition is unconditional with respect to replay. Ambiguous-delivery and ACK lifetimes retain their possiblySent barriers across later NOT_SENT; the same replay branch cannot silently omit proof or become a new legacy create.',
  'Bearer and proof reference do not enter pending operation, renderer reply or transport record in exercised paths. Original public envelope and existing three Native action shapes remain unchanged.',
  'Doctor/credential-provider behavior is unchanged by the scoped source diff; attestation itself does not bootstrap/renew/read session credentials, and other methods do not request it.'
 ],
 replay_availability_limit='The client cannot know whether the server already sealed the command. With the pilot on it conservatively requests a current proof for every create retry, including a potential sealed COMPLETED replay. Native unavailability or proof refusal can therefore prevent sending such a replay. This is an availability restriction, not a safety downgrade. Domain/Core must still return any actually sealed replay without a new grant, durable origin, consumption or event; this report does not certify that separate implementation.',
 limits_and_integration_requirements=[
  'Approval is for these exact client source bytes and pure mock wiring only. Root remains the sole integrator; no Main/checkpoint, live DB, prepared addon or private witness map was changed by this reviewer.',
  'Core implementation remains under separate construction/QA. This review uses the frozen interface0a544c964ddd0dd1d4a29e3af75725a0acb1a2e71560c08543a624dd21a87393 and the agreed result top kind+payload; it does not accept Core authority, origin persistence or transaction invariants.',
  'The current Root source prepared profile is unsupported until explicit addon adoption. Default-off integration is compatible; no actual Native feature usability or qualification is inferred.',
  'All Native/socket/HTTP boundaries were fake, and validator/resource dependencies were injected. The actual wire stringify/reify, final-send transport and post control flow were exercised, but actual Windows Native EOF behavior, packaged validator, GUI and release inventory were not executed.',
  'Normal packaged release module/descriptors must be rebuilt and checked after Root integration. This source review does not authorize running stale packaged inventories.',
  'Final synchronous guard closes the deterministic JavaScript scheduling gap; it does not claim an atomic lock over external OS discovery changes.',
  'Historical metadata reportf639dba66c00226fad644472f76349eab4bd669045cc7096f35687e0f00deda4 and consumed resource probe remain immutable and permanently no-replay. No inference, business acceptance or formal PASS is issued.'
 ],
 prohibited_operations=dict(real_native=0,real_HTTP=0,real_GUI=0,real_model=0,real_provider=0,packaged_validator_child=0,user_token_file_reads=0,old_DB_access=0,network=0,old_probe_replays=0),
 diagnostics=diagnostics,artifacts=artifacts)
target=OUT/'source-review.json';assert not target.exists(),'Never overwrite a frozen review'
target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status='FROZEN',report=record(target),decision=report['decision'],source_paths=len(source),pending_blockers=[],formal_increment=0,post_review_pins=len(rows))))
