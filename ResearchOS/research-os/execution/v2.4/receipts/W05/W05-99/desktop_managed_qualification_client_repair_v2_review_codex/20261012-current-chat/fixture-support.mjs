import fs from 'node:fs'
import path from 'node:path'
import assert from 'node:assert/strict'
import {EventEmitter} from 'node:events'
import {fileURLToPath} from 'node:url'
import {createRequire} from 'node:module'
const OUT=path.dirname(fileURLToPath(import.meta.url)),ROOT=path.resolve(OUT,'../../../../../../..'),WT=path.join(ROOT,'.local/worktrees/w05-desktop-managed-qualification-client-repair-v2-20261012')
const BUILD=path.join(WT,'.local/managed-client-repair-v2-bound-final'),require=createRequire(import.meta.url)
const {createDesktopManagement,observeWindowsProcess,strictJSON}=require(path.join(BUILD,'apps/desktop/main/lib/desktop-management.js'))
const facts=[]
export function fixture(name,{expiresSoon=false}={}){
 const dir=path.join(OUT,'lifecycle-fixture',name);fs.mkdirSync(dir,{recursive:true})
 const discoveryFile=path.join(dir,'discovery.json'),hostId='host-aaaaaaaaaaaa',pid=24680
 let context='["project-1","session-1",7,2,1]',statusState='QUALIFIED_PURPOSE_AUTHORIZED',consumed=true,serial=0,lastId=null,holdOperation=null,held=null
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
  if(request.operation==='PREPARE'){serial++;lastId='req-'+name+'-'+serial}
  const now=Date.now(),requestBody={request_id:lastId,project_id:request.project_id,session_id:request.session_id,model_config_ref:request.model_config_ref,owner_host:hostId,authorize_purpose:'mu_turn',issued_at:new Date(now-(expiresSoon&&serial===1?59800:1000)).toISOString(),expires_at:new Date(now+(expiresSoon&&serial===1?200:58000)).toISOString()}
  const result=request.operation==='PREPARE'?{state:'AWAITING_CONFIRMATION',request:requestBody,request_hash:requestHash,model_calls:1,tools:[],purpose:'mu_turn',purpose_seconds:600,cost_basis:'UNKNOWN',money:null}
    :request.operation==='STATUS'?{request_id:lastId,request_hash:requestHash,state:statusState,consumed}
    :{state:'QUALIFIED_PURPOSE_AUTHORIZED'}
  const frame={protocol:'researchos-desktop-management/1',message_id:request.message_id,operation:request.operation,host_id:hostId,kind:'RESULT',result}
  const deliver=()=>{const raw=Buffer.from(JSON.stringify(frame));frames.push({direction:'fixture_to_desktop',raw:raw.toString()});manager.onLine(raw)}
  if(request.operation===holdOperation)held=deliver;else setImmediate(deliver)
  callback?.();return true
 }}
 const scope={projectId:'project-1',sessionId:'session-1',modelRef:'model-1',model:{provider_id:'fixture',model_id:'no-model-execution'}}
 return {manager,scope,frames,dir,discoveryFile,discovery,hold:op=>holdOperation=op,release:()=>{const send=held;held=null;send?.()},setContext:x=>context=x,setStatus:(s,c)=>{statusState=s;consumed=c},context:()=>context}
}
