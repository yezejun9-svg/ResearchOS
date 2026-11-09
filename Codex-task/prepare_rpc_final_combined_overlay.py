import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=Path('D:/作品集/ResearchOS/research-os');WT=ROOT/'.local/worktrees/product-v1-native-rpc-wiring-20261105';B1=HERE/'product-v1-native-rpc-runtime-author-20261105/final-rev6';B2=HERE/'product-v1-native-rpc-wiring-final-review-20261105';OUT=HERE/'product-v1-native-rpc-final-combined-overlay';assert not OUT.exists()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(B1/'ARCHIVE.json')=='1c57e9129d6dd0201ae5ac2e5f7dbb1190272cae9f5f55a03ae2c40d08f59cce' and sha(B1/'SOURCE.json')=='2ff361290390541633a08240c9ef430734ccd6c461087fc704645686807bc7c0'
src=json.loads((B1/'SOURCE.json').read_bytes());replace={}
for ref,row in src.items():
 if not ref.endswith('.go'):continue
 f=B1/'source'/Path(ref).name;assert sha(f)==row['source_sha256'];replace[str(WT/ref)]=str(f)
assert len(replace)==8
r=json.loads((B2/'review-report.json').read_bytes());assert r['decision']=='APPROVED_SOURCE_FIXTURE_ONLY'
for ref,digest in r['source_sha256'].items():assert sha(WT/ref)==digest,ref
OUT.mkdir();p=OUT/'overlay.json';p.write_bytes((json.dumps(dict(Replace=replace),indent=2)+'\n').encode('utf8'));print(json.dumps(dict(overlay=str(p),sha256=sha(p),b1_source='final-rev6',b2_source_files=len(r['source_sha256']),status='SOURCE_PREPARED_NO_EXECUTION')))
