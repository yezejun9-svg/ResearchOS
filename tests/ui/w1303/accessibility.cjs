'use strict';
// Actual Electron accessibility observations; no renderer API or DOM patching.
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const playwright = require(process.env.RESEARCHOS_PLAYWRIGHT_MODULE || 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/Lib/site-packages/playwright/driver/package');
const root = path.resolve(__dirname, '../../..');
const input = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const out = path.resolve(process.argv[3]);
const report = { schema: 'researchos.electron-accessibility.v1', status: 'EXECUTING', checks: [], failures: [], theme_settle: [], contrast: [], targets: [], keyboard: [], reduced_motion: [], accessibility_tree: [], screenshots: [], limitations: [
  'Measured Electron Chromium semantics and computed styles; Windows UI Automation and physical screen-reader speech were not measured.',
  'Representative color pairs and primary mobile controls are sampled; this is not an exhaustive WCAG audit.',
  'Real local API with temporary FIXTURE project; formal independent acceptance remains separate.',
] };
let app;
function check(id, okay, detail = null) {
  report.checks.push({ id, status: okay ? 'PASS' : 'FAIL', detail });
  if (!okay) report.failures.push(id);
}
async function capture(page, name) {
  const file = path.join(out, `accessibility-${name}.png`);
  await page.screenshot({ path: file, fullPage: true, timeout: 15000 });
  report.screenshots.push({ path: path.basename(file), sha256: createHash('sha256').update(fs.readFileSync(file)).digest('hex') });
}
async function setViewport(width, height) {
  await app.evaluate(({ BrowserWindow }, size) => {
    const win = BrowserWindow.getAllWindows()[0];
    win.setMinimumSize(0, 0); win.setContentSize(size.width, size.height); win.webContents.setZoomFactor(1);
  }, { width, height });
}
async function navigate(page, route) {
  await page.goto('ros-app://desktop' + route, { waitUntil: 'domcontentloaded', timeout: 20000 });
  await page.locator('#main h1').waitFor({ timeout: 20000 });
  await page.waitForFunction(() => !document.querySelector('#main .loading-state'), null, { timeout: 20000 });
}
async function focusInfo(page) {
  return page.evaluate(() => {
    const el = document.activeElement;
    if (!el) return null;
    const style = getComputedStyle(el);
    return { tag: el.tagName, label: el.getAttribute('aria-label') || el.textContent?.trim().slice(0, 80) || '',
      href: el.getAttribute('href'), outline_style: style.outlineStyle, outline_width: style.outlineWidth,
      matches_focus_visible: el.matches(':focus-visible') };
  });
}
async function settleTheme(page, theme) {
  const samples = [];
  const start = Date.now();
  let stable = false;
  do {
    const value = await page.evaluate(() => ({
      nav: getComputedStyle(document.querySelector('.sidebar .nav-link')).color,
      title: getComputedStyle(document.querySelector('#main h1')).color,
      muted_token: getComputedStyle(document.documentElement).getPropertyValue('--muted').trim(),
      running_animations: document.getAnimations().filter(animation => animation.playState === 'running').length,
    }));
    samples.push({ elapsed_ms: Date.now() - start, ...value });
    const previous = samples.at(-2);
    stable = !!previous && value.running_animations === 0 && value.nav === previous.nav && value.title === previous.title;
    if (stable) break;
    await page.waitForTimeout(35);
  } while (Date.now() - start < 300);
  report.theme_settle.push({ theme, stable, samples });
  check(`THEME_SETTLED-${theme}`, stable, { elapsed_ms: Date.now() - start, samples });
  const final = samples.at(-1);
  const normalize = color => color.replace(/\s+/g, '').toLowerCase();
  const hex = /^#([a-f0-9]{6})$/i.exec(final.muted_token);
  const tokenRGB = hex ? `rgb(${[0, 2, 4].map(index => Number.parseInt(hex[1].slice(index, index + 2), 16)).join(', ')})` : null;
  check(`NAV_COLOR_MATCHES_MUTED_TOKEN-${theme}`, normalize(final.nav) === normalize(tokenRGB), { nav: final.nav, token: final.muted_token, computed_token: tokenRGB });
}
async function measureContrast(page, theme) {
  const samples = await page.evaluate(() => {
    const selectors = ['#main h1', '#main .page-heading p', '.topbar .brand', '.topbar .connection-text', '.sidebar .nav-link'];
    const rgba = value => {
      const m = value.match(/rgba?\(([^)]+)\)/);
      if (!m) return null;
      const parts = m[1].split(/[,\s/]+/).filter(Boolean).map(Number);
      return { rgb: parts.slice(0, 3), alpha: parts[3] ?? 1 };
    };
    const background = el => {
      let node = el, color = [255, 255, 255];
      const layers = [];
      while (node) {
        const parsed = rgba(getComputedStyle(node).backgroundColor);
        if (parsed && parsed.alpha > 0) layers.push(parsed);
        node = node.parentElement;
      }
      for (const layer of layers.reverse()) color = layer.rgb.map((v, i) => v * layer.alpha + color[i] * (1 - layer.alpha));
      return color;
    };
    const luminance = rgb => rgb.map(x => {
      const c = x / 255;
      return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
    }).reduce((acc, value, index) => acc + value * [0.2126, 0.7152, 0.0722][index], 0);
    return selectors.map(selector => {
      const el = document.querySelector(selector);
      if (!el || !el.getClientRects().length) return { selector, missing: true };
      const style = getComputedStyle(el), foreground = rgba(style.color)?.rgb, bg = background(el);
      const [high, low] = [luminance(foreground), luminance(bg)].sort((a, b) => b - a);
      return { selector, text: el.textContent?.trim().slice(0, 80), foreground, background: bg,
        font_size: style.fontSize, font_weight: style.fontWeight, ratio: Math.round((high + 0.05) / (low + 0.05) * 100) / 100,
        threshold: selector === '#main h1' ? 3 : 4.5 };
    });
  });
  for (const sample of samples) {
    report.contrast.push({ theme, ...sample });
    check(`CONTRAST-${theme}-${sample.selector}`, !sample.missing && sample.ratio >= sample.threshold, sample);
  }
}
async function measureTargets(page) {
  const groups = ['.topbar button', '.topbar .brand', '.bottom-nav a', '.sidebar.drawer-open .nav-link', '.sidebar.drawer-open .drawer-close'];
  const values = await page.evaluate(selectors => selectors.flatMap(selector => [...document.querySelectorAll(selector)].filter(el => el.getClientRects().length).map(el => {
    const rect = el.getBoundingClientRect();
    return { selector, label: el.getAttribute('aria-label') || el.textContent?.trim().slice(0, 60) || '', width: +rect.width.toFixed(1), height: +rect.height.toFixed(1) };
  })), groups);
  report.targets = values;
  for (const selector of groups) check(`MOBILE_TARGETS_PRESENT-${selector}`, values.some(item => item.selector === selector));
  for (const value of values) check(`MOBILE_44PX-${value.selector}-${value.label}`, value.width >= 44 && value.height >= 44, value);
}
async function reducedMotion(page) {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  const values = await page.evaluate(() => {
    const selectors = ['.sidebar', '.progress-rail', '.drawer-overlay', '.nav-link', '.topbar button'];
    return { matches: matchMedia('(prefers-reduced-motion: reduce)').matches,
      styles: selectors.map(selector => { const el = document.querySelector(selector), style = getComputedStyle(el);
        return { selector, transition: style.transitionDuration, animation: style.animationDuration }; }) };
  });
  report.reduced_motion = values;
  const zero = value => value.split(',').every(part => Number.parseFloat(part) === 0);
  check('REDUCED_MOTION_MEDIA_APPLIED', values.matches, values);
  check('REDUCED_MOTION_EFFECTS_ZERO', values.styles.every(item => zero(item.transition) && zero(item.animation)), values.styles);
  await page.emulateMedia({ reducedMotion: 'no-preference' });
}
async function keyboard(page) {
  await setViewport(390, 844);
  await navigate(page, `/p/${input.project_id}/resources`);
  const snapshot = await page.locator('body').ariaSnapshot();
  fs.writeFileSync(path.join(out, 'accessibility-mobile.aria.yml'), snapshot);
  report.accessibility_tree.push({ file: 'accessibility-mobile.aria.yml', bytes: Buffer.byteLength(snapshot) });
  check('AX_LANDMARKS_AND_LABELS', /navigation/.test(snapshot) && /main/.test(snapshot) && /打开导航/.test(snapshot));
  const focusTrace = [];
  for (let i = 0; i < 20; i++) {
    await page.keyboard.press('Tab');
    const active = await focusInfo(page); focusTrace.push(active);
    if (active?.label === '打开导航') break;
  }
  report.keyboard.push({ step: 'Tab to navigation opener', focus_trace: focusTrace });
  check('KEYBOARD_TAB_REACHES_MENU', focusTrace.at(-1)?.label === '打开导航', focusTrace);
  if (focusTrace.at(-1)?.label !== '打开导航') return;
  check('KEYBOARD_VISIBLE_FOCUS', focusTrace.at(-1).matches_focus_visible && focusTrace.at(-1).outline_style !== 'none' && Number.parseFloat(focusTrace.at(-1).outline_width) > 0, focusTrace.at(-1));
  await page.keyboard.press('Enter');
  await page.locator('.sidebar.drawer-open .drawer-close').waitFor({ timeout: 5000 });
  const opened = await focusInfo(page);
  report.keyboard.push({ step: 'Enter opens navigation', focus: opened });
  check('DRAWER_OPEN_FOCUS_CLOSE', opened?.label === '关闭导航' && await page.locator('#main').getAttribute('inert') !== null, opened);
  await measureTargets(page);
  await capture(page, 'mobile-drawer-open');
  await page.keyboard.press('Shift+Tab');
  const wrapped = await focusInfo(page);
  report.keyboard.push({ step: 'Shift+Tab wraps inside drawer', focus: wrapped });
  check('DRAWER_REVERSE_TAB_TRAP', !!wrapped?.label && wrapped.label !== '打开导航' && await page.evaluate(() => document.activeElement?.closest('.sidebar') !== null), wrapped);
  await page.keyboard.press('Escape');
  await page.locator('.sidebar.drawer-open').waitFor({ state: 'detached', timeout: 5000 });
  const returned = await focusInfo(page);
  report.keyboard.push({ step: 'Escape closes drawer and returns focus', focus: returned });
  check('DRAWER_ESCAPE_FOCUS_RETURN', returned?.label === '打开导航' && await page.locator('#main').getAttribute('inert') === null, returned);
  await capture(page, 'mobile-drawer-closed');
  await page.keyboard.press('Enter');
  await page.locator('.sidebar.drawer-open .drawer-close').waitFor({ timeout: 5000 });
  const routeTrace = [];
  for (let i = 0; i < 20; i++) {
    await page.keyboard.press('Tab');
    const active = await focusInfo(page); routeTrace.push(active);
    if (active?.href?.endsWith('/cycles')) break;
  }
  report.keyboard.push({ step: 'Tab through drawer to cycle link', focus_trace: routeTrace });
  check('KEYBOARD_REACHES_CYCLE_LINK', routeTrace.at(-1)?.href?.endsWith('/cycles'), routeTrace);
  if (routeTrace.at(-1)?.href?.endsWith('/cycles')) {
    await page.keyboard.press('Enter');
    await page.waitForURL(/\/cycles(?:\/|$)/, { timeout: 10000 });
    report.keyboard.push({ step: 'Enter navigates to cycle', url: page.url() });
    check('KEYBOARD_CYCLE_NAVIGATION', page.url().includes('/cycles'));
  }
  await page.getByRole('button', { name: '打开阶段进度' }).click();
  const railFocus = await focusInfo(page);
  await page.keyboard.press('Escape');
  const railReturn = await focusInfo(page);
  report.keyboard.push({ step: 'Rail Escape', opened: railFocus, returned: railReturn });
  check('RAIL_ESCAPE_FOCUS_RETURN', railFocus?.label === '关闭进度' && railReturn?.label === '打开阶段进度');
  await page.getByRole('button', { name: /打开通知/ }).click();
  const noticeFocus = await focusInfo(page);
  await page.keyboard.press('Escape');
  const noticeReturn = await focusInfo(page);
  report.keyboard.push({ step: 'Notice Escape', opened: noticeFocus, returned: noticeReturn });
  check('NOTICE_ESCAPE_FOCUS_RETURN', noticeFocus?.label === '关闭通知' && /^打开通知/.test(noticeReturn?.label || ''));
}
async function main() {
  app = await playwright._electron.launch({
    executablePath: process.env.RESEARCHOS_ELECTRON || path.join(root, 'apps/desktop/node_modules/electron/dist/electron.exe'),
    args: [path.join(root, 'apps/desktop')], cwd: root,
    env: { ...process.env, RESEARCHOS_CLI_DISCOVERY: input.discovery_file }, timeout: 40000,
  });
  const page = await app.firstWindow();
  await page.locator('#main h1').waitFor({ timeout: 20000 });
  report.electron = await app.evaluate(() => process.versions.electron);
  check('ACTUAL_ELECTRON_NATIVE_ORIGIN', page.url().startsWith('ros-app://desktop/') && await page.locator('#access-token').count() === 0, page.url());
  await setViewport(1440, 1000);
  await navigate(page, `/p/${input.project_id}/resources`);
  for (const theme of ['light', 'dark']) {
    await page.evaluate(value => localStorage.setItem('researchos.theme', value), theme);
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.locator('#main h1').waitFor({ timeout: 15000 });
    await page.waitForFunction(value => document.documentElement.dataset.theme === value, theme, { timeout: 10000 });
    await settleTheme(page, theme);
    await measureContrast(page, theme);
    await capture(page, `contrast-${theme}`);
  }
  await reducedMotion(page);
  await keyboard(page);
  report.status = report.failures.length ? 'FAIL' : 'PASS';
}
main().catch(error => { report.status = 'FAIL'; report.error = error.stack || String(error); }).finally(async () => {
  if (app) await app.close().catch(() => {});
  fs.writeFileSync(path.join(out, 'accessibility.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify({ status: report.status, checks: report.checks.length, failures: report.failures, error: report.error || null }));
  process.exitCode = report.status === 'PASS' ? 0 : 1;
});
