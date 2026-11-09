import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
const require=createRequire(import.meta.url);
const root='D:/作品集/ResearchOS/research-os';
const pkg='C:/Users/yqyyds/.codex/researchos-resource-cache/normal-first-use-combined-c381-20261012/apps/desktop';
const out=path.dirname(decodeURIComponent(new URL(import.meta.url).pathname.slice(1)));
process.env.RESEARCHOS_DESKTOP_WIRE_ROOT=pkg;
process.env.RESEARCHOS_DESKTOP_CASE_RECEIPT=path.join(out,'bound-fixture-raw-02');
const {harness,pair,snapshot}=await import(pathToFileURL(path.join(root,'tests/ui/desktop/http-wire-boundary.test.mjs')).href);
const ipc=require(path.join(root,'apps/desktop/main/lib/ipc.js'));
const source=fs.readFileSync(path.join(root,'apps/desktop/main/main.js'),'utf8');
const begin=source.indexOf('async function prepareQualificationScope() {');
const end=source.indexOf('\nconst codingDirectories',begin);
assert(begin>=0 && end>begin);
const exactFunction=source.slice(begin,end);
const bindings=['main/main.js','main/lib/ipc.js','main/lib/http-wire.js'].map(rel=>{
 const sourceBytes=fs.readFileSync(path.join(root,'apps/desktop',rel));
 const shippedBytes=fs.readFileSync(path.join(pkg,rel));
 assert(sourceBytes.equals(shippedBytes));
 return {path:rel,sha256:crypto.createHash('sha256').update(sourceBytes).digest('hex')};
});
async function scenario(interleave){
 const snap=snapshot();
 const state={projectId:snap.project_id,sessionId:snap.session_id,expectedRevision:snap.revision,writerEpoch:snap.writer.epoch,writerClientId:snap.writer.client_id,writerExpiresAt:snap.writer.expires_at,selectionGeneration:0,authorityGeneration:0};
 const initial=JSON.stringify(state);
 let announce,release;
 const arrived=new Promise(resolve=>announce=resolve);
 const gate=new Promise(resolve=>release=resolve);
 const timeline=[];
 const h=await harness(async raw=>{
  const env=JSON.parse(raw);
  timeline.push({phase:'public-fixture-http',method:env.method,ticket:ipc.callV2.sequences.get(state)});
  if(env.method==='host.status'&&interleave){announce();await gate;}
  const response=pair(env.method).response;
  response.command_id=env.command_id;
  return {body:response};
 },{state});
 const context=()=>JSON.stringify([state.projectId,state.sessionId,String(state.expectedRevision),String(state.writerEpoch),state.writerClientId,state.writerExpiresAt,state.selectionGeneration,state.authorityGeneration]);
 const machine={hostId:'host-aaaaaaaaaaaa',currentHost:()=>({data_dir:'fixture-data-root'})};
 const sandbox={v2Deps:{...h.deps,contextVerified:true},sessionState:state,desktopManagement:machine,qualificationContext:context,ipc,crypto,Date,JSON,String,Object};
 vm.createContext(sandbox);
 vm.runInContext(exactFunction+'\nthis.frozenPrepare=prepareQualificationScope;',sandbox);
 let prep,poll;
 try{
  const original=sandbox.frozenPrepare().then(result=>({ok:true,result}),error=>({ok:false,reason:error.code||error.message}));
  if(interleave){
   await arrived;
   const hostTicket=ipc.callV2.sequences.get(state);
   poll=ipc.callV2(h.deps,'session.events',{after_sequence:4,limit:200});
   const deadline=Date.now()+5000;
   while(ipc.callV2.sequences.get(state)===hostTicket && Date.now()<deadline)await new Promise(resolve=>setTimeout(resolve,10));
   assert.equal(ipc.callV2.sequences.get(state),hostTicket+1);
   timeline.push({phase:'background-events-queued',hostTicket,currentTicket:ipc.callV2.sequences.get(state)});
   release();
  }
  prep=await original;
  const events=poll?await poll:null;
  assert.equal(JSON.stringify(state),initial);
  if(interleave){assert.equal(prep.reason,'HOST_OR_CONTEXT_CHANGED');assert.equal(events.completed,true);}
  else{assert.equal(prep.ok,true,JSON.stringify(prep));assert.equal(prep.result.scope.modelRef,'fixture_config_1');}
  return {scenario:interleave?'host-status-overlapped-by-background-event-read':'isolated-qualification-scope',prep:prep.ok?{ok:true,modelRef:prep.result.scope.modelRef}:prep,events:events?{ok:events.ok,completed:events.completed,reason:events.reason||null}:null,stateUnchanged:true,timeline,actual_http_count:h.observations.http.length,actual_validator_children:h.observations.children.length,real_models:0,real_tools:0,production_host_requests:0};
 }finally{release?.();await h.close();}
}
const scenarios=[];
for(const interleave of [false,true])scenarios.push(await scenario(interleave));
const record={schema:'researchos.qualification-read-interleaving-diagnostic/1',at:new Date().toISOString(),source_scope_function_sha256:crypto.createHash('sha256').update(exactFunction).digest('hex'),bindings,scenarios,source_mutations:0,production_gui_actions:0,production_host_requests:0,model_calls:0,tool_calls:0,formal_increment:0,scope:'Public synthetic local HTTP fixture plus unchanged approved validator; not production qualification or acceptance'};
const resultPath=path.join(out,'interleaving-diagnostic-result-02.json');
fs.writeFileSync(resultPath,JSON.stringify(record,null,2),{flag:'wx'});
console.log(JSON.stringify({resultPath,sha256:crypto.createHash('sha256').update(fs.readFileSync(resultPath)).digest('hex'),scenarios},null,2));
