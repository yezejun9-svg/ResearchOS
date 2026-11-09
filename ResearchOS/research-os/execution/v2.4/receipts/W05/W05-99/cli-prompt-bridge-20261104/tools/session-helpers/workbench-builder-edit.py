from pathlib import Path

root = Path(r'D:\作品集\ResearchOS\research-os\.local\worktrees\workbench-experience-20261104')

def write(name, content):
    p = root / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding='utf-8', newline='\n')

write('apps/web/src/activity.js', '''const activityKinds = new Set(['TOOL_STARTED', 'TOOL_RESULT', 'RUN_STATE', 'GOAL_STATE', 'ARTIFACT', 'JUDGE_DECISION', 'ERROR', 'USAGE'])
const outcomes = { SUCCEEDED: '工具成功', FAILED: '工具失败', CANCELLED: '已取消', BLOCKED: '受阻', UNKNOWN: '结果待核对' }
const runStates = { QUEUED: '排队中', STARTING: '启动中', RUNNING: '执行中', CANCEL_REQUESTED: '正在取消', SETTLED: '执行已结束', FAILED: '执行失败', CANCELLED: '已取消', LOST: '连接丢失', RECONCILING: '恢复核对中' }
const goalStates = { DRAFT: '目标草稿', ACTIVE: '目标进行中', PAUSED: '目标已暂停', VERIFYING: '目标验收中', ACCEPTED: '目标已验收', FAILED: '目标失败', CANCELLED: '目标已取消', BLOCKED: '目标受阻' }

export function activityRows(events, sessionId) {
  if (!sessionId) return []
  const seen = new Set(), tools = new Map()
  const ordered = events.filter(event => {
    if (event.session_id !== sessionId || !event.event_id || !Number.isSafeInteger(event.sequence) || seen.has(event.event_id)) return false
    seen.add(event.event_id)
    return true
  }).sort((a, b) => a.sequence - b.sequence)
  return ordered.filter(event => activityKinds.has(event.kind)).map(event => {
    const payload = event.payload || {}
    if (event.kind === 'TOOL_STARTED') tools.set(payload.tool_call_id, payload.tool_name)
    let title, summary, tone = 'neutral'
    switch (event.kind) {
      case 'TOOL_STARTED': title = payload.tool_name || '调用工具'; summary = payload.input_summary || '工具调用已发起'; break
      case 'TOOL_RESULT':
        title = tools.get(payload.tool_call_id) || '工具结果'
        summary = `${outcomes[payload.outcome] || '结果待核对'}${payload.summary ? ` · ${payload.summary}` : ''}`
        tone = payload.outcome === 'FAILED' ? 'error' : payload.outcome === 'SUCCEEDED' ? 'success' : 'neutral'
        break
      case 'RUN_STATE': title = runStates[payload.status] || '运行状态待核对'; summary = payload.reason || '执行状态回执'; tone = payload.status === 'FAILED' ? 'error' : 'neutral'; break
      case 'GOAL_STATE': title = goalStates[payload.status] || '目标状态待核对'; summary = payload.goal_id ? `目标修订 ${payload.revision}` : '目标状态回执'; tone = payload.status === 'ACCEPTED' ? 'success' : 'neutral'; break
      case 'ARTIFACT': title = '产物回执'; summary = { AVAILABLE: '产物已可用，验收状态另行核对', SUPERSEDED: '产物已被新版本替代', REVOKED: '产物访问已撤销' }[payload.availability] || '产物状态待核对'; break
      case 'JUDGE_DECISION': title = '判断建议'; summary = payload.summary || '查看判断回执与用途资格'; break
      case 'ERROR': title = '需要处理'; summary = payload.message || payload.summary || '查看错误回执'; tone = 'error'; break
      case 'USAGE': title = '用量回执'; summary = payload.cost_known === true && payload.money != null ? `${payload.money.amount} ${payload.money.currency}` : '费用待结算'; break
    }
    return { event, title, summary, tone }
  }).reverse().slice(0, 12)
}

export function composerSubmitKey(event) {
  return event.key === 'Enter' && !event.shiftKey && !event.altKey && !event.isComposing && !event.nativeEvent?.isComposing && event.keyCode !== 229 && event.nativeEvent?.keyCode !== 229
}
''')

