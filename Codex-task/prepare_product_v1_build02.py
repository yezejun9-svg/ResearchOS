import argparse,hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');HERE=Path(__file__).resolve().parent;CONTROL=HERE/'product-v1-owned-verification-20261104';OUT=ROOT/'execution/product-v1/receipts/single-harness-20261104/build-scope'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def put(p,v):
 assert not p.exists();p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
p=argparse.ArgumentParser();p.add_argument('--web-modules',required=True);p.add_argument('--web-manifest',required=True);p.add_argument('--web-manifest-sha',required=True);a=p.parse_args()
oldresult=read(CONTROL/'runs/product-v1-build-01/RESULT.json');assert oldresult['status']=='CHILD_NONZERO_STOPPED' and oldresult['stop_proved'] and not oldresult['errors'] and not oldresult['input_drift']
original=read(OUT/'registration.json');WT=Path(original['clean_worktree']);assert original['main_head']=='7006360ad46ce384993b008fe61878195b74b9bf'
cmd=['git','-c','gc.auto=0','-c','maintenance.auto=false','--no-optional-locks']
assert subprocess.check_output(cmd+['rev-parse','HEAD'],cwd=WT).decode().strip()==original['main_head']
assert not subprocess.check_output(cmd+['status','--porcelain=v1'],cwd=WT).strip()
for ref,digest in original['source_sha256'].items():assert sha(WT/ref)==digest and sha(ROOT/ref)==digest
web=Path(a.web_modules).resolve();manifest=Path(a.web_manifest);assert web.name=='node_modules' and web.is_relative_to(ROOT/'.local/product-v1-build-inputs-20261104/web-node_modules-02') and web.is_dir() and sha(manifest)==a.web_manifest_sha
scope=read(CONTROL/'scopes/product-v1-build-01.json');argv=list(scope['argv']);bundle=WT/'.local/desktop-v1-build-02';receipts=OUT/'producer-02'
assert not bundle.exists() and not receipts.exists()
for flag,value in [('--web-modules',str(web)),('--output',str(bundle)),('--receipts',str(receipts))]:argv[argv.index(flag)+1]=value
scope.update(scope_id='product-v1-build-02',argv=argv,inputs=[v for v in scope['inputs'] if v['path']!=original['web_manifest']]+[dict(path=str(manifest),sha256=sha(manifest))])
for item in scope['inputs']:assert sha(Path(item['path']))==item['sha256']
sp=CONTROL/'scopes/product-v1-build-02.json';put(sp,scope)
registration=dict(status='REGISTERED_EXPLICIT_RETRY_NOT_EXECUTED',at=datetime.now(timezone.utc).isoformat(),retry_of='product-v1-build-01',same_origin_key='product-v1-webcache-missing-hoisted-rolldown',attempt_index=2,diagnosis_correction='All365 packages existed. Original physical cache basename web-node_modules broke Node realpath ancestor resolution. New physical container ends in true node_modules, with actual Vite entry resolution verified; no hoisted packages added and no old cache changed.',source_head=original['main_head'],source_sha256=original['source_sha256'],scope_path=str(sp),scope_sha256=sha(sp),bundle=str(bundle),producer_receipts=str(receipts),web_manifest=str(manifest),web_manifest_sha256=sha(manifest),old_result_sha256=sha(CONTROL/'runs/product-v1-build-01/RESULT.json'),old_scope_stays_consumed=True,real_model_or_gui=False,product_acceptance_increment=0)
put(OUT/'registration-02.json',registration);(OUT/'prepare_product_v1_build02.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps({k:registration[k] for k in ['status','scope_path','scope_sha256','source_head','bundle','attempt_index','same_origin_key']}))
