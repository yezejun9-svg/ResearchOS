// Execute only the actual small UI-entry fragment against a controlled page
// object. No SDK import, Electron, window, IPC, Host or model exists here.
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const source = fs.readFileSync(new URL('./real-electron-flow.mjs', import.meta.url), 'utf8');
const start = source.indexOf("    const nameOptions = page.locator('details.project-name-option');");
const end = source.indexOf('    const helperOutcome = ', start);
assert(start > 0 && end > start);
const fragment = source.slice(start, end);
assert(!/项目显示名称|选择本地项目目录|配置模型并打开工作台/.test(source));
assert(source.includes("const open = page.getByRole('button', { name: '打开工作台', exact: true })"));
const invoke = (options = {}) => {
  const actions = [], state = { opened: false };
  const page = {
    locator(selector) {
      assert.equal(selector, 'details.project-name-option');
      return {
        count: async () => options.count ?? 1,
        locator(child) {
          assert.equal(child, 'summary');
          return { textContent: async () => options.summary ?? '自定义项目名称',
            click: async () => { actions.push('open-name-details'); state.opened = true; } };
        },
      };
    },
    getByLabel(label, opts) {
      assert.equal(label, '显示名称'); assert.equal(opts.exact, true);
      return { fill: async text => {
        assert(state.opened, 'must actually open details before fill');
        assert.equal(text, 'owned fixture');
        actions.push('fill-display-name');
      } };
    },
    getByRole(role, opts) {
      assert.equal(role, 'button'); assert.equal(opts.name, '选择目录'); assert.equal(opts.exact, true);
      return { click: async () => { actions.push('choose-directory'); } };
    },
  };
  const requireThat = (condition, reason) => { if (!condition) throw new Error(reason); };
  const context = vm.createContext({ page, scope: { project_display_name: 'owned fixture' },
    bounded: action => action(), guard() {}, requireThat });
  return { actions, completed: new vm.Script('(async () => {\n' + fragment + '\n})()').runInContext(context) };
};
let passed = 2;
const ok = invoke(); await ok.completed;
assert.deepEqual(ok.actions, ['open-name-details', 'fill-display-name', 'choose-directory']); passed++;
for (const count of [0, 2]) {
  const bad = invoke({ count });
  await assert.rejects(bad.completed, /EXACT_UI8_PROJECT_NAME_DETAILS_REQUIRED/);
  assert.deepEqual(bad.actions, []); passed++;
}
const changed = invoke({ summary: 'changed UI' });
await assert.rejects(changed.completed, /UI8_PROJECT_NAME_SUMMARY_CHANGED/);
assert.deepEqual(changed.actions, []); passed++;
console.log(JSON.stringify({ status: 'UI8_SELECTOR_FRAGMENT_PURE_PASS', passed,
  real_runner: 0, sdk: 0, gui: 0, native: 0, model: 0 }));
