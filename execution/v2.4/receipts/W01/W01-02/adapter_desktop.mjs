// Narrow ResearchOS desktop adapter for qualification (W01-02).
// Implements the NativeClient method surface actually used by Mu native screens
// (create/list/open/request/respond/rename/remove/pickFolder/enabled +
//  onChanged/onStatus/onReplaced/onRecord/onAttention), backed by the shared SessionSupervisor.
// Injection point in product will be NativeClientContext at
// desktop/packages/desktop/src/renderer/pages/native/utils/nativeClient.ts (located, not patched here).
export function createResearchOSDesktopClient(supervisor) {
  const conversations = new Map();
  const listeners = { changed: [], status: [], replaced: [], record: [], attention: [] };
  supervisor.on('event', (rec) => {
    const k = rec.event && rec.event.kind;
    if (k === 'worker_exit') listeners.status.forEach((f) => f({ up: false }));
    listeners.record.forEach((f) => f(rec));
    if (rec.event && rec.event.type === 'message_update') listeners.changed.forEach((f) => f(rec));
    if (rec.event && rec.event.type === 'turn_start') listeners.attention.forEach((f) => f(rec));
  });
  const api = {
    async enabled() { return { provider: 'shared-session-supervisor', ok: !supervisor.childExited }; },
    async create(meta = {}) {
      const id = 'conv-' + (conversations.size + 1);
      conversations.set(id, { id, title: meta.title || 'qualification', sessionId: supervisor.sessionId, createdAt: Date.now() });
      listeners.changed.forEach((f) => f({ type: 'created', id }));
      return { conversation: conversations.get(id), message: null };
    },
    async list() { return { conversations: [...conversations.values()] }; },
    async rename(id, title) { const c = conversations.get(id); if (c) c.title = title; listeners.replaced.forEach((f) => f({ type: 'renamed', id })); return { conversation: c, messages: [] }; },
    async remove(id) { conversations.delete(id); listeners.changed.forEach((f) => f({ type: 'removed', id })); return { success: true }; },
    async open(id) { return { conversation: conversations.get(id), messages: supervisor.subscribe(0) }; },
    async pickFolder() { return supervisor.workspace; },
    // desktop writer requests go through the SAME supervisor session as CLI
    async request(kind, params) {
      const command = kind === 'prompt' ? { type: 'prompt', message: params.message }
        : kind === 'steer' ? { type: 'steer', message: params.message }
        : kind === 'follow_up' ? { type: 'follow_up', message: params.message }
        : kind === 'abort' ? { type: 'abort' }
        : kind === 'bash' ? { type: 'bash', command: params.command }
        : kind === 'compact' ? { type: 'compact' }
        : { type: 'get_state' };
      return supervisor.write('desktop', command, params.command_id);
    },
    async respond(id, answer) { return { id, answer, ok: true }; },
    onChanged(f) { listeners.changed.push(f); },
    onStatus(f) { listeners.status.push(f); },
    onReplaced(f) { listeners.replaced.push(f); },
    onRecord(f) { listeners.record.push(f); },
    onAttention(f) { listeners.attention.push(f); },
  };
  return api;
}
