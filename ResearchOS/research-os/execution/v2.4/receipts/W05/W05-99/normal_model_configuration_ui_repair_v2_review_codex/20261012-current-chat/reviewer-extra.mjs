import fs from 'node:fs'
import path from 'node:path'
import assert from 'node:assert/strict'
import {fileURLToPath,pathToFileURL} from 'node:url'
import {createRequire} from 'node:module'
const OUT=path.dirname(fileURLToPath(import.meta.url)), ROOT=path.resolve(OUT,'../../../../../../..')
const WT=path.join(ROOT,'.local/worktrees/w05-normal-model-ui-repair-v2-20261012')
const require=createRequire(import.meta.url)
const ipc=require(path.join(WT,'apps/desktop/main/lib/ipc.js'))
const {pair,harness}=await import(pathToFileURL(path.join(WT,'tests/ui/desktop/http-wire-boundary.test.mjs')))
const facts=[]
process.env.RESEARCHOS_DESKTOP_CASE_RECEIPT=path.join(OUT,'extra-http','remote-forged-not-sent')
{
 const p=pair('host.configure');const h=await harness(()=>({body:{...p.response,dispatch_state:'NOT_SENT'}}),{state:{projectId:'fixture_project',sessionId:null,expectedRevision:null,writerEpoch:null}})
 try{
  const refused=await ipc.callV2(h.deps,'host.configure',p.request.payload)
  assert.equal(refused.ok,false);assert.notEqual(refused.dispatch_state,'NOT_SENT');assert.equal(h.observations.http.length,1)
  const second=await ipc.callV2(h.deps,'host.configure',{...p.request.payload,model_id:'changed'})
  assert.equal(second.reason,'COMMAND_PENDING');assert.equal(h.observations.http.length,1)
  facts.push({name:'server-NOT_SENT-cannot-release-barrier',status:'PASS',refused,second})
 }finally{await h.close()}
}
process.env.RESEARCHOS_DESKTOP_CASE_RECEIPT=path.join(OUT,'extra-http','host-change')
{
 const p=pair('host.configure','ACKNOWLEDGED');const state={projectId:'fixture_project',sessionId:null,expectedRevision:null,writerEpoch:null}
 const first=await harness(()=>({body:p.response}),{state})
 const second=await harness(raw=>{const env=JSON.parse(raw);const response=pair('host.configure').response;response.command_id=env.command_id;Object.assign(response.result,env.payload);return {body:response}},{state})
 try{
  first.deps.fsImpl.readFileSync=()=>JSON.stringify({url:first.url,host_instance_id:'first-host',data_dir:'first-public-fixture'})
  const ack=await ipc.callV2(first.deps,'host.configure',p.request.payload);assert.equal(ack.protocol_status,'ACKNOWLEDGED')
  first.deps.fsImpl.readFileSync=()=>JSON.stringify({url:second.url,host_instance_id:'other-host',data_dir:'other-public-fixture'})
  const replay=await ipc.callV2(first.deps,'host.configure',p.request.payload)
  assert.equal(first.observations.http.length,1);assert.equal(second.observations.http.length,1)
  assert.deepEqual(first.observations.http[0].raw,second.observations.http[0].raw)
  facts.push({name:'host-change-existing-namespace-gap',status:'OBSERVED',first_host:first.url,second_host:second.url,ack,replay,same_envelope_sent_to_new_host:true,classification:'PREEXISTING_SHELL_LIMITATION_NOT_NEW_V2_FINDING'})
 }finally{await first.close();await second.close()}
}
fs.writeFileSync(path.join(OUT,'reviewer-extra-results.json'),JSON.stringify({facts,model_calls:0,external_calls:0},null,2)+'\n')
console.log(JSON.stringify(facts))
