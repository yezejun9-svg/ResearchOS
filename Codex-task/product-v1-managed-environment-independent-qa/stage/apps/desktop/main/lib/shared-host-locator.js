'use strict';

// Position only: no URL, token, principal, project, session, or writer state.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { strictJSON } = require('./desktop-management.js');
const { HOST_ID } = require('./native.js');
const { readDiscovery } = require('./host.js');
const SCHEMA = 'researchos.shared-host-locator/1';
const fail = code => Object.assign(new Error(code), { code });
const folded = value => process.platform === 'win32' ? path.resolve(value).toLowerCase() : path.resolve(value);

function canonicalPath(fsImpl, value, directory) {
  if (typeof value !== 'string' || !path.isAbsolute(value) || value.includes('\0') ||
      process.platform === 'win32' && (!/^[a-z]:[\\/]/i.test(value) || value.startsWith('\\\\')))
    throw fail('HOST_LOCATOR_PATH_INVALID');
  const stat = fsImpl.lstatSync(value);
  if (stat.isSymbolicLink() || (directory ? !stat.isDirectory() : !stat.isFile()) ||
      folded(fsImpl.realpathSync(value)) !== folded(value)) throw fail('HOST_LOCATOR_PATH_ALIAS');
  return value;
}

function readLocator(fsImpl, file) {
  canonicalPath(fsImpl, file, false);
  const stat = fsImpl.lstatSync(file);
  if (stat.size <= 0 || stat.size > 8192) throw fail('HOST_LOCATOR_INVALID');
  const value = strictJSON(fsImpl.readFileSync(file));
  const names = ['schema', 'discovery_file', 'data_root', 'host_instance_id'];
  if (!value || Array.isArray(value) || Object.keys(value).length !== names.length ||
      names.some(name => !Object.hasOwn(value, name)) || value.schema !== SCHEMA || !HOST_ID.test(value.host_instance_id))
    throw fail('HOST_LOCATOR_INVALID');
  canonicalPath(fsImpl, value.discovery_file, false);
  canonicalPath(fsImpl, value.data_root, true);
  return value;
}

function sameLocator(a, b) {
  return a.schema === b.schema && a.host_instance_id === b.host_instance_id &&
    folded(a.discovery_file) === folded(b.discovery_file) && folded(a.data_root) === folded(b.data_root);
}

function publishOwnedHostLocator({ management, discoveryFile, dataRoot, env = process.env, fsImpl = fs }) {
  if (env.RESEARCHOS_SHARED_HOST_LOCATOR_DISABLED === '1') return { status: 'DISABLED' };
  if (management?.state !== 'READY') throw fail('HOST_LOCATOR_OWNED_READY_REQUIRED');
  // currentHost checks both process identities, private READY, child PID and native Host ID.
  const owned = management.currentHost();
  if (typeof management.options?.discoveryFile !== 'string' || typeof management.options?.dataRoot !== 'string' ||
      folded(management.options.discoveryFile) !== folded(discoveryFile) || folded(management.options.dataRoot) !== folded(dataRoot))
    throw fail('HOST_LOCATOR_IDENTITY_MISMATCH');
  canonicalPath(fsImpl, discoveryFile, false);
  canonicalPath(fsImpl, dataRoot, true);
  const discoveryStat = fsImpl.lstatSync(discoveryFile);
  if (discoveryStat.size <= 0 || discoveryStat.size > 8192) throw fail('HOST_LOCATOR_DISCOVERY_INVALID');
  const discoveryBytes = fsImpl.readFileSync(discoveryFile);
  const decoded = strictJSON(discoveryBytes);
  const discoveryKeys = ['url', 'pid', 'data_dir', 'host_instance_id'];
  if (!decoded || Array.isArray(decoded) || Object.keys(decoded).length !== 4 ||
      discoveryKeys.some(key => !Object.hasOwn(decoded, key))) throw fail('HOST_LOCATOR_DISCOVERY_INVALID');
  const fresh = readDiscovery({ readFileSync: () => discoveryBytes.toString('utf8') }, discoveryFile);
  const d = fresh.discovery;
  if (!fresh.ok || !d || !HOST_ID.test(d.host_instance_id) || d.host_instance_id !== management.hostId ||
      d.host_instance_id !== owned.host_instance_id || d.pid !== owned.pid || d.url !== owned.url ||
      typeof d.data_dir !== 'string' || folded(d.data_dir) !== folded(dataRoot) || folded(owned.data_dir) !== folded(dataRoot))
    throw fail('HOST_LOCATOR_IDENTITY_MISMATCH');
  // Recheck process and discovery identity after parsing, before creating global paths.
  const rechecked = management.currentHost();
  if (rechecked.host_instance_id !== owned.host_instance_id || rechecked.pid !== owned.pid ||
      rechecked.url !== owned.url || rechecked.data_dir !== owned.data_dir) throw fail('HOST_LOCATOR_IDENTITY_MISMATCH');
  const base = env.LOCALAPPDATA;
  if (typeof base !== 'string' || !path.isAbsolute(base)) throw fail('HOST_LOCATOR_BASE_UNAVAILABLE');
  canonicalPath(fsImpl, base, true);
  const directory = path.join(base, 'ResearchOS');
  fsImpl.mkdirSync(directory, { recursive: true, mode: 0o700 });
  canonicalPath(fsImpl, directory, true);
  const file = path.join(directory, 'host-locator-v1.json');
  const record = { schema: SCHEMA, discovery_file: discoveryFile, data_root: dataRoot, host_instance_id: d.host_instance_id };
  const existing = () => {
    let previous;
    try { previous = readLocator(fsImpl, file); }
    catch { throw fail('HOST_LOCATOR_CONFLICT'); }
    if (!sameLocator(previous, record)) throw fail('HOST_LOCATOR_CONFLICT');
    return { status: 'UNCHANGED' };
  };
  try { fsImpl.lstatSync(file); return existing(); }
  catch (error) { if (error.code !== 'ENOENT') throw error; }
  const temporary = path.join(directory, '.host-locator-' + crypto.randomUUID() + '.tmp');
  let fd;
  try {
    fd = fsImpl.openSync(temporary, 'wx', 0o600);
    fsImpl.writeFileSync(fd, JSON.stringify(record) + '\n');
    fsImpl.fsyncSync(fd); fsImpl.closeSync(fd); fd = undefined;
    // Publish a complete inode without replacing a competing locator. No rename fallback.
    try { fsImpl.linkSync(temporary, file); }
    catch (error) { if (error.code === 'EEXIST') return existing(); throw error; }
    return { status: 'PUBLISHED' };
  } finally {
    if (fd !== undefined) fsImpl.closeSync(fd);
    if (fsImpl.existsSync(temporary)) fsImpl.unlinkSync(temporary);
  }
}

module.exports = { SCHEMA, readLocator, publishOwnedHostLocator };
