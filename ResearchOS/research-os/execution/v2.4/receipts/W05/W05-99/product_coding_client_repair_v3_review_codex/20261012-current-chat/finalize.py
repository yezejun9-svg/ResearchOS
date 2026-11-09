from pathlib import Path
import hashlib,json,subprocess
O=Path(__file__).resolve().parent;ROOT=O.parents[6]
A=O.parents[1]/'product_coding_client_repair_v3_codex/20261012-current-chat'
C=Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/coding-client-v3-20261012')
OLD=O.parents[1]/'product_coding_client_repair_v2_review_codex/20261012-current-chat'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(n,v):(O/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert sha(A/'manifest.json')=='7cab3b1e93d114b8a3a9e8fbcc61d8a26d9581e1a318ea081a24dec2637340ff'
assert sha(A/'source-bundle.json')=='86bfb5130e1cc0ce42957434b1b64f7c0c76cdc9384b6092beb4cf31b9dd8eee'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=C,text=True).strip()=='2fda8155d457784c22655be553af87b8f3b114f2'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=C).strip()
for row in read(OLD/'receipt_manifest.json')['files']:assert sha(OLD/row['path'])==row['sha256']
assert sha(OLD/'independent-review.json')=='730de4165869889202133f4419f0a738c2e317265d65acd9f13c3856382904c6'
assert sha(OLD/'receipt_manifest.json')=='39930f2639c332a336f55bde33ccdcc3fba481e025a992769f0d75b1a0d0127b'
v=read(O/'input-verification.json');assert v['checks']==v['passed']==8305 and not v['failures']
assert read(O/'raw-census-verification.json')['passed']
f=read(O/'review-fixtures-results.json');assert f['all_passed'] and len(f['facts'])==13
timers=[x for x in f['facts'] if x['scenario'].startswith('production-45000ms')]
assert len(timers)==3 and all(x['elapsed_ms']>=45000 for x in timers)
expired=next(x for x in timers if x['scenario'].endswith('expired-result'))
assert expired['elapsed_ms']>=61000
n=read(O/'native-repick-results.json')
assert n['pass'] and n['resourceGeneration']==2 and n['prepares']==2 and n['confirms']==n['privilegedPrompts']==n['refreshes']==1
for name in ['review-fixtures','status-recovery-dom','native-repick-dom']:
 inv=read(O/(name+'.invocation.json'));assert inv['exit']==0
 for suffix in ['stdout','stderr']:assert sha(O/(name+'.'+suffix))==inv[suffix+'_sha256']
status=(O/'status-recovery-dom.stdout').read_text(encoding='utf-8')
assert '"confirms":1' in status and '"refreshes":1' in status and '"refresh_attempts":2' in status and '"page_errors":[]' in status
canon={}
for name in ['current_spec.json','checkpoint.json','step_state.json','path_ownership.json','commands.json']:
 file=ROOT/'execution/v2.4'/name;canon[name]=dict(sha256=sha(file))
