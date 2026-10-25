import React from 'react'

export function WorkbenchLayout({ sessions, conversation, context }) {
  return <div className="workbench-layout">
    <aside className="workbench-session-pane" aria-label="项目会话">{sessions}</aside>
    <section className="workbench-conversation-pane" aria-label="当前研究会话">{conversation}</section>
    <aside className="workbench-context-pane" aria-label="工作区、配置与资格">{context}</aside>
  </div>
}
