// Pure functions from the actual candidate runner. Do not launch the runner,
// Electron, PowerShell helper, Native CLI, or any model.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { FIXED_SOURCE, requireAdditionPins, parseNativeReply, verifyProjectBinding } from './real-electron-flow.mjs';

const here=path.dirname(fileURLToPath(import.meta.url));
const expected={
  'allow.txt':'fb5a1260681aa728b71d87fb40688512acb11cc0e215f204a34fa079acf16816',
  'write-existing.txt':'40d994eb11671f554c25dc4746e2336233e92645622e9346281bab9b6e25b916',
};

test('the fixed source has the helper and Main canonical Windows spelling',()=>{
  assert.equal(FIXED_SOURCE,path.resolve('C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-native-qualification-中文-root-01/S'));
  assert.equal(FIXED_SOURCE,path.win32.normalize(FIXED_SOURCE));
  assert.match(FIXED_SOURCE,/\\S$/);
});

function successfulHelper(validPath) {
  const dialog=222, corePID=101, invalid='C:\\owned\\invalid-nonexistent-nonce';
  return {core:{pid:corePID},invalid,chosen:{exit:0,stdout:JSON.stringify({
    schema:'researchos.owned-native-path-entry/1',phase:'VALID_PATH',status:'VALID_SHELL_OK_CLOSED_REQUIRES_MAIN_BINDING',
    authorization_state:'SHELL_CONFIRM_OBSERVED_MAIN_BINDING_NOT_YET_VERIFIED',
    cleanup:{status:'NOT_NEEDED',attempted:false},history:[{event:'INVALID_DISMISSED_SAME_CHOOSER_RETAINED'},{event:'VALID_SHELL_DIALOG_CLOSED'}],
    clicked_ok:true,invalid_ok_attempted:true,valid_ok_attempted:true,outcome_uncertain:false,
    input_is_authorization:false,actual_task_submissions:0,model_outcome:'NOT_RUN_ZERO_BUDGET',invalid_kept_chooser_open:true,
    invalid_input:{path:invalid,input_is_authorization:false,dialog_hwnd:dialog},
    valid_input:{path:validPath,input_is_authorization:false,dialog_hwnd:dialog},
    invalid_warning:{observed:true,owner_pid:corePID,owner:dialog},dialog_hwnd:dialog,
  })}};
}
test('actual Native helper predicate accepts canonical S and rejects another S',()=>{
  const yes=successfulHelper(FIXED_SOURCE);
  assert.equal(parseNativeReply(yes.chosen,yes.core,FIXED_SOURCE,yes.invalid).valid_input.path,FIXED_SOURCE);
  const no=successfulHelper(path.join(path.dirname(FIXED_SOURCE),'OTHER','S'));
  assert.throws(()=>parseNativeReply(no.chosen,no.core,FIXED_SOURCE,no.invalid),/NATIVE_PATH_EVIDENCE_REQUIRED/);
});
test('actual Main public binding predicate uses that same exact spelling',()=>{
  const context={project_id:'fresh-project-1',session_id:null};
  const binding={status:'ACTIVE',project_id:context.project_id,authorized_workspace_ref:'ref-1',display_path:FIXED_SOURCE};
  const listed={ok:true,completed:true,result:{items:[binding]}};
  assert.equal(verifyProjectBinding(context,listed,FIXED_SOURCE,FIXED_SOURCE),binding);
  assert.throws(()=>verifyProjectBinding(context,listed,FIXED_SOURCE.replaceAll('\\','/'),FIXED_SOURCE),/REAL_MAIN_ACTIVE_EXACT_FIXTURE_REQUIRED/);
});
test('missing, malformed and wrong B3 addition pins reject before any simulated launch or submit',()=>{
  let callbacks=0;
  const proceed=pins=>{const validated=requireAdditionPins({allowed_additions:pins});callbacks++;return validated;};
  for(const pins of [null,{}, {'allow.txt':null,'write-existing.txt':expected['write-existing.txt']},
    {'allow.txt':'x','write-existing.txt':expected['write-existing.txt']},
    {'allow.txt':expected['allow.txt'],'write-existing.txt':'f'.repeat(64)}]) {
    assert.throws(()=>proceed(pins),/EXACT_B3_ADDITIONS_PINS_REQUIRED/);
  }
  assert.equal(callbacks,0);
  assert.deepEqual(proceed(expected),expected);
  assert.equal(callbacks,1);
});
test('raw template remains blocked and the actual preflight guard precedes root creation and submit',()=>{
  const template=JSON.parse(fs.readFileSync(path.join(here,'scope.template.json'),'utf8'));
  assert.notEqual(template.status,'ROOT_APPROVED_REAL_RUN');
  assert.equal(template.qualification.allowed_additions['allow.txt'],null);
  const source=fs.readFileSync(path.join(here,'real-electron-flow.mjs'),'utf8');
  const guard=source.indexOf('const allowedAdditions = requireAdditionPins(scope.qualification);');
  assert.ok(guard>0 && guard<source.indexOf("activeRunEvidence.phase = 'CREATE_FRESH_RUN_ROOT'") &&
    guard<source.indexOf('_electron.launch(') && guard<source.indexOf('submit.click()'));
});
