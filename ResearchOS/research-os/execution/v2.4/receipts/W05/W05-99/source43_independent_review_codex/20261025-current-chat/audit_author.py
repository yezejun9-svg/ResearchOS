import json,pathlib,hashlib,sys
sys.stdout.reconfigure(encoding='utf-8')
base=pathlib.Path(__file__).parent.parent.parent/'source43_b_stop_finalpath_codex'/'20261025-current-chat'
refs=[]
def verify(node):
    if isinstance(node,dict):
        if all(k in node for k in ('path','sha256','bytes')):
            path=pathlib.Path(node['path']);path=path if path.is_absolute() else base/path
            raw=path.read_bytes(); assert hashlib.sha256(raw).hexdigest()==node['sha256'] and len(raw)==node['bytes'],str(path)
            refs.append({'path':str(path),'sha256':node['sha256'],'bytes':node['bytes']})
        for v in node.values():verify(v)
    elif isinstance(node,list):
        for v in node:verify(v)
for name,sha in [('FINAL-supplement.json','5b7113cd39b8806efe6fe08f87ea598e2a81f3bc0abb1d494b5a60f4792497d4'),('FINAL-supplement-seal.json','2c219dc9ea2e07db94b86b98e196d5a70840be126384f80b87c80699fe6c962d')]:
    raw=(base/name).read_bytes();assert hashlib.sha256(raw).hexdigest()==sha;verify(json.loads(raw))
idx=json.loads((base/'command-index.json').read_text(encoding='utf-8'))
verify(idx)
for row in idx['recorded_commands']:
    actual=json.loads((base/row['id']/'exit.json').read_text(encoding='utf-8'))
    assert actual['exit']==row['exit']
    recipe=json.loads((base/row['invocation']).read_text(encoding='utf-8'))
    print(row['id'], row['exit'],recipe['argv'])
result={'verified_reference_count':len(refs),'references':refs,'command_count':len(idx['recorded_commands']),'author_supplement_and_seal_verified':True}
(pathlib.Path(__file__).parent/'author-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('VERIFIED',len(refs),'references')
