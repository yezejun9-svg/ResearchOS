import fs from 'node:fs';import path from 'node:path';import{fileURLToPath}from'node:url';import{createHash}from'node:crypto';import{spawnSync}from'node:child_process';import{createRequire}from'node:module';
const out=path.dirname(fileURLToPath(import.meta.url)),source='C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-pause-checkpoint-m0-v2-20261012',prior='C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-m0-v5-independent-review-20261013',root='D:/作品集/ResearchOS/research-os',modules=root+'/qualification/v2.4/mu/node_modules',node='C:/Users/yqyyds/AppData/Local/nvm/v24.9.0/node.exe',freeze=source+'/.local/v6-final-20261014-r3';
const sha=b=>createHash('sha256').update(b).digest('hex'),hash=p=>sha(fs.readFileSync(p)),read=p=>JSON.parse(fs.readFileSync(p,'utf8')),json=(n,x)=>fs.writeFileSync(out+'/'+n,JSON.stringify(x,null,2)+'\n',{flag:'wx'});
function verify(p,h){const b=fs.readFileSync(p);if(sha(b)!==h)throw Error('Hash mismatch '+p);return b;}
function run(name,exe,args,cwd=source){if(fs.existsSync(out+'/'+name+'.command.json'))throw Error('Refusing overwrite '+name);const started=new Date().toISOString(),r=spawnSync(exe,args,{cwd,encoding:'utf8',timeout:180000,env:{...process.env,TEMP:out,TMP:out}});fs.writeFileSync(out+'/'+name+'.stdout.txt',r.stdout??'',{flag:'wx'});fs.writeFileSync(out+'/'+name+'.stderr.txt',r.stderr??'',{flag:'wx'});const record={name,started,exe,args,cwd,exit:r.status,signal:r.signal,error:r.error?.message,stdout_sha256:sha(r.stdout??''),stderr_sha256:sha(r.stderr??'')};json(name+'.command.json',record);console.log(JSON.stringify(record));return r;}
const names=['author-agent','author-session','v5-boundary','strengthened-n5','registered-independent-agent','registered-independent-session','registered-negative-session','v4-boundary','registered-control','corrected-queue-control','negative-agent','adjacent-agent'];
function audit(){
 const bytes=verify(freeze+'/v6-final-manifest.json','9e5dd1e5d93f19c6a4aa5eb5c0e2ebd7f0d1e05a987f6ec03963b4b560139da9'),m=JSON.parse(bytes);
 verify(freeze+'/v6-source.patch',m.patch_sha256);verify(freeze+'/report.json',m.report_sha256);verify(freeze+'/compiled-inputs-census.json',m.compiled_inputs_census_sha256);
 for(const f of m.source9){verify(source+'/'+f.path,f.sha256);verify(freeze+'/source/'+f.path,f.sha256);}
 for(const[n,h]of Object.entries(m.files))verify(freeze+'/'+n,h.sha256);
 const census=read(freeze+'/compiled-inputs-census.json');for(const f of census)verify(f.path,f.sha256);
 verify(prior+'/report.json',m.rejected_v5_review_sha256);verify(prior+'/state-contract-v5-addendum.md',m.state_contract_v5_sha256);
 return{manifest:m,source9:m.source9.length,author_compiled_inputs:census.length,author_bundles:Object.keys(m.files).filter(n=>n.endsWith('.metafile.json')).length,author_files:Object.keys(m.files).length,at:new Date().toISOString()};
}
if(process.argv[2]==='prepare'){
 const a=audit();json('freeze-audit-before.json',a);fs.copyFileSync(freeze+'/v6-final-manifest.json',out+'/received-manifest.json',fs.constants.COPYFILE_EXCL);fs.copyFileSync(freeze+'/scope.json',out+'/scope.json',fs.constants.COPYFILE_EXCL);
 fs.mkdirSync(out+'/inputs');for(const f of a.manifest.source9)fs.copyFileSync(source+'/'+f.path,out+'/inputs/'+f.path.replaceAll('/','__'),fs.constants.COPYFILE_EXCL);
 const provenance=[];for(const name of names.filter(n=>!n.startsWith('author-'))){const p=prior+'/'+name+'.test.ts';fs.copyFileSync(p,out+'/'+name+'.test.ts',fs.constants.COPYFILE_EXCL);provenance.push({path:name+'.test.ts',original:p,sha256:hash(p),unchanged:true});}json('fixture-provenance.json',provenance);
 fs.copyFileSync(prior+'/state-contract-v5-addendum.md',out+'/state-contract-v5-addendum.md',fs.constants.COPYFILE_EXCL);
 fs.writeFileSync(out+'/vitest.config.mjs',fs.readFileSync(prior+'/vitest.config.mjs','utf8').replaceAll(prior+'/vite-cache',out.replaceAll('\\','/')+'/vite-cache'),{flag:'wx'});fs.copyFileSync(prior+'/tsconfig.json',out+'/tsconfig.json',fs.constants.COPYFILE_EXCL);
 console.log(JSON.stringify({source9:a.source9,inputs:a.author_compiled_inputs,bundles:a.author_bundles,files:a.author_files}));
}else if(process.argv[2]==='compile'){
 const targets=process.argv.slice(3).length?process.argv.slice(3):names,require=createRequire(import.meta.url),esbuild=require(modules+'/esbuild/lib/main.js'),inputs=new Map();
 for(const name of targets){if(fs.existsSync(out+'/'+name+'.mjs'))throw Error('Refusing existing bundle '+name);const entry=name==='author-agent'?source+'/packages/agent/test/pause-checkpoint.test.ts':name==='author-session'?source+'/packages/coding-agent/test/pause-checkpoint.test.ts':out+'/'+name+'.test.ts';
 const result=await esbuild.build({absWorkingDir:source,entryPoints:[entry],outfile:out+'/'+name+'.mjs',bundle:true,platform:'node',format:'esm',target:'node24',nodePaths:[modules],metafile:true,logLevel:'warning',banner:{js:'import {createRequire as bundleRequire} from "node:module";const require=bundleRequire(import.meta.url);'},plugins:[{name:'candidate-v6-source-only',setup(b){b.onResolve({filter:/^@earendil-works\/(pi-agent-core|pi-ai)(?:\/.*)?$/},args=>{const[,pkg,...rest]=args.path.split('/');const base=pkg==='pi-agent-core'?source+'/packages/agent/src':root+'/qualification/v2.4/mu/packages/ai/dist',suffix=rest.join('/'),ext=pkg==='pi-agent-core'?'.ts':'.js';for(const p of[base+'/'+(suffix||'index')+ext,base+'/'+suffix+'/index'+ext])if(fs.existsSync(p))return{path:p};throw Error('Unresolved '+args.path);});}}]});json(name+'.metafile.json',result.metafile);
 for(const p of Object.keys(result.metafile.inputs)){if(p.startsWith('<'))continue;const f=path.resolve(source,p);if(!inputs.has(f))inputs.set(f,{path:f,realpath:fs.realpathSync(f),sha256:hash(f),bytes:fs.statSync(f).size});}console.log('compiled '+name);}
 json((process.argv.slice(3).length?process.argv.slice(3).join('-'):'baseline')+'-compiled-inputs.json',[...inputs.values()]);
}else if(process.argv[2]==='baseline'){
 if(run('baseline-compile',node,[out+'/review-driver.mjs','compile'],out).status!==0)throw Error('compile failed');
 run('v6-regression-67',node,['--test','--test-reporter=tap',...names.map(n=>out+'/'+n+'.mjs')],out);
 run('original-agent-40',node,[modules+'/vitest/vitest.mjs','--run','--config',out+'/vitest.config.mjs','test/agent.test.ts'],source+'/packages/agent');
 run('worker-2',node,['--test','--test-reporter=tap','scripts/researchos-worker-pause-checkpoint.test.mjs']);
 run('targeted-tsgo',node,[modules+'/@typescript/native-preview/bin/tsgo.js','-p',out+'/tsconfig.json','--noEmit']);
}else if(process.argv[2]==='test'){
 const targets=process.argv.slice(3),label=targets.join('-');if(run(label+'-compile',node,[out+'/review-driver.mjs','compile',...targets],out).status!==0)throw Error('compile failed');run(label,node,['--test','--test-reporter=tap',...targets.map(n=>out+'/'+n+'.mjs')],out);
}else if(process.argv[2]==='audit'){
 const a=audit(),map=new Map();for(const n of fs.readdirSync(out).filter(n=>n.endsWith('-compiled-inputs.json')))for(const f of read(out+'/'+n)){const old=map.get(f.path);if(old&&old.sha256!==f.sha256)throw Error('Input drift across runs '+f.path);verify(f.path,f.sha256);map.set(f.path,f);}json('all-independent-inputs.json',[...map.values()]);json('freeze-audit-after.json',{...a,independent_inputs:map.size,drift:[]});console.log(JSON.stringify({source9:a.source9,author_inputs:a.author_compiled_inputs,author_bundles:a.author_bundles,independent_inputs:map.size,drift:0}));
}else throw Error('unknown action');
