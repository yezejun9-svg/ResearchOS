const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const dir = __dirname;
const root = 'D:\\作品集\\ResearchOS\\research-os';
const css = path.join(root, '.local', 'worktrees', 'product-v1-mobile-scroll-region-20261105', 'apps', 'web', 'src', 'workbench.css');
const mainCss = path.join(root, 'apps', 'web', 'src', 'workbench.css');
const digest = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const receipt = JSON.parse(fs.readFileSync(path.join(dir, 'receipt.json'), 'utf8'));
const next = fs.readFileSync(css);
const baseline = fs.readFileSync(mainCss);
const needle = Buffer.from('@media(max-width:767px){html:has(.workbench-route){scroll-padding-bottom:calc(64px + env(safe-area-inset-bottom) + 12px)}.workbench-route .main-area{padding:18px 16px calc(88px + env(safe-area-inset-bottom))}', 'ascii');
const replacement = Buffer.from('@media(max-width:767px){.app-grid.workbench-route{height:calc(100vh - var(--header-height,56px) - 64px - env(safe-area-inset-bottom));height:calc(100dvh - var(--header-height,56px) - 64px - env(safe-area-inset-bottom));min-height:0;overflow:hidden}.workbench-route .main-area{height:100%;overflow-y:auto;overscroll-behavior-y:contain;scroll-padding-bottom:20px;padding:18px 16px 20px}body:has(.workbench-route) .bottom-nav{height:calc(64px + env(safe-area-inset-bottom));padding-bottom:env(safe-area-inset-bottom)}', 'ascii');
const at = baseline.indexOf(needle);
if (at < 0 || baseline.indexOf(needle, at + 1) >= 0) throw Error('Baseline anchor mismatch');
const expected = Buffer.concat([baseline.subarray(0, at), replacement, baseline.subarray(at + needle.length)]);
if (!expected.equals(next)) throw Error('Diff includes nonleased bytes');
if (digest(baseline) !== receipt.baseline_sha256 || digest(next) !== receipt.updated_sha256) throw Error('Source hash mismatch');
const postcss = require(path.join(root, 'apps', 'web', 'node_modules', 'postcss'));
const parsed = postcss.parse(next.toString('utf8'), { from: css });
const result = {
  source_pin: digest(next),
  baseline_pin: digest(baseline),
  exact_single_replacement: true,
  inverse_byte_match: Buffer.concat([next.subarray(0, at), needle, next.subarray(at + replacement.length)]).equals(baseline),
  css_syntax: 'postcss.parse passed',
  parsed_top_level_nodes: parsed.nodes.length,
  source_files_changed_in_scope: ['apps/web/src/workbench.css'],
  runtime_tests: 'Owned by Root build10 and browser controller'
};
if (!result.inverse_byte_match) throw Error('Inverse byte check failed');
fs.writeFileSync(path.join(dir, 'diffcheck.json'), JSON.stringify(result, null, 2) + '\n', 'utf8');
const names = ['apply_mobile_scroll.js', 'verify_mobile_scroll.js', 'forward.patch', 'inverse.patch', 'receipt.json', 'diffcheck.json'];
const manifest = { scope_id: receipt.scope_id, source_pin: result.source_pin, files: Object.fromEntries(names.map(name => [name, digest(fs.readFileSync(path.join(dir, name)))])) };
fs.writeFileSync(path.join(dir, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n', 'utf8');
console.log(JSON.stringify(result));
