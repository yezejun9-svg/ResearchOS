// New revision-04 selector counterexamples; no runner import or Native call.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const runner = fs.readFileSync(path.join(here, 'real-electron-flow.mjs'), 'utf8');
const helper = fs.readFileSync(path.join(here, 'choose-owned-folder.ps1'), 'utf8');
const template = JSON.parse(fs.readFileSync(path.join(here, 'scope.template.json'), 'utf8'));
const assert = (ok, label) => { if (!ok) throw new Error(label); };
const start = runner.indexOf('function requireWarningDismissSelector(scope) {');
const end = runner.indexOf('function requirePathEntryScope(scope) {', start);
assert(start >= 0 && end > start, 'SELECTOR_FUNCTION_MISSING');
const box = vm.createContext({
  folded: value => path.resolve(value).toLowerCase(),
  requireThat: (ok, code) => assert(ok, code),
});
vm.runInContext(`${runner.slice(start, end)}\nthis.check=requireWarningDismissSelector`, box);
const check = selector => box.check({native_picker:{validation_warning:{dismiss_selector:selector}}});
const expected = template.native_picker.validation_warning.dismiss_selector;
check(expected);
const reject = (field, value) => {
  try { check({...expected, [field]:value}); }
  catch { return field; }
  throw new Error(`UNPINNED_SELECTOR_ACCEPTED:${field}`);
};
const cases = [
  reject('expected_control_id', 1),
  reject('expected_button_count', 2),
  reject('basis', 'GUESSED'),
  reject('message_box_result_is_control_id', true),
  reject('evidence_event_sequence', 35),
  reject('evidence_sha256', '0'.repeat(64)),
  reject('evidence_path', 'C:/other/native-folder-automation.json'),
];
assert(helper.includes('Select-UniqueWarningDismissButton') &&
  helper.includes('WARNING_DISMISS_EXPECTED_CONTROL_ID_MUST_BE_PINNED_2') &&
  helper.includes('ZERO_BUDGET_NATIVE_STAGE_ONE_TASK_GLOBAL_PROFILE') &&
  runner.includes('pin(scope.native_picker.validation_warning.dismiss_selector.evidence_path,'),
  'DUAL_SELECTOR_EVIDENCE_GATE_MISSING');
console.log(JSON.stringify({status:'SELECTOR_PURE_CHECKS_PASS',new_counterexamples:cases.length,runner_imports:0,helper_invocations:0,app_launches:0,model_calls:0}));
