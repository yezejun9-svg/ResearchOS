import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import test from 'node:test';
const SRC='C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-read-lane-20261012';
const OUT='C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-read-lane-v2-review-20261012';
const require=createRequire(import.meta.url);
const ipc=require(path.join(SRC,'apps/desktop/main/lib/ipc.js'));
const {createDesktopManagement}=require(path.join(SRC,'apps/desktop/main/lib/desktop-management.js'));
const {harness,pair,snapshot}=await import(pathToFileURL(path.join(SRC,'tests/ui/desktop/http-wire-boundary.test.mjs')));
const main=fs.readFileSync(path.join(SRC,'apps/desktop/main/main.js'),'utf8');
const cut=(start,end)=>{const a=main.indexOf(start),b=main.indexOf(end,a);assert(a>=0&&b>a);return main.slice(a,b);};
const proxy=cut('const sessionState = new Proxy(selectedState,','// Raw startup diagnostics');
const prepare=cut('async function prepareQualificationScope() {','\nconst codingDirectories');
fs.writeFileSync(path.join(OUT,'actual-main-extractions.json'),JSON.stringify({main_sha256:crypto.createHash('sha256').update(main).digest('hex'),proxy_sha256:crypto.createHash('sha256').update(proxy).digest('hex'),prepare_sha256:crypto.createHash('sha256').update(prepare).digest('hex'),proxy,prepare},null,2));
const deferred=()=>{let release;return {promise:new Promise(r=>release=r),release:(...v)=>release(...v)};};
const summarize=p=>p.then(v=>({ok:true,value:v}),e=>({ok:false,reason:e.code||e.message}));
const cases=[];
async function fixture(options={}) {
  const s=snapshot();
  const {sessionState,qualificationContext}=Function('selectedState',proxy+'\nreturn {sessionState,qualificationContext};')({projectId:s.project_id,sessionId:s.session_id,expectedRevision:s.revision,writerEpoch:s.writer.epoch,writerClientId:s.writer.client_id,writerExpiresAt:s.writer.expires_at,selectionGeneration:0,authorityGeneration:0});
  const hits=[];
  const h=await harness(async raw=>{
    const env=JSON.parse(raw);hits.push(env);
    const value=await options.respond?.(env,hits);
    if(value)return value;
    const response=pair(env.method).response;response.command_id=env.command_id;
    options.mutate?.(env,response);
    return {body:response};
  },{state:sessionState});
  h.deps.commandIdFor=method=>'review-'+method+'-'+crypto.randomUUID();
  if(options.credentialFor)h.deps.credentialFor=options.credentialFor;
  const identity=pid=>({PID:pid,CreatedNS:String(pid)+'000000000',ImageSHA256:'a'.repeat(64)});
  const machine=createDesktopManagement({fsImpl:h.deps.fsImpl,discoveryFile:h.deps.discoveryFile,dataRoot:'fixture-data-root',context:qualificationContext,observeProcess:identity});
  machine.state='READY';machine.child={pid:1234};machine.hostId='host-aaaaaaaaaaaa';machine.identity=identity(1234);machine.parentIdentity=identity(process.pid);
  const v2Deps={...h.deps,contextVerified:true};
  const prepareScope=Function('v2Deps','sessionState','desktopManagement','qualificationContext','ipc','crypto',prepare+'\nreturn prepareQualificationScope;')(v2Deps,sessionState,machine,qualificationContext,ipc,crypto);
  return {...h,hits,machine,sessionState,v2Deps,prepare:prepareScope};
}
function record(name,details){cases.push({name,...details});fs.writeFileSync(path.join(OUT,'supplemental-cases.json'),JSON.stringify(cases,null,2));}
for(const [name,method,credentialIndex] of [['R04 authority credential waits while display host.status finishes','host.status',2],['R05 authority credential waits while display session.get finishes','session.get',1]]) {
  test(name,{timeout:45000},async()=>{
    const arrived=deferred(),gate=deferred();let n=0;
    const h=await fixture({credentialFor:async()=>{if(++n===credentialIndex){arrived.release();await gate.promise;}return 'public-fixture-only';}});
    try {
      const scope=summarize(h.prepare());await arrived.promise;
      const shown=await ipc.callV2(h.deps,method,{});
      assert.equal(shown.completed,true);
      record(name,{display_finished_before_authority_dispatch:true,hits_before_release:h.hits.map(x=>x.method)});
      gate.release();const result=await scope;assert.equal(result.ok,true,JSON.stringify(result));
      assert.equal(result.value.scope.modelRef,'fixture_config_1');
    } finally {gate.release();await h.close();}
  });
}
test('R06 real transport serializes queued successful replies and later ticket rejects older read',{timeout:45000},async()=>{
  const entered=deferred(),gate=deferred(),queued=deferred();let calls=0;
  const h=await fixture({respond:async env=>{if(env.method==='session.get'&&++calls===1){entered.release();await gate.promise;}}});
  try {
    const older=ipc.callV2(h.deps,'session.get',{});await entered.promise;
    const transport=h.deps.v2Transport;h.deps.v2Transport=(...args)=>{queued.release();return transport(...args);};
    const newer=ipc.callV2(h.deps,'session.get',{});await queued.promise;
    assert.equal(h.hits.length,1);assert.equal(calls,1);
    gate.release();const [a,b]=await Promise.all([older,newer]);
    assert.equal(a.reason,'STALE_RESPONSE');assert.equal(b.completed,true);
    assert.equal(h.hits.length,2);
    record('R06',{single_transport:true,http_reverse_success_order_reachable:false,first_reply:a.reason,second_completed:b.completed,request_command_ids:h.hits.map(x=>x.command_id)});
  }finally{gate.release();await h.close();}
});
for(const method of ['session.send','session.control']) {
  test('R09/R19 '+method+' ACK reservation during Main authority credential wait',{timeout:45000},async()=>{
    const entered=deferred(),gate=deferred();let credentials=0;
    const h=await fixture({credentialFor:async()=>{if(++credentials===2){entered.release();await gate.promise;}return 'public-fixture-only';},respond:async env=>{if(env.method===method){const response=pair(method,'ACKNOWLEDGED').response;response.command_id=env.command_id;return {body:response};}}});
    try {
      const scope=summarize(h.prepare());await entered.promise;
      const ack=await ipc.callV2(h.deps,method,pair(method).request.payload);assert.equal(ack.protocol_status,'ACKNOWLEDGED');
      const operation=h.sessionState.pendingOperation;assert(operation);
      gate.release();const result=await scope;assert.equal(result.ok,false);assert.equal(result.reason,'HOST_OR_CONTEXT_CHANGED');
      assert.equal(h.sessionState.pendingOperation,operation);
      record(method+' ACK overlap',{scope:result,pending_command_id:operation.commandId,hits:h.hits.map(x=>x.method)});
    }finally{gate.release();await h.close();}
  });
}
test('R10 events status GET cannot adopt or clear original ACK attach; replay bytes retained',{timeout:45000},async()=>{
  let attaches=0;
  const h=await fixture({respond:async env=>{
    const response=pair(env.method,env.method==='session.attach'&&++attaches===1?'ACKNOWLEDGED':'COMPLETED').response;
    response.command_id=env.command_id;
    if(env.method==='session.attach'&&response.status==='COMPLETED')response.result.write_owner_acquired=true;
    return {body:response};
  }});
  try {
    const payload={...pair('session.attach').request.payload,request_write_owner:true};
    const ack=await ipc.callV2(h.deps,'session.attach',payload);assert.equal(ack.protocol_status,'ACKNOWLEDGED');
    const pending=h.sessionState.pendingOperation;
    for(const method of ['session.events','host.status','session.get']) {
      const read=await ipc.callV2(h.deps,method,pair(method).request.payload);assert.equal(read.completed,true,JSON.stringify(read));assert.equal(h.sessionState.pendingOperation,pending);
    }
    const blocked=await ipc.callV2(h.deps,'session.send',pair('session.send').request.payload);assert.equal(blocked.reason,'COMMAND_PENDING');
    const done=await ipc.callV2(h.deps,'session.attach',payload);assert.equal(done.completed,true,JSON.stringify(done));
    const requests=h.observations.http.filter(x=>JSON.parse(x.raw).method==='session.attach');assert.equal(requests.length,2);assert(requests[0].raw.equals(requests[1].raw));
    assert.equal(h.sessionState.pendingOperation,undefined);
    record('R10',{pending_preserved_during:['session.events','host.status','session.get'],original_replay_bytes_equal:true});
  }finally{await h.close();}
});
for(const variant of ['REJECTED','MALFORMED']) {
  test('R16 actual Main declines '+variant+' host.status',{timeout:45000},async()=>{
    const h=await fixture({respond:async env=>{
      if(env.method!=='host.status')return;
      const response=pair('host.status',variant==='REJECTED'?'REJECTED':'COMPLETED').response;response.command_id=env.command_id;
      if(variant==='MALFORMED')response.result='invalid';
      return {body:response};
    }});
    try {const result=await summarize(h.prepare());assert.equal(result.ok,false);assert.equal(result.reason,'HOST_OR_CONTEXT_CHANGED');record('R16 '+variant,{result,children:h.observations.children.length});}
    finally {await h.close();}
  });
}
test('R19 stale-CAS CANCEL rejection still invalidates pending Main authority scope',{timeout:45000},async()=>{
  const entered=deferred(),gate=deferred();let credentials=0;
  const h=await fixture({credentialFor:async()=>{if(++credentials===2){entered.release();await gate.promise;}return 'public-fixture-only';},respond:async env=>{if(env.method==='session.control'){const response=pair('session.control','REJECTED').response;response.command_id=env.command_id;return {body:response};}}});
  try {
    const scope=summarize(h.prepare());await entered.promise;
    const rejected=await ipc.callV2(h.deps,'session.control',pair('session.control').request.payload);assert.equal(rejected.protocol_status,'REJECTED');
    gate.release();const result=await scope;assert.equal(result.ok,false);assert.equal(result.reason,'HOST_OR_CONTEXT_CHANGED');
    record('R19 REJECTED',{scope:result,rejected,write_sequence:ipc.callV2.writeSequences.get(h.sessionState)});
  }finally{gate.release();await h.close();}
});
for(const method of ['provider.probe','workspace.register']) {
  test('non-read '+method+' must fence Main authority scope while reserved',{timeout:45000},async()=>{
    const arrived=deferred(),statusGate=deferred(),effectGate=deferred(),queued=deferred();
    const h=await fixture({respond:async env=>{
      if(env.method==='host.status'){arrived.release();await statusGate.promise;}
      if(env.method===method)await effectGate.promise;
    }});
    try {
      const scope=summarize(h.prepare());await arrived.promise;
      const transport=h.deps.v2Transport;h.deps.v2Transport=(...args)=>{queued.release();return transport(...args);};
      const operation=ipc.callV2(h.deps,method,pair(method).request.payload);await queued.promise;
      statusGate.release();const result=await scope;
      record('non-read '+method,{scope_accepted:result.ok,write_sequence:ipc.callV2.writeSequences.get(h.sessionState)||0,pending_barrier:!!h.sessionState.pendingOperation,hits:h.hits.map(x=>x.method),source_classifies_as_presentation:false});
      effectGate.release();await operation;
      assert.equal(result.ok,false,'non-read operation did not invalidate authority scope');
    }finally{statusGate.release();effectGate.release();await h.close();}
  });
}
// V2 independent cases: production functions with fixture health/native identities,
// actual serialized HTTP transport and the byte-bound validator. No product calls.
for (const credentialIndex of [1,2]) {
 test('V2 activity completes during authority credential wait '+credentialIndex,{timeout:45000},async()=>{
  const entered=deferred(),gate=deferred();let n=0;
  const h=await fixture({credentialFor:async()=>{if(++n===credentialIndex){entered.release();await gate.promise;}return 'public-fixture-only';}});
  try {
   const scope=summarize(h.prepare());await entered.promise;
   const activity=await ipc.callV2(h.deps,'provider.probe',pair('provider.probe').request.payload);assert.equal(activity.completed,true);
   assert.equal(ipc.callV2.lifetimes.get(h.sessionState).size,0);
   gate.release();const result=await scope;assert.equal(result.ok,false);assert.equal(result.reason,credentialIndex===1?'SESSION_CHANGED':'HOST_OR_CONTEXT_CHANGED');
   record('V2 credential wait '+credentialIndex,{scope:result,activity_completed_before_scope_resume:true,activity_generation:ipc.callV2.writeSequences.get(h.sessionState)});
  } finally {gate.release();await h.close();}
 });
}
test('V2 preexisting activity finishes during authority ensureCore but entry barrier remains',{timeout:45000},async()=>{
 const effectEntered=deferred(),effectGate=deferred(),healthEntered=deferred(),healthGate=deferred();
 const h=await fixture({respond:async env=>{if(env.method==='provider.probe'){effectEntered.release();await effectGate.promise;}}});
 try {
  const activity=ipc.callV2(h.deps,'provider.probe',pair('provider.probe').request.payload);await effectEntered.promise;
  const originalGet=h.deps.httpImpl.get;
  h.deps.httpImpl.get=(...args)=>{const req=new (require('node:events').EventEmitter)();healthEntered.release();healthGate.promise.then(()=>originalGet(...args));return req;};
  const scope=summarize(h.prepare());await healthEntered.promise;effectGate.release();assert.equal((await activity).completed,true);
  assert.equal(ipc.callV2.lifetimes.get(h.sessionState).size,0);healthGate.release();const result=await scope;
  assert.equal(result.reason,'SESSION_CHANGED');assert.deepEqual(h.hits.map(x=>x.method),['provider.probe']);
  record('V2 entry barrier',{scope:result,activity_completed_while_health_pending:true,authority_http_sent:false});
 } finally {effectGate.release();healthGate.release();await h.close();}
});
for(const first of ['ACKNOWLEDGED','MALFORMED']) {
 test('V2 '+first+' activity survives display credential loss and NOT_SENT replay',{timeout:45000},async()=>{
  let count=0;
  const h=await fixture({respond:async env=>{
   if(env.method==='provider.probe'&&++count===1){if(first==='MALFORMED')return {raw:Buffer.from('{invalid')};const response=pair('provider.probe','ACKNOWLEDGED').response;response.command_id=env.command_id;return {body:response};}
  }});
  try {
   const payload=pair('provider.probe').request.payload;
   const initial=await ipc.callV2(h.deps,'provider.probe',payload);assert.equal(initial.completed??false,false);
   const lifetimes=ipc.callV2.lifetimes.get(h.sessionState);assert.equal(lifetimes.size,1);const operation=[...lifetimes.values()][0];assert.equal(operation.activity,true);assert.equal(operation.write,false);assert.equal(operation.request.headers.Authorization,undefined);
   h.deps.credentialFor=async()=>{throw Error('fixture renewal failed');};
   const lost=await ipc.callV2(h.deps,'provider.probe',payload);assert.equal(lost.reason,'CREDENTIAL_UNAVAILABLE');assert.notEqual(lost.dispatch_state,'NOT_SENT');assert.equal([...lifetimes.values()][0],operation);
   delete h.deps.credentialFor;
   const original=h.deps.v2Transport;h.deps.v2Transport=async()=>({ok:false,validated:false,reason:'FIXTURE_PREFLIGHT_UNAVAILABLE',dispatch_state:'NOT_SENT'});
   const refused=await ipc.callV2(h.deps,'provider.probe',payload);assert.notEqual(refused.dispatch_state,'NOT_SENT');assert.equal([...lifetimes.values()][0],operation);h.deps.v2Transport=original;
   for(const method of ['session.get','host.status','session.events']){assert.equal((await ipc.callV2(h.deps,method,pair(method).request.payload)).completed,true);assert.equal([...lifetimes.values()][0],operation);}
   const scope=await summarize(h.prepare());assert.equal(scope.reason,'SESSION_CHANGED');
   const changed=await ipc.callV2(h.deps,'provider.probe',{...payload,model_id:'different-fixture-model'});assert.equal(changed.reason,'COMMAND_PENDING');
   const replay=await ipc.callV2(h.deps,'provider.probe',payload);assert.equal(replay.completed,true);assert.equal(lifetimes.size,0);
   const raw=h.observations.http.filter(x=>JSON.parse(x.raw).method==='provider.probe');assert.equal(raw.length,2);assert(raw[0].raw.equals(raw[1].raw));
   record('V2 retained '+first,{initial,credential_loss:lost,preflight_refusal:refused,scope,original_command_id:operation.commandId,replay_raw_equal:true});
  } finally {await h.close();}
 });
}
test('V2 nonwrite original replay refuses changed native host then succeeds on original',{timeout:45000},async()=>{
 let probes=0;const h=await fixture({respond:async env=>{if(env.method==='provider.probe'&&++probes===1){const response=pair('provider.probe','ACKNOWLEDGED').response;response.command_id=env.command_id;return {body:response};}}});
 try {
  const payload=pair('provider.probe').request.payload;assert.equal((await ipc.callV2(h.deps,'provider.probe',payload)).protocol_status,'ACKNOWLEDGED');
  const original=h.deps.fsImpl.readFileSync;h.deps.fsImpl.readFileSync=()=>JSON.stringify({url:h.url,pid:1234,data_dir:'fixture-other-data-root',host_instance_id:'host-bbbbbbbbbbbb'});
  const result=await ipc.callV2(h.deps,'provider.probe',payload);assert.equal(result.reason,'HOST_CHANGED_PENDING');assert.equal(h.hits.length,1);
  h.deps.fsImpl.readFileSync=original;assert.equal((await ipc.callV2(h.deps,'provider.probe',payload)).completed,true);
  assert(h.observations.http[0].raw.equals(h.observations.http[1].raw));record('V2 replay host origin',{result,original_replay_equal:true});
 } finally {await h.close();}
});
test('V2 non-CAS activity does not require writer but existing send still does',{timeout:45000},async()=>{
 const h=await fixture();try {
  h.sessionState.writerClientId='foreign-fixture-writer';h.sessionState.writerExpiresAt='2000-01-01T00:00:00Z';
  const probe=await ipc.callV2(h.deps,'provider.probe',pair('provider.probe').request.payload);assert.equal(probe.completed,true);
  const send=await ipc.callV2(h.deps,'session.send',pair('session.send').request.payload);assert.equal(send.reason,'WRITE_OWNER_REQUIRED');assert.equal(send.dispatch_state,'NOT_SENT');assert.equal(h.hits.length,1);
  record('V2 CAS separation',{probe_completed:true,send});
 }finally{await h.close();}
});
for(const field of ['projectId','writerClientId']) {
 test('V2 actual Proxy '+field+' ABA during authority credential wait',{timeout:45000},async()=>{
  const entered=deferred(),gate=deferred();let n=0;
  const h=await fixture({credentialFor:async()=>{if(++n===2){entered.release();await gate.promise;}return 'public-fixture-only';}});
  try {const scope=summarize(h.prepare());await entered.promise;const original=h.sessionState[field];h.sessionState[field]='other-fixture-value';h.sessionState[field]=original;gate.release();const result=await scope;assert.equal(result.reason,'HOST_OR_CONTEXT_CHANGED');record('V2 Proxy ABA '+field,{result,selection_generation:h.sessionState.selectionGeneration,authority_generation:h.sessionState.authorityGeneration});}
  finally{gate.release();await h.close();}
 });
}
