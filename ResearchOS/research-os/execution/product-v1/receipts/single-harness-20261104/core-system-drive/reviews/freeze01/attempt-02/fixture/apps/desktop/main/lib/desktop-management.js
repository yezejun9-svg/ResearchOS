const path=require('node:path');
function failure(code) { const e = new Error(code); e.code = code; return e; }
function managedControlEnvironment(ambient, options) {
  const env = {};
  for (const name of ['SystemRoot', 'WINDIR', 'TEMP', 'TMP', 'USERPROFILE', 'APPDATA',
    'LOCALAPPDATA', 'PATH', 'PATHEXT', 'COMSPEC']) {
    const entries = Object.entries(ambient).filter(([key]) => key.toUpperCase() === name.toUpperCase());
    if (entries.length > 1) throw failure('ENV_CASE_COLLISION');
    if (entries.length && typeof entries[0][1] === 'string' && entries[0][1]) env[name] = entries[0][1];
  }
  // Shell components running inside Core need the Windows volume even when
  // the installed bundle/data root is on another drive. Never trust an ambient
  // SystemDrive: derive it only from the validated public system directory.
  const systemDirectory = value => {
    if (typeof value !== 'string' || !value || /[\x00-\x1f%<>"|?*]/.test(value) ||
        value.slice(2).includes(':') || /(?:^|[\\/])\.{1,2}(?:[\\/]|$)/.test(value) ||
        !path.win32.isAbsolute(value)) throw failure('SYSTEMROOT_INVALID');
    const normalized = path.win32.normalize(value);
    const volume = path.win32.parse(normalized).root;
    if (!/^[A-Za-z]:\\$/.test(volume) || normalized.length <= volume.length)
      throw failure('SYSTEMROOT_INVALID');
    return normalized.replace(/\\$/, '');
  };
  const systemRoot = systemDirectory(env.SystemRoot);
  if (env.WINDIR && systemDirectory(env.WINDIR).toLowerCase() !== systemRoot.toLowerCase())
    throw failure('SYSTEMROOT_INVALID');
  env.SystemDrive = systemRoot.slice(0, 2).toUpperCase();
  return Object.assign(env, { RESEARCHOS_DATA_DIR: options.dataRoot,
    RESEARCHOS_WEB_DIR: options.webDir, RESEARCHOS_LISTEN: '127.0.0.1:0' });
}

module.exports={managedControlEnvironment};
