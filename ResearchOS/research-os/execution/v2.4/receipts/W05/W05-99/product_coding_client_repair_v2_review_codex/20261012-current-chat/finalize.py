from pathlib import Path
import hashlib,json,subprocess
O=Path(__file__).resolve().parent;ROOT=O.parents[6]
A=O.parents[1]/'product_coding_client_repair_v2_codex/20261012-current-chat'
C=Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/coding-client-v2-20261012')
D=ROOT/'.local/worktrees/w05-product-coding-client-repair-v2-20261012'
B=C/'.local/builds/product-coding-client-repair-v2-20261012'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(n,v):(O/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert sha(A/'manifest.json')=='44379f527ddaf8935888c64470489c36820470e7ab8a6e3d5047b9dcb41c694a'
assert sha(A/'source-bundle.json')=='2e949f70fd39ccbcf91b82884ec3fa86ea7b82040bf93bc78413080dfa35ec46'
assert sha(B/'apps/web/src/workbench.jsx')==sha(C/'apps/web/src/workbench.jsx')== 'edc6fed2ac1dc0cc1a72a0f4650f2d89f42fc6f68d5d257d976c75f958a3c730'
for wt in [C,D]:
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=wt,text=True).strip()=='b20c816ec346c1dad1534b18b02abbb4f47c4628'
 assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=wt).strip()
facts=read(O/'review-fixtures-results.json');assert len(facts['facts'])==6
assert next(f for f in facts['facts'] if f['scenario']=='prepare-timeout-late-terminal')['timeout_ms']==45000
assert read(O/'review-fixtures.invocation.json')['exit']==read(O/'status-recovery-dom.invocation.json')['exit']==0
canon={}
for name in ['current_spec.json','checkpoint.json','step_state.json','path_ownership.json','commands.json']:
 p=ROOT/'execution/v2.4'/name;canon[name]=dict(sha256=sha(p))
write('main-canon-end-observation.json',dict(read_only_observation=True,head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),files=canon))
findings=[
dict(id='W05-CODING-V2-001',priority='P2',title='Preserve a late PREPARE terminal result after the production timeout',path='apps/desktop/main/lib/desktop-management.js',lines=[430,455,538,540],related_lines=[342,343,662],
 trigger='PREPARE_CODING exceeds its unchanged 45000ms timer; valid original RESULT arrives later while the native process and host stay unchanged.',
 observed='onLine clears pending and resolves an already rejected promise. prepareCoding never validates or stores the late request_id/request_hash. The retained operation stays PREPARE_UNRESOLVED without identity. STATUS throws CODING_PREPARE_ORIGINAL_UNRESOLVED and another PREPARE throws CODING_ORIGINAL_REQUEST_PENDING.',
 impact='An ordinary slow preparation permanently blocks coding setup for this Desktop manager even after an authoritative late result is available; the original request cannot be reconciled.',
 evidence='fixtures/prepare-timeout-late-terminal/frames.json; review-fixtures-results.json',
 repair='Give the retained original operation a terminal-reply handler independent of the caller promise; validate and adopt the original late result exactly once before clearing the shared pending barrier. Keep invalid or host-mismatched replies quarantined.'),
dict(id='W05-CODING-V2-002',priority='P2',title='Settle an authoritative PREPARE rejection so corrected input can retry',path='apps/desktop/main/lib/desktop-management.js',lines=[538,540],
 trigger='The private host responds to PREPARE_CODING with valid ERROR/MANAGEMENT_REJECTED, such as a missing source path before any intent is created.',
 observed='The explicit rejection throws CODING_PREPARE_REJECTED but leaves the newly created no-ID PREPARE_UNRESOLVED operation active. All later PREPARE and STATUS calls fail as in finding 001.',
 impact='A recoverable preparation input error requires a manager restart instead of allowing corrected paths; no ambiguity remains in this proven rejected case.',
 evidence='fixtures/prepare-authoritative-rejection/frames.json; review-fixtures-results.json',
 repair='Represent a validated authoritative PREPARE rejection as a terminal nonaccepted operation, retain its audit information, and permit corrected PREPARE only after the shared barrier is clear. Do not treat timeout or malformed replies as rejection.'),
dict(id='W05-CODING-V2-003',priority='P1',title='Recheck synchronous consent guards after the final awaited recheck returns',path='apps/desktop/main/lib/desktop-management.js',lines=[584,590],
 trigger='After the second recheckCodingConsent finishes its internal checks, a queued context-change microtask runs before confirmCoding resumes from await.',
 observed='The finally block clears consentPending and confirmCoding consumes/sends CONFIRM_CODING without checking current selection again. Synthetic fixture switches session-1 to session-2 in this exact microtask window and records one CONFIRM for session-1 followed by CODING_CONFIGURED.',
 impact='A user selection changed before send can still commit the old session scope. The comment claiming no await between final guard and write overlooks the outer await boundary.',
 evidence='fixtures/post-consent-await-context-switch/frames.json; review-fixtures-results.json',
 qualification='Deterministic synthetic event ordering injected via observeProcess callback; no claim that a native GUI race was exercised. All candidate methods and bound modules are unchanged.',
 repair='After the final await, synchronously verify active intent, no pending command, consent ownership, context/selection/resource generation, native host/process identity and expiry immediately before marking confirmSent and writing. Share the synchronous guard with recheckCodingConsent; do not add another await between it and exchange.')]