write('apps/web/src/components/activity-rail.jsx', '''import React from 'react'
import { activityRows } from '../activity.js'
import { display } from '../../../desktop/main/lib/wire-values.mjs'
import { Link, stages } from '../navigation'
import { itemsOf } from '../api'

export function ActivityRail({ events, snapshot, projection, projectState, releases, projectId, navigate }) {
  const activity = activityRows(events, snapshot?.session_id)
  const latestRelease = itemsOf(releases).at(-1)
  return <>
    <section className="iteration-overview" aria-label="项目迭代进度">
      <div className="inspector-heading"><div><span className="workbench-eyebrow">PROJECT PULSE</span><h2>项目近况</h2></div><span className="inspector-label">实时回执</span></div>
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
      {activity.length ? <ol className="activity-timeline">{activity.map(({ event, title, summary, tone }) => <li className={`activity-item activity-${tone}`} key={event.event_id}>
        <span className="activity-marker" aria-hidden="true"/><details><summary><span className="activity-item-heading"><strong>{title}</strong><span>#{event.sequence}</span></span><span className="activity-summary">{summary}</span></summary>
          <div className="activity-receipt"><small>事件 {event.event_id}</small>{event.run_id && <small>运行 {event.run_id}</small>}<details><summary>技术回执</summary><pre>{display(event.payload)}</pre></details></div>
        </details>
      </li>)}</ol> : <div className="inspector-empty"><p>每一步，都有迹可循。</p><small>开始会话后，工具调用、执行结果和产物会显示在这里。</small></div>}
      <p className="inspector-caption">执行结束与成果验收分别记录。</p>
    </section>
  </>
}
''')

write('apps/web/src/components/workbench-layout.jsx', '''import React, { useEffect, useState } from 'react'

export function WorkbenchLayout({ sessions, conversation, context, hasSession }) {
  const [expanded, setExpanded] = useState(!hasSession)
  useEffect(() => setExpanded(!hasSession), [hasSession])
  return <div className="workbench-layout">
    <div className="workbench-main-column">
      <details className="workbench-sessions-disclosure" open={expanded} onToggle={event => setExpanded(event.currentTarget.open)}>
        <summary><span>项目会话</span><small>{hasSession ? '切换 / 新建' : '选择一个会话，开始协作'}</small></summary>
        <aside className="workbench-session-pane" aria-label="项目会话">{sessions}</aside>
      </details>
      <section className="workbench-conversation-pane" aria-label="当前研究会话">{conversation}</section>
    </div>
    <aside className="workbench-context-pane" aria-label="项目进度、执行轨迹与工作区">{context}</aside>
  </div>
}
''')

