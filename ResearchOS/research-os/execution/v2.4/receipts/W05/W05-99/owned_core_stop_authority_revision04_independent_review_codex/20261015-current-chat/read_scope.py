import hashlib,json,pathlib,sys
root=pathlib.Path('D:/作品集/ResearchOS/research-os')
scope=json.loads((root/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp520/owned-core-stop-r4-independent-review-scope.json').read_text(encoding='utf-8'))
if sys.argv[1]=='inputs':
    for item in scope['inputs']:
        p=root/item['path']; data=p.read_bytes(); actual=hashlib.sha256(data).hexdigest()
        print('PIN',p,actual,actual==item['sha256']); assert actual==item['sha256']
        if p.name not in ('command-index.json','evidence-manifest.json'):
            print(data.decode('utf-8'))
else:
    for rel in scope['source_allowlist_readonly']:
        if sys.argv[1] not in rel and sys.argv[1]!='all': continue
        p=pathlib.Path(scope['worktree'])/rel
        print('FILE',rel,'SHA256',hashlib.sha256(p.read_bytes()).hexdigest())
        for n,line in enumerate(p.read_text(encoding='utf-8').splitlines(),1): print(f'{n}: {line}')
