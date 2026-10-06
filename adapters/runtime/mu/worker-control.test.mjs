import test from "node:test";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdtemp, mkdir, writeFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createInterface } from "node:readline";
import { createHash } from "node:crypto";
import { gzipSync } from "node:zlib";

const digest = (raw) => `sha256:${createHash("sha256").update(raw).digest("hex")}`;
const bundle = process.env.RESEARCHOS_QUEUE_WORKER_BUNDLE;
assert.ok(bundle, "the current rebuilt pinned SDK bundle is required");

async function harness(t, cancel) {
  const root = await mkdtemp(join(tmpdir(), "researchos-queue-sdk-"));
  await mkdir(join(root,"input"));await mkdir(join(root,"output"));
  const binding = { project_id:"project",session_id:"session",task_id:"task",run_id:"run",runtime_epoch:1,queue_generation:"generation",dispatch_key:"dispatch",manifest_hash:digest("manifest") };
  await writeFile(join(root,"input","request.json"),JSON.stringify({task_id:"task",run_id:"run",epoch:1,input_refs:[],context:{},task_title:"queue evidence",task_description:"original prompt",queue_control:true,queue_binding:binding}));
  await writeFile(join(root,"input","worker.json"),JSON.stringify({ref:"local-fixture",api:"openai-completions",provider:"openai",model:"fixture",endpoint:"https://fixture.invalid",route:"loopback-broker",max_output_tokens:128,max_calls:8,tools:[]}));
  const child = spawn(process.execPath,[bundle,join(root,"input","request.json")],{cwd:root,stdio:["pipe","pipe","pipe"]});
  const exited = new Promise(resolve => child.once("exit",resolve));
  binding.process_identity={pid:child.pid,process_created_ns:"host-fixture-creation",job:"host-fixture-job",appcontainer_sid:"fixture-sid",profile:"fixture-profile",staging_directory:root};
  t.after(async()=>{child.kill();await exited;await rm(root,{recursive:true,force:true,maxRetries:5,retryDelay:50})});
  let stderr="";child.stderr.on("data",data=>stderr+=data);
  const frames=[];const requests=[];let sent=false,prepared=false,committed=false,abort=false;
  const send = (frame)=>child.stdin.write(JSON.stringify({...frame,binding})+"\n");
  const text="同样的原始用户输入 — exact bytes";
  const attachment="原始附件 UTF-8 text";
  const content=JSON.stringify({text,attachments:[{ref:{kind:"Artifact",id:"attachment",revision:1,content_hash:digest(attachment)},media_type:"text/plain",text:attachment}]});
  const command=(id,n)=>({command_id:id,message_id:`message-${n}`,queue_sequence:n,content,content_hash:digest(content),delivery:n===1?"STEER":"FOLLOW_UP"});
  const acknowledge=(frame)=>{
    const sse='data: '+JSON.stringify({id:"fixture",object:"chat.completion.chunk",choices:[{index:0,delta:{role:"assistant",content:"bounded reply"},finish_reason:null}]})+'\n\ndata: '+JSON.stringify({id:"fixture",object:"chat.completion.chunk",choices:[{index:0,delta:{},finish_reason:"stop"}]})+'\n\ndata: [DONE]\n\n';
    child.stdin.write(JSON.stringify({sequence:frame.sequence,key:frame.key,state:"CONFIRMED",payload:{status:200,content_type:"text/event-stream",body_encoding:"gzip+base64",body_gzip_base64:gzipSync(sse).toString("base64"),body_sha256:digest(sse)}})+"\n");
  };
  const finished=new Promise((resolve,reject)=>{
    const reader=createInterface({input:child.stdout});
    reader.on("line",line=>{try{
      const frame=JSON.parse(line);frames.push(frame);assert.equal(frame.sequence,frames.length);
      if(frame.type==="context.ready")send({type:"command.deliver",initialize:true,command:null});
      if(frame.type==="effect.request"){
        requests.push(frame.payload.body);
        if(!sent){sent=true;send({type:"command.deliver",command:command("first",1)});send({type:"command.deliver",command:command("second",2)});if(cancel){send({type:"command.clear_abort"});return;}setTimeout(()=>acknowledge(frame),50);}else acknowledge(frame);
      }
      if(frame.type==="command.abort_observed")abort=true;
      if(frame.type==="command.idle"){
        if(cancel && abort){child.kill();resolve();return;}
        if(!sent)return;
        if(!prepared){prepared=true;send({type:"command.prepare_seal",through:2});}
        else if(frame.payload.through===2&&!committed){committed=true;send({type:"command.commit_seal",through:2});}
      }
    }catch(error){reject(error);child.kill();}});
    child.on("error",reject);child.on("exit",code=>{if(cancel&&abort)resolve();else if(code===0)resolve();else reject(new Error(`worker exit ${code}: ${stderr}`))});
  });
  await finished;
  const accepted=frames.filter(f=>f.type==="command.accepted"&&f.payload.command_id);
  assert.deepEqual(accepted.map(f=>f.payload.command_id),["first","second"]);
  assert.ok(frames.some(f=>f.type==="command.accepted"&&f.payload.initialized===true));
  if(cancel){assert.equal(frames.filter(f=>f.type==="command.cleared").length,2);assert.equal(frames.filter(f=>f.type==="command.consumed").length,0);assert.ok(abort);assert.equal(requests.length,1);}
  else {
    assert.deepEqual(frames.filter(f=>f.type==="command.consumed").map(f=>f.payload.command_id),["first","second"]);
    assert.ok(frames.some(f=>f.type==="command.sealed"));assert.equal(frames.at(-1).type,"turn.completed");
    const latest=JSON.stringify(requests.at(-1).messages);assert.ok(latest.includes(text));assert.equal(latest.split(attachment).length-1,2,"both original attachment text parts reach actual model");assert.equal(latest.includes("researchos.command.v1"),false);assert.equal(latest.includes("queue_generation"),false);
    const messages=requests.at(-1).messages.filter(m=>m.role==="user"&&JSON.stringify(m.content).includes(text));assert.equal(messages.length,2,"duplicate text must retain both distinct SDK messages");
  }
}

test("pinned AgentSession consumes STEER and FOLLOW_UP with stable IDs and exact user content",{timeout:20000},t=>harness(t,false));
test("pinned AgentSession clear/abort remains responsive during pending MODEL effect",{timeout:20000},t=>harness(t,true));
