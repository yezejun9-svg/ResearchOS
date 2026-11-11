#!/usr/bin/env node
// Local development commands. This does not register construction acceptance.
import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, statSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const local = path.join(root, '.local', 'dev');
const web = path.join(root, 'apps', 'web');
const desktop = path.join(root, 'apps', 'desktop');
const isWindows = process.platform === 'win32';
const goVersion = readFileSync(path.join(root, 'go.mod'), 'utf8').match(/^go\s+(\S+)$/m)?.[1];
const command = process.argv[2] || 'help';
const extra = process.argv.slice(3);

function environment(overrides = {}, remove = []) {
  const env = { ...process.env };
  const changed = [...Object.keys(overrides), ...remove];
  for (const key of Object.keys(env)) {
    if (changed.some(name => isWindows ? key.toUpperCase() === name.toUpperCase() : key === name)) delete env[key];
  }
  return { ...env, ...overrides };
}

const env = environment({
  GOTOOLCHAIN: 'local', GOENV: 'off', GOWORK: 'off', GOFLAGS: '',
  GOPATH: path.join(local, 'gopath'), GOMODCACHE: path.join(local, 'gopath', 'pkg', 'mod'),
  GOCACHE: path.join(local, 'go-cache'), GOTMPDIR: path.join(local, 'tmp'),
  TEMP: path.join(local, 'tmp'), TMP: path.join(local, 'tmp'), TMPDIR: path.join(local, 'tmp'),
  npm_config_cache: path.join(local, 'npm-cache'),
}, ['GOROOT', 'GOOS', 'GOARCH']);

function isFile(file) {
  try { return statSync(file).isFile(); } catch { return false; }
}

function npmCommand() {
  // Invoke npm's JavaScript entry directly on Windows; .cmd files need a shell.
  if (!isWindows) return { executable: 'npm', prefix: [] };
  const pathEntry = Object.entries(process.env).find(([key]) => key.toUpperCase() === 'PATH')?.[1] || '';
  const directories = [path.dirname(process.execPath), ...pathEntry.split(path.delimiter)];
  for (const directory of directories.filter(Boolean)) {
    const cli = path.join(directory.replace(/^"|"$/g, ''), 'node_modules', 'npm', 'bin', 'npm-cli.js');
    if (isFile(cli)) return { executable: process.execPath, prefix: [cli] };
  }
  throw new Error('npm CLI not found beside Node or on PATH. Install Node.js with npm.');
}

function run(executable, args, { cwd = root, capture = false } = {}) {
  if (!capture) console.log(`\n[dev] ${path.basename(executable)} ${args.map(arg => JSON.stringify(arg)).join(' ')}`);
  const result = spawnSync(executable, args, {
    cwd, env, shell: false, windowsHide: true,
    stdio: capture ? 'pipe' : 'inherit', encoding: 'utf8',
  });
  if (result.error) throw new Error(`Cannot run ${path.basename(executable)}: ${result.error.message}`);
  if (result.status !== 0) {
    const error = new Error(`${path.basename(executable)} failed (${result.signal || result.status}).${capture ? ` ${(result.stderr || '').trim()}` : ''}`);
    error.exitCode = result.status || 1;
    throw error;
  }
  return (result.stdout || '').trim();
}

function requireNode() {
  if (Number(process.versions.node.split('.')[0]) < 24) throw new Error('Node.js 24 or newer is required.');
}

function goTool() {
  const executable = process.env.GO_BINARY || 'go';
  const version = run(executable, ['version'], { capture: true });
  if (!goVersion || !version.startsWith(`go version go${goVersion} `)) {
    throw new Error(`go.mod requires Go ${goVersion}; found ${version}. Select the compiler with GO_BINARY or PATH.`);
  }
  return { executable, version };
}

function prepare() {
  for (const directory of [local, env.GOPATH, env.GOMODCACHE, env.GOCACHE, env.GOTMPDIR, env.npm_config_cache, path.join(local, 'bin')]) {
    mkdirSync(directory, { recursive: true });
  }
}

function requireWindows() {
  if (!isWindows || process.arch !== 'x64') throw new Error('The Core, CLI and native verifier development targets currently require Windows x64.');
}

function vitePath() {
  const vite = path.join(web, 'node_modules', 'vite', 'bin', 'vite.js');
  if (!isFile(vite)) throw new Error('Web dependencies are missing. Run: node scripts/dev.mjs setup');
  return vite;
}

function doctor() {
  requireNode();
  let failures = 0;
  console.log(`[dev] Repository: ${root}\n[dev] Node: ${process.version}\n[dev] Platform: ${process.platform}/${process.arch}`);
  for (const [name, inspect] of [
    ['Go', () => goTool().version],
    ['npm', () => { const npm = npmCommand(); return run(npm.executable, [...npm.prefix, '--version'], { capture: true }); }],
  ]) {
    try { console.log(`[dev] ${name}: ${inspect()}`); }
    catch (error) { failures++; console.error(`[dev] ${name}: ${error.message}`); }
  }
  console.log(`[dev] Web dependencies: ${existsSync(path.join(web, 'node_modules', 'vite')) ? 'present' : 'run setup'}`);
  console.log(`[dev] Optional Electron dependencies: ${existsSync(path.join(desktop, 'node_modules', 'electron', 'dist', 'electron.exe')) ? 'present' : 'run setup-desktop if needed'}`);
  console.log(`[dev] Cache and output directory: ${local}`);
  if (!isWindows || process.arch !== 'x64') console.log('[dev] Web development is available; native check/build require Windows x64.');
  if (failures) throw new Error(`${failures} required tool check(s) failed.`);
}

