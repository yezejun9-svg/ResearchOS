// ResearchOS v2.4 W01-02 qualification supervisor.
// Single host supervising one Mu/Pi 0.87.1 RPC worker; shared session for CLI and Desktop clients.
// NOT product: business authority emulation only (writer epoch, dedupe, journal replay, shutdown).
import { spawn } from 'node:child_process';
import { join } from 'node:path';
import { createInterface } from 'node:readline';
import { EventEmitter } from 'node:events';

export class SessionSupervisor extends EventEmitter {
  constructor({ muRoot, workspace, model, env }) {
    super();
    this.muRoot = muRoot; this.workspace = workspace;
    this.sessionId = 'ros-qual-session-001';
    this.writer = 'cli'; this.epoch = 1;
    this.journal = []; this.seq = 0;
    this.commands = new Map(); // command_id -> {promise, sent}
    this.cost = { providerRequests: 0, actual: null, in_flight: null, cap: null };
    this._pending = new Map(); // request id -> resolve
    this.childExited = false;
    const child = spawn('node', [
      join(muRoot, 'packages', 'coding-agent', 'dist', 'rpc-entry.js'), '--mode', 'rpc', '--model', model,
    ], { cwd: workspace, env: { ...process.env, ...(env || {}) }, stdio: ['pipe', 'pipe', 'pipe'] });
    this.child = child;
    this.rl = createInterface({ input: child.stdout });
    this.rl.on('line', (l) => {
      l = l.trim(); if (!l) return;
      let msg; try { msg = JSON.parse(l); } catch { this.push({ kind: 'stdout_nonjson', raw: l.slice(0, 200) }); return; }
      this.push(msg);
    });
    this.stderrBuf = '';
    child.stderr.on('data', (d) => { this.stderrBuf += d.toString(); });
    child.on('exit', (code, signal) => {
      this.childExited = true;
      this.push({ kind: 'worker_exit', code, signal });
      for (const [, res] of this._pending) res({ ok: false, error: 'worker_exit' });
      this._pending.clear();
    });
    const killWorker = () => { try { child.kill(); } catch { /* already dead */ } };
    process.on('exit', killWorker);
    process.on('SIGINT', () => { killWorker(); process.exit(130); });
    process.on('SIGTERM', () => { killWorker(); process.exit(143); });
    this._killWorker = killWorker;
  }
  push(msg) {
    const rec = { seq: ++this.seq, ts: Date.now(), event: msg };
    this.journal.push(rec);
    this.emit('event', rec);
    if (msg && msg.type) this._route(msg);
  }
  _route(msg) {
    // upstream responses echo request id; treat {id, type:'response'|...} shapes defensively
    if (msg.id && this._pending.has(msg.id)) {
      const res = this._pending.get(msg.id); this._pending.delete(msg.id);
      res({ ok: !(msg.error), msg });
    }
  }
  sendCommand(obj) {
    const payload = JSON.stringify(obj);
    this.child.stdin.write(payload + '\n');
    if (obj.type === 'prompt' || obj.type === 'bash') this.cost.providerRequests += 1;
    return new Promise((resolve) => {
      if (obj.id) this._pending.set(obj.id, resolve); else resolve({ ok: true, msg: { fireAndForget: true } });
      setTimeout(() => { if (this._pending.has(obj.id)) { this._pending.delete(obj.id); resolve({ ok: true, msg: { noEcho: true, last: this.journal.slice(-1)[0] } }); } }, 3000);
    });
  }
  // client write with epoch authority; duplicate command_id NOT re-executed
  async write(client, command, commandId) {
    if (client !== this.writer) {
      return { status: 'REJECTED_STALE_EPOCH', client, writer: this.writer, epoch: this.epoch };
    }
    if (commandId && this.commands.has(commandId)) {
      return { status: 'DEDUPED', command_id: commandId, prior: this.commands.get(commandId) };
    }
    const stamped = { ...command, id: commandId || `c-${this.seq + 1}` , ros: { session_id: this.sessionId, writer_epoch: this.epoch, client } };
    const r = await this.sendCommand(stamped);
    if (commandId) this.commands.set(commandId, r);
    return { status: 'EXECUTED', command_id: stamped.id, result: r };
  }
  handoff(toClient) { this.writer = toClient; this.epoch += 1; const rec = { status: 'HANDOFF', writer: toClient, epoch: this.epoch }; this.push({ kind: 'writer_handoff', ...rec }); return rec; }
  subscribe(fromSeq = 0) { return this.journal.filter((r) => r.seq > fromSeq); }
  async waitUntil(pred, timeoutMs = 120000) {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      const hit = this.journal.find(pred); if (hit) return hit;
      await new Promise((r) => setTimeout(r, 100));
    }
    return null;
  }
  shutdown() { this.sendCommand({ type: 'abort' }); setTimeout(this._killWorker, 500); }
}
