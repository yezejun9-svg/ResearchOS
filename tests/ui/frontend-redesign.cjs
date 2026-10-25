'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
let playwright;
try { playwright = require(process.env.RESEARCHOS_PLAYWRIGHT_MODULE || 'playwright'); }
catch (error) { throw new Error('Playwright is unavailable; set RESEARCHOS_PLAYWRIGHT_MODULE to the installed driver package path', { cause: error }); }
const { installFixture, projectId } = require('./frontend-redesign-fixture.cjs');

const url = process.argv[2];
const out = path.resolve(process.argv[3]);
if (!url || !out || new URL(url).hostname !== '127.0.0.1') throw new Error('A task-owned loopback preview URL and output directory are required');
fs.mkdirSync(out, { recursive: true });
const report = { schema: 'researchos.frontend-redesign-fixture.v1', evidence_kind: 'VISUAL_INTERACTION_FIXTURE_ONLY', checks: [], screenshots: [], limitations: ['Browser and native-shaped bridges are disposable fixtures. No Core, owner, provider, or formal acceptance is asserted.'] };
function check(name, value, detail) { report.checks.push({ name, status: value ? 'PASS' : 'FAIL', detail }); assert.ok(value, `${name}: ${JSON.stringify(detail)}`); }
function shot(page, name) { const target = path.join(out, `${name}.png`); return page.screenshot({ path: target, fullPage: true }).then(() => report.screenshots.push({ name, path: target, sha256: createHash('sha256').update(fs.readFileSync(target)).digest('hex') })); }

async function main() {
  const browser = await playwright.chromium.launch({ headless: true });
  try {
    for (const width of [320, 768, 1024, 1440]) {
      for (const theme of ['light', 'dark']) {
        const context = await browser.newContext({ viewport: { width, height: 900 }, deviceScaleFactor: 1 });
        const page = await context.newPage();
        const errors = [];
        page.on('pageerror', error => errors.push(error.message));
        const fixture = await installFixture(page, { native: true });
        await page.addInitScript(theme => localStorage.setItem('researchos.theme', theme), theme);
        await page.goto(`${url}/p/${projectId}`, { waitUntil: 'domcontentloaded' });
        await page.getByRole('heading', { name: '河流污染证据核对' }).waitFor({ timeout: 12000 });
        await page.getByText('请核对上游与下游水质记录').waitFor({ timeout: 12000 });
        const metrics = await page.evaluate(() => ({ viewport: innerWidth, document: document.documentElement.scrollWidth,
          regions: [...document.querySelectorAll('.workbench-layout > *')].map(el => ({ label: el.getAttribute('aria-label'), width: Math.round(el.getBoundingClientRect().width) })),
          theme: document.documentElement.dataset.theme, font: getComputedStyle(document.body).fontFamily }));
        check(`${width}-${theme}-no-overflow`, metrics.document <= metrics.viewport, metrics);
        check(`${width}-${theme}-regions`, metrics.regions.length === 3 && metrics.regions.every(x => x.width > 0), metrics);
        check(`${width}-${theme}-theme`, metrics.theme === theme, metrics);
        check(`${width}-${theme}-font-stack`, metrics.font.includes('Microsoft YaHei UI') && metrics.font.includes('Microsoft YaHei'), metrics);
        check(`${width}-${theme}-console`, errors.length === 0, errors);
        check(`${width}-${theme}-interception`, fixture.unexpected.length === 0, fixture.unexpected);
        await shot(page, `native-${width}-${theme}`);
        if (width === 1440 && theme === 'light') {
          const input = page.getByRole('textbox', { name: '会话消息' });
          await input.fill('核对采样点 A 与 B 的时间差异。');
          await page.getByRole('button', { name: '发送', exact: true }).click();
          await page.getByText('核对采样点 A 与 B 的时间差异。').waitFor();
          const calls = await page.evaluate(() => window.__frontendFixtureCalls);
          check('native-send-callback', calls.some(x => x.name === 'session.send' && x.body.text.includes('采样点 A')), calls);
          check('native-pending-visible', await page.getByText('1 条命令等待处理。').count() === 1);
          await page.getByRole('button', { name: '打开阶段进度' }).click();
          check('drawer-focus', await page.evaluate(() => document.activeElement?.getAttribute('aria-label') === '关闭进度'));
          await page.keyboard.press('Escape');
          check('drawer-close-escape', await page.locator('.progress-rail.drawer-open').count() === 0);
          await shot(page, 'native-1440-pending');
        }
        await context.close();
      }
    }
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const fixture = await installFixture(page);
    await page.goto(`${url}/p/${projectId}`, { waitUntil: 'domcontentloaded' });
    await page.getByLabel('访问令牌').fill('disposable-fixture-token');
    await page.getByRole('button', { name: '打开工作台' }).click();
    await page.getByRole('heading', { name: '城市河流研究' }).waitFor();
    check('browser-workbench-route', new URL(page.url()).pathname === `/p/${projectId}`);
    check('browser-fixture-no-fallthrough', fixture.unexpected.length === 0, fixture.unexpected);
    check('browser-console', errors.length === 0, errors);
    await shot(page, 'browser-1440-light');
    await context.close();

    const pendingContext = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const pendingPage = await pendingContext.newPage();
    const pendingFixture = await installFixture(pendingPage, { native: true, qualificationState: 'AWAITING_CONFIRMATION' });
    await pendingPage.goto(`${url}/p/${projectId}`, { waitUntil: 'domcontentloaded' });
    const confirm = pendingPage.getByRole('button', { name: '明确确认一次调用' });
    await confirm.waitFor();
    check('qualification-pending-visible', await pendingPage.getByText('等待明确确认', { exact: true }).count() > 0 && await confirm.isEnabled());
    await shot(pendingPage, 'native-1440-confirmation-pending');
    pendingPage.once('dialog', dialog => dialog.dismiss());
    await confirm.click();
    const callsAfterDismiss = await pendingPage.evaluate(() => window.__frontendFixtureCalls);
    check('qualification-dismiss-does-not-confirm', !callsAfterDismiss.some(call => call.name === 'qualificationConfirm'), callsAfterDismiss);
    check('qualification-pending-no-fallthrough', pendingFixture.unexpected.length === 0, pendingFixture.unexpected);
    await pendingContext.close();

    const errorContext = await browser.newContext({ viewport: { width: 1024, height: 900 } });
    const errorPage = await errorContext.newPage();
    const errorFixture = await installFixture(errorPage, { native: true, profileError: true });
    await errorPage.goto(`${url}/p/${projectId}`, { waitUntil: 'domcontentloaded' });
    await errorPage.getByText('部分项目资料尚未读取').waitFor();
    check('partial-project-error-visible', await errorPage.getByRole('button', { name: '重新读取' }).count() > 0);
    check('partial-project-no-fallthrough', errorFixture.unexpected.length === 0, errorFixture.unexpected);
    await shot(errorPage, 'native-1024-partial-error');
    await errorContext.close();
  } finally { await browser.close(); }
}

main().then(() => { report.status = 'PASS'; }).catch(error => { report.status = 'FAIL'; report.error = error.stack || String(error); }).finally(() => {
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify({ status: report.status, checks: report.checks.length, screenshots: report.screenshots.length, error: report.error || null }));
  if (report.status !== 'PASS') process.exitCode = 1;
});
