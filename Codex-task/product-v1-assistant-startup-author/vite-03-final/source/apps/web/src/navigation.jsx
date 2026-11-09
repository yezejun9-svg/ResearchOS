import React, { useEffect, useState } from 'react'

const nativeDesktop = !!window.researchos?.desktop?.context

export const stages = [['discovery', '发现'], ['verification', '核验'], ['experiment', '实验'], ['review', '评审'], ['delivery', '交付'], ['follow_up', '跟踪']]
export const taskLabels = { DRAFT: '草稿', READY: '待执行', RUNNING: '执行中', EXECUTION_REPORTED: '结果已提交', VERIFYING: '验收中', ACCEPTED: '已验收', FAILED: '失败', BLOCKED: '受阻', CANCELLED: '已取消', NEEDS_REVALIDATION: '需重验', DEFERRED_NO_PROGRESS: '无进展延期' }
export const runLabels = { QUEUED: '排队', STARTING: '启动中', RUNNING: '运行中', CANCEL_REQUESTED: '取消请求中', SETTLED: '执行已结束', FAILED: '执行失败', CANCELLED: '已取消', LOST: '连接丢失', RECONCILING: '恢复对账中' }

export const navigation = [['home', '工作台', 'workbench'], ...(!nativeDesktop ? [['chat', '对话接续', 'continuity']] : []), ['cycle', '研究周期', 'cycle'], ['release', '成果审查', 'release'], ['evidence', '来源证据', 'evidence'], ['experiment', '实验评测', 'experiment'], ['knowledge', '知识技能', 'knowledge'], ['team', '团队运行器', 'team'], ['resources', '费用资源', 'resources'], ['settings', '设置设备', 'settings']]

export function routeOf(path) {
  const p = path.split('/').filter(Boolean).map(decodeURIComponent)
  if (!p.length) return { kind: 'projects', key: path }
  if (p[0] !== 'p' || !p[1]) return { kind: 'not-found', key: path }
  const projectId = p[1]
  if (p.length === 2) return { kind: 'workbench', projectId, key: path }
  const kind = { cycles: 'cycle', tasks: 'task', releases: 'release', evidence: 'evidence', experiments: 'experiment', knowledge: 'knowledge', team: 'team', resources: 'resources', settings: 'settings', continuity: nativeDesktop ? 'workbench' : 'continuity' }[p[2]]
  if (!kind || (['evidence', 'knowledge', 'team', 'resources', 'settings'].includes(kind) && p.length > 3)) return { kind: 'not-found', projectId, key: path }
  if (['cycle', 'task', 'release', 'experiment'].includes(kind) && !p[3]) return { kind: 'selection', section: kind, projectId, key: path }
  return { kind, projectId, id: p[3], key: path }
}

export function useRoute() {
  const currentRoute = () => ({ ...routeOf(location.pathname), search: location.search })
  const [route, setRoute] = useState(currentRoute)
  useEffect(() => { const pop = () => setRoute(currentRoute()); addEventListener('popstate', pop); return () => removeEventListener('popstate', pop) }, [])
  const navigate = path => { const target = new URL(path, location.origin); if (target.pathname + target.search !== location.pathname + location.search) history.pushState(null, '', target); setRoute({ ...routeOf(target.pathname), search: target.search }); scrollTo(0, 0) }
  return [route, navigate]
}

export function Link({ to, navigate, children, ...props }) {
  return <a {...props} href={to} onClick={event => { props.onClick?.(event); if (!event.defaultPrevented && event.button === 0 && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey) { event.preventDefault(); navigate(to) } }}>{children}</a>
}
