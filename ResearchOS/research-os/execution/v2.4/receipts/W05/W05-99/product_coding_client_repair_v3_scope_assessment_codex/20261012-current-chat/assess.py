from pathlib import Path
import json,hashlib,subprocess,datetime
O=Path(__file__).resolve().parent;ROOT=O.parents[6];RECEIPTS=O.parents[1]
N=RECEIPTS/'native_folder_visibility_scope_assessment_codex/20261012-current-chat'
N.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(d,n,v):(d/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
MAIN='b806a06fb62576c18dfd1e7174c1dfd929677506';BASE='b20c816ec346c1dad1534b18b02abbb4f47c4628'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==MAIN
OLD=RECEIPTS/'product_coding_client_repair_v2_review_codex/20261012-current-chat'
assert sha(OLD/'independent-review.json')=='730de4165869889202133f4419f0a738c2e317265d65acd9f13c3856382904c6'
assert sha(OLD/'receipt_manifest.json')=='39930f2639c332a336f55bde33ccdcc3fba481e025a992769f0d75b1a0d0127b'
for row in read(OLD/'receipt_manifest.json')['files']:assert sha(OLD/row['path'])==row['sha256']
paths=read(RECEIPTS/'product_coding_client_repair_v2_scope_assessment_codex/20261012-current-chat/scope-repair-assessment.json')['allowed_paths']
common=dict(created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),decision='SCOPE_CONFIRMED_FOR_REPAIR_NOT_CANDIDATE_ACCEPTANCE',assessor='codex:/root/runtime_identity_boundary',source_or_canon_changes=False,tests_run=0,actual_model_calls=0,actual_tool_calls=0,formal_acceptance_delta=0,parent_acceptance_delta=0,max_source_writers=2)
coding=dict(common,branch='coding-client-repair-v3',base_commit=BASE,allowed_paths=paths,
 assessment='The three b20 findings can be repaired inside the original eight registered Desktop/client paths. Prefer changing only main.js, desktop-management.js and directly relevant existing tests unless additional original paths are needed. No Core/public schema or Native visibility scope expansion.',
 protected_evidence=dict(review_sha256=sha(OLD/'independent-review.json'),manifest_sha256=sha(OLD/'receipt_manifest.json'),original49files_verified_unchanged=True,prior_four_closures_preserved=True,old_C_D_worktrees_frozen=True),
 requirements=[
 'Keep the original PREPARE operation, message correlation, immutable scope and native origin binding independently of the UI/caller promise. Timeout rejects the caller without destroying original terminal processing.',
 'Route an exact valid late RESULT through one original-operation handler before releasing the shared command barrier. Adopt trusted id/hash and frozen scope once even when UI context changed. An expired late result still retains its original identity for read-only original STATUS; expiry never authorizes CONFIRM.',
 'The handler must reject/quarantine malformed, wrong-message, wrong-operation, wrong-host or wrong-process replies; validate all returned frozen scope/check fields against original scope. No new PREPARE or newer-intent overwrite while original pending/uncertain.',
 'Distinguish authoritative terminal ERROR/MANAGEMENT_REJECTED from timeout, malformed reply and broken identity. For an exact original PREPARE known rejected before creation, store terminal rejection audit, then retire only after shared barrier clears so corrected input may PREPARE. Do not blanket-retire uncertain/confimed operations.',
 'After the final awaited scope recheck returns, synchronously validate original active intent identity, consent ownership, shared pending state, host/dataRoot/control/parent identity, current context/selection/model/writer/revision, native resource generation and expiry immediately next to the private write. No await or deferred guard may intervene before consumed mark and frame dispatch.',
 'Main must expose the live resource generation as a trusted synchronous read to the manager; comparing only two frozen review objects does not establish the current generation at send time. Renderer payload must not supply authority or generation.',
 'Preserve explicit main-owned native consent, human-readable frozen review, cancellation with zero writes, original pending barrier across coding/qualification/SHUTDOWN, one CONFIRM maximum, and successful V2 refresh deduplication/retry from prior four repairs.'
 ],
 required_candidate_evidence=[
 'Unchanged45000ms PREPARE timeout followed by exact valid late RESULT: original id/hash retained, original STATUS works, no extra PREPARE/CONFIRM; include late arrival after request expiry.',
 'Valid original explicit ERROR permits corrected PREPARE after settled rejection and preserved audit; wrong/malformed host response remains quarantined and blocks new dispatch.',
 'Reproduce final inner-check to outer-await continuation microtask context switch and resource-generation switch independently: both send zero CONFIRM and retain unconsumed original.',
 'Unchanged valid explicit consent still sends one original CONFIRM. Prior four closure evidence remains immutable and run proportionate candidate regressions.',
 'Frozen new candidate exact-source/build descriptor/native binary/module and React bindings; standalone local fixtures are not Main, live qualification or formal acceptance.'
 ])
