import pathlib,json,subprocess,hashlib,tarfile,io,datetime
R=pathlib.Path(__file__).parent;SRC=R.parent/'coding-any-repair-20261014';E=R.parent/'coding-any-repair-20261014-evidence';S=R/'source'
D=pathlib.Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/coding_prepare_rejection_diagnosis_codex/20261014-current-chat')
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def save(n,o):(R/n).write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf8')
def git(*a):return subprocess.check_output(['git','-C',str(SRC),*a]).decode().strip()
C='1846ef315a2057d78ee9349379eb9557b66ea519';BASE='454492f78fc0536966c8c8343d4bdd2fd99250b7'
assert git('rev-parse','HEAD')==C and not git('status','--porcelain')
assert sha(E/'manifest.sha256.json')=='747c8a85c7696b2f44892306cc8676b17e17e0aa80da31d5bca73baa378d71fb'
manifest=read(E/'manifest.sha256.json');report=read(E/'repair-report.json')
for f in manifest['files']:assert sha(E/f['file'])==f['sha256']
assert git('diff','--name-only',BASE,C).splitlines()==sorted(report['changed_paths'])
assert sha(SRC/'internal/host/runtime_coding_windows.go')==report['source_sha256']
assert sha(SRC/'internal/host/runtime_coding_windows_test.go')==report['test_sha256']
scope=read(D/'scope-input.json');audit=read(D/'actual-workspace-scope-audit.json');actual=pathlib.Path(audit['actual_workspace'])
assert sha(D/'scope-input.json')==report['original_scope_input_sha256']
assert sha(D/'actual-workspace-scope-audit.json')==report['original_326_file_audit_sha256']
assert len(scope['SourcePaths'])==len(audit['source_files'])==326
assert sorted(scope['SourcePaths'])==sorted(f['path'] for f in audit['source_files'])
fixture=R/'actual326-fixture';fixture.mkdir(exist_ok=False)
for f in audit['source_files']:
 p=actual/f['path'];assert sha(p)==f['sha256']
 target=fixture/f['path'];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes())
directories={}
for f in audit['source_files']:
 if f['path'].endswith('.go'):
  parent=pathlib.PurePosixPath(f['path']).parent.as_posix()
  directories[parent]=sorted(p.name for p in (actual/parent).glob('*.go') if not p.name.endswith('_test.go'))
for parent,names in directories.items():
 for name in names:assert (pathlib.PurePosixPath(parent)/name).as_posix() in scope['SourcePaths'],(parent,name)
paths=['adapters','internal','ops','evaluation/holdout/jev','evaluation/evolution','evaluation/skills','go.mod','go.sum','migrations','contracts','bootstrap','spec']
data=subprocess.check_output(['git','-C',str(SRC),'archive',C,*paths]);S.mkdir(exist_ok=False)
with tarfile.open(fileobj=io.BytesIO(data)) as t:
 for m in t.getmembers():assert (m.isfile() or m.isdir()) and (S/m.name).resolve().is_relative_to(S.resolve())
 t.extractall(S,filter='data')
baseline=R/'baseline-runtime_coding_windows.go';baseline.write_bytes(subprocess.check_output(['git','-C',str(SRC),'show',BASE+':internal/host/runtime_coding_windows.go']))
save('baseline-overlay.json',{'Replace':{str(S/'internal/host/runtime_coding_windows.go'):str(baseline)}})
(R/'scope-input.json').write_bytes((D/'scope-input.json').read_bytes())
files=[{'path':p.relative_to(S).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in S.rglob('*') if p.is_file()]
save('input-before.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(SRC),'commit':C,'base':BASE,'tree':git('rev-parse','HEAD^{tree}'),'author_manifest':manifest,'author_report':report,'snapshot_files':files,'actual_workspace':str(actual),'actual_scope':scope,'actual326_files':audit['source_files'],'production_directory_members':directories,'baseline_source_sha256':sha(baseline),'go_exe_sha256':sha(pathlib.Path(scope['ToolchainRoot'])/'bin/go.exe')})
print(json.dumps({'source_files':len(files),'actual326_files':len(audit['source_files']),'source_commit':C}))
