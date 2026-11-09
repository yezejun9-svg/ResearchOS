'use strict';
// Drive the actual Electron renderer against real sealed Artifact fixtures.
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const playwright = require(process.env.RESEARCHOS_PLAYWRIGHT_MODULE || 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/Lib/site-packages/playwright/driver/package');
const root = path.resolve(__dirname, '../../..');
const input = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const out = path.resolve(process.argv[3]);
const report = { schema: 'researchos.electron-preview.v1', status: 'EXECUTING', checks: [], failures: [], screenshots: [], observations: [], limitations: [
  'Real Electron and real local API with sealed FIXTURE artifacts; not independent formal acceptance.',
  'PDF Chromium rendering can vary; an observed preview or controlled fallback is recorded.',
] };
let app;
function check(id, okay, detail = null) {
  report.checks.push({ id, status: okay ? 'PASS' : 'FAIL', detail });
  if (!okay) report.failures.push(id);
}
async function capture(page, label) {
  const target = path.join(out, `preview-${label}.png`);
  await page.screenshot({ path: target, fullPage: true, timeout: 15000 });
  report.screenshots.push({ path: path.basename(target), sha256: createHash('sha256').update(fs.readFileSync(target)).digest('hex') });
}
async function openArtifact(page, label) {
  const item = input.artifacts[label];
  await page.goto(`ros-app://desktop${input.project_path}/evidence?focus=${encodeURIComponent(item.evidence_id)}`, { waitUntil: 'domcontentloaded', timeout: 20000 });
  const main = page.locator('#main');
  await main.locator('h1').waitFor({ timeout: 15000 });
  await main.getByRole('button', { name: '受控预览' }).waitFor({ timeout: 15000 });
  check(`${label}-SEALED_HASH_VISIBLE`, await main.innerText().then(text => text.includes(item.content_hash)));
  await main.getByRole('button', { name: '受控预览' }).click();
  await main.getByRole('button', { name: '重新读取' }).waitFor({ timeout: 20000 });
  await page.waitForTimeout(300);
  return main;
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
  report.origin = new URL(page.url()).origin;
  check('ACTUAL_ELECTRON_NATIVE_ORIGIN', page.url().startsWith('ros-app://desktop/') && await page.locator('#access-token').count() === 0, page.url());
  check('NO_RENDERER_CREDENTIAL', await page.evaluate(() => !window.researchos?.credential && !Object.keys(localStorage).some(key => /token|credential/i.test(key))));

  let main = await openArtifact(page, 'html');
  const frame = main.locator('iframe[title="无脚本 HTML 预览"]');
  await frame.waitFor({ timeout: 15000 });
  const sandbox = await frame.getAttribute('sandbox');
  const html = await frame.getAttribute('srcdoc');
  const child = frame.contentFrame();
  await child.locator('h1').waitFor({ timeout: 10000 });
  await page.waitForTimeout(700);
  const marked = await page.evaluate(() => document.body.dataset.previewPwned === 'yes');
  const childFrame = await (await frame.elementHandle()).contentFrame();
  const childExecuted = await childFrame.evaluate(() => window.fixtureExecuted === true);
  check('HTML_SANDBOX_EMPTY', sandbox === '', { sandbox });
  check('HTML_INNER_CSP_DENIES_NETWORK_AND_SCRIPT', html.includes("default-src 'none'") && html.includes("form-action 'none'"));
  check('HTML_SCRIPT_DID_NOT_REACH_PARENT', !marked);
  check('HTML_CHILD_SCRIPT_BLOCKED', !childExecuted);
  check('HTML_NAVIGATION_BLOCKED', page.url().startsWith('ros-app://desktop/'));
  report.observations.push({ format: 'html', child_heading: await child.locator('h1').innerText(), parent_marked: marked, child_script_executed: childExecuted, page_url: page.url() });
  await capture(page, 'html');

  main = await openArtifact(page, 'text');
  const text = await main.locator('pre.preview-text').innerText();
  check('UTF8_TEXT_EXACT', text.includes('中文 UTF-8 preview ✅') && text.includes('second line'), text);
  await capture(page, 'text');

  main = await openArtifact(page, 'image');
  const image = main.locator('img.preview-image');
  const imageResult = await image.evaluate(el => ({ complete: el.complete, width: el.naturalWidth, height: el.naturalHeight }));
  check('IMAGE_RENDERED', imageResult.complete && imageResult.width > 0 && imageResult.height > 0, imageResult);
  report.observations.push({ format: 'image', ...imageResult });
  await capture(page, 'image');

  main = await openArtifact(page, 'pdf');
  const pdfFrame = main.locator('iframe[title="PDF 预览"]');
  const fallback = main.getByRole('button', { name: '受控下载' });
  const pdf = { frame: await pdfFrame.count(), fallback: await fallback.count(), alert: await main.getByRole('alert').allInnerTexts() };
  check('PDF_PREVIEW_OR_CONTROLLED_FALLBACK', pdf.frame === 1 || pdf.fallback === 1, pdf);
  report.observations.push({ format: 'pdf', ...pdf });
  await capture(page, 'pdf');

  report.status = report.failures.length ? 'FAIL' : 'PASS';
}
main().catch(error => { report.status = 'FAIL'; report.error = error.stack || String(error); }).finally(async () => {
  if (app) await app.close().catch(() => {});
  fs.writeFileSync(path.join(out, 'preview.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify({ status: report.status, checks: report.checks.length, failures: report.failures, error: report.error || null }));
  process.exitCode = report.status === 'PASS' ? 0 : 1;
});
