import React, { useEffect, useState } from 'react'

const unfinished = task => !['ACCEPTED', 'CANCELLED'].includes(task.status)

function taskLink(event, path, navigate) {
  if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return
  event.preventDefault()
  navigate(path)
}

export function SessionContinuation({ api, projectId, snapshot, navigate }) {
  const [attempt, setAttempt] = useState(0)
  const [state, setState] = useState({ loading: true, goal: null, tasks: [], error: null })
  const goalId = snapshot.goal_id

  useEffect(() => {
    const controller = new AbortController()
    setState({ loading: !!goalId, goal: null, tasks: [], error: null })
    if (!goalId) return () => controller.abort()

    async function read() {
      try {
        const goal = await api.call('getGoal', { params: { projectId, id: goalId }, signal: controller.signal })
        if (goal.id !== goalId || goal.project_id !== projectId || !Array.isArray(goal.task_ids) || new Set(goal.task_ids).size !== goal.task_ids.length) {
          throw new Error('目标与当前会话或项目不一致，请重新读取')
        }
        const tasks = []
        // Bound concurrency while reading every Task named by the Goal, including later pages.
        for (let offset = 0; offset < goal.task_ids.length; offset += 10) {
          const batch = await Promise.all(goal.task_ids.slice(offset, offset + 10).map(id =>
            api.call('getTask', { params: { projectId, id }, signal: controller.signal })
          ))
          if (controller.signal.aborted) return
          for (let index = 0; index < batch.length; index++) {
            const task = batch[index]
            if (task.id !== goal.task_ids[offset + index] || task.project_id !== projectId || task.goal_id !== goalId) {
              throw new Error('任务与当前目标或项目不一致，请重新读取')
            }
            tasks.push(task)
          }
        }
        if (tasks.length !== goal.task_ids.length) throw new Error('目标任务尚未完整读取，请重新读取')
        if (!controller.signal.aborted) setState({ loading: false, goal, tasks, error: null })
      } catch (error) {
        if (!controller.signal.aborted) setState({ loading: false, goal: null, tasks: [], error })
      }
    }
    read()
    return () => controller.abort()
  }, [api, projectId, snapshot.session_id, goalId, snapshot.revision, attempt])

  const pending = state.tasks.filter(unfinished)
  return <section className="panel goal-section session-continuation" data-goal-id={state.goal?.id} aria-label="当前目标与待办任务">
    <div className="section-heading"><h2>当前目标</h2>{state.goal && <span className="tag">{state.goal.status}</span>}</div>
    {!goalId && <p className="empty-state">当前会话尚未关联目标。</p>}
    {goalId && state.loading && <p role="status">正在读取当前目标与任务…</p>}
    {goalId && state.error && <div className="state-notice" role="alert"><p>{state.error.message}。当前目标与任务暂不可确认。</p><button type="button" onClick={() => setAttempt(value => value + 1)}>重新读取</button></div>}
    {state.goal && <><h3>{state.goal.title}</h3><p>{state.goal.original_intent}</p>
      {pending.length > 0 ? <><h3>{pending.length === 1 ? '待继续任务' : `待办任务（${pending.length}）`}</h3><div className="record-list">{pending.map(task => {
        const path = `/p/${encodeURIComponent(projectId)}/tasks/${encodeURIComponent(task.id)}`
        return <a key={task.id} className="task-row" href={path} onClick={event => taskLink(event, path, navigate)}><span><strong>{task.title}</strong><small>{task.status}</small></span><span>查看任务 →</span></a>
      })}</div></> : <p className="empty-state">此目标暂无未完成任务。</p>}
    </>}
  </section>
}
