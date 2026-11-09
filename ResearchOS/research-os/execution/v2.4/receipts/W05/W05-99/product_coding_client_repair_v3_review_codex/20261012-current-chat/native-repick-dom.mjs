import {fixture as makeFixture,scope as originalScope,context as originalContext,registerDesktopCoding} from './fixture.mjs';
import fs from 'node:fs'
import path from 'node:path'
import assert from 'node:assert/strict'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { createRequire } from 'node:module'

const here = path.dirname(fileURLToPath(import.meta.url))
const root = process.env.RESEARCHOS_SHARED_ROOT
const sharedRoot = process.env.RESEARCHOS_SHARED_ROOT || root
const uiImport = process.env.RESEARCHOS_UI_SOURCE
  ? '/@fs/' + path.resolve(process.env.RESEARCHOS_UI_SOURCE).replaceAll('\\', '/')
  : '../../../apps/web/src/workbench.jsx'
const require = createRequire(import.meta.url)
const { chromium } = require('C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/Lib/site-packages/playwright/driver/package')
const { createServer } = await import(pathToFileURL(path.join(sharedRoot, 'apps/web/node_modules/vite/dist/node/index.js')))
const stem = `.coding_authorization_${process.pid}`
const html = path.join(here, stem + '.html'), entry = path.join(here, stem + '.jsx')
const record = []
const nativeFixture=makeFixture('dom-explicit-error-go-reselection')
let resourceGeneration=0, selectedToolchain=null, privilegedPrompts=0
const ipcHandlers=new Map()
const trustedReview=()=>({resource_generation:resourceGeneration,workspace:{authorized_workspace_ref:'workspace-1',display_name:'Fixture',display_path:'C:/workspace'}})
let lastInput=null
const scopedInput=body=>({context:originalContext,review:trustedReview(),scope:{...originalScope(),coding:{...originalScope().coding,...body,checks:body.checks.map(check=>({...check,toolchain_root:selectedToolchain}))}}})
registerDesktopCoding({handle:(name,fn)=>ipcHandlers.set(name,fn)},{
 desktopManagement:nativeFixture.manager,codingSenderAllowed:()=>true,
 prepareCodingScope:async body=>{lastInput=body;return scopedInput(body)},
 recheckCodingScope:async()=>scopedInput(lastInput),
 privilegedCodingConsent:async()=>{privilegedPrompts++;return true},
 pickCodingDirectory:async()=>{nativeFixture.manager.commandIdle();selectedToolchain='C:/trusted-go-'+(++resourceGeneration);nativeFixture.setGeneration(resourceGeneration);return {selected:true,name:'go-toolchain'}}
})
const expiry = new Date(Date.now() + 50000).toISOString()
const frozen = { ok: true, available: true, state: 'AWAITING_CODING_CONFIRMATION', expires_at: expiry,
  consumed: false, model_calls: 0, scope: { read_paths: ['go.mod', 'pkg/value.go', 'pkg/value_test.go'],
    write_paths: ['pkg/value.go'], max_read_bytes: 8192, max_write_bytes: 8192,
    max_tool_calls: 8, max_output_tokens: 2048,
    checks: [{ id: 'go-check', package: './pkg', test_pattern: '^TestValue$',
      source_paths: ['go.mod', 'pkg/value.go', 'pkg/value_test.go'], toolchain_selected: true,
      vendor_selected: false, timeout_seconds: 90, process_limit: 32, memory_mib: 1024,
      max_text_bytes: 4096 }] },
  frozen_checks: [{ id: 'go-check' }] }