write('main-canon-end-observation.json',dict(read_only=True,head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),files=canon))
closed=[
 dict(id='W05-CODING-V2-001',status='CLOSED_SOURCE_BOUND_FIXTURE',evidence=['production-45000ms-timeout-late-valid-result','production-45000ms-timeout-late-expired-result'],result='Original onTerminal validates and applies result before barrier release independently of the abandoned caller promise. Actual45s timeout and61s delivery after60s TTL retain id/hash and permit original STATUS without extra PREPARE/CONFIRM.'),
 dict(id='W05-CODING-V2-002',status='CLOSED_SOURCE_BOUND_FIXTURE',evidence=['explicit-rejection-go-resource-reselection','production-45000ms-timeout-late-terminal-error','native-repick-dom'],result='Exact original null-result MANAGEMENT_REJECTED becomes audited PREPARE_REJECTED. After barrier settles, explicit corrected input/new trusted resource generation may PREPARE; uncertainty and ambiguous ERROR cannot rearm. Actual Chromium plus bound IPC/manager records Go1 changing to Go2 in second frame.'),
 dict(id='W05-CODING-V2-003',status='CLOSED_SOURCE_BOUND_FIXTURE',evidence=['post-consent-await-session-switch','post-consent-await-resource-switch','valid-explicit-confirm-exactly-once'],result='exchange.beforeWrite synchronously checks original intent, context, native identity, expiry and live resource generation after all awaits. Both microtask invalidations send zero CONFIRM; unchanged explicit acceptance sends exactly one.'),
 dict(id='W05-CODING-CLIENT-001',status='PRIOR_CLOSURE_RECHECKED',evidence=['privileged-cancel','valid-explicit-confirm-exactly-once','native-repick-dom'],result='Direct IPC cancel prompts once and writes zero CONFIRM; unchanged main privileged native consent remains required. Native dialog presentation is source reviewed, not interactively shown.'),
 dict(id='W05-CODING-CLIENT-002',status='PRIOR_CLOSURE_RECHECKED',evidence=['expiry-pending-barrier'],result='Exact expired original object and retirement history remain unchanged while its STATUS is pending.'),
 dict(id='W05-CODING-CLIENT-003',status='PRIOR_CLOSURE_RECHECKED',evidence=['prepare-context-change-retained'],result='Original PREPARE id remains after selection changes; return to original selection permits STATUS without another PREPARE.'),
 dict(id='W05-CODING-CLIENT-004',status='PRIOR_COMPONENT_CLOSURE_RECHECKED',evidence=['status-recovery-dom'],result='Chromium STATUS recovery, first refresh callback failure, retry, repeated STATUS and remount produce one CONFIRM, two refresh attempts and one successful refresh.')
]
report=dict(schema='researchos.independent-coding-client-repair-v3-review/1',decision='ACCEPT',acceptance_scope='SOURCE_AND_BOUND_LOCAL_FIXTURE_ONLY',
 candidate='2fda8155d457784c22655be553af87b8f3b114f2',base='b20c816ec346c1dad1534b18b02abbb4f47c4628',changed_paths=4,registered_paths=8,findings=[],closed_findings=closed,
 source_assessment=[
 'Production delta only desktop-management.js and main.js plus two relevant test files. IPC/preload/web surfaces remain byte-identical to b20.',
 'Exact original PREPARE correlation, native origin, immutable scope, ordered frozen checks, expiry and explicit error shape are validated before terminal settlement. Wrong-host, bad frozen check and ambiguous error fixtures quarantine the original.',
 'Final beforeWrite runs after serialization and before consumed/pending marks and stdin write in one synchronous turn. Main provides a trusted live codingDirectories.generation closure; renderer supplies no authority.',
 'The original shared command barrier, privileged consent, one-CONFIRM rule and successful V2 refresh deduplication are preserved.'
 ],
 verification=dict(input_checks=8305,passed_input_checks=8305,full_build_inputs=6439,build_input_digest=v['build_input_digest'],
 validator_binary_sha256='f884cd983336d0fd9cc454edc43071c959bf46c88d6f2aba788e5fa9aee542ed',
 descriptor_sha256='6caa84c002ff62c3cdaf6dd0b39c2e3a1afd9fa7a382a6a3a1fb3e24180a71f4',
 author_manifest_sha256=sha(A/'manifest.json'),source_bundle_sha256=sha(A/'source-bundle.json'),c_build_binding_sha256=sha(A/'c-build-binding.json'),
 raw_files=1741,raw_bytes=194930608,raw_census_sha256=read(O/'raw-census-verification.json')['census_sha256'],
 formula_locator_sha256=sha(A/'formula-locator.json'),old_b20_manifest49_members_unchanged=True,
 independent_management_ipc_scenarios=13,independent_Chromium_component_scenarios=2,actual_production_timeout_ms=45000,late_expired_delivery_elapsed_ms=expired['elapsed_ms'],
 author_bound_targeted_tests=32,author_complete_desktop_tests=218,author_Go_validator_pass=True,author_Chromium_scenarios=4,
 author_full_suite_independently_rerun=False,independent_build_performed=False),
 limitations=[
 'Exact source delta and bound local fixture acceptance only; not Main integration, integrated package, real provider qualification, actual first-use or W05/Main24/formal acceptance.',
 'Independent native identity and private Core replies are synthetic; privileged consent callbacks simulate cancel/accept. No actual Windows consent dialog or Root window was opened.',
 'STATUS browser uses synthetic bridge/refresh callback. Go-reselection browser uses actual bound IPC/manager plus synthetic trusted scope/resource picker/private replies. No real workspace authority granted.',
 'Full NativeWorkbench V2 parent reconciliation is source-reviewed and unchanged; independent DOM scope is DesktopCodingAuthorization.',
 'Author full218 suite, Go validator and build are hash-verified, not independently repeated.'
 ],
 history=[
 'Initial raw census reused v2 tab-separated algorithm and mismatched. Author append-only formula-locator specified sorted raw-relative [path,bytes,sha256] compact UTF-8 JSON; independent recomputation matches af23 exactly. Frozen evidence unchanged.',
 'Author first complete suite omitted RESEARCHOS_DESKTOP_ELECTRON; two renderer launch failures retained. Corrected218 suite separately preserved. No historical failure counters rewritten.',
 'One finalize tool submission had a JavaScript template-literal parse error before any tool execution/file write; corrected submission created this report.',
 'Exact scoped native PowerShell deletion of own vite-review-cache was rejected by automatic approval policy (blocked by policy). Cache retained/excluded, no alternate deletion attempted.'
 ],
 writes_scope='Only this new review receipt directory',source_canon_mutations=0,root_gui_actions=0,actual_model_calls=0,actual_tool_calls=0,external_paid_tunnel_actions=0,formal_acceptance_delta=0,parent_acceptance_delta=0,formal_case_acceptance=[])
