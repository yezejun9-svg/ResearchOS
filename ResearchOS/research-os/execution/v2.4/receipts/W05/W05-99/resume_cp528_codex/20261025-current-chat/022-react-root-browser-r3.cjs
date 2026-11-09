'use strict';
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const { createHash } = require('node:crypto');
const playwright = require('C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/Lib/site-packages/playwright/driver/package');
const fixturePath = "D:/作品集/ResearchOS/research-os/.local/worktrees/react-workbench-redesign-20261025/tests/ui/frontend-redesign-fixture.cjs";
const { installFixture, projectId } = require(fixturePath);
const out = "D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/root-react-browser-03"; fs.mkdirSync(out, { recursive: false });
const priorPath = "D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/root-react-browser-02/report.json"; const prior = JSON.parse(fs.readFileSync(priorPath));
const priorPassed = prior.checks.slice(0, -1); assert(priorPassed.every(x => x.pass)); assert.equal(prior.checks.at(-1).name, 'sidebar-connection-state-consistent');
const report = { evidence: 'ROOT_BROWSER_NATIVE_SHAPED_FIXTURE_ONLY', formalIncrement: 0, priorMobileChecks: { path: priorPath, sha256: createHash('sha256').update(fs.readFileSync(priorPath)).digest('hex'), checksPassed: priorPassed.length, excludedExactTextAssertion: prior.checks.at(-1) }, fixtureSha256: createHash('sha256').update(fs.readFileSync(fixturePath)).digest('hex'), checks: [], screenshots: [] };
function check(name, value, detail) { report.checks.push({ name, pass: !!value, detail }); assert.ok(value, name + ': ' + JSON.stringify(detail)); }
async function shot(page, name) { const p = path.join(out, name + '.png'); await page.screenshot({ path: p, fullPage: true }); report.screenshots.push({ path: p, sha256: createHash('sha256').update(fs.readFileSync(p)).digest('hex') }); }
async function main() {
 const browser = await playwright.chromium.launch({ headless: true });
 try {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } }); const page = await context.newPage();
  const errors = []; page.on('pageerror', e => errors.push(e.message)); const fixture = await installFixture(page, { native: true });
  await page.goto('http://127.0.0.1:5197/p/' + projectId, { waitUntil: 'domcontentloaded' }); await page.getByRole('heading', { name: '河流污染证据核对' }).waitFor();
  await page.locator('.sidebar-bottom .offline-dot').waitFor();
  const sidebar = await page.locator('.sidebar-bottom').innerText();
  check('sidebar-global-disconnected-semantic-consistency', /断开|中断/.test(sidebar) && await page.locator('.topbar .offline-dot').count() === 1, sidebar);
  const visible = await page.locator('body').innerText(); check('primary-state-labels-human-readable', !visible.includes('WAITING') && !visible.includes('NOT_REQUESTED'));
  const title = await page.getByRole('heading', { name: '工作区文件与差异', exact: true }).evaluate(el => ({ height: el.getBoundingClientRect().height, lineHeight: parseFloat(getComputedStyle(el).lineHeight) }));
  check('context-card-title-no-orphan-line', title.height <= title.lineHeight * 1.5, title);
  check('no-page-errors', errors.length === 0, errors); check('no-unexpected-network', fixture.unexpected.length === 0, fixture.unexpected);
  await shot(page, 'desktop-corrected-light');
  await page.getByRole('button', { name: '切换为深色主题', exact: true }).click(); check('theme-toggle', await page.locator('html').getAttribute('data-theme') === 'dark'); await shot(page, 'desktop-corrected-dark');
  await page.setViewportSize({ width: 320, height: 900 }); const size = await page.evaluate(() => ({ width: innerWidth, content: document.documentElement.scrollWidth }));
  check('current-build-mobile-no-overflow', size.content <= size.width, size); await shot(page, 'mobile-corrected-dark');
  await context.close();
 } finally { await browser.close(); }
}
main().then(() => report.status = 'PASS').catch(e => { report.status = 'FAIL'; report.error = e.stack; process.exitCode = 1; }).finally(() => { fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2)); console.log(JSON.stringify({ status: report.status, priorMobilePassed: priorPassed.length, checks: report.checks.length, screenshots: report.screenshots.length, error: report.error || null })); });