p=root/'apps/web/src/workbench.jsx'
s=p.read_text(encoding='utf-8')
s=s.replace("import { WorkbenchLayout } from './components/workbench-layout.jsx'", "import { WorkbenchLayout } from './components/workbench-layout.jsx'\nimport { ActivityRail } from './components/activity-rail.jsx'\nimport { composerSubmitKey } from './activity.js'\nimport './workbench.css'")
s=s.replace('function Panel({ title, children, aside }) { return <section className="panel">', 'function Panel({ title, children, aside, className = \'\' }) { return <section className={`panel ${className}`}>')
s=s.replace('setState(old => ({ ...old, snapshot, error: null }))', 'setState(old => ({ ...old, snapshot, events: old.snapshot?.session_id === snapshot.session_id ? old.events : [], error: null }))', 1)
s=s.replace('page.events.filter(item => !seen.has(item.event_id))', 'page.events.filter(item => item.session_id === snapshot.session_id && !seen.has(item.event_id))')
s=s.replace("  const tools = state.events.filter(event => ['TOOL_STARTED', 'TOOL_RESULT', 'ERROR', 'USAGE', 'ARTIFACT', 'JUDGE_DECISION'].includes(event.kind))", "  const selectedModel = state.host?.model_configurations?.find(item => item.model_config_ref === (snapshot?.model_config_ref || model))\n  const selectedWorkspace = state.host?.workspaces?.find(item => item.authorized_workspace_ref === (snapshot?.workspace_ref || workspace))")
s=s.replace('<header className="page-heading"><div><h1>{profile?.name || \'会话工作台\'}</h1><p>消息、工具结果和成果保留在当前项目中。</p></div><button disabled={!!busy} onClick={load}>刷新会话</button></header>', '<header className="page-heading workbench-heading"><div><span className="workbench-eyebrow">RESEARCH / WORKSPACE</span><h1>{profile?.name || \'会话工作台\'}</h1><p>把想法交给 Agent，让每一次迭代都有据可查。</p></div><button className="workbench-refresh" disabled={!!busy} onClick={load}>刷新会话</button></header>')
s=s.replace('<WorkbenchLayout sessions={<>', '<WorkbenchLayout hasSession={!!snapshot} sessions={<>')
s=s.replace('conversation={<div className="session-center"><Panel title={snapshot?.title || \'开始协作\'}', 'conversation={<div className="session-center"><Panel className="conversation-canvas" title={snapshot?.title || \'开始协作\'}')
s=s.replace('{snapshot ? <><div className="button-row">', '{snapshot ? <><div className="button-row session-run-controls">',1)
s=s.replace("{!snapshot.messages?.length && <p className=\"empty-state\">发送第一条消息，说明希望完成的事。</p>}", "{!snapshot.messages?.length && <ConversationWelcome setDraft={setDraft} composer={composer}/>}" )
# The input remains visible before a session is chosen; it never sends without the existing writer gate.
start=s.index('          <form className="session-composer"', s.index('export function NativeWorkbench'))
end=s.index('        <p className="small-muted" role="status"', start)
s=s[:start]+'''        </> : <div className="conversation-transcript"><ConversationWelcome setDraft={setDraft} composer={composer}/></div>}
          <form className="session-composer" onSubmit={event => { event.preventDefault(); if (disabled || !snapshot || !writer || !draft.trim()) return; command('发送消息', async () => { unwrap(await window.researchos.v2['session.send']({ text: draft, attachment_artifact_ids: attachment ? [attachment] : [], delivery })); setDraft(''); setAttachment(''); await readSnapshot(); setNotice('消息已接收，等待运行结果。') }) }}>
            <div className="composer-context"><span className="composer-prompt">researchos &gt;</span><span title={selectedModel?.model_id}>{selectedModel?.model_id || '尚未选择模型'}</span>{selectedWorkspace?.display_name && <span title={selectedWorkspace.display_name}>{selectedWorkspace.display_name}</span>}</div>
            <label className="composer-message-label"><span className="visually-hidden">发送给 Agent</span><textarea ref={composer} aria-label="会话消息" value={draft} onChange={event => setDraft(event.target.value)} onKeyDown={event => { if (composerSubmitKey(event)) { event.preventDefault(); if (!disabled && snapshot && writer && draft.trim()) event.currentTarget.form.requestSubmit() } }} placeholder="描述目标、提出问题，或告诉 Agent 下一步做什么…" required/></label>
            <div className="composer-controls"><label><span className="visually-hidden">投递方式</span><select aria-label="投递方式" value={delivery} onChange={event => setDelivery(event.target.value)}><option value="NORMAL">正常消息</option><option value="STEER">引导当前执行</option><option value="FOLLOW_UP">追加后续</option></select></label><small className="composer-shortcut">Enter 发送 · Shift+Enter 换行</small><button className="primary" type="submit" disabled={disabled || !snapshot || !writer || !draft.trim()}>发送</button></div>
            {attachment && <p>已附加受控产物：<span className="break-all">{attachment}</span><button type="button" onClick={() => setAttachment('')}>移除附件</button></p>}
            {(!snapshot || !writer) && <p className="composer-access-note">{snapshot ? '当前为只读，请先选择“在此继续”。' : '在上方选择或创建会话；输入内容会保留。'}</p>}
          </form>
''' +s[end:]
start=s.index('      {snapshot?.project_id === projectId && <SessionContinuation', s.index('export function NativeWorkbench'))
end=s.index('      {(snapshot?.pending_permissions || [])', start)
s=s[:start]+s[end:]
s=s.replace('      </div>} context={<>\n      {snapshot && <WorkspaceFiles', '''      </div>} context={<>
      <ActivityRail events={state.events} snapshot={snapshot} projection={shared?.data?.getProgressProjection} projectState={shared?.data?.getProjectState} releases={shared?.data?.listMilestoneRelease} projectId={projectId} navigate={navigate}/>
      {snapshot?.project_id === projectId && <details className="inspector-disclosure"><summary>目标与双端接续</summary><SessionContinuation key={`${projectId}:${snapshot.session_id}:${snapshot.goal_id || ''}:${snapshot.revision}`} api={api} projectId={projectId} snapshot={snapshot} navigate={navigate}/></details>}
      {snapshot && <details className="inspector-disclosure"><summary>工作区文件与差异</summary><WorkspaceFiles''')
