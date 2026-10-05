'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const playwright = require(process.env.RESEARCHOS_PLAYWRIGHT_MODULE ||
  'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/Lib/site-packages/playwright/driver/package');

const root = path.resolve(__dirname, '../../..');
const input = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const out = path.resolve(process.argv[3]);
const report = { schema: 'researchos.electron-transcript.v1', measurement_mode: 'FIXTURE', whole_card_accepted: false,
  status: 'EXECUTING', checks: [], screenshots: [], renderer_errors: [], request_failures: [] };
let app, page;
const hash = bytes => 'sha256:' + createHash('sha256').update(bytes).digest('hex');
function check(id, okay, detail = null) {
  report.checks.push({ id, status: okay ? 'PASS' : 'FAIL', detail });
  if (!okay) throw Error('failed assertion: ' + id);
}
async function screenshot(name) {
  const file = path.join(out, name + '.png');
  await page.screenshot({ path: file, fullPage: false });
  report.screenshots.push({ name: name + '.png', sha256: hash(fs.readFileSync(file)) });
}
async function main() {
  const rel = path.relative(path.join(root, '.local'), input.workspace_root);
  check('FRESH_ISOLATED_FIXTURE_ROOT', !rel.startsWith('..') && !path.isAbsolute(rel) &&
    /^researchos-w13-ui-transcript-[^\\/]+[\\/]service[\\/]chosen$/.test(rel));
  app = await playwright._electron.launch({
    executablePath: path.join(root, 'apps/desktop/node_modules/electron/dist/electron.exe'),
    args: [path.join(root, 'apps/desktop')], cwd: root, env: process.env, timeout: 50000,
  });
  page = await app.firstWindow();
  page.on('pageerror', error => report.renderer_errors.push(String(error)));
  page.on('console', message => { if (message.type() === 'error') report.renderer_errors.push(message.text()); });
  page.on('requestfailed', request => report.request_failures.push({ url: request.url(), failure: request.failure()?.errorText }));
  await page.goto('ros-app://desktop/p/' + encodeURIComponent(input.project_id), { waitUntil: 'domcontentloaded' });
  await page.locator('.session-picker li button').first().waitFor();
  const sessionButtons = await page.locator('.session-picker li button').count();
  check('ONE_FIXTURE_SESSION_VISIBLE', sessionButtons === 1);
  await page.locator('.session-picker li button').first().click();
  const articles = page.locator('.conversation-transcript article.conversation-message');
  await page.waitForFunction(() => document.querySelectorAll('.conversation-transcript article.conversation-message').length === 200);
  check('LATEST_200_VISIBLE', await articles.count() === 200);
  const firstText = await articles.first().locator('.message-text').textContent();
  const lastText = await articles.last().locator('.message-text').textContent();
  check('FIRST_VISIBLE_IS_SEED_2', firstText === 'u002');
  check('LAST_VISIBLE_EXACT_TEXT_HASH', hash(Buffer.from(lastText, 'utf8')) === input.last_text_hash &&
    Buffer.byteLength(lastText, 'utf8') === input.last_text_bytes);
  const wire = await page.evaluate(async () => {
    const context = await window.researchos.desktop.context();
    const reply = await window.researchos.v2['session.get']({});
    return { context, ok: reply?.ok, status: reply?.protocol_status, snapshot: reply?.result || null };
  });
  const snapshot = wire.snapshot || {};
  const ref = snapshot.transcript_artifact_ref;
  check('NATIVE_SAME_SESSION_GOAL', wire.ok === true && wire.status === 'COMPLETED' &&
    wire.context?.project_id === input.project_id && wire.context?.session_id === input.session_id &&
    snapshot.project_id === input.project_id && snapshot.session_id === input.session_id && snapshot.goal_id === input.goal_id);
  check('NATIVE_SEALED_REF_AND_WATERMARK', JSON.stringify(ref) === JSON.stringify(input.transcript_artifact_ref) &&
    snapshot.event_sequence === input.snapshot_event_sequence && snapshot.has_earlier_messages === true);
  check('NATIVE_LAST_200_IDENTITIES', snapshot.messages?.length === 200 &&
    snapshot.messages[0]?.message_id === input.first_visible_message_id &&
    snapshot.messages[199]?.message_id === input.last_message_id);
  fs.writeFileSync(path.join(out, 'native-wire-summary.json'), JSON.stringify({
    context: wire.context, project_id: snapshot.project_id, session_id: snapshot.session_id, goal_id: snapshot.goal_id,
    revision: snapshot.revision, event_sequence: snapshot.event_sequence,
    visible_count: snapshot.messages?.length, first_visible_message_id: snapshot.messages?.[0]?.message_id,
    last_visible_message_id: snapshot.messages?.[199]?.message_id, transcript_artifact_ref: ref,
  }, null, 2) + '\n');
  await screenshot('01-latest-200');
  const open = page.getByRole('button', { name: '读取完整会话记录', exact: true });
  await open.waitFor();
  await open.click();
  const preview = page.locator('.artifact-preview');
  await preview.waitFor();
  check('BOUND_ARTIFACT_METADATA_VISIBLE', (await preview.textContent()).includes(ref.content_hash));
  await screenshot('02-sealed-ref');
  await preview.getByRole('button', { name: '受控预览', exact: true }).click();
  await preview.locator('.preview-text').waitFor();
  const previewText = await preview.locator('.preview-text').textContent();
  check('CONTROLLED_PREVIEW_SHOWS_SEED_1', previewText.includes(input.first_message_id) && previewText.includes('u001'));
  check('CONTROLLED_PREVIEW_SHOWS_FINAL', previewText.includes(input.last_message_id) && previewText.includes('transcript-final:'));
  await screenshot('03-full-preview');
  const raw = await page.evaluate(async ({ project, id }) => {
    const response = await fetch(`/v1/projects/${encodeURIComponent(project)}/artifacts/${encodeURIComponent(id)}/content`,
      { headers: { Accept: 'application/json' }, cache: 'no-store' });
    return { status: response.status, content_type: response.headers.get('content-type'), text: await response.text() };
  }, { project: input.project_id, id: ref.id });
  check('ACTUAL_ARTIFACT_CONTENT_200', raw.status === 200 && raw.content_type?.includes('application/json'));
  const bytes = Buffer.from(raw.text, 'utf8');
  check('ACTUAL_ARTIFACT_SHA256', hash(bytes) === ref.content_hash);
  fs.writeFileSync(path.join(out, 'full-transcript.raw.json'), raw.text);
  const full = JSON.parse(raw.text);
  const messages = full.messages || [], sequence = full.message_sequences || [];
  const final = messages[200];
  const finalContent = (final?.parts || []).map(part => part.text).join('');
  check('FULL_201_ORIGINAL_MESSAGES', messages.length === 201 && sequence.length === 201 &&
    messages[0]?.message_id === input.first_message_id && messages[0]?.parts?.[0]?.text === 'u001' &&
    final?.message_id === input.last_message_id && hash(Buffer.from(finalContent, 'utf8')) === input.last_text_hash);
  check('FULL_SCOPE_AND_MESSAGE_WATERMARK', full.schema === 'researchos.session-transcript.v1' &&
    full.origin === 'SESSION_MESSAGE_JOURNAL' && full.project_id === input.project_id &&
    full.session_id === input.session_id && full.through_sequence === input.transcript_through_sequence &&
    sequence[200]?.end_sequence === full.through_sequence && full.through_sequence <= snapshot.event_sequence);
  const after = await page.evaluate(async () => (await window.researchos.v2['session.get']({})).result);
  check('RENDERER_READS_NO_NEW_EVENT', after?.session_id === input.session_id &&
    after?.event_sequence === snapshot.event_sequence &&
    JSON.stringify(after.transcript_artifact_ref) === JSON.stringify(ref));
  check('NO_RENDERER_ERRORS', report.renderer_errors.length === 0, report.renderer_errors);
  report.artifact = { ref, byte_size: bytes.length, message_count: messages.length,
    through_sequence: full.through_sequence, observation_scope: full.observation_scope,
    measurement_basis: full.measurement_basis };
  report.status = 'PASS';
}

main().catch(async error => {
  report.status = 'FAIL'; report.error = String(error.stack || error);
  if (page && !page.isClosed()) { try { await screenshot('failure'); } catch {} }
}).finally(async () => {
  if (app) await app.close();
  report.finished_at = new Date().toISOString();
  fs.writeFileSync(path.join(out, 'electron-transcript.json'), JSON.stringify(report, null, 2) + '\n');
  process.exitCode = report.status === 'PASS' ? 0 : 1;
});
