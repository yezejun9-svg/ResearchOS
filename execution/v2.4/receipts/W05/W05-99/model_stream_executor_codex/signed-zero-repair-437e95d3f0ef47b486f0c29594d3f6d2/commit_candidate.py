import pathlib,subprocess,json,hashlib
D=pathlib.Path(__file__).resolve().parent; R=D.parents[6]
sources=['internal/domain/runtime_model_stream.go','internal/domain/runtime_model_stream_test.go','apps/cli/cli_model_stream_integration_windows_test.go']
dirs=[D,D.parent/'closure-6f4e2cb1bf1d4aa48376dbc02eeb2b8c',D.parent/'closure-39d83fc9302f42ceb4e91d3403a96044']
assert subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R)==b''
names=sorted(set(sources+[p.relative_to(R).as_posix() for d in dirs for p in d.rglob('*') if p.is_file()]))
manifest={'source_paths':sources,'file_count_without_this_manifest':len(names),'files':[{'path':n,'sha256':hashlib.sha256((R/n).read_bytes()).hexdigest(),'bytes':(R/n).stat().st_size} for n in names],'unowned_deleted_paths_staged':False,'prior_closure_delta':'39053→39051 only SDK documentation image exy.png and node_modules mirror removed externally; module/SDK JS source hashes and bundle unchanged, exact3 product changes only. Actual go-list and all required tests pass; do not pretend historical vector identical.'}
with (D/'commit_manifest.json').open('x',encoding='utf8') as f: json.dump(manifest,f,indent=2,ensure_ascii=False); f.write('\n')
names.append((D/'commit_manifest.json').relative_to(R).as_posix())
subprocess.run(['git','-c','core.longpaths=true','add','--pathspec-from-file=-','--pathspec-file-nul'],cwd=R,input=b'\0'.join(x.encode() for x in names)+b'\0',check=True)
staged=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=R).decode().strip('\0').split('\0')
assert set(staged)==set(names),(len(staged),len(names))
subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
subprocess.run(['git','commit','-m','fix(runtime): match SDK signed-zero tool index identity'],cwd=R,check=True)
print('CANDIDATE',subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip())
print('COMMIT_MANIFEST_SHA256',hashlib.sha256((D/'commit_manifest.json').read_bytes()).hexdigest())
print('STAGED_EXACT_FILES',len(staged))
