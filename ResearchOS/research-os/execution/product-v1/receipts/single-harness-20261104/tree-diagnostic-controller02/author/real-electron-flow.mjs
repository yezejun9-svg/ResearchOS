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
const requireThat = (test, code) => { if (!test) throw Object.assign(new Error(code), { code }); };
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

function requireChatGPTAuthentication(capabilities) {
  requireThat(capabilities?.authentication?.state === 'LOGGED_IN' &&
    capabilities.authentication.kind === 'chatgpt', 'CHATGPT_LOGIN_REQUIRED_NO_API_PAYMENT_OR_LOGIN_FALLBACK');
}

function requireDiagnosticScope(scope) {
  requireThat(scope?.native_picker?.diagnostic_only === true &&
    scope?.budget?.task_submissions === 0 &&
    scope?.budget?.automatic_retries === 0 &&
    scope?.budget?.harness_id === 'codex', 'DIAGNOSTIC_ONLY_ZERO_SUBMISSION_SCOPE_REQUIRED');
}
function parseDiagnosticReply(chosen, core) {
  requireThat(chosen?.exit === 2 && typeof chosen.stdout === 'string' &&
    Buffer.byteLength(chosen.stdout) <= 65536, 'DIAGNOSTIC_REPLY_BOUNDED_COMPLETE_JSON_REQUIRED');
  const reply = JSON.parse(chosen.stdout);
  const d = reply.diagnostic;
  requireThat(reply.schema === 'researchos.owned-native-folder-diagnostic/1' &&
    reply.clicked_ok === false && reply.ok_attempted === false &&
    reply.reason === 'DIAGNOSTIC_ONLY_TREE_SNAPSHOT_COMPLETE_NO_OK' &&
    reply.cleanup?.status === 'OWNED_IDCANCEL_CLICKED' &&
    reply.authorization_state === 'NO_OK_CLICKED_NO_WORKSPACE_AUTHORIZATION_REQUESTED_BY_RUNNER',
  'DIAGNOSTIC_CANCEL_OR_NO_OK_UNCONFIRMED');
  requireThat(d?.schema === 'researchos.owned-dialog-tree-metadata/1' &&
    d.diagnostic_only === true && d.no_ok === true &&
    d.no_workspace_authorization === true && d.no_treeitem_navigation === true &&
    d.dialog_owner_pid === core.pid && typeof d.dialog_hwnd === 'string' &&
    d.dialog_hwnd === reply.cleanup.hwnd &&
    Number.isSafeInteger(d.tree_count) && d.tree_count >= 0 && d.tree_limit === 16 &&
    Array.isArray(d.trees) && d.captured_count === d.trees.length &&
    d.captured_count === Math.min(d.tree_count, 16) &&
    d.tree_truncated === (d.tree_count > 16), 'DIAGNOSTIC_SCOPE_OR_COUNT_MISMATCH');
  requireThat(d.tree_count !== 0 || d.win32_children_when_zero &&
    d.win32_children_when_zero.limit === 32 &&
    d.win32_children_when_zero.text_or_items_read === false &&
    Array.isArray(d.win32_children_when_zero.controls) &&
    d.win32_children_when_zero.controls.length <= 32, 'ZERO_TREE_WIN32_METADATA_REQUIRED');
  return reply;
}
function sanitizeDiagnosticScalars(value) {
  if (typeof value === 'string') return safeText(value);
  if (Array.isArray(value)) return value.map(sanitizeDiagnosticScalars);
  if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, sanitizeDiagnosticScalars(item)]));
  return value;
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

