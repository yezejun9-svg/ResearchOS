import React from 'react'; import {createRoot} from 'react-dom/client';
    import {DesktopCodingAuthorization} from '/@fs/C:/Users/yqyyds/.codex/researchos-build-worktrees/coding-client-v3-20261012/.local/builds/product-coding-client-repair-v3-20261012/apps/web/src/workbench.jsx';
    let root; window.remount = (session='session-1') => { root?.unmount(); root=createRoot(document.getElementById('root'));
      root.render(<DesktopCodingAuthorization projectId="project-1" sessionId={session} onConfigured={() => window.codingRefresh()}/>); };
    window.remount();