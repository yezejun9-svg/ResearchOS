#!/usr/bin/env node
// Launch only a sealed, repo-shaped development tree with an explicit fresh
// state root. This is not an installer or a service launcher.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

export const MANIFEST_SCHEMA = 'researchos.desktop-development-tree/1';
const REQUIRED = [
  'apps/desktop/main/main.js', 'apps/desktop/preload/preload.js',
  'apps/desktop/resources/client-wire/descriptor.json',
  'apps/desktop/resources/client-wire/researchos-client-wire-validator.exe',
  'apps/desktop/resources/control/researchos-control.exe',
  'apps/desktop/resources/control/runtime-verifier.exe',
  'apps/desktop/resources/control/runtime-verifier-installation.json',
  'apps/desktop/resources/control/runtime/mu-worker.mjs',
  'apps/desktop/resources/control/runtime/mu-worker.mjs.build.json',
  'apps/desktop/resources/control/runtime/node.exe',
  'apps/web/dist/index.html', 'runtime/electron/electron.exe',
  'spec/v2.0/contracts/domain.schema.json', 'spec/v2.0/contracts/openapi.json',
  'internal/api/contracts/client.protocol.schema.json',
  'internal/api/contracts/domain.schema.json', 'migrations/sqlite/next_v24_sessions.sql',
];
const HASH = /^[a-f0-9]{64}$/;

function refusal(code) { const error = new Error(code); error.code = code; return error; }
function folded(value) { return path.normalize(value).toLocaleLowerCase('en-US'); }
function within(parent, child) {
  const relative = path.relative(parent, child);
  return relative === '' || (!relative.startsWith('..' + path.sep) && relative !== '..' && !path.isAbsolute(relative));
}

// A path may not transit a symlink, junction or other resolved alias. In
// particular, a fresh-looking state name behind a junction is not fresh.
export function checkNativePath(value, missingLeaf = false) {
  if (typeof value !== 'string' || !path.isAbsolute(value)) throw refusal('ABSOLUTE_PATH_REQUIRED');
  const absolute = path.resolve(value);
  const drive = path.parse(absolute).root;
  const segments = absolute.slice(drive.length).split(path.sep).filter(Boolean);
  let current = drive;
  for (let index = 0; index < segments.length; index++) {
    current = path.join(current, segments[index]);
    let info;
    try { info = fs.lstatSync(current); }
    catch (error) {
      if (missingLeaf && index === segments.length - 1 && error.code === 'ENOENT') return absolute;
      throw refusal('PATH_UNAVAILABLE');
    }
    if (info.isSymbolicLink()) throw refusal('PATH_ALIAS_REFUSED');
    let resolved;
    try { resolved = fs.realpathSync.native(current); }
    catch { throw refusal('PATH_UNAVAILABLE'); }
    if (folded(resolved) !== folded(current)) throw refusal('PATH_ALIAS_REFUSED');
    if (index < segments.length - 1 && !info.isDirectory()) throw refusal('PATH_NOT_DIRECTORY');
  }
  return absolute;
}

function hashFile(file) {
  const h = crypto.createHash('sha256');
  const handle = fs.openSync(file, 'r');
  const buffer = Buffer.allocUnsafe(1024 * 1024);
  try {
    for (;;) {
      const count = fs.readSync(handle, buffer, 0, buffer.length, null);
      if (!count) break;
      h.update(buffer.subarray(0, count));
    }
  } finally { fs.closeSync(handle); }
  return h.digest('hex');
}

function relativeFile(value) {
  return typeof value === 'string' && value && !value.includes('\\') &&
    !value.includes(':') && !value.includes('\0') &&
    value.split('/').every(part => part && part !== '.' && part !== '..') &&
    path.posix.normalize(value) === value;
}

