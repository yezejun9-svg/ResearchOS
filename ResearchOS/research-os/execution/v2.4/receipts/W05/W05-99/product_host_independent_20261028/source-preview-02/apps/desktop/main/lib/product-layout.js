'use strict';

// This module is deliberately free of Electron APIs. The installer marker is
// generated only for a complete, location-bound product layout.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const SCHEMA = 'researchos.product-layout/1';
const BINDING_SCHEMA = 'researchos.product-data-binding/1';
const WITNESS_SCHEMA = 'researchos.product-supervisor/1';
const HASH = /^[a-f0-9]{64}$/;
const INSTALL_ID = /^[a-f0-9]{64}$/;

function refusal(code) { const error = new Error(code); error.code = code; return error; }
function sha(raw) { return crypto.createHash('sha256').update(raw).digest('hex'); }
function folded(p) { return path.normalize(p).toLocaleLowerCase('en-US'); }

function exactPath(p, kind = 'file', fsImpl = fs) {
  if (typeof p !== 'string' || !path.isAbsolute(p)) throw refusal('PRODUCT_PATH_REQUIRED');
  const full = path.resolve(p);
  let current = path.parse(full).root;
  for (const part of full.slice(current.length).split(path.sep).filter(Boolean)) {
    current = path.join(current, part);
    if (!fsImpl.existsSync(current)) break;
    const item = fsImpl.lstatSync(current);
    if (item.isSymbolicLink())
      throw refusal('PRODUCT_PATH_REDIRECTED');
  }
  const info = fsImpl.lstatSync(full);
  if (kind === 'file' ? !info.isFile() : !info.isDirectory()) throw refusal('PRODUCT_PATH_TYPE');
  if (folded(fsImpl.realpathSync.native(full)) !== folded(full)) throw refusal('PRODUCT_PATH_REDIRECTED');
  return full;
}

function relativeFile(root, relative, fsImpl = fs) {
  if (typeof relative !== 'string' || !relative || relative.includes('\\') ||
      relative.startsWith('/') || relative.split('/').some(part => !part || part === '.' || part === '..'))
    throw refusal('PRODUCT_FILE_PATH');
  const full = path.resolve(root, ...relative.split('/'));
  if (!folded(full).startsWith(folded(root) + path.sep)) throw refusal('PRODUCT_FILE_PATH');
  return exactPath(full, 'file', fsImpl);
}

function installationIdentity(marker) {
  const hashes = marker.binaries;
  return sha([SCHEMA, marker.install_root, marker.source_commit, marker.source_digest,
    marker.inventory_digest, marker.product_version, marker.client_protocol,
    String(marker.schema_version), ...['cli', 'control', 'electron', 'verifier', 'validator']
      .map(key => hashes[key]?.sha256 || '')].join('\n') + '\n');
}

function inventoryIdentity(files) {
  return sha('researchos.product-inventory/1\n' + files.map(row =>
    `${row.path}\n${row.sha256}\n${row.bytes}\n`).join(''));
}

