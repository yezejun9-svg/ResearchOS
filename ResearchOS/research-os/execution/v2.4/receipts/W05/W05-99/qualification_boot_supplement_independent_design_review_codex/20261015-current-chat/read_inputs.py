import hashlib, json, pathlib, sys
repo = pathlib.Path('D:/作品集/ResearchOS/research-os')
scope_path = repo / 'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp519/boot-supplement-independent-design-review-scope.json'
scope = json.loads(scope_path.read_text(encoding='utf-8-sig'))
selected = [int(x) for x in sys.argv[1:]]
for i, entry in enumerate(scope['inputs']):
    path = repo / entry['path']
    raw = path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    print(json.dumps({'input_index': i, 'path': entry['path'], 'bytes': len(raw), 'sha256': actual, 'match': actual == entry['sha256'] and len(raw) == entry['bytes']}, ensure_ascii=False))
    if actual != entry['sha256'] or len(raw) != entry['bytes']:
        raise SystemExit('FROZEN INPUT MISMATCH')
    if i in selected:
        print(raw.decode('utf-8-sig'))
