'use strict';
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { createHash } = require('node:crypto');
const playwright = require('C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/Lib/site-packages/playwright/driver/package');
const fixturePath = "D:/作品集/ResearchOS/research-os/.local/worktrees/react-workbench-redesign-20261025/tests/ui/frontend-redesign-fixture.cjs";
const { installFixture, projectId } = require(fixturePath);
const out = "D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/root-react-browser-01";
fs.mkdirSync(out, { recursive: false });
const report = { evidence: 'INDEPENDENT_ROOT_BROWSER_NATIVE_SHAPED_FIXTURE_ONLY', sourceFrozen: false, formalIncrement: 0, checks: [], screenshots: [], fixtureSha256: createHash('sha256').update(fs.readFileSync(fixturePath)).digest('hex') };
function check(name, value, detail) { report.checks.push({ name, pass: !!value, detail }); assert.ok(value, name + ': ' + JSON.stringify(detail)); }
async function shot(page, name) { const target = path.join(out, name + '.png'); await page.screenshot({ path: target, fullPage: true }); report.screenshots.push({ path: target, sha256: createHash('sha256').update(fs.readFileSync(target)).digest('hex') }); }
async function main() {
 const browser = await playwright.chromium.launch({ headless: true });
 try {
  const context = await browser.newContext({ viewport: { width: 320, height: 900 } });
  const page = await context.newPage(); const errors = []; page.on('pageerror', e => errors.push(e.message));
  const fixture = await installFixture(page, { native: true });
  await page.goto('http://127.0.0.1:5197/p/' + projectId, { waitUntil: 'domcontentloaded' });
  await page.getByRole('heading', { name: '河流污染证据核对' }).waitFor();
  const toggle = page.getByRole('button', { name: '打开导航', exact: true });
  await toggle.click();
  check('mobile-navigation-initial-focus', await page.evaluate(() => document.activeElement?.getAttribute('aria-label') === '关闭导航'));
  for (let i = 0; i < 14; i++) { await page.keyboard.press('Tab'); check('mobile-navigation-trap-' + i, await page.evaluate(() => !!document.activeElement?.closest('.sidebar.drawer-open'))); }
  await page.keyboard.press('Escape');
  check('mobile-navigation-escape-focus-return', await toggle.evaluate(el => el === document.activeElement));
  check('mobile-navigation-closed', await page.locator('.sidebar.drawer-open').count() === 0);
  await toggle.click();
  const cycle = page.getByRole('navigation', { name: '主导航', exact: true }).getByRole('link', { name: '研究周期', exact: true });
  const next = await cycle.getAttribute('href'); await cycle.click(); await page.waitForURL(u => u.pathname === next);
  check('mobile-navigation-route', new URL(page.url()).pathname === next, next);
  check('mobile-navigation-closes-after-route', await page.locator('.sidebar.drawer-open').count() === 0);
  await page.goBack(); await page.getByRole('heading', { name: '河流污染证据核对' }).waitFor();
  check('browser-back-restores-workbench', new URL(page.url()).pathname === '/p/' + projectId);
  const progress = page.getByRole('button', { name: '打开阶段进度', exact: true }); await progress.click();
  check('progress-initial-focus', await page.evaluate(() => document.activeElement?.getAttribute('aria-label') === '关闭进度'));
  await page.keyboard.press('Escape'); check('progress-escape-focus-return', await progress.evaluate(el => el === document.activeElement));
  const font = await page.evaluate(() => getComputedStyle(document.body).fontFamily); check('explicit-Chinese-system-font', font.includes('Microsoft YaHei'), font);
  const dimensions = await page.evaluate(() => ({ viewport: innerWidth, content: document.documentElement.scrollWidth }));
  check('mobile-no-overflow', dimensions.content <= dimensions.viewport, dimensions);
  await shot(page, 'mobile-after-keyboard-navigation');
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.getByRole('heading', { name: '河流污染证据核对' }).waitFor();
  const sidebarStatus = await page.locator('.sidebar-bottom').innerText();
  check('sidebar-connection-state-consistent', sidebarStatus.includes('连接中断'), sidebarStatus);
  check('human-readable-run-state', await page.getByText('等待输入', { exact: true }).count() > 0 || await page.getByText('等待继续', { exact: true }).count() > 0, await page.locator('.session-main').count() ? await page.locator('.session-main').innerText() : null);
  await shot(page, 'desktop-after-root-feedback');
  check('no-page-errors', errors.length === 0, errors);
  check('no-unexpected-network', fixture.unexpected.length === 0, fixture.unexpected);
  report.requests = fixture.requests;
  await context.close();
 } finally { await browser.close(); }
}
main().then(() => report.status = 'PASS').catch(e => { report.status = 'FAIL'; report.error = e.stack; process.exitCode = 1; }).finally(() => { fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2)); console.log(JSON.stringify({ status: report.status, checks: report.checks.length, screenshots: report.screenshots.length, error: report.error || null })); });