s=s.replace('setFileDirty={setFileDirty}/>}\n      <DesktopQualification', 'setFileDirty={setFileDirty}/></details>}\n      <details className="inspector-disclosure"><summary>模型运行资格</summary><DesktopQualification')
s=s.replace('sessionId={state.snapshot?.session_id || null}/>\n      <DesktopCodingAuthorization', 'sessionId={state.snapshot?.session_id || null}/></details>\n      <details className="inspector-disclosure"><summary>工作区与编码授权</summary><DesktopCodingAuthorization')
s=s.replace('sessionId={state.snapshot?.session_id || null} onConfigured={reconcileCodingCommit}/>\n    </>}', 'sessionId={state.snapshot?.session_id || null} onConfigured={reconcileCodingCommit}/></details>\n    </>}')
anchor='\nfunction BoundArtifact('
welcome='''
function ConversationWelcome({ setDraft, composer }) {
  return <div className="conversation-welcome"><span className="workbench-eyebrow">YOUR NEXT ITERATION</span><h2>让想法，开始迭代。</h2><p>从当前项目出发，一起研究、构建和验证。</p><div className="conversation-starters">{['梳理项目现状与下一步', '检查当前改动并运行必要测试', '继续尚未完成的工作'].map(text => <button type="button" key={text} onClick={() => { setDraft(text); composer.current?.focus() }}>{text}</button>)}</div></div>
}
'''
s=s.replace(anchor, welcome+anchor)
p.write_text(s,encoding='utf-8',newline='\n')

