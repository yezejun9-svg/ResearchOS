import hashlib, json, pathlib
repo = pathlib.Path('D:/作品集/ResearchOS/research-os')
scope = json.loads((repo / 'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp519/boot-supplement-independent-design-review-scope.json').read_text(encoding='utf-8-sig'))
for i in [0,5,8]:
    item=scope['inputs'][i]; obj=json.loads((repo/item['path']).read_text(encoding='utf-8-sig'))
    print('MANIFEST', i, 'KEYS', list(obj))
    for key,val in obj.items():
        if isinstance(val,list):
            print(key, json.dumps(val,ensure_ascii=False))
        elif not isinstance(val,dict): print(key,val)
for i in [7,10]:
    item=scope['inputs'][i]; obj=json.loads((repo/item['path']).read_text(encoding='utf-8-sig'))
    print('SCOPE',i)
    if i==7: print(json.dumps(obj,ensure_ascii=False,indent=2))
    else:
        print(json.dumps({k:v for k,v in obj.items() if k not in ['inputs','copied_findings']},ensure_ascii=False,indent=2))
