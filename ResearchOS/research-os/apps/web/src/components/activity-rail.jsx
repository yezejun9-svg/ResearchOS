import React, { useEffect, useState } from 'react'
import { activityRows, harnessActivityRows } from '../activity.js'
import { display } from '../../../desktop/main/lib/wire-values.mjs'
import { Link, stages } from '../navigation'
import { itemsOf } from '../api'

export function ActivityRail({ events, snapshot, harnessTask, projection, projectState, releases, projectId, navigate }) {
  const [expanded, setExpanded] = useState(false)
  useEffect(() => setExpanded(false), [snapshot?.session_id, harnessTask?.task_ref?.task_id])
  const activity = harnessTask ? harnessActivityRows(events, harnessTask.task_ref) : activityRows(events, snapshot?.session_id)
  const visibleActivity = expanded ? activity : activity.slice(0, 12)
  const latestRelease = itemsOf(releases).at(-1)
  return <>
    <section className="iteration-overview" aria-label="项目迭代进度">
      <div className="inspector-heading"><div><span className="workbench-eyebrow">PROJECT PULSE</span><h2>项目近况</h2></div><span className="inspector-label">状态投影</span></div>
      {projection ? <><p className="inspector-caption">计划 {projection.plan_revision} · 水位 #{projection.as_of_event_sequence}</p>
        <ol className="iteration-stages">{stages.map(([stage, label]) => {
          const item = projection.stages?.find(value => value.stage === stage)
          const known = item && Number.isSafeInteger(item.planned) && item.planned >= 0 && Number.isSafeInteger(item.accepted) && item.accepted >= 0
          return <li key={stage}><div><strong>{label}</strong><span>{known ? `${item.accepted} / ${item.planned}` : '尚无计划'}</span></div>
            {known && item.planned > 0 && <progress value={item.accepted} max={item.planned} aria-label={`${label}已验收 ${item.accepted}，计划 ${item.planned}`}/>}
            {item && (item.active > 0 || item.pending_review > 0 || item.blocked > 0) && <small>{[item.active > 0 && `${item.active} 进行中`, item.pending_review > 0 && `${item.pending_review} 待评审`, item.blocked > 0 && `${item.blocked} 受阻`].filter(Boolean).join(' · ')}</small>}
          </li>
        })}</ol>{projection.plan_change_note && <p className="inspector-caption">{projection.plan_change_note}</p>}</> : <p className="inspector-empty">正在等待项目进度回执。</p>}
      {projectState?.blocking_conflict_ids?.length > 0 && <p className="inspector-warning">{projectState.blocking_conflict_ids.length} 项冲突等待处理</p>}
      <div className="accepted-delivery"><span className="workbench-eyebrow">LATEST ACCEPTED</span>{latestRelease ? <Link to={`/p/${projectId}/releases/${latestRelease.id}`} navigate={navigate}><strong>{latestRelease.summary}</strong><small>里程碑 {latestRelease.sequence} · 查看成果</small></Link> : <p className="inspector-caption">尚无已验收成果</p>}</div>
    </section>
    <section className="activity-rail" aria-label="执行轨迹">
      <div className="inspector-heading"><div><span className="workbench-eyebrow">ACTIVITY</span><h2>执行轨迹</h2></div><span className="inspector-label">当前会话</span></div>
      {activity.length ? <ol className="activity-timeline">{visibleActivity.map(({ event, title, summary, tone }) => <li className={`activity-item activity-${tone}`} key={event.event_id}>
        <span className="activity-marker" aria-hidden="true"/><details><summary><span className="activity-item-heading"><strong>{title}</strong><span>#{String(event.sequence)}</span></span><span className="activity-summary">{summary}</span></summary>
          <div className="activity-receipt"><small>事件 {event.event_id}</small>{(event.run_id || event.run?.run_id) && <small>运行 {event.run_id || event.run.run_id}{event.run?.epoch ? ` · epoch ${event.run.epoch}` : ''}</small>}<details><summary>技术回执</summary><pre>{display(event.payload)}</pre></details></div>
        </details>
      </li>)}</ol> : <div className="inspector-empty"><p>每一步，都有迹可循。</p><small>开始会话后，工具调用、执行结果和产物会显示在这里。</small></div>}
      {activity.length > 12 && <button type="button" className="activity-expand" aria-expanded={expanded} onClick={() => setExpanded(value => !value)}>{expanded ? '只看最近 12 条' : `展开已读取轨迹（${activity.length}）`}</button>}
      <p className="inspector-caption">按已读取事件投影。执行结束与成果验收分别记录。</p>
    </section>
  </>
}
