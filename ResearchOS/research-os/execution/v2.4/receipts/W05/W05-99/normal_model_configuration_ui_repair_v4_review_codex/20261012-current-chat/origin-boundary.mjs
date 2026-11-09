import fs from 'node:fs'
import path from 'node:path'
import assert from 'node:assert/strict'
import crypto from 'node:crypto'
import {fileURLToPath,pathToFileURL} from 'node:url'
import {createRequire} from 'node:module'
const OUT=path.dirname(fileURLToPath(import.meta.url)),ROOT=path.resolve(OUT,'../../../../../../..'),WT=path.join(ROOT,'.local/worktrees/w05-normal-model-ui-repair-v4-20261012')
const require=createRequire(import.meta.url),ipc=require(path.join(WT,'.local/v4-bound-build-6/apps/desktop/main/lib/ipc.js'))
const {pair,harness}=await import(pathToFileURL(path.join(WT,'tests/ui/desktop/http-wire-boundary.test.mjs')))
const facts=[],expected=crypto.createHash('sha256').update(JSON.stringify(['host-aaaaaaaaaaaa','fixture-data-root'])).digest('hex')
async function check(name,respond,run){process.env.RESEARCHOS_DESKTOP_CASE_RECEIPT=path.join(OUT,'origin-boundary-http',name);const h=await harness(respond,{state:{projectId:'fixture_project',sessionId:null,expectedRevision:null,writerEpoch:null}});try{facts.push({name,...await run(h)})}finally{await h.close()}}
await check('renderer-origin-injection-refused',()=>{throw Error('must not post')},async h=>{
 const payload={...pair('host.configure').request.payload,local_host_origin:'f'.repeat(64)}
 const reply=await ipc.callV2(h.deps,'host.configure',payload)
 assert.equal(reply.ok,false);assert.equal(reply.dispatch_state,'NOT_SENT');assert.equal(reply.local_host_origin,expected);assert.equal(h.observations.http.length,0)
 return {reply,passed:true}
})
await check('remote-top-level-origin-injection-refused',raw=>{const env=JSON.parse(raw),reply=pair('host.status').response;reply.command_id=env.command_id;reply.local_host_origin='f'.repeat(64);return {body:reply}},async h=>{
 const reply=await ipc.callV2(h.deps,'host.status',{})
 assert.equal(reply.ok,false);assert.equal(reply.local_host_origin,expected);assert.equal(h.observations.http.length,1)
 return {reply,passed:true}
})
await check('data-root-only-change-blocks-replay',raw=>{const env=JSON.parse(raw),reply=pair('host.configure','ACKNOWLEDGED').response;reply.command_id=env.command_id;return {body:reply}},async h=>{
 const payload=pair('host.configure').request.payload,ack=await ipc.callV2(h.deps,'host.configure',payload)
 h.deps.fsImpl.readFileSync=()=>JSON.stringify({url:h.url,pid:9999,data_dir:'different-data-root',host_instance_id:'host-aaaaaaaaaaaa'})
 const replay=await ipc.callV2(h.deps,'host.configure',payload)
 assert.equal(replay.reason,'HOST_CHANGED_PENDING');assert.equal(replay.local_host_origin,ack.local_host_origin);assert.notEqual(replay.dispatch_state,'NOT_SENT');assert.equal(h.observations.http.length,1)
 return {ack,replay,passed:true}
})
await check('different-host-same-data-root-blocks-replay',raw=>{const env=JSON.parse(raw),reply=pair('host.configure','ACKNOWLEDGED').response;reply.command_id=env.command_id;return {body:reply}},async h=>{
 const payload=pair('host.configure').request.payload,ack=await ipc.callV2(h.deps,'host.configure',payload)
 h.deps.fsImpl.readFileSync=()=>JSON.stringify({url:h.url,pid:9999,data_dir:'fixture-data-root',host_instance_id:'host-bbbbbbbbbbbb'})
 const replay=await ipc.callV2(h.deps,'host.configure',payload)
 assert.equal(replay.reason,'HOST_CHANGED_PENDING');assert.equal(replay.local_host_origin,ack.local_host_origin);assert.notEqual(replay.dispatch_state,'NOT_SENT');assert.equal(h.observations.http.length,1)
 return {ack,replay,passed:true}
})
fs.writeFileSync(path.join(OUT,'origin-boundary-results.json'),JSON.stringify({model_calls:0,external_calls:0,facts},null,2)+'\n')
console.log(JSON.stringify({checks:facts.length,passed:facts.filter(x=>x.passed).length}))
