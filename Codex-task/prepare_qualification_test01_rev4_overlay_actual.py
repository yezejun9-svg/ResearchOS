import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=Path('D:/作品集/ResearchOS/research-os');WT=ROOT/'.local/worktrees/product-v1-native-qualification-producer-20261105';B1=HERE/'product-v1-native-rpc-runtime-author-20261105/final-rev6';B3=HERE/'product-v1-native-qualification-producer-author-20261105-rev4';OUT=HERE/'product-v1-native-qualification-test01-rev4-overlay';assert not OUT.exists()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(B3/'MANIFEST.json')=='522a562016d0b94ea4576d956106b08068bbf47449b6f9de01683d12b709b2b2'
for row in json.loads((B3/'MANIFEST.json').read_bytes())['files']:assert sha(WT/row['path'])==row['source_sha256'],row['path']
src=json.loads((B1/'SOURCE.json').read_bytes());replace={}
for ref,row in src.items():
 if not ref.endswith('.go'):continue
 f=B1/'source'/Path(ref).name;assert sha(f)==row['source_sha256'];replace[str(WT/ref)]=str(f)
assert len(replace)==8;OUT.mkdir();p=OUT/'overlay.json';p.write_bytes((json.dumps(dict(Replace=replace),indent=2)+'\n').encode('utf8'));print(json.dumps(dict(overlay=str(p),sha256=sha(p),status='FROZEN_SOURCE_ONLY_NOT_EXECUTED')))
