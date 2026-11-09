import React from 'react'; import {createRoot} from 'react-dom/client';
    import {DesktopCodingAuthorization} from '/@fs/D:/作品集/ResearchOS/research-os/.local/worktrees/w05-product-coding-client-20261012/.local/coding-client-bound-final3/apps/web/src/workbench.jsx';
    let root; window.remount = (session='session-1') => { root?.unmount(); root=createRoot(document.getElementById('root'));
      root.render(<DesktopCodingAuthorization projectId="project-1" sessionId={session} onConfigured={() => window.codingRefresh()}/>); };
    window.remount();