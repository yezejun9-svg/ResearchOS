"""Copy byte-exact frozen rules after root ownership registration."""
from pathlib import Path
import hashlib
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
scope=json.loads((HERE/'source_scope_codex.json').read_bytes())
paths=json.loads((ROOT/'execution/v2.4/path_ownership.json').read_bytes())
assert paths['revision']==49
assert paths['card_path_bindings']['W04-99']['source_scope']['sha256']==sha(HERE/'source_scope_codex.json')
source=ROOT/scope['frozen_rules']['source']['path'];manifest=ROOT/scope['frozen_rules']['manifest']['path']
assert sha(source)==scope['frozen_rules']['source']['sha256']
assert sha(manifest)==scope['frozen_rules']['manifest']['sha256']
raw_target=ROOT/'internal/domain/contracts/new-project-rules-v24.md'
meta_target=ROOT/'internal/domain/contracts/new-project-rules-v24.json'
assert not raw_target.exists() and not meta_target.exists()
with raw_target.open('xb') as f: f.write(source.read_bytes())
metadata={'schema':'researchos.embedded-project-rules-source.v1','source_path':source.name,'rules_version':'1.1','package_version':'2.4.0',
    'package_manifest_sha256':sha(manifest),'sha256':sha(source),'size_bytes':len(source.read_bytes())}
with meta_target.open('x',encoding='utf-8',newline='\n') as f:
    json.dump(metadata,f,ensure_ascii=False,indent=2);f.write('\n')
assert raw_target.read_bytes()==source.read_bytes() and len(raw_target.read_bytes())==12952
with (HERE/'rules_asset_copy_codex.json').open('x',encoding='utf-8',newline='\n') as f:
    json.dump({'status':'PASS_BYTE_EXACT_FROZEN_RULES_COPY','actor':'codex:/root','scope_sha256':sha(HERE/'source_scope_codex.json'),
        'source':scope['frozen_rules'],'assets':{p.relative_to(ROOT).as_posix():sha(p) for p in [raw_target,meta_target]},
        'original_manifest_unchanged':sha(manifest)==scope['frozen_rules']['manifest']['sha256'],'formal_case_count_delta':0},f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'status':'PASS_BYTE_EXACT_RULES_ASSETS','rules_sha256':sha(raw_target),'metadata_sha256':sha(meta_target),'bytes':12952}))
