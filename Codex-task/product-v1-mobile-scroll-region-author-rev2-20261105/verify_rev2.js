const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const dir = __dirname;
const root = 'D:\\作品集\\ResearchOS\\research-os';
const css = path.join(root, '.local', 'worktrees', 'product-v1-mobile-scroll-region-20261105', 'apps', 'web', 'src', 'workbench.css');
const baselineCss = path.join(root, 'apps', 'web', 'src', 'workbench.css');
const digest = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const receipt = JSON.parse(fs.readFileSync(path.join(dir, 'receipt.json'), 'utf8'));
const baseline = fs.readFileSync(baselineCss);
const actual = fs.readFileSync(css);
const needle = Buffer.from('@media(max-width:767px){html:has(.workbench-route){scroll-padding-bottom:calc(64px + env(safe-area-inset-bottom) + 12px)}.workbench-route .main-area{padding:18px 16px calc(88px + env(safe-area-inset-bottom))}', 'ascii');
const rule = Buffer.from('@media(max-width:767px){#root:has(.workbench-route){display:flex;flex-direction:column;height:100vh;height:100dvh;padding-bottom:calc(64px + env(safe-area-inset-bottom));overflow:hidden}#root:has(.workbench-route)>.topbar,#root:has(.workbench-route)>.connection-banner{flex:none}.app-grid.workbench-route{flex:1 1 0%;min-height:0;overflow:hidden}.workbench-route .main-area{height:100%;overflow-y:auto;overscroll-behavior-y:contain;scroll-padding-bottom:20px;padding:18px 16px 20px}body:has(.workbench-route) .bottom-nav{height:calc(64px + env(safe-area-inset-bottom));padding-bottom:env(safe-area-inset-bottom)}', 'ascii');
const at = baseline.indexOf(needle);
if (at < 0 || baseline.indexOf(needle, at + 1) >= 0) throw Error('Baseline anchor mismatch');
const expected = Buffer.concat([baseline.subarray(0, at), rule, baseline.subarray(at + needle.length)]);
if (!actual.equals(expected)) throw Error('Diff includes nonleased bytes');
if (digest(baseline) !== receipt.baseline_sha256 || digest(actual) !== receipt.updated_sha256) throw Error('Source hash mismatch');
const postcss = require(path.join(root, 'apps', 'web', 'node_modules', 'postcss'));
const parsed = postcss.parse(actual.toString('utf8'), { from: css });
const result = {
  source_pin: digest(actual), baseline_pin: digest(baseline),
  exact_single_replacement: true,
  inverse_byte_match: Buffer.concat([actual.subarray(0, at), needle, actual.subarray(at + rule.length)]).equals(baseline),
  css_syntax: 'postcss.parse passed', parsed_top_level_nodes: parsed.nodes.length,
  source_files_changed_in_scope: ['apps/web/src/workbench.css'],
  banner_layout_basis: 'AppShell header and 0-2 connection-banner nodes are direct root siblings before app-grid; flex allocates their intrinsic height.',
  runtime_tests: 'Owned by Root build10 and browser controller'
};
if (!result.inverse_byte_match) throw Error('Inverse byte check failed');
fs.writeFileSync(path.join(dir, 'diffcheck.json'), JSON.stringify(result, null, 2) + '\n', 'utf8');
const files = ['apply_rev2.js', 'verify_rev2.js', 'forward.patch', 'inverse.patch', 'receipt.json', 'diffcheck.json'];
const manifest = { scope_id: receipt.scope_id, revision: 2, source_pin: result.source_pin, files: Object.fromEntries(files.map(name => [name, digest(fs.readFileSync(path.join(dir, name)))])) };
fs.writeFileSync(path.join(dir, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n', 'utf8');
console.log(JSON.stringify(result));
