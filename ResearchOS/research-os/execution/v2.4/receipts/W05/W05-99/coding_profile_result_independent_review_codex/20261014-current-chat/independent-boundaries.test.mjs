import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { EventEmitter } from 'node:events'
import { createRequire } from 'node:module'

const require = createRequire(import.meta.url)
const { createDesktopManagement } = require("D:\\\u4f5c\u54c1\u96c6\\ResearchOS\\research-os\\.local\\worktrees\\coding-profile-result-20261014\\apps\\desktop\\main\\lib\\desktop-management.js")
const { registerDesktopCoding, registerDesktopQualification } = require("D:\\\u4f5c\u54c1\u96c6\\ResearchOS\\research-os\\.local\\worktrees\\coding-profile-result-20261014\\apps\\desktop\\main\\lib\\ipc.js")
const protocol = 'researchos-desktop-management/1'
const hash = 'sha256:' + 'b'.repeat(64)
const profileRef = () => ({ entity_type: 'Artifact', id: 'd'.repeat(32), revision: 1,
  content_hash: 'sha256:' + 'c'.repeat(64) })

function fixture() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ros-coding-client-'))
  const hostId = 'host-aaaaaaaaaaaa', pid = 24680
  const discoveryFile = path.join(dir, 'discovery.json')
  fs.writeFileSync(discoveryFile, JSON.stringify({ url: 'http://127.0.0.1:54321/', pid,
    data_dir: dir, host_instance_id: hostId }))
  let context = JSON.stringify(['project-1', 'session-1', 1, 1]), suppress = false, expiryMs = 55000
  let resourceGeneration = 0, rejectPrepareOnce = false
  let qualificationState = 'EXECUTION_SETTLED', qualificationConsumed = true
  let profileRefValue = profileRef()
  const queued = []
  const log = [], identity = id => ({ PID: id, CreatedNS: String(id) + '000000000', ImageSHA256: 'a'.repeat(64) })
  const child = new EventEmitter(); child.pid = pid
  const manager = createDesktopManagement({ fsImpl: fs, discoveryFile, dataRoot: dir,
    context: () => context, observeProcess: identity,
    codingResourceGeneration: () => resourceGeneration })
  child.stdin = { write(bytes, callback) {
    const frame = JSON.parse(bytes.toString('utf8')); log.push(frame)
    const base = { state: 'AWAITING_CODING_CONFIRMATION', request_id: 'coding-1', request_hash: hash,
      expires_at: new Date(Date.now() + expiryMs).toISOString(), project_id: 'project-1',
      session_id: 'session-1', old_model_config_ref: 'model-1', scope: coding(),
      frozen_checks: [{ id: 'value-check', package: './calc', test_pattern: '^TestValue$',
        source_count: 3, source_bytes: 123, source_manifest_hash: hash, toolchain_hash: hash,
        build_hash: hash, vendor_hash: '' }], normal_max_model_calls: 8,
      qualification_model_calls: 1, qualification_tool_calls: 0, model_calls: 0 }
    let result = frame.operation === 'PREPARE_CODING' ? { ...base, scope: frame.coding } :
      frame.operation === 'CONFIRM_CODING' || (frame.operation === 'STATUS_CODING' && log.some(item => item.operation === 'CONFIRM_CODING'))
        ? { ...base, state: 'CODING_CONFIGURED', scope: frame.operation === 'CONFIRM_CODING' ? log[0].coding : log[0].coding,
          model_config_ref: 'model-2', runtime_status: 'REGISTERED', profile_ref: profileRefValue,
          revision: 2, config_revision: 2 } : frame.operation === 'STATUS_CODING' &&
          Date.parse(manager.codingIntent?.expiresAt) <= Date.now()
            ? { ...base, state: 'EXPIRED' } : base
    if (frame.operation === 'PREPARE') result = { state: 'AWAITING_CONFIRMATION',
      request: { request_id: 'original-qualification', project_id: frame.project_id, session_id: frame.session_id,
        model_config_ref: frame.model_config_ref, owner_host: hostId, authorize_purpose: 'mu_turn',
        issued_at: new Date(Date.now() - 1000).toISOString(), expires_at: new Date(Date.now() + 55000).toISOString() },
      request_hash: hash, model_calls: 1, tools: [], purpose: 'mu_turn', purpose_seconds: 600,
      cost_basis: 'UNKNOWN', money: null }
    if (frame.operation === 'STATUS') result = { request_id: 'original-qualification', request_hash: hash,
      state: qualificationState, consumed: qualificationConsumed }
    if (frame.operation === 'CONFIRM') result = { state: 'EXECUTION_SETTLED' }
    const answer = { protocol, message_id: frame.message_id, operation: frame.operation,
      host_id: hostId, kind: 'RESULT', result }
    if (frame.operation === 'PREPARE_CODING' && rejectPrepareOnce) {
      rejectPrepareOnce = false; answer.kind = 'ERROR'; answer.result = null
      answer.error = { code: 'MANAGEMENT_REJECTED', message: 'fixture source path is missing' }
    }
    if (suppress) queued.push(answer)
    else setImmediate(() => manager.onLine(Buffer.from(JSON.stringify(answer))))
    callback?.(); return true
  } }
  manager.state = 'READY'; manager.child = child; manager.childExited = false; manager.hostId = hostId
  manager.identity = identity(pid); manager.parentIdentity = identity(process.pid)
  return { manager, log, dir, setContext: value => { context = value },
    setResourceGeneration: value => { resourceGeneration = value }, suppress: value => { suppress = value },
    rejectNextPrepare: () => { rejectPrepareOnce = true }, expiry: value => { expiryMs = value },
    qualification: (state, consumed = true) => { qualificationState = state; qualificationConsumed = consumed },
    setProfileRef: value => { profileRefValue = value },
    release: change => { const answer = queued.shift(); manager.onLine(Buffer.from(JSON.stringify(change ? change(answer) : answer))) },
    close: () => fs.rmSync(dir, { recursive: true, force: true }) }
}