write('apps/web/src/workbench.css', '''/* The same tokens serve light and dark; this layer only changes the workbench hierarchy. */
.workbench-eyebrow{display:block;color:var(--muted);font:10px/1.6 'Cascadia Code',Consolas,monospace;letter-spacing:.12em}
.workbench-route .main-area{padding:25px clamp(18px,2.3vw,36px) 48px}
.workbench-heading{margin-bottom:22px;align-items:center}.workbench-heading h1{font-size:23px;font-weight:620;letter-spacing:-.03em;margin-top:3px}.workbench-heading p{font-size:12px;margin-top:4px}.workbench-refresh{font-size:12px;background:none;border-color:transparent;color:var(--muted)}
.workbench-layout{grid-template-columns:minmax(0,1fr) 288px;gap:28px;align-items:start}.workbench-main-column{min-width:0}.workbench-context-pane{border-left:1px solid var(--border);padding-left:24px}
.workbench-sessions-disclosure{border-bottom:1px solid var(--border);margin-bottom:18px}.workbench-sessions-disclosure>summary{display:flex;align-items:center;justify-content:space-between;gap:12px;cursor:pointer;list-style:none;min-height:38px;padding:0 2px 10px;font-size:12px;font-weight:650}.workbench-sessions-disclosure>summary:after{content:'+';font:16px Consolas,monospace;color:var(--muted)}.workbench-sessions-disclosure[open]>summary:after{content:'−'}.workbench-sessions-disclosure>summary small{margin-left:auto;color:var(--muted);font-size:11px;font-weight:400}.workbench-sessions-disclosure .panel{border:0;padding:10px 0 0;background:none}.workbench-sessions-disclosure .section-heading{display:none}.workbench-session-pane .session-picker{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:6px;max-height:230px}.workbench-session-pane .session-picker li{min-width:0}.workbench-session-pane .session-picker button{border-color:transparent;background:none;margin:0;padding:10px 12px;border-radius:8px;font-size:12px}.workbench-session-pane .session-picker button[aria-current=page]{background:var(--accent-soft);border-color:var(--border)}.workbench-session-pane .session-picker small{font-size:11px}.workbench-session-pane details{padding:8px 0}.workbench-session-pane label{display:block;margin:10px 0}.workbench-session-pane input,.workbench-session-pane select{width:100%}
.workbench-conversation-pane>.session-center>.panel.conversation-canvas{background:none;border:0;padding:0;min-height:calc(100vh - 231px);display:flex;flex-direction:column}.conversation-canvas>.section-heading{margin-bottom:12px;min-height:28px}.conversation-canvas>.section-heading h2{font-size:14px;font-weight:600}.conversation-canvas>.section-heading .tag{font-size:11px;padding:3px 8px}.session-run-controls{align-items:center;gap:6px;padding-bottom:12px;border-bottom:1px solid var(--border)}.session-run-controls button{min-height:30px;padding:3px 10px;font-size:11px;background:none;border-color:transparent}.session-run-controls .tag{font-size:11px;margin-right:auto;background:none;padding-left:0}.session-run-controls .tag:before{content:'';width:5px;height:5px;border-radius:50%;background:var(--success);margin-right:6px}
.workbench-conversation-pane .conversation-transcript{max-height:calc(100vh - 450px);min-height:190px;flex:1;margin:18px 0 22px;padding-right:8px;scrollbar-width:thin}.workbench-layout .conversation-message{padding:18px 0;border:0;max-width:100%;font-size:14px;line-height:1.8}.workbench-layout .conversation-message h3{font-size:11px;letter-spacing:.04em;font-weight:600;margin-bottom:8px}.workbench-layout .conversation-message.role-user{border:1px solid var(--border);border-radius:var(--card-radius,12px);background:var(--surface);padding:14px 18px;margin:5px 0 12px}.workbench-layout .conversation-message.role-assistant h3{color:var(--accent)}
.conversation-welcome{display:flex;flex-direction:column;justify-content:center;align-items:flex-start;min-height:240px;padding:24px 8px}.conversation-welcome h2{font-size:clamp(24px,2.4vw,34px);font-weight:550;letter-spacing:-.045em;margin:10px 0}.conversation-welcome>p{color:var(--muted);font-size:13px;margin:0}.conversation-starters{display:flex;flex-wrap:wrap;gap:8px;margin-top:24px}.conversation-starters button{font-size:11px;text-align:left;min-height:34px;padding:7px 10px;border-color:var(--border);background:none;font-weight:400}
.workbench-conversation-pane .session-composer{margin-top:auto;position:sticky;bottom:16px;border:1px solid var(--border);border-radius:var(--panel-radius,16px);padding:12px 16px;background:var(--surface);box-shadow:0 6px 24px #00000008}.composer-context{display:flex;align-items:center;gap:12px;min-width:0;color:var(--muted);font-size:11px}.composer-context>span{max-width:40%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.composer-context>.composer-prompt{color:var(--accent);font:11px 'Cascadia Code',Consolas,monospace;flex-shrink:0;max-width:none}.composer-message-label{display:block;margin:8px 0}.workbench-conversation-pane .session-composer textarea{display:block;width:100%;min-height:80px;max-height:260px;padding:8px 0;border:0;border-radius:0;background:transparent;box-shadow:none;font:14px/1.65 inherit;resize:vertical}.workbench-conversation-pane .session-composer textarea:focus-visible{outline:0;box-shadow:inset 0 -2px var(--focus)}.composer-controls{gap:8px;align-items:center}.composer-controls select{font-size:11px;min-height:30px;padding:4px 7px;background:var(--subtle);border-color:transparent;max-width:160px}.composer-controls .primary{min-height:32px;font-size:12px;padding:5px 17px;margin-left:auto}.composer-shortcut{font-size:10px;color:var(--muted)}.composer-access-note{font-size:11px;color:var(--muted);margin:9px 0 0}.conversation-canvas>p[role=status]{font-size:11px;margin-top:9px;min-height:18px}.visually-hidden{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
.inspector-heading{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:15px}.inspector-heading h2{font-size:13px;font-weight:650;margin:3px 0 0}.inspector-label{font-size:10px;color:var(--muted);white-space:nowrap}.inspector-caption{font-size:11px;color:var(--muted);line-height:1.7;margin:10px 0}.inspector-empty{padding:18px 0;color:var(--muted);font-size:12px;line-height:1.8}.inspector-empty small{font-size:11px;display:block;margin-top:6px}.iteration-overview{padding:0 0 22px;border-bottom:1px solid var(--border)}.iteration-stages{display:grid;grid-template-columns:1fr 1fr;gap:14px 16px;list-style:none;padding:0;margin:17px 0}.iteration-stages li{min-width:0}.iteration-stages li>div{display:flex;justify-content:space-between;gap:6px;align-items:center}.iteration-stages strong{font-size:11px;font-weight:500}.iteration-stages span{font:10px 'Cascadia Code',Consolas,monospace;color:var(--muted)}.iteration-stages small{display:block;font-size:10px;color:var(--muted);margin-top:4px}.iteration-stages progress{appearance:none;display:block;width:100%;height:3px;border:0;border-radius:3px;overflow:hidden;margin-top:7px;background:var(--subtle);accent-color:var(--accent)}.iteration-stages progress::-webkit-progress-bar{background:var(--subtle)}.iteration-stages progress::-webkit-progress-value{background:var(--accent)}.iteration-stages progress::-moz-progress-bar{background:var(--accent)}.inspector-warning{font-size:12px;color:var(--warning);margin:14px 0}.accepted-delivery{border-top:1px solid var(--border);padding-top:14px;margin-top:16px}.accepted-delivery a{display:block;color:var(--text);margin-top:6px}.accepted-delivery strong{font-size:12px;font-weight:500;overflow-wrap:anywhere}.accepted-delivery small{display:block;color:var(--muted);font-size:11px;margin-top:5px}
.activity-rail{padding:22px 0 14px}.activity-timeline{list-style:none;margin:20px 0 0;padding:0}.activity-item{position:relative;padding:0 0 21px 18px;border-left:1px solid var(--border);margin-left:3px;min-width:0}.activity-item:last-child{border-color:transparent;padding-bottom:8px}.activity-marker{position:absolute;left:-4px;top:6px;width:7px;height:7px;border:1px solid var(--muted);border-radius:50%;background:var(--surface)}.activity-success .activity-marker{background:var(--success);border-color:var(--success)}.activity-error .activity-marker{background:var(--danger);border-color:var(--danger)}.activity-item>details>summary{list-style:none;cursor:pointer}.activity-item-heading{display:flex;justify-content:space-between;align-items:center;gap:12px}.activity-item-heading strong{font:11px/1.6 'Cascadia Code',Consolas,monospace;overflow-wrap:anywhere;color:var(--text)}.activity-item-heading>span{font:10px 'Cascadia Code',Consolas,monospace;color:var(--muted);white-space:nowrap}.activity-summary{display:block;font-size:11px;line-height:1.7;color:var(--muted);margin-top:4px;overflow-wrap:anywhere}.activity-item>details>summary:hover .activity-item-heading strong{color:var(--accent)}.activity-receipt{background:var(--subtle);padding:10px;border-radius:8px;margin-top:10px;overflow-wrap:anywhere}.activity-receipt>small{display:block;font-size:10px;color:var(--muted);margin-bottom:5px}.activity-receipt summary{font-size:11px;cursor:pointer}.activity-receipt pre{max-height:240px;overflow:auto;font-size:10px;white-space:pre-wrap;margin-top:8px}.inspector-disclosure{border-top:1px solid var(--border);padding:12px 0}.inspector-disclosure>summary{font-size:12px;font-weight:500;cursor:pointer;min-height:28px}.inspector-disclosure>.panel{margin:10px 0 0;padding:12px!important;border-radius:8px}.inspector-disclosure .section-heading h2{font-size:12px}.inspector-disclosure .panel p,.inspector-disclosure label{font-size:11px}
@media(min-width:1600px){.workbench-layout{grid-template-columns:minmax(0,1fr) 320px;gap:36px}.workbench-conversation-pane{max-width:960px;margin:0 auto;width:100%}}
@media(max-width:1050px){.workbench-layout{grid-template-columns:minmax(0,1fr)}.workbench-context-pane{grid-column:auto;border-left:0;border-top:1px solid var(--border);padding:22px 0 0;display:grid;grid-template-columns:1fr 1fr;gap:0 28px}.iteration-overview{border-bottom:0}.activity-rail{padding-top:0}.inspector-disclosure{grid-column:1/-1}.workbench-conversation-pane .conversation-transcript{max-height:55vh}}
@media(max-width:767px){.workbench-route .main-area{padding:18px 16px 88px}.workbench-heading{display:flex;gap:10px;margin-bottom:14px}.workbench-heading h1{font-size:21px}.workbench-heading p{font-size:11px}.workbench-heading .workbench-refresh{margin-top:0;min-width:44px;min-height:44px;font-size:11px;padding:4px}.workbench-conversation-pane>.session-center>.panel.conversation-canvas{min-height:calc(100svh - 300px)}.workbench-conversation-pane .conversation-transcript{max-height:none;min-height:140px;padding-right:0}.conversation-welcome{padding:20px 0;min-height:200px}.conversation-welcome h2{font-size:26px}.conversation-starters{gap:7px;margin-top:18px}.conversation-starters button{min-height:44px;font-size:11px}.workbench-conversation-pane .session-composer{padding:12px;bottom:76px}.composer-shortcut{display:none}.composer-controls select,.composer-controls .primary{min-height:44px;min-width:44px}.composer-context{gap:8px}.composer-context>span:last-child:not(.composer-prompt){max-width:45%}.composer-context>span:nth-child(3){display:none}.composer-controls{flex-direction:row;align-items:center}.composer-controls .primary{flex:none}.workbench-context-pane{display:block;padding-top:18px}.activity-rail{padding-top:22px}.iteration-overview{border-bottom:1px solid var(--border)}.session-run-controls button{min-height:44px;min-width:44px}.workbench-sessions-disclosure>summary{min-height:44px}.workbench-session-pane .session-picker{grid-template-columns:minmax(0,1fr);display:grid}.workbench-session-pane .session-picker li{flex:none}.inspector-disclosure>summary{min-height:44px}.activity-item>details>summary{min-height:44px}.workbench-eyebrow{font-size:10px}}
''')

