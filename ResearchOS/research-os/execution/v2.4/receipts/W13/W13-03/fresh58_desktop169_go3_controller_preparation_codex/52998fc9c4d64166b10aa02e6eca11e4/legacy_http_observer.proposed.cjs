'use strict';
// Receipt-only preload. Never forwards headers or changes original server replies.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const http = require('node:http');
const root = process.env.RESEARCHOS_DESKTOP_CASE_RECEIPT;
if (!root || !path.isAbsolute(root)) throw Error('Explicit own case receipt required');
const dir = path.join(root, 'legacy-observer', String(process.pid));
fs.mkdirSync(dir, {recursive:true});
const journal = fs.openSync(path.join(dir,'events.jsonl'),'wx');
const digest = b => crypto.createHash('sha256').update(b).digest('hex');
let sequence=0, requests=0, completed=0, active=0, errors=0, rawBytes=0;
// Per-process recording bounds are finite; excess is a failure, never a false zero.
function event(value) {
  fs.writeSync(journal, JSON.stringify({sequence:++sequence,pid:process.pid,...value})+'\n');
}
function raw(name, buffer) {
  if (buffer.length>33554436 || rawBytes+buffer.length>1073741824) {
    event({kind:'evidence-overflow',bytes:buffer.length,prior_bytes:rawBytes});
    throw Error('Receipt evidence bound exceeded');
  }
  const file=path.join(dir,name);fs.writeFileSync(file,buffer,{flag:'wx'});rawBytes+=buffer.length;
  return {path:file,bytes:buffer.length,sha256:digest(buffer)};
}
function asBuffer(chunk, encoding) {
  if (chunk===undefined || chunk===null || typeof chunk==='function') return Buffer.alloc(0);
  return Buffer.isBuffer(chunk)?Buffer.from(chunk):Buffer.from(chunk, typeof encoding==='string'?encoding:undefined);
}
const original = http.Server.prototype.emit;
http.Server.prototype.emit = function(name,...args) {
  if (name!=='request') return Reflect.apply(original,this,[name,...args]);
  const [req,res]=args, id=++requests;active++;
  if (requests>64) {
    event({kind:'request-recording-overflow',id,already_received:true,remaining_unenumerated:null});
    throw Error('Fixture request observation bound exceeded');
  }
  event({kind:'request-received',id,method:req.method,url:req.url,rawHeaders:req.rawHeaders,
    localAddress:req.socket.localAddress,remoteAddress:req.socket.remoteAddress,already_received:true});
  let body=[], readComplete=false, writeOrdinal=0, finished=false, receivedBytes=0;
  req.on('data',chunk=>{receivedBytes+=chunk.length;if(receivedBytes>33554436){event({kind:'request-body-overflow',id});throw Error('Request observation bound exceeded');}body.push(Buffer.from(chunk));});
  req.on('end',()=>{readComplete=true;event({kind:'request-body-complete',id,raw:raw(id+'.request.raw',Buffer.concat(body))});});
  req.on('error',error=>{errors++;event({kind:'request-read-error',id,error:String(error),reader_complete:readComplete});});
  for(const method of ['write','end']) {
    const call=res[method];
    res[method]=function(...values) {
      const bytes=asBuffer(values[0],values[1]), ordinal=++writeOrdinal;
      let result;
      try {result=Reflect.apply(call,this,values);}
      catch(error) {errors++;event({kind:'response-call-error',id,method,ordinal,error:String(error),attempted:raw(id+'.write-'+ordinal+'.attempt.raw',bytes),actual_socket_bytes:null});throw error;}
      event({kind:'response-call-returned',id,method,ordinal,status:this.statusCode,
        explicit_headers:this.getHeaders(),accepted_argument:raw(id+'.write-'+ordinal+'.accepted.raw',bytes),
        write_return_boolean:typeof result==='boolean'?result:null,actual_socket_bytes:null,
        boundary:'SERVER_RESPONSE_METHOD_RETURN_NOT_NETWORK_CAPTURE',auto_Date:null,auto_ContentLength:null});
      return result;
    };
  }
  res.once('finish',()=>{finished=true;completed++;event({kind:'response-finish',id,status:res.statusCode,explicit_headers:res.getHeaders(),reader_complete:readComplete,actual_socket_bytes:null});});
  res.once('error',error=>{errors++;event({kind:'response-error',id,error:String(error)});});
  res.once('close',()=>{active--;event({kind:'response-close',id,finished,reader_complete:readComplete});});
  return Reflect.apply(original,this,[name,...args]);
};
event({kind:'observer-start',boundary:'FIXTURE_SERVER_RECEIVE_AND_RESPONSE_METHODS',product_headers_modified:false});
process.once('exit',code=>{
  event({kind:'observer-exit',code,requests_received:requests,response_finished:completed,active,errors,raw_bytes:rawBytes,
    outbound_network_total:null,unobserved_client_requests:null,OS_lifecycle_proof:false});
  fs.closeSync(journal);
});
