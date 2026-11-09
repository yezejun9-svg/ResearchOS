import hashlib,json,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent;OUT=HERE/'product-v1-workbench-refinement-vite01-evidence'
CONTROL=HERE/'product-v1-owned-verification-20261104';ID='product-v1-workbench-refinement-vite-01'
PREP=HERE/'product-v1-build14-prep-rev2-20261105/ui-vite-candidate';STAGE=PREP/'stage-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
assert not OUT.exists();sp=CONTROL/'scopes'/(ID+'.json');assert sha(sp)=='a67150bc8a73a83fd3312f4956f7e8328ae88bff244445a42542f69b67029f3c'
s=read(sp);r=read(CONTROL/'runs'/ID/'RESULT.json');v=read(STAGE/'RESULT.json');reg=read(PREP/'registration.json')
assert r['root_exit_code']==0 and r['job_active_zero'] and r['stop_proved'] and not r['input_drift'] and not r['timed_out'] and r['terminate_job_attempts']==0
assert v['status']=='BUILT_NOT_APP_OR_MODEL_TESTED' and v['exit_code']==0 and v['source_drift']==[] and v['module_closure_unchanged']
for item in s['inputs']:assert sha(Path(item['path']))==item['sha256'],item['path']
for item in r['raw']:assert sha(CONTROL/'runs'/ID/item['file'])==item['sha256']
for ref,digest in reg['sources_sha256'].items():assert sha(STAGE/ref)==digest
for item in v['outputs']:assert sha(STAGE/'apps/web/dist'/item['path'])==item['sha256']
OUT.mkdir();sources=[(sp,'scope.json')]
sources +=[(p,'owned-run/'+p.name) for p in (CONTROL/'runs'/ID).iterdir() if p.is_file()]
sources +=[(PREP/name,'prepared/'+name) for name in ['MANIFEST.json','README.md','register_ui_vite.py','run_ui_vite.py','registration.json']]
sources +=[(STAGE/name,'stage/'+name) for name in ['RESULT.json','vite.stdout.raw','vite.stderr.raw']]
sources +=[(STAGE/ref,'stage/'+ref) for ref in reg['sources_sha256']]
sources +=[(STAGE/'apps/web/dist'/item['path'],'stage/apps/web/dist/'+item['path']) for item in v['outputs']]
review=HERE/'product-v1-vite-rev2-independent-review-20261105';sources +=[(p,'prepared-independent-review/'+p.name) for p in review.iterdir() if p.is_file()]
sources +=[(HERE/'product-v1-build-inputs-20261104/repair-02/TARGET.readback.json','dependency-TARGET.readback.json')]
for p,ref in sources:
 dest=OUT/ref;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest);assert sha(dest)==sha(p)
summary=dict(status='VITE_BUILT_SOURCE_AND_DEPENDENCY_CLOSURE_UNCHANGED',scope_sha256=sha(sp),source_files=len(reg['sources_sha256']),dependency_files=365,outer_inputs=len(s['inputs']),outputs=v['outputs'],job_active_zero=True,job_total_processes=r['job_total_processes'],timeout=False,force=0,geometry='NOT_RUN',new_native_model_calls=0,formal_increment=0,product_acceptance_increment=0)
(OUT/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8');shutil.copyfile(__file__,OUT/Path(__file__).name)
files=[dict(path=p.relative_to(OUT).as_posix(),sha256=sha(p)) for p in sorted(OUT.rglob('*')) if p.is_file()];selection=OUT/'archive-file-list.json';selection.write_text(json.dumps(dict(root=str(OUT),files=files),indent=2)+'\n',encoding='utf8');print(json.dumps(dict(selection=str(selection),sha256=sha(selection),files=len(files),summary=summary)))