function coding() { return { client_id: 'desktop-shell', expected_revision: 1, writer_epoch: 1,
  config_revision: 2, workspace_ref: 'workspace-1', read_paths: ['go.mod', 'calc/value.go', 'calc/value_test.go'],
  write_paths: ['calc/value.go'], max_read_bytes: 8192, max_write_bytes: 8192,
  max_tool_calls: 8, max_output_tokens: 2048, checks: [{ id: 'value-check', package: './calc',
    test_pattern: '^TestValue$', source_paths: ['go.mod', 'calc/value.go', 'calc/value_test.go'],
    toolchain_root: 'C:/trusted-go', timeout_seconds: 90, process_limit: 32,
    memory_mib: 1024, max_text_bytes: 4096 }] } }
const scope = () => ({ projectId: 'project-1', sessionId: 'session-1', modelRef: 'model-1',
  model: { provider_id: 'local', model_id: 'fixture' }, coding: coding() })
const review = () => ({ resource_generation: 0, workspace: { authorized_workspace_ref: 'workspace-1',
  display_name: 'Trusted workspace', display_path: 'C:/trusted-workspace', project_id: 'project-1',
  revision: 1, access: 'READ_WRITE', status: 'ACTIVE' } })
const original = JSON.stringify(['project-1', 'session-1', 1, 1])
const recheck = () => ({ context: original, scope: scope(), review: review() })
const prepare = f => f.manager.prepareCoding(scope(), original, review())
const approve = f => f.manager.confirmCoding(async () => true, async () => recheck())
const configuredResult = (f, ref) => ({ state: 'CODING_CONFIGURED', request_id: 'coding-1',
  request_hash: hash, project_id: 'project-1', session_id: 'session-1',
  old_model_config_ref: 'model-1', model_config_ref: 'model-2', runtime_status: 'REGISTERED',
  profile_ref: ref, model_calls: 0, normal_max_model_calls: 8, qualification_model_calls: 1,
  qualification_tool_calls: 0, scope: coding(), frozen_checks: f.manager.codingIntent.frozenChecks,
  revision: 2, config_revision: 2 })

const qualificationContext = (changes = {}) => JSON.stringify(Object.assign(
  ['project-1', 'session-1', '1', '1', 'desktop-shell', '2026-10-14T01:00:00Z', 2, 4], changes))
async function settledQualification(f) {
  f.setContext(qualificationContext())
  await f.manager.prepare(scope(), qualificationContext())
  await f.manager.confirm()
}


test('independent valid Artifact ID and revision boundaries settle original confirm and status', async () => {
 for (const id of ['a','A_.:-9','a'.repeat(128),'a'.repeat(129),'a'.repeat(160)]) {
  for (const revision of [1,Number.MAX_SAFE_INTEGER]) {
   const f=fixture();try {
    const value={...profileRef(),id,revision};f.setProfileRef(value);await prepare(f);
    const settled=await approve(f);assert.deepEqual(settled.profile_ref,value);
    const status=await f.manager.statusCoding();assert.deepEqual(status.profile_ref,value);
    assert.equal(status.commit_key,settled.commit_key);assert(Object.isFrozen(status.profile_ref));
    assert.throws(()=>{status.profile_ref.id='mutated'},TypeError);
    assert.equal(f.manager.codingIntent.profileRef.id,id);
   } finally {f.close()}
  }
 }
});
test('independent existing result guards remain fail closed with valid Artifact ref', async () => {
 const mutations={state:'EXECUTION_SETTLED',request_id:'foreign',request_hash:'sha256:'+'0'.repeat(64),project_id:'foreign',session_id:'foreign',old_model_config_ref:'foreign',model_config_ref:'bad/ref',runtime_status:'QUALIFIED',model_calls:1,normal_max_model_calls:9,qualification_model_calls:2,qualification_tool_calls:1,scope:{},frozen_checks:[],revision:1.5,config_revision:Number.MAX_SAFE_INTEGER+1};
 for(const [key,value] of Object.entries(mutations)) { const f=fixture();try {
  await prepare(f);const result={...configuredResult(f,profileRef()),[key]:value};
  assert.throws(()=>f.manager.acceptCodingResult(f.manager.codingIntent,result),{code:'CODING_RESULT_INVALID'},key);
  assert.equal(f.manager.codingIntent.state,'AWAITING_CODING_CONFIRMATION');assert.equal(f.manager.codingIntent.profileRef,undefined);
 } finally {f.close()} }
});
