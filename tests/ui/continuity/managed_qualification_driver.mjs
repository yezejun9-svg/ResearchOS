import fs from 'node:fs'
import path from 'node:path'
import assert from 'node:assert/strict'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { createRequire } from 'node:module'

const here = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(here, '../../..')
const sharedRoot = process.env.RESEARCHOS_SHARED_ROOT || root
const uiImport = process.env.RESEARCHOS_UI_SOURCE
  ? '/@fs/' + path.resolve(process.env.RESEARCHOS_UI_SOURCE).replaceAll('\\', '/')
  : '../../../apps/web/src/workbench.jsx'
const require = createRequire(import.meta.url)
const { chromium } = require('C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/Lib/site-packages/playwright/driver/package')
const { createServer } = await import(pathToFileURL(path.join(sharedRoot, 'apps/web/node_modules/vite/dist/node/index.js')))
const stem = `.managed_qualification_${process.pid}`
const html = path.join(here, stem + '.html')
const entry = path.join(here, stem + '.jsx')
const recorded = []
let current = { ok: true, state: 'READY', available: true }
let confirmed = 0
const prepared = { ok: true, state: 'AWAITING_CONFIRMATION', available: true,
  model: { provider_id: 'ollama', model_id: 'qwen3:4b-instruct' }, request_id: 'req-fixture',
  expires_at: new Date(Date.now() + 45000).toISOString(), consumed: false }
const authorized = { ...prepared, state: 'QUALIFIED_PURPOSE_AUTHORIZED', consumed: true,
  authorized: true, checked_at: new Date().toISOString() }
let server, browser, page
try {
  fs.writeFileSync(html, `<div id="root"></div><script type="module" src="/${path.basename(entry)}"></script>`, 'utf8')
  fs.writeFileSync(entry, `import React from 'react'; import {createRoot} from 'react-dom/client';
    import {DesktopQualification} from '${uiImport}';
    let root; window.remount = (session='session-1') => {
      root?.unmount(); root=createRoot(document.getElementById('root'));
      root.render(<DesktopQualification projectId="project-1" sessionId={session}/>);
    }; window.remount();`, 'utf8')
  server = await createServer({ configFile: false, root: here, cacheDir: path.join(sharedRoot, '.local', 'vite-managed-qualification-cache'),
    server: { host: '127.0.0.1', port: 0, hmr: false, watch: { ignored: ['**'] }, fs: { allow: [root, sharedRoot] } },
    resolve: { alias: [
      { find: /^react\/jsx-dev-runtime$/, replacement: path.join(sharedRoot, 'apps/web/node_modules/react/jsx-dev-runtime.js') },
      { find: /^react\/jsx-runtime$/, replacement: path.join(sharedRoot, 'apps/web/node_modules/react/jsx-runtime.js') },
      { find: /^react$/, replacement: path.join(sharedRoot, 'apps/web/node_modules/react/index.js') },
      { find: /^react-dom\/client$/, replacement: path.join(sharedRoot, 'apps/web/node_modules/react-dom/client.js') },
    ] } })
  await server.listen()
  browser = await chromium.launch({ headless: true })
  page = await browser.newPage()
  page.setDefaultTimeout(12000)
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  await page.exposeFunction('managedBridge', async (method, args) => {
    recorded.push({ method, args })
    if (method === 'qualificationCurrent') return current
    if (method === 'qualificationPrepare') { current = prepared; return current }
    if (method === 'qualificationConfirm') { confirmed++; current = authorized; return current }
    if (method === 'qualificationStatus') return current
    throw Error('unexpected bridge method')
  })
  await page.addInitScript(() => {
    const desktop = {}
    for (const name of ['qualificationCurrent', 'qualificationPrepare', 'qualificationConfirm', 'qualificationStatus'])
      desktop[name] = (...args) => window.managedBridge(name, args)
    window.researchos = { desktop }
  })
  await page.goto(server.resolvedUrls.local[0] + path.basename(html))
  await page.getByRole('button', { name: '准备当前会话' }).click()
  await page.getByText('准备完成；模型调用尚未开始', { exact: false }).waitFor()
  assert.equal(confirmed, 0)
  assert.equal(await page.getByRole('button', { name: '明确确认一次调用' }).isEnabled(), true)
  await page.evaluate(() => window.remount())
  await page.getByText('原请求：req-fixture', { exact: false }).waitFor()
  page.on('dialog', dialog => dialog.accept())
  await page.getByRole('button', { name: '明确确认一次调用' }).click()
  await page.getByText('最近一次复核显示用途授权', { exact: false }).waitFor()
  assert.equal(confirmed, 1)
  assert.equal(await page.getByRole('button', { name: '明确确认一次调用' }).isDisabled(), true)
  await page.getByRole('button', { name: '复核原请求' }).click()
  assert.equal(confirmed, 1)
  current = { ...prepared, state: 'CONTEXT_CHANGED_PENDING', available: true, authorized: false }
  await page.evaluate(() => window.remount('session-2'))
  await page.getByText('项目或会话已变更', { exact: false }).waitFor()
  assert.equal(await page.getByRole('button', { name: '明确确认一次调用' }).isDisabled(), true)
  assert.deepEqual(errors, [])
  assert(recorded.every(call => call.args.length === 0))
  console.log(JSON.stringify({ status: 'SYNTHETIC_DOM_PASS', cases: ['prepare-zero-model', 'remount-original-request',
    'one-explicit-confirm', 'status-no-reconfirm', 'changed-context-lock'], bridge_calls: recorded,
    actual_model_calls: 0, page_errors: errors }))
} finally {
  await page?.close(); await browser?.close(); await server?.close()
  for (const file of [html, entry]) if (fs.existsSync(file)) fs.unlinkSync(file)
}
