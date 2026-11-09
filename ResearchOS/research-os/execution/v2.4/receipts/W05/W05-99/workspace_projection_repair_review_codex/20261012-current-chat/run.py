import json,os,pathlib,subprocess,datetime
P=pathlib.Path(__file__).resolve().parent
W=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/workspace-projection-20261012')
A=P.parent.parent/'workspace_projection_repair_codex'/'20261012-current-chat'
m=json.loads((A/'author-manifest.json').read_text('utf-8-sig'))
env=os.environ.copy();env.update(m['go_environment'])
env.update(GOCACHE=str(P/'go-cache'),GOTMPDIR=str(P/'go-tmp'),TEMP=str(P/'test-tmp'),TMP=str(P/'test-tmp'),RESEARCHOS_MODEL_STREAM_EVIDENCE_DIR=str(P/'native-http-evidence'))
overlay={'Replace':{str(W/'internal/domain/reviewer_projection_windows_test.go'):str(P/'reviewer_projection_windows_test.go')}}
(P/'overlay.json').write_text(json.dumps(overlay),'utf-8')
argv=[m['go_binary'],'test','-overlay',str(P/'overlay.json'),'./internal/domain','./internal/api','-run','^(TestIndependentProjectionMatrix|TestWorkspaceProjection.*|TestConfigurationActualWindowsHostOfflineHTTP)$','-count=1','-v']
(P/'test-invocation.json').write_text(json.dumps(dict(argv=argv,cwd=str(W),environment={k:env[k] for k in [*m['go_environment'],'TEMP','TMP','RESEARCHOS_MODEL_STREAM_EVIDENCE_DIR']},started=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2),'utf-8')
with (P/'test.stdout').open('wb') as out,(P/'test.stderr').open('wb') as err:r=subprocess.run(argv,cwd=W,env=env,stdout=out,stderr=err)
(P/'test-result.json').write_text(json.dumps(dict(exit_code=r.returncode,finished=datetime.datetime.now(datetime.timezone.utc).isoformat())),'utf-8')
print('INDEPENDENT_TEST_EXIT',r.returncode)
print((P/'test.stdout').read_text('utf-8',errors='replace')[-10000:])
print((P/'test.stderr').read_text('utf-8',errors='replace')[-2000:])
raise SystemExit(r.returncode)