write('tests/ui/desktop/activity-projection.test.mjs', '''import test from 'node:test'
import assert from 'node:assert/strict'
import { activityRows, composerSubmitKey } from '../../../apps/web/src/activity.js'

test('activity is scoped to the current session, ordered and deduplicated', () => {
  const start = { event_id: 'e1', session_id: 'current', sequence: 1, kind: 'TOOL_STARTED', payload: { tool_call_id: 't1', tool_name: 'read_file', input_summary: 'README.md' } }
  const end = { event_id: 'e2', session_id: 'current', sequence: 2, kind: 'TOOL_RESULT', payload: { tool_call_id: 't1', outcome: 'SUCCEEDED', summary: '读取 12 行' } }
  const other = { ...end, event_id: 'secret', session_id: 'previous', sequence: 3 }
  const rows = activityRows([end, other, start, start], 'current')
  assert.deepEqual(rows.map(row => row.event.event_id), ['e2', 'e1'])
  assert.equal(rows[0].title, 'read_file')
  assert.match(rows[0].summary, /工具成功/)
  assert.doesNotMatch(rows[0].summary, /已验收/)
  assert.deepEqual(activityRows([start], null), [])
})

test('run completion and available artifacts never imply acceptance; unknown cost stays unknown', () => {
  const event = (id, kind, payload) => ({ event_id: id, session_id: 's', sequence: Number(id), kind, payload })
  const rows = activityRows([
    event('1', 'RUN_STATE', { status: 'SETTLED' }),
    event('2', 'ARTIFACT', { availability: 'AVAILABLE' }),
    event('3', 'USAGE', { cost_known: false, money: { amount: '0', currency: 'USD' } }),
    event('4', 'GOAL_STATE', { goal_id: 'g', revision: 2, status: 'VERIFYING' }),
  ], 's')
  assert.equal(rows.find(row => row.event.kind === 'RUN_STATE').title, '执行已结束')
  assert.match(rows.find(row => row.event.kind === 'ARTIFACT').summary, /另行核对/)
  assert.equal(rows.find(row => row.event.kind === 'USAGE').summary, '费用待结算')
  assert.equal(rows.find(row => row.event.kind === 'GOAL_STATE').title, '目标验收中')
})

test('composer sends on Enter while IME and Shift+Enter retain multiline composition', () => {
  assert.equal(composerSubmitKey({ key: 'Enter' }), true)
  assert.equal(composerSubmitKey({ key: 'Enter', ctrlKey: true }), true)
  assert.equal(composerSubmitKey({ key: 'Enter', shiftKey: true }), false)
  assert.equal(composerSubmitKey({ key: 'Enter', isComposing: true }), false)
  assert.equal(composerSubmitKey({ key: 'Enter', nativeEvent: { isComposing: true } }), false)
  assert.equal(composerSubmitKey({ key: 'Enter', nativeEvent: { keyCode: 229 } }), false)
})
''')
