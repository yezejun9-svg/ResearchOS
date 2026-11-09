from pathlib import Path
root=Path(r'D:\作品集\ResearchOS\research-os\.local\worktrees\workbench-experience-20261104')
p=root/'apps/web/src/activity.js'
s=p.read_text(encoding='utf-8')
s="import { integer, compare } from '../../desktop/main/lib/wire-values.mjs'\n\n"+s
s=s.replace('!Number.isSafeInteger(event.sequence)', '!integer(event.sequence)')
s=s.replace('.sort((a, b) => a.sequence - b.sequence)', '.sort((a, b) => compare(a.sequence, b.sequence))')
s=s.replace('}).reverse().slice(0, 12)', '}).reverse()')
s=s.replace('`${payload.money.amount} ${payload.money.currency}`', '`${payload.money.amount?.exact_decimal ?? payload.money.amount} ${payload.money.currency}`')
p.write_text(s,encoding='utf-8',newline='\n')
p=root/'apps/web/src/components/activity-rail.jsx'
s=p.read_text(encoding='utf-8')
s=s.replace("import React from 'react'", "import React, { useEffect, useState } from 'react'")
s=s.replace('  const activity = activityRows(events, snapshot?.session_id)', '  const [expanded, setExpanded] = useState(false)\n  useEffect(() => setExpanded(false), [snapshot?.session_id])\n  const activity = activityRows(events, snapshot?.session_id)\n  const visibleActivity = expanded ? activity : activity.slice(0, 12)')
s=s.replace('实时回执', '状态投影')
s=s.replace('{activity.map(', '{visibleActivity.map(')
s=s.replace('#{event.sequence}', '#{String(event.sequence)}')
s=s.replace('      <p className="inspector-caption">执行结束与成果验收分别记录。</p>', '      {activity.length > 12 && <button type="button" className="activity-expand" aria-expanded={expanded} onClick={() => setExpanded(value => !value)}>{expanded ? \'只看最近 12 条\' : `展开已读取轨迹（${activity.length}）`}</button>}\n      <p className="inspector-caption">按已读取事件投影。执行结束与成果验收分别记录。</p>')
p.write_text(s,encoding='utf-8',newline='\n')
p=root/'apps/web/src/workbench.css'
s=p.read_text(encoding='utf-8').replace('font-size:11px','font-size:12px').replace('font-size:10px','font-size:12px').replace('font:10px','font:12px').replace('font:11px','font:13px')
s=s.replace('.activity-summary{display:block;font-size:12px', '.activity-summary{display:block;font-size:13px')
s=s.replace('.iteration-stages strong{font-size:12px', '.iteration-stages strong{font-size:13px')
s=s.replace('.composer-context{display:flex;align-items:center;gap:12px;min-width:0;color:var(--muted);font-size:12px', '.composer-context{display:flex;align-items:center;gap:12px;min-width:0;color:var(--muted);font-size:13px')
s += '\n.activity-expand{font-size:12px;min-height:36px;padding:6px 10px;background:none;margin-top:8px}.workbench-eyebrow{font-size:10px}\n'
p.write_text(s,encoding='utf-8',newline='\n')
p=root/'tests/ui/desktop/activity-projection.test.mjs'
s=p.read_text(encoding='utf-8')
s += '''
test('exact uint64 event ordering preserves large values and all already read history', () => {
  const first = 9007199254740993n
  const events = Array.from({ length: 16 }, (_, i) => ({ event_id: `large-${i}`, session_id: 's', sequence: first + BigInt(i), kind: 'RUN_STATE', payload: { status: i === 0 ? 'FAILED' : 'RUNNING' } }))
  const rows = activityRows(events.reverse(), 's')
  assert.equal(rows.length, 16)
  assert.equal(rows[0].event.sequence, first + 15n)
  assert.equal(rows.at(-1).event.sequence, first)
  assert.equal(rows.at(-1).title, '执行失败')
})

test('a known exact decimal amount remains readable without numeric rounding', () => {
  const [row] = activityRows([{ event_id: 'money', session_id: 's', sequence: 1n, kind: 'USAGE', payload: { cost_known: true, money: { amount: { exact_decimal: '0.001200' }, currency: 'USD' } } }], 's')
  assert.equal(row.summary, '0.001200 USD')
})
'''
p.write_text(s,encoding='utf-8',newline='\n')
