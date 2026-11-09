import pathlib,hashlib,json,datetime,subprocess,os
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[6]
DRAFT=HERE.parent/'typed-route-5188793d240a4f1197f92bbc510ad9e1'
def ref(p):return {'path':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def write(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
paths=['internal/domain/runtime_model_verification.go','internal/domain/runtime_provider_binding_windows_test.go']
for label,args in [('source-diff-check',['git','diff','--check','--',*paths]),('source-current-diff',['git','diff','--binary','--',*paths]),('git-status-before-commit',['git','status','--short'])]:
    invocation={'argv':args,'cwd':str(ROOT),'started':datetime.datetime.now(datetime.timezone.utc).isoformat(),'environment_overrides':{}}
    write(HERE/(label+'.invocation.json'),invocation)
    with (HERE/(label+'.stdout.raw')).open('xb') as out,(HERE/(label+'.stderr.raw')).open('xb') as err:r=subprocess.run(args,cwd=ROOT,stdout=out,stderr=err)
    write(HERE/(label+'.result.json'),invocation|{'finished':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit':r.returncode,'stdout':ref(HERE/(label+'.stdout.raw')),'stderr':ref(HERE/(label+'.stderr.raw'))})
    if r.returncode:raise SystemExit(r.returncode)
files=[ref(p) for base in [DRAFT,HERE] for p in sorted(base.rglob('*')) if p.is_file()]
manifest={'schema':'researchos.public-candidate-manifest.v1','actor':'codex:/root/command_queue_impl','purpose':'Provider inventory causal author attempt3, SOURCE_EXECUTION_REPORTED only','files':files,'file_count':len(files),'total_bytes':sum(f['bytes'] for f in files),'self_excluded':True,'private_resources':0,'models':0,'scope':'Only two new public receipt namespaces; no earlier raw rewritten','source2':[ref(ROOT/p) for p in paths]}
write(HERE/'manifest.json',manifest)
print(json.dumps({'manifest':ref(HERE/'manifest.json'),'files':len(files),'bytes':manifest['total_bytes'],'source2':manifest['source2']},ensure_ascii=True))
