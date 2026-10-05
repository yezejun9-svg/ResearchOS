// Drive the real Electron renderer through Chromium DevTools. No page fixtures or
// renderer stubs are injected. All output is confined to the caller's receipt dir.
'use strict';

const fs = require('node:fs');
const path = require('node:path');

const [, , port, metadataFile, receiptDir] = process.argv;
if (!port || !metadataFile || !receiptDir) throw Error('usage: node gui_restore.cjs PORT METADATA_JSON RECEIPT_DIR');
const meta = JSON.parse(fs.readFileSync(metadataFile, 'utf8'));
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
const save = (name, value) => fs.writeFileSync(path.join(receiptDir, name), JSON.stringify(value, null, 2) + '\n');

async function target() {
  for (let i = 0; i < 100; i++) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/json/list`);
      const pages = await response.json();
      const page = pages.find(item => item.type === 'page' && item.webSocketDebuggerUrl);
      if (page) return page;
    } catch { /* Electron has not opened its debugger yet. */ }
    await pause(150);
  }
  throw Error('ELECTRON_CDP_PAGE_TIMEOUT');
}

async function main() {
  const page = await target();
  const socket = new WebSocket(page.webSocketDebuggerUrl);
  const pending = new Map(), events = [], rendererErrors = [];
  let serial = 0;
  await new Promise((resolve, reject) => {
    socket.addEventListener('open', resolve, { once: true });
    socket.addEventListener('error', reject, { once: true });
  });
  socket.addEventListener('message', event => {
    let value;
    try { value = JSON.parse(event.data); } catch { return; }
    if (value.id && pending.has(value.id)) {
      const slot = pending.get(value.id); pending.delete(value.id);
      if (value.error) slot.reject(Error(JSON.stringify(value.error))); else slot.resolve(value.result);
      return;
    }
    if (!value.method) return;
    if (value.method === 'Runtime.exceptionThrown') {
      rendererErrors.push({ method: value.method, text: value.params?.exceptionDetails?.text || 'exception' });
    } else if (value.method === 'Runtime.consoleAPICalled' && value.params?.type === 'error') {
      rendererErrors.push({ method: value.method, text: (value.params.args || []).map(item => item.value || item.description || '').join(' ').slice(0, 1000) });
    }
    events.push({ method: value.method, timestamp: Date.now() });
  });
  async function send(method, params = {}) {
    const id = ++serial;
    const promise = new Promise((resolve, reject) => {
      const timer = setTimeout(() => { pending.delete(id); reject(Error(`CDP_TIMEOUT:${method}`)); }, 15000);
      pending.set(id, {
        resolve: value => { clearTimeout(timer); resolve(value); },
        reject: error => { clearTimeout(timer); reject(error); },
      });
    });
    socket.send(JSON.stringify({ id, method, params }));
    return promise;
  }
  async function evaluate(expression) {
    const reply = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
    if (reply.exceptionDetails) throw Error(`RENDERER_EVAL:${reply.exceptionDetails.text || 'exception'}`);
    return reply.result?.value;
  }
  async function waitFor(expression, name) {
    for (let i = 0; i < 60; i++) {
      try { if (await evaluate(expression)) return; }
      catch (error) { if (!/RENDERER_EVAL|Execution context was destroyed|Cannot find context/.test(String(error))) throw error; }
      await pause(250);
    }
    throw Error(`UI_TIMEOUT:${name}`);
  }
  async function capture(name) {
    const state = await evaluate(`({ url:location.href, title:document.title,
      headings:[...document.querySelectorAll('h1,h2,h3')].map(x=>x.textContent.trim()),
      body:document.body.innerText.slice(0,12000),
      sessionButtons:[...document.querySelectorAll('.session-picker button')].map(x=>x.textContent.trim()),
      root:!!document.getElementById('root'), bridge:!!window.researchos?.desktop })`);
    save(`${name}.json`, state);
    const screenshot = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
    fs.writeFileSync(path.join(receiptDir, `${name}.png`), Buffer.from(screenshot.data, 'base64'));
    return state;
  }
  const pid = encodeURIComponent(meta.project_id), tid = encodeURIComponent(meta.task_id);
  try {
    await send('Runtime.enable'); await send('Page.enable'); await send('Log.enable');
    await send('Page.navigate', { url: `ros-app://desktop/p/${pid}` });
    await waitFor(`document.querySelector('.session-picker button') && document.body.innerText.includes(${JSON.stringify(meta.session_title)})`, 'restored session list');
    const before = await capture('01-session-list');
    const clicked = await evaluate(`(() => { const button=[...document.querySelectorAll('.session-picker button')].find(x=>x.textContent.includes(${JSON.stringify(meta.session_title)})); if(!button) return false; button.click(); return true; })()`);
    if (!clicked) throw Error('SESSION_BUTTON_ABSENT');
    await waitFor(`document.querySelector('.conversation-transcript')?.textContent.includes('backup')`, 'restored transcript');
    const session = await capture('02-session-open');
    const native = await evaluate(`(async () => {
      const context = await window.researchos.desktop.context();
      const reply = await window.researchos.v2['session.get']({});
      const value = reply?.result || {};
      return { context, ok: reply?.ok, status: reply?.protocol_status,
        project_id: value.project_id, session_id: value.session_id, goal_id: value.goal_id,
        task_id: value.task_id, event_sequence: value.event_sequence, title: value.title };
    })()`);
    save('native-session.json', native);
    await send('Page.navigate', { url: `ros-app://desktop/p/${pid}/tasks/${tid}` });
    await waitFor(`document.querySelector('h1')?.textContent.trim() === ${JSON.stringify(meta.task_title)}`, 'restored task detail');
    const task = await capture('03-task');
    await send('Page.navigate', { url: `ros-app://desktop/p/${pid}` });
    await waitFor(`document.querySelector('.goal-section')?.textContent.includes(${JSON.stringify(meta.goal_title)})`, 'restored goal dashboard');
    const goal = await capture('04-goal');
    const checks = {
      session_list_title: before.sessionButtons.some(item => item.includes(meta.session_title)),
      session_open_title: session.body.includes(meta.session_title),
      restored_transcript: session.body.includes('backup'),
      task_detail_title: task.headings.includes(meta.task_title),
      task_url_id: task.url.endsWith(`/tasks/${tid}`),
      goal_dashboard_title: goal.body.includes(meta.goal_title),
      native_session_identity: native.ok === true && native.status === 'COMPLETED' &&
        native.context?.session_id === meta.session_id && native.context?.project_id === meta.project_id &&
        native.session_id === meta.session_id && native.project_id === meta.project_id &&
        native.goal_id === meta.goal_id && native.task_id === meta.task_id,
      restored_event_cursor: native.event_sequence === meta.event_cursor,
      renderer_errors_zero: rendererErrors.length === 0,
      native_bridge_present: [before, session, task, goal].every(item => item.root && item.bridge),
    };
    save('renderer-events.json', { events, renderer_errors: rendererErrors });
    save('gui-checks.json', checks);
    if (Object.values(checks).some(value => !value)) throw Error('GUI_ASSERTION_FAILED:' + JSON.stringify(checks));
    process.stdout.write(JSON.stringify({ status: 'PASS', checks, screenshots: 4 }) + '\n');
  } finally { socket.close(); }
}

main().catch(error => { process.stderr.write(String(error.stack || error) + '\n'); process.exitCode = 1; });
