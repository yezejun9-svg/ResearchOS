import test from 'node:test'
import assert from 'node:assert/strict'
import {harnessActivityRows} from './stage01/apps/web/src/activity.js'
const ref={project_id:'qa-project',task_id:'qa-task'}
const event=(id,sequence,kind,payload,patch={})=>({event_id:id,sequence,task_ref:ref,kind,payload,run:null,timestamp:'2026-11-04T00:00:00Z',...patch})
test('Q02 correct API TaskRef projects failed native tool with explicit error tone',()=>{
 const raw=event('e1','9007199254740993','TOOL_EVENT',{status:null,text:null,tool:{id:'t1',name:'read',phase:'FAILED',summary:'denied'},task:null,error:null})
 const rows=harnessActivityRows([raw],ref)
 assert.equal(rows.length,1);assert.equal(rows[0].tone,'error');assert.match(rows[0].summary,/FAILED.*denied/)
})
test('Q03 Q07 projection exact integer order, task filtering and deduplication',()=>{
 const one=event('e1','9007199254740993','LOG',{text:'first'}),two=event('e2','9223372036854775807','LOG',{text:'last'})
 const foreign=event('e3','2','LOG',{text:'foreign'}, {task_ref:{...ref,task_id:'other'}})
 const rows=harnessActivityRows([two,one,one,foreign],ref)
 assert.deepEqual(rows.map(r=>r.event.event_id),['e2','e1']);assert.ok(!JSON.stringify(rows).includes('foreign'))
})
test('Q23 UNKNOWN and cancel request do not become successful acceptance',()=>{
 for(const status of ['UNKNOWN','CANCEL_REQUESTED']){
  const rows=harnessActivityRows([event('state','1','RUN_STATE',{status,text:null,tool:null,task:null,error:null})],ref)
  assert.equal(rows.length,1);assert.equal(rows[0].tone,'neutral');assert.ok(!JSON.stringify(rows).includes('ACCEPTED'))
 }
})