export async function run(scopeFile, expectedScopeSHA) {
  requireThat(process.platform === 'win32', 'WINDOWS_REQUIRED');
  pin(scopeFile, expectedScopeSHA);
  const scope = JSON.parse(fs.readFileSync(scopeFile, 'utf8'));
  requireThat(scope.schema === 'researchos.real-electron-single-codex-scope/1' && scope.status === 'ROOT_APPROVED_REAL_RUN', 'PREPARATION_ONLY_NOT_RUN');
  requireThat(/^[a-zA-Z0-9._-]{24,128}$/.test(scope.scope_nonce || ''), 'SCOPE_NONCE_REQUIRED');
  requireThat(scope.root_supervision?.required === true && scope.root_supervision?.mechanism === 'ROOT_EXISTING_UNNAMED_JOB', 'ROOT_JOB_REQUIRED');
  requireThat(HASH.test(scope.root_supervision.controller_sha256 || '') && HASH.test(scope.root_supervision.launch_contract_sha256 || ''), 'ROOT_CONTROLLER_PINS_REQUIRED');
  requireThat(scope.root_supervision.outer_deadline_ms > scope.deadlines.flow_ms + scope.deadlines.close_ms + 10000, 'OUTER_DEADLINE_MUST_CONTAIN_FLOW_AND_CLOSE');
  requireThat(scope.deadlines.flow_ms > 0 && scope.deadlines.flow_ms <= 600000 && scope.deadlines.close_ms > 0 && scope.deadlines.close_ms <= 60000, 'DEADLINES_INVALID');
  requireDiagnosticScope(scope);
  requireThat(scope.native_picker.operator_fallback === false, 'AUTOMATION_SCOPE_HAS_NO_OPERATOR_FALLBACK');
  requireThat(scope.contract_sha256 === CONTRACT, 'HARNESS_CONTRACT_PIN_REQUIRED');
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

  fs.mkdirSync(scope.run_root); // no recursive root creation, no overwrite or reuse
  for (const dir of ['workspace', 'receipts', 'screenshots', 'tmp']) fs.mkdirSync(path.join(scope.run_root, dir));
  const receipts = path.join(scope.run_root, 'receipts');
  const write = (name, value) => fs.writeFileSync(path.join(receipts, name), JSON.stringify(value, null, 2) + '\n', { flag: 'wx' });
  const workspace = path.join(scope.run_root, 'workspace');
  // Diagnostic owns an empty fixture directory; no workspace file contents.
  const started = Date.now(), until = started + scope.deadlines.flow_ms;
  let timedOut = false, closing = false, app = null, helper = null, page = null;
  const state = { status: 'RUNNING', formal_increment: 0, product_increment: 0,
    scope_sha256: expectedScopeSHA, scope_nonce: scope.scope_nonce, source_head: scope.source.head,
    bundle_manifest_sha256: scope.bundle.manifest_sha256,
    root_job_proof: 'EXTERNAL_ROOT_CONTROLLER_ONLY_NOT_SELF_VERIFIED',
    allowed_task_submissions: 0, actual_dom_submit_attempts: 0, actual_transport_post_count: 'NOT_INSTRUMENTED',
    renderer_routes: [], event_refs: [], console: [], main_reports: [],
    close: { attempted: false, app_close_resolved: false, owned_core_exit: 'UNVERIFIED' },
    model_outcome: 'NOT_RUN_DIAGNOSTIC_ONLY', windows_enforcement: 'NOT_MEASURED_DIAGNOSTIC_ONLY' };
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
      workspace, diagnostic_only: true, workspace_file_contents_read: false,
      root_job_required_before_invocation: true, no_auth_files_read_or_copied: true });
    // Importing the cached SDK and launching happen ONLY after all Root-reviewed
    // pins and fresh-state checks. There is no install/browser discovery fallback.
    const { _electron } = await import(pathToFileURL(path.join(scope.playwright.root, 'index.mjs')).href);
    guard(); state.electron_launch_attempted = true;
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
    requireThat(core.image_sha256 === scope.bundle.control_sha256, 'ACTUAL_CORE_HASH_MISMATCH');
    write('owned-core.json', { scope_nonce: scope.scope_nonce, identity_source: 'ROS_DESKTOP_REPORT.ready_to_show',
      action_deadline_utc: new Date(until).toISOString(), owned_core_identity: core });
    const nameOptions = page.locator('details.project-name-option');
    requireThat(await nameOptions.count() === 1, 'EXACT_UI8_PROJECT_NAME_DETAILS_REQUIRED');
    const nameSummary = nameOptions.locator('summary');
    requireThat((await nameSummary.textContent()).trim() === '自定义项目名称', 'UI8_PROJECT_NAME_SUMMARY_CHANGED');
    await bounded(() => nameSummary.click());
    await bounded(() => page.getByLabel('显示名称', { exact: true }).fill(scope.project_display_name));
    guard(); await bounded(() => page.getByRole('button', { name: '选择目录', exact: true }).click());
    const helperOutcome = new Promise(resolve => {
      const osEnv = Object.fromEntries(Object.entries(env).filter(([name]) => !name.startsWith('RESEARCHOS_')));
      helper = spawn(scope.windows.powershell, ['-NoLogo', '-NoProfile', '-NonInteractive', '-File', path.join(HERE, 'choose-owned-folder.ps1'),
        '-ScopePath', scopeFile, '-ScopeSHA256', expectedScopeSHA, '-ScopeNonce', scope.scope_nonce,
        '-CoreIdentityPath', path.join(receipts, 'owned-core.json')], { env: osEnv, cwd: scope.run_root, detached: false, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
      const chunks = []; let stdoutBytes = 0, stderr = '';
      helper.stdout.on('data', chunk => {
        stdoutBytes += chunk.length;
        if (stdoutBytes <= 65536) chunks.push(Buffer.from(chunk));
      });
      helper.stderr.on('data', chunk => { if (stderr.length < 16384) stderr += chunk.toString('utf8'); });
      helper.on('error', error => resolve({ exit: null, error: safeText(error.message) }));
      helper.on('close', exit => {
        if (stdoutBytes > 65536) return resolve({ exit, stdout: null, stdout_bytes: stdoutBytes, error: 'DIAGNOSTIC_STDOUT_LIMIT', stderr: safeText(stderr) });
        try {
          const stdout = new TextDecoder('utf-8', { fatal: true }).decode(Buffer.concat(chunks));
          resolve({ exit, stdout, stdout_bytes: stdoutBytes, stderr: safeText(stderr) });
        } catch { resolve({ exit, stdout: null, error: 'DIAGNOSTIC_STDOUT_UTF8', stderr: safeText(stderr) }); }
      });
    });
    const chosen = await bounded(() => helperOutcome, 45000);
    let pickerResult;
    try { pickerResult = parseDiagnosticReply(chosen, core); }
    catch (error) {
      write('native-folder-automation.json', { exit: chosen.exit, error: safeText(error.message),
        stdout_sha256: typeof chosen.stdout === 'string' ? sha(chosen.stdout) : null,
        stdout_bytes: chosen.stdout_bytes, stderr: safeText(chosen.stderr || '') });
      throw error;
    }
    const sanitized = sanitizeDiagnosticScalars(pickerResult);
    write('native-folder-automation.json', { exit: chosen.exit, stdout: JSON.stringify(sanitized),
      stdout_sha256: sha(chosen.stdout), stdout_bytes: chosen.stdout_bytes, stderr: chosen.stderr });
    write('owned-tree-snapshot.json', sanitized.diagnostic);
    state.native_picker_cleanup = sanitized.cleanup;
    state.native_workspace_authorization = sanitized.authorization_state;
    state.native_picker = 'DIAGNOSTIC_OWNED_IDCANCEL_NO_OK';
    state.model_outcome = 'NOT_RUN_DIAGNOSTIC_ONLY';
    state.status = 'OWNED_DIALOG_TREE_DIAGNOSTIC_CAPTURED_NOT_PRODUCT_ACCEPTED';

  } catch (error) {
    state.status = 'BLOCKED_OR_FAILED'; state.error = { code: safeText(error.code || error.message), message: safeText(error.message) };
    if (state.actual_dom_submit_attempts && !state.task?.terminal) state.model_outcome = 'UNKNOWN_NO_AUTOMATIC_RESUBMIT';
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
    state.transport_routes = { observation: 'NO_HARNESS_ROUTES_DIAGNOSTIC_ONLY', expected: [] };
    state.outbox_ref_basis = 'NOT_READ_DIAGNOSTIC_ONLY';
    write('result.json', state);
    console.log(JSON.stringify({ status: state.status, result: path.join(receipts, 'result.json'),
      model_outcome: state.model_outcome, formal_increment: 0, product_increment: 0,
      exact_owned_core_exit_confirmation_required_from_root: true }));
  }
  return state;
}

if (process.argv[1] && folded(process.argv[1]) === folded(fileURLToPath(import.meta.url))) {
  const args = process.argv.slice(2);
  if (args.length !== 5 || args[0] !== '--execute' || args[1] !== '--scope' || args[3] !== '--scope-sha256') {
    console.log(JSON.stringify({ status: 'PREPARATION_ONLY_NOT_RUN', usage: 'Root supervised only: --execute --scope <reviewed absolute file> --scope-sha256 <reviewed hash>' }));
    process.exitCode = 2;
  } else {
    try { const result = await run(path.resolve(args[2]), args[4]); if (result.status !== 'OWNED_DIALOG_TREE_DIAGNOSTIC_CAPTURED_NOT_PRODUCT_ACCEPTED' || !result.close.app_close_resolved) process.exitCode = 2; }
    catch (error) { console.error(safeText(error.code || error.message)); process.exitCode = 2; }
  }
}
