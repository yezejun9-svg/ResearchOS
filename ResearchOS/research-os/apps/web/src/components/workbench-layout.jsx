import React, { useEffect, useState } from 'react'

export function WorkbenchLayout({ sessions, conversation, context, hasSession, variant = '', sessionTools = null, historyExpanded, historyHint }) {
  const [expanded, setExpanded] = useState(historyExpanded ?? !hasSession)
  useEffect(() => setExpanded(historyExpanded ?? !hasSession), [hasSession, historyExpanded])
  return <div className={`workbench-layout ${variant ? `workbench-layout-${variant}` : ''}`}>
    <div className="workbench-main-column">
      {sessionTools}
      <details className="workbench-sessions-disclosure" open={expanded} onToggle={event => setExpanded(event.currentTarget.open)}>
        <summary><span>{variant === 'assistant' ? '任务历史' : '项目会话'}</span><small>{historyHint ?? (hasSession ? '切换 / 新建' : '选择一个会话，开始协作')}</small></summary>
        <aside className="workbench-session-pane" aria-label="项目会话">{sessions}</aside>
      </details>
      <section className="workbench-conversation-pane" aria-label="当前研究会话">{conversation}</section>
    </div>
    <aside className="workbench-context-pane" aria-label="项目进度、执行轨迹与工作区">{context}</aside>
  </div>
}
