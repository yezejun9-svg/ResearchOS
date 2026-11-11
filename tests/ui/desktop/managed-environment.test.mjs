import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { managedControlEnvironment } = require('../../../apps/desktop/main/lib/desktop-management.js');
const owned = { dataRoot: 'D:\\owned\\data', webDir: 'D:\\owned\\web' };

test('managed Core can discover npm CLIs under the normal account without inheriting credentials', () => {
  const result = managedControlEnvironment({ SystemRoot: 'C:\\Windows', USERPROFILE: 'C:\\Users\\owner',
    APPDATA: 'C:\\Users\\owner\\AppData\\Roaming', PATH: 'C:\\nvm4w\\nodejs;C:\\Windows\\System32',
    PATHEXT: '.COM;.EXE;.BAT;.CMD', OPENAI_API_KEY: 'private-fixture', RESEARCHOS_TOKEN: 'private-fixture',
    CODEX_HOME: 'D:\\untrusted', NODE_OPTIONS: '--require=untrusted', HTTP_PROXY: 'private-fixture',
    RESEARCHOS_DATA_DIR: 'D:\\other', RESEARCHOS_LISTEN: '0.0.0.0:9999' }, owned);
  assert.equal(result.PATH, 'C:\\nvm4w\\nodejs;C:\\Windows\\System32');
  assert.equal(result.PATHEXT, '.COM;.EXE;.BAT;.CMD');
  assert.equal(result.USERPROFILE, 'C:\\Users\\owner');
  assert.equal(result.RESEARCHOS_DATA_DIR, owned.dataRoot);
  assert.equal(result.RESEARCHOS_WEB_DIR, owned.webDir);
  assert.equal(result.RESEARCHOS_LISTEN, '127.0.0.1:0');
  for (const key of ['OPENAI_API_KEY','RESEARCHOS_TOKEN','CODEX_HOME','NODE_OPTIONS','HTTP_PROXY']) assert.equal(Object.hasOwn(result,key),false);
  assert.equal(JSON.stringify(result).includes('private-fixture'),false);
});

test('Windows mixed-case discovery keys are canonicalized without inventing an account', () => {
  const result=managedControlEnvironment({ systemroot:'c:/Windows', Path:'C:\\tools', pathext:'.EXE;.CMD', userprofile:'C:\\Users\\owner', COMSPEC:'C:\\Windows\\System32\\cmd.exe' },owned);
  assert.equal(result.PATH,'C:\\tools'); assert.equal(result.PATHEXT,'.EXE;.CMD');
  assert.equal(result.USERPROFILE,'C:\\Users\\owner'); assert.equal(result.COMSPEC,'C:\\Windows\\System32\\cmd.exe');
  assert.equal(Object.hasOwn(result,'Path'),false);
});

test('ambiguous Windows environment keys fail before spawning Core', () => {
  assert.throws(()=>managedControlEnvironment({PATH:'C:\\trusted',Path:'C:\\other'},owned),{code:'ENV_CASE_COLLISION'});
});

test('missing optional discovery variables are not guessed or replaced by a synthetic home', () => {
  const result=managedControlEnvironment({SystemRoot:'C:\\Windows',PATH:undefined,USERPROFILE:'',OTHER:'ignored'},owned);
  assert.equal(Object.hasOwn(result,'PATH'),false);assert.equal(Object.hasOwn(result,'USERPROFILE'),false);
  assert.deepEqual(Object.keys(result).sort(),['RESEARCHOS_DATA_DIR','RESEARCHOS_LISTEN','RESEARCHOS_WEB_DIR','SystemDrive','SystemRoot']);
});


test('SystemDrive is derived from the real system volume, not bundle/data/cwd or ambient drive', async t => {
  for (const [root, expected] of [['C:\\Windows','C:'],['c:\\Windows','C:'],['d:/WinNT','D:'],['E:\\OS Folder\\Windows\\','E:']]) {
    await t.test(root, () => {
      const result=managedControlEnvironment({SystemRoot:root,SystemDrive:'Z:',systemdrive:'X:',
        OPENAI_API_KEY:'private-fixture',HTTPS_PROXY:'private-fixture',ALL_PROXY:'private-fixture',NO_PROXY:'private-fixture',
        NODE_OPTIONS:'--require=untrusted',CODEX_HOME:'Z:\\untrusted',RESEARCHOS_DATA_DIR:'Z:\\outside'},
        {...owned,cwd:'D:\\sealed-bundle'});
      assert.equal(result.SystemDrive,expected);
      assert.equal(result.SystemRoot,root);
      assert.deepEqual(Object.keys(result).filter(key=>key.toUpperCase()==='SYSTEMDRIVE'),['SystemDrive']);
      assert.equal(result.RESEARCHOS_DATA_DIR,owned.dataRoot);
      for(const key of ['OPENAI_API_KEY','HTTPS_PROXY','ALL_PROXY','NO_PROXY','NODE_OPTIONS','CODEX_HOME','cwd']) assert.equal(Object.hasOwn(result,key),false);
      assert.equal(JSON.stringify(result).includes('private-fixture'),false);
    });
  }
});

test('mixed-case matching system directories are accepted without forwarding drive aliases', () => {
  const result=managedControlEnvironment({sYsTeMrOoT:'c:/Windows/',windir:'C:\\WINDOWS',SYSTEMDRIVE:'Z:'},owned);
  assert.equal(result.SystemDrive,'C:');assert.equal(result.SystemRoot,'c:/Windows/');
  assert.equal(result.WINDIR,'C:\\WINDOWS');assert.equal(Object.hasOwn(result,'SYSTEMDRIVE'),false);
});

test('missing, relative, unresolved, device and ambiguous system roots fail closed', async t => {
  for(const [name,root] of [
    ['missing',undefined],['null',null],['number',7],['empty',''],['relative','Windows'],['drive-relative','C:Windows'],
    ['root-relative','\\Windows'],['UNC','\\\\server\\share\\Windows'],['device','\\\\?\\C:\\Windows'],
    ['DOS device','\\\\.\\C:\\Windows'],['placeholder','%SystemRoot%'],['embedded placeholder','C:\\%root%'],
    ['NUL','C:\\Windows\0tail'],['newline','C:\\Windows\ntail'],['volume only','C:\\'],
    ['parent segment','C:\\Windows\\..\\Else'],['current segment','C:\\Windows\\.\\System'],['alternate stream','C:\\Windows:stream'],
  ]) await t.test(name,()=>assert.throws(()=>managedControlEnvironment({SystemRoot:root,SystemDrive:'C:'},owned),{code:'SYSTEMROOT_INVALID'}));
  for(const windir of ['D:\\Windows','C:\\OtherWindows','Windows','%SystemRoot%'])
    await t.test('conflicting WINDIR '+windir,()=>assert.throws(()=>managedControlEnvironment({SystemRoot:'C:\\Windows',WINDIR:windir},owned),{code:'SYSTEMROOT_INVALID'}));
  await t.test('duplicate SystemRoot case aliases',()=>assert.throws(()=>managedControlEnvironment({SystemRoot:'C:\\Windows',systemroot:'C:\\Windows'},owned),{code:'ENV_CASE_COLLISION'}));
});
