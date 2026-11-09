import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE/'product-v1-owned-verification-20261104'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=BASE/'MANIFEST.json';assert sha(manifest)=='63c53c61e9e05bd387f643e2e34c7a9969b0dfbe3b0673bf30e88691de6db768'
m=json.loads(manifest.read_bytes());assert m['construction_frozen'] and not m['source_modification_permitted']
results=[]
for item in m['files']:
 path=BASE/item['path'];assert sha(path)==item['sha256'],item['path']
 if path.name=='RESULT.json':
  r=json.loads(path.read_bytes());assert r['stop_proved'] and r['job_assigned'] and r['resumed'] and not r['errors']
  assert r['root_signaled'] and r['job_active_zero'] and r['close_order'][0]=='job' and not r['automatic_retry']
  results.append(dict(scope_id=r['scope_id'],status=r['status'],total_processes=r['job_total_processes'],root_exit_code=r['root_exit_code'],sha256=item['sha256']))
assert len(results)==5
source=(BASE/'owned_run.py').read_text(encoding='utf8');assert sha(BASE/'owned_run.py')==m['controller_sha256']
assert source.index('k.assign(job, pi.hProcess)')<source.index('k.resume(pi.hThread)')
assert 'OpenProcess' not in source and 'taskkill' not in source
decision=dict(schema='researchos.root-owned-supervisor-review/1',reviewer='codex:/root',author='codex:/root/runtime_readiness',decision='APPROVED_FOR_SEPARATELY_SCOPED_BOUNDED_BUILD_AND_GUI',manifest_sha256=sha(manifest),controller_sha256=m['controller_sha256'],verified_files=len(m['files']),verified_fresh_fixture_results=results,review='Full controller source inspected: suspended creation, explicit inherited handles, assign+membership before resume, original-handle fallback, bounded monitor/cleanup, Job close before raw processing, consumed exact scope and explicit environment. Existing five scopes remain consumed and were not rerun.',conditions=['Exact new Root command/scope and all executable/input hashes required','New source-bound build and fresh owned state only','GUI wrapper must handle normal graceful close inside deadline; Job is outer fail-safe','Job is process/resource ownership, not filesystem/network sandbox; native Harness permissions still need actual independent verification'],product_acceptance_increment=0,actual_product_build_gui_model='NOT_RUN')
dest=HERE/'product-v1-owned-supervisor-root-review.json';assert not dest.exists();dest.write_bytes((json.dumps(decision,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
print(json.dumps(dict(review_sha256=sha(dest),files=len(m['files']),fixture_results=results,product_acceptance_increment=0)))
