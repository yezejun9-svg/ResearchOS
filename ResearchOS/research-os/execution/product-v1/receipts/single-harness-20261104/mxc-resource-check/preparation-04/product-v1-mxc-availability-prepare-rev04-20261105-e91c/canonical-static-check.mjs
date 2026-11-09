// Pure public filesystem inspection. Does not import wrapper or launch processes.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const root=path.dirname(fileURLToPath(import.meta.url));
const old=root.replace('rev04-20261105-e91c','rev03-20261105-d83a');
const fold=p=>path.resolve(p).toLowerCase();
const sha=p=>{const h=crypto.createHash('sha256'),fd=fs.openSync(p,'r'),buf=Buffer.alloc(1048576);try{let n;while((n=fs.readSync(fd,buf,0,buf.length,null)))h.update(buf.subarray(0,n));}finally{fs.closeSync(fd);}return h.digest('hex');};
const inner=JSON.parse(fs.readFileSync(path.join(root,'mxc.scope.template.json')));
const outer=JSON.parse(fs.readFileSync(path.join(root,'f13.scope.template.json')));
const before=fs.readFileSync(path.join(old,'mxc-echo.mjs'),'utf8');
const after=fs.readFileSync(path.join(root,'mxc-echo.mjs'),'utf8');
assert.equal(after,before.replaceAll('C:/nvm4w/nodejs','C:/Users/yqyyds/AppData/Local/nvm/v24.9.0').replaceAll('mxc_availability_20261105_d83a','mxc_availability_20261105_e91c'));
assert.equal(sha(path.join(root,'bounded-capture.mjs')),sha(path.join(old,'bounded-capture.mjs')));
const publicPaths=[inner.executable,outer.executable,inner.argv[7],outer.inputs.find(v=>v.path.endsWith('owned_run.py')).path,path.join(root,'bounded-capture.mjs')];
const checks=[];
for(const file of publicPaths){
  assert.ok(path.isAbsolute(file));let cursor=path.resolve(file);let ancestors=0;
  for(;;){assert.equal(fs.lstatSync(cursor).isSymbolicLink(),false,cursor);assert.equal(fold(fs.realpathSync.native(cursor)),fold(cursor),cursor);ancestors++;const parent=path.dirname(cursor);if(parent===cursor)break;cursor=parent;}
  assert.ok(fs.statSync(file).isFile());
  checks.push({path:file,canonical:fs.realpathSync.native(file),ancestors_verified:ancestors,sha256:sha(file)});
}
assert.equal(fold(process.execPath),fold(outer.executable));
for(const pin of outer.inputs.filter(v=>/^[a-f0-9]{64}$/.test(v.sha256)))assert.equal(sha(pin.path),pin.sha256,pin.path);
const previous=JSON.parse(fs.readFileSync(path.join(old,'MANIFEST.json')));
for(const f of previous.files)assert.equal(sha(path.join(old,f.name)),f.sha256);
assert.deepEqual(inner.argv,JSON.parse(fs.readFileSync(path.join(old,'mxc.scope.template.json'))).argv);
assert.equal(inner.timeout_ms,35000);assert.equal(outer.timeout_seconds,45);assert.equal(outer.cleanup_seconds,5);
assert.equal(outer.process_limit,16);assert.equal(outer.memory_mib,2048);
assert.equal(inner.state,'PREPARATION_ONLY_NOT_AUTHORIZED');assert.equal(outer.authorization,'PREPARATION_ONLY_NOT_AUTHORIZED');
assert.equal(inner.model_tasks,0);assert.equal(inner.native_invocations,1);
const result={schema:'researchos.mxc-canonical-path-static-check.v1',status:'PASS',checks,
  only_wrapper_delta:'canonical Node/Codex constants and unique scope id',
  rev03_manifest_unchanged:true,capture_module_identical:true,argv_identical:true,budgets_identical:true,
  syntax:'CHECKED_SEPARATELY',native_invocations:0,model_tasks:0,stream_suite_rerun:false,
  run_exists:fs.existsSync(path.dirname(inner.run_root)),registered_scope_exists:fs.existsSync(path.join(root,'mxc.scope.json'))};
fs.writeFileSync(path.join(root,'STATIC-CHECK.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({status:result.status,public_paths:checks.length,native_invocations:0,model_tasks:0}));

