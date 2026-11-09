import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
const source=fs.readFileSync(new URL('./real-electron-flow.mjs',import.meta.url),'utf8');
function extract(name) {
  const start=source.indexOf('function '+name+'(');assert(start>=0);
  const end=source.indexOf('\nfunction ',start+1);return source.slice(start,end);
}
const context=vm.createContext({Buffer,requireThat:(condition,code)=>{if(!condition)throw new Error(code);}});
for(const name of ['decodeNativeReply','observeNativeReply']) vm.runInContext(extract(name),context);
const saved=new URL('../product-v1-native-path-entry-中文-run-01/receipts/native-folder-automation.json',import.meta.url);
const bytes=fs.readFileSync(saved),recorded=JSON.parse(bytes.toString('utf8'));
assert.equal(recorded.exit,2);
const passed=[];
const check=(name,fn)=>{fn();passed.push(name);};
const fail=(name,fn)=>check(name,()=>assert.throws(fn));
const decoded=context.decodeNativeReply(recorded);
check('actual01_complete_exit2_json_remains_blocked',()=>{
  assert.equal(decoded.status,'BLOCKED');assert.equal(decoded.reason,'BUTTON_DIALOG_NOT_FOREGROUND_NO_CLICK');
  assert.equal(decoded.phase,'INVALID_PATH');
});
check('actual01_known_no_ok_preserved_without_pending_unknown',()=>{
  const observation=context.observeNativeReply(decoded);
  assert.equal(observation.authorization_observation,'NOT_ESTABLISHED_NO_OK_ATTEMPT_RECORDED');
  assert.equal(observation.invalid_ok_attempted,false);assert.equal(observation.valid_ok_attempted,false);
  assert.equal(observation.outcome_uncertain,false);assert.equal(observation.cleanup.attempted,true);
  assert.equal(observation.cleanup.status,'OWNERSHIP_OR_CANCEL_UNKNOWN_ROOT_JOB_REQUIRED');
});
const chosen=reply=>({exit:2,stdout:JSON.stringify(reply)});
fail('malformed_json_unknown',()=>context.decodeNativeReply({exit:2,stdout:'{'}));
fail('oversize_text_unknown',()=>context.decodeNativeReply({exit:2,stdout:' '.repeat(65537)}));
fail('foreign_schema_unknown',()=>context.decodeNativeReply(chosen({...decoded,schema:'other'})));
fail('string_boolean_unknown',()=>context.decodeNativeReply(chosen({...decoded,invalid_ok_attempted:'false'})));
fail('unknown_phase_unknown',()=>context.decodeNativeReply(chosen({...decoded,phase:'OTHER'})));
fail('missing_cleanup_unknown',()=>context.decodeNativeReply(chosen({...decoded,cleanup:null})));
fail('exit_status_mismatch_unknown',()=>context.decodeNativeReply({exit:0,stdout:recorded.stdout}));
fail('contradictory_valid_attempt_phase_unknown',()=>context.decodeNativeReply(chosen({...decoded,valid_ok_attempted:true})));
check('uncertain_input_does_not_become_known_authorization',()=>{
  const reply=context.decodeNativeReply(chosen({...decoded,outcome_uncertain:true,authorization_state:'UNKNOWN_NO_AUTHORIZATION_INFERRED_NO_RETRY'}));
  assert.equal(context.observeNativeReply(reply).authorization_observation,'UNKNOWN_NO_AUTHORIZATION_INFERRED_NO_RETRY');
});
assert.equal(crypto.createHash('sha256').update(fs.readFileSync(saved)).digest('hex'),crypto.createHash('sha256').update(bytes).digest('hex'));
console.log(JSON.stringify({schema:'researchos.native-path-entry-parser03-pure/1',pure_cases:passed,
  actual01_record_read_only:true,actual01_record_sha256:crypto.createHash('sha256').update(bytes).digest('hex'),
  actual01_runtime_outcome:'FAILED_UNCHANGED_NOT_RELABELED',inherited_pure_cases_not_rerun:28,
  source_functions_extracted_only:true,runner_import:0,run_function:0,app:0,cli:0,task:0,model:0},null,2));