let state = { ok: true, available: true, state: 'READY' }, confirms = 0, prepares = 0, refreshes = 0, refreshAttempts = 0
const statusRecovery = process.env.ROS_STATUS_RECOVERY === '1'
const refreshFailOnce = process.env.ROS_REFRESH_FAIL_ONCE === '1'
const prepareErrorRepick = process.env.ROS_PREPARE_ERROR_REPICK === '1'
let server, browser, page
try {
  fs.writeFileSync(html, `<div id="root"></div><script type="module" src="/${path.basename(entry)}"></script>`, 'utf8')
  fs.writeFileSync(entry, `import React from 'react'; import {createRoot} from 'react-dom/client';
    import {DesktopCodingAuthorization} from '${uiImport}';
    let root; window.remount = (session='session-1') => { root?.unmount(); root=createRoot(document.getElementById('root'));
      root.render(<DesktopCodingAuthorization projectId="project-1" sessionId={session} onConfigured={() => window.codingRefresh()}/>); };
    window.remount();`, 'utf8')
  server = await createServer({ configFile: false, root: here,
    cacheDir: path.join(here, 'vite-review-cache'),
    server: { host: '127.0.0.1', port: 0, hmr: false, watch: { ignored: ['**'] },
      fs: { allow: [root, sharedRoot] } },
    resolve: { alias: [
      { find: /^react\/jsx-dev-runtime$/, replacement: path.join(sharedRoot, 'apps/web/node_modules/react/jsx-dev-runtime.js') },
      { find: /^react\/jsx-runtime$/, replacement: path.join(sharedRoot, 'apps/web/node_modules/react/jsx-runtime.js') },
      { find: /^react$/, replacement: path.join(sharedRoot, 'apps/web/node_modules/react/index.js') },
      { find: /^react-dom\/client$/, replacement: path.join(sharedRoot, 'apps/web/node_modules/react-dom/client.js') },
    ] } })
  await server.listen()
  browser = await chromium.launch({ headless: true })
  page = await browser.newPage(); page.setDefaultTimeout(12000)
  const errors = []; page.on('pageerror', error => errors.push(error.message))
  await page.exposeFunction('codingRefresh', () => {
    refreshAttempts++
    if (refreshFailOnce && refreshAttempts === 1) throw new Error('V2_READ_FAILED')
    refreshes++
  })
  await page.exposeFunction('codingBridge', async (method,args)=>{
    record.push({method,args})
    if(method==='codingCurrent')return {ok:true,...nativeFixture.manager.codingSummary()}
    const channel={codingPickToolchain:'pickToolchain',codingPickVendor:'pickVendor',codingPrepare:'prepare',codingConfirm:'confirm',codingStatus:'status'}[method]
    if(!channel)throw new Error('unexpected '+method)
    if(method==='codingPrepare'){
      prepares++
      if(prepares===1){
        nativeFixture.setHold(true)
        const result=ipcHandlers.get('ros:desktop:coding:prepare')({},args[0])
        await new Promise(resolve=>setImmediate(resolve))
        assert.equal(nativeFixture.held.length,1)
        Object.assign(nativeFixture.held[0],{kind:'ERROR',result:null,error:{code:'MANAGEMENT_REJECTED',message:'first resource unavailable'}})
        nativeFixture.deliver();nativeFixture.setHold(false)
        return await result
      }
    }
    if(method==='codingConfirm')confirms++
    return await ipcHandlers.get('ros:desktop:coding:'+channel)({},args[0])
  })
  await page.addInitScript(() => {
    const desktop = {}
    for (const name of ['codingCurrent', 'codingPickToolchain', 'codingPickVendor', 'codingPrepare',
      'codingConfirm', 'codingStatus']) desktop[name] = (...args) => window.codingBridge(name, args)
    window.researchos = { desktop }
  })
  await page.goto(server.resolvedUrls.local[0] + path.basename(html))
  await page.getByRole('button', { name: '选择 Go 工具链目录' }).click()
  await page.getByText('go-toolchain').waitFor()
  await page.getByRole('button', { name: '准备并冻结' }).click()
  if (prepareErrorRepick) {
    await page.getByRole('alert').getByText('CODING_PREPARE_REJECTED').waitFor()
    await page.getByRole('button', { name: '选择 Go 工具链目录' }).click()
    await page.getByRole('button', { name: '准备并冻结' }).click()
  }
  await page.getByText('冻结完成；配置尚未写入', { exact: false }).waitFor()
  assert.equal(prepares, prepareErrorRepick ? 2 : 1); assert.equal(confirms, 0)
  const preparedInput = record.find(item => item.method === 'codingPrepare').args[0]
  assert.equal(preparedInput.checks[0].toolchain_root, undefined)
  assert.equal(preparedInput.read_paths[0], 'go.mod')
  await page.evaluate(() => window.remount())
  await page.getByText('本次冻结摘要').waitFor()
  await page.getByText('读取 8192 字节/文件', { exact: false }).waitFor()
  await page.getByText('最多 32 个进程、1024 MiB 内存', { exact: false }).waitFor()
  assert.equal(await page.getByRole('button', { name: '准备并冻结' }).isDisabled(), true)
  await page.getByRole('button', { name: '明确确认配置' }).click()
  if (statusRecovery) {
    await page.getByRole('alert').getByText('MANAGEMENT_REPLY_UNCERTAIN', { exact: false }).waitFor()
    assert.equal(confirms, 1); assert.equal(refreshes, 0)
    await page.getByRole('button', { name: '复核原请求' }).click()
  }
  if (refreshFailOnce) {
    await page.getByRole('alert').getByText('V2_READ_FAILED', { exact: false }).waitFor()
    assert.equal(refreshes, 0)
    await page.getByRole('button', { name: '复核原请求' }).click()
  }
  await page.getByText('编码配置已保存', { exact: false }).waitFor()
  assert.equal(confirms, 1); assert.equal(refreshes, 1)
  assert.equal(await page.getByRole('button', { name: '明确确认配置' }).isDisabled(), true)
  await page.getByRole('button', { name: '复核原请求' }).click()
  assert.equal(confirms, 1)
  assert.equal(refreshes, 1)
  await page.evaluate(() => window.remount())
  await page.getByText('编码配置已保存', { exact: false }).waitFor({ state: 'hidden' }).catch(() => {})
  await page.getByRole('button', { name: '复核原请求' }).click()
  assert.equal(refreshes, 1)
  assert.equal(await page.getByText('C:/trusted-go').count(), 0)
  assert.deepEqual(errors, [])
  assert.equal(resourceGeneration,2)
  assert.equal(privilegedPrompts,1)
  assert.equal(nativeFixture.sent[0].coding.checks[0].toolchain_root,'C:/trusted-go-1')
  assert.equal(nativeFixture.sent[1].coding.checks[0].toolchain_root,'C:/trusted-go-2')
  assert.equal(nativeFixture.manager.retiredCodingIntents[0].retireReason,'AUTHORITATIVE_PREPARE_REJECTION')
  nativeFixture.save()
  fs.writeFileSync(path.join(here,'native-repick-results.json'),JSON.stringify({pass:true,resourceGeneration,privilegedPrompts,prepares,confirms,refreshes,retired:nativeFixture.manager.retiredCodingIntents,actual_model_calls:0,actual_tool_calls:0,page_errors:errors},null,2))

  fs.writeFileSync(path.join(here,'native-repick.dom.html'),await page.content());
  await page.screenshot({path:path.join(here,'native-repick.png'),fullPage:true});
  fs.writeFileSync(path.join(here,'native-dom-bridge-calls.json'),JSON.stringify(record,null,2));
  console.log(JSON.stringify({ status: prepareErrorRepick ? 'SYNTHETIC_CODING_PREPARE_ERROR_REPICK_PASS' :
    refreshFailOnce ? 'SYNTHETIC_CODING_REFRESH_RETRY_PASS' :
    statusRecovery ? 'SYNTHETIC_CODING_STATUS_RECOVERY_PASS' : 'SYNTHETIC_CODING_DOM_PASS',
    prepares, confirms, refreshes, refresh_attempts: refreshAttempts, actual_model_calls: 0, page_errors: errors }))
} finally {
  await page?.close(); await browser?.close(); await server?.close()
  // Generated inputs retained as independent evidence.
}
