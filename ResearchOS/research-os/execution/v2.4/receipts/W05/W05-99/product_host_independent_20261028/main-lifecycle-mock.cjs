'use strict';
// Pure VM review: Electron, Core management, files, pipes and network are mocks.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const {EventEmitter} = require('node:events');
const sourceRoot = path.resolve(process.argv[2]);
const output = path.resolve(process.argv[3]);
if (!output.startsWith(path.resolve(__dirname) + path.sep)) throw Error('OUTPUT_OUTSIDE_REVIEW');
if (fs.existsSync(output)) throw Error('OUTPUT_ALREADY_EXISTS');
const source = fs.readFileSync(path.join(sourceRoot, 'apps/desktop/main/main.js'), 'utf8');
const product = require(path.join(sourceRoot, 'apps/desktop/main/lib/product-layout.js'));
const tick = () => new Promise(resolve => setImmediate(resolve));
const results = [];
function deferred() { let resolve, reject; const promise = new Promise((a,b) => {resolve=a; reject=b;}); return {promise,resolve,reject}; }
function harness({primary=true, background=true, failure=false}={}) {
  const calls = {start:0, shutdown:0, windows:0, trays:0, diagnostics:[], quit:0, exit:[], writes:[], order:[], ipc:[]};
  const ready=deferred(), started=deferred();
  const layout={installID:'a'.repeat(64), userData:'C:\\mock\\profile', dataRoot:'C:\\mock\\data', discovery:'C:\\mock\\data\\discovery.json',
    controlExe:'C:\\mock\\control.exe', verifierManifest:'C:\\mock\\verifier.json', runtimeAssetsDir:'C:\\mock\\runtime', electronExe:'C:\\mock\\electron.exe'};
  const app=new EventEmitter();
  const windows=[], trays=[];
  app.setPath=()=>calls.order.push('set-user-data'); app.getPath=()=>layout.userData;
  app.requestSingleInstanceLock=()=>{calls.order.push('lock');return primary;};
  app.whenReady=()=>ready.promise; app.getFileIcon=async()=>({mock:true});
  app.quit=()=>{let prevented=false;app.emit('before-quit',{preventDefault(){prevented=true;}});if(!prevented){calls.quit++;for(const win of windows){win.destroyed=true;win.emit('closed');}}};
  app.exit=code=>calls.exit.push(code);
  class Window extends EventEmitter {
    constructor(){super();calls.windows++;windows.push(this);this.destroyed=false;this.webContents=new EventEmitter();
      this.webContents.setWindowOpenHandler=()=>{};this.webContents.executeJavaScript=async()=>({bridge:true,react_root:true,mounted_title:'ResearchOS',navigation:1});}
    isDestroyed(){return this.destroyed;} isMinimized(){return false;} restore(){} show(){} focus(){}
    async loadURL(){} close(){let prevented=false;this.emit('close',{preventDefault(){prevented=true;}});if(!prevented){this.destroyed=true;this.emit('closed');}}
  }
  Window.fromWebContents=()=>windows[0];
  class Tray extends EventEmitter {constructor(){super();calls.trays++;trays.push(this);}setToolTip(){}setContextMenu(menu){this.menu=menu;}destroy(){this.destroyed=true;}}
  const management={state:'NOT_STARTED',hostId:'host-123456789abc',identity:{PID:300,CreatedNS:'123',ImageSHA256:'b'.repeat(64)},
    parentIdentity:{PID:200,CreatedNS:'122',ImageSHA256:'c'.repeat(64)},uncertain:false,busy:false,
    observe(){return this.parentIdentity;},summary(){return {state:this.state,reason:this.failure};},
    currentHost(){if(this.state!=='READY')throw Error('not ready');return {pid:300,data_dir:layout.dataRoot};},
    hasUnconfirmedChild(){return this.uncertain;},
    async start(){calls.start++;calls.order.push('start');this.state='STARTING';this.uncertain=true;await started.promise;
      if(failure){this.state='BROKEN';this.failure='READY_TIMEOUT';throw Error('READY_TIMEOUT');}this.state='READY';return this.summary();},
    async shutdown(){calls.shutdown++;if(this.busy)throw Object.assign(Error('SHUTDOWN_REFUSED'),{code:'SHUTDOWN_REFUSED'});
      this.state='STOPPED';this.uncertain=false;return {state:'STOPPED',process_exit_confirmed:true};}};
  const ipc={BRIDGE:[],register:()=>calls.ipc.push('register'),registerV2:()=>calls.ipc.push('v2'),registerDesktopReview:()=>calls.ipc.push('review'),
    registerDesktopQualification:()=>calls.ipc.push('qualification'),registerDesktopCoding:()=>calls.ipc.push('coding')};
  const imports={
    electron:{app,BrowserWindow:Window,Tray,Menu:{buildFromTemplate:x=>x},ipcMain:{handle:name=>calls.ipc.push(name)},
      dialog:{showMessageBox:async(...args)=>{calls.diagnostics.push(args.at(-1));return{};}},protocol:{registerSchemesAsPrivileged(){},handle(){}}},
    'node:child_process':{spawn(){throw Error('REAL_SPAWN_FORBIDDEN');}},'node:http':{request(){throw Error('REAL_NETWORK_FORBIDDEN');}},
    'node:fs':{mkdirSync:name=>calls.writes.push(name)},
    './lib/host.js':{ensureCore:async()=>({health:'UP',discovery:{pid:300,url:'http://127.0.0.1:1'},launched:true,spawns:1})},
    './lib/ipc.js':ipc,'./lib/http-wire.js':{createTransport:()=>({})},
    './lib/native.js':{createCredentialProvider:()=>async()=> 'mock-credential'},
    './lib/app-protocol.js':{APP_ORIGIN:'ros-app://desktop',routeTable:()=>({}),createAppProtocol:()=>({})},
    './lib/first-use.js':{chooseWorkspace(){}},'./lib/context.js':{createContextStore:()=>({load:()=>({}),save(){}})},
    './lib/desktop-management.js':{createDesktopManagement:()=>management},
    './lib/product-layout.js':{...product,loadProductLayout:()=>layout,validateProductPaths(){},verifyProductParent:(_l,p)=>p,
      writeStartupWitness:()=>({state:'STARTING',nonce:'mock'}),claimProductData(){},
      writeSupervisorWitness:()=>({state:'READY',nonce:'mock'}),retireSupervisorWitness:()=>true},
  };
  const sandbox={module:{exports:{}},exports:{},__dirname:'C:\\mock\\apps\\desktop\\main',
    process:{pid:200,execPath:layout.electronExe,argv:background?['electron','app','--product-host-background']:['electron','app'],env:{},versions:{electron:'MOCK'}},
    console:{log(){},error(){}},Buffer,URL,TextDecoder,Promise,setTimeout,clearTimeout,
    require(name){if(name in imports)return imports[name];if(name==='node:path'||name==='node:crypto'||name==='node:util')return require(name);
      if(name.endsWith('openapi.json'))return {};throw Error('UNMOCKED_IMPORT:'+name);}};
  vm.runInNewContext(source,sandbox,{filename:'captured-main.js'});
  return {calls,app,ready,started,management,windows,trays};
}
async function main(){
  const winner=harness();winner.ready.resolve();await tick();
  assert.equal(winner.calls.start,1);assert.equal(winner.calls.trays,1);assert.equal(winner.calls.windows,0);
  assert(winner.calls.order.indexOf('lock')<winner.calls.order.indexOf('start'));
  winner.app.emit('second-instance',{},[],'.',{installation_id:'a'.repeat(64),intent:'show-ui'});
  winner.started.resolve();await tick();await tick();
  assert.equal(winner.calls.windows,1);assert.equal(winner.calls.start,1);
  winner.app.emit('second-instance',{},[],'.',{installation_id:'a'.repeat(64),intent:'show-ui'});await tick();
  assert.equal(winner.calls.windows,1);assert.equal(winner.calls.start,1);
  results.push({id:'MAIN-STARTING-QUEUED-SHOW-READY-REUSE',pass:true});
  winner.management.busy=true;winner.windows[0].close();await tick();
  assert.equal(winner.calls.quit,0);assert.equal(winner.windows[0].destroyed,false);assert.equal(winner.calls.shutdown,1);
  winner.management.busy=false;winner.windows[0].close();winner.trays[0].menu[2].click();await tick();await tick();
  assert.equal(winner.calls.shutdown,2);assert.equal(winner.calls.quit,1);assert.equal(winner.calls.exit.length,0);
  results.push({id:'MAIN-BUSY-CLOSE-RETAINS-WINDOW-SERIAL-EXIT',pass:true});
  const loser=harness({primary:false});loser.ready.resolve();await tick();
  assert.equal(loser.calls.start,0);assert.equal(loser.calls.windows,0);assert.equal(loser.calls.quit,1);
  results.push({id:'MAIN-SINGLETON-LOSER-NEVER-STARTS-CORE',pass:true});
  const broken=harness({failure:true});broken.ready.resolve();await tick();broken.started.resolve();await tick();await tick();
  assert.equal(broken.calls.trays,1);assert(broken.calls.diagnostics.length>0);assert.equal(broken.calls.exit.length,0);
  const count=broken.calls.diagnostics.length;
  broken.app.emit('second-instance',{},[],'.',{installation_id:'a'.repeat(64),intent:'show-ui'});await tick();
  assert(broken.calls.diagnostics.length>count);assert.equal(broken.calls.start,1);assert.equal(broken.calls.shutdown,0);
  results.push({id:'MAIN-BROKEN-STARTUP-KEEPS-DIAGNOSTIC-ENTRY',pass:true});
}
main().then(()=>{fs.writeFileSync(output,JSON.stringify({stage:'VM_MOCK_NOT_NATIVE_NOT_SOURCE_ACCEPTANCE',source_root:sourceRoot,results,native_runs:0},null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(results));})
  .catch(error=>{fs.writeFileSync(output,JSON.stringify({stage:'VM_MOCK_FAILED',source_root:sourceRoot,results,error:error.stack,native_runs:0},null,2)+'\n',{flag:'wx'});console.error(error);process.exitCode=1;});
