'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const {EventEmitter}=require('node:events');
const source=fs.readFileSync(path.join(__dirname,'snapshot/driver/lifecycle.mjs'),'utf8');
function between(start,end){const a=source.indexOf(start),b=source.indexOf(end,a);assert(a>=0&&b>a);return source.slice(a,b);}
const functions=between('function ownDevToolsEndpoint(stderr) {','async function safeClose(label, instance) {');
const catchStart=source.lastIndexOf('} catch (error) {')+'} catch (error) {'.length;
const catchEnd=source.lastIndexOf('} finally {');assert(catchStart>0&&catchEnd>catchStart);
const catchBody=source.slice(catchStart,catchEnd);
const results=[];
function harness(mode){
 const saved=new Map(),events=[],calls={spawn:0,unref:0,connect:0,disconnect:0,kills:0,descriptors:[],logs:[]},made=[];
 let nextFd=10;
 const mockFs={openSync:(p,flag)=>{assert.equal(flag,'wx');calls.descriptors.push(p);return ++nextFd;},closeSync(){},
  readFileSync:()=>mode.startsWith('native-')?'':'DevTools listening on ws://127.0.0.1:54321/devtools/browser/abc-123\n',
  appendFileSync:(p,b)=>events.push({path:p,body:JSON.parse(b)}),existsSync:()=>false};
 const mockSpawn=(exe,args,opts)=>{calls.spawn++;assert.equal(opts.shell,false);assert.equal(opts.stdio[0],'ignore');assert.equal(typeof opts.stdio[1],'number');
  const c=new EventEmitter();c.pid=42001;c.unref=()=>calls.unref++;c.kill=()=>{calls.kills++;throw Error('KILL_FORBIDDEN');};made.push(c);return c;};
 const browser={connected:true,contexts:()=>[],isConnected(){return this.connected;},async close(){calls.disconnect++;if(mode==='disconnect-error')throw Error('MOCK_DISCONNECT_FAILURE');this.connected=false;}};
 const sandbox={fs:mockFs,path,assert,URL,Date,console:{error:s=>calls.logs.push(s)},process:{exitCode:0},
  spawn:mockSpawn,chromium:{async connectOverCDP(){calls.connect++;if(mode==='cdp-error')throw Error('MOCK_CDP_CONNECT_ERROR');return browser;}},
  async waitFor(predicate,label){if(mode==='native-exit')made[0].emit('exit',17,null);const ready=await predicate();if(!ready)throw Error('OBSERVATION_TIMEOUT:'+label);},
  save:(n,v)=>{assert(!saved.has(n));saved.set(n,JSON.parse(JSON.stringify(v)));},witness:()=>{throw Error('UNEXPECTED_WITNESS_READ');},
  check:()=>{throw Error('UNEXPECTED_SUCCESS_PATH');},read:()=>{throw Error('UNEXPECTED_READ');}};
 const declaration="const out='C:/owned-review',bundle='C:/bundle',appRoot='C:/bundle/apps/desktop',electron='C:/bundle/electron.exe',env={},children=[],assertions=[],witnessPath='C:/owned-review/witness.json';let application=null,firstWitness=null,secondWitness=null,thirdWitness=null,providerConnections=0;\n";
 vm.runInNewContext(declaration+functions+'\nasync function failureHandler(error){'+catchBody+'}\nglobalThis.exports={spawnNative,launch,failureHandler,children};',sandbox,{filename:'captured-v2-functions.js'});
 return{...sandbox.exports,saved,events,calls,made,sandbox};
}
(async()=>{
 const observed=harness('observe');const entry=observed.spawnNative('first');
 assert.equal(entry.pid,42001);assert.equal(observed.calls.spawn,1);assert.equal(observed.calls.unref,1);assert(observed.saved.has('first.spawn.json'));
 assert.equal(observed.made[0].listenerCount('error'),1);assert.equal(observed.made[0].listenerCount('exit'),1);
 observed.made[0].emit('exit',0,null);assert.equal(entry.terminal,true);assert.equal(entry.exit,0);assert.equal(observed.events[0].body.event,'exit');
 results.push({id:'SPAWN_IMMEDIATE_PID_RAW_HANDLERS_UNREF_AND_EXIT_RECORD',pass:true});
 for(const mode of ['native-timeout','native-exit','cdp-error','page-timeout','disconnect-error']){
  const h=harness(mode);let error;try{await h.launch('first');}catch(e){error=e;}assert(error,'expected controlled failure');
  await h.failureHandler(error);
  assert.equal(h.calls.spawn,1);assert.equal(h.calls.kills,0);assert.equal(h.sandbox.process.exitCode,1);
  assert(h.saved.has('UNRESOLVED.json'));const aggregate=h.saved.get('UNRESOLVED.json');assert.equal(aggregate.restart_authorized,false);assert.equal(aggregate.forced_termination,false);
  assert.equal(aggregate.children.length,1);assert.equal(aggregate.children[0].pid,42001);
  if(mode!=='native-exit'){assert(h.saved.has('first.unresolved.json'));assert.equal(h.saved.get('first.unresolved.json').terminal,false);}
  else{assert.equal(aggregate.children[0].terminal,true);assert.equal(aggregate.children[0].exit,17);}
  if(mode==='page-timeout'||mode==='disconnect-error')assert.equal(h.calls.disconnect,1);else assert.equal(h.calls.disconnect,0);
  results.push({id:mode,pass:true,spawn:h.calls.spawn,product_kill_calls:h.calls.kills,cdp_disconnect_calls:h.calls.disconnect,error:error.message});
 }
 const output={status:'PURE_VM_FAILURE_PATHS_PASS',cases:results,real_child_processes:0,product_core_electron_runs:0,limitation:'Extracted frozen controller functions and catch body; mocked filesystem/process/CDP. Real disconnect behavior separately traced in bound framework source.'};
 fs.writeFileSync(path.join(__dirname,'MOCK-RESULT.json'),JSON.stringify(output,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(output));
})().catch(e=>{console.error(e);process.exitCode=1;});
