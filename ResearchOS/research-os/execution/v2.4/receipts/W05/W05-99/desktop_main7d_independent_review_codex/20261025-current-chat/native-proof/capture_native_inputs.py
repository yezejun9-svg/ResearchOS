import hashlib,json,pathlib
E=pathlib.Path(__file__).parent
N=pathlib.Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat')
P=N/'owned-native-desktop-smoke-01'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def put(p,v):
    with pathlib.Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
names=['native-proof.json','native-result.json','native-invocation.pre.json','spawn.json','stdout.raw','stderr.raw','exact-owned-pids-postcheck.pre.json','exact-owned-pids-postcheck.result.json','exact-owned-pids-postcheck.stdout.raw','exact-owned-pids-postcheck.stderr.raw','originals.before.json','originals.after.json']
paths=[P/name for name in names]+[N/'continuation-cp553/Owned-Desktop-native-scope.json',N/'085-owned-desktop-native.recipe.json',N/'085-owned-desktop-native.recipe.result.json',N/'085-owned-desktop-native.recipe.stdout.raw',N/'085-owned-desktop-native.recipe.stderr.raw',N/'run_owned_desktop_native.py']
put(E/'001-capture.recipe.json',{'reads':[str(p) for p in paths],'writes':str(E),'mode':'READ_ONLY_EVIDENCE_NO_GUI_CORE_OR_OLD_RESOURCE_READ','bootstrap_read':'Initial scope/proof/outer-result read occurred in tool chunk d407bf before this local recipe; not claimed as pre-recorded.'})
out=E/'inputs';out.mkdir(exist_ok=False)
refs=[]
for p in paths:
    data=p.read_bytes();target=out/p.name
    with target.open('xb') as f:f.write(data)
    refs.append({'source':str(p),'local':str(target),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
    assert data==p.read_bytes()
assert sha(out/'Owned-Desktop-native-scope.json')=='328aeca61c34d84d2a8931181c4d08d0a885d1e61145dc733d1bc3ae71f802bf'
assert sha(out/'native-proof.json')=='23111efd8606c7d6380497c72a59cf119b89ed0cc205de42584c5f22babf685b'
put(E/'001-captured-refs.json',refs)
before=json.loads((out/'originals.before.json').read_bytes());after=json.loads((out/'originals.after.json').read_bytes())
print(json.dumps({'refs':len(refs),'preservation_keys_before':list(before),'preservation_keys_after':list(after),'preservation_equal':before==after,'different_top_keys':[k for k in set(before)|set(after) if before.get(k)!=after.get(k)]},ensure_ascii=False))
for name in ['native-invocation.pre.json','native-result.json','exact-owned-pids-postcheck.result.json','exact-owned-pids-postcheck.pre.json','stdout.raw','stderr.raw','085-owned-desktop-native.recipe.json']:
    print(name);print((out/name).read_text(encoding='utf-8-sig'))
