// Preparation only until a separately sealed Root scope authorizes execution.
// Exercises real product APIs on a fresh owned data directory; no provider call.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import net from 'node:net';
import assert from 'node:assert/strict';
import {spawn, execFileSync} from 'node:child_process';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const sha = value => crypto.createHash('sha256').update(value).digest('hex');
const read = name => JSON.parse(fs.readFileSync(name, 'utf8').replace(/^\uFEFF/, ''));
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const scopePath = path.resolve(process.argv[2] || 'MISSING_SCOPE.json');
const scope = read(scopePath);
assert.equal(scope.native_launch_authorized, true);
assert.equal(scope.mode, 'OWNED_PRODUCT_HOST_LIFECYCLE_NO_PROVIDER');
assert.equal(scope.formal_increment, 0);
assert.equal(scope.independent_source_build_accepted, true);
const bundle = path.resolve(scope.bundle_root);
const worktree = path.resolve(scope.worktree);
const state = path.resolve(scope.state_root);
const out = path.resolve(scope.receipts_root);
function beneath(parent, child) {
  const relative = path.relative(parent, child);
  return relative !== '' && !relative.startsWith('..' + path.sep) && relative !== '..' && !path.isAbsolute(relative);
}
assert(beneath(path.join(worktree, '.local'), bundle));
assert(beneath(path.join(worktree, '.local'), state));
assert(!beneath(bundle, state) && !beneath(state, bundle));
assert(!fs.existsSync(state) && !fs.existsSync(out));
const git = (...args) => execFileSync('git', args, {cwd: worktree, encoding: 'utf8', windowsHide: true}).trim();
assert.equal(git('rev-parse', 'HEAD'), scope.candidate_commit);
assert.equal(git('rev-parse', 'HEAD^{tree}'), scope.candidate_tree);
assert.equal(git('status', '--porcelain=v1', '--untracked-files=all'), '');
for (const ref of scope.bound_files) {
  const bytes = fs.readFileSync(ref.path);
  assert.equal(bytes.length, ref.bytes, ref.path);
  assert.equal(sha(bytes), ref.sha256, ref.path);
}
const marker = read(path.join(bundle, 'installed-product.json'));
assert.equal(marker.installation_id, scope.installation_id);
assert.equal(path.resolve(marker.install_root), bundle);
for (const row of marker.files) {
  const file = path.resolve(bundle, row.path);
  assert(beneath(bundle, file));
  const bytes = fs.readFileSync(file);
  assert.equal(sha(bytes), row.sha256, row.path);
  assert.equal(bytes.length, row.bytes, row.path);
}
fs.mkdirSync(out);
fs.mkdirSync(state);
const local = path.join(state, 'LocalAppData');
const profile = path.join(state, 'User');
const roaming = path.join(state, 'Roaming');
const temporary = path.join(state, 'Temp');
const workspace = path.join(state, '项目 空间');
for (const dir of [local, profile, roaming, temporary, workspace]) fs.mkdirSync(dir);
const seed = Buffer.from('ResearchOS owned lifecycle workspace\r\n', 'utf8');
fs.writeFileSync(path.join(workspace, 'README.md'), seed, {flag: 'wx'});
const dataRoot = path.join(local, 'ResearchOS', 'data');
const witnessPath = path.join(dataRoot, 'product-supervisor.json');
const env = Object.fromEntries(Object.entries(process.env).filter(([key]) =>
  ['SYSTEMROOT', 'WINDIR', 'COMSPEC', 'OS', 'PATHEXT', 'PATH'].includes(key.toUpperCase())));
Object.assign(env, {LOCALAPPDATA: local, APPDATA: roaming, USERPROFILE: profile, TEMP: temporary, TMP: temporary});
const require = createRequire(import.meta.url);
const {_electron} = require(scope.playwright_path);
const cli = path.join(bundle, marker.binaries.cli.path);
const electron = path.join(bundle, marker.binaries.electron.path);
const control = path.join(bundle, marker.binaries.control.path);
const appRoot = path.join(bundle, 'apps', 'desktop');
const assertions = [];
const children = [];
let application = null;
let providerConnections = 0;
let sequence = 0;
let firstWitness = null;
let secondWitness = null;
let thirdWitness = null;

