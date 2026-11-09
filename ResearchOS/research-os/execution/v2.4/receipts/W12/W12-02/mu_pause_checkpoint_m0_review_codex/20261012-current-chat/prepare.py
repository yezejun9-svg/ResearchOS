import pathlib,json,hashlib,subprocess
ROOT=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-pause-checkpoint-m0-20261012')
OUT=pathlib.Path(__file__).parent
AUTHOR=OUT.parent.parent/'mu_pause_checkpoint_m0_codex'/'20261012-current-chat'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((AUTHOR/'source-manifest.json').read_text())
checks=[]
for group,base in [('source',ROOT),('inputs',ROOT),('proof',AUTHOR),('bundle',AUTHOR)]:
 for item in ([m[group]] if group=='bundle' else m[group]):
  p=pathlib.Path(item['path']); p=p if p.is_absolute() else base/p
  checks.append(dict(group=group,path=str(p),sha256=sha(p),matches=sha(p)==item['sha256'],bytes=p.stat().st_size))
assert all(x['matches'] for x in checks)
git=lambda *args:subprocess.check_output(['git',*args],cwd=ROOT,text=True)
assert git('rev-parse','HEAD').strip()==m['commit']
assert git('status','--porcelain')==''
(OUT/'source-binding.json').write_text(json.dumps(dict(checks=checks,head=m['commit'],base=m['base'],git=git('show','-s','--format=fuller','HEAD'),status='clean'),indent=2))
prefix=(ROOT/'packages/agent/test/pause-checkpoint.test.ts').read_text().split('test("both raw queues')[0]
prefix=prefix.replace('../src/agent.ts',ROOT.as_posix()+'/packages/agent/src/agent.ts').replace('../src/types.ts',ROOT.as_posix()+'/packages/agent/src/types.ts')
(OUT/'independent-agent.test.ts').write_text(prefix+(OUT/'independent-agent-cases.txt').read_text())
prefix=(ROOT/'packages/coding-agent/test/pause-checkpoint.test.ts').read_text().split('test("complete session header')[0]
prefix=prefix.replace('../../../scripts/',ROOT.as_posix()+'/scripts/').replace('../src/',ROOT.as_posix()+'/packages/coding-agent/src/').replace('./model-runtime-test-utils.ts',ROOT.as_posix()+'/packages/coding-agent/test/model-runtime-test-utils.ts')
(OUT/'independent-session.test.ts').write_text(prefix+(OUT/'independent-session-cases.txt').read_text())
compile=(pathlib.Path('C:/Users/yqyyds/.codex/mu-m0-build-20261012/compile-tests.mjs').read_text()).split('for (const target')[0]
compile+='''
const targets = [
 ['author-agent',root+'/packages/agent/test/pause-checkpoint.test.ts'],
 ['author-session',root+'/packages/coding-agent/test/pause-checkpoint.test.ts'],
 ['independent-agent',new URL('./independent-agent.test.ts',import.meta.url).pathname.slice(1)],
 ['independent-session',new URL('./independent-session.test.ts',import.meta.url).pathname.slice(1)],
];
const out = decodeURIComponent(new URL('.',import.meta.url).pathname.slice(1));
for (const [name,entry] of targets) {
 const result=await esbuild.build({entryPoints:[decodeURIComponent(entry)],outfile:path.join(out,name+'.mjs'),bundle:true,platform:'node',format:'esm',target:'node24',nodePaths:[modules],plugins:[candidatePlugin],metafile:true,logLevel:'warning',banner:{js:'import { createRequire as createRequireForBundle } from "node:module"; const require = createRequireForBundle(import.meta.url);'}});
 require('node:fs').writeFileSync(path.join(out,name+'.metafile.json'),JSON.stringify(result.metafile,null,2));
 process.stdout.write(name+' candidate bundle compiled\\n');
}
'''
(OUT/'compile.mjs').write_text(compile)
print(json.dumps(dict(bindings=len(checks),all_matches=True,head=m['commit'])))
