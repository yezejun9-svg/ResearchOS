'use strict';
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../../../../../..');
const file=path.join(root,'tests/ui/w1303/permission.cjs');
const source=fs.readFileSync(file,'utf8');
const start=source.indexOf(' const replay=()=>page.evaluate('),end=source.indexOf(" check('NO_RENDERER_ERRORS'",start);
if(start<0||end<0)throw Error('Driver probe block not found');
const block=source.slice(start,end);
const refusal=code=>({ok:false,protocol_status:'REJECTED',error_code:code});
const cases=[
 {name:'direct_stale',replies:[refusal('STALE_REVISION')]},
 {name:'direct_blocked',replies:[refusal('RESOURCE_BLOCKED')]},
 {name:'refresh_once_then_stale',replies:[refusal('VERSION_CONFLICT'),refusal('STALE_REVISION')]},
 {name:'refresh_once_then_blocked',replies:[refusal('VERSION_CONFLICT'),refusal('RESOURCE_BLOCKED')]},
 {name:'second_version_still_fails',replies:[refusal('VERSION_CONFLICT'),refusal('VERSION_CONFLICT')],error:'CLOSED_REQUEST_CANNOT_WRITE_AGAIN'},
 {name:'successful_replay_fails',replies:[{ok:true,protocol_status:'COMPLETED'}],error:'CLOSED_REQUEST_CANNOT_WRITE_AGAIN'},
 {name:'first_version_requires_rejected',replies:[{ok:false,protocol_status:'COMPLETED',error_code:'VERSION_CONFLICT'}],error:'STALE_SNAPSHOT_REFUSED_WITHOUT_WRITE'},
 {name:'version_write_is_failure',replies:[refusal('VERSION_CONFLICT')],badBytes:true,error:'STALE_SNAPSHOT_REFUSED_WITHOUT_WRITE'},
 {name:'refresh_wrong_project_fails',replies:[refusal('VERSION_CONFLICT')],project:'foreign-project',error:'REFRESH_IS_SAME_ORIGINAL_SESSION'},
 {name:'refresh_wrong_session_fails',replies:[refusal('VERSION_CONFLICT')],session:'foreign-session',error:'REFRESH_IS_SAME_ORIGINAL_SESSION'},
 {name:'extra_resolution_event_fails',replies:[refusal('STALE_REVISION')],extraEvent:true,error:'NO_REPLAY_PERMISSION_EVENT'},
 {name:'replay_write_fails',replies:[refusal('STALE_REVISION')],badBytes:true,error:'REJECTION_PRESERVES_PHYSICAL_BYTES'}
];
(async()=>{
 const results=[];
 for(const spec of cases){
  const trace=[],payloads=[],report={checks:[]};let index=0;
  const original={request:{id:'original-request',revision:1},action_digest:'sha256:'+'a'.repeat(64)};
  const context={Buffer,report,input:{project_id:'original-project',expected_written_text:'approved',prompt:original},observed:{session:{result:{session_id:'original-session'}}},choice:'DENY',source:'fixture-source',initial:Buffer.from('original-bytes'),fs:{readFileSync:()=>Buffer.from(spec.badBytes?'wrong-bytes':'original-bytes')},window:{researchos:{v2:{
   'permission.respond':async payload=>{trace.push('permission.respond');payloads.push(JSON.parse(JSON.stringify(payload)));if(index>=spec.replies.length)throw Error('Unbounded replay');return spec.replies[index++];},
   'session.get':async()=>{trace.push('session.get');return{ok:true,result:{project_id:spec.project||'original-project',session_id:spec.session||'original-session'}};},
   'session.events':async()=>{trace.push('session.events');const events=[{kind:'PERMISSION_REQUIRED'},{kind:'PERMISSION_RESOLVED'}];if(spec.extraEvent)events.push({kind:'PERMISSION_RESOLVED'});return{ok:true,result:{events}};}
  }}},page:{evaluate:async(fn,args)=>fn(args)},check:(id,okay,detail)=>{report.checks.push({id,pass:!!okay,detail});if(!okay)throw Error('ASSERT:'+id)}};
  vm.createContext(context);let error=null;
  try{await vm.runInContext('(async()=>{'+block+'})()',context,{timeout:1000});}catch(e){error=String(e.message);}
  const expected=spec.error?'ASSERT:'+spec.error:null;
  if(error!==expected)throw Error(spec.name+': unexpected error '+error);
  if(index>2)throw Error(spec.name+': exceeded two attempts');
  for(const payload of payloads)if(payload.resource_request_id!==original.request.id||payload.resource_request_revision!==original.request.revision||payload.action_digest!==original.action_digest)throw Error('Original action identity changed');
  if(index===2&&(trace.filter(x=>x==='session.get').length!==1||JSON.stringify(payloads[0])!==JSON.stringify(payloads[1])))throw Error('Refresh or frozen payload mismatch');
  results.push({name:spec.name,status:'PASS',expected_rejection:expected,trace,probe_count:index,assertions:report.checks,recorded_replies:report.closed_request_probe_replies});
 }
 const result={status:'PASS',scope:'Isolated simulation of the exact test-driver replay block; no Electron, GUI, provider or runtime product execution.',driver_sha256:crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'),block_sha256:crypto.createHash('sha256').update(block).digest('hex'),cases:results,new_gui_runs:0};
 fs.writeFileSync(path.join(__dirname,'permission-probe-unit-result.json'),JSON.stringify(result,null,2)+'\n');
 process.stdout.write(JSON.stringify({status:'PASS',cases:results.length,new_gui_runs:0})+'\n');
})().catch(e=>{console.error(e);process.exitCode=1});
