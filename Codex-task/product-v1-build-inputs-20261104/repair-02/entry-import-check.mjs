// C-owned public module import only, not a Desktop/project build or GUI.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
import {pathToFileURL,fileURLToPath} from 'node:url';
const owner=path.resolve(process.argv[2]),modules=path.resolve(process.argv[3]);
const graph=JSON.parse(fs.readFileSync(path.join(owner,'TARGET.resolution.json'),'utf8'));
const inside=p=>{const rel=path.relative(modules,p);return rel===''||(!rel.startsWith('..'+path.sep)&&rel!=='..'&&!path.isAbsolute(rel));};
assert.equal(graph.nodes.length,18);for(const pkg of graph.nodes)assert.ok(inside(pkg.entry));
const entry=name=>graph.nodes.find(v=>v.name===name).entry;
const vite=await import(pathToFileURL(entry('vite')).href);
await import(pathToFileURL(path.join(modules,'vite/dist/node/chunks/node.js')).href);
const react=await import(pathToFileURL(entry('react')).href);
const anchor=path.join(modules,'__entry_check__.mjs');
const clientEntry=fileURLToPath(import.meta.resolve('react-dom/client',pathToFileURL(anchor).href));
assert.ok(inside(clientEntry));const client=await import(pathToFileURL(clientEntry).href);
assert.equal(vite.version,'8.3.1');assert.equal(react.version,'19.3.0');assert.equal(typeof client.createRoot,'function');
const require=createRequire(anchor);
require(entry('@rolldown/binding-win32-x64-msvc'));
assert.ok(require(entry('lightningcss')).transform({filename:'public-fixture.css',code:Buffer.from('a{color:red}'),minify:true}).code.length>0);
const native=Object.keys(require.cache).filter(p=>p.endsWith('.node'));
assert.ok(native.every(inside));assert.ok(native.some(p=>p.includes('lightningcss-win32-x64-msvc')));
assert.ok(native.some(p=>p.includes('@rolldown')&&p.includes('win32-x64-msvc')));
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const result={status:'C_OWNED_VITE_ACTUAL_ENTRY_IMPORT_PASSED',vite:vite.version,react:react.version,
  package_count:graph.nodes.length,module_roots_all_inside_new_cache:true,react_client_entry:clientEntry,
  vite_entry:entry('vite'),vite_failing_chunk:path.join(modules,'vite/dist/node/chunks/node.js'),
  native_binaries:native.map(p=>({path:p,sha256:hash(p)})),D_Desktop_builds:0,GUI_or_model_calls:0,network_calls:0,installs:0};
fs.writeFileSync(path.join(owner,'ENTRY-IMPORT-VALIDATION.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(result));
