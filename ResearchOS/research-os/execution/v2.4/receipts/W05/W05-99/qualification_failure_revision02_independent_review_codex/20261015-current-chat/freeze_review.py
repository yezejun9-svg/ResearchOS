import json, hashlib, datetime, subprocess
from pathlib import Path
ROOT=Path(r'D:\作品集\ResearchOS\research-os')
OWN=Path(__file__).parent
BASE='4f4023c956f84d65743f39ce77d6c8899a21ada1'
PREFIX='execution/v2.4/receipts/W05/W05-99/'
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,data):
    p=OWN/name
    if p.exists(): raise RuntimeError('refuse overwrite '+name)
    p.write_text(data if isinstance(data,str) else json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

supp=ROOT/PREFIX/'historical_qualification_public_provenance_codex/20261015-current-chat/semantics01/COLLECTION-manifest.json'
assert digest(supp)=='65f8dc740f745f0d836ad886222c6e52ec980a60edcc86bf363873f547ded258'
checks=[{'path':str(supp),'sha256':digest(supp),'match':True}]
for f in json.loads(supp.read_text(encoding='utf-8-sig'))['files']:
    p=Path(f['path']); actual=digest(p); assert actual==f['sha256'] and p.stat().st_size==f['bytes']
    checks.append({'path':str(p),'sha256':actual,'bytes':p.stat().st_size,'match':True})
write('supplement-hash-verification.json',checks)
extra=ROOT/PREFIX/'historical_qualification_public_provenance_codex/20261015-current-chat/verifier-authority-inputs01/COLLECTION-manifest.json'
assert digest(extra)=='29872605ae6a972dbcbbfaf77b675859b4f8c975ee270b9ae974ae38ed36c558'
extra_checks=[{'path':str(extra),'sha256':digest(extra),'match':True}]
for f in json.loads(extra.read_text(encoding='utf-8-sig'))['files']:
    p=Path(f['path']); actual=digest(p); assert actual==f['sha256'] and p.stat().st_size==f['bytes']
    extra_checks.append({'path':str(p),'sha256':actual,'bytes':p.stat().st_size,'match':True})
write('verifier-supplement-hash-verification.json',extra_checks)

# Bind frozen architecture source refs to captured immutable Git blobs, not live dirty files.
frozen=json.loads((ROOT/PREFIX/'qualification_failure_revision02_architecture_codex/20261015-current-chat/frozen-inputs.json').read_text())
source_checks=[]
for f in frozen['files']:
    p=OWN/('source--'+f['path'].replace('/','--')+'.stdout.raw')
    if p.exists() and p.stat().st_size:
        actual=digest(p); assert actual==f['sha256']
        source_checks.append({'source':f['path'],'git_commit':BASE,'captured_sha256':actual,'matches_frozen_architecture_input':True})
write('frozen-source-crosscheck.json',source_checks)

matrix=[
 {'id':'P01','premise':'Historical Core exact binary and source/build input identity','status':'SUPPORTED_WITH_DECLARED_LOCAL_RECEIPT_TRUST','evidence':['attempt02/01-core-build-chain.json','attempt02/02-current-core-to-historical-identity.json'],'detail':'c4a3b498 image, creation 134365308586079750; 2294 compile inputs before/after equal and 13 critical exact4f blobs recorded. Five extra critical bindings frozen in semantics01. No remote attestation or protected same-user holdout inferred.'},
 {'id':'P02','premise':'Exact historical staged worker/config/request/bundle identity','status':'SUPPORTED_WITH_DECLARED_LOCAL_RECEIPT_TRUST','evidence':['attempt02/03-exact-staged-worker-bindings.json','attempt02/04-package-composition-chain.json'],'detail':'worker5f364598, bundle2a8e7013, worker config6a6b5130, requestd7ec1d72 bind original dispatch705b11ec/Runf3dcb996/epoch1; current dirty source is not substituted.'},
 {'id':'P03','premise':'Wrapper source and SDK identity distinction','status':'SUPPORTED','evidence':['historical_mu_bundle_provenance_review/review.json','git-wrapper-292ad.stdout.raw:695-710'],'detail':'ResearchOS wrapper292ad and upstream SDK8df are distinct; original native128 wrong-repository probe is preserved, not treated as new failure of wrapper attribution.'},
 {'id':'P04','premise':'Complete historically pinned SDK generated-dist/node_modules/esbuild transitive build inputs','status':'MISSING_RETAINED_LIMIT','necessary_for_host_gate_only':False,'detail':'Original asset receipt has no complete historical transitive vector/metafile. 5083 retained vendor hashes and exact output bytes do not fill this gap. No reproducible-build acceptance.'},
 {'id':'P05','premise':'Rejected TOOL cannot reach Host prepare or dispatch through brokerEffect','status':'SUPPORTED_SOURCE_SEMANTICS','evidence':['internal/domain/runtime_broker_windows.go:82-84,145-152,203-209,242-265','internal/domain/runtime_model.go:100-102','internal/domain/runtime_coordinator_windows.go:473-520'],'detail':'Qualification admission checks MODEL-only before prepareEffectTx. resourceWriteLock held by dispatchGate. All Host TOOL/MODEL/SOURCE/EXPERIMENT calls here occur after durable PREPARED then STARTED. Historical generic503 is not an online typed B rejection.'},
 {'id':'P06','premise':'Actual configured custom tool callback delegates only to Host','status':'SUPPORTED_WRAPPER_SOURCE_AND_ASSET_CHAIN_NOT_FULL_BUNDLE_AUDIT','evidence':['git-wrapper-292ad.stdout.raw:695-710,741-745,795-801'],'detail':'makeTools.execute awaits protocol.effect(TOOL); configured tools replace builtins; extensions/skills/context discovery disabled. This bounds the reviewed wrapper callback, not every transitive SDK initialization or imported native Node API. Actual bundle whole-program semantics was not independently audited.'},
 {'id':'P07','premise':'Historical sandbox is fresh zero-capability AppContainer with explicit handle/environment boundary','status':'SUPPORTED_SOURCE_AND_PUBLIC_NATIVE_METADATA','evidence':['ops/experiment_sandbox/sandbox_windows.go:136-168,247-301','adapters/runtime/bridge_windows.go:318-328','semantics01/02-public-bridge-structural-metadata.json'],'detail':'Fresh SID; input GRGX/output FA; only stdin/out/err inherited; explicit SystemRoot and isolated temp/profile dirs; no route bearer/private verifier job inherited. caps[] is regular AppContainer, not LPAC.'},
 {'id':'P08','premise':'No descendant can escape the job/process confinement','status':'SUPPORTED_JOB_CONFINEMENT_ONLY','evidence':['ops/experiment_sandbox/sandbox_windows.go:100-108,213-218,268-272,301,365-375'],'detail':'ActiveProcessLimit1, KILL_ON_JOB_CLOSE, no breakaway flag. Native job_total_processes is 2, so do not claim one historical process or invent identity of a second. children_stopped proves final active count0 under source/receipt trust; it does not enumerate all historical attempted descendants.'},
 {'id':'P09','premise':'No independent historical network path outside the Host','status':'MISSING_FOR_UNIVERSAL_CLAIM','evidence':['ops/experiment_sandbox/sandbox_windows.go:264-301','semantics01/02-public-bridge-structural-metadata.json'],'detail':'No explicit networking capability plus fresh SID supports default-denied network semantics. No historical effective WFP/loopback-exemption state or per-subject network-denial observation is in supplied evidence. Do not infer a bypass occurred; do not infer universal historical absence from caps[].'},
 {'id':'P10','premise':'No independent OS shared-object/filesystem/IPC effect path outside the reviewed Host','status':'MISSING_FOR_UNIVERSAL_CLAIM','evidence':['ops/experiment_sandbox/sandbox_windows.go:59-84,148-168,254-272'],'detail':'Ordinary AppContainer includes ALL APPLICATION PACKAGES access semantics and OS-created private storage. Only staging DACLs are set here; host does not inventory all historically accessible shared resources or opt out as LPAC. Private scratch writes are not external TOOL effects, but cannot extrapolate from them to every OS path. No concrete escape is claimed.'},
 {'id':'P11','premise':'Historical worker final native closure and no queued/output branch','status':'SUPPORTED_PUBLIC_NATIVE_METADATA','evidence':['semantics01/02-public-bridge-structural-metadata.json','ops/experiment_sandbox/sandbox_windows.go:339-379'],'detail':'Original worker identity69860/1792057406096619100; exit124,timedout,children_stopped,streams_drained,cleanup_complete,output_copied; artifacts[],queue_requiredfalse,noqueue_control. Original cancellation/timeouts preserved. No raw frames read by reviewer.'},
 {'id':'P12','premise':'Historical stream exactness, rejected-key zero effect and entire current DB census','status':'NOT_REVALIDATED_ACTUAL_OPERATION_PREREQUISITE','detail':'Prior frozen diagnosis reports frames3/ACK2 and MODEL CONFIRMED with UNKNOWN money. This review does not open raw private frames or actual DB. Exact raw hash/sequence, rejection payload, zero key-stage and full census must be validated by separately accepted C operational preflight, not synthesized from this review.'},
 {'id':'P13','premise':'Same live Core retained qualification window prevents subsequent verifier/worker admission','status':'SUPPORTED_CONDITIONAL_ON_HISTORICAL_AND_FINAL_CENSUS','evidence':['internal/host/runtime_qualification_windows.go:157-196','internal/domain/runtime_qualification_confirmation_windows.go:198-263','internal/domain/runtime_coordinator_windows.go:248,550-565','internal/host/desktop_management_windows.go:256'],'detail':'Begin precedes verifier launch; consumed Run implies entered window; End cannot clear unresolved subject. Scan and coding paths gate qualificationActive; new CONFIRM fails Begin. Full final current census and same live creation identity still required. No new CONFIRM used as probe.'},
 {'id':'P14','premise':'Original verifier captured numeric exit/native wait','status':'MISSING_STOP_ACTUAL_BLOCKER','evidence':['internal/host/runtime_verifier_process_windows.go:219-226','semantics01/03-verifier-closure-source-boundary.json'],'detail':'Synchronous defer close implies cancel/pipe close/original Cmd.Wait attempted and returned before response. Wait result ignored, no numeric exit captured. This is not original native wait success, not exit0, not strict closure acceptance.'},
 {'id':'P15','premise':'Original verifier never received job or credential','status':'CONDITIONAL_NEW_PROOF_CLASS_NOT_ACCEPTED','evidence':['internal/host/runtime_qualification_windows.go:180-213','apps/runtime-verifier/main_windows.go:26-36','internal/verifier/protocol.go:62-108','internal/verifier/client.go:22-37'],'detail':'On exact Execute error at196, token204 and verify/job path213 are unreachable. Worker reads full job only after handshake and does no client call before Verify. Missing installed-verifier exact compiled identity/init closure and exact historical response/control-flow binding; no capability to replace current mandatory nativeclosure.'}
]
matrix[-1]['late_supplement']='verifier-authority-inputs01 binds f255f4d4 binary/installation and three exact4f source rows to historical union compile vector; raw public response/state refs supplied. This fills principal image/source-chain input, but not precise verifier-only init/transitive closure, historical196 branch proof or credential transfer census.'
write('premise-matrix.json',{'schema':'researchos.f01-independent-premise-matrix.v1','broad_f01_verdict':'NOT_PROVABLE_FROM_SUPPLIED_EVIDENCE','narrow_host_denial_verdict':'SUPPORTED_SOURCE_INFERENCE_NOT_ONLINE_REJECTION','premises':matrix,'formal_increment':0})

c_addendum={
 'status':'REQUIRED_BEFORE_C_SOURCE_CARD','reason':'Concrete nested lease handoff and uncovered official release_host entry',
 'existing_paths_add':['internal/domain/backup_upgrade.go','internal/domain/backup_prepared_abandonment_upgrade.go','internal/domain/backup_prepared_abandonment_handoff.go','internal/domain/backup_prepared_abandonment_upgrade_other.go','ops/supervisor/release_host/main.go'],
 'already_allowed_paths_reused':['ops/backup/main.go','ops/backup/maintenance_gate_windows.go','ops/backup/maintenance_gate_other.go','internal/domain/backup_prepared_abandonment_upgrade_windows.go','adapters/runtime/data_root_windows.go','internal/host/maintenance_startup_gate_windows.go'],
 'new_paths_add':['internal/domain/backup_source_lease_windows.go','internal/domain/backup_source_lease_other.go','ops/supervisor/release_host/maintenance_gate_windows.go','ops/supervisor/release_host/maintenance_gate_other.go'],
 'test_paths_add':['internal/domain/backup_source_lease_windows_test.go','internal/domain/backup_prepared_abandonment_handoff_test.go','internal/domain/backup_prepared_abandonment_upgrade_windows_test.go','ops/supervisor/release_host/maintenance_gate_windows_test.go'],
 'tests_already_allowed_reused':['ops/backup/maintenance_gate_windows_test.go','internal/host/maintenance_startup_gate_windows_test.go','adapters/runtime/qualification_maintenance_gate_windows_test.go'],
 'concrete_design':[
  'Windows CLI helper canonicalizes exact source/root/file identity, acquires ONE checked DataRootLease, invokes combined qualification+replacement gate before keys, protected store, DB opening or upgrade template operations; defer closes only after full workflow return.',
  'Add narrow Windows domain entry adapters UpgradeLocalUnderSourceLease and UpgradePreparedAbandonmentBackupUnderSourceLease taking held *runtime.DataRootLease (not JSON/bool/callback). They validate native lease root and opt.Source mapping, create package-private borrowed preparedUpgradeRootLease, and delegate to existing workflows.',
  'LocalUpgradeOptions carries an unexported sourceLease capability (excluded from JSON/hash); private prepared workflows call acquirePreparedUpgradeRootLease(root,opt.sourceLease). A borrowed lease validates Held/root and never closes underlying handle; outer owner alone closes. An internally acquired lease retains original owner/Close semantics. No close/reopen or second acquisition between gate and source open.',
  'All UpgradeLocal dispatch branches (schema13, configuration, queue, prepared23) are entered under the outer held capability. Existing standalone/default package APIs may not be used as an official command bypass; their policy must fail closed or use the same guarded adapter. No free-form callback is accepted.',
  'release_host main must invoke a platform wrapper acquiring the exact root lease and combined gate BEFORE OpenCanary/store.Open; existing control-fixture launch branch must retain its own disposable-root validation. C namespace guard in LockDataRoot alone does not implement replacement history validation.',
  'Nonwindows adapters must reject unsupported maintenance capability or preserve explicit fixture-only behavior; no nil-authority success masquerading as a Windows lease.',
  'Carry the full pre-existing C allowlist unchanged plus these exact additions; freeze signatures/ownership and test inventory in addendum before source. This is a proposed minimal coherent design, not implemented code.'
 ],
 'required_cuts':['pending qualification BEGIN blocks each CLI before protected/key/DB access','pending verifier replacement blocks each CLI under same lease','borrowed correct root succeeds without native reacquisition','wrong-root/closed/reused/forged capability rejects','inner failure never closes borrowed outer lease','outer release only after DB and workflow close','all five upgrade plan branches and create/export entries','release_host legacy and control fixture modes','inherited recovery/migration token held before+after combined gate','normal/Core/replacement/C own-recover exact exemption matrices'],
 'formal_increment':0
}
write('C-minimal-addendum.json',c_addendum)

stop_alt={
 'strict_current_stop':'STOP_UNAVAILABLE','native_closure_missing':True,
 'possible_class':'SOURCE_DERIVED_NEVER_JOB_AUTHORIZED_V1','accepted':False,
 'minimal_missing_evidence':['Exact actual installed verifier image digest/create identity/parent binding to immutable build receipt and compiled main_windows.go, protocol.go, client.go plus all package init effects relevant before main; no current build substitute','Exact historical managed response and Run/dispatch facts bind ExecuteLocalQualification error return196, excluding later LocalQualificationReview/token/verify path; no private job/token read required','Complete source call graph proves sole job writer is process.verify, no alternate stdin writer, inherited credential handle/env, DB direct-open, background init side effect or alternate token mint/transfer path','Authority distinction: ensureRuntimeVerifier creates principal/grants before run but principal declaration alone is not possession of bearer; show old verifier job never obtained any existing credential','Independent acceptance of a new operational invariant that a possibly alive, never-job-authorized, pipe-closed exact verifier is safe for this specific stop; do not call it exited, stopped, waited or numerically successful','If adopted, freeze separate STOP architecture/source allowlist/tests and an exact approved operation; existing mandatory all-native-closure contract remains unchanged until then'],
 'source_derived_close_limit':'Calling and returning from ignored Cmd.Wait is not success evidence. No original exit code can be recreated after the fact. PID absence or new current fixture cannot repair it.',
 'no_replay_alternative':'Continue evidence-only recovery of existing exact original native wait/exit artifacts; or independently review the never-job class above. Neither launches/verifies/replays old request. If neither can be established, keep strict actual STOP and dependent C blocked.',
 'authorization_anchor':{'required':'Independent non-self-asserted exact operation authorization anchor with real nonempty accepted hash before usable commit path','minimal_option':'Operation-specific build pins exact approved operation plan hash plus independently frozen F01/native evidence manifest hashes; source/proof parsing still revalidates all facts. A separate local protected registry is acceptable only with an explicit owner/update contract; caller JSON or expect-plan-sha256 alone is integrity, not approval.','limitation':'Same-SID local registry or compiled pins do not create cryptographic independence against a malicious same-user administrator. Trust basis remains declared OS Owner plus controlled operator workflow; do not claim protected holdout.','source_freeze':'An empty allowlist may safely disable commit temporarily but is not complete delivery of an operational Source contract. Freeze concrete anchor loading/validation/fixtures before acceptance; future actual plan pins remain separate authority.'},
 'formal_increment':0
}
stop_alt['late_binding_supplement']={'manifest_sha256':digest(extra),'supported':'f255f4d4 installed image plus installation and three exact4f source hashes recorded in joint historical compile vector','still_missing':'Verifier-specific transitive init closure; exact historical196 branch inference and all credential/job paths; independently approved new proof class. Nativeclosure remains missing.'}
write('STOP-alternative-proof-prerequisites.json',stop_alt)

findings=[
 {'id':'R2-F01','priority':'P1','severity':'High','kind':'EVIDENCE_GAP_NOT_ASSERTED_EXPLOIT','title':'F01 broad historical NO_EFFECT is not established','location':'C-ARCHITECTURE.md F01 section; premise-matrix P09/P10/P12','impact':'Treating Host-firstgate evidence as every permitted effect path would permit unsupported FAILED-only historical reconstruction and fresh-attempt eligibility.','scenario':'A validator accepts caps[] as universal no-network/no-shared-object evidence and concludes no effect despite no historical coverage of those paths. This is the inference failure being prevented; no actual escape was observed.','recommendation':'Preserve narrow HOST_BROKER_DENIED inference; retain NOT_PROVABLE for full C until necessary historical containment/raw/census premises or a separately narrowed approved contract are established. Do not use new fixture or wrapper provenance to erase missing transitive input limits.'},
 {'id':'R2-F02','priority':'P1','severity':'High','kind':'DESIGN_ENTRY_INTERLOCK_GAP','title':'C concrete lease handoff and one official entry remain absent from exact scope','location':'backup_prepared_abandonment_handoff.go:181; backup_prepared_abandonment_upgrade.go:416; backup_upgrade.go:245-254; ops/supervisor/release_host/main.go:39-49','impact':'Naive outer lease collides with inner acquisition; releasing it permits a journal race. Central qualification check leaves replacement history unchecked in release_host.','scenario':'Outer backup wrapper checks pending history then releases lease to satisfy inner Acquire; another official maintenance creates a journal before upgradeOpenExclusive. Or release_host acquires central qualification-only lease and reaches store.Open while replacement history is pending.','recommendation':'Freeze C-minimal-addendum.json exact paths, opaque borrowed lease adapter and all-entry tests before Source card. Hold one native lease continuously across combined gate and full source workflow.'},
 {'id':'R2-F03','priority':'P1','severity':'High','kind':'STOP_ACTUAL_EVIDENCE_GAP','title':'Original verifier native closure remains unavailable','location':'internal/host/runtime_verifier_process_windows.go:219-226; STOP-ARCHITECTURE.md Historical fence premise4','impact':'Strict stop could terminate Core with an unproven native verifier lifetime.','scenario':'A successful-looking management response is re-labelled original native exit0 although close() discarded Wait error and no exit receipt exists.','recommendation':'Keep strict STOP_UNAVAILABLE. Existing receipt recovery or separately reviewed never-job proof class may be pursued; neither is current native closure. See exact prerequisite file.'},
 {'id':'R2-F04','priority':'P1','severity':'High','kind':'SOURCE_CONTRACT_AUTHORIZATION_ANCHOR_GAP','title':'STOP accepted-plan provenance requires a concrete non-self-asserted anchor','location':'STOP-ARCHITECTURE.md Frozen plan / required actual inputs; STOP-exact-scope.json required_actual_inputs','impact':'Caller-created proof JSON and matching supplied plan hash could be mistaken for independent approval.','scenario':'Same caller writes accepted=true or arbitrary scope hash plus consistent plan and invokes commit. Rehashing those bytes proves consistency, not acceptance.','recommendation':'Freeze operation-specific compiled plan/evidence pins or explicit protected registry ownership/update contract; validate real evidence independently. Empty production allowlist is temporary disabled state, not full usable Source acceptance. State same-user trust limits truthfully.'}
]
review={
 'schema':'researchos.qualification-revision02-independent-review.v1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'owner':'codex:/root/qualification_failure_revision02_review','base_commit':BASE,
 'scope_sha256':'8bc13800ccb444fa445cf504d6861a2b9458c0e84c5b0901af9ad616e97e8165','architecture_sha256':'24cad12c2ff5bcb9df20c9749c384a8cb67b5459a30a168e316b8d8e209ae3d6','supplement_sha256':digest(supp),'verifier_binding_supplement_sha256':digest(extra),
 'verdict':'B_AND_D_DESIGN_DIRECTION_ACCEPTABLE_C_ADDENDUM_REQUIRED_F01_NOT_PROVABLE_STOP_ACTUAL_UNAVAILABLE',
 'b_design':'Firstgate exact typed construction, dispatchGate write serialization, admission-close/all-goroutine completion+drain/heartbeat join and private persisted validator correctly address F06. Requires real source+fixtures; historicalgeneric503 remains UNKNOWN.',
 'c_design':'F02/F03 authorship and exact five-version single-transaction design resolved at architecture level. F04 concrete all-entry/lease gap persists. Actual C blocked by F01 and STOP.',
 'd_design':'F05 exact binding reuse, all three runtime-only lookups, per-grant original subject, atomic schema24 intent/index lineage and unchanged NoProgress/budget ancestry correctly specified. D-addendum01 supersedes fixture-stub dependency and fake JS paths; accepted real B mandatory.',
 'stop_design':'No console/PID/tree fallback; exact retained handles and explicit zero-row BEGIN IMMEDIATE/query_only reservation are coherent conditional architecture. Native fixture query_only lock preservation remains required. Originalverifier actual proof and concrete approval anchor unresolved.',
 'previous_findings':{'F01':'PARTIALLY_ADDRESSED_IDENTITY_BOUND_FULL_SEMANTICS_NOT_PROVABLE','F02':'RESOLVED_DESIGN_ONLY','F03':'RESOLVED_DESIGN_ONLY','F04':'PARTIAL_CONCRETE_ADDENDUM_REQUIRED','F05':'RESOLVED_DESIGN_ONLY_WITH_D_ADDENDUM01','F06':'RESOLVED_DESIGN_ONLY','F07':'CONSOLE_BRANCH_REMOVED_EXACT_HANDLE_REPLACEMENT_NOT_ACTUAL_ACCEPTED'},
 'findings':findings,'counts':{'Critical':0,'High':4,'Medium':0,'Low':0},
 'trust_boundaries_STRIDE':[
  {'boundary':'worker frames -> Host effects','threats':['Spoofing route/run/epoch','Tampering frame/key','Repudiation generic denial re-labelled proof','Elevation capability to external TOOL'],'control':'Exact first gate before prepare, immutable evidence, zero-stage checks, host-private typed validator; historical generic failure not typed'},
  {'boundary':'native sandbox -> external OS/resources','threats':['InformationDisclosure shared resources','Tampering independent external writes','Elevation alternate handles/network','DenialOfService process lifetime'],'control':'Fresh AppContainer and job/handle/env restrictions supported; universal historical closure missing'},
  {'boundary':'maintenance plan -> schema24 DB/journal','threats':['Spoofing owner/author','Tampering stale CAS or self-asserted approval','Repudiation incomplete journal','Elevation early-entry bypass'],'control':'Exact currentOwner runnull MANIFEST, single transaction marker and append-only journal; all-entry borrowed-lease gap blocks Source'},
  {'boundary':'prepare-next UI -> fresh authority','threats':['Replay consumed request','Tampering lineage head','Elevation renderer authority or fake proof','DenialOfService unbounded retries'],'control':'Real B validator, immutable atomic sequence, same budget/NoProgress, explicit separate one-call confirmation'}
 ],
 'owasp_mapping':{'relevant':['OWASP A01 Broken Access Control','OWASP A04 Insecure Design','OWASP A08 Software and Data Integrity Failures','LLM05 Improper Output Handling','LLM06 Excessive Agency','LLM10 Unbounded Consumption'],'limits':'Architecture review of pinned subset, not a whole-repository dependency/CVE audit. No dependency changes, scan or installed-package execution performed.'},
 'positive_observations':['No raw ACK/frame rewrite; FAILED-only and UNKNOWN accounting preserved','Maintenance proof truthfully currentOwner-authored with run_idnull and explicit historical subject','All-goroutine join/drain and heartbeat join are required instead of only worker exit','Exact native handle identity and no console-wide/PID/name/tree fallback','D real persisted B proof dependency and actual existing React/browser runner paths'],
 'tests_run':0,'test_assertions':0,'source_acceptance':False,'actual_acceptance':False,'formal_increment':0,
 'forbidden_actions_performed':False,'read_boundaries':'Only frozen public receipt/source/contract files and Microsoft documentation; no actual DB, current process/OS query, backup, model, private raw frames, credentials/private keys, GUI or Source edit.',
 'evidence_files':['premise-matrix.json','C-minimal-addendum.json','STOP-alternative-proof-prerequisites.json','input-hash-verification.json','supplement-hash-verification.json','frozen-source-crosscheck.json','diagnostics.jsonl']
}
write('review.json',review)
write('external-references.json',[
 {'url':'https://learn.microsoft.com/en-us/windows/win32/secauthz/implementing-an-appcontainer','use':'Regular AppContainer and LPAC differ; LPAC explicitly opts out of ALL APPLICATION PACKAGES. Platform semantics only, no historical machine-state proof.'},
 {'url':'https://learn.microsoft.com/en-us/windows/win32/secauthz/appcontainer-isolation','use':'File/registry grants and private AppContainer storage remain possible; isolation is access-controlled resources, not zero possible OS effects.'},
 {'url':'https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/troubleshooting-uwp-firewall','use':'Network isolation uses WFP capability rules; loopback exemptions are separately configurable. No such historical state observed here.'}
])
write('initial-read-diagnostics.json',{'commands':'Initial Get-Content/Get-FileHash and bounded rg reads before capture.py creation','hash_result':'58 manifest/file hashes matched; scope hash matched','diagnostics':[{'kind':'rg Windows wildcard path','text':'rg: internal/domain/backup*: filename/directory/volume syntax invalid (os error 123)','resolution':'Replaced by git grep with exact paths, recorded in backup-callgraph/nested-backup raw files','no_test_failure':True},{'kind':'bounded schema filename search','exit':1,'reason':'Artifact schema is consolidated domain.schema.json, not per-type filename','resolution':'Captured exact consolidated schema from4f; no source change'}],'note':'Immutable input hashes and subsequent complete source stdout/stderr are retained; these initial file-read console outputs were not copied verbatim. No hidden test pass is inferred.'})

md='''# 资格失败 revision02 独立架构与 F01 语义审查

结论：B、D 的设计方向可继续进入各自受控施工；C 还需要冻结具体租约交接与遗漏入口。历史 Core/worker 身份链现已补足，但完整历史 NO_EFFECT 重建仍为 **NOT_PROVABLE**。当前严格 STOP actual 为 **STOP_UNAVAILABLE**。本审查不接受 Source、实际停止/维护/新调用或正式用例；formal_increment=0。

冻结 scope、四个输入 manifest 及其58个文件验证匹配；新增 semantics01 manifest 与4个文件也匹配。相关源码从不可变4f4023 Git blob捕获，并与架构冻结哈希比对。未检查正在施工的 A/STOP源码或改变共享状态。运行测试0、断言0；静态分析不记作fixture PASS。

## 影响与阻塞

### R2-F01 [High / P1] 历史 Host 拒绝成立，完整所有路径的 NO_EFFECT 缺证

位置：`internal/domain/runtime_broker_windows.go:82,149,203,255`、`runtime_model.go:100`、`ops/experiment_sandbox/sandbox_windows.go:59,264`。

Core c4a3b498、2294历史编译输入、13项关键源码及新增5项源码、原worker5f364598/bundle2a8e7013已绑定。SDK8df与wrapper292ad区别已澄清，原native128探针保留。SDK完整历史transitive build input closure仍未证明。

TOOL在首次providerRoute内被MODEL-only检查拒绝，发生于prepareEffectTx之前；Host所有工具/模型/来源/实验执行在PREPARED和STARTED提交之后。dispatchGate已有resourceWriteLock。wrapper292ad的makeTools.execute只await protocol.effect(TOOL)，不直接执行该工具。可以据此形成**Host代理路径拒绝**的历史推论；不得把generic503改称原在线typed NO_EFFECT。

更广的“任何允许路径均无外部效应”需要额外前提。源码设置普通AppContainer空capabilities、仅三条标准管道、隔离环境、input只读/output可写和job限制，均有历史绑定。但普通AppContainer没有LPAC的ALL APPLICATION PACKAGES opt-out；OS共享授权/IPC并非由该源码完整枚举。网络默认拒绝有平台依据，历史有效WFP/loopback例外状态未捕获。微软资料仅说明平台机制，不能证明本次历史机状态。[AppContainer/LPAC](https://learn.microsoft.com/en-us/windows/win32/secauthz/implementing-an-appcontainer)、[资源隔离](https://learn.microsoft.com/en-us/windows/win32/secauthz/appcontainer-isolation)、[网络隔离与例外](https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/troubleshooting-uwp-firewall)。

没有发现或声称一次真实沙箱逃逸。缺口是把局部控制推成完整历史事实。私有scratch写入本身不是外部TOOL效果；仍不能据此跳过更广证明。保留完整15项 `premise-matrix.json`，缺项不签发C重建。若合同只需某一具体Host工具路径，应先明确缩窄证明命题和消费方，不在实现时偷偷缩窄。

native receipt实际job_total_processes=2；ActiveProcessLimit1不能改写成历史总共一个进程。可接受原回执证明最终job active0、exit124、timeout、streams/cleanup/output完成。artifacts=[]、queue_required=false、无queue_control支持窄分支，原始frame语义和DB全量census须由另行接受的实际preflight核验。

### R2-F02 [High / P1] C具体lease handoff与supervisor入口尚未闭合

位置：`backup_prepared_abandonment_handoff.go:181`、`backup_prepared_abandonment_upgrade.go:416`、`backup_upgrade.go:245`、`ops/supervisor/release_host/main.go:39`。

两个prepared升级工作流会内部取得源租约。外层为combined gate先持锁会造成再次获取失败；放锁后再进内部则留下检查至执行间隙。其他upgrade-local分支也必须被同一外层租约覆盖。release_host在OpenCanary之后才取lease并直接store.Open；C中心qualification检查不等于replacement gate，它不在当前production allowlist。

限定修订见 `C-minimal-addendum.json`：外层一次取得精确native lease→两namespace组合检查→读取key/protected/DB→全工作流结束后释放；两个prepared分支接收不可由JSON构造的借用capability，重新验证Held/root，不重复取得、不关闭外层lease。release_host先经过同一组合检查，或通过可测硬规则证明只接受全新disposable root。没有宽泛callback、skip布尔或解除锁再检查。

最小新增现有文件：backup_upgrade.go、backup_prepared_abandonment_upgrade.go、backup_prepared_abandonment_handoff.go、backup_prepared_abandonment_upgrade_other.go、ops/supervisor/release_host/main.go。另加domain平台借用adapter与release_host平台gate及对应4组测试；完整准确列表在JSON。其余原C范围保留，需先冻结addendum再开Source卡。

### R2-F03 [High / P1] 原verifier closure仍不能满足严格STOP

位置：`internal/host/runtime_verifier_process_windows.go:219-226`。

源码defer close会cancel、关闭管道并调用原cmd.Wait；管理同步响应可以支持此收尾路径已执行的推论。Wait返回值被丢弃，不能写成captured native wait成功、numeric exit0或已获原始退出回执。原worker closure与verifier closure是独立事实；当前strict STOP仍不可执行。

可分析另一类证明：若本次确实在Host196行Execute错误返回，则204行短Token及process.verify(job)不可到达；verifier main握手后仅等待完整job，Verify之前无HTTP业务调用。ensureRuntimeVerifier创建principal/grants不等于给子进程发credential。但实际installed verifier二进制与main/protocol/client及init闭合绑定、本次历史错误路径绑定、所有stdin/凭据传递路径还需补齐。即使补齐，只能叫SOURCE_DERIVED_NEVER_JOB_AUTHORIZED，不能叫nativeclosed，也不能自动替换现STOP合同。最小缺证与独立Source/操作边界见 `STOP-alternative-proof-prerequisites.json`。不重放旧request，不凭PIDabsence通过。

### R2-F04 [High / P1] STOP须冻结具体接受锚点

位置：STOP架构的accepted F01/plan输入边界。

caller JSON与expect-plan-sha256只能证明自洽，不能证明外部接受。最小可行方案是一次operation专用构建中固定已审plan和证据manifest hash，或有明确owner/更新规则的受保护registry；仍逐项校验事实，不能只查allowlist。默认空表可使功能安全禁用，但不能当可操作Source已完整交付。具体anchor合同与测试需另冻；它不能凭空对同SID管理员形成密码学独立性，local receipt/Owner trust必须如实声明。

## 已解决的设计项与后续验收

- B：首次gate私有构造点、knownroute/marker/key/零effect-stage、不可由第二gate或generic503提升；admission close、所有broker goroutine join/completion drain、heartbeat join全部明确。实现后要用并发晚帧/晚completion/持久化失败测试证明；不得只等Bridge.Done。
- C F02/F03：schema24允许MANIFEST、GENERATED、LIVE、currentOwner、run_id=null。artifact_uses在run=nil立即返回；五个domain version及refs、upload、observation、outbox、snapshot、marker写集覆盖现有event/put附带写。保持原Task/NoProgress/财务/原输出清单；FullPlan hash避免自引用。当前是合同比对，未运行事务fixture。
- D F05：三个runtime-only查找、精确binding reuse、历史grant按自身Run/Task/epoch、schema24幂等索引与原子单调链、相同Goal/输入/NoProgress均已明确。D-addendum01有效覆盖原stub声明：必须接受真实B的validatedQualificationFailureTx并经真实firstgate/drain/terminal路径生成fixture。
- D runner：node:test真实desktop库和现有Python Playwright实际React workbench路径合理。新测试不得以组件mock、插入FAILED行或总返回true替代production proof与UI交互。
- STOP：console广播分支明确禁用；exact handle/creation/SID/image/parent、一次terminate、原handle wait及停止后真实lease设计合理。BEGIN IMMEDIATE后query_only=ON是明确限定的zero-row例外，不是普通C lease替代；必须用真实driver/native WAL fixture证实保留writer reservation与DML/DDL拒绝。

本轮STRIDE从worker→broker、sandbox→OS、maintenance plan→DB/journal、prepare UI→fresh authority四个边界展开；相关OWASP类别为A01/A04/A08、LLM05/LLM06/LLM10。依赖未变，本轮未做全仓CVE扫描，不把源码设计审查写成供应链安全接受。

优点：权限由代码gate执行；raw ACK/frames和UNKNOWN money保留；证明作者与历史subject分离；新调用必须真实失败闭合后另行明确确认。仍应按本报告阻塞项修订并独立验收，不增加任何正式计数。
'''
md += '\n补充E（29872605）及3个文件哈希匹配：f255f4d4安装二进制、installation、main/protocol/client三项真实历史编译输入的绑定已补入。2294是两个binary的联合vector，不等于verifier精确init依赖闭合；公开响应refs也尚未独立证明历史196分支。该补充缩小never-job缺证清单，不改变本报告strict STOP_UNAVAILABLE或native closure结论。\n'
write('review.md',md)
write('freeze-invocation.json',{'argv':['python',str(OWN/'freeze_review.py')],'writes':'own receipts only','operation':'deterministic review packaging and frozen-input hash checks, not product test','expected_exit':0,'test_assertions':0})
files=[]
for p in sorted(OWN.iterdir()):
    if p.is_file() and p.name not in ('FINAL-manifest.json',):
        files.append({'path':p.name,'bytes':p.stat().st_size,'sha256':digest(p)})
write('FINAL-manifest.json',{'schema':'researchos.qualification-revision02-independent-review-manifest.v1','status':review['verdict'],'owner':review['owner'],'base_commit':BASE,'scope_sha256':review['scope_sha256'],'files':files,'formal_increment':0})
print(json.dumps({'review_sha256':digest(OWN/'review.json'),'review_md_sha256':digest(OWN/'review.md'),'manifest_sha256':digest(OWN/'FINAL-manifest.json'),'files':len(files),'verdict':review['verdict']},ensure_ascii=False))
