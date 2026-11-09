import fs from 'node:fs'
import path from 'node:path'
import crypto from 'node:crypto'
import http from 'node:http'
import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'

const worktree = path.resolve(process.argv[2])
const root = path.resolve(process.argv[3])
const receipt = path.dirname(fileURLToPath(import.meta.url))
const runId = process.argv[4] || 'run2'
const require = createRequire(import.meta.url)
const { createDesktopManagement, installedResources } = require(path.join(worktree, '.local/managed-client-bound-final3/apps/desktop/main/lib/desktop-management.js'))
const candidateDir = path.join(root, '.local/builds/desktop-managed-qualification-core-repair-v2-20261012')
const controlExe = path.join(candidateDir, 'researchos-control.exe')
const verifierExe = path.join(candidateDir, 'runtime-verifier.exe')
const runtimeAssetsDir = path.join(root, '.local/builds/current-chat-runtime-assets-20261012')
const fixture = path.join(receipt, `real-core-fixture-${runId}`)
const dataRoot = path.join(fixture, 'data')
const discoveryFile = path.join(fixture, 'discovery.json')
const verifierManifest = path.join(fixture, 'runtime-verifier-installation.json')
const hash = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex')
const expected = { control: 'a97e5e8d52d9523817a49b682bce75df243bd8569286ff92b49d31575886e44b',
  verifier: '35dfc144a98627dc4204239f4cd2f63c9f40aa0001cf77a9dddf30dd8b727063' }
if (hash(controlExe) !== expected.control || hash(verifierExe) !== expected.verifier) throw Error('CANDIDATE_IMAGE_MISMATCH')
fs.mkdirSync(fixture, { recursive: true })
fs.writeFileSync(verifierManifest, JSON.stringify({ schema: 'researchos.runtime-verifier-installation.v1',
  service_id: 'researchos.runtime-qualification-verifier.v1', protocol: 'researchos.runtime-verifier/1',
  executable: verifierExe, executable_hash: 'sha256:' + expected.verifier,
  source_commit: '0df32ed4eeeba3b9714477ccfae759ef90b633ee', arguments: [] }, null, 2) + '\n')
const frames = [], diagnostic = [], result = { evidence_class: 'SOURCE_SYNTHETIC_REAL_BINARY',
  candidate_commit: '0df32ed4eeeba3b9714477ccfae759ef90b633ee', control_sha256: expected.control,
  verifier_sha256: expected.verifier, data_root: dataRoot, actual_model_calls: 0, confirm_sent: false,
  started_at: new Date().toISOString() }
result.paths = { controlExe, verifierExe, verifierManifest, runtimeAssetsDir, dataRoot, discoveryFile }
try { result.installation_preflight = installedResources({ controlExe, verifierManifest, runtimeAssetsDir }) }
catch (error) { result.installation_preflight_error = error.code || error.message }
const manager = createDesktopManagement({ controlExe, verifierManifest, runtimeAssetsDir,
  dataRoot, discoveryFile, webDir: path.join(worktree, '.local/managed-client-bound-final3/apps/web/dist'),
  cwd: worktree, httpImpl: http, context: () => 'synthetic-scope',
  diagnostic: message => diagnostic.push(message) })
const onLine = manager.onLine.bind(manager)
manager.onLine = raw => { frames.push({ direction: 'core_to_desktop', raw: raw.toString('utf8') }); return onLine(raw) }
try {
  result.start = await manager.start()
  result.pid = manager.child?.pid || null
  if (result.start.state !== 'READY') throw Error('CANDIDATE_MANAGEMENT_NOT_READY:' + result.start.reason)
  const write = manager.child.stdin.write.bind(manager.child.stdin)
  manager.child.stdin.write = (bytes, callback) => {
    frames.push({ direction: 'desktop_to_core', raw: bytes.toString('utf8').trimEnd() })
    return write(bytes, callback)
  }
  try {
    await manager.prepare({ projectId: 'p-synthetic', sessionId: 's-synthetic', modelRef: 'mc-synthetic',
      model: { provider_id: 'fixture', model_id: 'no-model-call' } }, 'synthetic-scope')
    result.prepare = 'UNEXPECTED_ACCEPTANCE'
    throw Error('UNBOOTSTRAPPED_SYNTHETIC_SCOPE_ACCEPTED')
  } catch (error) {
    if (error.message === 'UNBOOTSTRAPPED_SYNTHETIC_SCOPE_ACCEPTED') throw error
    result.prepare = { rejected: true, code: error.code || error.message }
  }
  result.shutdown = await manager.shutdown()
  result.status = result.shutdown.process_exit_confirmed && result.prepare.rejected ? 'CANDIDATE_COUPLING_PASS' : 'FAILED'
} catch (error) {
  result.status = 'FAILED'; result.error = error.code || error.message
  if (manager.state === 'READY') {
    try { result.shutdown = await manager.shutdown() }
    catch (shutdownError) { result.shutdown_error = shutdownError.code || shutdownError.message }
  }
} finally {
  result.ended_at = new Date().toISOString()
  result.manager_state = manager.state
  result.diagnostic = diagnostic
  fs.writeFileSync(path.join(receipt, `candidate-coupling-${runId}-private-frames.json`), JSON.stringify(frames, null, 2) + '\n', { flag: 'wx' })
  fs.writeFileSync(path.join(receipt, `candidate-coupling-${runId}-result.json`), JSON.stringify(result, null, 2) + '\n', { flag: 'wx' })
  console.log(JSON.stringify(result))
  if (result.status !== 'CANDIDATE_COUPLING_PASS') process.exitCode = 1
}
