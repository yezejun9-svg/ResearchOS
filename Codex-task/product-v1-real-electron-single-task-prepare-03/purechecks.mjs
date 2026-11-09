// Preparation-only counterexamples. Reads source text; never imports the runner.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const runner = fs.readFileSync(path.join(here, 'real-electron-flow.mjs'), 'utf8');
const helper = fs.readFileSync(path.join(here, 'choose-owned-folder.ps1'), 'utf8');
const scope = JSON.parse(fs.readFileSync(path.join(here, 'scope.template.json'), 'utf8'));
const assert = (value, label) => { if (!value) throw new Error(label); };
const functionBody = name => {
  const start = runner.indexOf(`function ${name}(`);
  assert(start >= 0, `MISSING_${name}`);
  const open = runner.indexOf('{', start);
  let depth = 0;
  for (let index = open; index < runner.length; index++) {
    if (runner[index] === '{') depth++;
    if (runner[index] === '}' && --depth === 0) return runner.slice(start, index + 1);
  }
  throw new Error(`UNCLOSED_${name}`);
};
const context = vm.createContext({ requireThat: (value, code) => assert(value, code) });
vm.runInContext(`${functionBody('requireChatGPTAuthentication')}\n${functionBody('verifyProjectBinding')}`, context);
const succeeds = (work, label) => { work(); return label; };
const fails = (work, label) => { try { work(); } catch { return label; } throw new Error(`ACCEPTED_${label}`); };
const tests = [];
tests.push(succeeds(() => context.requireChatGPTAuthentication({authentication:{state:'LOGGED_IN',kind:'chatgpt'}}), 'actual-chatgpt'));
for (const [state, kind] of [['LOGGED_IN','api_key'],['LOGGED_OUT','chatgpt'],['UNPROBED','chatgpt'],['ERROR','chatgpt']]) {
  tests.push(fails(() => context.requireChatGPTAuthentication({authentication:{state,kind}}), `reject-${state}-${kind}`));
}
const fixture = 'C:\\owned\\fresh\\workspace';
const project = {project_id:'project-1',session_id:null};
const row = {status:'ACTIVE',project_id:'project-1',authorized_workspace_ref:'workspace-1',display_path:fixture};
const listed = {ok:true,completed:true,result:{items:[row]}};
tests.push(succeeds(() => context.verifyProjectBinding(project, listed, fixture, fixture), 'one-active-exact-path'));
tests.push(fails(() => context.verifyProjectBinding(project, {ok:true,completed:true,result:{items:[row,row]}}, fixture, fixture), 'reject-two-workspaces'));
tests.push(fails(() => context.verifyProjectBinding(project, {ok:true,completed:true,result:{items:[{...row,status:'PENDING'}]}}, fixture, fixture), 'reject-pending'));
tests.push(fails(() => context.verifyProjectBinding(project, {ok:true,completed:true,result:{items:[{...row,real_path:'C:\\other'}]}}, fixture, fixture), 'reject-canonical-mismatch'));
tests.push(fails(() => context.verifyProjectBinding(project, listed, 'C:\\other', fixture), 'reject-ui-path-mismatch'));
assert(scope.status !== 'ROOT_APPROVED_REAL_RUN' && scope.harness.runner_sha256 === null &&
  scope.harness.folder_helper_sha256 === null && scope.root_supervision.controller_sha256 === null &&
  scope.prerequisite.native_zero_flow.root_result_sha256 === null, 'TEMPLATE_MUST_FAIL_CLOSED');
const executableLines = runner.replace(/^\s*\/\/.*$/gm, '');
assert(runner.includes('state.actual_dom_submit_attempts = 1') && runner.includes('UNKNOWN_NO_AUTOMATIC_RESUBMIT') &&
  !executableLines.includes('bridge.submit(') && !executableLines.includes('taskkill') &&
  !executableLines.includes('process.kill('), 'ONE_SUBMIT_NO_FORCE_OR_BRIDGE_FALLBACK');
assert(helper.includes('Assert-MessageDeadline ([DateTime]::UtcNow) $actionDeadline') &&
  helper.includes('Assert-MessageDeadline ([DateTime]::UtcNow) $messageDeadline') &&
  helper.includes('native-helper-history.ndjson'), 'NATIVE_ACTION_DEADLINE_GUARDS');
console.log(JSON.stringify({status:'PURE_CHECKS_PASS', counterexamples:tests.length, runner_imports:0, helper_invocations:0, app_launches:0, model_calls:0}));
