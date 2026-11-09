import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';
const source=fs.readFileSync(new URL('./real-electron-flow.mjs',import.meta.url),'utf8');
const a=source.indexOf('function requireDiagnosticScope('),b=source.indexOf('function inventory(',a);
const context=vm.createContext({Buffer,requireThat:(ok,reason)=>{if(!ok)throw new Error(reason);},safeText:String});
vm.runInContext(source.slice(a,b)+'\nthis.fns={requireDiagnosticScope,parseDiagnosticReply}',context);
const {requireDiagnosticScope,parseDiagnosticReply}=context.fns;
let passed=0;const scope={native_picker:{diagnostic_only:true,direct_native_tree:true},budget:{task_submissions:0,automatic_retries:0,harness_id:'codex'}};
requireDiagnosticScope(scope);passed++;
for(const value of [false,undefined,'true']) {assert.throws(()=>requireDiagnosticScope({...scope,native_picker:{...scope.native_picker,direct_native_tree:value}}));passed++;}
const body={schema:'researchos.owned-native-folder-diagnostic/1',clicked_ok:false,ok_attempted:false,reason:'DIAGNOSTIC_ONLY_TREE_SNAPSHOT_COMPLETE_NO_OK',
  cleanup:{status:'OWNED_IDCANCEL_CLICKED',hwnd:'55'},authorization_state:'NO_OK_CLICKED_NO_WORKSPACE_AUTHORIZATION_REQUESTED_BY_RUNNER',
  diagnostic:{schema:'researchos.owned-dialog-tree-metadata/1',diagnostic_only:true,no_ok:true,no_workspace_authorization:true,no_treeitem_navigation:true,
    dialog_owner_pid:42,dialog_hwnd:'55',tree_count:1,tree_limit:16,captured_count:1,tree_truncated:false,trees:[{}],
    tree_source:'VERIFIED_NATIVE_SYSTREEVIEW32_FROM_HANDLE',direct_native_tree:{native_window:{process_id:42,class_name:'SysTreeView32',visible:true,enabled:true},can_authorize_selection:false,selected:[]}}};
assert.equal(parseDiagnosticReply({exit:2,stdout:JSON.stringify(body)},{pid:42}).diagnostic.tree_count,1);passed++;
const changed=structuredClone(body);changed.clicked_ok=true;
assert.throws(()=>parseDiagnosticReply({exit:2,stdout:JSON.stringify(changed)},{pid:42}));passed++;
assert(!source.includes('window.researchos.harness')&&!source.includes('submit.click('));passed++;
console.log(JSON.stringify({status:'DIRECT_RUNNER_PURE_PASS',passed,sdk:0,gui:0,model:0}));
