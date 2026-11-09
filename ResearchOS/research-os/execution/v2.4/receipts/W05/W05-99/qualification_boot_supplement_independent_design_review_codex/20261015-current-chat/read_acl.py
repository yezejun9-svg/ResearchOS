import hashlib,json,pathlib,subprocess
repo=pathlib.Path('D:/作品集/ResearchOS/research-os')
base=repo/'execution/v2.4/receipts/W05/W05-99/qualification_official_entry_resource_map_codex/20261015-current-chat'
for name,expected in [('file-ancestor-metadata.json','f4c58e80940d0dc81ce9c0bac70a1131030238c27cfe7e9347e749ac33d71cc5'),('file-ancestor-compact.json','bcdde661f9f5514807e2148daa752a11f0c66cd39e1d1ded000a9cfd73fb4a22')]:
    raw=(base/name).read_bytes(); assert hashlib.sha256(raw).hexdigest()==expected
    obj=json.loads(raw.decode('utf-8-sig')); print('VERIFIED',name,expected)
    if name=='file-ancestor-metadata.json':
        print('FULL_SHAPE',type(obj).__name__,list(obj)[:10] if isinstance(obj,dict) else list(obj[0]))
        continue
    for row in obj:
        if row['kind']!='EXACT_ANCESTOR': continue
        aces=[a for a in row['relevant_aces'] if a['qualifier']=='AccessAllowed' or a['sid'] in ['S-1-1-0','S-1-5-11','S-1-5-32-545','S-1-5-21-2314176124-1781180693-2759285857-1001']]
        print(json.dumps({k:row[k] for k in ['path','owner','canonical','ace_count']}|{'selected_aces':aces},ensure_ascii=False))
for name in ['apps/cli','docs/installation/README.md']:
    assert (repo/name).exists()
result=subprocess.run(['rg','-n','exec.Command|store.Open|host.New|AcquireDataRootLease|\.Start\(|fixture|disposable|SCM','apps/cli','docs/installation/README.md'],cwd=repo,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
print('RG_EXIT',result.returncode); print(result.stdout.decode('utf-8')); print(result.stderr.decode('utf-8'))
