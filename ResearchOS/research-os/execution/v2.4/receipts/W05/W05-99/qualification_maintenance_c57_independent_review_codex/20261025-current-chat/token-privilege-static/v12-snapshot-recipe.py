import hashlib,json,pathlib,subprocess
r=pathlib.Path('D:/作品集/ResearchOS/research-os')
out=r/'execution/v2.4/receipts/W05/W05-99/qualification_maintenance_c57_independent_review_codex/20261025-current-chat/token-privilege-static'
author=r/'.local/worktrees/qualification-maintenance-c57-20261025'
evidence=r/'execution/v2.4/receipts/W05/W05-99/qualification_recovery_boundary_boot6_codex/20261025-current-chat'
snapshot=out/'v12-snapshot'
manifest=json.loads((evidence/'final-v12-six-source-manifest.json').read_text(encoding='utf-8'))
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha((evidence/'final-v12-six-source-manifest.json').read_bytes())=='261b798794b5be7ed306c662012beae4709a07f53481d0eb0e889a6cfa137df0'
assert sha((evidence/'final-v12-additive-seal.json').read_bytes())=='28c48b05b90032f47158272fcbcad940ccfa196bd0557a4d0879c4d860d8142b'
paths=[x['path'] for x in manifest]
argv=['git','-C',str(author),'diff','--binary','08d63ed86356a93fe5715732cfeae0624c5cb6c9','--',*paths]
p=subprocess.run(argv,capture_output=True)
(out/'v12-verified-diff.stdout.raw').write_bytes(p.stdout)
(out/'v12-verified-diff.stderr.raw').write_bytes(p.stderr)
(out/'v12-verified-diff.native-exit.txt').write_text(str(p.returncode),encoding='ascii')
print(json.dumps({'argv':argv,'exit':p.returncode,'diff_sha256':sha(p.stdout)},ensure_ascii=False))
assert p.returncode==0
assert p.stdout==(evidence/'final-v12-six-source.patch').read_bytes(),'current six diff differs from sealed patch'
for item in manifest:
    relative=pathlib.Path(item['path'])
    assert not relative.is_absolute() and '..' not in relative.parts
    raw=(author/relative).read_bytes()
    assert sha(raw)==item['sha256'] and len(raw)==item['bytes'],item['path']
    destination=snapshot/relative
    destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open('xb') as f:f.write(raw)
    assert sha(destination.read_bytes())==item['sha256']
    print(json.dumps({'path':item['path'],'sha256':sha(raw),'bytes':len(raw),'snapshot':str(destination)},ensure_ascii=False))
    if item['path'] in ['internal/recoveryboundary/boot_windows.go','internal/recoveryboundary/boot_windows_test.go']:
        with (out/(relative.name+'.v12.numbered.txt')).open('x',encoding='utf-8') as f:
            f.write(''.join(f'{i}: {line}\n' for i,line in enumerate(raw.decode('utf-8').splitlines(),1)))
print('SNAPSHOT_VERIFIED')