function save(name, value) {
  fs.writeFileSync(path.join(out, name), JSON.stringify(value, null, 2) + '\n', {flag: 'wx'});
}
function check(id, condition, details = null) {
  assert(condition, id);
  assertions.push({id, passed: true, details});
  fs.appendFileSync(path.join(out, 'assertions.jsonl'), JSON.stringify(assertions.at(-1)) + '\n');
}
function run(label, exe, args) {
  const prefix = String(++sequence).padStart(2, '0') + '-' + label;
  const stdout = fs.openSync(path.join(out, prefix + '.stdout.raw'), 'wx');
  const stderr = fs.openSync(path.join(out, prefix + '.stderr.raw'), 'wx');
  const child = spawn(exe, args, {cwd: bundle, env, windowsHide: true, stdio: ['ignore', stdout, stderr]});
  fs.closeSync(stdout); fs.closeSync(stderr);
  const entry = {label, prefix, pid: child.pid, executable: exe, args, exit: null, terminal: false};
  children.push(entry);
  save(prefix + '.spawn.json', entry);
  const terminal = new Promise(resolve => {
    child.once('error', error => { entry.terminal = true; entry.error = error.message; resolve(entry); });
    child.once('exit', (code, signal) => { entry.terminal = true; entry.exit = code; entry.signal = signal; resolve(entry); });
  });
  return {child, entry, async wait(timeout = 60000) {
    let timer;
    const result = await Promise.race([terminal, new Promise(resolve => { timer = setTimeout(() => resolve(null), timeout); })]);
    clearTimeout(timer);
    if (!result) {
      save(prefix + '.unresolved.json', {...entry, observation_timeout_ms: timeout, restart_authorized: false});
      throw Error('OWNED_COMMAND_OBSERVATION_TIMEOUT:' + label);
    }
    save(prefix + '.exit.json', entry);
    return {...entry, stdout: fs.readFileSync(path.join(out, prefix + '.stdout.raw'), 'utf8'),
      stderr: fs.readFileSync(path.join(out, prefix + '.stderr.raw'), 'utf8')};
  }};
}
function jsonRows(text) { return text.split(/\r?\n/).filter(Boolean).map(line => JSON.parse(line)); }
function verifyCLISession(id, command, expected) {
  check(id + '-exit0', command.exit === 0);
  const operations = jsonRows(command.stdout).flatMap(row => Array.isArray(row.operations) ? row.operations : []);
  const reads = operations.filter(row => row.method === 'session.get' && row.status === 'COMPLETED' && row.exit_code === 0);
  check(id + '-one-completed-session-read', reads.length === 1);
  for (const [key, value] of Object.entries(expected)) {
    check(id + '-' + key, typeof value === 'string' && value.length > 0 && reads[0].result?.[key] === value);
  }
}
function pidsAbsentScript(ids) {
  assert(ids.length === 2 && ids.every(pid => Number.isSafeInteger(pid) && pid > 0));
  return '$limit=[DateTime]::UtcNow.AddSeconds(35); do { $rows=@(); foreach($ownedId in @(' + ids.join(',') + ')) { ' +
    '$p=Get-CimInstance Win32_Process -Filter ("ProcessId="+$ownedId); $rows+=@{pid=$ownedId;present=($null -ne $p);image=if($p){$p.ExecutablePath}else{$null};creation=if($p){[string]$p.CreationDate}else{$null}} }; ' +
    'if(-not($rows | Where-Object present)) { break }; Start-Sleep -Milliseconds 200 } while([DateTime]::UtcNow -lt $limit); ' +
    'ConvertTo-Json -InputObject @($rows) -Depth 4 -Compress';
}
async function waitFor(predicate, label, timeout = 45000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) { if (await predicate()) return; await delay(100); }
  throw Error('OBSERVATION_TIMEOUT:' + label);
}
function witness() { return read(witnessPath); }
async function launch(label) {
  application = await _electron.launch({executablePath: electron, args: [appRoot], cwd: bundle, env, timeout: 45000});
  const child = application.process();
  const entry = {label, pid: child.pid, executable: electron, terminal: child.exitCode !== null, exit: child.exitCode};
  children.push(entry);
  child.on('exit', (code, signal) => { entry.terminal = true; entry.exit = code; entry.signal = signal; });
  save(label + '.spawn.json', entry);
  // Preserve the actual native application's reports, without altering it.
  child.stdout?.on('data', bytes => fs.appendFileSync(path.join(out, label + '.stdout.raw'), bytes));
  child.stderr?.on('data', bytes => fs.appendFileSync(path.join(out, label + '.stderr.raw'), bytes));
  const window = await application.firstWindow({timeout: 45000});
  await window.waitForFunction(() => !!document.querySelector('#root h1') && !!window.researchos?.v2, null, {timeout: 20000});
  await waitFor(() => fs.existsSync(witnessPath) && witness().state === 'READY', label + '-READY');
  const record = witness();
  check(label + '-parent-pid-matches', record.parent_process.PID === child.pid);
  check(label + '-bound-install-data', record.installation_id === marker.installation_id && path.resolve(record.data_root) === dataRoot);
  const status = await window.evaluate(() => window.researchos.v2['host.status']({}));
  save(label + '.status.json', status);
  check(label + '-real-native-host-status', status.ok && status.completed && status.result?.host_instance_id === record.host_id);
  await window.screenshot({path: path.join(out, label + '.png')});
  save(label + '.witness.json', record);
  return {window, record, entry};
}
async function safeClose(label, instance) {
  // Invoke the existing window-close event; never terminate or bypass shutdown.
  await application.evaluate(({BrowserWindow}) => {
    const windows = BrowserWindow.getAllWindows();
    if (windows.length !== 1) throw Error('EXPECTED_ONE_PRODUCT_WINDOW');
    setTimeout(() => windows[0].close(), 20);
    return true;
  });
  await waitFor(() => instance.entry.terminal, label + '-parent-exit', 45000);
  check(label + '-parent-clean-exit', instance.entry.exit === 0, instance.entry);
  check(label + '-witness-retired', !fs.existsSync(witnessPath));
  // Windows process creation time is checked by the product on reconnect. At
  // shutdown, only inspect the exact two PIDs provided by this owned witness.
  const ids = [instance.record.parent_process.PID, instance.record.control_process.PID];
  const proof = await run(label + '-pids', scope.powershell_path, ['-NoProfile', '-NonInteractive', '-Command', pidsAbsentScript(ids)]).wait(45000);
  check(label + '-pid-query-success', proof.exit === 0);
  const rows = JSON.parse(proof.stdout.replace(/^\uFEFF/, ''));
  check(label + '-both-processes-absent', rows.length === 2 && rows.every(row => !row.present), rows);
  application = null;
}
const sentinel = net.createServer(socket => { providerConnections++; socket.destroy(); });
await new Promise(resolve => sentinel.listen(0, '127.0.0.1', resolve));
const modelEndpoint = `https://127.0.0.1:${sentinel.address().port}/v1`;
save('invocation.json', {at: new Date().toISOString(), scope: scopePath, scope_sha256: sha(fs.readFileSync(scopePath)),
  bundle, state, dataRoot, workspace, marker_id: marker.installation_id,
  provider_endpoint: modelEndpoint, environment_keys: Object.keys(env).sort(),
  evidence_mode: 'OWNED_NATIVE_LIFECYCLE_NO_PROVIDER_NO_INSTALLER', formal_increment: 0});

