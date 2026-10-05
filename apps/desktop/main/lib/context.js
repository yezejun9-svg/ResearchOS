'use strict';

const fs = require('node:fs');
const path = require('node:path');

function reference(value) {
  return typeof value === 'string' && value.length > 0 && value.length <= 256 ? value : null;
}

function createContextStore(file, fsImpl = fs) {
  return {
    load() {
      try {
        const raw = JSON.parse(fsImpl.readFileSync(file, 'utf8'));
        if (raw.version !== 1) return { projectId: null, sessionId: null };
        const projectId = reference(raw.project_id);
        return { projectId, sessionId: projectId ? reference(raw.session_id) : null };
      } catch { return { projectId: null, sessionId: null }; }
    },
    save(state) {
      const projectId = reference(state.projectId);
      const body = JSON.stringify({ version: 1, project_id: projectId,
        session_id: projectId ? reference(state.sessionId) : null }) + '\n';
      fsImpl.mkdirSync(path.dirname(file), { recursive: true });
      const temp = file + '.' + process.pid + '.tmp';
      try {
        fsImpl.writeFileSync(temp, body, { mode: 0o600 });
        fsImpl.renameSync(temp, file);
      } catch (error) {
        try { fsImpl.unlinkSync(temp); } catch { /* no temporary file to remove */ }
        throw error;
      }
    },
  };
}

module.exports = { createContextStore };
