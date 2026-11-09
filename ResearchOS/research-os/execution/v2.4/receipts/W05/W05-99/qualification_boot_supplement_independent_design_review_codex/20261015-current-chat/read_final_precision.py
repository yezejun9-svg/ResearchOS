import json,pathlib,hashlib
repo=pathlib.Path('D:/作品集/ResearchOS/research-os')
base=repo/'execution/v2.4/receipts/W05/W05-99/qualification_official_entry_resource_map_codex/20261015-current-chat'
obj=json.loads((base/'file-ancestor-compact.json').read_text(encoding='utf-8-sig'))
for row in obj:
    if row['kind']=='EXACT_ANCESTOR' and row['path'].startswith('D:'):
        print(row['path'],'OWNER',row['owner'],'ACE_COUNT',row['ace_count'],'CANONICAL',row['canonical'])
        print(json.dumps(row['relevant_aces'],ensure_ascii=False))
full=json.loads((base/'file-ancestor-metadata.json').read_text(encoding='utf-8-sig'))
print('FULL_FIRST_KEYS',list(full['records'][0]))
for rel,lo,hi in [('apps/cli/coding_task.go',25,105),('docs/installation/README.md',1,40),('apps/control/main.go',20,48)]:
    p=repo/rel
    if not p.is_file(): print('MISSING',rel); continue
    raw=p.read_bytes(); lines=raw.decode('utf-8-sig').splitlines(); print('SOURCE',rel,hashlib.sha256(raw).hexdigest())
    print('\n'.join(f'{n}: {lines[n-1]}' for n in range(lo,min(hi,len(lines))+1)))
