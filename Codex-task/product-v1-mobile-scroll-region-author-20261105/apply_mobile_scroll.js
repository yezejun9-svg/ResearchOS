const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const root = 'D:\\作品集\\ResearchOS\\research-os';
const css = path.join(root, '.local', 'worktrees', 'product-v1-mobile-scroll-region-20261105', 'apps', 'web', 'src', 'workbench.css');
const out = __dirname;
const expected = '5ef1a169db8c193f77e0410bc9e4ed960ae66752f1bed1387bd2097640900f02';
const digest = bytes => crypto.createHash('sha256').update(bytes).digest('hex');

const old = fs.readFileSync(css);
if (digest(old) !== expected) throw Error('CSS lease baseline changed');
const needle = Buffer.from('@media(max-width:767px){html:has(.workbench-route){scroll-padding-bottom:calc(64px + env(safe-area-inset-bottom) + 12px)}.workbench-route .main-area{padding:18px 16px calc(88px + env(safe-area-inset-bottom))}', 'ascii');
const replacement = Buffer.from('@media(max-width:767px){.app-grid.workbench-route{height:calc(100vh - var(--header-height,56px) - 64px - env(safe-area-inset-bottom));height:calc(100dvh - var(--header-height,56px) - 64px - env(safe-area-inset-bottom));min-height:0;overflow:hidden}.workbench-route .main-area{height:100%;overflow-y:auto;overscroll-behavior-y:contain;scroll-padding-bottom:20px;padding:18px 16px 20px}body:has(.workbench-route) .bottom-nav{height:calc(64px + env(safe-area-inset-bottom));padding-bottom:env(safe-area-inset-bottom)}', 'ascii');
const at = old.indexOf(needle);
if (at < 0 || old.indexOf(needle, at + 1) !== -1) throw Error('CSS edit anchor is not unique');
const next = Buffer.concat([old.subarray(0, at), replacement, old.subarray(at + needle.length)]);
const backAt = next.indexOf(replacement);
const inverse = Buffer.concat([next.subarray(0, backAt), needle, next.subarray(backAt + replacement.length)]);
if (!inverse.equals(old)) throw Error('Inverse does not restore baseline');
if (Buffer.from(next.toString('utf8'), 'utf8').compare(next) !== 0) throw Error('UTF-8 validation failed');
fs.writeFileSync(css, next);
if (!fs.readFileSync(css).equals(next)) throw Error('CSS write readback differs');

const before = old.toString('utf8').split('\n');
const after = next.toString('utf8').split('\n');
const line = old.subarray(0, at).toString('utf8').split('\n').length;
if (before.length !== after.length || before[line - 1] === after[line - 1]) throw Error('Unexpected line diff');
const header = '--- a/apps/web/src/workbench.css\n+++ b/apps/web/src/workbench.css\n@@ -' + line + ',1 +' + line + ',1 @@\n';
fs.writeFileSync(path.join(out, 'forward.patch'), header + '-' + before[line - 1] + '\n+' + after[line - 1] + '\n', 'utf8');
fs.writeFileSync(path.join(out, 'inverse.patch'), header + '-' + after[line - 1] + '\n+' + before[line - 1] + '\n', 'utf8');
const receipt = {
  scope_id: 'PRODUCT_V1_MOBILE_SCROLL_REGION',
  source_path: 'apps/web/src/workbench.css',
  baseline_sha256: expected,
  updated_sha256: digest(next),
  baseline_bytes: old.length,
  updated_bytes: next.length,
  only_exact_anchor_replaced: true,
  inverse_restores_baseline: true,
  utf8_valid: true,
  forward_patch: 'forward.patch',
  inverse_patch: 'inverse.patch',
  verification_boundary: 'Static byte and CSS checks only; Root owns full build and browser observations.'
};
fs.writeFileSync(path.join(out, 'receipt.json'), JSON.stringify(receipt, null, 2) + '\n', 'utf8');
console.log(JSON.stringify(receipt));
