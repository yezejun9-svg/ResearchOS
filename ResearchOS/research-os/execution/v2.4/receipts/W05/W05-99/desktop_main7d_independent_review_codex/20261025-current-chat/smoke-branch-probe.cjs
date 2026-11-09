'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const src = fs.readFileSync(path.join(__dirname, 'snapshot/apps/desktop/main/main.js'), 'utf8');
const start = src.indexOf('  if (SMOKE) {');
const end = src.indexOf('\n}\n\napp.whenReady', start);
if (start < 0 || end < 0) throw new Error('frozen smoke block absent');
const block = src.slice(start, end);
const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
const run = new AsyncFunction('SMOKE','renderer','nativeProbe','desktopManagement','console','app',block);
(async () => {
 const results = [];
 for (const c of [
  {name:'BROKEN_without_native_probe',state:'BROKEN',probe:null},
  {name:'BROKEN_with_native_probe_OK',state:'BROKEN',probe:{ok:true}},
  {name:'READY_successful_shutdown',state:'READY',probe:{ok:true}},
  {name:'READY_failed_shutdown',state:'READY',probe:{ok:true},failShutdown:true},
  {name:'BROKEN_with_unconfirmed_child',state:'BROKEN',probe:null,child:true},
 ]) {
  let exited = null, shutdownCalls = 0;const logs = [];
  const manager = {state:c.state,failure:'FIXTURE',hasUnconfirmedChild:()=>!!c.child,
   shutdown:async()=>{shutdownCalls++;if(c.failShutdown)throw Error('FIXTURE_SHUTDOWN_FAILURE');return {state:'STOPPED',process_exit_confirmed:true};}};
  await run(true,{bridge:true,mounted_title:'fixture',review:true,react_root:true},c.probe,manager,{log:s=>logs.push(s)},{exit:n=>{exited=n;}});
  results.push({name:c.name,app_exit:exited,shutdown_calls:shutdownCalls,report_logs:logs});
 }
 if(results[0].app_exit!==0 || results[1].app_exit!==0 || results[2].shutdown_calls!==1 || results[2].report_logs.length!==0 || results[3].app_exit!==2 || results[4].app_exit!==null)throw Error('frozen behavior differs');
 console.log(JSON.stringify({class:'EXACT_FROZEN_SMOKE_BLOCK_WITH_MOCKED_APP_AND_MANAGER_NO_GUI_OR_CORE',source_sha256:crypto.createHash('sha256').update(src).digest('hex'),block_sha256:crypto.createHash('sha256').update(block).digest('hex'),results},null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
