import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {createRequire} from 'node:module';
const out=path.dirname(new URL(import.meta.url).pathname.slice(1));
const source='C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-pause-checkpoint-m0-v2-20261012';
const root='D:/作品集/ResearchOS/research-os';
const modules=root+'/qualification/v2.4/mu/node_modules';
const node='C:/Users/yqyyds/AppData/Local/nvm/v24.9.0/node.exe';
const sha=b=>createHash('sha256').update(b).digest('hex');
const json=(name,value)=>fs.writeFileSync(path.join(out,name),JSON.stringify(value,null,2));
fs.mkdirSync(out,{recursive:true});
function run(name,exe,args,cwd=source){const r=spawnSync(exe,args,{cwd,encoding:'utf8',timeout:180000,env:{...process.env,TEMP:out,TMP:out}});fs.writeFileSync(path.join(out,name+'.stdout.txt'),r.stdout??'');fs.writeFileSync(path.join(out,name+'.stderr.txt'),r.stderr??'');const record={name,exe,args,cwd,status:r.status,signal:r.signal,error:r.error?.message,stdout_sha256:sha(r.stdout??''),stderr_sha256:sha(r.stderr??'')};json(name+'.command.json',record);console.log(JSON.stringify(record));return r;}
if(process.argv[2]==='prepare'){
 const manifest=JSON.parse(fs.readFileSync(source+'/.local/bundles/wip-manifest.json','utf8'));
 const census=manifest.exact_scope.map(f=>{const bytes=fs.readFileSync(source+'/'+f.path);return{...f,actual_sha256:sha(bytes),actual_bytes:bytes.length,matches:sha(bytes)===f.sha256};});
 if(census.some(f=>!f.matches))throw Error('Candidate hash mismatch');
 const patch=fs.readFileSync(source+'/.local/bundles/mu-m0-v2-wip.patch');if(sha(patch)!=='71cfeda5c1e6c9f5217e32cf2d7cc1f25bcce9a8d2a6d7b6a75e1dda77883347')throw Error('Patch mismatch');
 fs.copyFileSync(source+'/.local/bundles/wip-manifest.json',out+'/frozen-author-manifest.json');fs.writeFileSync(out+'/frozen.patch',patch);json('candidate-census-before.json',census);
 run('git-head','git',['rev-parse','HEAD']);run('git-status','git',['status','--short']);run('git-diff','git',['diff','--binary']);run('node-version',node,['--version']);
 for(const file of ['independent-agent.test.ts','independent-session.test.ts'])fs.copyFileSync(source+'/.local/bundles/'+file,out+'/'+file);
 const config=fs.readFileSync(source+'/.local/vitest-agent-config.mjs','utf8').replaceAll(source+'/.local/vite-cache',out+'/vite-cache');fs.writeFileSync(out+'/vitest.config.mjs',config);
 fs.copyFileSync(source+'/.local/tsconfig-targeted.json',out+'/tsconfig.json');
 json('bindings.json',{source,root,modules,node,alias_agent:source+'/packages/agent/src',alias_ai:root+'/qualification/v2.4/mu/packages/ai/dist',worktree:false,installed:false});
}else if(process.argv[2]==='compile'){
 const require=createRequire(import.meta.url),esbuild=require(modules+'/esbuild/lib/main.js');
 const targets=[['author-agent',source+'/packages/agent/test/pause-checkpoint.test.ts'],['author-session',source+'/packages/coding-agent/test/pause-checkpoint.test.ts'],['independent-agent',out+'/independent-agent.test.ts'],['independent-session',out+'/independent-session.test.ts']];
 if(fs.existsSync(out+'/negative-agent.test.ts'))targets.push(['negative-agent',out+'/negative-agent.test.ts']);
 if(fs.existsSync(out+'/negative-session.test.ts'))targets.push(['negative-session',out+'/negative-session.test.ts']);
 const inputMap=new Map();
 for(const[name,entry]of targets){const build=await esbuild.build({absWorkingDir:source,entryPoints:[entry],outfile:out+'/'+name+'.mjs',bundle:true,platform:'node',format:'esm',target:'node24',nodePaths:[modules],metafile:true,logLevel:'warning',banner:{js:'import {createRequire as bundleRequire} from "node:module";const require=bundleRequire(import.meta.url);'},plugins:[{name:'explicit-candidate-agent',setup(b){b.onResolve({filter:/^@earendil-works\/(pi-agent-core|pi-ai)(?:\/.*)?$/},args=>{const[,name,...rest]=args.path.split('/');const base=name==='pi-agent-core'?source+'/packages/agent/src':root+'/qualification/v2.4/mu/packages/ai/dist';const suffix=rest.join('/');const ext=name==='pi-agent-core'?'.ts':'.js';for(const f of [base+'/'+(suffix||'index')+ext,base+'/'+suffix+'/index'+ext])if(fs.existsSync(f))return{path:f};throw Error('Unresolved '+args.path);});}}]});json(name+'.metafile.json',build.metafile);for(const p of Object.keys(build.metafile.inputs)){if(p.startsWith('<'))continue;const file=path.resolve(source,p);if(!inputMap.has(file)){const bytes=fs.readFileSync(file);inputMap.set(file,{path:file,realpath:fs.realpathSync(file),sha256:sha(bytes),bytes:bytes.length});}}console.log('compiled '+name);}
 json('compile-inputs-census.json',[...inputMap.values()]);
}else if(process.argv[2]==='run'){
 run('baseline-21',node,['--test','--test-reporter=tap',...['author-agent','author-session','independent-agent','independent-session'].map(n=>out+'/'+n+'.mjs')],out);
 run('negative-extra',node,['--test','--test-reporter=tap',out+'/negative-agent.mjs',out+'/negative-session.mjs'],out);
 run('worker-2',node,['--test','--test-reporter=tap','scripts/researchos-worker-pause-checkpoint.test.mjs']);
 run('original-agent-40',node,[modules+'/vitest/vitest.mjs','--run','--config',out+'/vitest.config.mjs','test/agent.test.ts'],source+'/packages/agent');
 run('targeted-tsgo',node,[modules+'/@typescript/native-preview/bin/tsgo.js','-p',out+'/tsconfig.json','--noEmit']);
 const before=JSON.parse(fs.readFileSync(out+'/candidate-census-before.json'));json('candidate-census-after.json',before.map(f=>({...f,after_sha256:sha(fs.readFileSync(source+'/'+f.path)),unchanged:f.sha256===sha(fs.readFileSync(source+'/'+f.path))})));
}
