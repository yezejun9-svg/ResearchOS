import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { EventEmitter } from 'node:events';
import assert from 'node:assert/strict';
import test from 'node:test';
const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');
const fixtures = JSON.parse(fs.readFileSync(path.join(ROOT,'tests/contracts/fixtures/client_protocol_v2_fixtures.json'),'utf8')).fixtures;
const get = name => structuredClone(fixtures.find(f=>f.name===name)?.value);
const ipc = require(path.join(ROOT,'apps/desktop/main/lib/ipc.js'));
const {createDesktopManagement} = require(path.join(ROOT,'apps/desktop/main/lib/desktop-management.js'));
const v2 = require(path.join(ROOT,'apps/desktop/main/lib/v2.js'));
const { createTransport } = require(path.join(ROOT,'apps/desktop/main/lib/http-wire.js'));
const exact = await import(pathToFileURL(path.join(ROOT,'apps/desktop/main/lib/wire-values.mjs')).href);
// Bind the exact Main implementation and its Proxy generation logic. These
// fixtures exercise real IPC calls through the packaged validator below.
const mainSource = fs.readFileSync(path.join(ROOT,'apps/desktop/main/main.js'),'utf8');
const qualificationBegin = mainSource.indexOf('async function prepareQualificationScope() {');
const qualificationEnd = mainSource.indexOf('\nconst codingDirectories',qualificationBegin);
const stateBegin = mainSource.indexOf('const sessionState = new Proxy(selectedState,');
const stateEnd = mainSource.indexOf('// Raw startup diagnostics',stateBegin);
assert(qualificationBegin >= 0 && qualificationEnd > qualificationBegin && stateBegin >= 0 && stateEnd > stateBegin);
const actualPrepareSource = mainSource.slice(qualificationBegin,qualificationEnd);
const actualStateSource = mainSource.slice(stateBegin,stateEnd);
const deferred = () => {let release;const promise=new Promise(resolve=>release=resolve);return {promise,release};};
function qualificationState() {
  const s=snapshot();
  const selectedState={projectId:s.project_id,sessionId:s.session_id,expectedRevision:s.revision,
    writerEpoch:s.writer.epoch,writerClientId:s.writer.client_id,writerExpiresAt:s.writer.expires_at,
    selectionGeneration:0,authorityGeneration:0};
  return Function('selectedState',actualStateSource+'\nreturn {sessionState,qualificationContext};')(selectedState);
}
async function qualificationFixture(intercept=async()=>{}, options={}) {
  const {sessionState,qualificationContext}=qualificationState();
  const hits=[];
  const h=await harness(async raw=>{
    const env=JSON.parse(raw);hits.push(env.method);
    await intercept(env,hits);
    const response=pair(env.method).response;response.command_id=env.command_id;
    options.modifyResponse?.(env,response);
    return {body:response};
  },{state:sessionState});
  const identity=pid=>({PID:pid,CreatedNS:String(pid)+'000000000',ImageSHA256:'a'.repeat(64)});
  const machine=createDesktopManagement({fsImpl:h.deps.fsImpl,discoveryFile:h.deps.discoveryFile,
    dataRoot:'fixture-data-root',context:qualificationContext,observeProcess:identity});
  machine.state='READY';machine.child={pid:1234};machine.hostId='host-aaaaaaaaaaaa';
  machine.identity=identity(1234);machine.parentIdentity=identity(process.pid);
  const v2Deps={...h.deps,contextVerified:true};
  const prepare=Function('v2Deps','sessionState','desktopManagement','qualificationContext','ipc','crypto',
    actualPrepareSource+'\nreturn prepareQualificationScope;')(
      v2Deps,sessionState,machine,qualificationContext,ipc,crypto);
  return {...h,hits,sessionState,qualificationContext,machine,prepare,sourceHash:crypto.createHash('sha256').update(actualPrepareSource).digest('hex')};
}
export function snapshot(overrides = {}) {
  const value=get('valid_snapshot');
  value.writer={client_id:'desktop-shell',epoch:2,expires_at:'2099-01-01T00:00:00Z'};
  return Object.assign(value,overrides);
}
export function pair(method,status='COMPLETED') {
  const key=method.replaceAll('.','_');
  const request=get('valid_request_'+key);
  let response=get('valid_response_'+key);
  request.client_id='desktop-shell';request.command_id='fixture-'+method;
  if(['host.status','host.configure','project.bootstrap','workspace.register','workspace.list','provider.models'].includes(method)) {
    request.project_id=null;request.session_id=null;request.expected_revision=null;request.writer_epoch=null;
  }
  if(method==='session.list') {request.session_id=null;request.expected_revision=null;request.writer_epoch=null;}
  if(method==='session.create') {request.session_id=null;request.expected_revision=null;request.writer_epoch=null;}
  if(method==='goal.start') {request.session_id=null;request.expected_revision=null;request.writer_epoch=null;}
  if(method==='session.attach') {request.payload.request_write_owner=false;request.writer_epoch=2;}
  response.command_id=request.command_id;response.method=method;response.session_id=request.session_id;
  if(method==='host.status'){response.result.client_id=request.client_id;response.revision=null;}
  if(method==='host.configure'){response.result.config_revision=request.payload.config_revision;response.revision=null;}
  if(method==='session.create') {response.result=snapshot();response.session_id=response.result.session_id;response.revision=response.result.revision;}
  if(method==='session.get'||method==='session.update') {response.result=snapshot();response.revision=response.result.revision;}
  if(method==='session.attach') {response.result={snapshot:snapshot(),write_owner_acquired:false};response.revision=response.result.snapshot.revision;}
  if(response.result?.snapshot) {response.result.snapshot.writer={client_id:'desktop-shell',epoch:2,expires_at:'2099-01-01T00:00:00Z'};response.revision=response.result.snapshot.revision;}
  if(method==='session.list')response.result.items=[snapshot()];
  if(status!=='COMPLETED') {
    const template=get(status==='ACKNOWLEDGED'?'valid_async_ack':'valid_rejected_response');
    response={...template,command_id:request.command_id,method,session_id:request.session_id};
  }
  return {request,response};
}
export async function harness(respond, options = {}) {
  const appRoot=options.appRoot || process.env.RESEARCHOS_DESKTOP_WIRE_ROOT;
  if(!appRoot)throw Error('actual built development resource root required');
  const observations={http:[],responses:[],children:[],cleanup:[],apiSetup:0,external:0,model:0};
  const server=http.createServer(async(req,res)=>{
    const parts=[];for await(const part of req)parts.push(part);
    const raw=Buffer.concat(parts);observations.http.push({raw,sha256:crypto.createHash('sha256').update(raw).digest('hex'),method:req.method,url:req.url});
    const reply=await respond(raw,observations.http.length);
    if(reply.hold)return;
    res.writeHead(reply.status ?? 200,{'Content-Type':'application/json'});res.end(reply.raw ?? Buffer.from(exact.stringify(reply.body)));
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const url='http://127.0.0.1:'+server.address().port;
  const transport=createTransport({appRoot,record:value=>{if(value.kind==='child')observations.children.push(value);else if(value.kind==='http')observations.responses.push(value);else if(value.kind==='child-cleanup')observations.cleanup.push(value);options.record?.(value);}});
  const deps={sessionState:options.state || {},clientId:'desktop-shell',credential:'public-fixture-only',commandIdFor:method=>'fixture-'+method,
    fsImpl:{readFileSync:()=>JSON.stringify({url,pid:1234,data_dir:'fixture-data-root',host_instance_id:'host-aaaaaaaaaaaa'})},discoveryFile:'public-fixture-discovery',
    httpImpl:{get(_url,_options,callback){const req=new EventEmitter();process.nextTick(()=>{const res=new EventEmitter();res.statusCode=200;callback(res);res.emit('end');});return req;}},
    v2Transport:transport};
  return {deps,transport,url,observations,close:async()=>{server.closeAllConnections();await new Promise(resolve=>server.close(resolve));saveEvidence(observations);}};
}
function saveEvidence(observations) {
  const directory=process.env.RESEARCHOS_DESKTOP_CASE_RECEIPT;
  if(!directory)return;
  fs.mkdirSync(directory,{recursive:true});
  const run=path.join(directory,crypto.randomUUID());fs.mkdirSync(run);
  const publicRows=observations.http.map((row,i)=>{fs.writeFileSync(path.join(run,'request-'+i+'.raw'),row.raw);return {...row,raw:undefined,bytes:row.raw.length};});
  const children=observations.children.map((row,i)=>{
    for(const field of ['input','stdout','stderr'])fs.writeFileSync(path.join(run,`child-${i}.${field}`),row[field]);
    return row.facts;
  });
  const responses=(observations.responses||[]).map((row,i)=>{fs.writeFileSync(path.join(run,'response-'+i+'.raw'),row.response);return {status:row.status,bytes:row.response.length,sha256:crypto.createHash('sha256').update(row.response).digest('hex')};});
  fs.writeFileSync(path.join(run,'observations.json'),JSON.stringify({http:publicRows,responses,children,cleanup:observations.cleanup||[],external:0,model:0},null,2));
}
export async function invoke(method,response,request,options={}) {
  const state={projectId:request.project_id,sessionId:request.session_id,expectedRevision:request.expected_revision,writerEpoch:request.writer_epoch,
    writerClientId:'desktop-shell',writerExpiresAt:'2099-01-01T00:00:00Z'};
  const h=await harness(async()=>response,{...options,state});
  try {
    const result=await ipc.callV2(h.deps,method,request.payload);
    return {result,observations:h.observations,state};
  } finally {await h.close();}
}
const direct = process.argv[1] && path.resolve(process.argv[1])===fileURLToPath(import.meta.url);
if(direct && !process.versions.electron) {
  for(const [index,method] of v2.METHODS.entries()) for(const status of ['COMPLETED','ACKNOWLEDGED','REJECTED']) {
    test(`desktop-http/M${String(index+1).padStart(2,'0')}-${status}`,{timeout:45000},async()=>{
      const {request,response}=pair(method,status);
      const {result,observations,state}=await invoke(method,{body:response},request);
      assert.equal(result.protocol_status,status,exact.display(result));
      assert.equal(observations.http.length,1);
      assert.equal(observations.children.length,2);
      for(const child of observations.children)assert(child.facts.exited&&child.facts.closed&&child.facts.stdoutClosed&&child.facts.stderrClosed&&child.facts.stdinClosed);
      if(status==='ACKNOWLEDGED'){assert.equal(result.completed,false);assert.equal(state.expectedRevision,request.expected_revision);assert.equal(state.writerEpoch,request.writer_epoch);}
      if(status==='REJECTED')assert.equal(result.ok,false);
      if(status==='COMPLETED')assert.equal(result.completed,true);
    });
  }
}

async function responseCase(change, expected, method='session.get') {
  const {request,response}=pair(method);const changed=change(response,request) || {body:response};
  const result=await invoke(method,changed,request);
  assert.equal(result.observations.http.length,1);
  if(expected==='VALID')assert.equal(result.result.completed,true,exact.display(result.result));
  else {assert.equal(result.result.ok,false);if(expected)assert.equal(result.result.reason,expected,exact.display(result.result));}
  return result;
}
async function purePacket(rawRequest, rawResponse, phase='REQUEST', status=null, mutate=()=>{}) {
  const app=process.env.RESEARCHOS_DESKTOP_WIRE_ROOT;assert(app);
  const packet={schema:'researchos.desktop.http-validation/1',phase,nonce:crypto.randomUUID(),http_status:status,
    request_raw_base64:Buffer.from(rawRequest).toString('base64'),response_raw_base64:Buffer.from(rawResponse || '').toString('base64')};
  mutate(packet);
  const {spawn}=await import('node:child_process');
  const executable=path.join(app,'resources/client-wire/researchos-client-wire-validator.exe');
  const proc=spawn(executable,[],{cwd:app,windowsHide:true,shell:false,env:{SystemRoot:process.env.SystemRoot},stdio:['pipe','pipe','pipe']});
  const parts=[],errors=[];let exit=null,closed=false,stdoutClosed=false,stderrClosed=false;
  proc.stdout.on('data',p=>parts.push(p));proc.stderr.on('data',p=>errors.push(p));
  proc.stdout.on('close',()=>stdoutClosed=true);proc.stderr.on('close',()=>stderrClosed=true);
  proc.on('exit',code=>exit=code);
  const done=new Promise((resolve,reject)=>{proc.on('error',reject);proc.on('close',()=>{closed=true;resolve();});});
  // This exact owned validator is blocked on its still-open stdin while its
  // actual loaded public executable modules are recorded. No foreign PID scan.
  auditOwnedModules(proc.pid,'pure-validator');
  const timer=setTimeout(()=>proc.kill(),10000);proc.stdin.end(JSON.stringify(packet));await done;clearTimeout(timer);
  const out=Buffer.concat(parts);saveEvidence({http:[],children:[{input:Buffer.from(JSON.stringify(packet)),stdout:out,stderr:Buffer.concat(errors),facts:{phase,pid:proc.pid,exit,closed,stdoutClosed,stderrClosed}}]});
  assert.equal(exit,0);assert(closed&&stdoutClosed&&stderrClosed);
  return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(out));
}
function auditOwnedModules(pid, label) {
  assert(Number.isSafeInteger(pid)&&pid>0);
  const executable=path.join(process.env.SystemRoot,'System32/WindowsPowerShell/v1.0/powershell.exe');
  const script=`[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false); $owned = Get-Process -Id ${pid} -ErrorAction Stop; @{pid=$owned.Id;start_time=$owned.StartTime.ToUniversalTime().ToString('o');modules=@($owned.Modules | ForEach-Object {$_.FileName})} | ConvertTo-Json -Compress`;
  const argv=['-NoProfile','-NonInteractive','-Command',script];
  const result=require('node:child_process').spawnSync(executable,argv,{windowsHide:true,shell:false,encoding:'utf8',timeout:10000});
  const directory=process.env.RESEARCHOS_DESKTOP_CASE_RECEIPT;assert(directory);fs.mkdirSync(directory,{recursive:true});
  const stem=path.join(directory,'modules-'+label+'-'+crypto.randomUUID());fs.writeFileSync(stem+'.stdout',result.stdout||'');fs.writeFileSync(stem+'.stderr',result.stderr||'');
  fs.writeFileSync(stem+'.invocation.json',JSON.stringify({actualargv:[executable,...argv],cwd:ROOT,exit:result.status,error:result.error?.code||null,owned_pid:pid},null,2));
  assert.equal(result.status,0,result.stderr);const raw=JSON.parse(result.stdout);assert.equal(raw.pid,pid);
  const files=raw.modules.map(file=>({path:file,sha256:crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'),bytes:fs.statSync(file).size}));
  fs.writeFileSync(stem+'.closure.json',JSON.stringify({pid,start_time:raw.start_time,files},null,2));
}
const simpleResponses={
 'B-utf8/invalid-byte':()=>responseCase(()=>({raw:Buffer.from([0xc0,0xaf])}),'INVALID_JSON'),
 'B-utf8/lone-surrogate':()=>responseCase(()=>({raw:Buffer.from('"\\ud800"')}),'INVALID_JSON'),
 'B-duplicate/literal':()=>responseCase(r=>({raw:Buffer.from(exact.stringify(r).replace('{','{"method":"session.get",'))}),'INVALID_JSON'),
 'B-duplicate/decoded-key':()=>responseCase(r=>({raw:Buffer.from(exact.stringify(r).replace('{','{"metho\\u0064":"session.get",'))}),'INVALID_JSON'),
 'B-duplicate/nested':()=>responseCase(r=>({raw:Buffer.from(exact.stringify(r).replace('"result":{','"result":{"session_id":"duplicate",'))}),'INVALID_JSON'),
 'B-trailing/second-object':()=>responseCase(r=>({raw:Buffer.from(exact.stringify(r)+' {}')}),'INVALID_JSON'),
 'B-trailing/suffix':()=>responseCase(r=>({raw:Buffer.from(exact.stringify(r)+' suffix')}),'INVALID_JSON'),
 'B-fraction/near-integer':()=>responseCase(r=>({raw:Buffer.from(exact.stringify(r).replace(/"revision":\d+/, '"revision":1.0000000000000001'))}),'INVALID_RESPONSE_SCHEMA'),
 'B-fraction/scoped-near':()=>responseCase(r=>({raw:Buffer.from(exact.stringify(r).replace(/"revision":\d+/g, '"revision":8.0000000000000001'))}),'INVALID_RESPONSE_SCHEMA'),
 'B-maxplus/max-to-next':()=>responseCase(r=>{r.revision=r.result.revision=9007199254740992n;return {body:r};},'VALID'),
 'B-maxplus/integer-exponent':()=>responseCase(r=>({raw:Buffer.from(exact.stringify(r).replace(/"revision":\d+/g,'"revision":1e1'))}),'VALID'),
 'B-maxplus/beyond-int64':()=>responseCase(r=>{r.revision=r.result.revision=9223372036854775808n;return {body:r};},'VALID'),
 'B-adjacent/distinct':async()=>{const a=await responseCase(r=>{r.revision=r.result.revision=9007199254740992n;return {body:r};},'VALID');assert.equal(a.state.expectedRevision,9007199254740992n);assert.notEqual(a.state.expectedRevision,9007199254740993n);assert.match(exact.stringify({revision:9007199254740993n}),/:9007199254740993/);},
 'B-protocol/wrong':()=>responseCase(r=>{r.protocol_version='wrong';return {body:r};},'INVALID_RESPONSE_SCHEMA'),
 'B-command/wrong':()=>responseCase(r=>{r.command_id='different';return {body:r};},'RESPONSE_IDENTITY'),
 'B-method/wrong':()=>responseCase(r=>{r.method='session.update';return {body:r};},'RESPONSE_IDENTITY'),
 'B-project/result-wrong':()=>responseCase(r=>{r.result.project_id='other';return {body:r};},'RESPONSE_IDENTITY'),
 'B-project/invented-top':()=>responseCase(r=>{r.project_id='invented';return {body:r};},'INVALID_RESPONSE_SCHEMA'),
 'B-session/wrong':()=>responseCase(r=>{r.session_id='other';return {body:r};},'RESPONSE_IDENTITY'),
 'B-session/null':()=>responseCase(r=>{r.session_id=null;return {body:r};},'RESPONSE_IDENTITY'),
 'B-derived/create-valid':()=>responseCase(r=>({body:r}),'VALID','session.create'),
 'B-derived/create-wrong-project':()=>responseCase(r=>{r.result.project_id='other';return {body:r};},'RESPONSE_IDENTITY','session.create'),
 'B-derived/goal-null':()=>responseCase(r=>({body:r}),'VALID','goal.start'),
 'B-http503/text':()=>responseCase(()=>({status:503,raw:Buffer.from('temporarily unavailable')}),'HTTP_503'),
 'B-http503/json':()=>responseCase(()=>({status:503,raw:Buffer.from('{"code":"HOST_UNAVAILABLE"}')}),'HTTP_503'),
 'B-http401/no-write-replay':async()=>{const p=pair('session.send');const r=await invoke('session.send',{status:401,raw:Buffer.from('unauthorized')},p.request);assert.equal(r.result.reason,'HTTP_401');assert.equal(r.observations.http.length,1);},
 'B-oversize/response':()=>responseCase(()=>({raw:Buffer.alloc(16777217,32)}),'LOCAL_RESOURCE_LIMIT'),
 'B-oversize/request':async()=>{const p=pair('session.send');p.request.payload.text='x'.repeat(8388609);const h=await harness(()=>{throw Error('must not POST')});try{const r=await h.transport('POST',h.url+'/v2/command',p.request,{});assert.equal(r.reason,'LOCAL_RESOURCE_LIMIT');assert.equal(h.observations.http.length,0);}finally{await h.close();}},
 'B-truncated/body':()=>responseCase(r=>({raw:Buffer.from(exact.stringify(r).slice(0,-1))}),'INVALID_JSON'),
 'B-reject/valid':async()=>{const p=pair('session.get','REJECTED');const r=await invoke('session.get',{body:p.response},p.request);assert.equal(r.result.protocol_status,'REJECTED');assert.equal(r.observations.http.length,1);},
 'B-reject/invalid-top':()=>responseCase(r=>{r.status='NOT_IMPLEMENTED';return {body:r};},'INVALID_RESPONSE_SCHEMA'),
 'B-reject/bad-pending':()=>responseCase(r=>{r.status='ACKNOWLEDGED';return {body:r};},'INVALID_RESPONSE_SCHEMA'),
 'B-atomic/foreign-read':()=>responseCase(r=>{r.result.writer.client_id='foreign';return {body:r};},'VALID'),
 'B-atomic/config-revision':async()=>{const p=pair('host.status');p.response.result.config_revision=9007199254740993n;const r=await invoke('host.status',{body:p.response},p.request);assert.equal(r.result.completed,true);assert.equal(r.state.expectedRevision,null);},
 'identity/host-client':()=>responseCase(r=>{r.result.client_id='different';return {body:r};},'RESPONSE_IDENTITY','host.status'),
 'identity/host-revision-one':()=>responseCase(r=>{r.revision=1;return {body:r};},'VALID','host.status'),
 'schema/host-revision-zero':()=>responseCase(r=>{r.revision=0;return {body:r};},'INVALID_RESPONSE_SCHEMA','host.status'),
 'numeric/negative-zero':async()=>{const p=pair('session.events');const raw=exact.stringify(p.response).replace('"next_sequence":4','"next_sequence":-0');const r=await invoke('session.events',{raw:Buffer.from(raw)},p.request);assert.equal(r.result.completed,true);assert(raw.includes('"next_sequence":-0'));assert(!raw.includes('NaN'));},
 'request/fullschema-before-http':async()=>{const p=pair('session.send');p.request.payload.unknown='invalid';const h=await harness(()=>{throw Error('must not POST')});try{const r=await h.transport('POST',h.url+'/v2/command',p.request,{});assert.equal(r.reason,'INVALID_REQUEST_SCHEMA');assert.equal(h.observations.http.length,0);}finally{await h.close();}},
 'numeric/unsafe-local-number':async()=>{const p=pair('session.get');p.request.expected_revision=9007199254740992;const h=await harness(()=>{throw Error('must not POST')});try{const r=await h.transport('POST',h.url+'/v2/command',p.request,{});assert.equal(r.reason,'AMBIGUOUS_LOCAL_NUMBER');assert.equal(h.observations.http.length,0);}finally{await h.close();}},
 'numeric/forged-tags':async()=>{const p=pair('session.get');p.request.expected_revision={type:'integer',value:'9007199254740993'};const h=await harness(()=>{throw Error('must not POST')});try{const r=await h.transport('POST',h.url+'/v2/command',p.request,{});assert.equal(r.reason,'INVALID_REQUEST_SCHEMA');assert.equal(h.observations.http.length,0);}finally{await h.close();}},
};
if(direct && !process.versions.electron)for(const [name,run] of Object.entries(simpleResponses))test('desktop-http/'+name,{timeout:45000},run);

async function pendingTakeover(stages) {
  const p=pair('session.attach');p.request.payload.request_write_owner=true;
  const state={projectId:p.request.project_id,sessionId:p.request.session_id,expectedRevision:7,writerEpoch:2,writerClientId:'foreign',writerExpiresAt:'2099-01-01T00:00:00Z'};
  const ack=get('valid_async_ack');const snap=snapshot({revision:8,writer:{client_id:'desktop-shell',epoch:3,expires_at:'2099-01-01T00:00:00Z'}});
  const h=await harness(async(raw,index)=>{
    const env=JSON.parse(raw.toString('utf8'));
    const response=index===1?{...ack,status:'ACKNOWLEDGED'}:{...pair(env.method).response,status:'COMPLETED',revision:8,result:env.method==='session.get'?snap:{snapshot:snap,write_owner_acquired:true}};
    response.protocol_version=env.protocol_version;response.command_id=env.command_id;response.method=env.method;response.session_id=env.session_id;
    return {body:response};
  },{state});
  try {
    const args={after_sequence:3,request_write_owner:true};const first=await ipc.callV2(h.deps,'session.attach',args);
    assert.equal(first.protocol_status,'ACKNOWLEDGED');assert.equal(state.writerEpoch,2);assert.equal(state.expectedRevision,7);
    if(stages>=2){const read=await ipc.callV2(h.deps,'session.get',{});assert.equal(read.completed,true);assert.equal(state.writerEpoch,2);assert.equal(state.expectedRevision,7);
      const blocked=await ipc.callV2(h.deps,'session.send',{text:'held',attachment_artifact_ids:[],delivery:'NORMAL'});assert.equal(blocked.reason,'COMMAND_PENDING');assert.equal(h.observations.http.length,2);}
    if(stages>=3){const complete=await ipc.callV2(h.deps,'session.attach',args);assert.equal(complete.completed,true);assert.equal(state.writerEpoch,3);assert.equal(state.expectedRevision,8);assert.deepEqual(h.observations.http[0].raw,h.observations.http[2].raw);}
    assert.equal(h.observations.http.length,stages);
  } finally {await h.close();}
}
const more={
 'B-ackattach/pending-no-adopt':()=>pendingTakeover(1),
 'B-ackattach/get-no-completion':()=>pendingTakeover(2),
 'B-ackattach/same-command-completed':()=>pendingTakeover(3),
 'B-acksend/pending-draft':async()=>{const p=pair('session.send','ACKNOWLEDGED');const r=await invoke('session.send',{body:p.response},p.request);assert.equal(r.result.completed,false);assert.equal(r.state.pendingOperation.method,'session.send');assert.equal(r.observations.http.length,1);},
 'B-atomic/late':async()=>{const p=pair('session.get');const state={projectId:p.request.project_id,sessionId:p.request.session_id,expectedRevision:1,writerEpoch:2};let release;
   const ready=new Promise(resolve=>release=resolve);const h=await harness(async()=>{state.projectId='new-project';release();return {body:p.response};},{state});
   try{const request=ipc.callV2(h.deps,'session.get',{});await ready;const r=await request;assert.equal(r.reason,'STALE_RESPONSE');assert.equal(state.projectId,'new-project');assert.equal(state.expectedRevision,1);}finally{await h.close();}},
 'capacity/request-eight-mib':async()=>{const raw=exact.stringify(pair('host.status').request);const v=await purePacket(raw+' '.repeat(8388608-Buffer.byteLength(raw)));assert.equal(v.outcome,'VALID');},
 'capacity/response-sixteen-mib':async()=>{const p=pair('host.status');const raw=exact.stringify(p.response);const h=await harness(()=>({raw:Buffer.from(raw+' '.repeat(16777216-Buffer.byteLength(raw)))}));
   try{const r=await h.transport('POST',h.url+'/v2/command',p.request,{});assert.equal(r.validated,true);assert.equal(h.observations.http.length,1);}finally{await h.close();}},
 'capacity/private-frame':async()=>{const p=pair('host.status');const req=exact.stringify(p.request),res=exact.stringify(p.response);const v=await purePacket(req+' '.repeat(8388608-Buffer.byteLength(req)),res+' '.repeat(16777216-Buffer.byteLength(res)),'RESPONSE',200);assert.equal(v.outcome,'VALID');},
 'capacity/metadata':async()=>{const v=await purePacket(exact.stringify(pair('host.status').request),'','REQUEST',null,p=>{p.unknown='x';});assert.equal(v.outcome,'REFUSED');},
 'capacity/unicode-host-limit':async()=>{const p=pair('workspace.write');p.request.payload.text='界'.repeat(360000);const h=await harness(()=>({status:413,raw:Buffer.from('bounded host request')}));
   try{const r=await h.transport('POST',h.url+'/v2/command',p.request,{});assert.equal(r.reason,'HTTP_413');assert(h.observations.http[0].raw.length>1048576);assert.equal(h.observations.http.length,1);}finally{await h.close();}},
 'capacity/queued-bytes':async()=>{const p=pair('session.get');p.request.payload.bad=true;const h=await harness(()=>{throw Error('preflight must refuse')});
   try{const jobs=Array.from({length:4},()=>h.transport('POST',h.url+'/v2/command',p.request,{}));const outcomes=await Promise.all(jobs);assert(outcomes.some(x=>x.reason==='LOCAL_RESOURCE_LIMIT'));assert.equal(h.observations.http.length,0);assert(h.observations.children.length<=3);}finally{await h.close();}},
 'resource/exponent':async()=>{const v=await purePacket('1e4097');assert.equal(v.reason,'LOCAL_RESOURCE_LIMIT');},
 'resource/coefficient':async()=>{const v=await purePacket('1'.repeat(4097));assert.equal(v.reason,'LOCAL_RESOURCE_LIMIT');},
 'resource/depth':async()=>{const v=await purePacket('['.repeat(257)+'0'+']'.repeat(257));assert.equal(v.reason,'LOCAL_RESOURCE_LIMIT');},
 'resource/nodes':async()=>{const v=await purePacket('['+'0,'.repeat(262144)+'0]');assert.equal(v.reason,'LOCAL_RESOURCE_LIMIT');},
 'resource/token':async()=>{const v=await purePacket('1e+'+'0'.repeat(8190));assert.equal(v.reason,'LOCAL_RESOURCE_LIMIT');},
 'resource/decoded-strings':async()=>{const v=await purePacket('"'+'a'.repeat(8388608)+'"');assert.equal(v.reason,'LOCAL_RESOURCE_LIMIT');},
 'prebuilder/default-configure':async()=>{const p=pair('host.configure');const r=await invoke('host.configure',{body:p.response},p.request);assert.equal(r.result.completed,true);const sent=JSON.parse(r.observations.http[0].raw.toString('utf8'));for(const k of ['project_id','session_id','expected_revision','writer_epoch'])assert.equal(sent[k],null);},
 'model-config/selected-project-first-use':async()=>{const p=pair('host.configure');const state={projectId:'fixture_project',sessionId:null,expectedRevision:null,writerEpoch:null};const h=await harness(()=>({body:p.response}),{state});try{const r=await ipc.callV2(h.deps,'host.configure',p.request.payload);assert.equal(r.completed,true);assert.equal(h.observations.http.length,1);const sent=JSON.parse(h.observations.http[0].raw);for(const k of ['project_id','session_id','expected_revision','writer_epoch'])assert.equal(sent[k],null);assert.deepEqual(sent.payload,p.request.payload);assert.equal(state.projectId,'fixture_project');assert.equal(state.sessionId,null);}finally{await h.close();}},
 'model-config/session-writer-scope':async()=>{const p=pair('host.configure');const state={projectId:'fixture_project',sessionId:'fixture_session',expectedRevision:7,writerEpoch:2,writerClientId:'desktop-shell',writerExpiresAt:'2099-01-01T00:00:00Z'};p.response.session_id='fixture_session';p.response.revision=7;const h=await harness(()=>({body:p.response}),{state});try{const r=await ipc.callV2(h.deps,'host.configure',p.request.payload);assert.equal(r.completed,true);const sent=JSON.parse(h.observations.http[0].raw);assert.deepEqual([sent.project_id,sent.session_id,sent.expected_revision,sent.writer_epoch],['fixture_project','fixture_session',7,2]);assert.equal(state.expectedRevision,7);assert.equal(state.writerEpoch,2);}finally{await h.close();}},
 'model-config/session-no-writer-refused':async()=>{const p=pair('host.configure');const state={projectId:'fixture_project',sessionId:'fixture_session',expectedRevision:7,writerEpoch:null,writerClientId:null,writerExpiresAt:null};const h=await harness(()=>({body:p.response}),{state});try{const r=await ipc.callV2(h.deps,'host.configure',p.request.payload);assert.equal(r.reason,'WRITE_OWNER_REQUIRED');assert.equal(h.observations.http.length,0);}finally{await h.close();}},
 'model-config/local-refusal-releases-undispatched-write':async()=>{const p=pair('host.configure');const h=await harness(raw=>{const env=JSON.parse(raw);const good=pair('host.configure');good.response.command_id=env.command_id;Object.assign(good.response.result,env.payload);return {body:good.response};},{state:{projectId:'fixture_project',sessionId:null,expectedRevision:null,writerEpoch:null}});try{const invalid={...p.request.payload,provider_id:''};const refused=await ipc.callV2(h.deps,'host.configure',invalid);assert.equal(refused.reason,'INVALID_REQUEST_SCHEMA');assert.equal(refused.dispatch_state,'NOT_SENT');assert.equal(h.observations.http.length,0);const saved=await ipc.callV2(h.deps,'host.configure',p.request.payload);assert.equal(saved.completed,true);assert.equal(h.observations.http.length,1);}finally{await h.close();}},
 'model-config/ack-replay-preserves-original-envelope':async()=>{const p=pair('host.configure');let index=0;const h=await harness(raw=>{const env=JSON.parse(raw);const response=pair('host.configure',++index===1?'ACKNOWLEDGED':'COMPLETED').response;response.command_id=env.command_id;response.session_id=env.session_id;if(index>1)Object.assign(response.result,env.payload);return {body:response};},{state:{projectId:'fixture_project',sessionId:null,expectedRevision:null,writerEpoch:null}});try{const ack=await ipc.callV2(h.deps,'host.configure',p.request.payload);assert.equal(ack.protocol_status,'ACKNOWLEDGED');const done=await ipc.callV2(h.deps,'host.configure',p.request.payload);assert.equal(done.completed,true);assert.equal(h.observations.http.length,2);assert.deepEqual(JSON.parse(h.observations.http[0].raw),JSON.parse(h.observations.http[1].raw));}finally{await h.close();}},
 'model-config/uncertain-response-retains-write-barrier':async()=>{const p=pair('host.configure');const h=await harness(()=>({raw:Buffer.from('{bad')}),{state:{projectId:'fixture_project',sessionId:null,expectedRevision:null,writerEpoch:null}});try{const first=await ipc.callV2(h.deps,'host.configure',p.request.payload);assert.equal(first.ok,false);assert.notEqual(first.dispatch_state,'NOT_SENT');assert.equal(h.observations.http.length,1);const changed=await ipc.callV2(h.deps,'host.configure',{...p.request.payload,model_id:'different-model'});assert.equal(changed.reason,'COMMAND_PENDING');assert.equal(h.observations.http.length,1);}finally{await h.close();}},
 'model-config/uncertain-then-local-refusal-keeps-original':async()=>{const p=pair('host.configure');const h=await harness(()=>({raw:Buffer.from('{bad')}),{state:{projectId:'fixture_project',sessionId:null,expectedRevision:null,writerEpoch:null}});const original=h.deps.v2Transport;let attempts=0;h.deps.v2Transport=(...args)=>++attempts===2?Promise.resolve({ok:false,reason:'LOCAL_RESOURCE_LIMIT',dispatch_state:'NOT_SENT'}):original(...args);try{const first=await ipc.callV2(h.deps,'host.configure',p.request.payload);assert.notEqual(first.dispatch_state,'NOT_SENT');assert.equal(h.observations.http.length,1);const retry=await ipc.callV2(h.deps,'host.configure',p.request.payload);assert.equal(retry.reason,'LOCAL_RESOURCE_LIMIT');assert.notEqual(retry.dispatch_state,'NOT_SENT');const changed=await ipc.callV2(h.deps,'host.configure',{...p.request.payload,model_id:'different-model'});assert.equal(changed.reason,'COMMAND_PENDING');assert.equal(h.observations.http.length,1);}finally{await h.close();}},
 'model-config/ack-then-local-refusal-keeps-original':async()=>{const p=pair('host.configure','ACKNOWLEDGED');const h=await harness(()=>({body:p.response}),{state:{projectId:'fixture_project',sessionId:null,expectedRevision:null,writerEpoch:null}});const original=h.deps.v2Transport;let attempts=0;h.deps.v2Transport=(...args)=>++attempts===2?Promise.resolve({ok:false,reason:'LOCAL_RESOURCE_LIMIT',dispatch_state:'NOT_SENT'}):original(...args);try{const ack=await ipc.callV2(h.deps,'host.configure',p.request.payload);assert.equal(ack.protocol_status,'ACKNOWLEDGED');const retry=await ipc.callV2(h.deps,'host.configure',p.request.payload);assert.equal(retry.reason,'LOCAL_RESOURCE_LIMIT');assert.notEqual(retry.dispatch_state,'NOT_SENT');const changed=await ipc.callV2(h.deps,'host.configure',{...p.request.payload,model_id:'different-model'});assert.equal(changed.reason,'COMMAND_PENDING');assert.equal(h.observations.http.length,1);}finally{await h.close();}},
 'model-config/credential-unavailable-before-first-send':async()=>{const p=pair('host.configure');const h=await harness(raw=>{const env=JSON.parse(raw);const response=pair('host.configure').response;response.command_id=env.command_id;Object.assign(response.result,env.payload);return {body:response};},{state:{projectId:'fixture_project',sessionId:null,expectedRevision:null,writerEpoch:null}});try{h.deps.credentialFor=async()=>{throw Error('unavailable')};const refused=await ipc.callV2(h.deps,'host.configure',p.request.payload);assert.equal(refused.reason,'CREDENTIAL_UNAVAILABLE');assert.equal(refused.dispatch_state,'NOT_SENT');assert.equal(h.observations.http.length,0);h.deps.credentialFor=async()=> 'public-fixture-only';const saved=await ipc.callV2(h.deps,'host.configure',p.request.payload);assert.equal(saved.completed,true);assert.equal(h.observations.http.length,1);}finally{await h.close();}},
 'model-config/credential-loss-after-ack-keeps-original':async()=>{const p=pair('host.configure','ACKNOWLEDGED');const h=await harness(()=>({body:p.response}),{state:{projectId:'fixture_project',sessionId:null,expectedRevision:null,writerEpoch:null}});try{const ack=await ipc.callV2(h.deps,'host.configure',p.request.payload);assert.equal(ack.protocol_status,'ACKNOWLEDGED');h.deps.credentialFor=async()=>{throw Error('unavailable')};const retry=await ipc.callV2(h.deps,'host.configure',p.request.payload);assert.equal(retry.reason,'CREDENTIAL_UNAVAILABLE');assert.notEqual(retry.dispatch_state,'NOT_SENT');const changed=await ipc.callV2(h.deps,'host.configure',{...p.request.payload,model_id:'different-model'});assert.equal(changed.reason,'COMMAND_PENDING');assert.equal(h.observations.http.length,1);}finally{await h.close();}},
 'model-config/host-switch-keeps-origin-barrier':async()=>{const p=pair('host.configure');let mode='ACKNOWLEDGED',hostId='host-aaaaaaaaaaaa',dataDir='fixture-data-root',pid=1234;const h=await harness(raw=>{const env=JSON.parse(raw);const response=pair('host.configure',mode).response;response.command_id=env.command_id;response.session_id=env.session_id;if(mode==='COMPLETED')Object.assign(response.result,env.payload);return {body:response};},{state:{projectId:'fixture_project',sessionId:null,expectedRevision:null,writerEpoch:null}});h.deps.fsImpl.readFileSync=()=>JSON.stringify({url:h.url,pid,data_dir:dataDir,host_instance_id:hostId});try{const ack=await ipc.callV2(h.deps,'host.configure',p.request.payload);assert.equal(ack.protocol_status,'ACKNOWLEDGED');hostId='host-bbbbbbbbbbbb';dataDir='other-data-root';const wrong=await ipc.callV2(h.deps,'host.configure',p.request.payload);assert.equal(wrong.reason,'HOST_CHANGED_PENDING');assert.equal(h.observations.http.length,1);const changed=await ipc.callV2(h.deps,'host.configure',{...p.request.payload,model_id:'different-model'});assert.equal(changed.reason,'COMMAND_PENDING');hostId='host-aaaaaaaaaaaa';dataDir='fixture-data-root';pid=9999;mode='COMPLETED';const done=await ipc.callV2(h.deps,'host.configure',p.request.payload);assert.equal(done.completed,true);assert.equal(h.observations.http.length,2);assert.deepEqual(JSON.parse(h.observations.http[0].raw),JSON.parse(h.observations.http[1].raw));}finally{await h.close();}},
 'model-config/host-switch-during-credential-before-send':async()=>{const p=pair('host.configure');const h=await harness(()=>{throw Error('must not dispatch')},{state:{projectId:'fixture_project',sessionId:null,expectedRevision:null,writerEpoch:null}});let hostId='host-aaaaaaaaaaaa';h.deps.fsImpl.readFileSync=()=>JSON.stringify({url:h.url,pid:1234,data_dir:'fixture-data-root',host_instance_id:hostId});h.deps.credentialFor=async()=>{hostId='host-bbbbbbbbbbbb';return 'public-fixture-only'};try{const result=await ipc.callV2(h.deps,'host.configure',p.request.payload);assert.equal(result.reason,'HOST_CHANGED_BEFORE_SEND');assert.equal(result.dispatch_state,'NOT_SENT');assert.equal(h.observations.http.length,0);}finally{await h.close();}},
 'model-config/origin-is-native-not-remote':async()=>{const h=await harness(raw=>{const env=JSON.parse(raw);const response=pair('host.status').response;response.command_id=env.command_id;response.result.host_instance_id='host-ffffffffffff';return {body:response};});try{const status=await ipc.callV2(h.deps,'host.status',{});assert.equal(status.completed,true);assert.equal(status.result.host_instance_id,'host-ffffffffffff');const expected=crypto.createHash('sha256').update(JSON.stringify(['host-aaaaaaaaaaaa','fixture-data-root'])).digest('hex');assert.equal(status.local_host_origin,expected);}finally{await h.close();}},
 'model-config/completed-keeps-origin-after-host-switch':async()=>{const p=pair('host.configure');let release,arrived;const ready=new Promise(resolve=>arrived=resolve);const a=await harness(async raw=>{const env=JSON.parse(raw);arrived();await new Promise(resolve=>release=resolve);const response=pair('host.configure').response;response.command_id=env.command_id;Object.assign(response.result,env.payload);return {body:response};});const b=await harness(raw=>{const env=JSON.parse(raw);assert.equal(env.method,'host.status');const response=pair('host.status').response;response.command_id=env.command_id;return {body:response};});let discovery={url:a.url,pid:1,data_dir:'root-A',host_instance_id:'host-aaaaaaaaaaaa'};a.deps.fsImpl.readFileSync=()=>JSON.stringify(discovery);try{const completion=ipc.callV2(a.deps,'host.configure',p.request.payload);await ready;discovery={url:b.url,pid:2,data_dir:'root-B',host_instance_id:'host-bbbbbbbbbbbb'};release();const done=await completion;const status=await ipc.callV2(a.deps,'host.status',{});assert.equal(done.completed,true);assert.notEqual(done.local_host_origin,status.local_host_origin);assert.equal(done.result.model_config_ref,p.response.result.model_config_ref);assert.equal(a.observations.http.length,1);assert.equal(b.observations.http.length,1);}finally{if(release)release();await a.close();await b.close();}},
 'model-config/concurrent-status-keeps-terminal-result-and-origin':async()=>{const p=pair('host.configure');let release,arrived;const ready=new Promise(resolve=>arrived=resolve);const a=await harness(async raw=>{const env=JSON.parse(raw);arrived();await new Promise(resolve=>release=resolve);const response=pair('host.configure').response;response.command_id=env.command_id;Object.assign(response.result,env.payload);return {body:response};});const b=await harness(raw=>{const env=JSON.parse(raw);assert.equal(env.method,'host.status');const response=pair('host.status').response;response.command_id=env.command_id;return {body:response};});let discovery={url:a.url,pid:1,data_dir:'root-A',host_instance_id:'host-aaaaaaaaaaaa'};a.deps.fsImpl.readFileSync=()=>JSON.stringify(discovery);try{const completion=ipc.callV2(a.deps,'host.configure',p.request.payload);await ready;discovery={url:b.url,pid:2,data_dir:'root-B',host_instance_id:'host-bbbbbbbbbbbb'};const queued=deferred(),original=a.deps.v2Transport;a.deps.v2Transport=(...args)=>{queued.release();return original(...args);};const statusPromise=ipc.callV2(a.deps,'host.status',{});await queued.promise;release();const [done,status]=await Promise.all([completion,statusPromise]);assert.equal(done.completed,true);assert.equal(done.result.model_config_ref,p.response.result.model_config_ref);assert.deepEqual(done.result.provider_id,p.request.payload.provider_id);assert.notEqual(done.local_host_origin,status.local_host_origin);assert.equal(a.observations.http.length,1);assert.equal(b.observations.http.length,1);}finally{if(release)release();await a.close();await b.close();}},
 'model-config/same-logical-host-new-url-replays':async()=>{const p=pair('host.configure');const a=await harness(raw=>{const env=JSON.parse(raw);const response=pair('host.configure','ACKNOWLEDGED').response;response.command_id=env.command_id;return {body:response};});const b=await harness(raw=>{const env=JSON.parse(raw);const response=pair('host.configure').response;response.command_id=env.command_id;Object.assign(response.result,env.payload);return {body:response};});let discovery={url:a.url,pid:1,data_dir:'root-A',host_instance_id:'host-aaaaaaaaaaaa'};a.deps.fsImpl.readFileSync=()=>JSON.stringify(discovery);try{const ack=await ipc.callV2(a.deps,'host.configure',p.request.payload);assert.equal(ack.protocol_status,'ACKNOWLEDGED');discovery={url:b.url,pid:999,data_dir:'root-A',host_instance_id:'host-aaaaaaaaaaaa'};const done=await ipc.callV2(a.deps,'host.configure',p.request.payload);assert.equal(done.completed,true);assert.equal(done.local_host_origin,ack.local_host_origin);assert.deepEqual(JSON.parse(a.observations.http[0].raw),JSON.parse(b.observations.http[0].raw));}finally{await a.close();await b.close();}},
 'model-config/status-credential-switch-refused-before-send':async()=>{
   const a=await harness(()=>{throw Error('old host status must not be sent')});
   let discovery={url:a.url,pid:1,data_dir:'root-A',host_instance_id:'host-aaaaaaaaaaaa'};
   a.deps.fsImpl.readFileSync=()=>JSON.stringify(discovery);
   a.deps.credentialFor=async()=>{discovery={url:a.url,pid:2,data_dir:'root-B',host_instance_id:'host-bbbbbbbbbbbb'};return 'public-fixture-only'};
   try{const status=await ipc.callV2(a.deps,'host.status',{});assert.equal(status.reason,'HOST_CHANGED_BEFORE_SEND');assert.equal(status.dispatch_state,'NOT_SENT');assert.equal(a.observations.http.length,0);}finally{await a.close();}
 },
 'model-config/status-response-switch-refused-after-transport':async()=>{
   let release,arrived;const ready=new Promise(resolve=>arrived=resolve);
   const a=await harness(async raw=>{const env=JSON.parse(raw);arrived();await new Promise(resolve=>release=resolve);const response=pair('host.status').response;response.command_id=env.command_id;return {body:response};});
   let discovery={url:a.url,pid:1,data_dir:'root-A',host_instance_id:'host-aaaaaaaaaaaa'};
   a.deps.fsImpl.readFileSync=()=>JSON.stringify(discovery);
   try{const pending=ipc.callV2(a.deps,'host.status',{});await ready;discovery={url:a.url,pid:2,data_dir:'root-B',host_instance_id:'host-bbbbbbbbbbbb'};release();const status=await pending;assert.equal(status.reason,'HOST_CHANGED_DURING_STATUS');assert.equal(status.ok,false);assert.equal(a.observations.http.length,1);}finally{if(release)release();await a.close();}
 },
 'model-config/status-same-logical-host-new-port-allowed':async()=>{
   let release,arrived;const ready=new Promise(resolve=>arrived=resolve);
   const a=await harness(async raw=>{const env=JSON.parse(raw);arrived();await new Promise(resolve=>release=resolve);const response=pair('host.status').response;response.command_id=env.command_id;return {body:response};});
   let discovery={url:a.url,pid:1,data_dir:'root-A',host_instance_id:'host-aaaaaaaaaaaa'};
   a.deps.fsImpl.readFileSync=()=>JSON.stringify(discovery);
   try{const pending=ipc.callV2(a.deps,'host.status',{});await ready;discovery={url:'http://127.0.0.1:12345',pid:2,data_dir:'root-A',host_instance_id:'host-aaaaaaaaaaaa'};release();const status=await pending;assert.equal(status.completed,true);assert.equal(status.local_host_origin,crypto.createHash('sha256').update(JSON.stringify(['host-aaaaaaaaaaaa','root-A'])).digest('hex'));assert.equal(a.observations.http.length,1);}finally{if(release)release();await a.close();}
 },
 'prebuilder/scoped-configure':async()=>{const p=pair('host.configure');Object.assign(p.request,{project_id:'fixture_project',session_id:'fixture_session',expected_revision:7,writer_epoch:2});p.response.session_id=p.request.session_id;p.response.revision=8;const r=await invoke('host.configure',{body:p.response},p.request);assert.equal(r.result.completed,true);assert.equal(r.state.expectedRevision,7);},
 'prebuilder/partial-scope':async()=>{const p=pair('host.configure');Object.assign(p.request,{project_id:'fixture_project',session_id:'fixture_session',expected_revision:null,writer_epoch:2});const r=await invoke('host.configure',{body:p.response},p.request);assert.equal(r.result.reason,'CONFIGURATION_SCOPE_INCOMPLETE');assert.equal(r.observations.http.length,0);},
 'prebuilder/project-goal':async()=>{const p=pair('goal.start');const r=await invoke('goal.start',{body:p.response},p.request);assert.equal(r.result.completed,true);assert.equal(r.state.sessionId,null);},
 'prebuilder/session-goal':async()=>{const p=pair('goal.start');Object.assign(p.request,{session_id:'fixture_session',expected_revision:7,writer_epoch:2});p.response.session_id=p.request.session_id;const r=await invoke('goal.start',{body:p.response},p.request);assert.equal(r.result.completed,true);},
 'prebuilder/attach-read':async()=>{const p=pair('session.attach');const r=await invoke('session.attach',{body:p.response},p.request);assert.equal(r.result.completed,true);assert.equal(JSON.parse(r.observations.http[0].raw).writer_epoch,2);},
 'prebuilder/attach-claim':()=>pendingTakeover(1),
 'channels/exact11and23':async()=>{const handlers=new Map();const add={handle:(name,fn)=>{assert(!handlers.has(name));handlers.set(name,fn);}};ipc.register(add,{});ipc.registerV2(add,{});assert.equal(ipc.BRIDGE.length,11);assert.equal(v2.METHODS.length,23);assert.equal(handlers.size,34);for(const method of v2.METHODS)assert(handlers.has('ros:v2:'+method));assert(!handlers.has('ros:v2:unknown'));},
 'lifecycle/phase-raw-binding':async()=>{const p=pair('host.status');let changed=false;const h=await harness(()=>{throw Error('changed preflight must produce zero POST');},{record:row=>{if(row.kind==='child'&&row.facts.phase==='REQUEST'){assert(row.facts.exited&&row.facts.closed&&row.facts.stdoutClosed&&row.facts.stderrClosed);p.request.command_id='changed-after-preflight';changed=true;}}});
   try{const r=await h.transport('POST',h.url+'/v2/command',p.request,{});assert(changed);assert.equal(r.ok,false);assert.equal(r.reason,'REQUEST_CHANGED_AFTER_PREFLIGHT');assert.equal(h.observations.http.length,0);assert.equal(h.observations.children.length,1);}finally{await h.close();}},
};
async function firstUsePending(stage) {
  const {chooseWorkspace}=require(path.join(ROOT,'apps/desktop/main/lib/first-use.js'));let saved=false;
  const h=await harness(raw=>{const req=JSON.parse(raw.toString('utf8'));const p=pair(req.method,req.method===stage?'ACKNOWLEDGED':'COMPLETED');p.response.command_id=req.command_id;p.response.session_id=req.session_id;return {body:p.response};},{state:{projectId:null,sessionId:null,expectedRevision:null,writerEpoch:null}});
  try{
    const result=await chooseWorkspace({host:{ensureCore:async()=>({discovery:{url:h.url}})},native:{hostInstanceId:()=> 'host-public-fixture',dialNative:async()=>({kind:'NATIVE_WORKSPACE_CHOOSE_RESULT',payload:{selection_ref:'fixture_selection',display_path:'D:/public-fixture'}})},
      callV2:ipc.callV2,deps:{...h.deps,credentialFor:async()=> 'public-fixture-only'},contextStore:{save:()=>saved=true},sessionState:h.deps.sessionState});
    assert.equal(result.ok,false);assert.equal(saved,false);assert.equal(h.observations.http.length,stage==='workspace.register'?1:2);
  }finally{await h.close();}
}
more['first-use/workspace-ack']=()=>firstUsePending('workspace.register');more['first-use/bootstrap-ack']=()=>firstUsePending('project.bootstrap');
if(direct && !process.versions.electron)for(const [name,run] of Object.entries(more))test('desktop-http/'+name,{timeout:45000},run);

if(direct && !process.versions.electron) {
  test('qualification-lane/R01 isolated real Main scope',{timeout:45000},async()=>{
    const h=await qualificationFixture();try{
      const result=await h.prepare();
      assert.equal(result.scope.modelRef,'fixture_config_1');
      assert.deepEqual(h.hits,['session.get','host.status']);
      assert.equal(h.observations.children.length,4);
      assert.equal(h.sourceHash,crypto.createHash('sha256').update(actualPrepareSource).digest('hex'));
    }finally{await h.close();}
  });
  for(const [id,blocked,poll] of [
    ['R02','host.status','session.events'],['R03','session.get','session.events'],
    ['R04','host.status','host.status'],['R05','session.get','session.get']]) {
    test(`qualification-lane/${id} ${blocked} overlapped by ${poll}`,{timeout:45000},async()=>{
      const arrived=deferred(),gate=deferred();let held=false;
      const h=await qualificationFixture(async env=>{if(env.method===blocked&&!held){held=true;arrived.release();await gate.promise;}});
      try{
        const prepared=h.prepare();await arrived.promise;
        const queued=deferred(),original=h.deps.v2Transport;
        h.deps.v2Transport=(...args)=>{queued.release();return original(...args);};
        const display=ipc.callV2(h.deps,poll,poll==='session.events'?pair(poll).request.payload:{});
        await queued.promise;gate.release();
        const scope=await prepared;
        const shown=await display;assert.equal(shown.completed,true,JSON.stringify(shown));
        assert.equal(scope.scope.modelRef,'fixture_config_1');
        assert.equal(h.hits.filter(method=>method===poll).length,poll===blocked?2:1);
        assert.equal(h.observations.children.length,h.hits.length*2);
      }finally{gate.release();await h.close();}
    });
  }
  test('qualification-lane/R06 presentation methods isolate and same-method newest wins',{timeout:45000},async()=>{
    const first=deferred(),gate=deferred();let count=0;
    const h=await qualificationFixture(async env=>{if(env.method==='session.get'&&++count===1){first.release();await gate.promise;}});
    try{
      const old=ipc.callV2(h.deps,'session.get',{});await first.promise;
      const queued=deferred(),original=h.deps.v2Transport;let queuedCount=0;
      h.deps.v2Transport=(...args)=>{if(++queuedCount===2)queued.release();return original(...args);};
      const eventsPromise=ipc.callV2(h.deps,'session.events',pair('session.events').request.payload);
      const latestPromise=ipc.callV2(h.deps,'session.get',{});
      await queued.promise;gate.release();const stale=await old;
      const [events,latest]=await Promise.all([eventsPromise,latestPromise]);
      assert.equal(events.completed,true);assert.equal(latest.completed,true);
      assert.equal(stale.reason,'STALE_RESPONSE');assert.deepEqual(h.hits,['session.get','session.events','session.get']);
    }finally{gate.release();await h.close();}
  });
  for(const [id,field,changed,original,returnToA] of [
    ['R07','projectId','other-project','fixture_project',false],
    ['R07','projectId','other-project','fixture_project',true],
    ['R07','sessionId','other-session','fixture_session',false],
    ['R07','sessionId','other-session','fixture_session',true],
    ['R08','expectedRevision',2,1,true],
    ['R08','writerEpoch',3,2,true],
    ['R08','writerClientId','other-client','desktop-shell',true],
    ['R08','writerExpiresAt','2098-01-01T00:00:00Z','2099-01-01T00:00:00Z',true]]) {
    test(`qualification-lane/${id} Main Proxy ${field} ${returnToA?'ABA':'change'} fence`,{timeout:45000},async()=>{
      const arrived=deferred(),gate=deferred();let held=false;
      const hold=id==='R07'?'session.get':'host.status';
      const h=await qualificationFixture(async env=>{if(env.method===hold&&!held){held=true;arrived.release();await gate.promise;}});
      try{
        const pending=h.prepare().then(()=>({ok:true}),e=>({ok:false,reason:e.code||e.message}));
        await arrived.promise;
        const before=h.sessionState[id==='R07'?'selectionGeneration':'authorityGeneration'];
        h.sessionState[field]=changed;
        if(returnToA)h.sessionState[field]=original;
        assert.equal(h.sessionState[id==='R07'?'selectionGeneration':'authorityGeneration'],before+(returnToA?2:1));
        gate.release();const result=await pending;
        assert.equal(result.ok,false);assert.equal(result.reason,id==='R07'?'SESSION_CHANGED':'HOST_OR_CONTEXT_CHANGED');
        assert.equal(h.observations.http.length,id==='R07'?1:2);
      }finally{gate.release();await h.close();}
    });
  }
  test('qualification-lane/R09 write reservation invalidates pending scope',{timeout:45000},async()=>{
    const arrived=deferred(),gate=deferred();let held=false;
    const h=await qualificationFixture(async env=>{if(env.method==='host.status'&&!held){held=true;arrived.release();await gate.promise;}});
    try{
      const pending=h.prepare().then(()=>({ok:true}),e=>({ok:false,reason:e.code||e.message}));await arrived.promise;
      const queued=deferred(),original=h.deps.v2Transport;
      h.deps.v2Transport=(...args)=>{queued.release();return original(...args);};
      const sendPromise=ipc.callV2(h.deps,'session.send',pair('session.send').request.payload);
      await queued.promise;gate.release();const result=await pending;
      const sent=await sendPromise;assert.equal(sent.completed,true,JSON.stringify(sent));
      assert.equal(result.ok,false);assert.equal(result.reason,'HOST_OR_CONTEXT_CHANGED');
      assert.deepEqual(h.hits,['session.get','host.status','session.send']);
    }finally{gate.release();await h.close();}
  });
  for(const [method,change] of [
    ['provider.probe',()=>{}],
    ['workspace.register',()=>{}],
    ['session.create',()=>{}],
    ['session.attach',payload=>{payload.request_write_owner=false;}],
    ['provider.models',payload=>{payload.refresh=true;payload.allow_network=true;}],
  ]) {
    test(`qualification-lane/V2 ${method} activity fences in-flight authority read`,{timeout:45000},async()=>{
      const arrived=deferred(),gate=deferred();let held=false;
      const h=await qualificationFixture(async env=>{if(env.method==='host.status'&&!held){held=true;arrived.release();await gate.promise;}});
      try {
        const pending=h.prepare().then(()=>({ok:true}),e=>({reason:e.code||e.message}));
        await arrived.promise;
        const payload=pair(method).request.payload;change(payload);
        const dispatched=deferred(),original=h.deps.v2Transport;
        h.deps.v2Transport=(...args)=>{dispatched.release();return original(...args);};
        const activity=ipc.callV2(h.deps,method,payload);
        await dispatched.promise;gate.release();
        assert.equal((await pending).reason,'HOST_OR_CONTEXT_CHANGED');
        await activity;
        assert.equal(ipc.callV2.writeSequences.get(h.sessionState),1);
      }finally{gate.release();await h.close();}
    });
    test(`qualification-lane/V2 ${method} pending activity refuses new authority scope`,{timeout:45000},async()=>{
      const h=await qualificationFixture();const entered=deferred(),gate=deferred();
      try {
        const payload=pair(method).request.payload;change(payload);
        const original=h.deps.v2Transport;
        h.deps.v2Transport=(...args)=>{entered.release();return gate.promise.then(()=>original(...args));};
        const activity=ipc.callV2(h.deps,method,payload);
        await entered.promise;
        const scope=await h.prepare().then(()=>({ok:true}),e=>({reason:e.code||e.message}));
        assert.equal(scope.reason,'SESSION_CHANGED');
        assert.equal(h.hits.length,0);
        gate.release();await activity;
      }finally{gate.release();await h.close();}
    });
  }
  test('qualification-lane/V2 cached provider.models stays a display read even with allow_network',{timeout:45000},async()=>{
    const arrived=deferred(),gate=deferred();let held=false;
    const h=await qualificationFixture(async env=>{if(env.method==='host.status'&&!held){held=true;arrived.release();await gate.promise;}});
    try {
      const pending=h.prepare();await arrived.promise;
      const payload=pair('provider.models').request.payload;
      payload.refresh=false;payload.allow_network=true;
      const dispatched=deferred(),original=h.deps.v2Transport;
      h.deps.v2Transport=(...args)=>{dispatched.release();return original(...args);};
      const cached=ipc.callV2(h.deps,'provider.models',payload);
      await dispatched.promise;gate.release();
      assert.equal((await pending).scope.modelRef,'fixture_config_1');
      await cached;
      assert.equal(ipc.callV2.writeSequences.get(h.sessionState)||0,0);
    }finally{gate.release();await h.close();}
  });
  test('qualification-lane/V2 uncertain probe stays fenced through display GET and exact replay',{timeout:45000},async()=>{
    const h=await qualificationFixture();
    try {
      const payload=pair('provider.probe').request.payload;
      const original=h.deps.v2Transport;let attempted;
      h.deps.v2Transport=async(...args)=>{attempted=args[2];throw Error('fixture transport interruption');};
      const uncertain=await ipc.callV2(h.deps,'provider.probe',payload);
      assert.equal(uncertain.reason,'TRANSPORT_FAILURE');
      h.deps.v2Transport=original;
      const display=await ipc.callV2(h.deps,'session.get',{});
      assert.equal(display.completed,true);
      assert.equal((await h.prepare().then(()=>({ok:true}),e=>({reason:e.code||e.message}))).reason,'SESSION_CHANGED');
      const replay=await ipc.callV2(h.deps,'provider.probe',payload);
      assert.equal(replay.completed,true,JSON.stringify(replay));
      assert.equal(h.observations.http.at(-1).raw.toString('utf8'),exact.stringify(attempted));
      assert.equal((await h.prepare()).scope.modelRef,'fixture_config_1');
    }finally{await h.close();}
  });
  test('qualification-lane/V2 acknowledged probe survives display GET until exact replay',{timeout:45000},async()=>{
    let probes=0;
    const h=await qualificationFixture(async()=>{},{modifyResponse:(env,response)=>{
      if(env.method==='provider.probe' && ++probes===1)
        Object.assign(response,pair('provider.probe','ACKNOWLEDGED').response,{command_id:env.command_id,session_id:env.session_id});
    }});
    try {
      const payload=pair('provider.probe').request.payload;
      const acknowledged=await ipc.callV2(h.deps,'provider.probe',payload);
      assert.equal(acknowledged.protocol_status,'ACKNOWLEDGED');
      assert.equal((await ipc.callV2(h.deps,'session.get',{})).completed,true);
      assert.equal((await h.prepare().then(()=>({ok:true}),e=>({reason:e.code||e.message}))).reason,'SESSION_CHANGED');
      const replay=await ipc.callV2(h.deps,'provider.probe',payload);
      assert.equal(replay.completed,true,JSON.stringify(replay));
      const probesSent=h.observations.http.filter(row=>JSON.parse(row.raw).method==='provider.probe');
      assert.equal(probesSent.length,2);
      assert.deepEqual(probesSent[1].raw,probesSent[0].raw);
      assert.equal((await h.prepare()).scope.modelRef,'fixture_config_1');
    }finally{await h.close();}
  });
  test('qualification-lane/R16 Main writer and model checks stay enforced',{timeout:45000},async()=>{
    const h=await qualificationFixture(async()=>{},{modifyResponse:(env,response)=>{
      if(env.method==='session.get')response.result.writer.client_id='foreign';
    }});try{
      const refused=await h.prepare().then(()=>({ok:true}),e=>({reason:e.code||e.message}));
      assert.equal(refused.reason,'WRITE_OWNER_REQUIRED');
      assert.deepEqual(h.hits,['session.get']);
    }finally{await h.close();}
  });
  test('qualification-lane/R16 unavailable model remains refused',{timeout:45000},async()=>{
    const h=await qualificationFixture(async()=>{},{modifyResponse:(env,response)=>{
      if(env.method==='session.get')response.result.model_config_ref='missing-model';
    }});try{
      const refused=await h.prepare().then(()=>({ok:true}),e=>({reason:e.code||e.message}));
      assert.equal(refused.reason,'SESSION_MODEL_UNAVAILABLE');
      assert.deepEqual(h.hits,['session.get','host.status']);
    }finally{await h.close();}
  });
  test('qualification-lane/R17 renderer body cannot select authority lane',{timeout:45000},async()=>{
    const h=await qualificationFixture();const handlers=new Map();
    ipc.registerV2({handle:(channel,handler)=>handlers.set(channel,handler)},h.deps);
    try{
      const forged={readPurpose:'qualification-authority-read',readLane:'authority',context:h.qualificationContext()};
      const result=await handlers.get('ros:v2:session.get')({},forged);
      assert.match(result.reason,/^(UNEXPECTED_PAYLOAD_KEYS|INVALID_REQUEST_SCHEMA)/);
      assert.equal(h.observations.http.length,0);
      assert.equal(handlers.has('ros:v2:qualification:authority'),false);
    }finally{await h.close();}
  });
  test('qualification-lane/R19 CANCEL reservation fences pending Main scope',{timeout:45000},async()=>{
    const arrived=deferred(),gate=deferred();let held=false;
    const h=await qualificationFixture(async env=>{if(env.method==='host.status'&&!held){held=true;arrived.release();await gate.promise;}});
    try{
      const pending=h.prepare().then(()=>({ok:true}),e=>({reason:e.code||e.message}));await arrived.promise;
      const queued=deferred(),original=h.deps.v2Transport;
      h.deps.v2Transport=(...args)=>{queued.release();return original(...args);};
      const cancelPromise=ipc.callV2(h.deps,'session.control',pair('session.control').request.payload);
      await queued.promise;gate.release();
      const [scope,cancel]=await Promise.all([pending,cancelPromise]);
      assert.equal(scope.reason,'HOST_OR_CONTEXT_CHANGED');
      assert.equal(cancel.completed,true,JSON.stringify(cancel));
      assert.deepEqual(h.hits,['session.get','host.status','session.control']);
      assert.equal(h.observations.http.filter(row=>JSON.parse(row.raw).method==='session.control').length,1);
    }finally{gate.release();await h.close();}
  });
  test('qualification-lane/R20 Main host quiesce blocks completion',{timeout:45000},async()=>{
    const arrived=deferred(),gate=deferred();let held=false;
    const h=await qualificationFixture(async env=>{if(env.method==='host.status'&&!held){held=true;arrived.release();await gate.promise;}});
    try{
      const pending=h.prepare().then(()=>({ok:true}),e=>({reason:e.code||e.message}));await arrived.promise;
      h.machine.state='STOPPING';gate.release();const result=await pending;
      assert.equal(result.reason,'MANAGEMENT_LINK_UNAVAILABLE');assert.deepEqual(h.hits,['session.get','host.status']);
    }finally{gate.release();await h.close();}
  });
  test('qualification-lane/R20 actual control process replacement blocks completion',{timeout:45000},async()=>{
    const arrived=deferred(),gate=deferred();let held=false;
    const h=await qualificationFixture(async env=>{if(env.method==='host.status'&&!held){held=true;arrived.release();await gate.promise;}});
    try{
      const pending=h.prepare().then(()=>({ok:true}),e=>({reason:e.code||e.message}));await arrived.promise;
      h.machine.observe=pid=>({PID:pid,CreatedNS:'replacement',ImageSHA256:'b'.repeat(64)});
      gate.release();const result=await pending;
      assert.equal(result.reason,'CONTROL_PROCESS_CHANGED');
      assert.deepEqual(h.hits,['session.get','host.status']);
    }finally{gate.release();await h.close();}
  });
}

function negativeResource(mode) {
  const original=process.env.RESEARCHOS_DESKTOP_WIRE_ROOT;assert(original);
  const parent=process.env.RESEARCHOS_DESKTOP_CASE_RECEIPT;assert(parent);
  fs.mkdirSync(parent,{recursive:true});
  const stageFile=path.join(parent,'negative-stage-'+crypto.randomUUID()+'.jsonl');
  const stage=(step,extra={})=>fs.appendFileSync(stageFile,JSON.stringify({step,at:new Date().toISOString(),...extra})+'\n');
  const fixtureParent=path.resolve(ROOT,'.local/desktop-wire-negative');
  assert(fixtureParent.startsWith(ROOT+path.sep));fs.mkdirSync(fixtureParent,{recursive:true});
  const root=path.join(fixtureParent,crypto.randomUUID());fs.mkdirSync(root);
  stage('exclusive-short-root',{root,original,root_length:root.length,original_length:original.length});
  const copyPublic=(source,target)=>{const stat=fs.lstatSync(source);assert(!stat.isSymbolicLink());if(stat.isDirectory()){fs.mkdirSync(target);for(const name of fs.readdirSync(source))copyPublic(path.join(source,name),path.join(target,name));}else{assert(stat.isFile());fs.writeFileSync(target,fs.readFileSync(source),{flag:'wx'});}};
  for(const name of ['main','preload','resources','package.json']) {
    stage('copy-before',{name});copyPublic(path.join(original,name),path.join(root,name));stage('copy-after',{name});
  }
  const dp=path.join(root,'resources/client-wire/descriptor.json');
  const descriptor=JSON.parse(fs.readFileSync(dp,'utf8'));
  stage('descriptor-read',{descriptor_path:dp});
  const exe=path.join(root,'resources/client-wire/researchos-client-wire-validator.exe');
  const sum=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
  if(mode==='missing')fs.renameSync(exe,exe+'.held-original');
  else if(mode==='digest')fs.appendFileSync(exe,'public-negative');
  else if(mode==='alias') {
    const originalDirectory=path.dirname(exe),target=originalDirectory+'-held-original';
    fs.renameSync(originalDirectory,target);fs.symlinkSync(target,originalDirectory,'junction');
  } else if(mode==='descriptor') {descriptor.schema_sha256_pair[0]='0'.repeat(64);fs.writeFileSync(dp,JSON.stringify(descriptor));}
  else if(mode==='module-drift')fs.appendFileSync(path.join(root,'main/lib/v2.js'),'\n// public negative drift\n');
  else {
    const fixture=descriptor.qualification_fixture_binary;
    assert.equal(fixture.mode,'PUBLIC_SYNTHETIC_NEGATIVE_ONLY');assert.equal(sum(fixture.path),fixture.sha256);
    fs.writeFileSync(exe,fs.readFileSync(fixture.path));descriptor.binary_sha256=sum(exe);descriptor.binary_bytes=fs.statSync(exe).size;
    fs.writeFileSync(dp,JSON.stringify(descriptor));fs.writeFileSync(path.join(path.dirname(exe),'fixture-mode.txt'),mode);
  }
  stage('negative-ready',{mode});
  return root;
}
async function negativeChild(mode, expected, unreaped=false) {
  const appRoot=negativeResource(mode),p=pair('host.status');
  const h=await harness(()=>{throw Error('negative preflight must produce zero POST')},{appRoot});
  const started=Date.now();
  try {
    const result=await h.transport('POST',h.url+'/v2/command',p.request,{});
    assert.equal(result.ok,false);if(expected)assert.equal(result.reason,expected,exact.display(result));
    assert.equal(h.observations.http.length,0);
    if(unreaped){assert(h.observations.children[0].facts.cleanupUnconfirmed);
      const next=await h.transport('POST',h.url+'/v2/command',p.request,{});assert.equal(next.ok,false);assert.equal(h.observations.children.length,1);
      while(h.observations.cleanup.length===0&&Date.now()-started<16000)await new Promise(r=>setTimeout(r,50));
      assert.equal(h.observations.cleanup.length,1);assert(h.observations.cleanup[0].facts.closed);assert(h.observations.cleanup[0].facts.stdoutClosed&&h.observations.cleanup[0].facts.stderrClosed);
    } else for(const child of h.observations.children)assert(child.facts.exited&&child.facts.closed&&child.facts.stdoutClosed&&child.facts.stderrClosed);
  } finally {await h.close();}
}
const negativeCases={
 'B-truncated/child':()=>negativeChild('truncated','PRIVATE_CORRELATION'),
 'B-binary/missing':()=>negativeChild('missing'),
 'B-binary/digest':()=>negativeChild('digest','VALIDATOR_BINARY_DIGEST'),
 'B-binary/alias':()=>negativeChild('alias','VALIDATOR_RESOURCE_ALIAS'),
 'B-binary/descriptor':()=>negativeChild('descriptor','VALIDATOR_DESCRIPTOR'),
 'B-binary/module-drift':()=>negativeChild('module-drift','VALIDATOR_MODULE_DIGEST'),
 'B-binary/actual-dev-root':()=>responseCase(r=>({body:r}),'VALID'),
 'B-correlation/version':()=>negativeChild('version','PRIVATE_CORRELATION'),
 'B-correlation/nonce':()=>negativeChild('nonce','PRIVATE_CORRELATION'),
 'B-correlation/request-digest':()=>negativeChild('request-digest','PRIVATE_CORRELATION'),
 'B-correlation/response-digest':()=>negativeChild('response-digest','PRIVATE_CORRELATION'),
 'B-correlation/http-status':()=>negativeChild('http-status','PRIVATE_CORRELATION'),
 'B-correlation/phase':()=>negativeChild('phase','PRIVATE_CORRELATION'),
 'B-correlation/two-values':()=>negativeChild('two-values','PRIVATE_CORRELATION'),
 'B-timeout/deadline-reap':()=>negativeChild('hang','VALIDATOR_TIMEOUT'),
 'B-timeout/unreaped-blocks':()=>negativeChild('unreaped','VALIDATOR_TIMEOUT',true),
 'B-timeout/nonzero':()=>negativeChild('nonzero','VALIDATOR_EXIT'),
 'B-timeout/stderr-cap':()=>negativeChild('stderr-cap','LOCAL_RESOURCE_LIMIT'),
 'capacity/output-cap':()=>negativeChild('output-cap','LOCAL_RESOURCE_LIMIT'),
 'lifecycle/request-timeout':()=>negativeChild('hang','VALIDATOR_TIMEOUT'),
};
if(direct && !process.versions.electron)for(const [name,run] of Object.entries(negativeCases))test('desktop-http/'+name,{timeout:45000},run);

if(direct && !process.versions.electron) {
  test('desktop-http/revision/ack-before-concurrent-get',{timeout:45000},async()=>{
    const p=pair('session.attach');
    const state={projectId:p.request.project_id,sessionId:p.request.session_id,expectedRevision:7,writerEpoch:2,writerClientId:'foreign',writerExpiresAt:'2099-01-01T00:00:00Z'};
    const advanced=snapshot({revision:8,writer:{client_id:'desktop-shell',epoch:3,expires_at:'2099-01-01T00:00:00Z'}});
    let gotA,releaseA,enqueuedB;
    const arrivedA=new Promise(resolve=>gotA=resolve),allowA=new Promise(resolve=>releaseA=resolve),queuedB=new Promise(resolve=>enqueuedB=resolve);
    const transitions=[];
    const h=await harness(async(raw,index)=>{
      const env=JSON.parse(raw.toString('utf8'));
      if(index===1){gotA();await allowA;}
      const response=index===1?pair(env.method,'ACKNOWLEDGED').response:pair(env.method).response;
      Object.assign(response,{command_id:env.command_id,session_id:env.session_id});
      if(index!==1){response.revision=8;if(env.method==='session.get')response.result=advanced;else if(env.method==='session.attach')response.result={snapshot:advanced,write_owner_acquired:true};else response.result.snapshot=advanced;}
      return {body:response};
    },{state});
    const real=h.deps.v2Transport;h.deps.v2Transport=(...args)=>{if(args[2].method==='session.get')enqueuedB();return real(...args);};
    const args={after_sequence:3,request_write_owner:true};
    try {
      const a=ipc.callV2(h.deps,'session.attach',args);await arrivedA;
      const b=ipc.callV2(h.deps,'session.get',{});await queuedB;releaseA();
      const ack=await a;assert.equal(ack.protocol_status,'ACKNOWLEDGED');assert.equal(ack.completed,false);
      assert.equal(state.pendingOperation.method,'session.attach');transitions.push({stage:'ACK',command:state.pendingOperation.commandId,revision:state.expectedRevision,epoch:state.writerEpoch});
      const read=await b;assert.equal(read.completed,true);assert.equal(state.expectedRevision,7);assert.equal(state.writerEpoch,2);assert.equal(state.writerClientId,'foreign');
      assert.equal(state.pendingOperation.commandId,JSON.parse(h.observations.http[0].raw).command_id);
      const childrenBefore=h.observations.children.length;
      const blocked=await ipc.callV2(h.deps,'session.send',{text:'blocked',attachment_artifact_ids:[],delivery:'NORMAL'});
      assert.equal(blocked.reason,'COMMAND_PENDING');assert.equal(h.observations.http.length,2);assert.equal(h.observations.children.length,childrenBefore);
      const complete=await ipc.callV2(h.deps,'session.attach',args);assert.equal(complete.completed,true);
      assert.deepEqual(h.observations.http[0].raw,h.observations.http[2].raw);assert.equal(state.pendingOperation,undefined);
      assert.equal(state.expectedRevision,8);assert.equal(state.writerEpoch,3);assert.equal(state.writerClientId,'desktop-shell');
      transitions.push({stage:'original-COMPLETED',revision:state.expectedRevision,epoch:state.writerEpoch});
      const sent=await ipc.callV2(h.deps,'session.send',{text:'one dependent send',attachment_artifact_ids:[],delivery:'NORMAL'});assert.equal(sent.completed,true);
      assert.equal(h.observations.http.length,4);assert.equal(h.observations.children.length,8);
      fs.mkdirSync(process.env.RESEARCHOS_DESKTOP_CASE_RECEIPT,{recursive:true});
      fs.writeFileSync(path.join(process.env.RESEARCHOS_DESKTOP_CASE_RECEIPT,'revision-transitions.json'),JSON.stringify(transitions,null,2));
    } finally {releaseA();await h.close();}
  });
  test('desktop-http/revision/private-six-key-types',{timeout:45000},async()=>{
    const request=exact.stringify(pair('host.status').request);
    const aliased=await purePacket(request,'','REQUEST',null,p=>{p.Schema=p.schema;delete p.schema;});
    const nullString=await purePacket(request,'','REQUEST',null,p=>{p.response_raw_base64=null;});
    for(const value of [aliased,nullString]){assert.equal(value.outcome,'REFUSED');assert.equal(value.reason,'PRIVATE_PACKET');}
  });
  test('desktop-http/revision/private-json-whitespace',{timeout:45000},()=>negativeChild('nbsp','PRIVATE_JSON'));
}


async function rendererProcess(kind) {
  const {spawn}=await import('node:child_process');
  const executable=process.env.RESEARCHOS_DESKTOP_ELECTRON;assert(executable);
  const args=[fileURLToPath(import.meta.url),'--renderer-case='+kind];
  const temporary=path.resolve(ROOT,'.local/desktop-electron-temp',crypto.randomUUID());assert(temporary.startsWith(ROOT+path.sep));fs.mkdirSync(temporary,{recursive:true});
  const env={SystemRoot:process.env.SystemRoot,WINDIR:process.env.WINDIR||process.env.SystemRoot,TEMP:temporary,TMP:temporary,
    RESEARCHOS_DESKTOP_WIRE_ROOT:process.env.RESEARCHOS_DESKTOP_WIRE_ROOT,RESEARCHOS_DESKTOP_CASE_RECEIPT:process.env.RESEARCHOS_DESKTOP_CASE_RECEIPT};
  const child=spawn(executable,args,{cwd:ROOT,env,windowsHide:true,shell:false,stdio:['ignore','pipe','pipe']});
  const out=[],err=[];let exited=false,stdoutClosed=false,stderrClosed=false;
  child.stdout.on('data',b=>out.push(b));child.stderr.on('data',b=>err.push(b));child.stdout.on('close',()=>stdoutClosed=true);child.stderr.on('close',()=>stderrClosed=true);child.on('exit',()=>exited=true);
  const timer=setTimeout(()=>child.kill(),85000);
  const code=await new Promise((resolve,reject)=>{child.on('error',reject);child.on('close',resolve);});clearTimeout(timer);
  const evidence=process.env.RESEARCHOS_DESKTOP_CASE_RECEIPT;assert(evidence);fs.mkdirSync(evidence,{recursive:true});
  fs.writeFileSync(path.join(evidence,'electron.stdout'),Buffer.concat(out));fs.writeFileSync(path.join(evidence,'electron.stderr'),Buffer.concat(err));
  fs.writeFileSync(path.join(evidence,'electron.invocation.json'),JSON.stringify({actualargv:[executable,...args],cwd:ROOT,pid:child.pid,exit:code,exited,stdoutClosed,stderrClosed,mode:'ACTUAL_OFFSCREEN_PUBLIC_FIXTURE',external:0,model:0},null,2));
  assert.equal(code,0,Buffer.concat(err).toString('utf8')+Buffer.concat(out).toString('utf8'));assert(exited&&stdoutClosed&&stderrClosed);
}
if(direct&&!process.versions.electron) {
  test('desktop-renderer/react-roundtrip',{timeout:90000},()=>rendererProcess('react'));
  test('desktop-renderer/legacy-roundtrip',{timeout:90000},()=>rendererProcess('legacy'));
}
async function runActualRenderer(kind) {
  const {app,BrowserWindow,ipcMain,protocol,session}=require('electron');
  assert(['react','legacy'].includes(kind));
  const receipt=process.env.RESEARCHOS_DESKTOP_CASE_RECEIPT;assert(receipt);fs.mkdirSync(receipt,{recursive:true});
  const userDataParent=path.resolve(ROOT,'.local/desktop-renderer-public');assert(userDataParent.startsWith(ROOT+path.sep));fs.mkdirSync(userDataParent,{recursive:true});
  const userData=path.join(userDataParent,crypto.randomUUID());fs.mkdirSync(userData);fs.writeFileSync(path.join(receipt,'owned-profile-path.json'),JSON.stringify({path:userData,exclusive:true,private_user_profile:false}));
  app.setPath('userData',userData);app.disableHardwareAcceleration();app.commandLine.appendSwitch('disable-background-networking');
  protocol.registerSchemesAsPrivileged([{scheme:'ros-app',privileges:{standard:true,secure:true,supportFetchAPI:true,stream:true}}]);
  await app.whenReady();
  const appRoot=process.env.RESEARCHOS_DESKTOP_WIRE_ROOT;assert(appRoot);
  const large=9007199254740993n,prior=large-1n;let eventReads=0;
  const snap=snapshot({revision:large,event_sequence:large,earliest_event_sequence:large,goal_id:null,goal_status:null,active_run_id:null,run_status:null,pending_permissions:[],writer:{client_id:'desktop-shell',epoch:large,expires_at:'2099-01-01T00:00:00Z'}});
  const state={projectId:snap.project_id,sessionId:snap.session_id,expectedRevision:null,writerEpoch:null};
  const h=await harness((raw,index)=>{
    assert(index<=8,'renderer HTTP ceiling exceeded');
    const req=JSON.parse(raw.toString('utf8'));const p=pair(req.method,req.method==='session.send'?'ACKNOWLEDGED':'COMPLETED');
    const res=p.response;res.command_id=req.command_id;res.session_id=req.session_id;
    if(req.method==='session.get'){res.result=snap;res.revision=large;}
    if(req.method==='session.list')res.result.items=[snap];
    if(req.method==='session.events'){
      eventReads++;res.revision=large;res.result={events:eventReads===1?[{event_id:'public-usage',session_id:snap.session_id,sequence:large,core_build_id:'fixture_build',protocol_version:'researchos-client/2',run_id:null,command_id:null,domain_event_id:null,kind:'USAGE',payload:{ledger_entry_id:'public-ledger',provider_usage_id:null,input_tokens:large,output_tokens:prior,money:null,cost_known:false}}]:[],next_sequence:large,high_watermark:large,has_more:false};
    }
    return {body:res};
  },{state});
  h.deps.contextVerified=true;h.deps.commandIdFor=()=>crypto.randomUUID();
  ipc.registerV2(ipcMain,h.deps);ipc.registerDesktopReview(ipcMain,h.deps);
  for(const channel of ipc.BRIDGE)ipcMain.handle('ros:'+channel,()=>({ok:true,items:[],models:[],sessions:[],workspaces:[],summary:'public unrelated legacy fixture'}));
  ipcMain.handle('ros:desktop:chooseWorkspace',()=>({ok:false,reason:'NOT_REQUESTED_IN_THIS_FIXTURE'}));
  const setup=[];const {staticResponse}=require(path.join(ROOT,'apps/desktop/main/lib/app-protocol.js'));
  protocol.handle('ros-app',request=>{
    const u=new URL(request.url);assert.equal(u.host,'desktop');
    if(!u.pathname.startsWith('/v1/'))return staticResponse(path.resolve(appRoot,'../web/dist'),u.pathname);
    setup.push({url:request.url,method:request.method,mode:'PUBLIC_RENDERER_SETUP_NOT_HTTP_MODEL'});
    if(u.pathname.endsWith('/events/stream'))return new Response('data: {}\n\n',{headers:{'content-type':'text/event-stream'}});
    return Response.json(u.pathname.endsWith('/profile')?{id:snap.project_id,name:'Public Desktop fixture'}:{items:[]});
  });
  session.defaultSession.webRequest.onBeforeRequest((details,callback)=>callback({cancel:!details.url.startsWith('ros-app://desktop/')&&!details.url.startsWith('file://')}));
  let window;
  const consoleRows=[];
  const waitFor=async(expression)=>{const until=Date.now()+20000;while(Date.now()<until){if(await window.webContents.executeJavaScript(expression))return;await new Promise(r=>setTimeout(r,40));}throw Error('renderer condition timeout: '+expression);};
  try {
    window=new BrowserWindow({show:false,width:1200,height:900,webPreferences:{preload:path.join(appRoot,'preload/preload.js'),offscreen:true,contextIsolation:true,nodeIntegration:false,sandbox:true}});
    window.webContents.setWindowOpenHandler(()=>({action:'deny'}));window.webContents.on('console-message',(_e,level,message)=>consoleRows.push({level,message}));
    if(kind==='react')await window.loadURL('ros-app://desktop/p/'+snap.project_id);else await window.loadFile(path.join(appRoot,'main/workbench.html'));
    auditOwnedModules(process.pid,'electron-main');auditOwnedModules(window.webContents.getOSProcessId(),'electron-renderer');
    await waitFor("document.body.textContent.includes('9007199254740993')");
    if(kind==='legacy'){await waitFor("document.getElementById('review-event-list').textContent.includes('9007199254740993')");await window.webContents.executeJavaScript("document.getElementById('review-events').click()");}
    const end=Date.now()+12000;while(eventReads<2&&Date.now()<end)await new Promise(r=>setTimeout(r,40));assert(eventReads>=2);
    const events=h.observations.http.filter(x=>JSON.parse(x.raw).method==='session.events');
    assert.match(events[0].raw.toString(),/"after_sequence":9007199254740992/);assert.match(events[1].raw.toString(),/"after_sequence":9007199254740993/);
    const selector=kind==='react'?'textarea[aria-label="会话消息"]':'#review-message';
    await window.webContents.executeJavaScript(`(()=>{const n=document.querySelector(${JSON.stringify(selector)});const set=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set;set.call(n,'keep public draft');n.dispatchEvent(new Event('input',{bubbles:true}));})()`);
    await waitFor(kind==='react'?"!document.querySelector('.session-composer button[type=submit]').disabled":"!document.getElementById('review-send').disabled");
    await window.webContents.executeJavaScript(kind==='react'?"document.querySelector('.session-composer button[type=submit]').click()":"document.getElementById('review-send').click()");
    await waitFor("document.body.textContent.includes('ACKNOWLEDGED')");
    assert.equal(await window.webContents.executeJavaScript(`document.querySelector(${JSON.stringify(selector)}).value`),'keep public draft');
    assert.equal(state.expectedRevision,large);assert.equal(state.writerEpoch,large);assert.equal(state.pendingOperation.method,'session.send');
    const sent=h.observations.http.filter(x=>JSON.parse(x.raw).method==='session.send');assert.equal(sent.length,1);assert.match(sent[0].raw.toString(),/"expected_revision":9007199254740993/);assert.match(sent[0].raw.toString(),/"writer_epoch":9007199254740993/);
    const count=h.observations.http.length;const blocked=await window.webContents.executeJavaScript("window.researchos.v2['session.update']({title:'must remain pending',archived:false})");assert.equal(blocked.reason,'COMMAND_PENDING');assert.equal(h.observations.http.length,count);
    fs.writeFileSync(path.join(receipt,'renderer-dom.html'),await window.webContents.executeJavaScript('document.documentElement.outerHTML'));
    fs.writeFileSync(path.join(receipt,'renderer-facts.json'),JSON.stringify({kind,setup,console:consoleRows,actualElectron:process.versions.electron,http:h.observations.http.length,eventReads,external:0,model:0,pass:true},null,2));
    console.log('DESKTOP_RENDERER_PASS '+kind);
  } finally {if(window&&!window.isDestroyed())window.destroy();await h.close();protocol.unhandle('ros-app');}
}
if(direct&&process.versions.electron) {
  const kind=process.argv.find(x=>x.startsWith('--renderer-case='))?.split('=')[1];
  runActualRenderer(kind).then(()=>require('electron').app.exit(0)).catch(error=>{console.error(error.stack);require('electron').app.exit(1);});
}
