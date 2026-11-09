const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const root = 'D:\\作品集\\ResearchOS\\research-os';
const css = path.join(root, '.local', 'worktrees', 'product-v1-mobile-scroll-region-20261105', 'apps', 'web', 'src', 'workbench.css');
const mainCss = path.join(root, 'apps', 'web', 'src', 'workbench.css');
const out = __dirname;
const baselinePin = '5ef1a169db8c193f77e0410bc9e4ed960ae66752f1bed1387bd2097640900f02';
const rev1Pin = '89d0bcd9ff46d34bc5eb6dc7103cef448727ff2c85c5a1d5ffddf71f337a49a6';
const digest = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const baseline = fs.readFileSync(mainCss);
const rev1 = fs.readFileSync(css);
if (digest(baseline) !== baselinePin || digest(rev1) !== rev1Pin) throw Error('Source pin changed');

const needle = Buffer.from('@media(max-width:767px){html:has(.workbench-route){scroll-padding-bottom:calc(64px + env(safe-area-inset-bottom) + 12px)}.workbench-route .main-area{padding:18px 16px calc(88px + env(safe-area-inset-bottom))}', 'ascii');
const rev1Rule = Buffer.from('@media(max-width:767px){.app-grid.workbench-route{height:calc(100vh - var(--header-height,56px) - 64px - env(safe-area-inset-bottom));height:calc(100dvh - var(--header-height,56px) - 64px - env(safe-area-inset-bottom));min-height:0;overflow:hidden}.workbench-route .main-area{height:100%;overflow-y:auto;overscroll-behavior-y:contain;scroll-padding-bottom:20px;padding:18px 16px 20px}body:has(.workbench-route) .bottom-nav{height:calc(64px + env(safe-area-inset-bottom));padding-bottom:env(safe-area-inset-bottom)}', 'ascii');
const rev2Rule = Buffer.from('@media(max-width:767px){#root:has(.workbench-route){display:flex;flex-direction:column;height:100vh;height:100dvh;padding-bottom:calc(64px + env(safe-area-inset-bottom));overflow:hidden}#root:has(.workbench-route)>.topbar,#root:has(.workbench-route)>.connection-banner{flex:none}.app-grid.workbench-route{flex:1 1 0%;min-height:0;overflow:hidden}.workbench-route .main-area{height:100%;overflow-y:auto;overscroll-behavior-y:contain;scroll-padding-bottom:20px;padding:18px 16px 20px}body:has(.workbench-route) .bottom-nav{height:calc(64px + env(safe-area-inset-bottom));padding-bottom:env(safe-area-inset-bottom)}', 'ascii');
const baseAt = baseline.indexOf(needle);
const rev1At = rev1.indexOf(rev1Rule);
if (baseAt < 0 || rev1At < 0 || baseline.indexOf(needle, baseAt + 1) >= 0 || rev1.indexOf(rev1Rule, rev1At + 1) >= 0) throw Error('Anchor mismatch');
const expectedRev1 = Buffer.concat([baseline.subarray(0, baseAt), rev1Rule, baseline.subarray(baseAt + needle.length)]);
if (!expectedRev1.equals(rev1)) throw Error('Rev1 includes unleased changes');
const rev2 = Buffer.concat([baseline.subarray(0, baseAt), rev2Rule, baseline.subarray(baseAt + needle.length)]);
const inverse = Buffer.concat([rev2.subarray(0, baseAt), needle, rev2.subarray(baseAt + rev2Rule.length)]);
if (!inverse.equals(baseline) || !Buffer.from(rev2.toString('utf8'), 'utf8').equals(rev2)) throw Error('Inverse or UTF-8 failure');
fs.writeFileSync(css, rev2);
if (!fs.readFileSync(css).equals(rev2)) throw Error('CSS write readback differs');

const before = baseline.toString('utf8').split('\n');
const after = rev2.toString('utf8').split('\n');
const line = baseline.subarray(0, baseAt).toString('utf8').split('\n').length;
const header = '--- a/apps/web/src/workbench.css\n+++ b/apps/web/src/workbench.css\n@@ -' + line + ',1 +' + line + ',1 @@\n';
fs.writeFileSync(path.join(out, 'forward.patch'), header + '-' + before[line - 1] + '\n+' + after[line - 1] + '\n', 'utf8');
fs.writeFileSync(path.join(out, 'inverse.patch'), header + '-' + after[line - 1] + '\n+' + before[line - 1] + '\n', 'utf8');
const receipt = {
  scope_id: 'PRODUCT_V1_MOBILE_SCROLL_REGION', revision: 2,
  source_path: 'apps/web/src/workbench.css',
  baseline_sha256: baselinePin, rev1_sha256: rev1Pin, updated_sha256: digest(rev2),
  baseline_bytes: baseline.length, updated_bytes: rev2.length,
  exact_single_replacement: true, inverse_restores_baseline: true, utf8_valid: true,
  forward_patch: 'forward.patch', inverse_patch: 'inverse.patch',
  change: 'Flex column route shell subtracts actual header and optional banner heights before main scrollport.',
  verification_boundary: 'Static source checks only; Root owns full build and browser observations.'
};
fs.writeFileSync(path.join(out, 'receipt.json'), JSON.stringify(receipt, null, 2) + '\n', 'utf8');
console.log(JSON.stringify(receipt));
