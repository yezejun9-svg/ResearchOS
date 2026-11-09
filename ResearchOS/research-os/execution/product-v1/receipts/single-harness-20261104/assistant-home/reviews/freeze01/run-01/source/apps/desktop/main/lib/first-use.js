'use strict';

const path = require('node:path');

// The host opens the operating-system folder chooser and issues a short-lived
// selection reference. A renderer path or an Electron-only dialog cannot grant
// workspace authority.
async function chooseWorkspace({ host, native, callV2, deps, contextStore, sessionState }, body = {}) {
  const displayName = typeof body.display_name === 'string' ? body.display_name.trim() : '';
  if (displayName.length > 200) return { ok: false, reason: 'DISPLAY_NAME_TOO_LONG' };
  const started = await host.ensureCore(deps);
  if (!started.discovery) return { ok: false, reason: started.health };
  let choice;
  try {
    // Credential bootstrap is entirely inside main and may renew an expired host session.
    await deps.credentialFor(started.discovery);
    const instance = native.hostInstanceId(deps.fsImpl, started.discovery);
    choice = await native.dialNative('\\\\.\\pipe\\ResearchOSHost-v1-' + instance.slice(5), {
      kind: 'NATIVE_WORKSPACE_CHOOSE_REQUEST', client_id: deps.clientId || 'desktop-shell',
      payload: { requested_path: null, requested_access: 'READ_WRITE' },
    }, 5 * 60 * 1000);
  } catch (error) { return { ok: false, reason: String(error.message || error) }; }
  if (choice?.kind === 'NATIVE_ERROR') return { ok: false, reason: 'NATIVE_' + String(choice.error?.code || 'ERROR') };
  const selected = choice?.payload;
  if (choice?.kind !== 'NATIVE_WORKSPACE_CHOOSE_RESULT' ||
      typeof selected?.selection_ref !== 'string' || !selected.selection_ref ||
      typeof selected?.display_path !== 'string' || !selected.display_path) {
    return { ok: false, reason: 'NATIVE_CHOICE_INVALID' };
  }
  const name = displayName || path.basename(selected.display_path);
  const firstUseState = { projectId: null, sessionId: null, expectedRevision: null, writerEpoch: null };
  const firstUseDeps = { ...deps, sessionState: firstUseState };
  const registered = await callV2(firstUseDeps, 'workspace.register', {
    selection_ref: selected.selection_ref, display_name: name, requested_access: 'READ_WRITE',
  });
  const workspaceRef = registered.result?.authorized_workspace_ref;
  if (!registered.ok || registered.completed !== true || typeof workspaceRef !== 'string' || !workspaceRef) {
    return { ok: false, reason: registered.reason || registered.error_code || 'WORKSPACE_REGISTER_FAILED', protocol_status: registered.protocol_status };
  }
  const bootstrapped = await callV2(firstUseDeps, 'project.bootstrap', {
    authorized_workspace_ref: workspaceRef, display_name: name,
  });
  const result = bootstrapped.result;
  if (!bootstrapped.ok || bootstrapped.completed !== true || typeof result?.project_id !== 'string' || !result.project_id ||
      result.workspace?.project_id !== result.project_id || result.workspace?.status !== 'ACTIVE' ||
      typeof result.workspace?.authorized_workspace_ref !== 'string') {
    return { ok: false, reason: bootstrapped.reason || bootstrapped.error_code || 'PROJECT_BOOTSTRAP_FAILED', protocol_status: bootstrapped.protocol_status };
  }
  // expectedRevision belongs to a client session. A project profile revision
  // is not a session CAS value; session.create requires both fields to be null.
  const next = { projectId: result.project_id, sessionId: null, expectedRevision: null, writerEpoch: null };
  try { contextStore.save(next); }
  catch { return { ok: false, reason: 'CONTEXT_STORE_FAILED', project_id: result.project_id }; }
  Object.assign(sessionState, next);
  return { ok: true, project_id: result.project_id, authorized_workspace_ref: result.workspace.authorized_workspace_ref,
    display_name: name, display_path: selected.display_path, result };
}

module.exports = { chooseWorkspace };
