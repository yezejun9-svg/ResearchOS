// New revision-03 identity counterexamples. Source extraction has no runner import.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const source = fs.readFileSync(path.join(here, 'real-electron-flow.mjs'), 'utf8');
const assert = (value, label) => { if (!value) throw new Error(label); };
const extract = name => {
  const start = source.indexOf(`function ${name}(`);
  assert(start >= 0, `MISSING_${name}`);
  const open = source.indexOf('{', start);
  let depth = 0;
  for (let index = open; index < source.length; index++) {
    if (source[index] === '{') depth++;
    else if (source[index] === '}' && --depth === 0) return source.slice(start, index + 1);
  }
  throw new Error(`UNCLOSED_${name}`);
};
const scalarHelpers = ['requestID', 'sameTaskRef', 'sameRunRef'].map(name => {
  const line = source.split('\n').find(value => value.startsWith(`const ${name} = `));
  assert(line, `MISSING_${name}`);
  return line;
}).join('\n');
const pure = ['bindRun', 'bindPending', 'bindTask', 'bindEventPage'].map(extract).join('\n');
const sandbox = vm.createContext({ requireThat: (value, code) => assert(value, code) });
vm.runInContext(`${scalarHelpers}\n${pure}\nthis.api={bindRun,bindPending,bindTask,bindEventPage}`, sandbox);
const {bindRun,bindPending,bindTask,bindEventPage} = sandbox.api;
const reject = (call, label) => { try { call(); } catch { return label; } throw new Error(`ACCEPTED_${label}`); };
const project = 'project-1', workspace = 'workspace-1', prompt = 'read fixture';
const ref = {project_id:project,task_id:'task-1'};
const runA = {run_id:'run-A',epoch:'1'}, runB = {run_id:'run-B',epoch:'2'};
const task = {request_id:'request-1',task_ref:ref,workspace_ref:workspace,prompt,harness_id:'codex',scope:'workspace-read',ephemeral:true,run:runA};
const pending = request_id => ({ok:true,data:{kind:'submit',request_id,state:'UNKNOWN',task_ref:null,workspace_ref:workspace,prompt}});
const tests = [];
const fromPending = {};
bindPending(fromPending,pending('request-1'),project,workspace,prompt);
tests.push(reject(() => bindTask(fromPending,{...task,request_id:'request-2'},project,workspace,prompt),'pending-R1-list-R2'));
assert(fromPending.request_id === 'request-1' && fromPending.task_ref == null,'PENDING_PIN_MUTATED');
const fromTask = {};
bindTask(fromTask,task,project,workspace,prompt);
tests.push(reject(() => bindPending(fromTask,pending('request-2'),project,workspace,prompt),'task-R1-pending-R2'));
assert(fromTask.request_id === 'request-1' && fromTask.task_ref.task_id === 'task-1','TASK_PIN_MUTATED');
bindPending(fromTask,{ok:true,data:null},project,workspace,prompt);
assert(fromTask.request_id === 'request-1','NULL_PENDING_CLEARED_PIN');
tests.push(reject(() => bindPending({}, {ok:true,data:{...pending('request-1').data,kind:'cancel'}},project,workspace,prompt),'cancel-journal'));
tests.push(reject(() => bindPending({}, {ok:true,data:{...pending('request-1').data,prompt:'other'}},project,workspace,prompt),'wrong-prompt-journal'));
tests.push(reject(() => bindEventPage(fromTask,{task_ref:ref,snapshot:null,events:[{task_ref:ref,run:runB,payload:{task:null}}]},project,workspace,prompt),'event-second-run'));
assert(fromTask.run_ref.run_id === 'run-A','SECOND_RUN_REPLACED_FIRST');
tests.push(reject(() => bindEventPage(fromTask,{task_ref:ref,snapshot:null,events:[{task_ref:ref,run:runA,payload:{task:{...task,request_id:'request-2'}}}]},project,workspace,prompt),'event-task-second-request'));
tests.push(reject(() => bindEventPage(fromTask,{task_ref:ref,snapshot:{...task,run:runB},events:[],reset:true},project,workspace,prompt),'reset-second-run'));
assert(!source.includes('state.request_id = items[0].request_id') && !source.includes('state.task_ref = items[0].task_ref'),'CATCH_IDENTITY_OVERWRITE');
console.log(JSON.stringify({status:'IDENTITY_PURE_CHECKS_PASS',new_counterexamples:tests.length,runner_imports:0,app_launches:0,model_calls:0}));
