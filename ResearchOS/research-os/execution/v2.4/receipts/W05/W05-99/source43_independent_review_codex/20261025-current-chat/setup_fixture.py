import pathlib,json
base=pathlib.Path('C:/Users/yqyyds/.codex/researchos-fixture-cache/source43-independent-review-20261025')
assert not base.exists(),'fresh fixture owner root required'
base.mkdir()
for name in ['tmp','gocache','bin','roots']:(base/name).mkdir()
(base/'OWNER.json').write_text(json.dumps({'owner':'codex:/root/source43_independent_review_20261025','source':'085b4711afe0c1288448b174eef24ecd5af0551b'}),encoding='utf-8')
print(base)
