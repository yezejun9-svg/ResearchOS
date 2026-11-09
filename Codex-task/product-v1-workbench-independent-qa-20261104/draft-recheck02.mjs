import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import vm from 'node:vm'
const source=fs.readFileSync(new URL('./stage02/apps/web/src/workbench.jsx',import.meta.url),'utf8')
const block=source.slice(source.indexOf('function NativeHarnessWorkbench('),source.indexOf('function NativeMuWorkbench('))
const extract=(pattern,name)=>{const match=pattern.exec(block);assert.ok(match,'Frozen actual '+name+' extracted');return match[0]}
const sendSource=extract(/async function send\(event\) \{[\s\S]*?\n  \}/,'send')
const editSource=extract(/function editDraft\(value\) \{[\s\S]*?\n  \}/,'editDraft')
const scopeSource=block.slice(block.indexOf('if (draftScope.current.projectId'),block.indexOf('  function editDraft')).trim()
const cleanupSource=extract(/\(\) => \{ stopped = true;[^\n]+ \}/,'cleanup')
const onChange=/onChange=\{(event => editDraft\(event\.target\.value\))\}/.exec(block)?.[1]
assert.ok(onChange,'Actual textarea onChange must use the revision-stamping path')
assert.match(block,/<ConversationWelcome setDraft=\{editDraft\}/,'Welcome suggestions must use same edit path')
function fixture(){
 let resolve;const pending=new Promise(r=>resolve=r);let current='submitted text',notices=[]
 const control={submit:()=>pending,dispose(){}}
 const context=vm.createContext({canSend:true,draft:'submitted text',projectId:'qa-project',workspace:'qa-workspace',
  draftVersion:{current:0},draftScope:{current:{projectId:'qa-project',workspace:'qa-workspace'}},controller:{current:control},control,
  setDraft:value=>{current=typeof value==='function'?value(current):value},setNotice:v=>notices.push(v),
  stopped:false,unsubscribe(){},clearInterval(){},timer:0,removeEventListener(){},document:{removeEventListener(){}},changed(){},tick(){},visible(){}})
 vm.runInContext(editSource,context)
 return {context,resolve,send:vm.runInContext('('+sendSource+')',context),edit:vm.runInContext('('+onChange+')',context),
  cleanup:vm.runInContext('('+cleanupSource+')',context),current:()=>current,notices:()=>notices,
  scope:(project,workspace)=>{context.projectId=project;context.workspace=workspace;vm.runInContext(scopeSource,context)}}
}
for(const back of [false,true])test('real send/onChange preserves new edit generation, edit-back='+back,async()=>{
 const f=fixture(),p=f.send({preventDefault(){}});f.edit({target:{value:'new unsent text'}});if(back)f.edit({target:{value:'submitted text'}})
 const expected=f.current();f.resolve(true);await p;assert.equal(f.current(),expected);assert.equal(f.context.draftVersion.current,back?2:1)
})
test('unchanged submitted draft is cleared after successful accepted task',async()=>{
 const f=fixture(),p=f.send({preventDefault(){}});f.resolve(true);await p;assert.equal(f.current(),'')
})
test('submission failure preserves the current draft and does not claim acceptance',async()=>{
 const f=fixture(),p=f.send({preventDefault(){}});f.edit({target:{value:'later'}});f.resolve(false);await p;assert.equal(f.current(),'later');assert.deepEqual(f.notices(),[''])
})
for(const axis of ['workspace','project'])test('actual render scope ABA invalidates old draft clear: '+axis,async()=>{
 const f=fixture(),p=f.send({preventDefault(){}})
 if(axis==='workspace'){f.scope('qa-project','other-workspace');f.scope('qa-project','qa-workspace')}
 else {f.scope('other-project','qa-workspace');f.scope('qa-project','qa-workspace')}
 f.resolve(true);await p;assert.equal(f.current(),'submitted text');assert.equal(f.context.draftVersion.current,2)
})
test('actual effect cleanup invalidates late result after unmount or Harness switch',async()=>{
 const f=fixture(),p=f.send({preventDefault(){}});f.cleanup();f.resolve(true);await p;assert.equal(f.current(),'submitted text');assert.equal(f.context.controller.current,null);assert.deepEqual(f.notices(),[''])
})
test('a different live controller prevents late result changing current draft or notice',async()=>{
 const f=fixture(),p=f.send({preventDefault(){}});f.context.controller.current={submit:async()=>false};f.resolve(true);await p
 assert.equal(f.current(),'submitted text');assert.deepEqual(f.notices(),[''])
})
test('actual editDraft supports Welcome function-updater edits without ABA loss',async()=>{
 const f=fixture(),p=f.send({preventDefault(){}});vm.runInContext("editDraft(old => old + ' suggestion')",f.context);vm.runInContext("editDraft(() => 'submitted text')",f.context)
 f.resolve(true);await p;assert.equal(f.current(),'submitted text');assert.equal(f.context.draftVersion.current,2)
})
