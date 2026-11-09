'use strict';
// Pure main-process fixtures. Every network/process boundary is poisoned or
// replaced with a recorder. No Electron, Native pipe or HTTP server is started.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const crypto=require('node:crypto');
const root=path.resolve(__dirname,'../..');
const lib=path.join(root,'apps/desktop/main/lib');
for(const [module,key] of [['node:net','connect'],['node:http','request'],['node:child_process','spawn']])
  require(module)[key]=()=>{throw Error('REAL_IO_FORBIDDEN');};
const native=require(path.join(lib,'native.js'));
const host=require(path.join(lib,'host.js'));
const ipc=require(path.join(lib,'ipc.js'));
const ref='natt-'+'a'.repeat(64);
const discovery=()=>({host_instance_id:'host-012345abcdef',url:'http://127.0.0.1:45678',data_dir:'fixture-root',pid:42});
const payload=()=>({workspace_ref:'ws-fixture',model_config_ref:null,title:'Fixture'});
const envelope=()=>({protocol_version:'researchos-client/2',command_id:'cmd-fixture',client_id:'fixture-desktop',
  project_id:'proj-fixture',session_id:null,expected_revision:null,writer_epoch:null,method:'session.create',payload:payload()});
const proof=()=>({kind:'NATIVE_CLIENT_ATTEST_RESULT',payload:{schema_version:1,attestation_ref:ref,
  client_instance_ref:'nci-'+'b'.repeat(32),host_instance_id:'host-012345abcdef',expires_at:'2030-01-01T00:00:00Z'}});
