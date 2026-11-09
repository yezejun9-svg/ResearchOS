// Only a fresh C fixture and the copied public dependency tree. No server,
// Desktop/Core/GUI/model, npm scripts, network or project env/config is loaded.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
import {pathToFileURL,fileURLToPath} from 'node:url';
const owner=path.resolve(process.argv[2]);
const modules=path.resolve(process.argv[3]);
const graph=JSON.parse(fs.readFileSync(path.join(owner,'TARGET.resolution.json'),'utf8'));
const inside=(root,p)=>{const rel=path.relative(root,p);return rel===''||(!rel.startsWith('..'+path.sep)&&rel!=='..'&&!path.isAbsolute(rel));};
for(const pkg of graph.nodes)assert.ok(inside(modules,pkg.source_root));
const entry=name=>graph.nodes.find(n=>n.name===name).entry;
const anchor=path.join(modules,'__minimal_check__.mjs');
const reactClient=import.meta.resolve('react-dom/client',pathToFileURL(anchor).href);
assert.ok(inside(modules,fileURLToPath(reactClient)));
const vite=await import(pathToFileURL(entry('vite')).href);
const react=await import(pathToFileURL(entry('react')).href);
const client=await import(reactClient);
assert.equal(vite.version,'8.3.1');assert.equal(react.version,'19.3.0');assert.equal(typeof client.createRoot,'function');
const require=createRequire(anchor);
require(entry('@rolldown/binding-win32-x64-msvc'));
const lightning=require(entry('lightningcss'));
assert.ok(lightning.transform({filename:'fixture.css',code:Buffer.from('a { color: red; }'),minify:true}).code.length>0);
const fixture=path.join(owner,'minimal-project-01');
fs.mkdirSync(fixture); // Exclusive, never empty or overwrite a previous fixture.
fs.writeFileSync(path.join(fixture,'index.html'),'<html><body><div id="root"></div><script type="module" src="/entry.js"></script></body></html>',{flag:'wx'});
fs.writeFileSync(path.join(fixture,'entry.js'),'import React from "react"; import {createRoot} from "react-dom/client"; import "./style.css"; createRoot(document.getElementById("root")).render(React.createElement("h1",null,"closure-ok"));',{flag:'wx'});
fs.writeFileSync(path.join(fixture,'style.css'),'h1 { color: #25cbb0; }',{flag:'wx'});
await vite.build({root:fixture,configFile:false,envFile:false,logLevel:'info',
  resolve:{alias:[{find:'react-dom/client',replacement:fileURLToPath(reactClient)},{find:'react',replacement:entry('react')}]},
  css:{transformer:'lightningcss'},build:{outDir:path.join(fixture,'dist'),emptyOutDir:false,minify:false,cssMinify:'lightningcss'}});
const binaries=Object.keys(require.cache).filter(p=>p.endsWith('.node'));
assert.ok(binaries.some(p=>p.includes('lightningcss-win32-x64-msvc')));
assert.ok(binaries.some(p=>p.includes('@rolldown')&&p.includes('win32-x64-msvc')));
assert.ok(binaries.every(p=>inside(modules,p)));
const files=[];function walk(dir){for(const item of fs.readdirSync(dir,{withFileTypes:true})){const file=path.join(dir,item.name);if(item.isDirectory())walk(file);else files.push({path:path.relative(fixture,file),bytes:fs.statSync(file).size,sha256:crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex')});}}
walk(path.join(fixture,'dist'));
assert.ok(files.some(p=>p.path==='dist'+path.sep+'index.html'));
const result={status:'C_MINIMAL_VITE_REACT_NATIVE_BINDINGS_BUILD_PASSED',vite:vite.version,react:react.version,
  source_graph_packages:graph.nodes.length,modules_root:modules,react_client_entry:reactClient,
  native_binaries:binaries.map(p=>({path:p,sha256:crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex')})),
  output_files:files,D_Desktop_builds:0,GUI_or_model_calls:0,network_calls:0,installs:0};
fs.writeFileSync(path.join(owner,'MINIMAL-VALIDATION.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(result));
