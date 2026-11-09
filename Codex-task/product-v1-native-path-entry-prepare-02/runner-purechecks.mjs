import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const source=fs.readFileSync(new URL('./real-electron-flow.mjs',import.meta.url),'utf8');
function extract(name) {
  const start=source.indexOf('function '+name+'(');
  assert(start>=0);
  const end=source.indexOf('\nfunction ',start+1);
  return source.slice(start,end);
}
const context=vm.createContext({Buffer,HASH:/^[a-f0-9]{64}$/,
  requireThat:(condition,code)=>{if(!condition)throw new Error(code);}});
for(const name of ['requirePathEntryScope','parseNativeReply','verifyProjectBinding']) vm.runInContext(extract(name),context);
const passed=[];
const check=(name,fn)=>{fn();passed.push(name);};
const fail=(name,fn)=>check(name,()=>assert.throws(fn));
const fixture='C:\\owned\\workspace',invalid='C:\\owned\\invalid-nonexistent-NONCE';
const core={pid:42};
const reply={schema:'researchos.owned-native-path-entry/1',status:'VALID_SHELL_OK_CLOSED_REQUIRES_MAIN_BINDING',
  clicked_ok:true,valid_ok_attempted:true,invalid_ok_attempted:true,invalid_kept_chooser_open:true,outcome_uncertain:false,
  input_is_authorization:false,actual_task_submissions:0,model_outcome:'NOT_RUN_ZERO_BUDGET',
  authorization_state:'SHELL_CONFIRM_OBSERVED_MAIN_BINDING_NOT_YET_VERIFIED',dialog_hwnd:7,
  invalid_input:{path:invalid,dialog_hwnd:7,input_is_authorization:false},
  valid_input:{path:fixture,dialog_hwnd:7,input_is_authorization:false},
  invalid_warning:{observed:true,owner_pid:42,owner:7},
  history:[{event:'INVALID_DISMISSED_SAME_CHOOSER_RETAINED'},{event:'VALID_SHELL_DIALOG_CLOSED'}]};
const chosen=x=>({exit:0,stdout:JSON.stringify(x)});
check('complete_invalid_valid_sequence',()=>context.parseNativeReply(chosen(reply),core,fixture,invalid));
fail('uncertain_native_outcome',()=>context.parseNativeReply(chosen({...reply,outcome_uncertain:true}),core,fixture,invalid));
fail('foreign_warning_owner',()=>context.parseNativeReply(chosen({...reply,invalid_warning:{...reply.invalid_warning,owner:8}}),core,fixture,invalid));
fail('missing_warning_retention',()=>context.parseNativeReply(chosen({...reply,invalid_kept_chooser_open:false}),core,fixture,invalid));
const ctx={project_id:'project-real',session_id:null};
const binding={status:'ACTIVE',project_id:ctx.project_id,authorized_workspace_ref:'workspace-real',display_path:fixture};
const listed={ok:true,completed:true,result:{items:[binding]}};
check('public_main_active_binding_exact',()=>context.verifyProjectBinding(ctx,listed,fixture,fixture));
fail('displayed_path_mismatch',()=>context.verifyProjectBinding(ctx,listed,'C:\\other',fixture));
fail('foreign_project_binding',()=>context.verifyProjectBinding(ctx,{...listed,result:{items:[{...binding,project_id:'other'}]}},fixture,fixture));
fail('optional_real_path_contradiction',()=>context.verifyProjectBinding(ctx,{...listed,result:{items:[{...binding,real_path:'C:\\other'}]}},fixture,fixture));
const pin='a'.repeat(64);
const scope={budget:{task_submissions:0,model_calls:0,automatic_retries:0,harness_id:'codex'},
  deadlines:{picker_ms:60000,flow_ms:300000,close_ms:30000},
  native_picker:{profile:'INVALID_VALID_PATH_ENTRY_ONLY',validation_warning:{caption:'ResearchOS',text:'frozen warning',source_sha256:pin}},
  source:{pins:[{path:'internal/host/native_folder_windows.go',sha256:pin}]}};
check('zero_budget_frozen_source_bound_scope',()=>context.requirePathEntryScope(scope));
fail('template_null_warning_pin_fails_closed',()=>context.requirePathEntryScope({...scope,native_picker:{...scope.native_picker,validation_warning:{...scope.native_picker.validation_warning,source_sha256:null}}}));
fail('positive_model_budget_rejected',()=>context.requirePathEntryScope({...scope,budget:{...scope.budget,model_calls:1}}));
fail('positive_task_budget_rejected',()=>context.requirePathEntryScope({...scope,budget:{...scope.budget,task_submissions:1}}));
fail('picker_deadline_must_fit_flow',()=>context.requirePathEntryScope({...scope,deadlines:{...scope.deadlines,flow_ms:90000}}));
fail('source_warning_pin_mismatch',()=>context.requirePathEntryScope({...scope,source:{pins:[{path:'internal/host/native_folder_windows.go',sha256:'b'.repeat(64)}]}}));
assert(!source.includes('window.researchos.harness.'));
assert(!source.includes('submit.click'));
console.log(JSON.stringify({schema:'researchos.native-path-entry-runner-pure/1',pure_cases:passed,
  source_functions_extracted_only:true,runner_import:0,run_function:0,app:0,cli:0,task:0,model:0},null,2));
