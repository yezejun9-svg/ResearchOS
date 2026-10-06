from pathlib import Path
root=Path(__file__).resolve().parents[7]
p=root/'adapters/runtime/mu/worker-provider-binding.test.mjs'
source=(root/'adapters/runtime/mu/worker-stream.test.mjs').read_text(encoding='utf-8')
fn=source[source.index('async function childFixture('):source.index('test("rebuilt actual AgentSession streams')]
fn=fn.replace('async function childFixture(t, cancel) {','async function providerCancelFixture(t) {\n  const cancel = true;')
fn=fn.replace('JSON.stringify({ ref: "FIXTURE", api: "openai-completions", provider: "openai", model: "fixture", endpoint: "https://fixture.invalid", route: "fixture", max_output_tokens: 128, max_calls: 1, tools: [] })','JSON.stringify({...config(),max_calls:1})')
fn=fn.replace('abortObserved = false, cancelAt;','abortObserved = false, cancelledIdle = false, cancelAt;')
fn=fn.replace('if (cancel) { assert.ok(abortObserved); done.resolve(); return; }','if (cancel) { cancelledIdle = frame.payload.cancelled === true && frame.payload.sdk_idle === true && frame.payload.sdk_queue_empty === true; if (cancelledIdle && abortObserved) done.resolve(); return; }')
fn=fn.replace('abortObserved = true; record(', 'abortObserved = true; if (cancelledIdle) done.resolve(); record(')
fn=fn.replace('heldEffect = frame; produce(frame)', 'validateProviderRequest(config(), config().endpoint, frame.payload.body); heldEffect = frame; produce(frame)')
extra='''
// Actual pinned AgentSession negative control; transport credits are fixture
// facts here. SQLite and native Host provenance remain separate Go controls.
import { createHash } from "node:crypto";
import { spawn } from "node:child_process";
import { createInterface } from "node:readline";
import { mkdtemp,mkdir,writeFile,readFile,rm } from "node:fs/promises";
import { tmpdir } from "node:os";
const hash=raw=>`sha256:${createHash("sha256").update(raw).digest("hex")}`;
const EMPTY=hash("");
const pending=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b});promise.catch(()=>{});return{promise,resolve,reject}};
const canonicalJSON=v=>JSON.stringify(v,(_k,p)=>p!==null&&typeof p==="object"&&!Array.isArray(p)?Object.fromEntries(Object.keys(p).sort().map(k=>[k,p[k]])):p);
const base={project_id:"fixture-project",session_id:"fixture-session",task_id:"task",run_id:"run",runtime_epoch:1,queue_generation:"generation",dispatch_key:"dispatch",manifest_hash:hash("manifest"),process_identity:{pid:1,process_created_ns:"1",job:"fixture-job",appcontainer_sid:"fixture-sid",profile:"fixture-profile",staging_directory:"fixture-stage"}};
const chunk=(delta,finish_reason=null)=>({choices:[{index:0,delta,finish_reason}]});
const sse=v=>`data: ${JSON.stringify(v)}\\n\\n`;
'''
if 'async function providerCancelFixture' in p.read_text(encoding='utf-8'):raise RuntimeError('already appended')
with p.open('a',encoding='utf-8') as f:f.write(extra+fn+'\ntest("actual provider SDK cancellation bypasses held observation and preserves late original ACK",{timeout:10000},providerCancelFixture);\n')
