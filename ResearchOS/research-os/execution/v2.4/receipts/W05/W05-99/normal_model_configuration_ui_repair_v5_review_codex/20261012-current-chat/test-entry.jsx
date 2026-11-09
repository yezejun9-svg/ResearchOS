import React from 'react'
import {createRoot} from 'react-dom/client'
import {NativeModelConfiguration} from '/@fs/D:/作品集/ResearchOS/research-os/.local/worktrees/w05-normal-model-ui-repair-v5-20261012/apps/web/src/workbench.jsx'
window.researchos={desktop:{selectProject:project_id=>window.bridge('selectProject',{project_id})},v2:{'host.status':payload=>window.bridge('host.status',payload),'host.configure':payload=>window.bridge('host.configure',payload)}}
let root=createRoot(document.getElementById('root'))
window.mount=(project='fixture_project')=>root.render(React.createElement(NativeModelConfiguration,{key:project,projectId:project}))
window.remount=(project='fixture_project')=>{root.unmount();root=createRoot(document.getElementById('root'));window.mount(project)}
window.mount()

