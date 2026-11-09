import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=Path('D:/作品集/ResearchOS/research-os');WT=ROOT/'.local/worktrees/product-v1-native-preparation-wiring-20261105';B3=HERE/'product-v1-native-qualification-producer-author-20261105-rev4';OWNER=HERE/'product-v1-native-preparation-wiring-author-20261105-rev3';OUT=HERE/'product-v1-native-preparation-test02-rev3-overlay';assert not OUT.exists()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(B3/'MANIFEST.json')=='522a562016d0b94ea4576d956106b08068bbf47449b6f9de01683d12b709b2b2' and sha(OWNER/'MANIFEST.json')=='4d959c6f8002b9cb154da7c7d30108e181c93214df768627b8754935a5c9adc2'
for ref,row in json.loads((OWNER/'MANIFEST.json').read_bytes())['paths'].items():assert sha(WT/ref)==row['source_sha256'],ref
replace={}
for row in json.loads((B3/'MANIFEST.json').read_bytes())['files']:
 ref=row['path'];f=B3/'source'/ref;assert sha(f)==row['source_sha256'];replace[str(WT/ref)]=str(f)
assert len(replace)==8;OUT.mkdir();p=OUT/'overlay.json';p.write_bytes((json.dumps(dict(Replace=replace),indent=2)+'\n').encode('utf8'));print(json.dumps(dict(overlay=str(p),sha256=sha(p),status='SOURCE_ONLY_NOT_EXECUTED')))