function loadProductLayout(repo, fsImpl = fs) {
  const root = path.resolve(repo);
  const markerPath = path.join(root, 'installed-product.json');
  if (!fsImpl.existsSync(markerPath)) {
    // A generated product tree must never silently become a development tree.
    if (fsImpl.existsSync(path.join(root, 'runtime', 'electron')) ||
        fsImpl.existsSync(path.join(root, 'bin', 'researchos.exe')))
      throw refusal('PRODUCT_MANIFEST_UNAVAILABLE');
    return null;
  }
  exactPath(root, 'directory', fsImpl);
  const raw = fsImpl.readFileSync(exactPath(markerPath, 'file', fsImpl));
  if (raw.length < 32 || raw.length > 1 << 20) throw refusal('PRODUCT_MANIFEST_SIZE');
  let marker;
  try { marker = JSON.parse(raw.toString('utf8')); }
  catch { throw refusal('PRODUCT_MANIFEST_INVALID'); }
  if (!marker || marker.schema !== SCHEMA || marker.mode !== 'OWNED_PRODUCT_LAYOUT_NOT_INSTALLER' ||
      folded(marker.install_root || '') !== folded(root) || !INSTALL_ID.test(marker.installation_id || '') ||
      !/^[a-f0-9]{40}$/.test(marker.source_commit || '') ||
      !HASH.test(marker.source_digest || '') || !HASH.test(marker.inventory_digest || '') ||
      marker.product_version !== '2.4.0' ||
      marker.client_protocol !== 'researchos-client/2' || marker.schema_version !== 24 ||
      !marker.binaries || !Array.isArray(marker.files) || marker.files.length < 100 ||
      inventoryIdentity(marker.files) !== marker.inventory_digest ||
      installationIdentity(marker) !== marker.installation_id)
    throw refusal('PRODUCT_MANIFEST_INVALID');
  const names = new Set();
  let previousPath = '';
  for (const row of marker.files) {
    if (!row || !HASH.test(row.sha256 || '') || !Number.isSafeInteger(row.bytes) || row.bytes < 0)
      throw refusal('PRODUCT_MANIFEST_INVALID');
    const name = row.path.toLocaleLowerCase('en-US');
    if (names.has(name) || (previousPath && row.path <= previousPath)) throw refusal('PRODUCT_MANIFEST_ALIAS');
    names.add(name);
    previousPath = row.path;
    const full = relativeFile(root, row.path, fsImpl);
    const content = fsImpl.readFileSync(full);
    if (content.length !== row.bytes || sha(content) !== row.sha256) throw refusal('PRODUCT_FILE_CHANGED');
  }
  for (const key of ['cli', 'control', 'electron', 'verifier', 'validator']) {
    const item = marker.binaries[key];
    if (!item || !HASH.test(item.sha256 || '') || !names.has(String(item.path).toLocaleLowerCase('en-US')))
      throw refusal('PRODUCT_BINARY_MISSING');
    if (sha(fsImpl.readFileSync(relativeFile(root, item.path, fsImpl))) !== item.sha256)
      throw refusal('PRODUCT_BINARY_CHANGED');
  }
  const local = process.env.LOCALAPPDATA;
  if (typeof local !== 'string' || !path.isAbsolute(local)) throw refusal('PRODUCT_LOCALAPPDATA_REQUIRED');
  const base = path.join(path.resolve(local), 'ResearchOS');
  const dataRoot = path.join(base, 'data');
  return Object.freeze({ root, markerPath, marker, installID: marker.installation_id,
    inventoryDigest: marker.inventory_digest,
    dataRoot, discovery: path.join(dataRoot, 'discovery.json'),
    witness: path.join(dataRoot, 'product-supervisor.json'),
    binding: path.join(dataRoot, 'product-binding.json'),
    userData: path.join(base, 'desktop-user-data'),
    cliConfig: path.join(base, 'cli-config.json'),
    controlExe: relativeFile(root, marker.binaries.control.path, fsImpl),
    electronExe: relativeFile(root, marker.binaries.electron.path, fsImpl),
    webDir: path.join(root, 'apps', 'web', 'dist'),
    verifierManifest: path.join(root, 'apps', 'desktop', 'resources', 'control', 'runtime-verifier-installation.json'),
    runtimeAssetsDir: path.join(root, 'apps', 'desktop', 'resources', 'control', 'runtime') });
}

function verifyProductParent(layout, parent, executable = process.execPath) {
  if (folded(executable) !== folded(layout.electronExe) ||
      parent?.PID !== process.pid ||
      parent.ImageSHA256 !== layout.marker.binaries.electron.sha256 ||
      !/^[0-9]+$/.test(parent.CreatedNS || ''))
    throw refusal('PRODUCT_PARENT_IDENTITY');
  return parent;
}

function validateProductPaths(layout, fsImpl = fs) {
  const local = path.resolve(process.env.LOCALAPPDATA);
  exactPath(local, 'directory', fsImpl);
  for (const directory of [path.dirname(layout.dataRoot), layout.dataRoot, layout.userData]) {
    if (fsImpl.existsSync(directory)) exactPath(directory, 'directory', fsImpl);
  }
  for (const file of [layout.binding, layout.witness, layout.discovery, layout.cliConfig]) {
    if (fsImpl.existsSync(file)) exactPath(file, 'file', fsImpl);
  }
}

function claimProductData(layout, fsImpl = fs) {
  const { dataRoot, binding, installID } = layout;
  validateProductPaths(layout, fsImpl);
  const expected = { schema: BINDING_SCHEMA, installation_id: installID };
  if (fsImpl.existsSync(dataRoot)) {
    exactPath(dataRoot, 'directory', fsImpl);
    if (!fsImpl.existsSync(binding)) {
      const entries = fsImpl.readdirSync(dataRoot);
      if (entries.length) {
        if (entries.length !== 1 || entries[0] !== path.basename(layout.witness))
          throw refusal('PRODUCT_DATA_UNBOUND');
        const starting = JSON.parse(fsImpl.readFileSync(exactPath(layout.witness, 'file', fsImpl), 'utf8'));
        if (starting.state !== 'STARTING' || starting.installation_id !== installID ||
            starting.install_root !== layout.root || starting.inventory_digest !== layout.inventoryDigest ||
            starting.parent_process.PID !== process.pid)
          throw refusal('PRODUCT_DATA_UNBOUND');
      }
    } else {
      const saved = JSON.parse(fsImpl.readFileSync(exactPath(binding, 'file', fsImpl), 'utf8'));
      if (saved.schema !== expected.schema || saved.installation_id !== installID)
        throw refusal('PRODUCT_DATA_INSTALLATION_CONFLICT');
      return;
    }
  } else fsImpl.mkdirSync(dataRoot, { recursive: true, mode: 0o700 });
  const file = binding + '.' + process.pid + '.tmp';
  fsImpl.writeFileSync(file, JSON.stringify(expected) + '\n', { flag: 'wx', mode: 0o600 });
  try { fsImpl.renameSync(file, binding); }
  catch (error) { try { fsImpl.unlinkSync(file); } catch {} throw error; }
}

