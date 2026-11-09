import fs from 'node:fs'
import path from 'node:path'
import assert from 'node:assert/strict'
import {fileURLToPath,pathToFileURL} from 'node:url'
import {createRequire} from 'node:module'
const OUT=path.dirname(fileURLToPath(import.meta.url)),ROOT=path.resolve(OUT,'../../../../../../..'),WT=path.join(ROOT,'.local/worktrees/w05-normal-model-ui-repair-v5-20261012'),BUILD=path.join(WT,'.local/v5-bound-build-1')
const require=createRequire(import.meta.url),ipc=require(path.join(BUILD,'apps/desktop/main/lib/ipc.js'))
const {pair,harness}=await import(pathToFileURL(path.join(WT,'tests/ui/desktop/http-wire-boundary.test.mjs')))
const facts=[]
for(const phase of ['credential','response']){
 process.env.RESEARCHOS_DESKTOP_CASE_RECEIPT=path.join(OUT,'status-barrier-http',phase)
 let discovery,sequence=0,release,arrived,configureMode='ACKNOWLEDGED';const ready=new Promise(resolve=>arrived=resolve)
 const h=await harness(async raw=>{
  const env=JSON.parse(raw),reply=pair(env.method,env.method==='host.configure'?configureMode:'COMPLETED').response
  reply.command_id=env.command_id;reply.session_id=env.session_id
  if(env.method==='host.status'){arrived();await new Promise(resolve=>release=resolve)}
  if(env.method==='host.configure'&&configureMode==='COMPLETED')Object.assign(reply.result,env.payload)
  return {body:reply}
 },{state:{projectId:'fixture_project',sessionId:null,expectedRevision:null,writerEpoch:null}})
 discovery={url:h.url,pid:1,data_dir:'root-A',host_instance_id:'host-aaaaaaaaaaaa'}
 h.deps.fsImpl.readFileSync=()=>JSON.stringify(discovery);h.deps.commandIdFor=method=>'barrier-'+(++sequence)+'-'+method
 try{
  const payload=pair('host.configure').request.payload,ack=await ipc.callV2(h.deps,'host.configure',payload)
  const original=h.deps.sessionState.pendingOperation
  assert.equal(ack.protocol_status,'ACKNOWLEDGED');assert.equal(original.acknowledged,true);assert.equal(original.possiblySent,true)
  if(phase==='credential')h.deps.credentialFor=async()=>{discovery={...discovery,host_instance_id:'host-bbbbbbbbbbbb',data_dir:'root-B'};return 'public-fixture-only'}
  const pendingStatus=ipc.callV2(h.deps,'host.status',{})
  if(phase==='response'){await ready;discovery={...discovery,host_instance_id:'host-bbbbbbbbbbbb',data_dir:'root-B'};release()}
  const status=await pendingStatus
  assert.equal(status.reason,phase==='credential'?'HOST_CHANGED_BEFORE_SEND':'HOST_CHANGED_DURING_STATUS')
  assert.equal(h.deps.sessionState.pendingOperation,original)
  assert.equal(ipc.callV2.lifetimes.get(h.deps.sessionState).get(original.commandId),original)
  assert.equal(original.acknowledged,true);assert.equal(original.possiblySent,true)
  assert.equal(status.result,undefined)
  const wrong=await ipc.callV2(h.deps,'host.configure',payload)
  assert.equal(wrong.reason,'HOST_CHANGED_PENDING');assert.notEqual(wrong.dispatch_state,'NOT_SENT')
  h.deps.credentialFor=async()=> 'public-fixture-only'
  discovery={url:h.url,pid:9999,data_dir:'root-A',host_instance_id:'host-aaaaaaaaaaaa'};configureMode='COMPLETED'
  const done=await ipc.callV2(h.deps,'host.configure',payload)
  assert.equal(done.completed,true);assert.equal(done.local_host_origin,ack.local_host_origin)
  const requests=h.observations.http.map(x=>JSON.parse(x.raw)).filter(x=>x.method==='host.configure')
  assert.equal(requests.length,2);assert.deepEqual(requests[0],requests[1])
  facts.push({phase,passed:true,ack,status,wrong,done,requests})
 }finally{if(release)release();await h.close()}
}
fs.writeFileSync(path.join(OUT,'status-barrier-results.json'),JSON.stringify({model_calls:0,external_calls:0,facts},null,2)+'\n')
console.log(JSON.stringify({checks:facts.length,passed:facts.filter(x=>x.passed).length}))
