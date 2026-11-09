import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './style.css'

function App() {
  const [health, setHealth] = useState('检查中')
  useEffect(() => {
    fetch('/healthz', { cache: 'no-store' })
      .then(async response => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        const data = await response.json()
        setHealth(data.status === 'ready' ? '数据库已就绪' : '服务未就绪')
      })
      .catch(() => setHealth('服务未就绪'))
  }, [])
  return <main>
    <span className="eyebrow">ResearchOS · 开发骨架</span>
    <h1>研究工作台</h1>
    <p>当前仅验证控制服务、静态页面和 SQLite 启动。项目、任务与验收功能尚未实现。</p>
    <div className="status" role="status" aria-live="polite"><span className="dot" />{health}</div>
  </main>
}

createRoot(document.getElementById('root')).render(<App />)