function writeWitnessAtomic(layout, value, fsImpl = fs) {
  const file = layout.witness + '.' + process.pid + '.tmp';
  fsImpl.writeFileSync(file, JSON.stringify(value) + '\n', { flag: 'wx', mode: 0o600 });
  try { fsImpl.renameSync(file, layout.witness); }
  catch (error) { try { fsImpl.unlinkSync(file); } catch {} throw error; }
  return value;
}

function writeStartupWitness(layout, parent, fsImpl = fs) {
  validateProductPaths(layout, fsImpl);
  if (fsImpl.existsSync(layout.witness)) throw refusal('PRODUCT_EXISTING_WITNESS');
  if (fsImpl.existsSync(layout.dataRoot)) {
    if (fsImpl.existsSync(layout.binding)) {
      const binding = JSON.parse(fsImpl.readFileSync(exactPath(layout.binding, 'file', fsImpl), 'utf8'));
      if (binding.schema !== BINDING_SCHEMA || binding.installation_id !== layout.installID)
        throw refusal('PRODUCT_DATA_INSTALLATION_CONFLICT');
    } else if (fsImpl.readdirSync(layout.dataRoot).length) throw refusal('PRODUCT_DATA_UNBOUND');
  }
  if (!Number.isSafeInteger(parent?.PID) || parent.PID !== process.pid ||
      !/^[0-9]+$/.test(parent.CreatedNS || '') || !HASH.test(parent.ImageSHA256 || ''))
    throw refusal('PRODUCT_PARENT_IDENTITY');
  fsImpl.mkdirSync(layout.dataRoot, { recursive: true, mode: 0o700 });
  const value = { schema: WITNESS_SCHEMA, state: 'STARTING', install_root: layout.root,
    installation_id: layout.installID, inventory_digest: layout.inventoryDigest,
    data_root: layout.dataRoot, nonce: crypto.randomUUID(), parent_process: parent };
  return writeWitnessAtomic(layout, value, fsImpl);
}

function writeSupervisorWitness(layout, management, startup, fsImpl = fs) {
  if (management.state !== 'READY' || !management.identity || !management.parentIdentity || !management.hostId)
    throw refusal('PRODUCT_MANAGER_NOT_READY');
  const current = management.currentHost();
  if (folded(current.data_dir) !== folded(layout.dataRoot) || current.pid !== management.identity.PID)
    throw refusal('PRODUCT_MANAGER_IDENTITY_CHANGED');
  const prior = JSON.parse(fsImpl.readFileSync(exactPath(layout.witness, 'file', fsImpl), 'utf8'));
  if (JSON.stringify(prior) !== JSON.stringify(startup) ||
      JSON.stringify(startup.parent_process) !== JSON.stringify(management.parentIdentity))
    throw refusal('PRODUCT_STARTUP_WITNESS_CHANGED');
  const witness = { ...startup, state: 'READY', host_id: management.hostId,
    control_process: management.identity, parent_process: management.parentIdentity };
  return writeWitnessAtomic(layout, witness, fsImpl);
}

function retireSupervisorWitness(layout, witness, fsImpl = fs) {
  try {
    const saved = JSON.parse(fsImpl.readFileSync(layout.witness, 'utf8'));
    if (saved.nonce !== witness.nonce || saved.state !== witness.state ||
        saved.host_id !== witness.host_id || saved.installation_id !== witness.installation_id ||
        JSON.stringify(saved.control_process) !== JSON.stringify(witness.control_process)) return false;
    fsImpl.unlinkSync(layout.witness);
    return true;
  } catch { return false; }
}

function acceptProductIntent(installID, data) {
  return data?.installation_id === installID && ['ensure-host', 'show-ui'].includes(data.intent)
    ? data.intent : null;
}

function createProductSafeExit({ management, ownedIdentity, confirm, retire, onExit, onRefused }) {
  let pending = null;
  let stopped = false;
  return () => {
    if (pending) return pending;
    pending = (async () => {
      try {
        if (!stopped) {
          const owned = ownedIdentity(management);
          if (!owned) throw refusal('OWNED_CORE_IDENTITY_UNAVAILABLE');
          const result = await management.shutdown();
          if (!confirm(result, management, owned)) throw refusal('OWNED_EXIT_IDENTITY_UNCONFIRMED');
          stopped = true;
        }
        if (retire() !== true) throw refusal('PRODUCT_WITNESS_RETIRE_UNCONFIRMED');
      } catch (error) {
        await onRefused(error);
        throw error;
      }
      await onExit(true);
    })().finally(() => { pending = null; });
    return pending;
  };
}

module.exports = { SCHEMA, BINDING_SCHEMA, WITNESS_SCHEMA, installationIdentity,
  inventoryIdentity, loadProductLayout, validateProductPaths, claimProductData,
  writeStartupWitness, writeSupervisorWitness, retireSupervisorWitness,
  acceptProductIntent, createProductSafeExit, verifyProductParent };
