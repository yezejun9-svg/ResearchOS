from review_driver import *
import ast,re,sqlite3
# Complete only the two manifest files absent from the sparse review tree.
git('021-sparse-manifest',['sparse-checkout','add','/execution/commands.json','/execution/toolchains/locked.json'])
def old(p):return git('base-'+p.replace('/','-'),['show',BASE+':'+p])
def norm(s):return re.sub(r'\s+','',s)
checks={}; bmain=old('apps/web/src/main.jsx'); main=(WT/'apps/web/src/main.jsx').read_text(); oldwork=old('apps/web/src/workbench.jsx'); work=(WT/'apps/web/src/workbench.jsx').read_text(); oldscreens=old('apps/web/src/screens.jsx'); screens=(WT/'apps/web/src/screens.jsx').read_text(); nav=(WT/'apps/web/src/navigation.jsx').read_text()
checks['main-state-and-effects-preserved']=norm(bmain[bmain.index('function App()'):bmain.index('  return <>',bmain.index('function App()'))])==norm(main[main.index('function App()'):main.index('  return <AppShell')])
for name,end in [('NativeModelConfiguration','NativeProjectEntry'),('NativeProjectEntry','DesktopQualification')]:
 checks[name+'-entire-controller-preserved']=norm(oldwork[oldwork.index('export function '+name):oldwork.index('export function '+end)])==norm(work[work.index('export function '+name):work.index('export function '+end)])
for name in ['DesktopQualification','DesktopCodingAuthorization','NativeWorkbench']:
 start=oldwork.index('export function '+name);start2=work.index('export function '+name)
 marker='  return <Panel' if name!='NativeWorkbench' else '  return <>'
 checks[name+'-state-guards-commands-preserved']=norm(oldwork[start:oldwork.index(marker,start)])==norm(work[start2:work.index(marker,start2)])
checks['workspace-permission-artifact-controls-preserved']=norm(oldwork[oldwork.index('function BoundArtifact'):])==norm(work[work.index('function BoundArtifact'):])
checks['non-workbench-screens-preserved']=norm(oldscreens[oldscreens.index('function Cycle('):])==norm(screens[screens.index('function Cycle('):])
for name,end in [('routeOf','useRoute'),('useRoute','Link')]:
 a=bmain.index('function '+name);b=bmain.index('function '+end)
 c=nav.index('function '+name);d=nav.index('function '+end)
 checks[name+'-behavior-preserved']=norm(bmain[a:b].replace('export ',''))==norm(nav[c:d].replace('export ',''))
checks['Link-behavior-preserved']=norm(bmain[bmain.index('export function Link'):bmain.index('function Icon')])==norm(nav[nav.index('export function Link'):])
baseci=ast.parse(old('ops/ci/ui.py'));ci=ast.parse((WT/'ops/ci/ui.py').read_text())
def pattern_node(tree):return next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='patterns' for t in n.targets))
bp=pattern_node(baseci);cp=pattern_node(ci);patterns=ast.literal_eval(cp.value);original=ast.literal_eval(bp.value)
checks['CI-old17-plus-exact3']=len(original)==17 and len(patterns)==20 and set(patterns)-set(original)=={'apps/web/src/**/*','tests/ui/**/*.js','tests/ui/**/*.cjs'} and all(p in patterns for p in original)
cp.value=bp.value
checks['CI-all-other-AST-identical']=ast.dump(baseci)==ast.dump(ci)
manifest={p.relative_to(WT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for pattern in patterns for p in WT.glob(pattern) if p.is_file()}
checks['CI-571-sources']=len(manifest)==571
checks['CI-new-files-bound']=all(p in manifest for p in ['apps/web/src/components/app-shell.jsx','apps/web/src/components/ui.jsx','apps/web/src/components/workbench-layout.jsx','tests/ui/frontend-redesign.cjs','tests/ui/frontend-redesign-fixture.cjs','tests/ui/desktop/w13-react.test.js'])
protected=['apps/web/src/api.js','apps/web/src/hooks.js','apps/web/src/operations.js','apps/web/src/v2client.js','apps/web/src/Pairing.jsx','apps/web/src/profile-draft.jsx','apps/web/src/resource-recovery.jsx','apps/web/src/session-continuation.jsx','apps/web/src/continuity.jsx','apps/web/src/preview.jsx','apps/web/package.json','apps/web/package-lock.json','tests/ui/expected.json','tests/ui/desktop/w13-react.test.js','spec/v2.0/ui/design-tokens.json']
checks['protected-inputs-unchanged']=git('022-protected-inputs',['diff','--name-only',BASE,SHA,'--',*protected])==''
save(E/'STATIC-COMPARISON.json',dict(checks=checks,manifest_entries=len(manifest),protected=protected));save(E/'CI-SOURCE-MANIFEST.json',manifest)
print(json.dumps(checks));assert all(checks.values()),checks
# Read-only SQLite proof after owned Core exit; never read credential material.
data=ASCII/'real-isolated-01-data';dbs=[p for p in data.rglob('*') if p.suffix in ['.db','.sqlite','.sqlite3']]
save(E/'ISOLATED-DATA-FILES.json',dict(data_dir=str(data),databases=[str(p) for p in dbs],core_sha256=hashlib.sha256((ASCII/'control.exe').read_bytes()).hexdigest()))
for db in dbs:
 con=sqlite3.connect('file:'+db.as_posix()+'?mode=ro',uri=True)
 tables=[r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
 counts={t:con.execute('SELECT count(*) FROM "'+t+'"').fetchone()[0] for t in tables if t in ['projects','runs','worker_runs','sessions','tasks','goals']}
 save(E/'ISOLATED-SQLITE-PROOF.json',dict(database=str(db),selected_counts=counts,read_only=True));con.close()
