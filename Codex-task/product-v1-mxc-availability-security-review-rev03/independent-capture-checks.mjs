// New independent virtual-I/O checks; no candidate module import or Native process.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import vm from 'node:vm';
const root=new URL('../',import.meta.url),dir='product-v1-mxc-availability-prepare-rev03-20261105-d83a/';
const read=(d,n)=>fs.readFileSync(new URL(d+n,root),'utf8'),sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const capture=read(dir,'bounded-capture.mjs'),wrapper=read(dir,'mxc-echo.mjs');
const assert=(v,m)=>{if(!v)throw Error(m)};
assert(sha(capture)==='5b1092acf0d4727bab5885cd8e7ce6c9d46420d8bcb63bedca65ce1198272740','CAPTURE_PIN');
assert(sha(wrapper)==='6011310276abb45c4bbcfdd786dac15e1dfdcdd93fb0805a9dfae45d10f6ac14','WRAPPER_PIN');
const box=vm.createContext({fs:{},path:path.win32,crypto});
vm.runInContext(capture.replace(/^import .*\n/gm,'').replaceAll('export ','')+'\nthis.api={BoundedCapture,durableJSON};',box);
const {BoundedCapture,durableJSON}=box.api;
class MemoryIO {
  files=new Map();durable=new Map();handles=new Map();nextFd=1;fail=null;
  err(op){if(this.fail===op)throw Object.assign(new Error('synthetic '+op+' failure'),{code:'EIO'});}
  openSync(name,flag){this.err('open');assert(flag==='wx','EXCLUSIVE_OPEN');if(this.files.has(name))throw Object.assign(Error('exists'),{code:'EEXIST'});this.files.set(name,Buffer.alloc(0));const fd=this.nextFd++;this.handles.set(fd,name);return fd;}
  writeFileSync(fd,data){this.err('write');const name=this.handles.get(fd);assert(name,'LIVE_FD');this.files.set(name,Buffer.concat([this.files.get(name),Buffer.from(data)]));}
  fsyncSync(fd){this.err('sync');const name=this.handles.get(fd);this.durable.set(name,Buffer.from(this.files.get(name)));}
  closeSync(fd){this.err('close');this.handles.delete(fd);}
  renameSync(from,to){this.err('rename');assert(this.files.has(from),'NEXT_EXISTS');this.files.set(to,this.files.get(from));this.files.delete(from);if(this.durable.has(from)){this.durable.set(to,this.durable.get(from));this.durable.delete(from);}}
}
const cases=[];const test=(name,fn)=>{fn();cases.push(name)};
const make=()=>{const io=new MemoryIO(),failures=[],source={pauses:0,pause(){this.pauses++}};const c=new BoundedCapture({directory:'C:/virtual-only',name:'stderr',io,onFailure:x=>failures.push(x)});c.attach(source);return{c,io,failures,source}};
const snap=(io,file)=>JSON.parse(io.durable.get(file).toString());
test('prefix and fsynced progress survive simulated loss of all memory before close',()=>{const {c,io}=make(),b=Buffer.from('sandbox refusal: synthetic\r\n');c.accept(b);assert(io.durable.get(c.prefixPath).equals(b),'PREFIX_NOT_DURABLE');const s=snap(io,c.progressPath);assert(s.durable_prefix_bytes===b.length&&s.prefix_sha256===sha(b)&&!s.stream_complete&&s.complete_stream_sha256===null&&!s.child_close_observed,'EARLY_PROGRESS_WRONG')});
test('timeout snapshot retains prior diagnostic and remains incomplete',()=>{const {c,io}=make();c.accept(Buffer.from('diagnostic'));c.markTimeout();const s=snap(io,c.progressPath);assert(s.status==='UNKNOWN_SOFT_TIMEOUT_AWAITING_ROOT_JOB'&&s.durable_prefix_bytes===10&&!s.stream_complete,'TIMEOUT_LOSS')});
test('17x64KiB plus4KiB cannot extend1MiB ingestion/hash',()=>{const {c,io,source}=make();for(let i=0;i<16;i++)c.accept(Buffer.alloc(65536,65));const before=c.state();c.accept(Buffer.alloc(65536,66));c.accept(Buffer.alloc(4096,67));const after=c.state();assert(before.ingested_bytes===1048576&&after.ingested_bytes===before.ingested_bytes&&after.ingested_sha256===before.ingested_sha256&&source.pauses===1,'QUOTA_NOT_ENFORCED');assert(io.durable.get(c.prefixPath).length===65536&&snap(io,c.progressPath).limit_reached,'QUOTA_NOT_DURABLE')});
test('oversized delivered chunk hashes only allowed bytes and reports discarded tail',()=>{const {c,io}=make();c.accept(Buffer.alloc(1048576+4096,65));const s=snap(io,c.progressPath);assert(s.ingested_bytes===1048576&&s.discarded_tail_bytes===4096&&s.ingested_sha256===sha(Buffer.alloc(1048576,65))&&!s.stream_complete,'OVERSIZE_NOT_BOUNDED')});
test('stream error recorded before childclose and prevents complete hash',()=>{const {c,io}=make();c.accept(Buffer.from('before'));c.recordError(Object.assign(Error('synthetic stream failure'),{code:'EPIPE'}));const s=snap(io,c.progressPath);assert(s.errors[0].code==='EPIPE'&&s.paused&&!s.child_close_observed,'ERROR_NOT_DURABLE');c.markEnd();assert(!c.finish().stream_complete,'ERROR_BECAME_COMPLETE')});
test('prefix fsync failure claims zero durable bytes and stops further hashing',()=>{const {c,io,failures}=make();io.fail='sync';c.accept(Buffer.from('not-durable'));const before=c.state();c.accept(Buffer.from('extra'));assert(before.persistence_failed&&before.durable_prefix_bytes===0&&!before.stream_complete&&failures.length>0&&before.ingested_sha256===c.state().ingested_sha256,'SYNC_FAILURE_NOT_CLOSED')});
test('snapshot rename failure preserves old progress and durable next for recovery',()=>{const {c,io,failures}=make();const original=Buffer.from(io.durable.get(c.progressPath));io.fail='rename';c.accept(Buffer.from('retained'));assert(io.durable.get(c.prefixPath).toString()==='retained'&&io.durable.get(c.progressPath).equals(original)&&io.durable.has(c.progressPath+'.next'),'ATOMIC_RECOVERY_LOST');assert(c.state().persistence_failed&&c.state().paused&&failures.length&&!c.state().stream_complete,'RENAME_FAILURE_NOT_CLOSED')});
test('first progress initialization failure blocks construction before any spawn',()=>{const io=new MemoryIO();io.fail='rename';let e;try{new BoundedCapture({directory:'C:/virtual-only',name:'stdout',io})}catch(x){e=x}assert(e?.code==='CAPTURE_INITIALIZATION_FAILED','INIT_FAILURE_NOT_REJECTED')});
test('EOF alone does not assert complete stream',()=>{const {c}=make();c.accept(Buffer.from('MXC_OK\r\n'));c.markEnd();assert(!c.state().stream_complete&&c.state().complete_stream_sha256===null,'EOF_PREMATURE_COMPLETE')});
test('childclose without EOF does not assert complete stream',()=>{const {c}=make();c.accept(Buffer.from('MXC_OK\r\n'));assert(!c.finish().stream_complete,'CLOSE_PREMATURE_COMPLETE')});
test('EOF plus childclose allows exact complete hash',()=>{const {c,io}=make(),b=Buffer.from('MXC_OK\r\n');c.accept(b);c.markEnd();const s=c.finish();assert(s.stream_complete&&s.complete_stream_sha256===sha(b)&&snap(io,c.progressPath).child_close_observed,'VALID_COMPLETE_REJECTED')});
test('quota remains incomplete after forced EOF and childclose notifications',()=>{const {c}=make();c.accept(Buffer.alloc(1048576));c.markEnd();const s=c.finish();assert(!s.stream_complete&&s.complete_stream_sha256===null,'QUOTA_FALSE_COMPLETE')});
test('prefix-close I/O failure cannot permit success',()=>{const {c,io,failures}=make();c.accept(Buffer.from('MXC_OK\n'));c.markEnd();io.fail='close';const s=c.finish();assert(s.persistence_failed&&!s.stream_complete&&failures.length>0,'CLOSE_ERROR_FALSE_SUCCESS')});
const old=read('product-v1-mxc-availability-prepare-rev02-20261105-c42b/','mxc-echo.mjs');
const block=(s,a,b)=>s.slice(s.indexOf(a),s.indexOf(b,s.indexOf(a)));
assert(block(old,'export function makeEnvironment','async function main')===block(wrapper,'export function makeEnvironment','async function main'),'ENV_DRIFT');
assert(block(old,'const ARGV =','const digest =')===block(wrapper,'const ARGV =','const digest ='),'ARGV_DRIFT');
const outer=JSON.parse(read(dir,'f13.scope.template.json')),inner=JSON.parse(read(dir,'mxc.scope.template.json'));
assert(outer.inputs.some(x=>x.path.endsWith('/bounded-capture.mjs')&&x.sha256===sha(capture)),'CAPTURE_NOT_PINNED_BEFORE_IMPORT');
assert(wrapper.indexOf('new BoundedCapture')<wrapper.indexOf('child = spawn'),'CAPTURE_INIT_AFTER_SPAWN');
assert(wrapper.includes('!timedOut && evidence.every(v=>v.stream_complete)')&&wrapper.includes('observationErrors.length === 0'),'SUCCESS_GATE');
assert(outer.timeout_seconds===45&&outer.cleanup_seconds===5&&outer.process_limit===16&&outer.memory_mib===2048&&inner.timeout_ms===35000,'BOUND_DRIFT');
const manifest=JSON.parse(read(dir,'MANIFEST.json'));for(const row of manifest.files){const bytes=fs.readFileSync(new URL(dir+row.name,root));assert(sha(bytes)===row.sha256&&bytes.length===row.bytes,'MANIFEST_DRIFT')}
console.log(JSON.stringify({status:'INDEPENDENT_CAPTURE_REPAIR_CHECKS_PASS',cases:cases.length,names:cases,known_origins_resolved:['mxc-rev02:diagnostics-not-durable-before-close','mxc-rev02:output-threshold-does-not-cap-ingestion'],manifest_members:manifest.files.length,environment_and_fixed_argv_byte_identical_to_rev02:true,capture_pinned_in_outer_inputs:true,actual_native_or_model_invocations:0,candidate_entrypoint_imports:0,real_process_kills:0,pure_io:'VIRTUAL_MEMORY_IO_ONLY'},null,2));
