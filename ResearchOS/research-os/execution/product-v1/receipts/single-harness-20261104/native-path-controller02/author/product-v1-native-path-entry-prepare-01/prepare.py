from pathlib import Path
import json, hashlib, difflib

here = Path(__file__).resolve().parent
base = here.parent / 'product-v1-real-electron-tree-diagnostic-revision-05'
old = (base / 'real-electron-flow.mjs').read_text(encoding='utf-8')
source = old
source = source.replace("const requireThat = (test, code) => { if (!test) throw Object.assign(new Error(code), { code }); };", """let activeGuardHistory = null;
let activeRunEvidence = null;
const requireThat = (test, code) => {
  if (activeGuardHistory) activeGuardHistory.push({ sequence: activeGuardHistory.length + 1, code, passed: !!test });
  if (!test) throw Object.assign(new Error(code), { code });
};""")
a = source.index('function requireChatGPTAuthentication(')
b = source.index('function inventory(', a)
source = source[:a] + r'''function requirePathEntryScope(scope) {
  requireThat(scope?.native_picker?.profile === 'INVALID_VALID_PATH_ENTRY_ONLY' &&
    scope?.budget?.task_submissions === 0 && scope?.budget?.model_calls === 0 &&
    scope?.budget?.automatic_retries === 0 && scope?.budget?.harness_id === 'codex',
  'PATH_ENTRY_ONLY_ZERO_TASK_MODEL_RETRY_BUDGET');
  const warning = scope.native_picker.validation_warning;
  requireThat(typeof warning?.caption === 'string' && warning.caption.length > 0 &&
    typeof warning?.text === 'string' && warning.text.length > 0 && HASH.test(warning.source_sha256 || ''),
  'BUILD07_FROZEN_WARNING_PINS_REQUIRED');
  requireThat(scope.source?.pins?.some(row => row.path === 'internal/host/native_folder_windows.go' &&
    row.sha256 === warning.source_sha256), 'WARNING_MATCHES_FROZEN_NATIVE_SOURCE_PIN');
  requireThat(Number.isSafeInteger(scope.deadlines?.picker_ms) && scope.deadlines.picker_ms >= 15000 &&
    scope.deadlines.picker_ms <= 90000 && scope.deadlines.flow_ms > scope.deadlines.picker_ms + scope.deadlines.close_ms + 10000,
    'PICKER_DEADLINE_MUST_FIT_FLOW_AND_CLEANUP');
}

function parseNativeReply(chosen, core, fixture, invalid) {
  requireThat(chosen?.exit === 0 && typeof chosen.stdout === 'string' &&
    Buffer.byteLength(chosen.stdout) <= 65536, 'NATIVE_REPLY_COMPLETE_BOUNDED_UTF8_JSON_REQUIRED');
  const reply = JSON.parse(chosen.stdout);
  requireThat(reply.schema === 'researchos.owned-native-path-entry/1' &&
    reply.status === 'VALID_SHELL_OK_CLOSED_REQUIRES_MAIN_BINDING' &&
    reply.clicked_ok === true && reply.valid_ok_attempted === true && reply.invalid_ok_attempted === true &&
    reply.invalid_kept_chooser_open === true && reply.outcome_uncertain === false &&
    reply.input_is_authorization === false && reply.actual_task_submissions === 0 &&
    reply.model_outcome === 'NOT_RUN_ZERO_BUDGET' &&
    reply.authorization_state === 'SHELL_CONFIRM_OBSERVED_MAIN_BINDING_NOT_YET_VERIFIED',
  'NATIVE_PATH_SEQUENCE_OR_OUTCOME_NOT_CONFIRMED_NO_RETRY');
  requireThat(reply.invalid_input?.path === invalid && reply.valid_input?.path === fixture &&
    reply.invalid_input.input_is_authorization === false && reply.valid_input.input_is_authorization === false &&
    reply.invalid_warning?.observed === true && reply.invalid_warning.owner_pid === core.pid &&
    Number.isSafeInteger(reply.dialog_hwnd) && reply.dialog_hwnd > 0 &&
    reply.invalid_warning.owner === reply.dialog_hwnd &&
    reply.invalid_input.dialog_hwnd === reply.dialog_hwnd && reply.valid_input.dialog_hwnd === reply.dialog_hwnd &&
    Array.isArray(reply.history) && reply.history.some(row => row.event === 'INVALID_DISMISSED_SAME_CHOOSER_RETAINED') &&
    reply.history.some(row => row.event === 'VALID_SHELL_DIALOG_CLOSED'), 'NATIVE_PATH_EVIDENCE_REQUIRED');
  return reply;
}

function verifyProjectBinding(context, listed, displayedPath, fixture) {
  requireThat(typeof context?.project_id === 'string' && context.project_id && context.session_id == null,
    'REAL_MAIN_FRESH_PROJECT_CONTEXT_REQUIRED');
  requireThat(listed?.ok === true && listed.completed === true && Array.isArray(listed.result?.items) &&
    listed.result.items.length === 1, 'REAL_MAIN_SINGLE_WORKSPACE_REPLY_REQUIRED');
  const binding = listed.result.items[0];
  requireThat(binding?.status === 'ACTIVE' && binding.project_id === context.project_id &&
    typeof binding.authorized_workspace_ref === 'string' && binding.authorized_workspace_ref &&
    binding.display_path === fixture && displayedPath === fixture, 'REAL_MAIN_ACTIVE_EXACT_FIXTURE_REQUIRED');
  for (const key of ['real_path', 'canonical_path']) {
    if (Object.hasOwn(binding, key)) requireThat(binding[key] === fixture, 'REAL_MAIN_CANONICAL_PATH_MISMATCH:' + key);
  }
  return binding;
}

''' + source[b:]
source = source.replace('export async function run(scopeFile, expectedScopeSHA) {', 'async function runPrepared(scopeFile, expectedScopeSHA) {')
source = source.replace('requireDiagnosticScope(scope);', 'requirePathEntryScope(scope);')
source = source.replace("  requireThat(scope.contract_sha256 === CONTRACT, 'HARNESS_CONTRACT_PIN_REQUIRED');", "  requireThat(scope.contract_sha256 === CONTRACT, 'HARNESS_CONTRACT_PIN_REQUIRED');\n  requireThat(folded(scope.contract_source?.path || '') === folded('D:/作品集/ResearchOS/research-os/execution/product-v1/contracts/harness.v1.interface.rev2.json'), 'ROOT_MAIN_CONTRACT_PATH_REQUIRED');\n  pin(scope.contract_source.path, CONTRACT);")
source = source.replace("  fs.mkdirSync(scope.run_root);", "  activeRunEvidence.phase = 'CREATE_FRESH_RUN_ROOT';\n  activeRunEvidence.run_root = scope.run_root;\n  fs.mkdirSync(scope.run_root);")
source = source.replace("const state = { status: 'RUNNING'", "const state = { guard_history: activeGuardHistory, status: 'RUNNING'")
source = source.replace("  const deadlineError =", "  activeRunEvidence.state = state;\n  activeRunEvidence.phase = 'PRELAUNCH';\n  const deadlineError =")
source = source.replace("guard(); state.electron_launch_attempted = true;", "guard(); activeRunEvidence.phase = 'ELECTRON_LAUNCH_ATTEMPTED'; state.electron_launch_attempted = true;")
source = source.replace("model_outcome: 'NOT_RUN_DIAGNOSTIC_ONLY', windows_enforcement: 'NOT_MEASURED_DIAGNOSTIC_ONLY'", "model_outcome: 'NOT_RUN_ZERO_BUDGET', actual_model_calls: 0, windows_enforcement: 'NOT_MEASURED_PATH_ENTRY_PROFILE'")
source = source.replace("// Diagnostic owns an empty fixture directory; no workspace file contents.", "// Empty owned directory only. Invalid sibling is deliberately never created.")
source = source.replace("const workspace = path.join(scope.run_root, 'workspace');", "const workspace = path.join(scope.run_root, 'workspace');\n  const invalid = path.join(scope.run_root, 'invalid-nonexistent-' + scope.scope_nonce);\n  requireThat(!fs.existsSync(invalid), 'INVALID_TARGET_MUST_NOT_EXIST');")
source = source.replace('workspace, diagnostic_only: true, workspace_file_contents_read: false,', "workspace, invalid_path: invalid, profile: 'INVALID_VALID_PATH_ENTRY_ONLY', task_budget: 0, model_budget: 0, workspace_file_contents_read: false,")
source = source.replace("requireThat(core.image_sha256 === scope.bundle.control_sha256, 'ACTUAL_CORE_HASH_MISMATCH');", "requireThat(core.image_sha256 === scope.bundle.control_sha256 && Number.isSafeInteger(core.pid) && core.pid > 0 &&\n      /^[0-9]+$/.test(core.created_ns || '') && /^host-[a-f0-9]{12}$/.test(core.host_id || ''), 'ACTUAL_CORE_IDENTITY_MISMATCH');")
source = source.replace("    write('owned-core.json',", "    const pickerUntil = Math.min(until - scope.deadlines.close_ms - 5000, Date.now() + scope.deadlines.picker_ms);\n    requireThat(pickerUntil > Date.now() + 10000, 'PICKER_TIME_REMAINING_REQUIRED');\n    write('owned-core.json',")
source = source.replace("action_deadline_utc: new Date(until).toISOString()", "action_deadline_utc: new Date(pickerUntil).toISOString()")
source = source.replace("    const helperOutcome =", "    activeRunEvidence.phase = 'NATIVE_HELPER_RUNNING_AUTHORIZATION_UNKNOWN';\n    state.native_workspace_authorization = 'UNKNOWN_WHILE_NATIVE_HELPER_PENDING';\n    const helperHistoryPath = path.join(receipts, 'native-helper-history.ndjson');\n    fs.writeFileSync(helperHistoryPath, '', {flag: 'wx'});\n    const helperStdoutPath = path.join(receipts, 'native-helper-stdout-prefix.bin');\n    const stdoutFD = fs.openSync(helperStdoutPath, 'wx');\n    const helperOutcome =")
source = source.replace("'-CoreIdentityPath', path.join(receipts, 'owned-core.json')],", "'-CoreIdentityPath', path.join(receipts, 'owned-core.json'), '-HistoryPath', helperHistoryPath],")
source = source.replace("const chunks = []; let stdoutBytes = 0, stderr = '';", "const chunks = []; const stdoutHash = crypto.createHash('sha256'); let stdoutBytes = 0, storedBytes = 0, stderr = '';\n      let stdoutClosed = false;\n      const closeRaw = () => { if (!stdoutClosed) { stdoutClosed = true; try { fs.closeSync(stdoutFD); } catch(error) { state.helper_stdout_io_error = safeText(error.message); } } };")
source = source.replace("        stdoutBytes += chunk.length;", "        stdoutBytes += chunk.length; stdoutHash.update(chunk);\n        const prefix = chunk.subarray(0, Math.max(0, 65536 - storedBytes));\n        if (prefix.length && !state.helper_stdout_io_error) { try { fs.writeSync(stdoutFD, prefix); storedBytes += prefix.length; } catch(error) { state.helper_stdout_io_error = safeText(error.message); } }\n        state.helper_stdout_progress = {received_bytes: stdoutBytes, retained_prefix_bytes: storedBytes, retained_prefix: helperStdoutPath, history_journal: helperHistoryPath};")
source = source.replace("helper.on('error', error => resolve({ exit: null, error: safeText(error.message) }));", "helper.on('error', error => { closeRaw(); resolve({ exit: null, error: safeText(error.message) }); });")
source = source.replace("      helper.on('close', exit => {", "      helper.on('close', exit => {\n        closeRaw(); state.helper_stdout_progress = {...state.helper_stdout_progress, final_sha256: stdoutHash.digest('hex'), received_bytes: stdoutBytes};\n        if (state.helper_stdout_io_error) return resolve({ exit, stdout: null, stdout_bytes: stdoutBytes, error: 'HELPER_STDOUT_RECEIPT_WRITE_FAILED', stderr: safeText(stderr) });")
source = source.replace("    const chosen = await bounded(() => helperOutcome, 45000);", "    const helperWaitMs = pickerUntil + scope.deadlines.close_ms + 3000 - Date.now();\n    const chosen = await bounded(() => helperOutcome, helperWaitMs);")
a = source.index('    let pickerResult;')
b = source.index('\n  } catch (error) {', a)
source = source[:a] + r'''    // Preserve raw failure history before interpreting success. No truncation of
    // helper JSON and no automatic second helper invocation after uncertainty.
    write('native-folder-automation.json', chosen);
    const pickerResult = parseNativeReply(chosen, core, workspace, invalid);
    requireThat(pickerResult.invalid_warning.caption === scope.native_picker.validation_warning.caption &&
      pickerResult.invalid_warning.text === scope.native_picker.validation_warning.text, 'NATIVE_WARNING_PIN_MISMATCH');
    state.native_picker_cleanup = pickerResult.cleanup;
    state.native_workspace_authorization = pickerResult.authorization_state;
    state.native_picker = 'REAL_INVALID_WARNING_RETAINED_VALID_SHELL_OK_OBSERVED';
    activeRunEvidence.phase = 'SHELL_CONFIRM_OBSERVED_MAIN_BINDING_NOT_YET_VERIFIED';
    const resultPanel = page.locator('.project-open-result[role="status"]');
    await bounded(() => resultPanel.waitFor({ state: 'visible', timeout: Math.min(60000, until - Date.now()) }), 60000);
    requireThat(await resultPanel.count() === 1, 'REAL_PROJECT_SUCCESS_PANEL_NOT_UNIQUE');
    const shownPath = resultPanel.locator('p.break-all');
    requireThat(await shownPath.count() === 1, 'PROJECT_DISPLAY_PATH_NOT_UNIQUE');
    const displayedPath = await shownPath.textContent();
    requireThat(displayedPath === workspace, 'UI_DISPLAY_PATH_NOT_EXACT_OWNED_FIXTURE');
    await screenshot('02-project-created-path');
    // Existing readonly Main/preload calls only. These are independently
    // observed current state, not the original chooseWorkspace Promise reply.
    const context = await observe(() => page.evaluate(() => window.researchos.desktop.context()));
    const listed = await observe(() => page.evaluate(() => window.researchos.v2['workspace.list']({})));
    write('main-current-project-observation.json', {
      source: 'EXISTING_TYPED_MAIN_BRIDGES_DESKTOP_CONTEXT_AND_V2_WORKSPACE_LIST',
      timing: 'AFTER_REAL_SHELL_CONFIRM_AND_UI_SUCCESS_BEFORE_OPEN_WORKBENCH',
      original_choose_workspace_reply_captured: false, context, listed, displayed_path: displayedPath,
    });
    const binding = verifyProjectBinding(context, listed, displayedPath, workspace);
    state.project_id = context.project_id;
    state.authorized_workspace_ref = binding.authorized_workspace_ref;
    state.public_display_path = binding.display_path;
    state.private_real_path = Object.hasOwn(binding, 'real_path') ? 'EXACT_FIXTURE_OBSERVED' : 'NOT_EXPOSED_BY_PUBLIC_BRIDGE';
    state.native_workspace_authorization = 'REAL_MAIN_ACTIVE_PROJECT_WORKSPACE_BINDING_OBSERVED';
    activeRunEvidence.phase = 'REAL_MAIN_ACTIVE_BINDING_OBSERVED';
    const open = resultPanel.getByRole('button', { name: '打开工作台', exact: true });
    requireThat(await open.count() === 1 && await open.isEnabled(), 'OPEN_WORKBENCH_BUTTON_UNIQUE_ENABLED_REQUIRED');
    guard(); await bounded(() => open.click());
    await bounded(() => page.waitForFunction(projectId => {
      const url = new URL(window.location.href);
      return url.pathname === '/p/' + encodeURIComponent(projectId) || url.hash === '#/p/' + encodeURIComponent(projectId);
    }, context.project_id));
    const afterContext = await observe(() => page.evaluate(() => window.researchos.desktop.context()));
    requireThat(afterContext.project_id === context.project_id && afterContext.session_id == null, 'PROJECT_CONTEXT_CHANGED_ON_OPEN');
    write('main-context-after-open.json', { source: 'EXISTING_TYPED_MAIN_DESKTOP_CONTEXT', context: afterContext });
    route(); await screenshot('03-workbench-zero-task');
    activeRunEvidence.phase = 'WORKBENCH_OPEN_SAME_PROJECT_ZERO_TASK';
    state.status = 'REAL_NATIVE_PATH_ENTRY_AND_PROJECT_BINDING_OBSERVED_NOT_PRODUCT_ACCEPTED';
''' + source[b:]
source = source.replace("    if (state.actual_dom_submit_attempts && !state.task?.terminal) state.model_outcome = 'UNKNOWN_NO_AUTOMATIC_RESUBMIT';\n", '')
source = source.replace("state.transport_routes = { observation: 'NO_HARNESS_ROUTES_DIAGNOSTIC_ONLY', expected: [] };", "state.transport_routes = { observation: 'NO_TASK_ENDPOINTS_NO_HTTP_INTERCEPTION_TYPED_MAIN_READS_ONLY', expected: [] };")
source = source.replace("state.outbox_ref_basis = 'NOT_READ_DIAGNOSTIC_ONLY';", "state.outbox_ref_basis = 'NOT_READ_ZERO_BUDGET';")
a = source.index("if (process.argv[1]")
source = source[:a] + r'''export async function run(scopeFile, expectedScopeSHA) {
  const history = [];
  activeGuardHistory = history;
  activeRunEvidence = {phase: 'PREFLIGHT'};
  try { return await runPrepared(scopeFile, expectedScopeSHA); }
  catch (error) {
    const known = activeRunEvidence.state;
    const failure = { schema: 'researchos.path-entry-runner-failure/1', status: 'RUNNER_FAILURE_PHASE_PRESERVED',
      code: safeText(error.code || error.message), guard_history: history,
      phase: activeRunEvidence.phase, run_root: activeRunEvidence.run_root || null,
      electron_launch_attempted: known?.electron_launch_attempted || false,
      native_workspace_authorization: known?.native_workspace_authorization || 'NOT_YET_ESTABLISHED',
      native_picker: known?.native_picker || 'NOT_YET_CONFIRMED',
      project_id: known?.project_id || null, close: known?.close || null,
      helper_stdout_progress: known?.helper_stdout_progress || null,
      task_submissions: 0, model_outcome: 'NOT_RUN_ZERO_BUDGET',
      stdout_must_be_preserved_by_root: true };
    // Root captures complete stdout even when no fresh run root was created.
    console.log(JSON.stringify(failure));
    return failure;
  } finally { activeGuardHistory = null; activeRunEvidence = null; }
}

if (process.argv[1] && folded(process.argv[1]) === folded(fileURLToPath(import.meta.url))) {
  const args = process.argv.slice(2);
  if (args.length !== 5 || args[0] !== '--execute' || args[1] !== '--scope' || args[3] !== '--scope-sha256') {
    console.log(JSON.stringify({ status: 'PREPARATION_ONLY_NOT_RUN', usage: 'Root supervised only: --execute --scope <reviewed absolute file> --scope-sha256 <reviewed hash>' }));
    process.exitCode = 2;
  } else {
    const result = await run(path.resolve(args[2]), args[4]);
    if (result.status !== 'REAL_NATIVE_PATH_ENTRY_AND_PROJECT_BINDING_OBSERVED_NOT_PRODUCT_ACCEPTED' || !result.close?.app_close_resolved) process.exitCode = 2;
  }
}
'''
(here/'real-electron-flow.mjs').write_text(source, encoding='utf-8', newline='\n')
(here/'runner.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True), source.splitlines(True), fromfile='revision05/real-electron-flow.mjs', tofile='native-path-entry01/real-electron-flow.mjs')),encoding='utf-8')
template=json.loads((base/'scope.template.json').read_text(encoding='utf-8'))
template['status']='NOT_RUN_TEMPLATE_REQUIRES_BUILD07_PINS_ROOT_REVIEW_AND_EXACT_JOB'
template['source']['head']='2b39fe3a6e8d69981a4079bb585086dca98b283e'
template['source']['pin_status']='CP635_BUILD07_EXACT_INTEGRATED_SOURCE_ROOT_VERIFIED'
source_root=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-build-07-20261104')
template['source']['root']=str(source_root)
template['source']['pins']=[row for row in template['source']['pins'] if row['path']!='execution/product-v1/contracts/harness.v1.interface.rev2.json']
template['contract_source']={'path':'D:/作品集/ResearchOS/research-os/execution/product-v1/contracts/harness.v1.interface.rev2.json',
 'sha256':'046a49b2b1f82593fe86924913b2ee4d77152ac1cef7dbbb86562f6dfe0cfa1c','role':'ROOT_MAIN_OUTER_INPUT_NOT_BUILD_WORKTREE_CONTENT'}
for row in template['source']['pins']:
    row['sha256']=hashlib.sha256((source_root/row['path']).read_bytes()).hexdigest()
template['bundle']={'root':str(source_root/'.local/desktop-v1-build-07'),
 'manifest_sha256':'ba4fbefa07e1ba9597ee54c894949edb5d33847e38b10d3f53ee8704d84fd6e7',
 'electron_sha256':'8d205e25b40da3ada4a08c92f32bfbd8e8d38edb4bfe443deea77fc9de685bac',
 'control_sha256':'4e1c951b65ef325a8d9e842d0e21e7a05ad6b49b631db6030353ce0f28380cce',
 'source_binding_review':'ROOT_VERIFIED_COMPLETE_INTEGRATED_SOURCE'}
template['launcher']['path']=str(source_root/'apps/desktop/launch-development.mjs')
template['launcher']['sha256']=hashlib.sha256((source_root/'apps/desktop/launch-development.mjs').read_bytes()).hexdigest()
template['harness']={'runner_sha256':hashlib.sha256((here/'real-electron-flow.mjs').read_bytes()).hexdigest(),
 'folder_helper_sha256':hashlib.sha256((here/'choose-owned-folder.ps1').read_bytes()).hexdigest()}
template['native_picker']={'profile':'INVALID_VALID_PATH_ENTRY_ONLY','runtime_verified':False,'operator_fallback':False,
 'input':'UNIQUE_OWNED_DIRECT_EDIT_SYSTEM_MARSHALLED_WM_SETTEXT_WM_GETTEXT',
 'input_is_authorization':False,'button':'SINGLE_POSTED_STANDARD_BM_CLICK_THEN_OBSERVE_ACTUAL_EFFECT_NO_RETRY',
 'validation_warning':{'caption':'ResearchOS','text':'文件夹路径无效或不存在。请输入已有的文件夹路径后重试。','source_sha256':'1d52e52aa2c4bbc2653156fd3602c6f6ab9fd208342a154f0e1c2ac6a2ebef6a','status':'CP634_EXACT2_ROOT_REVIEWED'},
 'failure_cleanup':'ONLY_REVALIDATED_SAME_CHOOSER_IDCANCEL_IF_NO_UNCERTAIN_ACTION_ELSE_ROOT_JOB_UNKNOWN',
 'deadline_wire':'STRICT_ORIGINAL_UTC_STRING_YYYY_MM_DD_THH_MM_SS_FFF_Z_INVARIANT'}
template['budget']={'task_submissions':0,'model_calls':0,'automatic_retries':0,'harness_id':'codex'}
template['deadlines']['picker_ms']=60000
template.pop('diagnostic_result_semantics',None)
template['project_observation']='REAL_UI_EXACT_PATH_THEN_EXISTING_TYPED_MAIN_CONTEXT_WORKSPACE_LIST_NOT_ORIGINAL_CHOOSEWORKSPACE_REPLY'
template['selector_binding']['source_head']=template['source']['head']
template['selector_binding']['bundle_manifest_sha256']=template['bundle']['manifest_sha256']
template['payment_policy']={'submission':'ABSENT_IN_THIS_ZERO_BUDGET_CONTROLLER_NO_CAPABILITY_OR_AUTH_PROBE'}
(here/'scope.template.json').write_text(json.dumps(template,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(here/'helper.diff').write_text(''.join(difflib.unified_diff((base/'choose-owned-folder.ps1').read_text(encoding='utf-8').splitlines(True),
 (here/'choose-owned-folder.ps1').read_text(encoding='utf-8').splitlines(True),fromfile='revision05/choose-owned-folder.ps1',tofile='native-path-entry01/choose-owned-folder.ps1')),encoding='utf-8')
