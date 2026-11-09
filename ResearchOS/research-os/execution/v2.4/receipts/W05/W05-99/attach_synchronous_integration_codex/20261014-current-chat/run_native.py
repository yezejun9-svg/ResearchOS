import os,subprocess,json,time,hashlib,pathlib,datetime
root=pathlib.Path(r'C:/Users/yqyyds/.codex/researchos-build-worktrees')
work=root/'attach-exact6-independent-20261013'; ev=root/'attach-exact6-independent-evidence-20261013'
env=os.environ.copy(); env.update(GOROOT=r'D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go',GOPATH=r'D:/作品集/ResearchOS/research-os/.local/tools/gopath',GOMODCACHE=r'D:/作品集/ResearchOS/research-os/.local/tools/gopath/pkg/mod',GOCACHE=str(root/'attach-exact6-independent-cache'),GOTMPDIR=str(root/'attach-exact6-independent-tmp'),GOTOOLCHAIN='local',GOPROXY='off',GOSUMDB='off',GOOS='windows',GOARCH='amd64',CGO_ENABLED='0')
for k in ['GOCACHE','GOTMPDIR']: pathlib.Path(env[k]).mkdir(exist_ok=True)
rx='^TestAttach|^TestClientAttachRefusesUnsettledCanonicalRun$|^TestClientSameWriterRenewsExpiredLease$|^TestClientTypedRejectionRollsBackBusinessWrites$|^TestClientCancelChangesCanonicalRun$|^TestClientResumeNeverRestartsPreviousRun$|^TestW14SessionWriterLeaseHandoff$|^TestW13WorkspaceFilesRealHostHTTPReadDiffImport$'
cmd=[env['GOROOT']+'/bin/go.exe','test','-work','-x','./internal/domain','./internal/api','-run',rx,'-count=1','-v']
record={'argv':cmd,'cwd':str(work),'environment':{k:env[k] for k in ['GOROOT','GOPATH','GOMODCACHE','GOCACHE','GOTMPDIR','GOTOOLCHAIN','GOPROXY','GOSUMDB','GOOS','GOARCH','CGO_ENABLED']},'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
with (ev/'independent-native.stdout.raw').open('wb') as out,(ev/'independent-native.stderr.raw').open('wb') as err:
 p=subprocess.Popen(cmd,cwd=work,env=env,stdout=out,stderr=err);record['pid']=p.pid;(ev/'independent-native.process.json').write_text(json.dumps(record,indent=2),encoding='utf-8');code=p.wait()
record['exit_code']=code;record['finished_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();(ev/'independent-native.process.json').write_text(json.dumps(record,indent=2),encoding='utf-8');(ev/'independent-native.exit.txt').write_text(str(code));print(json.dumps(record));print((ev/'independent-native.stdout.raw').read_text())
