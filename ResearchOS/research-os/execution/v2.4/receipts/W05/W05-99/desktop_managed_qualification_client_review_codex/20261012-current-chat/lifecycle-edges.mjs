import fs from 'node:fs'
import path from 'node:path'
import assert from 'node:assert/strict'
import {EventEmitter} from 'node:events'
import {fileURLToPath} from 'node:url'
import {createRequire} from 'node:module'
const OUT=path.dirname(fileURLToPath(import.meta.url)),ROOT=path.resolve(OUT,'../../../../../../..'),WT=path.join(ROOT,'.local/worktrees/w05-desktop-managed-qualification-client-20261012')
const BUILD=path.join(WT,'.local/managed-client-bound-final3'),require=createRequire(import.meta.url)
const {createDesktopManagement,observeWindowsProcess,strictJSON}=require(path.join(BUILD,'apps/desktop/main/lib/desktop-management.js'))
const facts=[]
function fixture(name,{expiresSoon=false}={}){
 const dir=path.join(OUT,'lifecycle-fixture',name);fs.mkdirSync(dir,{recursive:true})
 const discoveryFile=path.join(dir,'discovery.json'),hostId='host-aaaaaaaaaaaa',pid=24680
 let context='["project-1","session-1",7,2,1]',statusState='QUALIFIED_PURPOSE_AUTHORIZED',consumed=true
 const identity=pid=>({PID:pid,CreatedNS:String(pid)+'000000000',ImageSHA256:'a'.repeat(64)})
 const discovery={url:'http://127.0.0.1:54321',pid,data_dir:dir,host_instance_id:hostId}
 fs.writeFileSync(discoveryFile,JSON.stringify(discovery))
 const child=new EventEmitter();child.pid=pid;const frames=[]
 const manager=createDesktopManagement({fsImpl:fs,discoveryFile,dataRoot:dir,context:()=>context,observeProcess:identity})
 Object.assign(manager,{state:'READY',child,childExited:false,hostId,identity:identity(pid),parentIdentity:identity(process.pid)})
 manager.exitPromise=new Promise(resolve=>manager.resolveExit=resolve)
 const requestHash='sha256:'+'b'.repeat(64)
 child.stdin={write(bytes,callback){
  const request=JSON.parse(bytes.toString());frames.push({direction:'desktop_to_fixture',raw:bytes.toString()})
  const now=Date.now(),requestBody={request_id:'req-'+name,project_id:'project-1',session_id:'session-1',model_config_ref:'model-1',owner_host:hostId,authorize_purpose:'mu_turn',issued_at:new Date(now-(expiresSoon?59800:1000)).toISOString(),expires_at:new Date(now+(expiresSoon?200:58000)).toISOString()}
  const result=request.operation==='PREPARE'?{state:'AWAITING_CONFIRMATION',request:requestBody,request_hash:requestHash,model_calls:1,tools:[],purpose:'mu_turn',purpose_seconds:600,cost_basis:'UNKNOWN',money:null}
    :request.operation==='STATUS'?{request_id:'req-'+name,request_hash:requestHash,state:statusState,consumed}
    :{state:'QUALIFIED_PURPOSE_AUTHORIZED'}
  const frame={protocol:'researchos-desktop-management/1',message_id:request.message_id,operation:request.operation,host_id:hostId,kind:'RESULT',result}
  setImmediate(()=>{const raw=Buffer.from(JSON.stringify(frame));frames.push({direction:'fixture_to_desktop',raw:raw.toString()});manager.onLine(raw)})
  callback?.();return true
 }}
 const scope={projectId:'project-1',sessionId:'session-1',modelRef:'model-1',model:{provider_id:'fixture',model_id:'no-model-execution'}}
 return {manager,scope,frames,dir,discoveryFile,discovery,setContext:x=>context=x,setStatus:(s,c)=>{statusState=s;consumed=c},context:()=>context}
}
const f=fixture('expired-context',{expiresSoon:true})
await f.manager.prepare(f.scope,f.context())
const original={...f.manager.intent};f.setContext('["project-1","session-2",7,2,2]')
await new Promise(resolve=>setTimeout(resolve,300))
assert(Date.parse(original.expiresAt)<Date.now())
const failed={}
for(const [name,call] of [['status',()=>f.manager.status()],['confirm',()=>f.manager.confirm()],['prepare-new-session',()=>f.manager.prepare({...f.scope,sessionId:'session-2'},f.context())]]){
 try{await call();assert.fail('unexpected success')}catch(error){failed[name]=error.code}
}
assert.deepEqual(failed,{status:'CONTEXT_CHANGED',confirm:'CONTEXT_CHANGED','prepare-new-session':'QUALIFICATION_INTENT_PENDING'})
f.setContext('["project-1","session-1",7,2,3]')
await assert.rejects(f.manager.status(),{code:'CONTEXT_CHANGED'})
await assert.rejects(f.manager.prepare(f.scope,f.context()),{code:'QUALIFICATION_INTENT_PENDING'})
facts.push({name:'unconfirmed-expired-intent-cannot-recover-after-context-change',defect_reproduced:true,original,now:new Date().toISOString(),failed,summary:f.manager.summary(),frames:f.frames})

const h=fixture('summary-host-change')
await h.manager.prepare(h.scope,h.context());await h.manager.confirm()
assert.equal(h.manager.summary().authorized,true)
const before=h.manager.summary()
fs.writeFileSync(h.discoveryFile,JSON.stringify({...h.discovery,host_instance_id:'host-bbbbbbbbbbbb',data_dir:path.join(h.dir,'other-host')}))
assert.throws(()=>h.manager.currentHost(),{code:'HOST_CHANGED'})
const after=h.manager.summary()
assert.equal(after.authorized,true);assert.equal(after.available,true);assert.equal(after.state,'QUALIFIED_PURPOSE_AUTHORIZED')
facts.push({name:'current-summary-retains-authorization-after-host-switch',defect_reproduced:true,before,after,currentHostProbe:'HOST_CHANGED',frames:h.frames})

const processIdentity=observeWindowsProcess(process.pid)
assert.equal(processIdentity.PID,process.pid);assert.equal(typeof processIdentity.CreatedNS,'string')
facts.push({name:'actual-windows-parent-process-observed',passed:true,identity:processIdentity,nodeExecPath:process.execPath})
fs.writeFileSync(path.join(OUT,'lifecycle-edge-results.json'),JSON.stringify({evidence_class:'BOUND_CLIENT_MODULE_PUBLIC_IN_PROCESS_FRAMES_NOT_CORE_OR_MODEL',actual_model_calls:0,external_calls:0,facts},null,2)+'\n')
console.log(JSON.stringify(facts.map(({frames,...f})=>f)))
