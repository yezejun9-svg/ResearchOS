import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';
const source=fs.readFileSync(new URL('./source/real-electron-flow.mjs',import.meta.url),'utf8');
const start=source.indexOf("    const nameOptions = page.locator('details.project-name-option');"),end=source.indexOf('    const helperOutcome = ',start);assert(start>0&&end>start);
const fragment=source.slice(start,end);const requireThat=(value,reason)=>{if(!value)throw Error(reason)};
const results=[];
async function call(options={}){
 const actions=[];let expanded=false;
 const page={locator(selector){assert.equal(selector,'details.project-name-option');return{count:async()=>options.count??1,locator(child){assert.equal(child,'summary');return{textContent:async()=>options.summary??'自定义项目名称',click:async()=>{expanded=true;actions.push('expanded')}}}}},getByLabel(name,opts){assert.equal(name,'显示名称');assert.equal(opts.exact,true);return{fill:async text=>{assert(expanded);assert.equal(text,'owned');actions.push('filled')}}},getByRole(role,opts){assert.equal(role,'button');assert.equal(opts.name,'选择目录');assert.equal(opts.exact,true);return{click:async()=>actions.push('choose')}}};
 const context=vm.createContext({page,scope:{project_display_name:'owned'},requireThat,bounded:f=>f(),guard(){}});
 try{await vm.runInContext('(async()=>{'+fragment+'})()',context);return{actions}}catch(error){return{actions,error:error.message}}
}
const good=await call();assert.deepEqual(good.actions,['expanded','filled','choose']);assert.equal(good.error,undefined);results.push({name:'real-fragment-expands-before-fill-and-one-choose',status:'PASS'});
for(const count of [0,2]){const value=await call({count});assert.equal(value.error,'EXACT_UI8_PROJECT_NAME_DETAILS_REQUIRED');assert.deepEqual(value.actions,[]);results.push({name:'count-'+count+'-no-action',status:'PASS'})}
const changed=await call({summary:'changed'});assert.equal(changed.error,'UI8_PROJECT_NAME_SUMMARY_CHANGED');assert.deepEqual(changed.actions,[]);results.push({name:'changed-summary-no-action',status:'PASS'});
const a=source.indexOf('const UI8_SELECTOR_SOURCE = {'),b=source.indexOf('};',a)+2;const ga=source.indexOf('  for (const [name, expected] of Object.entries(UI8_SELECTOR_SOURCE)) {'),gb=source.indexOf('  }\n',ga)+4;
const guard=source.slice(a,b)+'\n'+source.slice(ga,gb);
const rows=[{path:'apps/web/src/workbench.jsx',sha256:'e0f4c6db45757b0f506b950fb5eb004de7358f1667cbaf876ab5addee7eadd19'},{path:'apps/web/src/screens.jsx',sha256:'d7405a7bf396b97907dca9ac4bf9182295fba5251b9766e276a67f9ef6b573be'}];
for(const [name,pins,passes] of [['exact-source',rows,true],['missing-source',rows.slice(0,1),false],['wrong-source',rows.map(row=>({...row,sha256:'0'.repeat(64)})),false]]){const execute=()=>vm.runInNewContext(guard,{scope:{source:{pins}},requireThat});if(passes)execute();else assert.throws(execute,/EXACT_UI8_SELECTOR_SOURCE_PIN_REQUIRED/);results.push({name,status:'PASS'})}
assert(source.includes("const open = page.getByRole('button', { name: '打开工作台', exact: true });"));
assert(!/项目显示名称|选择本地项目目录|配置模型并打开工作台/.test(source));results.push({name:'real-open-locator-no-obsolete-fallback',status:'PASS'});
console.log(JSON.stringify({status:'INDEPENDENT_UI8_ENTRY_FRAGMENT_AND_PIN_GUARD_PASS',passed:results.length,cases:results,SDK:0,GUI:0,Native:0,model:0,formal_increment:0}));
