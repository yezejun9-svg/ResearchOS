from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[6]
WT=ROOT/'.local/worktrees/w05-desktop-managed-qualification-client-20261012'
source=(OUT/'lifecycle-edges.mjs').read_text(encoding='utf-8').split("const f=fixture('expired-context'")[0]
source=source.replace('function fixture(name,','export function fixture(name,')
(OUT/'fixture-support.mjs').write_text(source,encoding='utf-8')
(OUT/'qualification-entry.html').write_text('<div id="root"></div><script type="module" src="/qualification-entry.jsx"></script>',encoding='utf-8')
ui=(WT/'.local/managed-client-bound-final3/apps/web/src/workbench.jsx').as_posix()
(OUT/'qualification-entry.jsx').write_text("import React from 'react';import {createRoot} from 'react-dom/client';import {DesktopQualification} from '/@fs/"+ui+"';let root;window.remount=(session='session-1')=>{root?.unmount();root=createRoot(document.getElementById('root'));root.render(<DesktopQualification projectId=\"project-1\" sessionId={session}/>)};window.remount();",encoding='utf-8')