write(O,'scope-repair-assessment.json',coding)
E=RECEIPTS/'normal_desktop_first_use_causal_retry02_codex/20261012-current-chat/native-dialog-core-hidden-enumeration.json'
e=read(E);assert e['core_pid']==66564 and any(w['hwnd']==85200592 and w['class']=='#32770' and w['visible']==False for w in e['all_top_level_windows'])
prod='internal/host/native_folder_windows.go';raw=subprocess.check_output(['git','show',MAIN+':'+prod],cwd=ROOT);assert hashlib.sha256(raw).hexdigest()==sha(ROOT/prod)
native=dict(common,branch='native-folder-visibility',base_commit=MAIN,allowed_paths=[prod,'internal/host/native_folder_windows_test.go'],
 assessment='The existing native-folder implementation plus one Windows-only native component test file are sufficient. Preserve private Core windowsHide:true, IPC/SID/ACL checks, public schemas and workspace authority semantics. No native_pipe or Electron spawn edits are needed for the proposed repair.',
 source_observation=dict(path=prod,sha256=sha(ROOT/prod),lock_os_thread_already_present=True,callback_only_when_initial_nonempty=True,explicit_show_missing=True,explicit_COM_initialization_not_found_in_current_function_or_host_search=True),
 actual_failure_evidence=dict(path=str(E.relative_to(ROOT)),sha256=sha(E),core_pid=66564,dialog_hwnd=85200592,dialog_class='#32770',visible=False,window_mutations_in_receipt=0),
 causal_status='Root receipt proves a hidden dialog owned by the intended Core. The startup first-show explanation is supported by documented ShowWindow behavior and current hidden launch, but exact Shell callback/show ordering is not proven by source or API names; the isolated hidden-helper component test must prove the repair.',
 requirements=[
 'Retain existing runtime.LockOSThread/UnlockOSThread and install the initialized callback for both empty and nonempty initial paths. Preserve optional preselection as a suggestion only, never a confirmed choice.',
 'Ensure required COM STA initialization on that locked thread, handle HRESULT correctly, and balance successful initialization/uninitialization. Include S_FALSE balancing and refuse incompatible apartment state safely; keep changes in this production file.',
 'Show only the HWND delivered for this invocation of the trusted Shell chooser. Use lifecycle-bound ownership of any deferred event/timer, not a broad process/window sweep, global first-show changes, a console-show change, or a surviving goroutine that can touch a reused HWND.',
 'ShowWindowAsync is a viable implementation candidate, not proof of ordering. Establish that the eventual show happens after the startup-hidden behavior and survives initial Shell show processing; use actual visibility observation. Avoid SW_SHOWDEFAULT which reapplies startup settings.',
 'Treat foreground activation separately from visibility; OS foreground restrictions mean SetForegroundWindow is best-effort. No global focus hacks or authority bypass. Do not assert activation succeeded solely from a queued show call.',
 'Cancellation must return no chosen path and create no workspace binding, model/configuration, or tool effects. Preserve filesystem-only selection, PIDL freeing, UTF-16 lifetime, and native ACL/SID trust boundary.',
 'Use a stable callback/lifecycle where practical rather than allocating unbounded callback closures for repeated dialogs. Any timer/event must stop on completion or cancel before HWND reuse.'
 ],
 required_candidate_evidence=[
 'Compile an isolated test helper from the exact candidate with SysProcAttr.HideWindow true (or equivalent verified STARTF_USESHOWWINDOW/SW_HIDE); record actual startup flags and unique helper PID. The helper calls the production chooser without prewarming/consuming the startup first-show on another window.',
 'For empty initial and supplied initial cases, enumerate only exact helper-owned windows until its #32770 chooser is visibly shown with nonempty usable rectangle; record PID/HWND/class/visibility/rect/startup details. Do not use the test controller to ShowWindow the chooser.',
 'Cancel only the helper-owned dialog via ordinary cancel command; verify chooser returns cancellation/no path and helper exits normally. No registered workspace or live Host required, and no RootGUI/dialog/process operations.',
 'Run a second chooser in the same hidden helper to prove callback/COM/deferred-display lifetime ends cleanly and normal repeated opening remains visible and cancellable.',
 'Capture raw native enumeration and test invocation/output. A mocked ShowWindow return or source-only assertion does not pass visibility; a noninteractive environment is a separately blocked component branch.',
 'Original hidden Root dialog receipt remains immutable and the actual first-use flow remains unaccepted until a new correctly bound candidate is integrated and Root separately retries it.'
 ],
 primary_sources=[
 dict(url='https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-showwindow',supports='Startup information can override the first ShowWindow call; SW_SHOWDEFAULT reuses startup settings.'),
 dict(url='https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-showwindowasync',supports='Asynchronous show request queues work; nonzero return means the operation started, not proven visible completion.'),
 dict(url='https://learn.microsoft.com/en-us/windows/win32/api/shlobj_core/nf-shlobj_core-shbrowseforfolderw',supports='Requires COM initialization with apartment threading; cancelled selection returns NULL; caller frees returned PIDL.'),
 dict(url='https://learn.microsoft.com/en-us/windows/win32/api/shlobj_core/ns-shlobj_core-browseinfow',supports='Callback receives dialog notifications; optional application state is passed via lParam.'),
 dict(url='https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setforegroundwindow',supports='Foreground activation has OS restrictions and must not be equated with visibility.')
 ])
write(N,'scope-repair-assessment.json',native)
for dest in [O,N]:
 digest=sha(dest/'scope-repair-assessment.json');(dest/'scope-repair-assessment.sha256').write_text(digest+'\n',encoding='utf-8')
 print(str(dest),digest)
assert sha(OLD/'receipt_manifest.json')=='39930f2639c332a336f55bde33ccdcc3fba481e025a992769f0d75b1a0d0127b'

