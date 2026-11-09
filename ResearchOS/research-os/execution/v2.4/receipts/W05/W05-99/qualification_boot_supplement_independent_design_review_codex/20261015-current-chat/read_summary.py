import json,pathlib
base=pathlib.Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/qualification_official_entry_resource_map_codex/20261015-current-chat')
rows=json.loads((base/'file-ancestor-compact.json').read_text(encoding='utf-8-sig'))
for row in rows:
    p=row['path']
    if p in ['D:\\','D:\\作品集','D:\\作品集\\ResearchOS','D:\\作品集\\ResearchOS\\research-os']:
        print(p,'OWNER',row['owner'])
        for a in row['relevant_aces']: print(a['sid'],a['mask'],a['flags'],a['qualifier'])
full=json.loads((base/'file-ancestor-metadata.json').read_text(encoding='utf-8-sig'))
for row in full['records']:
    if row['path'] in ['D:\\','D:\\作品集','C:\\Users\\yqyyds']:
        print('FULL_ACL',row['path'],json.dumps(row['acl'],ensure_ascii=False))
own=pathlib.Path(__file__).parent
for id in ['W01','W02']:
    obj=json.loads((own/(id+'-raw.json')).read_text(encoding='utf-8'))
    text=json.dumps(obj,ensure_ascii=False)
    for term in ['PROCESS_QUERY','ERROR_NOT_FOUND','READ_CONTROL','Owner Rights','WRITE_DAC']:
        idx=text.find(term)
        if idx>=0: print(id,term,text[max(0,idx-160):idx+350])
