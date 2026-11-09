import React from 'react'

export function Header({ title, description, action }) {
  return <header className="page-heading"><div><h1>{title}</h1>{description && <p>{description}</p>}</div>{action}</header>
}

export function Section({ title, aside, children, className = '' }) {
  return <section className={`panel ${className}`}><div className="section-heading"><h2>{title}</h2>{aside}</div>{children}</section>
}

export function Empty({ children }) { return <p className="empty-state">{children || '当前没有记录。'}</p> }

export function Tag({ value, type }) {
  const tone = type || (/失败|受阻|拒绝|限流|过期|PARTIAL|RATE_LIMITED/.test(String(value)) ? 'warning' : /验收|COMPLETE|CURRENT|IMPROVED/.test(String(value)) ? 'good' : '')
  return <span className={`tag ${tone}`}>{value ?? '未知'}</span>
}

export function JsonDetails({ value, label = '查看原始字段' }) {
  return <details className="raw-details"><summary>{label}</summary><pre>{JSON.stringify(value, null, 2)}</pre></details>
}
