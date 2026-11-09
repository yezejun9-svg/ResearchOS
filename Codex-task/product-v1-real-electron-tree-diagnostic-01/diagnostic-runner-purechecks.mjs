import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const source=fs.readFileSync(new URL('./real-electron-flow.mjs',import.meta.url),'utf8');
const start=source.indexOf('function requireDiagnosticScope('), end=source.indexOf('function inventory(',start);
const context=vm.createContext({Buffer,requireThat:(condition,code)=>{if(!condition)throw new Error(code);},safeText:value=>String(value).slice(0,16384)});
vm.runInContext(source.slice(start,end)+'\nthis.fns={requireDiagnosticScope,parseDiagnosticReply,sanitizeDiagnosticScalars}',context);
const {requireDiagnosticScope,parseDiagnosticReply,sanitizeDiagnosticScalars}=context.fns;
let passed=0;
const scope={native_picker:{diagnostic_only:true},budget:{task_submissions:0,automatic_retries:0,harness_id:'codex'}};
requireDiagnosticScope(scope); passed++;
for(const flag of [false,null,'true',undefined]) {
  assert.throws(()=>requireDiagnosticScope({...scope,native_picker:{diagnostic_only:flag}})); passed++;
}
assert.throws(()=>requireDiagnosticScope({...scope,budget:{...scope.budget,task_submissions:1}}));passed++;
const core={pid:123}, wrap=count=>({exit:2,stdout:JSON.stringify({
  schema:'researchos.owned-native-folder-diagnostic/1',clicked_ok:false,ok_attempted:false,
  reason:'DIAGNOSTIC_ONLY_TREE_SNAPSHOT_COMPLETE_NO_OK',cleanup:{status:'OWNED_IDCANCEL_CLICKED',hwnd:'456'},
  authorization_state:'NO_OK_CLICKED_NO_WORKSPACE_AUTHORIZATION_REQUESTED_BY_RUNNER',
  diagnostic:{schema:'researchos.owned-dialog-tree-metadata/1',diagnostic_only:true,no_ok:true,
    no_workspace_authorization:true,no_treeitem_navigation:true,dialog_owner_pid:123,dialog_hwnd:'456',
    tree_count:count,tree_limit:16,captured_count:Math.min(count,16),tree_truncated:count>16,
    trees:Array.from({length:Math.min(count,16)},(_,index)=>({index,name:'quoted "metadata"'})),
    win32_children_when_zero:count===0?{limit:32,text_or_items_read:false,controls:[]}:null}
})});
for(const count of [0,1,2,20]) {assert.equal(parseDiagnosticReply(wrap(count),core).diagnostic.tree_count,count);passed++;}
for(const modify of [
  reply=>{reply.clicked_ok=true;}, reply=>{reply.ok_attempted=true;},
  reply=>{reply.cleanup.status='OWNERSHIP_UNCONFIRMED_NO_CLICK';},
  reply=>{reply.cleanup.hwnd='other';},reply=>{reply.diagnostic.dialog_owner_pid=999;}
]) {
  const entry=wrap(2), body=JSON.parse(entry.stdout);modify(body);entry.stdout=JSON.stringify(body);
  assert.throws(()=>parseDiagnosticReply(entry,core));passed++;
}
const large=wrap(16), body=JSON.parse(large.stdout);
for(const tree of body.diagnostic.trees) tree.property_errors=Array.from({length:12},()=>({property:'field',reason:'x'.repeat(96)}));
large.stdout=JSON.stringify(body);assert(Buffer.byteLength(large.stdout)>16384);
const parsed=parseDiagnosticReply(large,core);assert.equal(JSON.parse(JSON.stringify(sanitizeDiagnosticScalars(parsed))).diagnostic.trees.length,16);passed++;
assert.throws(()=>parseDiagnosticReply({exit:2,stdout:'x'.repeat(65537)},core));passed++;
assert(!source.includes('window.researchos.harness')&&!source.includes('submit.click(')&&!source.includes('getByLabel(\'Codex'));passed++;
assert(source.includes("state.transport_routes = { observation: 'NO_HARNESS_ROUTES_DIAGNOSTIC_ONLY', expected: [] }"));passed++;
console.log(JSON.stringify({status:'DIAGNOSTIC_RUNNER_PURE_PASS',passed,runner:0,sdk:0,gui:0,native:0,model:0}));
