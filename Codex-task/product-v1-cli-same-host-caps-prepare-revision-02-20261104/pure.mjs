// In-memory synthetic fixtures only. Import does not call run()/SDK/CLI.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {parsePublicCaps} from './same-host-caps.mjs';
const marker='SYNTHETIC_SECRET_MARKER_NOT_A_CREDENTIAL';
const core={host_id:'host-0123456789ab',pid:1234};
const clean=()=>({command:'harness caps',status:'COMPLETED',completion_scope:'HOST_QUERY',exit_code:0,
  response:{api_version:'harness.v1',data:{harness_id:'codex',can_submit:false,reason_codes:['MISSING_LOGIN']}}});
const raw=x=>Buffer.from(JSON.stringify(x));
const checks=[];
function test(name,fn){try{fn();checks.push({name,pass:true});}catch(e){checks.push({name,pass:false,error:e.code||e.name});}}
for(const key of ['credential_value','client_secret','credentialValue','access_token','APIKEY'])test('reject-before-output-'+key,()=>{
  const r=clean();r.response.data.unexpected={nested:[{[key]:marker}]};
  assert.throws(()=>parsePublicCaps(raw(r),core),e=>e.code==='CLI_SECRET_OUTPUT_REFUSED'&&!e.message.includes(marker));
});
test('public-projection-excludes-all-free-text',()=>{
  const r=clean();r.unexpected=marker;r.response.data.reason_codes=[marker];r.response.data.installation={path:marker};
  const v=parsePublicCaps(raw(r),core);
  assert.equal(v.summary.can_submit,false);assert.equal(v.summary.reason_code_count,1);
  assert.equal(JSON.stringify(v).includes(marker),false);
  assert.deepEqual(Object.keys(v.public_report.response.data).sort(),['can_submit','harness_id','reason_code_count']);
});
test('malformed-json-error-cannot-carry-input',()=>{
  assert.throws(()=>parsePublicCaps(Buffer.from('{"credential_value":"'+marker+'"'),core),e=>e.code==='CAPS_JSON_INVALID'&&e.message==='CAPS_JSON_INVALID');
});
test('invalid-utf8-is-input-free-error',()=>{
  assert.throws(()=>parsePublicCaps(Buffer.from([0xff]),core),e=>e.code==='CAPS_JSON_INVALID'&&e.message==='CAPS_JSON_INVALID');
});
test('same-host-field-still-checked',()=>{
  const r=clean();r.host_id='host-000000000000';
  assert.throws(()=>parsePublicCaps(raw(r),core),e=>e.code==='CLI_REPORTED_HOST_MISMATCH');
});
test('actual-persistence-sites-use-metadata-and-public-projection',()=>{
  const s=fs.readFileSync(new URL('./same-host-caps.mjs',import.meta.url),'utf8');
  const line=s.split('\n').find(x=>x.includes("write('cli-streams.json'"));
  assert.ok(line&&!/stdout_text|stderr_text|decode\(|safe\(/.test(line));
  for(const key of ['stdout_bytes','retained_stdout_sha256','stderr_bytes','retained_stderr_sha256','exit_code','signal','overflow','spawn_error'])assert.ok(line.includes(key));
  assert.ok(s.includes("write('cli-caps.json',checked.public_report)"));
  assert.ok(s.indexOf('const checked=parsePublicCaps(stdout,core)')<s.indexOf("write('cli-caps.json',checked.public_report)"));
  assert.ok(!s.includes("write('cli-caps.json',report)"));
});
const report={schema:'researchos.cli-caps-freeze02-author-pure/1',checks,passed:checks.filter(x=>x.pass).length,
  failed:checks.filter(x=>!x.pass).length,app_launches:0,CLI_invocations:0,Native_calls:0,model_requests:0};
fs.writeFileSync(new URL('./pure-result.json',import.meta.url),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({passed:report.passed,failed:report.failed,app_launches:0,CLI_invocations:0,model_requests:0}));
if(report.failed)process.exitCode=1;