function setup() {
  requireNode();
  const go = goTool();
  const npm = npmCommand();
  prepare();
  run(go.executable, ['mod', 'download']);
  run(npm.executable, [...npm.prefix, 'ci', '--no-audit', '--no-fund'], { cwd: web });
  console.log('\n[dev] Go modules and locked web dependencies are ready.');
}

function setupDesktop() {
  requireNode();
  requireWindows();
  const npm = npmCommand();
  prepare();
  run(npm.executable, [...npm.prefix, 'ci', '--no-audit', '--no-fund'], { cwd: desktop });
  console.log('\n[dev] Locked Electron dependencies are installed. This does not assemble or launch the complete desktop tree.');
}

function check() {
  requireNode();
  requireWindows();
  const go = goTool();
  prepare();
  run(go.executable, ['mod', 'verify']);
  run(go.executable, ['test', '-mod=readonly', '-p', '1', '-run', '^$',
    './apps/control', './apps/cli', './apps/runtime-verifier', './apps/desktop/validator']);
  run(go.executable, ['test', '-mod=readonly', '-p', '1', '-count=1', './internal/canonical', './internal/store']);
  run(process.execPath, ['--test',
    'tests/ui/desktop/activity-projection.test.mjs',
    'tests/ui/desktop/managed-environment.test.mjs',
    'tests/ui/desktop/development-smoke.test.mjs',
  ]);
  run(process.execPath, ['--experimental-vm-modules', '--test', 'tests/development/google-oauth-config.test.mjs']);
  console.log('\n[dev] Development checks passed: entrypoint compilation, JSON/SQLite unit tests and mocked UI/Desktop boundary tests.');
}

function build() {
  requireNode();
  requireWindows();
  const go = goTool();
  const vite = vitePath();
  prepare();
  for (const [name, target] of [
    ['researchos-control.exe', './apps/control'],
    ['researchos.exe', './apps/cli'],
    ['runtime-verifier.exe', './apps/runtime-verifier'],
  ]) {
    run(go.executable, ['build', '-mod=readonly', '-trimpath', '-o', path.join(local, 'bin', name), target]);
  }
  run(process.execPath, [vite, 'build', '--outDir', path.join(local, 'web'), '--emptyOutDir'], { cwd: web });
  console.log(`\n[dev] Binaries: ${path.join(local, 'bin')}\n[dev] Web assets: ${path.join(local, 'web')}`);
  console.log('[dev] These are development artifacts. Complete Desktop assembly also requires Mu, client-wire bindings and the desktop build workflow.');
}

function webServer() {
  requireNode();
  let port = '5173';
  if (extra.length) {
    if (extra.length !== 2 || extra[0] !== '--port' || !/^\d+$/.test(extra[1]) || Number(extra[1]) < 1024 || Number(extra[1]) > 65535) {
      throw new Error('Usage: node scripts/dev.mjs web [--port 5173] (1024-65535).');
    }
    port = extra[1];
  }
  const vite = vitePath();
  prepare();
  console.log('[dev] Starting only the Vite UI server. Backend API calls require a separately configured Core; no backend proxy or native bridge is provided.');
  run(process.execPath, [vite, '--host', '127.0.0.1', '--port', port, '--strictPort'], { cwd: web });
}

function help() {
  console.log(`Usage: node scripts/dev.mjs <command>

  doctor          Check Node, npm and the Go version pinned by go.mod
  setup           Download Go modules and install web dependencies using npm ci
  check           Compile Windows entrypoints and run local, non-service tests
  build           Build Core, CLI, verifier and React assets into .local/dev
  web [--port N]  Run the loopback Vite UI server (default 5173)
  setup-desktop   Optionally install locked Electron dependencies; no app launch

Set GO_BINARY to a Go executable, or put Go ${goVersion} on PATH.
Native check/build currently support Windows x64. No command starts Core,
changes product data, or updates the formal execution checkpoint.`);
}

try {
  if (extra.length && command !== 'web') throw new Error(`Unexpected arguments for ${command}. Run: node scripts/dev.mjs help`);
  const commands = { doctor, setup, check, build, web: webServer, 'setup-desktop': setupDesktop, help };
  if (!Object.hasOwn(commands, command)) throw new Error(`Unknown command: ${command}. Run: node scripts/dev.mjs help`);
  commands[command]();
} catch (error) {
  console.error(`[dev] ${error.message}`);
  process.exitCode = error.exitCode || 1;
}
