import json,pathlib,hashlib
E=pathlib.Path(__file__).resolve().parent
p=E/'overlay.json';o=json.loads(p.read_text(encoding='utf-8'))
w=pathlib.Path('D:/作品集/ResearchOS/research-os/.local/worktrees/owned-core-stop-authority-r4-20261015')
extra=E/'independent_extra_windows_test.go'
o['Replace'][str(w/'ops/supervisor/independent_extra_windows_test.go')]=str(extra)
p.write_text(json.dumps(o,indent=2),encoding='utf-8')
print(json.dumps({'overlay':o,'extra_sha256':hashlib.sha256(extra.read_bytes()).hexdigest()},ensure_ascii=False,indent=2))
