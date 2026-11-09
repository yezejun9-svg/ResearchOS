import pathlib,json,subprocess,hashlib,os,time
E=pathlib.Path(__file__).parent;S=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/coding-any-independent-review-20261014/source');ROOT=pathlib.Path('D:/作品集/ResearchOS/research-os');C='b955c8665281193d5cbf90a146f936c9212c7940'
paths=['internal/domain/runtime_drain_windows.go','internal/domain/runtime.go','internal/domain/runtime_dispatch.go','internal/domain/budget_scopes.go','internal/domain/runtime_model_unknown_verification.go','internal/domain/runtime_qualification.go']
bind=[]
for name in paths:
 raw=subprocess.check_output(['git','-C',str(ROOT),'show',C+':'+name]);assert raw==(S/name).read_bytes();bind.append({'path':name,'old_core_commit':C,'sha256':hashlib.sha256(raw).hexdigest()})
overlay={'Replace':{str(S/'internal/domain/zz_readonly_shutdown_guard_test.go'):str(E/'readonly_shutdown_guard_test.go')}}
(E/'readonly-guard-overlay.json').write_text(json.dumps(overlay,ensure_ascii=True,indent=2),encoding='utf8')
(E/'readonly-guard-source-binding.json').write_text(json.dumps(bind,indent=2),encoding='utf8')
go=ROOT/'.local/tools/go1.27.1/go/bin/go.exe';temp=E/'go-temp';temp.mkdir(exist_ok=True)
env=os.environ.copy();env.update(GOFLAGS='-buildvcs=false',REVIEW_ORIGINAL_DATABASE=str(ROOT/'.local/live/current-chat-normal-desktop-first-use-20261012/data/researchos.sqlite'),GOCACHE='C:/Users/yqyyds/.codex/researchos-build-worktrees/coding-any-combined-build-20261014/.local/builds/coding-any-combined-20261014/go-cache',GOTMPDIR=str(temp),TEMP=str(temp),TMP=str(temp))
argv=[str(go),'test','./internal/domain','-overlay',str(E/'readonly-guard-overlay.json'),'-run','^TestReadOnlyOriginalShutdownGuard$','-count=1','-v'];start=time.time()
with (E/'readonly-guard.stdout.raw').open('xb') as out,(E/'readonly-guard.stderr.raw').open('xb') as err:p=subprocess.run(argv,cwd=S,env=env,stdout=out,stderr=err,timeout=120)
r={'argv':argv,'cwd':str(S),'native_exit':p.returncode,'seconds':time.time()-start,'db_access':'file URI mode=ro; query_only=ON; one connection; original production guard uses BEGIN/ROLLBACK only','original_source_commit':C,'source_files_verified':bind,'temporary_overlay_only':True,'source_writes':False,'database_writes':False}
(E/'readonly-guard.process.json').write_text(json.dumps(r,ensure_ascii=True,indent=2),encoding='utf8');print(json.dumps({'native_exit':p.returncode,'seconds':r['seconds']}))
raise SystemExit(p.returncode)
