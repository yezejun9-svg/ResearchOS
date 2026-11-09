// Prepared, not executed. Root must launch this Node process inside its existing
// exact, unnamed, kill-on-close Job before Resume. This runner does not self-certify
// that Job or replace the Root controller. Never invoke against an old state root.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawn } from 'node:child_process';
import { pathToFileURL, fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const HASH = /^[a-f0-9]{64}$/;
const CONTRACT = '046a49b2b1f82593fe86924913b2ee4d77152ac1cef7dbbb86562f6dfe0cfa1c';
const UIA_SHELL = 'C:/Users/yqyyds/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe';
const UIA_SHELL_SHA256 = '362a356ce7f0940ec74f73a8fc2c990a2cc24a38a11c90bbd8eca947110ad139';
const UI8_SELECTOR_SOURCE = {
  'apps/web/src/workbench.jsx': 'e0f4c6db45757b0f506b950fb5eb004de7358f1667cbaf876ab5addee7eadd19',
  'apps/web/src/screens.jsx': 'd7405a7bf396b97907dca9ac4bf9182295fba5251b9766e276a67f9ef6b573be',
};
const sha = data => crypto.createHash('sha256').update(data).digest('hex');
const fileSHA = name => sha(fs.readFileSync(name));
const folded = name => path.resolve(name).toLowerCase();
let activeGuardHistory = null;
let activeRunEvidence = null;
const requireThat = (test, code) => {
  if (activeGuardHistory) activeGuardHistory.push({ sequence: activeGuardHistory.length + 1, code, passed: !!test });
  if (!test) throw Object.assign(new Error(code), { code });
};
const inside = (parent, child) => { const rel = path.relative(parent, child); return rel && !rel.startsWith('..' + path.sep) && rel !== '..' && !path.isAbsolute(rel); };
const pin = (file, expected) => { requireThat(HASH.test(expected || '') && fileSHA(file) === expected, 'PIN_MISMATCH:' + path.basename(file)); };
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const dataOf = reply => { requireThat(reply?.ok === true, reply?.reason || 'TYPED_READ_FAILED'); return reply.data; };

function safeText(value) {
  // Keep no raw credential output. Original-byte digest and redaction status stay
  // available, while bounded text is sufficient for UI/boot error diagnosis.
  return String(value).replace(/Bearer\s+[^\s"']+/gi, 'Bearer [REDACTED]')
    .replace(/\b(?:sk-|sess-)[A-Za-z0-9_-]{12,}/g, '[REDACTED]')
    .replace(/((?:["'])?(?:api[_-]?key|access[_-]?token|refresh[_-]?token|authorization|password|client[_-]?secret|credential)(?:["'])?\s*[=:]\s*)(?:"(?:\\.|[^"\\\r\n])*"|'(?:\\.|[^'\\\r\n])*'|[^\s,;}]+)/gi, '$1"[REDACTED]"')
    .slice(0, 16384);
}

export function makeEnvironment(scope) {
  const root = scope.windows.system_root;
  const profile = scope.windows.normal_user_profile;
  requireThat(path.isAbsolute(root) && path.isAbsolute(profile), 'WINDOWS_PATHS_REQUIRED');
  const systemDrive = path.parse(root).root.replace(/[\\/]+$/, '');
  requireThat(/^[A-Za-z]:$/.test(systemDrive), 'WINDOWS_SYSTEMROOT_DRIVE_REQUIRED');
  // Every value is explicit. No ambient API keys, proxy, ROS, NODE_OPTIONS,
  // CODEX_HOME, custom instructions or an inherited PATH are copied.
  return {
    SystemRoot: root, WINDIR: root, SystemDrive: systemDrive.toUpperCase(), OS: 'Windows_NT',
    COMSPEC: path.join(root, 'System32/cmd.exe'), PATHEXT: '.COM;.EXE;.BAT;.CMD',
    PATH: [path.dirname(scope.codex.executable), path.dirname(scope.node.path),
      path.join(root, 'System32'), root].join(path.delimiter),
    USERPROFILE: profile, APPDATA: scope.windows.normal_app_data,
    LOCALAPPDATA: scope.windows.normal_local_app_data,
    TEMP: path.join(scope.run_root, 'tmp'), TMP: path.join(scope.run_root, 'tmp'),
    RESEARCHOS_DATA_DIR: path.join(scope.run_root, 'data'),
    RESEARCHOS_CLI_DISCOVERY: path.join(scope.run_root, 'discovery.json'),
    RESEARCHOS_DESKTOP_USER_DATA: path.join(scope.run_root, 'electron-user-data'),
    RESEARCHOS_SHARED_HOST_LOCATOR_DISABLED: '1',
    RESEARCHOS_CONTROL_EXE: path.join(scope.bundle.root, 'apps/desktop/resources/control/researchos-control.exe'),
    RESEARCHOS_DESKTOP_VERIFIER_MANIFEST: path.join(scope.bundle.root, 'apps/desktop/resources/control/runtime-verifier-installation.json'),
    RESEARCHOS_DESKTOP_RUNTIME_ASSETS_DIR: path.join(scope.bundle.root, 'apps/desktop/resources/control/runtime'),
    RESEARCHOS_WEB_DIR: path.join(scope.bundle.root, 'apps/web/dist'),
  };
}

function requirePathEntryScope(scope) {
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

function inventory(root) {
  const rows = [];
  function walk(folder) {
    for (const item of fs.readdirSync(folder, { withFileTypes: true })) {
      const target = path.join(folder, item.name);
      requireThat(!fs.lstatSync(target).isSymbolicLink(), 'FIXTURE_ALIAS_CREATED');
      if (item.isDirectory()) walk(target);
      else { requireThat(item.isFile(), 'FIXTURE_SPECIAL_FILE'); rows.push({ path: path.relative(root, target).replaceAll('\\', '/'), sha256: fileSHA(target), bytes: fs.statSync(target).size }); }
    }
  }
  walk(root); return rows.sort((a, b) => a.path.localeCompare(b.path));
}

function validateSDK(sdk) {
  pin(sdk.inventory_path, sdk.inventory_sha256);
  const expected = JSON.parse(fs.readFileSync(sdk.inventory_path, 'utf8'));
  requireThat(expected.schema === 'researchos.public-sdk-inventory/1' && expected.version === '1.62.1' &&
    folded(expected.root) === folded(sdk.root) && Array.isArray(expected.files) && expected.files.length > 0, 'SDK_INVENTORY_INVALID');
  const actual = inventory(sdk.root);
  const order = rows => rows.map(row => ({ path: row.path, sha256: row.sha256, bytes: row.bytes })).sort((a, b) => a.path.localeCompare(b.path));
  requireThat(JSON.stringify(order(expected.files)) === JSON.stringify(order(actual)), 'SDK_PACKAGE_DRIFT');
}

async function runPrepared(scopeFile, expectedScopeSHA) {
  requireThat(process.platform === 'win32', 'WINDOWS_REQUIRED');
  pin(scopeFile, expectedScopeSHA);
  const scope = JSON.parse(fs.readFileSync(scopeFile, 'utf8'));
  requireThat(scope.schema === 'researchos.real-electron-single-codex-scope/1' && scope.status === 'ROOT_APPROVED_REAL_RUN', 'PREPARATION_ONLY_NOT_RUN');
  requireThat(/^[a-zA-Z0-9._-]{24,128}$/.test(scope.scope_nonce || ''), 'SCOPE_NONCE_REQUIRED');
  requireThat(scope.root_supervision?.required === true && scope.root_supervision?.mechanism === 'ROOT_EXISTING_UNNAMED_JOB', 'ROOT_JOB_REQUIRED');
  requireThat(HASH.test(scope.root_supervision.controller_sha256 || '') && HASH.test(scope.root_supervision.launch_contract_sha256 || ''), 'ROOT_CONTROLLER_PINS_REQUIRED');
  requireThat(scope.root_supervision.outer_deadline_ms > scope.deadlines.flow_ms + scope.deadlines.close_ms + 10000, 'OUTER_DEADLINE_MUST_CONTAIN_FLOW_AND_CLOSE');
  requireThat(scope.deadlines.flow_ms > 0 && scope.deadlines.flow_ms <= 600000 && scope.deadlines.close_ms > 0 && scope.deadlines.close_ms <= 60000, 'DEADLINES_INVALID');
  requirePathEntryScope(scope);
  requireThat(scope.native_picker.operator_fallback === false, 'AUTOMATION_SCOPE_HAS_NO_OPERATOR_FALLBACK');
  requireThat(scope.contract_sha256 === CONTRACT, 'HARNESS_CONTRACT_PIN_REQUIRED');
  requireThat(folded(scope.contract_source?.path || '') === folded('D:/作品集/ResearchOS/research-os/execution/product-v1/contracts/harness.v1.interface.rev2.json'), 'ROOT_MAIN_CONTRACT_PATH_REQUIRED');
  pin(scope.contract_source.path, CONTRACT);
  requireThat(/^[a-f0-9]{40}$/.test(scope.source.head || '') && scope.source.pins?.length > 0, 'INTEGRATED_SOURCE_PINS_REQUIRED');
  for (const [name, expected] of Object.entries(UI8_SELECTOR_SOURCE)) {
    requireThat(scope.source.pins.some(row => row.path === name && row.sha256 === expected), 'EXACT_UI8_SELECTOR_SOURCE_PIN_REQUIRED:' + name);
  }
  pin(process.execPath, scope.node.sha256);
  requireThat(folded(process.execPath) === folded(scope.node.path), 'EXACT_NODE_REQUIRED');
  pin(path.join(HERE, 'real-electron-flow.mjs'), scope.harness.runner_sha256);
  pin(path.join(HERE, 'choose-owned-folder.ps1'), scope.harness.folder_helper_sha256);
  requireThat(folded(scope.windows.powershell) === folded(UIA_SHELL) &&
    scope.windows.powershell_sha256 === UIA_SHELL_SHA256, 'ROOT_REVIEWED_NORMAL_PWSH_7_REQUIRED_NO_POLICY_OVERRIDE');
  pin(scope.windows.powershell, scope.windows.powershell_sha256);
  pin(scope.codex.executable, scope.codex.sha256);
  pin(scope.launcher.path, scope.launcher.sha256);
  for (const row of scope.source.pins) pin(path.join(scope.source.root, row.path), row.sha256);
  requireThat(scope.playwright.version === '1.62.1', 'LOCKED_PLAYWRIGHT_REQUIRED');
  validateSDK(scope.playwright);
  const metadata = JSON.parse(fs.readFileSync(path.join(scope.playwright.root, 'package.json'), 'utf8'));
  requireThat(metadata.version === '1.62.1', 'PLAYWRIGHT_VERSION_DRIFT');
  const launcher = await import(pathToFileURL(scope.launcher.path).href);
  launcher.checkNativePath(scope.source.root);
  launcher.checkNativePath(scope.playwright.root);
  const bundle = launcher.validateBundle(scope.bundle.root);
  pin(path.join(bundle.bundle, 'development-manifest.json'), scope.bundle.manifest_sha256);
  pin(path.join(bundle.bundle, 'runtime/electron/electron.exe'), scope.bundle.electron_sha256);
  pin(path.join(bundle.bundle, 'apps/desktop/resources/control/researchos-control.exe'), scope.bundle.control_sha256);
  requireThat(scope.bundle.source_binding_review === 'ROOT_VERIFIED_COMPLETE_INTEGRATED_SOURCE', 'SOURCE_BOUND_BUILD_REQUIRED');
  const allowed = 'C:/Users/yqyyds/Documents/Codex/2026-11-04/task';
  requireThat(path.isAbsolute(scope.run_root) && inside(allowed, scope.run_root), 'NEW_C_SCOPE_REQUIRED');
  launcher.validateStatePath(scope.run_root, bundle.bundle);
  for (const key of ['normal_user_profile', 'normal_app_data', 'normal_local_app_data']) launcher.checkNativePath(scope.windows[key]);
  const env = makeEnvironment(scope);
  const actualEnvNames = Object.keys(env).sort();
  requireThat(!actualEnvNames.some(name => /^(OPENAI_|ANTHROPIC_|AZURE_|CODEX_|NODE_|HTTP_PROXY$|HTTPS_PROXY$|ALL_PROXY$)/i.test(name)), 'UNEXPECTED_ENV');

  activeRunEvidence.phase = 'CREATE_FRESH_RUN_ROOT';
  activeRunEvidence.run_root = scope.run_root;
  fs.mkdirSync(scope.run_root); // no recursive root creation, no overwrite or reuse
  for (const dir of ['workspace', 'receipts', 'screenshots', 'tmp']) fs.mkdirSync(path.join(scope.run_root, dir));
  const receipts = path.join(scope.run_root, 'receipts');
  const write = (name, value) => fs.writeFileSync(path.join(receipts, name), JSON.stringify(value, null, 2) + '\n', { flag: 'wx' });
  const workspace = path.join(scope.run_root, 'workspace');
  const invalid = path.join(scope.run_root, 'invalid-nonexistent-' + scope.scope_nonce);
  requireThat(!fs.existsSync(invalid), 'INVALID_TARGET_MUST_NOT_EXIST');
  // Empty owned directory only. Invalid sibling is deliberately never created.
  const started = Date.now(), until = started + scope.deadlines.flow_ms;
  let timedOut = false, closing = false, app = null, helper = null, page = null;
  const state = { guard_history: activeGuardHistory, status: 'RUNNING', formal_increment: 0, product_increment: 0,
    scope_sha256: expectedScopeSHA, scope_nonce: scope.scope_nonce, source_head: scope.source.head,
    bundle_manifest_sha256: scope.bundle.manifest_sha256,
    root_job_proof: 'EXTERNAL_ROOT_CONTROLLER_ONLY_NOT_SELF_VERIFIED',
    allowed_task_submissions: 0, actual_dom_submit_attempts: 0, actual_transport_post_count: 'NOT_INSTRUMENTED',
    renderer_routes: [], event_refs: [], console: [], main_reports: [],
    close: { attempted: false, app_close_resolved: false, owned_core_exit: 'UNVERIFIED' },
    model_outcome: 'NOT_RUN_ZERO_BUDGET', actual_model_calls: 0, windows_enforcement: 'NOT_MEASURED_PATH_ENTRY_PROFILE' };
  activeRunEvidence.state = state;
  activeRunEvidence.phase = 'PRELAUNCH';
  const deadlineError = () => Object.assign(new Error('FLOW_DEADLINE'), { code: 'FLOW_DEADLINE' });
  const guard = () => { if (timedOut || closing || Date.now() >= until) throw deadlineError(); };
  const bounded = async (work, maximum = 30000) => {
    guard(); const ms = Math.max(1, Math.min(maximum, until - Date.now())); let timer;
    try { return await Promise.race([work(), new Promise((_, reject) => { timer = setTimeout(() => { timedOut = Date.now() >= until; reject(deadlineError()); }, ms); })]); }
    finally { clearTimeout(timer); }
  };
  const log = (type, value) => {
    const raw = String(value), text = safeText(raw);
    if (state.console.length < 1000) state.console.push({ type, text, raw_sha256: sha(raw), redacted_or_truncated: text !== raw });
    else state.console_truncated = true;
    if ((type.startsWith('main:') || type === 'stdout') && raw.startsWith('ROS_DESKTOP_REPORT ')) {
      try {
        const parsed = JSON.parse(raw.slice('ROS_DESKTOP_REPORT '.length));
        const report = parsed.event === 'ready_to_show' ? { event: parsed.event,
          management_state: parsed.management_state, management_reason: safeText(parsed.management_reason || ''),
          host_health: parsed.host_health, host_url: parsed.host_url, owned_core_identity: parsed.owned_core_identity,
          renderer: { react_root: parsed.renderer?.react_root, bridge: parsed.renderer?.bridge },
          shared_host_locator: { status: parsed.shared_host_locator?.status } } :
          { event: safeText(parsed.event || 'UNKNOWN'), error: safeText(parsed.error || parsed.reason || '') };
        if (!state.main_reports.some(row => JSON.stringify(row) === JSON.stringify(report))) state.main_reports.push(report);
      } catch { state.malformed_main_report = true; }
    }
  };
  const screenshot = async name => { guard(); await bounded(() => page.screenshot({ path: path.join(scope.run_root, 'screenshots', name + '.png'), fullPage: true })); };
  const route = () => { const value = page.url(); requireThat(value.startsWith('ros-app://desktop/'), 'ACTUAL_REACT_ROUTE_REQUIRED'); state.renderer_routes.push({ at: new Date().toISOString(), url: value }); };
  const observe = async action => {
    guard(); const value = await bounded(action);
    return value;
  };
  try {
    write('launch-input.json', { scope, explicit_environment: env, argv: [path.join(bundle.bundle, 'apps/desktop')], electron_cwd: scope.run_root,
      workspace, invalid_path: invalid, profile: 'INVALID_VALID_PATH_ENTRY_ONLY', task_budget: 0, model_budget: 0, workspace_file_contents_read: false,
      root_job_required_before_invocation: true, no_auth_files_read_or_copied: true });
    // Importing the cached SDK and launching happen ONLY after all Root-reviewed
    // pins and fresh-state checks. There is no install/browser discovery fallback.
    const { _electron } = await import(pathToFileURL(path.join(scope.playwright.root, 'index.mjs')).href);
    guard(); activeRunEvidence.phase = 'ELECTRON_LAUNCH_ATTEMPTED'; state.electron_launch_attempted = true;
    app = await _electron.launch({ executablePath: path.join(bundle.bundle, 'runtime/electron/electron.exe'),
      args: [path.join(bundle.bundle, 'apps/desktop')], cwd: scope.run_root, env, timeout: Math.min(60000, until - Date.now()) });
    app.on('console', message => log('main:' + message.type(), message.text()));
    // On Windows this may be the SDK's cmd wrapper PID, never claim it is Core.
    state.playwright_launcher_pid = app.process()?.pid || null;
    const child = app.process();
    let pending = '';
    child?.stdout?.on('data', chunk => {
      pending += chunk.toString('utf8');
      while (pending.includes('\n')) { const index = pending.indexOf('\n'); log('stdout', pending.slice(0, index).replace(/\r$/, '')); pending = pending.slice(index + 1); }
      if (pending.length > 65536) { log('stdout_fragment', pending); pending = ''; }
    });
    child?.stderr?.on('data', chunk => log('stderr', chunk.toString('utf8')));
    page = await bounded(() => app.firstWindow({ timeout: Math.min(60000, until - Date.now()) }), 60000);
    page.setDefaultTimeout(15000);
    page.on('console', message => { if (['error', 'warning'].includes(message.type())) log('renderer:' + message.type(), message.text()); });
    page.on('pageerror', error => log('pageerror', error.message));
    await bounded(() => page.locator('#root').waitFor({ state: 'visible' }));
    route(); await screenshot('01-project-entry');
    while (!state.main_reports.some(row => row.event === 'ready_to_show' && row.owned_core_identity)) { guard(); await delay(100); }
    const ready = state.main_reports.find(row => row.event === 'ready_to_show' && row.owned_core_identity);
    requireThat(ready.management_state === 'READY' && ready.renderer?.react_root === true && ready.shared_host_locator?.status === 'DISABLED', 'FRESH_OWNED_CORE_NOT_READY');
    const core = ready.owned_core_identity;
    requireThat(core.image_sha256 === scope.bundle.control_sha256 && Number.isSafeInteger(core.pid) && core.pid > 0 &&
      /^[0-9]+$/.test(core.created_ns || '') && /^host-[a-f0-9]{12}$/.test(core.host_id || ''), 'ACTUAL_CORE_IDENTITY_MISMATCH');
    const pickerUntil = Math.min(until - scope.deadlines.close_ms - 5000, Date.now() + scope.deadlines.picker_ms);
    requireThat(pickerUntil > Date.now() + 10000, 'PICKER_TIME_REMAINING_REQUIRED');
    write('owned-core.json', { scope_nonce: scope.scope_nonce, identity_source: 'ROS_DESKTOP_REPORT.ready_to_show',
      action_deadline_utc: new Date(pickerUntil).toISOString(), owned_core_identity: core });
    const nameOptions = page.locator('details.project-name-option');
    requireThat(await nameOptions.count() === 1, 'EXACT_UI8_PROJECT_NAME_DETAILS_REQUIRED');
    const nameSummary = nameOptions.locator('summary');
    requireThat((await nameSummary.textContent()).trim() === '自定义项目名称', 'UI8_PROJECT_NAME_SUMMARY_CHANGED');
    await bounded(() => nameSummary.click());
    await bounded(() => page.getByLabel('显示名称', { exact: true }).fill(scope.project_display_name));
    guard(); await bounded(() => page.getByRole('button', { name: '选择目录', exact: true }).click());
    activeRunEvidence.phase = 'NATIVE_HELPER_RUNNING_AUTHORIZATION_UNKNOWN';
    state.native_workspace_authorization = 'UNKNOWN_WHILE_NATIVE_HELPER_PENDING';
    const helperHistoryPath = path.join(receipts, 'native-helper-history.ndjson');
    fs.writeFileSync(helperHistoryPath, '', {flag: 'wx'});
    const helperStdoutPath = path.join(receipts, 'native-helper-stdout-prefix.bin');
    const stdoutFD = fs.openSync(helperStdoutPath, 'wx');
    const helperOutcome = new Promise(resolve => {
      const osEnv = Object.fromEntries(Object.entries(env).filter(([name]) => !name.startsWith('RESEARCHOS_')));
      helper = spawn(scope.windows.powershell, ['-NoLogo', '-NoProfile', '-NonInteractive', '-File', path.join(HERE, 'choose-owned-folder.ps1'),
        '-ScopePath', scopeFile, '-ScopeSHA256', expectedScopeSHA, '-ScopeNonce', scope.scope_nonce,
        '-CoreIdentityPath', path.join(receipts, 'owned-core.json'), '-HistoryPath', helperHistoryPath], { env: osEnv, cwd: scope.run_root, detached: false, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
      const chunks = []; const stdoutHash = crypto.createHash('sha256'); let stdoutBytes = 0, storedBytes = 0, stderr = '';
      let stdoutClosed = false;
      const closeRaw = () => { if (!stdoutClosed) { stdoutClosed = true; try { fs.closeSync(stdoutFD); } catch(error) { state.helper_stdout_io_error = safeText(error.message); } } };
      helper.stdout.on('data', chunk => {
        stdoutBytes += chunk.length; stdoutHash.update(chunk);
        const prefix = chunk.subarray(0, Math.max(0, 65536 - storedBytes));
        if (prefix.length && !state.helper_stdout_io_error) { try { fs.writeSync(stdoutFD, prefix); storedBytes += prefix.length; } catch(error) { state.helper_stdout_io_error = safeText(error.message); } }
        state.helper_stdout_progress = {received_bytes: stdoutBytes, retained_prefix_bytes: storedBytes, retained_prefix: helperStdoutPath, history_journal: helperHistoryPath};
        if (stdoutBytes <= 65536) chunks.push(Buffer.from(chunk));
      });
      helper.stderr.on('data', chunk => { if (stderr.length < 16384) stderr += chunk.toString('utf8'); });
      helper.on('error', error => { closeRaw(); resolve({ exit: null, error: safeText(error.message) }); });
      helper.on('close', exit => {
        closeRaw(); state.helper_stdout_progress = {...state.helper_stdout_progress, final_sha256: stdoutHash.digest('hex'), received_bytes: stdoutBytes};
        if (state.helper_stdout_io_error) return resolve({ exit, stdout: null, stdout_bytes: stdoutBytes, error: 'HELPER_STDOUT_RECEIPT_WRITE_FAILED', stderr: safeText(stderr) });
        if (stdoutBytes > 65536) return resolve({ exit, stdout: null, stdout_bytes: stdoutBytes, error: 'DIAGNOSTIC_STDOUT_LIMIT', stderr: safeText(stderr) });
        try {
          const stdout = new TextDecoder('utf-8', { fatal: true }).decode(Buffer.concat(chunks));
          resolve({ exit, stdout, stdout_bytes: stdoutBytes, stderr: safeText(stderr) });
        } catch { resolve({ exit, stdout: null, error: 'DIAGNOSTIC_STDOUT_UTF8', stderr: safeText(stderr) }); }
      });
    });
    const helperWaitMs = pickerUntil + scope.deadlines.close_ms + 3000 - Date.now();
    const chosen = await bounded(() => helperOutcome, helperWaitMs);
    // Preserve raw failure history before interpreting success. No truncation of
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

  } catch (error) {
    state.status = 'BLOCKED_OR_FAILED'; state.error = { code: safeText(error.code || error.message), message: safeText(error.message) };
    if (page && !page.isClosed()) { try { await page.screenshot({ path: path.join(scope.run_root, 'screenshots/blocked.png'), timeout: 3000 }); } catch {} }
  } finally {
    closing = true;
    state.helper_pending = !!helper && helper.exitCode === null;
    if (app) {
      state.close.attempted = true;
      let closeTimer;
      try {
        // app.close -> SDK app.quit -> Main window close -> owned shutdown.
        // No app.exit, process.kill, taskkill or arbitrary Core termination here.
        await Promise.race([app.close(), new Promise((_, reject) => { closeTimer = setTimeout(() => reject(new Error('APP_CLOSE_UNCONFIRMED_ROOT_JOB_MUST_CONTAIN')), scope.deadlines.close_ms); })]);
        state.close.app_close_resolved = true;
      } catch (error) { state.close.reason = safeText(error.message); }
      finally { clearTimeout(closeTimer); }
    }
    state.elapsed_ms = Date.now() - started;
    state.close.owned_core_exit = 'REQUIRES_ROOT_EXACT_PROCESS_IDENTITY_AND_JOB_ACCOUNTING';
    state.transport_routes = { observation: 'NO_TASK_ENDPOINTS_NO_HTTP_INTERCEPTION_TYPED_MAIN_READS_ONLY', expected: [] };
    state.outbox_ref_basis = 'NOT_READ_ZERO_BUDGET';
    write('result.json', state);
    console.log(JSON.stringify({ status: state.status, result: path.join(receipts, 'result.json'),
      model_outcome: state.model_outcome, formal_increment: 0, product_increment: 0,
      exact_owned_core_exit_confirmation_required_from_root: true }));
  }
  return state;
}

export async function run(scopeFile, expectedScopeSHA) {
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
