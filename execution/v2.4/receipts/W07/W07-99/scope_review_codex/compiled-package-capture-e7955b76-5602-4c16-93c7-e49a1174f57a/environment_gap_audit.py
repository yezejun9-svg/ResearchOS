import hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[6]
BASE=ROOT/'execution/v2.4/receipts/W07/W07-99/source_executor_codex'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
fixture=BASE/'run-bd622ff64a7948a68d8b236c83d1e06a/source-before.json'
live=BASE/'run-c495292dee2d4e4fba7bb11a06979907/source-before.json'
a,b=load(fixture),load(live)
shared=set(a)&set(b);changed=[p for p in shared if a[p]!=b[p]]
only_a=sorted(set(a)-set(b));only_b=sorted(set(b)-set(a))
assert len(a)==1614 and len(b)==2256 and not changed and not only_a and len(only_b)==642
assert all(path.startswith('.local/gopath/') for path in only_b)
result={'mode':'READ_ONLY_RETAINED_DISPATCH_CAPTURE_VECTOR_COMPARISON','formal_acceptance':False,'network_calls':0,'fixture':ref(fixture),'LIVE':ref(live),'fixture_source_count':len(a),'LIVE_source_count':len(b),'shared_count':len(shared),'shared_hash_mismatches':changed,'fixture_only':only_a,'LIVE_only':[{'path':p,'sha256':b[p]} for p in only_b],'finding':'Native G01 and LIVE collection use different Go module-cache roots. Source collector includes dependencies when they fall under ROOT, so Go environment defaults change the frozen source identity even though every common file hash agrees. Missing GOPATH/GOCACHE must default consistently, while explicit nonempty environment remains authoritative. Old proofs are not repairable by editing their source manifests.'}
(OUT/'environment_gap_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'audit':ref(OUT/'environment_gap_audit.json'),'fixture':len(a),'LIVE':len(b),'missing_module_cache_files':len(only_b),'shared_hashes_equal':not changed}))