result=dict(schema='researchos.independent-coding-client-repair-v2-review/1',decision='REQUEST_CHANGES',candidate='b20c816ec346c1dad1534b18b02abbb4f47c4628',base='eb7f712d21268c87f9af9428048313c9361c52d6',
 evidence_class='SOURCE_BOUND_LOCAL_FIXTURE_AND_CHROMIUM_COMPONENT_REVIEW',findings=findings,
 original_findings=[dict(id='W05-CODING-001',status='FIXTURE_CLOSED',evidence='Main IPC now requires privileged callback; direct invocation with cancel prompts once and sends zero CONFIRM. Native dialog implementation reviewed, not shown interactively.'),
 dict(id='W05-CODING-002',status='FIXTURE_CLOSED',evidence='Expired intent is retained while STATUS is pending and same original receives late status.'),
 dict(id='W05-CODING-003',status='FIXTURE_CLOSED',evidence='PREPARE result retains request ID on context change; returning to original selection can STATUS without another PREPARE.'),
 dict(id='W05-CODING-004',status='COMPONENT_FIXTURE_CLOSED',evidence='Chromium STATUS recovery followed by one failed refresh and successful retry: confirms1, refreshes1, attempts2; repeated STATUS/remount do not duplicate successful refresh. NativeWorkbench parent callback reviewed, not full end-to-end V2 transport exercised.')],
 verification=dict(inputs=read(O/'input-verification.json')['checks'],passed_inputs=read(O/'input-verification.json')['passed'],build_input_count=6439,
 author_manifest_sha256=sha(A/'manifest.json'),source_bundle_sha256=sha(A/'source-bundle.json'),c_build_binding_sha256=sha(A/'c-build-binding.json'),supplement_sha256=sha(A/'supplement-01.json'),author_test_count=211,author_tests_independently_rerun=False,supplement_case_files_verified=1663,
 independent_old_closures=4,independent_new_reproductions=3,unchanged_production_timeout_ms=45000,bound_ui_source_sha256=sha(B/'apps/web/src/workbench.jsx')),
 limitations=['No live model or tool calls, native Root GUI interaction, full Core regression, provider qualification, Main integration or formal acceptance.',
 'Possible stale session/model reconciliation discrepancy considered at source level only; not reported as a finding without a suitable counterexample.',
 'Author full 211-test run is hash-verified evidence, not an independent rerun.'],
 history=['Initial verifier assumed a standalone raw-census.json; corrected to the author freeze.py line-census algorithm. Initial supplement parser used locale default encoding; corrected to explicit UTF-8. Neither failed verifier changed author files.',
 'Initial fast timeout reproduction used20ms; final sealed reproduction uses unchanged45000ms production timer.',
 'Scoped native PowerShell Remove-Item for own vite-review-cache was rejected by automatic approval policy (blocked by policy); cache retained and excluded, no alternate deletion attempted.'],
 actual_model_calls=0,actual_tool_calls=0,formal_acceptance_delta=0,parent_acceptance_delta=0,acceptance=[])
write('independent-review.json',result)
(O/'README.md').write_text("""# Independent coding client repair v2 review

Decision: **REQUEST_CHANGES**. Candidate: b20c816ec346c1dad1534b18b02abbb4f47c4628.

The original four findings pass their corresponding independent local/component checks. Three new findings remain: P2 lost late PREPARE result after the actual 45-second timeout; P2 permanent no-ID intent after an explicit PREPARE rejection; P1 context change in the outer final-await continuation still permits CONFIRM. See independent-review.json for source lines, exact trigger, repair direction, and evidence qualifications.

Verified 6548/6548 input checks, including 6439 build inputs and the C-bound modules/assets. The append-only author supplement's 1663 case files (185325030 bytes) and its 211/211 results match both copies and their sealed census; that complete suite was not independently rerun. Independent six native-management/IPC synthetic scenarios include three original-issue closures and three defect reproductions. Real Chromium component test exercises STATUS recovery, failed-refresh retry and remount deduplication: one CONFIRM, one successful refresh, two refresh attempts, zero page errors. NativeWorkbench's parent V2 callback was read, not end-to-end exercised.

Zero actual model calls, tool executions, external/paid/tunnel effects, Root GUI actions, Source/Canon mutations or formal/parent acceptance increments. Candidate author receipts and source worktrees remain unchanged. Only this review receipt was written.

Harness diagnostics: initial input checker assumed a separate census file; author uses a computed census. Supplement JSON required explicit UTF-8. Both were corrected before the final checks. Final timeout reproduction uses unmodified production45000ms, superseding a fast20ms exploration.

Cleanup: native PowerShell deletion of this review's vite-review-cache was rejected by automatic approval policy (blocked by policy). Cache retained, excluded from manifest; no alternate deletion used. Generated DOM input files, screenshot, HTML, frame logs and scripts are retained as evidence.
""",encoding='utf-8')
entries=[]
for p in sorted(O.rglob('*')):
 if p.is_file() and 'vite-review-cache' not in p.parts and p.name not in ['receipt_manifest.json','review-seal.json']:
  entries.append(dict(path=p.relative_to(O).as_posix(),sha256=sha(p),bytes=p.stat().st_size))
write('receipt_manifest.json',dict(files=entries,excluded=['vite-review-cache/**','receipt_manifest.json','review-seal.json']))
write('review-seal.json',dict(decision='REQUEST_CHANGES',decision_sha256=sha(O/'independent-review.json'),manifest_sha256=sha(O/'receipt_manifest.json'),files=len(entries)))
print(json.dumps(read(O/'review-seal.json')))

