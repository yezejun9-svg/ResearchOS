import hashlib,json,pathlib
E=pathlib.Path(__file__).parent
N=pathlib.Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat')
P=N/'desktop-main-integration-01'
paths=sorted(p for p in P.iterdir() if p.is_file())+sorted(N.glob('090-desktop-main-integration.recipe.*'))+[N/'continuation-cp555/Desktop-Main-integration-scope.json',N/'preserve_desktop_main_ecc28.py',N/'integrate_desktop_main_ecc28.py']
def put(name,v):
    with (E/name).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
put('001-capture.recipe.json',{'reads':[str(p) for p in paths],'mode':'READ_ONLY_POST_INTEGRATION_RECEIPTS_NO_TEST_OR_NATIVE','writes':str(E)})
out=E/'inputs';out.mkdir(exist_ok=False);refs=[]
for p in paths:
    raw=p.read_bytes();target=out/p.name
    with target.open('xb') as f:f.write(raw)
    assert raw==p.read_bytes()
    refs.append({'path':str(p),'copy':str(target),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
put('CAPTURED-INPUTS.json',refs)
assert hashlib.sha256((out/'Desktop-Main-integration-scope.json').read_bytes()).hexdigest()=='ecf4ed370ee094af13a290d1c04c6d7925da7823ab4b273b84efcb97297ae8a2'
print(json.dumps({'captured':[{'name':pathlib.Path(r['path']).name,'sha256':r['sha256'],'bytes':r['bytes']} for r in refs]},ensure_ascii=False))
for name in ['Desktop-Main-integration-scope.json','090-desktop-main-integration.recipe.result.json','090-desktop-main-integration.recipe.stdout.raw']:
    print(name);print((out/name).read_text(encoding='utf-8'))