write('independent-review.json',report)
(O/'README.md').write_text("""# Independent coding client repair v3 review

Decision: ACCEPT — SOURCE_AND_BOUND_LOCAL_FIXTURE_ONLY. Candidate2fda8155d457784c22655be553af87b8f3b114f2; baseb20c816ec346c1dad1534b18b02abbb4f47c4628.

All three b20 findings and the earlier four closure checks have independent corresponding evidence. No new actionable findings. Thirteen management/IPC scenarios pass, including unchanged45-second timeout with late valid RESULT/terminal ERROR, actual61-second delivery of an expired60-second result, original STATUS recovery, Go resource reselection, two final-await microtask invalidations, positive one-CONFIRM and wrong-host/malformed/ambiguous-error quarantine.

Two real Chromium component scenarios pass. STATUS recovery plus failed refresh retry succeeds exactly once across repeated STATUS/remount. Go reselection uses actual bound IPC and manager: first authoritative rejection, resource generation1 to2, second PREPARE carrying C:/trusted-go-2, one synthetic privileged acceptance, one CONFIRM, one refresh. Zero page errors. Windows consent and Core transport are synthetic, not an actual Root flow.

8305/8305 input checks pass including6439 build inputs, registered/bound modules/assets. Author census independently reproduces1741 files/194930608 bytes. Author32 targeted, Go validator,4 Chromium and corrected218 full desktop results are hash verified; full suite/build not independently repeated. Initial missing-Electron-environment failures remain preserved.

Acceptance covers this exact source delta and bound local fixtures only. Main integration, rebuilt integrated package, native Root flow, live qualification and formal/parent acceptance are outside this review. Model/tool/external/paid/tunnel/RootGUI counts and formal/parent increments are zero. Prior b20 report49 members and v3 scope assessment remain unchanged.

Census mismatch was resolved using the author append-only formula-locator: lexically sorted raw-relative [path,bytes,sha256] compact UTF-8 JSON rather than v2 tab-separated representation. No frozen evidence was edited.

Cleanup: automatic approval policy rejected deletion of this receipt's temporary vite-review-cache (blocked by policy). Cache retained/excluded, no alternate deletion attempted. Browser inputs/images/HTML and frame logs retained as evidence.
""",encoding='utf-8')
entries=[]
for p in sorted(O.rglob('*')):
 if p.is_file() and 'vite-review-cache' not in p.parts and p.name not in ['receipt_manifest.json','review-seal.json']:
  entries.append(dict(path=p.relative_to(O).as_posix(),sha256=sha(p),bytes=p.stat().st_size))
write('receipt_manifest.json',dict(files=entries,excluded=['vite-review-cache/**','receipt_manifest.json','review-seal.json']))
write('review-seal.json',dict(decision='ACCEPT',acceptance_scope='SOURCE_AND_BOUND_LOCAL_FIXTURE_ONLY',decision_sha256=sha(O/'independent-review.json'),manifest_sha256=sha(O/'receipt_manifest.json'),files=len(entries)))
print(json.dumps(read(O/'review-seal.json')))

