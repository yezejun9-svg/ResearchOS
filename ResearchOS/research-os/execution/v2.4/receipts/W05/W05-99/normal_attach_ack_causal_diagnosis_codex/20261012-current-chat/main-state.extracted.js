const sessionState = new Proxy(selectedState, { set(target, key, value) {
  if (target[key] !== value) {
    if (key === 'projectId' || key === 'sessionId') target.selectionGeneration++;
    if (['expectedRevision', 'writerEpoch', 'writerClientId', 'writerExpiresAt'].includes(key)) target.authorityGeneration++;
  }
  target[key] = value; return true;
} });
const qualificationContext = () => JSON.stringify([
  sessionState.projectId, sessionState.sessionId,
  sessionState.expectedRevision == null ? null : String(sessionState.expectedRevision),
  sessionState.writerEpoch == null ? null : String(sessionState.writerEpoch),
  sessionState.writerClientId || null, sessionState.writerExpiresAt || null,
  sessionState.selectionGeneration, sessionState.authorityGeneration,
]);
