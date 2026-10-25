'use strict';

// Disposable, browser-only product fixture. Every business request is handled
// here; no request may reach a real Core or remote provider.
const projectId = 'fixture-project';

async function installFixture(page, { native = false, profileError = false, qualificationState = 'NOT_REQUESTED' } = {}) {
  const unexpected = [];
  const requests = [];
  const data = {
    '/v1/projects': { items: [{ project_id: projectId, name: '城市河流研究', intent: '整理水质与治理证据' }] },
    [`/v1/projects/${projectId}/profile`]: { project_id: projectId, name: '城市河流研究', revision: 3 },
    [`/v1/projects/${projectId}/state`]: { project_id: projectId, revision: 3, active_cycle_id: null, blocking_conflict_ids: [] },
    [`/v1/projects/${projectId}/progress`]: { project_id: projectId, plan_revision: 3, as_of_event_sequence: 0, stages: [] },
    [`/v1/projects/${projectId}/releases`]: { items: [] },
    [`/v1/projects/${projectId}/notifications`]: { items: [] },
    [`/v1/projects/${projectId}/goals`]: { items: [] },
    [`/v1/projects/${projectId}/tasks`]: { items: [] },
    [`/v1/projects/${projectId}/research-cycles`]: { items: [] },
    [`/v1/projects/${projectId}/resource-requests`]: { items: [] },
  };
  await page.route('**/*', async route => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    if (path.startsWith('/v1/') || path.startsWith('/v2/')) {
      requests.push({ method: route.request().method(), path });
      if (path.endsWith('/events/stream')) return route.fulfill({ status: 200, contentType: 'text/event-stream', body: ': fixture heartbeat\n\n' });
      if (profileError && path === `/v1/projects/${projectId}/profile`)
        return route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ code: 'FIXTURE_PROFILE_UNAVAILABLE', message: '项目资料暂不可用' }) });
      if (route.request().method() === 'GET' && Object.hasOwn(data, path))
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(data[path]) });
      unexpected.push(`${route.request().method()} ${path}`);
      return route.fulfill({ status: 599, contentType: 'application/json', body: JSON.stringify({ code: 'FIXTURE_UNEXPECTED_REQUEST' }) });
    }
    if (path === '/remote-info') return route.fulfill({ status: 404, body: '{}' });
    if (url.hostname === '127.0.0.1' && (path === '/' || path.startsWith('/p/') || path.startsWith('/assets/')))
      return route.continue();
    unexpected.push(`EXTERNAL ${url.href}`);
    return route.abort();
  });
  if (native) await page.addInitScript(({ projectId, qualificationState }) => {
    const initial = {
      project_id: projectId, session_id: 'session-one', title: '河流污染证据核对', revision: 7,
      event_sequence: 0, earliest_event_sequence: 0, run_status: 'WAITING', active_run_id: null,
      workspace_ref: 'workspace-one', goal_id: null, pending_command_ids: [], pending_permissions: [],
      writer: { client_id: 'fixture-client', expires_at: '2099-01-01T00:00:00Z' },
      messages: [
        { message_id: 'm1', role: 'USER', complete: true, parts: [{ text: '请核对上游与下游水质记录，标出来源不一致的结论。' }] },
        { message_id: 'm2', role: 'ASSISTANT', complete: true, parts: [{ text: '已收到研究问题。下一步先整理来源，再逐条核对采样时间和测点。' }] },
      ],
    };
    const state = { snapshot: initial, sessions: [{ session_id: initial.session_id, title: initial.title, run_status: 'WAITING' }] };
    const completed = result => ({ ok: true, completed: true, protocol_status: 'COMPLETED', result });
    window.__frontendFixtureCalls = [];
    const actions = {
      'host.status': () => ({ client_id: 'fixture-client', model_configurations: [{ model_config_ref: 'model-one', provider_id: 'local', model_id: 'research-model', config_revision: 1 }], workspaces: [{ project_id: projectId, status: 'ACTIVE', authorized_workspace_ref: 'workspace-one', display_name: '研究资料' }] }),
      'session.list': () => ({ items: state.sessions, next_cursor: null }),
      'session.get': () => state.snapshot,
      'session.events': () => ({ events: [], next_sequence: state.snapshot.event_sequence }),
      'session.attach': () => state.snapshot,
      'session.create': body => { const next = { ...initial, session_id: 'session-two', title: body.title, messages: [], revision: 1 }; state.sessions.unshift({ session_id: next.session_id, title: next.title, run_status: 'WAITING' }); state.snapshot = next; return next },
      'session.send': body => { state.snapshot.messages.push({ message_id: `m${state.snapshot.messages.length + 1}`, role: 'USER', complete: true, parts: [{ text: body.text }] }); state.snapshot.pending_command_ids.push('pending-fixture'); return { command_id: 'pending-fixture' } },
      'session.control': () => state.snapshot,
      'workspace.tree': () => ({ entries: [], next_cursor: null }),
      'workspace.diff': () => ({ base: 'HEAD', files: [], total_files: 0, truncated: false }),
    };
    const v2 = Object.fromEntries(Object.entries(actions).map(([name, action]) => [name, async body => { window.__frontendFixtureCalls.push({ name, body }); return completed(action(body || {})) }]));
    window.researchos = { desktop: {
      context: async () => ({ project_id: projectId, session_id: state.snapshot.session_id }),
      selectProject: async () => ({ ok: true }),
      openSession: async sessionId => { const session = state.sessions.find(item => item.session_id === sessionId); if (session) state.snapshot = { ...state.snapshot, session_id: session.session_id, title: session.title }; return completed(state.snapshot) },
      qualificationCurrent: async () => qualificationState === 'AWAITING_CONFIRMATION'
        ? { ok: true, available: true, state: qualificationState, consumed: false, request_id: 'fixture-request', expires_at: '2099-01-01T00:00:00Z', model: { provider_id: 'local', model_id: 'research-model' } }
        : { ok: true, available: false, state: qualificationState },
      codingCurrent: async () => ({ ok: true, available: false, state: 'NOT_REQUESTED' }),
    }, v2 };
  }, { projectId, qualificationState });
  return { unexpected, requests, projectId };
}

module.exports = { installFixture, projectId };
