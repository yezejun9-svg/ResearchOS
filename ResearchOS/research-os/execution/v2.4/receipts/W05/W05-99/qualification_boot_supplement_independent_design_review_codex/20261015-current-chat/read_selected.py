import hashlib,json,pathlib
repo=pathlib.Path('D:/作品集/ResearchOS/research-os')
base=repo/'execution/v2.4/receipts/W05/W05-99'
resources=base/'qualification_official_entry_resource_map_codex/20261015-current-chat'
arch=base/'qualification_recovery_boot_supplement_architecture_codex/20261015-current-chat'
def verified(parent,name):
    manifest=json.loads((parent/'FINAL-manifest.json').read_text(encoding='utf-8-sig'))
    item=next(x for x in manifest['files'] if x['path']==name)
    raw=(parent/name).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==item['sha256']
    print('VERIFIED',name,item['sha256'])
    return raw.decode('utf-8-sig')
for name in ['B-API-compatibility.md','actual-deployment-plan-reviewable.md']:
    print(verified(arch,name))
obj=json.loads(verified(resources,'file-ancestor-compact.json'))
print('COMPACT_TYPE',type(obj).__name__)
if isinstance(obj,dict):
    print('COMPACT_KEYS',list(obj))
    for k,v in obj.items():
        if isinstance(v,list): print('LIST',k,'LEN',len(v),'FIRST',json.dumps(v[:1],ensure_ascii=False))
        else: print(k,repr(v)[:1000])
elif isinstance(obj,list):
    print('COMPACT_FIRST',json.dumps(obj[:2],ensure_ascii=False))
for rel,starts in [('apps/cli/main.go',[(1,110)]),('apps/control/main.go',[(45,145)]),('ops/backup/main.go',[(175,220)]),('adapters/protectedstore/broker_windows.go',[(1,145)])]:
    path=repo/rel
    if not path.is_file(): print('MISSING',rel); continue
    raw=path.read_bytes(); print('SOURCE',rel,hashlib.sha256(raw).hexdigest())
    lines=raw.decode('utf-8-sig').splitlines()
    for lo,hi in starts:
        print('\n'.join(f'{n}: {lines[n-1]}' for n in range(lo,min(hi,len(lines))+1)))
