// Actual source function/launch-fragment checks only: no SDK or filesystem state.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const source=fs.readFileSync(new URL('./real-electron-flow.mjs',import.meta.url),'utf8');
const begin=source.indexOf('export function makeEnvironment('),end=source.indexOf('function requireChatGPTAuthentication(',begin);
const context=vm.createContext({path,requireThat:(ok,code)=>{if(!ok)throw new Error(code);}});
vm.runInContext(source.slice(begin,end).replace('export function','function')+'\nthis.makeEnvironment=makeEnvironment',context);
const scope={windows:{system_root:'C:/Windows',normal_user_profile:'C:/Users/synthetic',
  normal_app_data:'C:/Users/synthetic/AppData/Roaming',normal_local_app_data:'C:/Users/synthetic/AppData/Local'},
  run_root:'C:/synthetic-owned-run',bundle:{root:'C:/sealed-bundle'},node:{path:'C:/tools/node.exe'},codex:{executable:'C:/tools/codex.exe'}};
let passed=0;
for(const [root,drive] of [['C:/Windows','C:'],['c:\\Windows','C:'],['D:\\Windows','D:']]) {
  assert.equal(context.makeEnvironment({...scope,windows:{...scope.windows,system_root:root}}).SystemDrive,drive);passed++;
}
assert.throws(()=>context.makeEnvironment({...scope,windows:{...scope.windows,system_root:'\\\\server\\share\\Windows'}}),/SYSTEMROOT_DRIVE_REQUIRED/);passed++;
assert.throws(()=>context.makeEnvironment({...scope,windows:{...scope.windows,system_root:'C:Windows'}}),/WINDOWS_PATHS_REQUIRED/);passed++;
assert.equal(context.makeEnvironment({...scope,windows:{...scope.windows,system_drive:'Z:'}}).SystemDrive,'C:');passed++;
const a=source.indexOf('app = await _electron.launch('),b=source.indexOf('});',a)+3;
assert(a>source.indexOf('fs.mkdirSync(scope.run_root)')&&b>a);
let captured;
const launchContext=vm.createContext({path,scope,bundle:{bundle:scope.bundle.root},env:{SystemDrive:'C:'},
  until:Date.now()+60000,Date,Math,app:null,_electron:{launch:async options=>{captured=options;return 'FAKE_TEST_ONLY';}}});
await new vm.Script('(async()=>{'+source.slice(a,b)+'})()').runInContext(launchContext);
assert.equal(captured.cwd,scope.run_root);assert.notEqual(captured.cwd,scope.bundle.root);
assert.equal(captured.executablePath,path.join(scope.bundle.root,'runtime/electron/electron.exe'));passed++;
assert(source.includes("electron_cwd: scope.run_root"));passed++;
console.log(JSON.stringify({status:'ENVIRONMENT_ELECTRON_CWD_PURE_PASS',passed,sdk:0,gui:0,core:0,model:0}));