export function validateBundle(bundlePath) {
  const bundle = checkNativePath(bundlePath);
  if (!fs.statSync(bundle).isDirectory()) throw refusal('BUNDLE_NOT_DIRECTORY');
  const manifestPath = path.join(bundle, 'development-manifest.json');
  checkNativePath(manifestPath);
  let manifest;
  try { manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8')); }
  catch { throw refusal('BUNDLE_MANIFEST_INVALID'); }
  if (manifest.schema !== MANIFEST_SCHEMA || folded(manifest.bundle_root || '') !== folded(bundle) ||
      !Array.isArray(manifest.files) || !manifest.files.length || manifest.mode !== 'DEVELOPMENT_ONLY_BUILT_NOT_NATIVE_TESTED')
    throw refusal('BUNDLE_MANIFEST_INVALID');
  const names = new Set();
  let previous = '';
  for (const item of manifest.files) {
    if (!relativeFile(item.path) || item.path <= previous || !HASH.test(item.sha256) ||
        !Number.isSafeInteger(item.bytes) || item.bytes < 0) throw refusal('BUNDLE_INVENTORY_INVALID');
    previous = item.path;
    const foldedName = item.path.toLocaleLowerCase('en-US');
    if (names.has(foldedName)) throw refusal('BUNDLE_INVENTORY_ALIAS');
    names.add(foldedName);
    const target = path.join(bundle, ...item.path.split('/'));
    checkNativePath(target);
    const info = fs.lstatSync(target);
    if (!info.isFile() || info.size !== item.bytes || hashFile(target) !== item.sha256)
      throw refusal('BUNDLE_FILE_CHANGED');
  }
  for (const required of REQUIRED) if (!names.has(required.toLocaleLowerCase('en-US'))) throw refusal('BUNDLE_RESOURCE_MISSING');
  if (![...names].some(name => name.startsWith('apps/web/dist/assets/') && name.endsWith('.js')) ||
      ![...names].some(name => name.startsWith('apps/web/dist/assets/') && name.endsWith('.css')))
    throw refusal('BUNDLE_REACT_ASSETS_MISSING');
  const migrations = manifest.files.map(item => item.path).filter(name => /^migrations\/sqlite\/\d{4}_[^/]+\.sql$/.test(name));
  const numbers = migrations.map(name => Number(name.slice('migrations/sqlite/'.length, 'migrations/sqlite/'.length + 4))).sort((a, b) => a - b);
  if (!numbers.length || numbers.some((number, index) => number !== index + 1)) throw refusal('BUNDLE_MIGRATIONS_INCOMPLETE');
  const actual = [];
  function walk(directory) {
    for (const item of fs.readdirSync(directory, { withFileTypes: true })) {
      const target = path.join(directory, item.name);
      checkNativePath(target);
      if (item.isDirectory()) walk(target);
      else if (item.isFile()) actual.push(path.relative(bundle, target).split(path.sep).join('/').toLocaleLowerCase('en-US'));
      else throw refusal('BUNDLE_PATH_TYPE');
    }
  }
  walk(bundle);
  const expected = new Set([...names, 'development-manifest.json']);
  if (actual.length !== expected.size || actual.some(name => !expected.has(name))) throw refusal('BUNDLE_UNLISTED_PATH');
  const control = path.join(bundle, 'apps/desktop/resources/control');
  const install = JSON.parse(fs.readFileSync(path.join(control, 'runtime-verifier-installation.json'), 'utf8'));
  const verifier = path.join(control, 'runtime-verifier.exe');
  if (install.executable !== verifier || install.executable_hash !== 'sha256:' + hashFile(verifier) ||
      install.schema !== 'researchos.runtime-verifier-installation.v1' ||
      install.service_id !== 'researchos.runtime-qualification-verifier.v1' ||
      install.protocol !== 'researchos.runtime-verifier/1' ||
      !Array.isArray(install.arguments) || install.arguments.length) throw refusal('VERIFIER_BINDING_INVALID');
  const runtime = path.join(control, 'runtime');
  const mu = JSON.parse(fs.readFileSync(path.join(runtime, 'mu-worker.mjs.build.json'), 'utf8'));
  if (mu.mu_commit !== '8dfebe36508ac0c2508735bb866756dab9283e74' ||
      mu.vendored_files_verified !== 5083 || mu.bundle_sha256 !== hashFile(path.join(runtime, 'mu-worker.mjs')) ||
      mu.bundle_bytes !== fs.statSync(path.join(runtime, 'mu-worker.mjs')).size) throw refusal('MU_BINDING_INVALID');
  const client = JSON.parse(fs.readFileSync(path.join(bundle, 'apps/desktop/resources/client-wire/descriptor.json'), 'utf8'));
  if (client.build_input_digest !== manifest.client_wire?.build_input_digest ||
      client.binary_sha256 !== hashFile(path.join(bundle, 'apps/desktop/resources/client-wire/researchos-client-wire-validator.exe')))
    throw refusal('CLIENT_WIRE_BINDING_INVALID');
  return { bundle, manifest, fileCount: manifest.files.length };
}

// Windows environment keys are case-insensitive. Refuse collisions before
// allowing any key through, then construct a fresh environment from a tiny
// OS allowlist and the explicit development paths.
export function buildChildEnv(ambient, bundle, state, smoke = false) {
  const seen = new Map();
  for (const [key, value] of Object.entries(ambient)) {
    const upper = key.toUpperCase();
    if (seen.has(upper)) throw refusal('ENV_CASE_COLLISION');
    seen.set(upper, value);
  }
  const systemRoot = seen.get('SYSTEMROOT') || seen.get('WINDIR');
  if (typeof systemRoot !== 'string' || !path.isAbsolute(systemRoot) ||
      seen.get('WINDIR') && seen.get('SYSTEMROOT') && folded(seen.get('WINDIR')) !== folded(seen.get('SYSTEMROOT')))
    throw refusal('SYSTEMROOT_INVALID');
  const profile = path.join(state, 'profile');
  const root = path.resolve(systemRoot);
  const result = {
    SystemRoot: root, WINDIR: root, OS: 'Windows_NT',
    ComSpec: path.join(root, 'System32', 'cmd.exe'),
    PATH: [path.join(bundle, 'runtime/electron'), path.join(root, 'System32'), root].join(path.delimiter),
    USERPROFILE: profile, HOME: profile,
    APPDATA: path.join(profile, 'AppData/Roaming'),
    LOCALAPPDATA: path.join(profile, 'AppData/Local'),
    TEMP: path.join(state, 'tmp'), TMP: path.join(state, 'tmp'),
    RESEARCHOS_DATA_DIR: path.join(state, 'data'),
    RESEARCHOS_CLI_DISCOVERY: path.join(state, 'discovery.json'),
    RESEARCHOS_DESKTOP_USER_DATA: path.join(state, 'electron-user-data'),
    RESEARCHOS_CONTROL_EXE: path.join(bundle, 'apps/desktop/resources/control/researchos-control.exe'),
    RESEARCHOS_DESKTOP_VERIFIER_MANIFEST: path.join(bundle, 'apps/desktop/resources/control/runtime-verifier-installation.json'),
    RESEARCHOS_DESKTOP_RUNTIME_ASSETS_DIR: path.join(bundle, 'apps/desktop/resources/control/runtime'),
    RESEARCHOS_WEB_DIR: path.join(bundle, 'apps/web/dist'),
  };
  if (smoke) { result.ROS_DESKTOP_SMOKE = '1'; result.ROS_DESKTOP_NATIVE_SMOKE = '1'; }
  return result;
}

export function validateStatePath(statePath, bundle) {
  const state = checkNativePath(statePath, true);
  if (fs.existsSync(state)) throw refusal('STATE_NOT_FRESH');
  if (within(bundle, state) || within(state, bundle)) throw refusal('STATE_BUNDLE_OVERLAP');
  return state;
}

function validIdentity(value) {
  return value && Number.isSafeInteger(value.pid) && value.pid > 0 &&
    typeof value.created_ns === 'string' && /^[0-9]+$/.test(value.created_ns) &&
    typeof value.image_sha256 === 'string' && HASH.test(value.image_sha256) &&
    typeof value.host_id === 'string' && /^host-[a-f0-9]{12}$/.test(value.host_id);
}

export function validateSmokeReports(reports, exitCode) {
  const ready = reports.filter(row => row?.event === 'ready_to_show');
  const shutdown = reports.filter(row => row?.event === 'shutdown_confirmed');
  if (exitCode !== 0 || ready.length !== 1 || shutdown.length !== 1 ||
      reports.some(row => ['boot_failed', 'shutdown_unconfirmed'].includes(row?.event)))
    throw refusal('SMOKE_OUTCOME_UNCONFIRMED');
  const a = ready[0], b = shutdown[0];
  if (reports.indexOf(b) <= reports.indexOf(a) || a.management_state !== 'READY' ||
      a.host_health !== 'UP' || a.native_probe?.ok !== true ||
      a.renderer?.bridge !== true || a.renderer.react_root !== true ||
      !a.renderer.mounted_title || !(a.renderer.navigation > 0) ||
      !validIdentity(a.owned_core_identity) || b.process_exit_confirmed !== true ||
      JSON.stringify(b.owned_core_identity) !== JSON.stringify(a.owned_core_identity))
    throw refusal('SMOKE_OUTCOME_UNCONFIRMED');
  return { status: 'NATIVE_SMOKE_CONFIRMED', owned_core_identity: a.owned_core_identity };
}

export function prepareDevelopmentLaunch({ bundle, state, smoke = false, ambient = process.env }) {
  const inspected = validateBundle(bundle);
  const fresh = validateStatePath(state, inspected.bundle);
  const env = buildChildEnv(ambient, inspected.bundle, fresh, smoke);
  return { bundle: inspected.bundle, state: fresh,
    executable: path.join(inspected.bundle, 'runtime/electron/electron.exe'),
    argv: [path.join(inspected.bundle, 'apps/desktop')], cwd: inspected.bundle,
    env, manifest_sha256: hashFile(path.join(inspected.bundle, 'development-manifest.json')),
    inventory_count: inspected.fileCount, smoke };
}

export async function executeDevelopmentLaunch(options, spawnImpl = spawn) {
  const prepared = prepareDevelopmentLaunch(options);
  if (options.dryRun) return { mode: 'DRY_RUN_NO_STATE_NO_SPAWN', executable: prepared.executable,
    argv: prepared.argv, cwd: prepared.cwd, state: prepared.state,
    env_keys: Object.keys(prepared.env).sort(), manifest_sha256: prepared.manifest_sha256,
    inventory_count: prepared.inventory_count };
  fs.mkdirSync(prepared.state, { recursive: false });
  for (const relative of ['data', 'electron-user-data', 'profile/AppData/Roaming', 'profile/AppData/Local', 'tmp'])
    fs.mkdirSync(path.join(prepared.state, relative), { recursive: true });
  const child = spawnImpl(prepared.executable, prepared.argv, { cwd: prepared.cwd, env: prepared.env,
    windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
  const reports = [];
  let pending = '', bytes = 0;
  child.stdout.on('data', part => {
    process.stdout.write(part);
    bytes += part.length;
    if (bytes > 1 << 20) return;
    pending += part.toString('utf8');
    for (;;) {
      const end = pending.indexOf('\n');
      if (end < 0) break;
      const line = pending.slice(0, end).trim(); pending = pending.slice(end + 1);
      if (line.startsWith('ROS_DESKTOP_REPORT ')) {
        try { reports.push(JSON.parse(line.slice('ROS_DESKTOP_REPORT '.length))); }
        catch { reports.push({ event: 'malformed_report' }); }
      }
    }
  });
  child.stderr.on('data', part => process.stderr.write(part));
  const code = await new Promise((resolve, reject) => {
    child.once('error', reject);
    child.once('close', (exit, signal) => signal ? reject(refusal('DESKTOP_SIGNALLED')) : resolve(exit));
  });
  if (bytes > 1 << 20) throw refusal('SMOKE_REPORT_TOO_LARGE');
  if (prepared.smoke) return validateSmokeReports(reports, code);
  return { status: code === 0 ? 'DEVELOPMENT_EXITED' : 'DEVELOPMENT_FAILED', exit_code: code };
}

function cli(argv) {
  const options = {};
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--bundle' || arg === '--state') {
      if (options[arg.slice(2)] || !argv[i + 1]) throw refusal('CLI_ARGUMENTS');
      options[arg.slice(2)] = argv[++i];
    } else if (arg === '--dry-run' || arg === '--launch' || arg === '--smoke') {
      if (options[arg.slice(2)]) throw refusal('CLI_ARGUMENTS');
      options[arg.slice(2)] = true;
    } else throw refusal('CLI_ARGUMENTS');
  }
  if (!options.bundle || !options.state || options['dry-run'] === options.launch ||
      options.smoke && !options.launch) throw refusal('CLI_ARGUMENTS');
  return { bundle: options.bundle, state: options.state, dryRun: !!options['dry-run'], smoke: !!options.smoke };
}

if (process.argv[1] && folded(fileURLToPath(import.meta.url)) === folded(path.resolve(process.argv[1]))) {
  try {
    const result = await executeDevelopmentLaunch(cli(process.argv.slice(2)));
    process.stdout.write(JSON.stringify(result) + '\n');
    if (result.status === 'DEVELOPMENT_FAILED') process.exitCode = result.exit_code || 2;
  } catch (error) {
    process.stderr.write(`development launcher refused: ${error.code || error.message}\n`);
    process.exitCode = 2;
  }
}
