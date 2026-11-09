import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {BoundedCapture} from './bounded-capture.mjs';
const root=path.dirname(fileURLToPath(import.meta.url));
const out=fs.mkdtempSync(path.join(root,'pure-capture-evidence-'));
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const tests=[];
function create(name,options={}) {
  const directory=path.join(out,name);fs.mkdirSync(directory);
  const c=new BoundedCapture({directory,name:'stdout',...options});
  const fake={pauses:0,pause(){this.pauses++;}};c.attach(fake);
  return {c,fake,directory};
}
{
  const {c,directory}=create('first-chunk-before-close');
  const text=Buffer.from('native sandbox refusal diagnostic\r\n');
  c.accept(text);
  assert.deepEqual(fs.readFileSync(c.prefixPath),text);
  let p=JSON.parse(fs.readFileSync(c.progressPath));
  assert.equal(p.durable_prefix_bytes,text.length);assert.equal(p.ingested_sha256,sha(text));
  assert.equal(p.child_close_observed,false);assert.equal(p.stream_complete,false);assert.equal(p.complete_stream_sha256,null);
  c.markTimeout();p=JSON.parse(fs.readFileSync(c.progressPath));
  assert.equal(p.status,'UNKNOWN_SOFT_TIMEOUT_AWAITING_ROOT_JOB');assert.equal(p.ingested_bytes,text.length);
  assert.equal(p.prefix_sha256,sha(text));assert.equal(p.child_close_observed,false);
  // Deliberately no finish(): simulates reading durable evidence before outer hard-stop.
  tests.push('first_chunk_and_timeout_durable_without_child_close');
}
{
  const {c,fake}=create('limit-pauses-ingestion');
  const chunk=Buffer.alloc(65536,65);
  for(let i=0;i<16;i++)c.accept(chunk);
  const before=c.state();assert.equal(before.ingested_bytes,1048576);assert.equal(fake.pauses,1);
  c.accept(chunk);c.accept(Buffer.alloc(4096,66));
  const after=c.state();
  assert.equal(after.ingested_bytes,before.ingested_bytes);assert.equal(after.delivered_bytes,before.delivered_bytes);
  assert.equal(after.ingested_sha256,before.ingested_sha256);
  assert.equal(fs.statSync(c.prefixPath).size,65536);assert.equal(after.complete_stream_sha256,null);
  const p=JSON.parse(fs.readFileSync(c.progressPath));assert.equal(p.limit_reached,true);assert.equal(p.paused,true);
  c.markEnd();assert.equal(c.finish().stream_complete,false);
  tests.push('17x64KiB_plus_4KiB_capped_at_1MiB_no_post_limit_hash');
}
{
  const {c,fake}=create('oversize-single-chunk',{limit:1024,prefixLimit:128});
  c.accept(Buffer.alloc(4096,67));
  assert.equal(c.state().ingested_bytes,1024);assert.equal(c.state().discarded_tail_bytes,3072);
  assert.equal(c.state().ingested_sha256,sha(Buffer.alloc(1024,67)));assert.equal(fake.pauses,1);
  tests.push('oversize_chunk_only_bounded_prefix_hashed');
}
{
  const {c}=create('immediate-stream-error');
  c.accept(Buffer.from('error prefix'));
  c.recordError(Object.assign(new Error('synthetic stream error'),{code:'EPIPE'}));
  const p=JSON.parse(fs.readFileSync(c.progressPath));
  assert.equal(p.errors[0].code,'EPIPE');assert.equal(p.errors[0].message_prefix,'synthetic stream error');
  assert.equal(p.child_close_observed,false);assert.equal(p.paused,true);
  tests.push('stream_error_durable_before_close');
}
{
  let failures=0;const {c,fake}=create('fsync-failure',{onFailure:()=>failures++});
  c.io={...fs,fsyncSync(){throw Object.assign(new Error('synthetic fsync failure'),{code:'EIO'});}};
  c.accept(Buffer.from('diagnostic'));
  assert.equal(c.state().persistence_failed,true);assert.equal(c.state().stream_complete,false);
  assert.equal(c.state().durable_prefix_bytes,0);assert.ok(fake.pauses>0);assert.ok(failures>0);
  const before=c.state().ingested_sha256;c.accept(Buffer.alloc(4096));assert.equal(c.state().ingested_sha256,before);
  tests.push('fsync_failure_failclosed_pauses_no_durability_claim');
}
{
  const {c}=create('ordinary-complete-echo');
  c.accept(Buffer.from('MXC_OK\r\n'));c.markEnd();
  assert.equal(c.state().stream_complete,false);
  const p=c.finish();assert.equal(p.stream_complete,true);assert.equal(p.complete_stream_sha256,sha(Buffer.from('MXC_OK\r\n')));
  tests.push('complete_hash_requires_end_and_close');
}
const result={schema:'researchos.mxc-rev03-pure-capture-check.v1',status:'PASS',tests,assertions:'node:assert/strict',evidence_directory:out,native_invocations:0,model_tasks:0,real_process_kill_tests:0,resource_ready:false};
fs.writeFileSync(path.join(root,'PURE-CHECK.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({status:'PASS',cases:tests.length,native_invocations:0,model_tasks:0}));

