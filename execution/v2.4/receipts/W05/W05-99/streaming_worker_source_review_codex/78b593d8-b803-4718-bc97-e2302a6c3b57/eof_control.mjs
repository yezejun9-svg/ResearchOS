import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {mkdtemp,mkdir,writeFile,access,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,dirname} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createInterface} from 'node:readline';
const out=dirname(fileURLToPath(import.meta.url));
const bundle='D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-model-stream-worker/.local/model-stream/mu-worker.mjs';
const {canonicalJSON}=await import(pathToFileURL(bundle));
const hash=b=>'sha256:'+createHash('sha256').update(b).digest('hex');
const root=await mkdtemp(join(tmpdir(),'researchos-independent-stream-eof-'));
await mkdir(join(root,'input'));await mkdir(join(root,'output'));
const binding={project_id:'project',session_id:'session',task_id:'task',run_id:'run',runtime_epoch:1,queue_generation:'generation',dispatch_key:'dispatch',manifest_hash:hash('manifest')};
await writeFile(join(root,'input/request.json'),JSON.stringify({task_id:'task',run_id:'run',epoch:1,input_refs:[],context:{},task_title:'SYNTHETIC EOF',task_description:'independent local protocol control',queue_control:true,queue_binding:binding}));
await writeFile(join(root,'input/worker.json'),JSON.stringify({ref:'fixture',api:'openai-completions',provider:'openai',model:'fixture',endpoint:'https://fixture.invalid',route:'fixture',max_output_tokens:128,max_calls:1,tools:[]}));
const child=spawn(process.execPath,[bundle,join(root,'input/request.json')],{cwd:root,stdio:['pipe','pipe','pipe']});
binding.process_identity={pid:child.pid,process_created_ns:'1',job:'fixture-job',appcontainer_sid:'fixture-sid',profile:'fixture-profile',staging_directory:root};
const frames=[];let stderr='',eof=false,timeout=false,error;
child.stderr.on('data',b=>stderr+=b);const send=v=>child.stdin.write(JSON.stringify(v)+'\n');
const reader=createInterface({input:child.stdout});
reader.on('line',l=>{try{const f=JSON.parse(l);frames.push(f);
 if(f.type==='context.ready')send({type:'command.deliver',binding,initialize:true,command:null});
 if(f.type==='command.accepted'&&f.payload.initialized)send({sequence:f.sequence,key:'command.initialize',state:'CONFIRMED',payload:{}});
 if(f.type==='effect.request'){
  const b={...binding,effect_sequence:f.sequence,effect_key:f.key,request_hash:hash('fixture-request')};const sb={...b,stream_id:hash(canonicalJSON(b))};
  send({version:'MODEL_SSE_V1',type:'stream.open',binding:sb,sequence:0,offset:0,digest:hash(''),payload:{status:200,content_type:'text/event-stream'}});
  const raw=Buffer.from('data: '+JSON.stringify({id:'fixture',object:'chat.completion.chunk',choices:[{index:0,delta:{content:'EOF boundary visible'},finish_reason:null}]})+'\n\n');
  send({version:'MODEL_SSE_V1',type:'stream.data',binding:sb,sequence:1,offset:raw.length,digest:hash(raw),payload:{data_base64:raw.toString('base64'),terminal:false}});
 }
 if(f.type==='stream.observe'&&!eof){eof=true;child.stdin.end();}
}catch(e){error=String(e);child.kill();}});
const timer=setTimeout(()=>{timeout=true;child.kill();},5000);
const code=await new Promise(resolve=>child.on('exit',resolve));clearTimeout(timer);
let resultExists=true;try{await access(join(root,'output/result.json'));}catch{resultExists=false;}
const result={mode:'SYNTHETIC_TRANSPORT_ONLY',eof_during_uncredited_real_sdk_observation:eof,exit_code:code,timeout,error,result_exists:resultExists,model_requests:frames.filter(f=>f.type==='effect.request').length,completed_frames:frames.filter(f=>f.type==='turn.completed').length};
await writeFile(join(out,'eof.frames.json'),JSON.stringify(frames,null,2));await writeFile(join(out,'eof.stderr.raw'),stderr);await writeFile(join(out,'eof.result.json'),JSON.stringify(result,null,2));
assert.equal(eof,true);assert.equal(code,1);assert.equal(timeout,false);assert.equal(resultExists,false);assert.equal(result.model_requests,1);assert.equal(result.completed_frames,0);assert.equal(error,undefined);
await rm(root,{recursive:true,force:true,maxRetries:5,retryDelay:50});console.log(JSON.stringify(result));
