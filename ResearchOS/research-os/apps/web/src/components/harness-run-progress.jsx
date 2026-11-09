import React from 'react'
import { projectHarnessProgress } from '../harness-progress.js'
import { harnessSubmissionBlockers } from '../harness.js'

export function HarnessRunProgress({ task, events }) {
  const progress = projectHarnessProgress(task, events)
  if (progress.empty) return <section className="harness-run-progress" aria-label="Codex 任务进度"><p className="harness-progress-empty">尚无选中的 Task。提交只读任务后，这里会显示实际回执。</p></section>
  return <section className="harness-run-progress" aria-label="Codex 任务进度">
    <div className="harness-progress-heading"><strong>任务进度</strong><small>仅展示 Host 已记录的状态和当前事件窗口</small></div>
    <ol className="harness-progress-stages">{progress.stages.map(stage => <li key={stage.key} data-state={stage.state}>
      <span className="harness-progress-dot" aria-hidden="true"/><div><strong>{stage.title}</strong><span>{stage.detail}</span></div>
    </li>)}</ol>
  </section>
}

export function HarnessPermissionNotice({ capabilities }) {
  const blockers = harnessSubmissionBlockers(capabilities)
  if (!blockers.length) return null
  return <div className="harness-permission-notice" role="status">
    <strong>暂不能提交只读任务</strong>
    <ul>{blockers.map(item => <li key={item.code}>{item.message}</li>)}</ul>
    <p>安装或登录状态不代表执行权限已验证。</p>
    <details><summary>技术原因</summary><code>{blockers.map(item => item.code).join(' · ')}</code></details>
  </div>
}
