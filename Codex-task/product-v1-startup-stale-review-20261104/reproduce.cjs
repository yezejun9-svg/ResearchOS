'use strict';
// Pure dependency-injected IPC reproduction. Never import Electron/main boot,
// open a socket/pipe/DB, spawn Core, or use a real credential.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const root='D:/作品集/ResearchOS/research-os';
const lib=path.join(root,'apps/desktop/main/lib');
const ipc=require(path.join(lib,'ipc.js')),host=require(path.join(lib,'host.js')),native=require(path.join(lib,'native.js'));
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const main=fs.readFileSync(path.join(root,'apps/desktop/main/main.js'),'utf8');
const prefix=main.indexOf('const selectedState = {'),end=main.indexOf('const qualificationContext = ',prefix);
assert(prefix>=0&&end>prefix);
const freshState=()=>vm.runInNewContext(main.slice(prefix,end)+'\nsessionState;',{process:{env:{}}});
const discovery={url:'http://fixture.invalid:1',pid:1,data_dir:'C:/synthetic-unopened-root',host_instance_id:'host-0123456789ab'};
host.ensureCore=async()=>({discovery,health:'UP'});host.readDiscovery=()=>({ok:true,discovery});native.hostInstanceId=()=>discovery.host_instance_id;
const fresh=()=>{
 const state=freshState(),pending=[];let index=0;
 const deps={sessionState:state,fsImpl:{},discoveryFile:'NEVER_READ',clientId:'desktop-shell',credentialFor:async()=> 'SYNTHETIC_NOT_A_CREDENTIAL',commandIdFor:()=> 'fixture-'+(++index),v2Transport:async()=>new Promise(resolve=>pending.push(resolve))};
 const reply={validated:true,ok:true,body:{status:'COMPLETED',result:{projects:[],workspaces:[],model_configurations:[]},revision:null}};
 return {state,pending,deps,reply};
};
const tick=()=>new Promise(resolve=>setImmediate(resolve));
async function waitRequests(f,n){for(let i=0;i<50&&f.pending.length<n;i++)await tick();assert.equal(f.pending.length,n,'fixture reached held transport');}
(async()=>{
 const rows=[];
 {const f=fresh();const p=ipc.callV2(f.deps,'host.status',{});await waitRequests(f,1);f.pending[0](f.reply);const r=await p;assert(r.completed);rows.push({name:'single-fresh-start-status',result:r,selectionGeneration:f.state.selectionGeneration,authorityGeneration:f.state.authorityGeneration});}
 for(const order of [[0,1],[1,0]]){
  const f=fresh();const ps=[ipc.callV2(f.deps,'host.status',{}),ipc.callV2(f.deps,'host.status',{})];await waitRequests(f,2);
  for(const i of order){f.pending[i](f.reply);await tick();}
  const rs=await Promise.all(ps);assert.equal(rs[0].reason,'STALE_RESPONSE');assert.equal(rs[1].completed,true);
  assert.equal(f.state.selectionGeneration,0);assert.equal(f.state.authorityGeneration,0);
  rows.push({name:'two-independent-startup-status-readers',completion_order:order,results:rs,selectionGeneration:0,authorityGeneration:0,smoke_probe_present:false});
 }
 {const f=fresh();const p=ipc.callV2(f.deps,'host.status',{});await waitRequests(f,1);f.state.projectId='changed-project';f.pending[0](f.reply);const r=await p;assert.equal(r.reason,'STALE_RESPONSE');rows.push({name:'real-selection-change-must-remain-stale',result:r});}
 {const f=fresh();const p=ipc.callV2(f.deps,'host.status',{});await waitRequests(f,1);f.state.writerEpoch=1;f.pending[0](f.reply);const r=await p;assert.equal(r.reason,'STALE_RESPONSE');rows.push({name:'real-authority-change-must-remain-stale',result:r});}
 console.log(JSON.stringify({schema:'researchos.startup-stale-independent-pure-reproduction.v1',status:'COUNTEREXAMPLE_REPRODUCED_NO_SMOKE_REQUIRED',asserted_cases:rows.length,rows,source_sha256:{'apps/desktop/main/main.js':sha(path.join(root,'apps/desktop/main/main.js')),'apps/desktop/main/lib/ipc.js':sha(path.join(lib,'ipc.js'))},classification:'ACTUAL_IPC_FUNCTIONS_AND_EXTRACTED_MAIN_PROXY_WITH_INJECTED_FAKE_DEPENDENCIES',electron_imports:0,product_processes:0,sockets:0,native_calls:0,db_access:0,model_calls:0,formal_increment:0},null,2));
})().catch(error=>{console.error(error.stack);process.exitCode=1;});
