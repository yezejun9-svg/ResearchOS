// Observe the actual Electron renderer through its local debugger.
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const playwrightPath = process.env.RESEARCHOS_PLAYWRIGHT_MODULE ||
  'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/Lib/site-packages/playwright/driver/package';
const playwright = require(playwrightPath);
const [, , port, metadataFile, receiptDir] = process.argv;
if (!port || !metadataFile || !receiptDir) throw Error('usage: node gui_restore.cjs PORT METADATA_JSON RECEIPT_DIR');
const meta = JSON.parse(fs.readFileSync(metadataFile, 'utf8'));
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
const save = (name, value) => fs.writeFileSync(path.join(receiptDir, name), JSON.stringify(value, null, 2) + '\n');
const events = [], rendererErrors = [], requestFailures = [];
let browser, page, stage = 'connect';
async function bounded(promise, label, milliseconds = 30000) {
  let timer;
  try {
    return await Promise.race([promise, new Promise((_, reject) => {
      timer = setTimeout(() => reject(Error('UI_TIMEOUT:' + label)), milliseconds);
    })]);
  } finally { clearTimeout(timer); }
}
async function connect() {
  let lastError;
  for (let i = 0; i < 30; i++) {
    try { return await playwright.chromium.connectOverCDP('http://127.0.0.1:' + port, { timeout: 2000 }); }
    catch (error) { lastError = String(error); await pause(200); }
  }
  throw Error('ELECTRON_CDP_TIMEOUT:' + lastError);
}
async function evaluate(expression) { return bounded(page.evaluate(expression), stage + ':evaluate'); }
async function waitFor(predicate, value, name) {
  await page.waitForFunction(predicate, value, { timeout: 25000 });
  events.push({ stage, observation: name });
}
async function navigate(url) { await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 }); }
async function capture(name) {
  const state = await evaluate(`({ url:location.href, title:document.title,
    headings:[...document.querySelectorAll('h1,h2,h3')].map(x=>x.textContent.trim()),
    body:document.body.innerText.slice(0,12000),
    sessionButtons:[...document.querySelectorAll('.session-picker button')].map(x=>x.textContent.trim()),
    root:!!document.getElementById('root'), bridge:!!window.researchos?.desktop })`);
  save(name + '.json', state);
  await page.screenshot({ path: path.join(receiptDir, name + '.png'), fullPage: false, timeout: 15000 });
  return state;
}
async function main() {
  browser = await connect();
  const contexts = browser.contexts();
  page = contexts.flatMap(context => context.pages()).find(candidate => candidate.url().startsWith('ros-app://')) ||
    contexts.flatMap(context => context.pages())[0];
  if (!page) throw Error('ELECTRON_PAGE_ABSENT');
  page.setDefaultTimeout(25000);
  page.on('pageerror', error => rendererErrors.push({ method: 'pageerror', text: String(error).slice(0,1000) }));
  page.on('console', message => {
    if (message.type() === 'error') rendererErrors.push({ method: 'console', text: message.text().slice(0,1000) });
  });
  page.on('requestfailed', request => requestFailures.push({ url: request.url(), error: request.failure()?.errorText }));
  save('driver.json', { driver: 'playwright.chromium.connectOverCDP', module: playwrightPath,
    version: require(path.join(playwrightPath, 'package.json')).version, page_url_at_connect: page.url(),
    page_count: contexts.reduce((count, context) => count + context.pages().length, 0) });
  // Electron starts its own navigation. Wait for it before an explicit route.
  stage = 'initial-load';
  await page.locator('#main h1').waitFor({ timeout: 30000 });
  const pid = encodeURIComponent(meta.project_id), tid = encodeURIComponent(meta.task_id);
  stage = 'session-list';
  await navigate('ros-app://desktop/p/' + pid);
  await waitFor(title => document.querySelector('.session-picker button') && document.body.innerText.includes(title), meta.session_title, 'restored session list');
  const before = await capture('01-session-list');
  stage = 'session-open';
  const clicked = await evaluate(`(() => { const button=[...document.querySelectorAll('.session-picker button')].find(x=>x.textContent.includes(${JSON.stringify(meta.session_title)})); if(!button) return false; button.click(); return true; })()`);
  if (!clicked) throw Error('SESSION_BUTTON_ABSENT');
  await waitFor(() => document.querySelector('.conversation-transcript')?.textContent.includes('backup'), null, 'restored transcript');
  const session = await capture('02-session-open');
  const native = await evaluate(`(async () => {
    const context = await window.researchos.desktop.context();
    const reply = await window.researchos.v2['session.get']({});
    const value = reply?.result || {};
    return { context, ok: reply?.ok, status: reply?.protocol_status,
      project_id: value.project_id, session_id: value.session_id, goal_id: value.goal_id,
      event_sequence: value.event_sequence, title: value.title };
  })()`);
  save('native-session.json', native);
  stage = 'continuation';
  await waitFor(title => document.querySelector('.session-continuation')?.textContent.includes(title), meta.goal_title, 'current session goal');
  const continuation = await evaluate(`(() => {
    const section = document.querySelector('.session-continuation');
    return { goal_id:section?.dataset.goalId, text:section?.textContent,
      task_links:[...(section?.querySelectorAll('a') || [])].map(link => ({ href:link.getAttribute('href'), title:link.textContent.trim() })) };
  })()`);
  save('native-continuation.json', continuation);
  const resume = page.getByRole('button', { name: '在此继续', exact: true });
  await resume.click();
  await page.getByRole('button', { name: '当前可写', exact: true }).waitFor();
  const writer = await evaluate(`(async () => {
    const snapshot = await window.researchos.v2['session.get']({});
    const host = await window.researchos.v2['host.status']({});
    return { snapshot:snapshot.result, session_ok:snapshot.ok, host_ok:host.ok, client_id:host.result?.client_id };
  })()`);
  save('native-resumed-writer.json', writer);
  const restoredFile = await evaluate(`window.researchos.v2['workspace.read']({ workspace_ref:${JSON.stringify(meta.workspace_ref)}, relative_path:'src/main.go', max_bytes:1048576 })`);
  save('native-restored-file.json', restoredFile);
  stage = 'task';
  await page.locator('.session-continuation a[href="/p/' + pid + '/tasks/' + tid + '"]').click();
  await waitFor(title => document.querySelector('h1')?.textContent.trim() === title, meta.task_title, 'restored task detail');
  const task = await capture('03-task');
  const taskRecord = await evaluate(`(async () => {
    const response = await fetch('/v1/projects/${pid}/tasks/${tid}', { headers: { Accept:'application/json' }, cache:'no-store' });
    if (!response.ok) return { http_status:response.status };
    const value = await response.json();
    return { http_status:response.status, id:value.id, goal_id:value.goal_id, title:value.title, status:value.status };
  })()`);
  save('native-task.json', taskRecord);
  stage = 'goal';
  await navigate('ros-app://desktop/p/' + pid);
  await waitFor(title => document.querySelector('.goal-section')?.textContent.includes(title), meta.goal_title, 'restored goal dashboard');
  const goal = await capture('04-goal');
  const checks = {
    session_list_title: before.sessionButtons.some(item => item.includes(meta.session_title)),
    session_open_title: session.body.includes(meta.session_title),
    restored_transcript: session.body.includes('backup'),
    task_detail_title: task.headings.includes(meta.task_title),
    task_url_id: task.url.endsWith('/tasks/' + tid),
    task_record_identity: taskRecord.http_status === 200 && taskRecord.id === meta.task_id &&
      taskRecord.goal_id === meta.goal_id && taskRecord.title === meta.task_title,
    goal_dashboard_title: goal.body.includes(meta.goal_title),
    native_session_identity: native.ok === true && native.status === 'COMPLETED' &&
      native.context?.session_id === meta.session_id && native.context?.project_id === meta.project_id &&
      native.session_id === meta.session_id && native.project_id === meta.project_id && native.goal_id === meta.goal_id,
    restored_event_cursor: native.event_sequence === meta.event_cursor,
    current_goal_scope: continuation.goal_id === meta.goal_id && continuation.text.includes(meta.goal_title),
    original_next_task_link: continuation.task_links.some(link => link.href === '/p/' + pid + '/tasks/' + tid && link.title.includes(meta.task_title)),
    same_session_writable_on_new_host: writer.session_ok === true && writer.host_ok === true &&
      writer.snapshot?.project_id === meta.project_id && writer.snapshot?.session_id === meta.session_id &&
      writer.snapshot?.goal_id === meta.goal_id && writer.snapshot?.writer?.client_id === writer.client_id,
    restored_workspace_bytes_readable: restoredFile.ok === true && restoredFile.result?.text === 'package continued\n',
    renderer_errors_zero: rendererErrors.length === 0,
    native_bridge_present: [before, session, task, goal].every(item => item.root && item.bridge),
  };
  save('gui-checks.json', checks);
  if (Object.values(checks).some(value => !value)) throw Error('GUI_ASSERTION_FAILED:' + JSON.stringify(checks));
  stage = 'complete';
  process.stdout.write(JSON.stringify({ status: 'PASS', checks, screenshots: 4, mode: 'FIXTURE', whole_card_accepted: false }) + '\n');
}
main().catch(async error => {
  save('gui-failure.json', { stage, error: String(error.stack || error), page_url: page?.url() || null });
  if (page) {
    try { await bounded(page.screenshot({ path: path.join(receiptDir, 'failure.png'), timeout: 4000 }), 'failure screenshot', 5000); }
    catch (diagnosticError) { save('diagnostic-failure.json', { error: String(diagnosticError) }); }
  }
  process.stderr.write(String(error.stack || error) + '\n'); process.exitCode = 1;
}).finally(async () => {
  save('renderer-events.json', { stage, events, renderer_errors: rendererErrors, request_failures: requestFailures });
  if (browser) await bounded(browser.close(), 'disconnect', 5000).catch(() => {});
});
