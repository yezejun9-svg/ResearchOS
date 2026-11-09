async function prepareQualificationScope() {
  if (!v2Deps.contextVerified || !sessionState.projectId || !sessionState.sessionId)
    throw Object.assign(new Error('SESSION_NOT_SELECTED'), { code: 'SESSION_NOT_SELECTED' });
  const projectId = sessionState.projectId, sessionId = sessionState.sessionId;
  const selectionGeneration = sessionState.selectionGeneration;
  desktopManagement.currentHost();
  const opened = await ipc.callV2(v2Deps, 'session.get', {}, ipc.AUTHORITY_READ);
  desktopManagement.currentHost();
  if (!opened?.completed || opened.result?.project_id !== projectId || opened.result?.session_id !== sessionId ||
      sessionState.projectId !== projectId || sessionState.sessionId !== sessionId ||
      sessionState.selectionGeneration !== selectionGeneration)
    throw Object.assign(new Error('SESSION_CHANGED'), { code: 'SESSION_CHANGED' });
  const snapshot = opened.result, context = qualificationContext();
  if (snapshot.writer?.client_id !== 'desktop-shell' || Date.parse(snapshot.writer?.expires_at) <= Date.now() ||
      String(snapshot.writer?.epoch) !== String(sessionState.writerEpoch) ||
      String(snapshot.revision) !== String(sessionState.expectedRevision))
    throw Object.assign(new Error('WRITE_OWNER_REQUIRED'), { code: 'WRITE_OWNER_REQUIRED' });
  const status = await ipc.callV2(v2Deps, 'host.status', {}, ipc.AUTHORITY_READ);
  const currentHost = desktopManagement.currentHost();
  if (qualificationContext() !== context || !status?.completed ||
      status.local_host_origin !== crypto.createHash('sha256').update(JSON.stringify([
        desktopManagement.hostId, currentHost.data_dir])).digest('hex'))
    throw Object.assign(new Error('HOST_OR_CONTEXT_CHANGED'), { code: 'HOST_OR_CONTEXT_CHANGED' });
  const modelRef = snapshot.model_config_ref;
  const model = status.result?.model_configurations?.find(item => item.model_config_ref === modelRef);
  if (!model || !model.provider_id || !model.model_id)
    throw Object.assign(new Error('SESSION_MODEL_UNAVAILABLE'), { code: 'SESSION_MODEL_UNAVAILABLE' });
  return { context, snapshot, hostStatus: status.result, scope: { projectId, sessionId, modelRef,
    model: { provider_id: model.provider_id, model_id: model.model_id } } };
}
