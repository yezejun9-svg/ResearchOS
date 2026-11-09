// Pure Node resolution/metadata, not package execution. Needs
// --experimental-import-meta-resolve to honor the actual parent URL argument.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire,isBuiltin} from 'node:module';
import {pathToFileURL,fileURLToPath} from 'node:url';
const main='D:/作品集/ResearchOS/research-os';
const source=path.join(main,'apps/web/node_modules');
const target=process.argv[2]||null;
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const inside=(root,p)=>{const rel=path.relative(root,p);return rel===''||(!rel.startsWith('..'+path.sep)&&rel!=='..'&&!path.isAbsolute(rel));};
const packageName=spec=>spec.startsWith('@')?spec.split('/').slice(0,2).join('/'):spec.split('/')[0];
function resolve(spec,parent){
  const attempts=[];
  for(const mode of ['import','require']){
    try{
      const resolved=mode==='import'?import.meta.resolve(spec,pathToFileURL(parent).href):createRequire(parent).resolve(spec);
      if(resolved.startsWith('node:')||isBuiltin(resolved))return {builtin:true,mode,entry:resolved};
      const file=resolved.startsWith('file:')?fileURLToPath(resolved):resolved;
      if(!fs.statSync(file).isFile())throw Error('ENTRY_NOT_FILE');
      return {mode,entry:fs.realpathSync.native(file)};
    }catch(e){attempts.push({mode,code:e.code||e.message});}
  }
  return {unresolved:true,attempts};
}
function locate(spec,parent){
  const found=resolve(spec,parent);
  const allowed=target||main;
  if(found.builtin)return found;
  if(found.unresolved){
    // Some declared dependencies are genuinely types-only packages and have
    // no runtime export. Use Node's own search directories, not the often
    // unexported "pkg/package.json" subpath, and record that distinction.
    for(const directory of createRequire(parent).resolve.paths(packageName(spec))||[]){
      const root=path.join(directory,packageName(spec)),file=path.join(root,'package.json');
      if(!inside(allowed,root)||!fs.existsSync(file))continue;
      const pkg=JSON.parse(fs.readFileSync(file,'utf8'));
      if(pkg.name!==packageName(spec))continue;
      if(typeof pkg.types==='string'&&!pkg.main&&!pkg.exports&&!fs.existsSync(path.join(root,'index.js'))){
        const entry=path.resolve(root,pkg.types);
        if(inside(root,entry)&&fs.statSync(entry).isFile())return {mode:'node-search-types-only',entry,root,package:pkg,package_sha256:sha(file),runtime_entry:false};
      }
      break;
    }
    return found;
  }
  if(!inside(allowed,found.entry))throw Error('Resolved outside approved public root: '+found.entry);
  if(!found.entry.split(path.sep).includes('node_modules'))throw Error('Not a dependency path');
  let directory=path.dirname(found.entry);
  while(inside(allowed,directory)){
    const file=path.join(directory,'package.json');
    if(fs.existsSync(file)){
      const pkg=JSON.parse(fs.readFileSync(file,'utf8'));
      if(pkg.name===packageName(spec))return {...found,root:directory,package:pkg,package_sha256:sha(file)};
    }
    const next=path.dirname(directory);if(next===directory)break;directory=next;
  }
  throw Error('Package identity not found from resolved actual entry: '+spec);
}
const compatible=(values,actual)=>!Array.isArray(values)||(!values.includes('!'+actual)&&(!values.some(v=>!v.startsWith('!'))||values.includes(actual)));
const locks=[];
for(const file of [path.join(main,'apps/web/package-lock.json'),path.join(main,'apps/package-lock.json'),path.join(main,'package-lock.json')]){
  if(fs.existsSync(file))locks.push({file,sha256:sha(file),value:JSON.parse(fs.readFileSync(file,'utf8'))});
}
function omittedPlatform(spec){
  const suffix='node_modules/'+spec,candidates=[];
  for(const lock of locks)for(const [key,value] of Object.entries(lock.value.packages||{})){
    if(key===suffix||key.endsWith('/'+suffix))candidates.push({lock:lock.file,key,os:value.os,cpu:value.cpu,version:value.version});
  }
  return candidates.length&&candidates.every(v=>!compatible(v.os,process.platform)||!compatible(v.cpu,process.arch))?candidates:null;
}
const anchor=target?path.join(target,'__resolution_anchor__.mjs'):path.join(main,'apps/web/package.json');
// The anchor need not exist; resolution is based on its parent directory.
const queue=['vite','react','react-dom'].map(spec=>({spec,parent:anchor,required:true,owner:'<seed>'}));
const nodes=new Map(),edges=[],excluded=[];
while(queue.length){
  const edge=queue.shift();const found=locate(edge.spec,edge.parent);
  if(found.builtin){edges.push({...edge,...found});continue;}
  if(found.unresolved){
    const evidence=!edge.required&&omittedPlatform(edge.spec);
    if(evidence){excluded.push({...edge,reason:'LOCK_OS_CPU_EXCLUDES_CURRENT_WINDOWS_ARCH',evidence});continue;}
    throw Error('Required/current-platform dependency unresolved: '+JSON.stringify({...edge,...found}));
  }
  const pkg=found.package;
  if(!compatible(pkg.os,process.platform)||!compatible(pkg.cpu,process.arch)){
    if(edge.required)throw Error('Required dependency platform mismatch');
    excluded.push({...edge,reason:'INSTALLED_OS_CPU_EXCLUDES_CURRENT',os:pkg.os,cpu:pkg.cpu});continue;
  }
  edges.push({...edge,mode:found.mode,entry:found.entry,package_root:found.root,name:pkg.name,version:pkg.version,package_sha256:found.package_sha256});
  if(nodes.has(found.root))continue;
  nodes.set(found.root,{name:pkg.name,version:pkg.version,source_root:found.root,entry:found.entry,
    mode:found.mode,package_sha256:found.package_sha256,dependencies:pkg.dependencies||{},optionalDependencies:pkg.optionalDependencies||{},os:pkg.os,cpu:pkg.cpu});
  const optional=pkg.optionalDependencies||{};
  for(const spec of Object.keys(pkg.dependencies||{}).sort())if(!Object.hasOwn(optional,spec))queue.push({spec,parent:found.entry,required:true,owner:pkg.name});
  for(const spec of Object.keys(optional).sort()){
    const evidence=omittedPlatform(spec);
    if(evidence)excluded.push({spec,owner:pkg.name,reason:'LOCK_OS_CPU_EXCLUDES_CURRENT_WINDOWS_ARCH',evidence});
    else queue.push({spec,parent:found.entry,required:false,owner:pkg.name});
  }
}
const sourceVite=path.join(source,'vite/dist/node/chunks/node.js');
const oldVite=path.join(main,'.local/product-v1-build-inputs-20261104/web-node_modules/vite/dist/node/chunks/node.js');
const probes=target?[]:[{parent:sourceVite,spec:'rolldown',result:resolve('rolldown',sourceVite)},
  {parent:oldVite,spec:'rolldown',result:resolve('rolldown',oldVite)}];
console.log(JSON.stringify({schema:'researchos.public-node-package-resolution.v1',platform:process.platform,arch:process.arch,
  phase:target?'copied-target':'original-source',root:target||source,nodes:[...nodes.values()].sort((a,b)=>a.name.localeCompare(b.name)),
  edges,excluded,probes,locks:locks.map(({file,sha256})=>({file,sha256})),package_code_executed:false},null,2));