let checks=0;
function transportFixture({mutate,reply}={}){
  const posts=[],phases=[];
  const context={require,module:{exports:{}},exports:{},Buffer,URL,TextDecoder,structuredClone,console,setTimeout,clearTimeout,
    __dirname:lib,__fixture:{
      resource:()=>({descriptorHash:'fixture-same'}),
      child:async(_resource,packet)=>{phases.push(packet.phase);return {outcome:'VALID',value:reply||{status:'ACKNOWLEDGED',result:null,revision:null}};},
      post:async(url,raw,headers)=>{posts.push({url,raw:Buffer.from(raw),headers:{...headers}});return {raw:Buffer.from('{}'),status:200};},
      values:{stringify:JSON.stringify,reify:v=>v}}};
  vm.runInNewContext(fs.readFileSync(path.join(lib,'http-wire.js'),'utf8')+
    '\nresource=__fixture.resource;child=__fixture.child;post=__fixture.post;valuesPromise=Promise.resolve(__fixture.values);',context);
  return {transport:context.module.exports.createTransport({appRoot:'fixture-only'}),posts,phases};
}
async function testNative(){
  const d=discovery(); const req=envelope();const raw=Buffer.from(JSON.stringify(req));const calls=[];
  const attest=native.createClientAttestor({fsImpl:{readFileSync(){throw Error('TOKEN_READ_FORBIDDEN');}},now:()=>Date.parse('2026-11-04T00:00:00Z'),
    dial:async(pipe,frame)=>{calls.push({pipe,frame});return JSON.stringify(proof());}});
  assert.equal(await attest(d,raw,{Authorization:'Bearer fixture-bearer'}),ref);
  assert.equal(calls.length,1);assert.equal(calls[0].frame.kind,'NATIVE_CLIENT_ATTEST_REQUEST');
  assert.equal(calls[0].frame.payload.credential_value,'fixture-bearer');
  assert.equal(calls[0].frame.payload.request_raw_sha256,'sha256:'+crypto.createHash('sha256').update(raw).digest('hex'));
  assert.deepEqual(Object.keys(calls[0].frame.payload).sort(),['command_id','credential_value','expected_revision','method','project_id','request_raw_sha256','schema_version','session_id','writer_epoch'].sort());checks++;
  for(const mode of ['duplicate','trailing','extra','missing','wronghost','expired','unsupported','object','discovery']){
    const bound=discovery();
    const invalid=native.createClientAttestor({now:()=>Date.parse('2026-11-04T00:00:00Z'),dial:async()=>{
      const value=proof();
      if(mode==='unsupported')throw Error('fixture-bearer must not leak');
      if(mode==='extra')value.payload.extra=true;
      if(mode==='missing')delete value.payload.client_instance_ref;
      if(mode==='wronghost')value.payload.host_instance_id='host-ffffffffffff';
      if(mode==='expired')value.payload.expires_at='2020-01-01T00:00:00Z';
      if(mode==='object')return value;
      if(mode==='discovery')bound.pid++;
      const text=JSON.stringify(value);
      return mode==='duplicate'?text.replace('"schema_version":1','"schema_version":1,"schema_version":1'):mode==='trailing'?text+'{}':text;
    }});
    await assert.rejects(invalid(bound,raw,{Authorization:'Bearer fixture-bearer'}),{message:'NATIVE_CREATE_ATTESTATION_UNAVAILABLE'});checks++;
  }
}
async function testWire(){
  const f=transportFixture();const req=envelope();let commitment;
  const result=await f.transport('POST',discovery().url+'/v2/command',req,{Authorization:'Bearer fixture-final'},async(raw,headers)=>{
    assert.equal(f.posts.length,0);assert.deepEqual(f.phases,['REQUEST']);
    commitment=Buffer.from(raw);assert.equal(headers.Authorization,'Bearer fixture-final');return ref;});
  assert.equal(result.ok,true);assert.equal(f.posts.length,1);assert.ok(f.posts[0].raw.equals(commitment));
  assert.equal(f.posts[0].headers['X-ResearchOS-Native-Attestation'],ref);checks++;
  for(const mode of ['sync','async','unsupported']){
    const g=transportFixture();const changed=envelope();
    const result=await g.transport('POST',discovery().url+'/v2/command',changed,{Authorization:'Bearer fixture-final'},async()=>{
      if(mode==='async')await Promise.resolve();
      if(mode==='unsupported')throw Error('NATIVE_CREATE_ATTESTATION_UNAVAILABLE');
      changed.payload.title='changed-after-native';return ref;});
    assert.equal(result.dispatch_state,'NOT_SENT');assert.equal(g.posts.length,0);checks++;
  }
  const legacy=transportFixture();await legacy.transport('POST',discovery().url+'/v2/command',envelope(),{Authorization:'Bearer old'});
  assert.equal(legacy.posts.length,1);assert.equal(legacy.posts[0].headers['X-ResearchOS-Native-Attestation'],undefined);checks++;
}
async function testIPC(){
  let current=discovery();
  host.ensureCore=async()=>({discovery:current});host.readDiscovery=()=>({ok:true,discovery:current});
  const state={projectId:'proj-fixture',sessionId:null,expectedRevision:null,writerEpoch:null};
  let token='fixture-first',calls=[],proofs=0;
  const deps={fsImpl:{},clientId:'fixture-desktop',discoveryFile:'fixture-discovery',sessionState:state,
    commandIdFor:()=> 'cmd-replay',credentialFor:async()=>token,nativeCreatePilot:true,
    nativeCreateAttest:async(d,raw,headers)=>{proofs++;calls.push({raw:Buffer.from(raw),auth:headers.Authorization});return ref;},
    v2Transport:async(verb,url,env,headers,pre)=>{
      assert.equal(typeof pre,'function');await pre(Buffer.from(JSON.stringify(env)),headers);
      return {ok:true,validated:true,body:{status:'ACKNOWLEDGED',result:null,revision:null}};}};
  const first=await ipc.callV2(deps,'session.create',payload());assert.equal(first.ok,true);
  token='fixture-second';const second=await ipc.callV2(deps,'session.create',payload());assert.equal(second.ok,true);
  assert.equal(proofs,2);assert.ok(calls[0].raw.equals(calls[1].raw));
  assert.deepEqual(calls.map(c=>c.auth),['Bearer fixture-first','Bearer fixture-second']);
  const publicState=JSON.stringify(state),publicReply=JSON.stringify([first,second]);
  assert.ok(!publicState.includes('fixture-first')&&!publicState.includes('fixture-second')&&!publicState.includes('natt-'));
  assert.ok(!publicReply.includes('natt-'));checks++;
  const f=transportFixture();let nativeCalls=0;
  const changed={...deps,sessionState:{...state,pendingOperation:undefined},commandIdFor:()=> 'cmd-change',
    nativeCreateAttest:async()=>{nativeCalls++;current={...current,pid:current.pid+1};return ref;},v2Transport:f.transport};
  // Use a clean command lifetime while retaining the same public project tuple.
  changed.sessionState={projectId:'proj-fixture',sessionId:null,expectedRevision:null,writerEpoch:null};
  const refused=await ipc.callV2(changed,'session.create',payload());
  assert.equal(refused.dispatch_state,'NOT_SENT');assert.equal(f.posts.length,0);assert.equal(nativeCalls,1);checks++;
  const off={...deps,nativeCreatePilot:false,sessionState:{projectId:'proj-fixture'},
    nativeCreateAttest:async()=>{throw Error('gate-off Native call');},v2Transport:async(...args)=>{
      assert.equal(args.length,4);return {ok:false,reason:'fixture-refusal',dispatch_state:'NOT_SENT'};}};
  assert.equal((await ipc.callV2(off,'session.create',payload())).dispatch_state,'NOT_SENT');checks++;
  const other={...off,nativeCreatePilot:true,sessionState:{projectId:'proj-fixture'}};
  await ipc.callV2(other,'session.list',{cursor:null,limit:10});checks++;
}
(async()=>{await testNative();await testWire();await testIPC();
  console.log(JSON.stringify({status:'PASS',checks,real_native:0,real_HTTP:0,real_child_processes:0,token_file_reads:0}));
})().catch(error=>{console.error(error.stack);process.exitCode=1;});
