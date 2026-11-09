import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import test from 'node:test';
const SRC='C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-read-lane-20261012';
const OUT='C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-read-lane-review-20261012';
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
  return {...h,hits,machine,sessionState,prepare:prepareScope};
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
      record('non-read '+method,{scope_accepted:result.ok,write_sequence:ipc.callV2.writeSequences.get(h.sessionState)||0,pending_barrier:!!h.sessionState.pendingOperation,hits:h.hits.map(x=>x.method),source_classifies_as_presentation:true});
      effectGate.release();await operation;
      assert.equal(result.ok,false,'non-read operation did not invalidate authority scope');
    }finally{statusGate.release();effectGate.release();await h.close();}
  });
}