try {
  for (const verb of ['version', 'help', 'doctor']) {
    const result = await run('nonstarting-' + verb, cli, [verb]).wait(20000);
    if (verb !== 'doctor') check(verb + '-exit0', result.exit === 0);
    check(verb + '-jsonl', jsonRows(result.stdout).length > 0);
    check(verb + '-does-not-create-host-data', !fs.existsSync(dataRoot));
  }
  const first = await launch('first');
  firstWitness = first.record;
  const duplicate = run('duplicate-electron', electron, [appRoot]);
  const statuses = [run('cli-status-a', cli, ['status']), run('cli-status-b', cli, ['status'])];
  const duplicateResult = await duplicate.wait(30000);
  check('duplicate-electron-exit0', duplicateResult.exit === 0);
  for (const request of statuses) {
    const result = await request.wait(30000);
    check(request.entry.label + '-completed', result.exit === 0 && jsonRows(result.stdout).some(row => row.status === 'COMPLETED'));
  }
  check('duplicate-keeps-same-host', JSON.stringify(witness()) === JSON.stringify(firstWitness));
  const init = run('cli-init', cli, ['init', workspace]);
  const choose = await run('owned-folder-confirm', scope.powershell_path, ['-NoProfile', '-NonInteractive', '-File',
    path.join(here, 'choose-owned-folder.ps1'), '-OwnedCorePid', String(firstWitness.control_process.PID),
    '-OwnedCoreImage', control, '-OwnedCoreCreatedNS', firstWitness.control_process.CreatedNS,
    '-OwnedCoreSHA256', firstWitness.control_process.ImageSHA256, '-OwnedWorkspace', workspace]).wait(35000);
  check('owned-folder-native-confirm', choose.exit === 0);
  const initialized = await init.wait(45000);
  check('cli-init-exit0', initialized.exit === 0);
  const created = jsonRows(initialized.stdout).find(row => row.status === 'COMPLETED' && row.project_id);
  check('cli-project-created', !!created?.project_id && !!created.workspace_ref);
  check('cli-native-selected-exact-owned-folder', typeof created.result?.workspace?.display_path === 'string' &&
    path.resolve(created.result.workspace.display_path).toLowerCase() === workspace.toLowerCase());
  check('workspace-seed-unchanged', fs.readFileSync(path.join(workspace, 'README.md')).equals(seed));
  const configured = await run('cli-model-config-only', cli, ['config', 'set-model', '--model', 'openai/lifecycle-no-call',
    '--base-url', modelEndpoint, '--config-revision', '0', '--default']).wait(30000);
  check('cli-model-config-saved', configured.exit === 0);
  const config = read(path.join(local, 'ResearchOS', 'cli-config.json'));
  check('cli-config-project-retained', config.project_id === created.project_id);
  const selected = await first.window.evaluate(id => window.researchos.desktop.selectProject(id), created.project_id);
  save('desktop-project-selection.json', selected);
  check('desktop-selected-cli-project', selected.ok === true);
  const status = await first.window.evaluate(() => window.researchos.v2['host.status']({}));
  const models = status.result?.model_configurations || [];
  const model = models.find(row => row.model_id === 'lifecycle-no-call');
  check('desktop-sees-cli-model', !!model?.model_config_ref);
  const session = await first.window.evaluate(payload => window.researchos.v2['session.create'](payload), {
    workspace_ref: created.workspace_ref, model_config_ref: model.model_config_ref, title: 'Owned lifecycle retained session'});
  save('desktop-created-session.json', session);
  check('desktop-created-real-session', session.ok && session.completed && !!session.result?.session_id);
  const sid = session.result.session_id;
  const expectedSession = {session_id: sid, project_id: created.project_id,
    workspace_ref: created.workspace_ref, model_config_ref: model.model_config_ref};
  for (const [key, value] of Object.entries(expectedSession)) check('desktop-created-' + key, session.result[key] === value);
  const opened = await first.window.evaluate(id => window.researchos.desktop.openSession(id), sid);
  save('desktop-opened-session.json', opened);
  check('desktop-persisted-selected-session', opened.ok && opened.completed && opened.result?.session_id === sid);
  const before = await first.window.evaluate(() => window.researchos.desktop.context());
  save('desktop-context-before.json', before);
  const cliStatus = await run('cli-reads-desktop-session', cli, ['status', '--project', created.project_id, '--session', sid]).wait(30000);
  verifyCLISession('cli-reads-desktop-session', cliStatus, expectedSession);
  check('no-model-connection-before-close', providerConnections === 0);
  await first.window.screenshot({path: path.join(out, 'nonempty-before-close.png')});
  await safeClose('first-close', first);
  check('nonempty-state-retained', fs.existsSync(path.join(local, 'ResearchOS', 'cli-config.json')) && fs.existsSync(dataRoot));
  const second = await launch('reopen');
  secondWitness = second.record;
  check('reopen-new-host-identity', firstWitness.host_id !== secondWitness.host_id &&
    firstWitness.control_process.CreatedNS !== secondWitness.control_process.CreatedNS);
  check('reopen-same-install-data', firstWitness.installation_id === secondWitness.installation_id && firstWitness.data_root === secondWitness.data_root);
  const after = await second.window.evaluate(() => window.researchos.desktop.context());
  save('desktop-context-after.json', after);
  const savedSession = await second.window.evaluate(() => window.researchos.v2['session.get']({}));
  save('reopened-session.json', savedSession);
  check('reopened-real-same-session', savedSession.ok && savedSession.completed && savedSession.result?.session_id === sid);
  for (const [key, value] of Object.entries(expectedSession)) check('desktop-reopened-' + key, savedSession.result[key] === value);
  const cliAfter = await run('cli-after-reopen', cli, ['status', '--project', created.project_id, '--session', sid]).wait(30000);
  verifyCLISession('cli-after-reopen-same-session', cliAfter, expectedSession);
  check('reopen-workspace-seed-unchanged', fs.readFileSync(path.join(workspace, 'README.md')).equals(seed));
  check('no-provider-connections', providerConnections === 0);
  await second.window.screenshot({path: path.join(out, 'nonempty-after-reopen.png')});
  await safeClose('second-close', second);
  // The CLI must also start the shared host after a controlled exit, using the
  // retained discovery/data rather than relying on a GUI-first boot.
  const cliCold = await run('cli-cold-reopen', cli, ['status', '--project', created.project_id, '--session', sid]).wait(45000);
  verifyCLISession('cli-cold-reopen-same-session', cliCold, expectedSession);
  thirdWitness = witness();
  save('cli-cold-reopen.witness.json', thirdWitness);
  check('cli-cold-reopen-new-host', thirdWitness.state === 'READY' && thirdWitness.host_id !== secondWitness.host_id &&
    thirdWitness.installation_id === secondWitness.installation_id && thirdWitness.data_root === secondWitness.data_root);
  const show = await run('cli-host-show-ui', electron, [appRoot]).wait(30000);
  check('cli-host-show-ui-secondary-exits', show.exit === 0 && JSON.stringify(witness()) === JSON.stringify(thirdWitness));
  const closeResult = await run('cli-host-window-close', scope.powershell_path, ['-NoProfile', '-NonInteractive', '-File',
    path.join(here, 'close-owned-window.ps1'), '-OwnedDesktopPid', String(thirdWitness.parent_process.PID),
    '-OwnedDesktopImage', electron, '-OwnedDesktopCreatedNS', thirdWitness.parent_process.CreatedNS,
    '-OwnedDesktopSHA256', thirdWitness.parent_process.ImageSHA256]).wait(35000);
  check('cli-host-owned-window-close-sent', closeResult.exit === 0);
  await waitFor(() => !fs.existsSync(witnessPath), 'cli-host-witness-retired', 45000);
  const ids = [thirdWitness.parent_process.PID, thirdWitness.control_process.PID];
  const closed = await run('cli-host-final-pids', scope.powershell_path, ['-NoProfile', '-NonInteractive', '-Command', pidsAbsentScript(ids)]).wait(45000);
  check('cli-host-final-pids-query', closed.exit === 0);
  const closedRows = JSON.parse(closed.stdout.replace(/^\uFEFF/, ''));
  check('cli-host-both-processes-absent', closedRows.length === 2 && closedRows.every(row => !row.present), closedRows);
  check('no-provider-connections-final', providerConnections === 0);
  save('FINAL.json', {status: 'OWNED_NATIVE_LIFECYCLE_EXECUTION_REPORTED', assertions, children,
    project_id: created.project_id, session_id: sid, first_witness: firstWitness, second_witness: secondWitness, third_witness: thirdWitness,
    provider_connections: providerConnections, installer_acceptance: false, busy_native_test: 'NOT_RUN',
    clean_windows_test: 'NOT_RUN', formal_increment: 0, independent_acceptance: false});
  console.log(JSON.stringify({status: 'OWNED_NATIVE_LIFECYCLE_EXECUTION_REPORTED', assertions: assertions.length, receipts: out, formal_increment: 0}));
} catch (error) {
  save('UNRESOLVED.json', {status: 'FAILED_OR_UNRESOLVED_PRESERVE_OWNED_STATE', error: error.message, stack: error.stack,
    assertions, children, first_witness: firstWitness, second_witness: secondWitness, third_witness: thirdWitness,
    provider_connections: providerConnections, restart_authorized: false, forced_termination: false, formal_increment: 0});
  console.error(error.message);
  process.exitCode = 1;
} finally {
  await new Promise(resolve => sentinel.close(resolve));
  // No app.close/kill cleanup: a failed observation leaves its known handle for
  // Root reconciliation. Successful paths close through product window events.
}
