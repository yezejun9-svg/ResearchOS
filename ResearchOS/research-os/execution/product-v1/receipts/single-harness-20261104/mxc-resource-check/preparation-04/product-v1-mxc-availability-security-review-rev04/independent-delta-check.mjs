import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
const base='C:/Users/yqyyds/Documents/Codex/2026-11-04/task';
const prev=base+'/product-v1-mxc-availability-prepare-rev03-20261105-d83a';
const next=base+'/product-v1-mxc-availability-prepare-rev04-20261105-e91c';
const oldPrefix='C:/nvm4w/nodejs',newPrefix='C:/Users/yqyyds/AppData/Local/nvm/v24.9.0';
const oldHash='6011310276abb45c4bbcfdd786dac15e1dfdcdd93fb0805a9dfae45d10f6ac14',newHash='3328346c0c9466eda017b76d4e01e707d2d1d0d5e7be864f7ebfd5a6917ff3c2';
const bytes=p=>fs.readFileSync(p);
const sha=p=>crypto.createHash('sha256').update(bytes(p)).digest('hex');
const json=p=>JSON.parse(bytes(p));
const map={};
function transform(v){
 if(typeof v==='string')return v.replaceAll(oldPrefix,newPrefix).replaceAll(oldPrefix.replaceAll('/','\\'),newPrefix.replaceAll('/','\\')).replaceAll('rev03-20261105-d83a','rev04-20261105-e91c').replaceAll('mxc_availability_20261105_d83a','mxc_availability_20261105_e91c').replaceAll(oldHash,newHash);
 if(Array.isArray(v))return v.map(transform);
 if(v&&typeof v==='object')return Object.fromEntries(Object.entries(v).map(([k,x])=>[k,transform(x)]));
 return v;
}
assert.equal(sha(next+'/MANIFEST.json'),'8055e053377ed5f837abbe8ee870a5b46f5a214b3360da34ea07b591d93c9fcd');
assert.equal(sha(prev+'/MANIFEST.json'),'6e0b74a1d62256c8c040ca5732f2ac09887effe784eca8f5dbcc5f8df57c7439');
for(const dir of [prev,next]){
 const manifest=json(dir+'/MANIFEST.json');
 for(const f of manifest.files){assert.equal(sha(dir+'/'+f.name),f.sha256);assert.equal(bytes(dir+'/'+f.name).length,f.bytes);map[dir+'/'+f.name]=f.sha256;}
 map[dir+'/MANIFEST.json']=sha(dir+'/MANIFEST.json');
}
const before=bytes(prev+'/mxc-echo.mjs').toString('utf8'),after=bytes(next+'/mxc-echo.mjs').toString('utf8');
assert.equal(after,before.replaceAll(oldPrefix,newPrefix).replaceAll('mxc_availability_20261105_d83a','mxc_availability_20261105_e91c'));
assert.deepEqual(bytes(prev+'/bounded-capture.mjs'),bytes(next+'/bounded-capture.mjs'));
for(const name of ['mxc.scope.template.json','f13.scope.template.json'])assert.deepEqual(json(next+'/'+name),transform(json(prev+'/'+name)));
assert.deepEqual(json(next+'/pins.json').pins,transform(json(prev+'/pins.json').pins));
const inner=json(next+'/mxc.scope.template.json'),outer=json(next+'/f13.scope.template.json');
assert.equal(inner.state,'PREPARATION_ONLY_NOT_AUTHORIZED');assert.equal(outer.authorization,'PREPARATION_ONLY_NOT_AUTHORIZED');
assert.equal(inner.argv.length,12);assert.equal(inner.native_invocations,1);assert.equal(inner.model_tasks,0);
assert.equal(fs.existsSync(next+'/mxc.scope.json'),false);
assert.equal(fs.existsSync(path.dirname(inner.run_root)),false);
const publicChecks=[];
const fold=p=>path.resolve(p).toLowerCase();
for(const pin of json(next+'/pins.json').pins){
 assert.equal(sha(pin.path),pin.sha256);map[pin.path]=pin.sha256;
 let cursor=path.resolve(pin.path),count=0;
 for(;;){assert.equal(fs.lstatSync(cursor).isSymbolicLink(),false,cursor);assert.equal(fold(fs.realpathSync.native(cursor)),fold(cursor),cursor);count++;const up=path.dirname(cursor);if(up===cursor)break;cursor=up;}
 assert.equal(fs.statSync(pin.path).isFile(),true);
 publicChecks.push({path:pin.path,sha256:pin.sha256,ancestor_count:count,canonical:fs.realpathSync.native(pin.path)});
}
assert.equal(fold(process.execPath),fold(outer.executable));
console.log(JSON.stringify({status:'INDEPENDENT_CANONICAL_DELTA_PASS',wrapper_only_delta:'canonical Node/Codex prefix and unique scope_id',templates_exact_transformed_equivalence:true,capture_byte_identical:true,ordinary_makeEnvironment_argv_budget_unchanged:true,rev03_frozen_members:8,rev04_frozen_members:8,public_file_checks:publicChecks,source_sha256:map,actual_native_invocations:0,model_invocations:0,candidate_entrypoint_imports:0,stream_suite_rerun:false},null,2));

