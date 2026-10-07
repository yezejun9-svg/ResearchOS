import os,sys,json,hashlib,subprocess,datetime,pathlib
D=pathlib.Path(__file__).resolve().parent; R=D.parents[6]; M=pathlib.Path('D:/作品集/ResearchOS/research-os')
review=M/'execution/v2.4/receipts/W05/W05-99/streaming_repaired_source_review_codex/5455e415-03a4-466e-9cd1-0b0b5e691d87'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,o):
 with (D/n).open('x',encoding='utf8') as f: json.dump(o,f,indent=2,ensure_ascii=False); f.write('\n')
if not (D/'original_refs.json').exists():
 refs=[]
 for name in ['signed-zero.sse','signed_zero_probe.go','signed_zero_sdk_probe.mjs','signed-zero-go.invocation.json','signed-zero-go.stdout','signed-zero-go.stderr','signed-zero-sdk.invocation.json','signed-zero-sdk.stdout','signed-zero-sdk.stderr']:
  p=review/name; b=p.read_bytes(); (D/name).write_bytes(b); refs.append(dict(path=str(p),sha256=sha(p)))
 save('original_refs.json',refs)
 save('overlay.json',{'Replace':{str(R/'internal/domain/independent_signed_zero_test.go'):str(D/'signed_zero_probe.go')}})
env=os.environ.copy(); G=M/'.local/tools/go1.27.1/go'; N=pathlib.Path('C:/nvm4w/nodejs/node.exe')
env.update(GOROOT=str(G),GOTOOLCHAIN='local',GOENV='off',GOPATH=str(M/'.local/gopath'),GOCACHE=str(M/'.local/gocache'),GOPROXY='off',GOSUMDB='off',RESEARCHOS_GO=str(G/'bin/go.exe'),RESEARCHOS_NODE=str(N),RESEARCHOS_MU_BUNDLE=str(R/'.local/model-stream/mu-worker.mjs'),RESEARCHOS_REVIEW_SSE=str(D/'signed-zero.sse'))
kind=sys.argv[1]
argv=[str(G/'bin/go.exe'),'test','-overlay',str(D/'overlay.json'),'-count=1','-run','^TestIndependentSignedZeroToolIdentity$','-v','./internal/domain']
if kind=='sdk': argv=[str(N),str(D/'signed_zero_sdk_probe.mjs'),str(D/'signed-zero.sse'),str(M/'third_party/mu/packages/ai/dist/api/openai-completions.js')]
sources=['internal/domain/runtime_model_stream.go','internal/domain/runtime_model_stream_test.go','apps/cli/cli_model_stream_integration_windows_test.go']
before={x:sha(R/x) for x in sources}
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
with (D/(kind+'.stdout')).open('xb') as out,(D/(kind+'.stderr')).open('xb') as err: r=subprocess.run(argv,cwd=R,env=env,stdout=out,stderr=err)
save(kind+'.invocation.json',dict(actualargv=argv,cwd=str(R),started_at=start,ended_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit=r.returncode,source_before=before,source_after={x:sha(R/x) for x in sources},environment={k:env[k] for k in ['GOROOT','GOENV','GOTOOLCHAIN','GOPATH','GOCACHE','GOPROXY','GOSUMDB','RESEARCHOS_NODE','RESEARCHOS_MU_BUNDLE','RESEARCHOS_REVIEW_SSE']},tools={str(p):sha(p) for p in [G/'bin/go.exe',N]},raw_sha256=sha(D/'signed-zero.sse')))
print(kind,r.returncode); print((D/(kind+'.stdout')).read_text(encoding='utf8')); sys.exit(r.returncode)
