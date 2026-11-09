import pathlib,subprocess,os,json,time,hashlib,sys
R=pathlib.Path(__file__).parent;S=R/'source';O=R/'runs';O.mkdir(exist_ok=True)
N='C:/Users/yqyyds/AppData/Local/nvm/v24.9.0/node.exe'
G='D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe'
B=S/'.local/independent/mu-worker.mjs'
E=os.environ.copy();T=R/'fixture-temp';T.mkdir(exist_ok=True);E.update(TEMP=str(T),TMP=str(T),GOFLAGS='-buildvcs=false',RESEARCHOS_PAUSE_WORKER_BUNDLE=str(B),RESEARCHOS_ACCEPTED_MU_SOURCE='C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-pause-checkpoint-m0-v2-20261012')
E['RESEARCHOS_QUEUE_WORKER_BUNDLE']=str(B)
E['RESEARCHOS_REVIEW_CANDIDATE_ROOT']=str(B.parent)
commands={
 'host-actual':[G,'test','./internal/host','-run','TestIndependentActualRebuiltCandidateLoader','-count=1','-v'],
 'independent-node-r2':[N,'--test','adapters/runtime/mu/independent-review.test.mjs'],
 'build':[N,'adapters/runtime/mu/build-candidate.mjs',E['RESEARCHOS_ACCEPTED_MU_SOURCE'],str(B)],
 'node-r2':[N,'--test','adapters/runtime/mu/worker-pause.test.mjs','adapters/runtime/mu/build-candidate.test.mjs','adapters/runtime/mu/worker-control.test.mjs'],
 'bridge':[G,'test','./adapters/runtime','-run','TestBridgeProductionPause|TestPauseCheckpoint|TestBridgeControlIdentity|TestBridgeQueueEmpty|TestModelStreamBridge','-count=1','-v','-pause-worker-bundle',str(B),'-pause-worker-node',N],
 'host-r2':[G,'test','./internal/host','-run','TestTrustedCandidateAssets|TestLocalRuntimeAssetsMissing','-count=1','-v'],
 'independent':[G,'test','./adapters/runtime','-run','TestIndependent','-count=1','-v'],
}
for name in sys.argv[1:]:
 cmd=commands[name];start=time.time()
 with (O/(name+'.stdout.txt')).open('xb') as out,(O/(name+'.stderr.txt')).open('xb') as err:
  p=subprocess.run(cmd,cwd=S,env=E,stdout=out,stderr=err,timeout=150)
 result={'argv':cmd,'cwd':str(S),'exit':p.returncode,'elapsed_seconds':time.time()-start,'node_sha256':hashlib.sha256(pathlib.Path(N).read_bytes()).hexdigest(),'go_sha256':hashlib.sha256(pathlib.Path(G).read_bytes()).hexdigest(),'GOFLAGS':E['GOFLAGS']}
 (O/(name+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'name':name,'exit':p.returncode,'seconds':result['elapsed_seconds']}),flush=True)
 if p.returncode:sys.exit(p.returncode)
