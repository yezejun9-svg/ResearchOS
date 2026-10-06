'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const playwright = require(process.env.RESEARCHOS_PLAYWRIGHT_MODULE || 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/Lib/site-packages/playwright/driver/package');
const root = path.resolve(__dirname, '../../..');
const input = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const out = path.resolve(process.argv[3]);
const report = { schema: 'researchos.electron-workspace.v1', status: 'EXECUTING', checks: [], screenshots: [],
  limitations: ['Native directory selection callback is FIXTURE; file and API operations are real.',
    'No provider execution, installed-release acceptance or independent acceptance is asserted.'] };
let app, page;
function check(id, okay, detail = null) {
  report.checks.push({ id, status: okay ? 'PASS' : 'FAIL', detail });
  if (!okay) throw new Error('failed assertion: ' + id);
}
async function screenshot(name) {
  const file = path.join(out, name + '.png');
  await page.screenshot({ path: file, fullPage: true });
  report.screenshots.push({ file: name + '.png', sha256: createHash('sha256').update(fs.readFileSync(file)).digest('hex') });
}
async function settle() {
  await page.locator('#main h1').waitFor();
  await page.waitForFunction(() => !document.querySelector('#main .loading-state'));
}
async function idle() {
  await page.waitForFunction(() => ![...document.querySelectorAll('.session-center p[role=status]')].some(node => /…$/.test(node.textContent)));
}
async function main() {
  const relative = path.relative(path.join(root, '.local'), input.workspace_root);
  check('ISOLATED_WORKSPACE_ROOT', !relative.startsWith('..') && !path.isAbsolute(relative) && /^researchos-w13-ui-workspace-[^\\/]+[\\/]/.test(relative));
  const source = path.join(input.workspace_root, input.source_path || 'source.txt');
  const initial = fs.readFileSync(source, 'utf8');
  const rendererErrors = [];
  app = await playwright._electron.launch({
    executablePath: process.env.RESEARCHOS_ELECTRON || path.join(root, 'apps/desktop/node_modules/electron/dist/electron.exe'),
    args: [path.join(root, 'apps/desktop')], cwd: root, env: process.env, timeout: 40000,
  });
  page = await app.firstWindow();
  page.on('pageerror', error => rendererErrors.push(String(error)));
  await settle();
  await page.goto('ros-app://desktop/p/' + input.project_id, { waitUntil: 'domcontentloaded' });
  await settle();
  await page.locator('.session-picker li button').first().click();
  await page.getByRole('heading', { name: '工作区文件与差异', exact: true }).waitFor();
  const continueButton = page.getByRole('button', { name: '在此继续', exact: true });
  if (await continueButton.count()) await continueButton.click();
  await page.getByRole('button', { name: '当前可写', exact: true }).waitFor();
  check('NATIVE_SESSION_WRITER', await page.getByRole('button', { name: '当前可写', exact: true }).isDisabled());
  await page.getByRole('button', { name: '读取文件树', exact: true }).click();
  await page.locator('.file-list').getByRole('button', { name: input.source_path || 'source.txt', exact: true }).waitFor();
  check('REAL_TREE_SOURCE_VISIBLE', await page.locator('.file-list li').count() >= 3);
  const binary = page.locator('.file-list').getByRole('button', { name: input.binary_path || 'binary.dat', exact: true });
  check('UNREADABLE_BINARY_DISABLED', await binary.isDisabled());
  await page.getByRole('button', { name: '查看差异', exact: true }).click();
  await page.getByRole('button', { name: '读取完整差异', exact: true }).waitFor();
  check('TRUNCATED_DIFF_HAS_FULL_ARTIFACT', true);
  await page.getByRole('button', { name: '读取完整差异', exact: true }).click();
  await page.getByRole('button', { name: '受控预览', exact: true }).click();
  await page.getByRole('link', { name: '下载已核对的内容', exact: true }).waitFor();
  check('FULL_DIFF_HASH_VERIFIED_PREVIEW', (await page.locator('.artifact-preview .preview-text').textContent()).includes('diff --git'));
  await screenshot('full-diff');
  const directory = input.directory_path || 'nested';
  await page.locator('.file-list').getByRole('button', { name: directory + ' /', exact: true }).click();
  await page.getByRole('button', { name: '上级目录', exact: true }).waitFor();
  check('DIRECTORY_NAVIGATION', (await page.locator('.file-list li').count()) > 0);
  await page.getByRole('button', { name: '上级目录', exact: true }).click();
  await page.locator('.file-list').getByRole('button', { name: input.source_path || 'source.txt', exact: true }).click();
  const editor = page.getByRole('textbox', { name: '文件草稿', exact: true });
  await editor.waitFor();
  const wire = await page.evaluate(workspace => window.researchos.v2['workspace.read']({ workspace_ref: workspace, relative_path: 'source.txt', max_bytes: 1048576 }), input.workspace_ref);
  check('READ_EXACT_WIRE_TEXT', wire.ok && wire.result?.text === initial);
  check('EDITOR_REPRESENTS_SOURCE_TEXT', await editor.inputValue() === initial.replace(/\r\n?/g, '\n'), 'HTML textarea exposes line endings as LF; the typed response preserves original CRLF bytes.');
  check('REAL_FROZEN_TASK_PRESENT', typeof input.task_id === 'string' && input.task_id.length > 0);
  await page.getByRole('combobox', { name: /^关联任务/ }).selectOption(input.task_id);
  const saved = 'Desktop 保存的实际文本\nsecond line\n';
  await editor.fill(saved);
  await page.getByRole('button', { name: '保存草稿', exact: true }).click();
  await idle();
  check('WRITE_EXACT_PHYSICAL_BYTES', fs.readFileSync(source).equals(Buffer.from(saved)));
  check('WRITE_REFRESHED_BASELINE', await editor.inputValue() === saved && await page.getByRole('button', { name: '保存草稿', exact: true }).isDisabled());
  await page.getByRole('button', { name: '附加到消息', exact: true }).click();
  await page.locator('.session-composer p').filter({ hasText: '已附加受控产物' }).waitFor();
  await idle();
  const artifactId = await page.locator('.session-composer p .break-all').textContent();
  const sealed = await page.evaluate(async ({ project, artifactId }) => {
    const response = await fetch(`/v1/projects/${project}/artifacts/${artifactId}/content`);
    return { status: response.status, text: await response.text() };
  }, { project: input.project_id, artifactId });
  check('IMPORTED_ARTIFACT_EXACT_BYTES', sealed.status === 200 && sealed.text === saved);
  const draft = '尚未保存的用户草稿\n';
  await editor.fill(draft);
  const external = '外部编辑器的新版本\n';
  fs.writeFileSync(source, external);
  await page.getByRole('button', { name: '保存草稿', exact: true }).click();
  await page.getByText('外部版本已改变，当前草稿仍保留。请复制需要保留的内容，重新读取并手工合并。', { exact: true }).waitFor();
  check('HASH_CONFLICT_PRESERVES_FILE_AND_DRAFT', fs.readFileSync(source, 'utf8') === external && await editor.inputValue() === draft);
  check('CONFLICT_REQUIRES_REBASE', await page.getByRole('button', { name: '保存草稿', exact: true }).isDisabled());
  page.once('dialog', dialog => dialog.dismiss());
  await page.locator('.session-picker li button').first().click();
  check('DISMISSED_SESSION_SWITCH_PRESERVES_DRAFT', await editor.inputValue() === draft);
  await screenshot('conflict-preserved');
  page.once('dialog', dialog => dialog.accept());
  await page.getByRole('button', { name: '核对外部版本', exact: true }).click();
  await idle();
  check('EXPLICIT_REBASE_LOADS_EXTERNAL_VERSION', await editor.inputValue() === external);
  await editor.fill('');
  await page.getByRole('button', { name: '保存草稿', exact: true }).click();
  await idle();
  check('EMPTY_TEXT_WRITE_ALLOWED', fs.readFileSync(source).length === 0 && await editor.inputValue() === '');
  await screenshot('empty-write-complete');
  check('NO_RENDERER_ERRORS', rendererErrors.length === 0, rendererErrors);
  report.status = 'PASS';
}
main().catch(async error => {
  report.status = 'FAIL'; report.error = String(error.stack || error);
  if (page && !page.isClosed()) { try { await screenshot('failure'); } catch {} }
}).finally(async () => {
  if (app) await app.close();
  report.finished_at = new Date().toISOString();
  fs.writeFileSync(path.join(out, 'workspace.json'), JSON.stringify(report, null, 2));
  process.exitCode = report.status === 'PASS' ? 0 : 1;
});
