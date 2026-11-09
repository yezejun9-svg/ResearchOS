import fs from 'node:fs';
import path from 'node:path';
import {EventEmitter} from 'node:events';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
export const out=path.dirname(fileURLToPath(import.meta.url));
export const root=path.resolve(out,'../../../../../../..');
export const build=path.join(root,'.local/worktrees/w05-product-coding-client-20261012/.local/coding-client-bound-final3');
const require=createRequire(import.meta.url);
export const {createDesktopManagement}=require(path.join(build,'apps/desktop/main/lib/desktop-management.js'));
export const {registerDesktopCoding}=require(path.join(build,'apps/desktop/main/lib/ipc.js'));
export const hash='sha256:'+'b'.repeat(64),protocol='researchos-desktop-management/1';
export const context=JSON.stringify(['project-1','session-1',1,1]);
export function coding(){return {client_id:'desktop-shell',expected_revision:1,writer_epoch:1,config_revision:2,workspace_ref:'workspace-1',read_paths:['go.mod','calc/value.go','calc/value_test.go'],write_paths:['calc/value.go'],max_read_bytes:8192,max_write_bytes:8192,max_tool_calls:8,max_output_tokens:2048,checks:[{id:'value-check',package:'./calc',test_pattern:'^TestValue$',source_paths:['go.mod','calc/value.go','calc/value_test.go'],toolchain_root:'C:/trusted-go',timeout_seconds:90,process_limit:32,memory_mib:1024,max_text_bytes:4096}]};}
export const scope=()=>({projectId:'project-1',sessionId:'session-1',modelRef:'model-1',coding:coding()});
export function fixture(name,{ttl=55000}={}){
 const dir=path.join(out,'fixtures',name);fs.mkdirSync(dir,{recursive:true});
 const hostId='host-aaaaaaaaaaaa',pid=24680,discoveryFile=path.join(dir,'discovery.json');
 fs.writeFileSync(discoveryFile,JSON.stringify({url:'http://127.0.0.1:54321/',pid,data_dir:dir,host_instance_id:hostId}));
 let selected=context,seq=0,prepared=null,committed=false,hold=false;
 const sent=[],received=[],held=[];
 const identity=id=>({PID:id,CreatedNS:String(id)+'000000000',ImageSHA256:'a'.repeat(64)});
 const manager=createDesktopManagement({fsImpl:fs,discoveryFile,dataRoot:dir,context:()=>selected,observeProcess:identity});
 const child=new EventEmitter();child.pid=pid;
 function result(frame){
  if(frame.operation==='PREPARE_CODING'){
   prepared={state:'AWAITING_CODING_CONFIRMATION',request_id:`coding-${++seq}`,request_hash:hash,expires_at:new Date(Date.now()+ttl).toISOString(),project_id:'project-1',session_id:'session-1',old_model_config_ref:'model-1',scope:frame.coding,frozen_checks:[{id:'value-check',package:'./calc',test_pattern:'^TestValue$',source_count:3,source_bytes:123,source_manifest_hash:hash,toolchain_hash:hash,build_hash:hash,vendor_hash:''}],normal_max_model_calls:8,qualification_model_calls:1,qualification_tool_calls:0,model_calls:0};committed=false;return {...prepared};
  }
  if(frame.operation==='CONFIRM_CODING')committed=true;
  if(committed)return {...prepared,state:'CODING_CONFIGURED',model_config_ref:'model-2',runtime_status:'REGISTERED',profile_ref:'profile-1',revision:2,config_revision:2};
  return {...prepared,state:Date.parse(prepared.expires_at)<=Date.now()?'EXPIRED':'AWAITING_CODING_CONFIRMATION'};
 }
 function deliver(frame){received.push(frame);manager.onLine(Buffer.from(JSON.stringify(frame)));}
 child.stdin={write(bytes,callback){const frame=JSON.parse(bytes.toString('utf8'));sent.push(frame);const reply={protocol,message_id:frame.message_id,operation:frame.operation,host_id:hostId,kind:'RESULT',result:result(frame)};if(hold)held.push(reply);else setImmediate(()=>deliver(reply));callback?.();return true;}};
 manager.state='READY';manager.child=child;manager.childExited=false;manager.hostId=hostId;manager.identity=identity(pid);manager.parentIdentity=identity(process.pid);
 function save(){fs.writeFileSync(path.join(dir,'frames.json'),JSON.stringify({sent,received,held},null,2));}
 return {manager,sent,received,held,setContext:value=>{selected=value;},setHold:value=>{hold=value;},deliver:()=>deliver(held.shift()),save};
}
