import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=Path('D:/作品集/ResearchOS/research-os');WT=ROOT/'.local/worktrees/product-v1-build-11-20261105';BUNDLE=WT/'.local/desktop-v1-build-11';CONTROL=HERE/'product-v1-owned-verification-20261104';RUN=HERE/'product-v1-layout-visual-中文-run-05';OUT=HERE/'product-v1-visual05-root-postcheck';assert not OUT.exists()
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=read(BUNDLE/'development-manifest.json');reg=read(ROOT/'execution/product-v1/receipts/single-harness-20261104/build11-scope/registration.json')
assert sha(BUNDLE/'development-manifest.json')=='cb46a998a2c6f96c1c4f6a202d1f155a323f90ebbf1b981c63ced3560fbeab28'
assert m['source']['head']==reg['main_head']=='c3c7812347bb72930365fbb5db0efee8a965bc78' and not m['source']['candidate_delta']
for row in m['files']:assert sha(BUNDLE/row['path'])==row['sha256'],row['path']
assert {p.relative_to(BUNDLE).as_posix() for p in BUNDLE.rglob('*') if p.is_file()}=={r['path'] for r in m['files']}|{'development-manifest.json'}
for ref,digest in reg['source_sha256'].items():assert sha(WT/ref)==digest
outer=read(CONTROL/'runs/product-v1-layout-visual-05/RESULT.json');assert outer['root_exit_code']==0 and outer['job_active_zero'] and outer['stop_proved'] and not outer['errors'] and not outer['input_drift'] and not outer['terminate_job_attempts']
inner=read(RUN/'receipts/result.json');visual=read(RUN/'receipts/workbench-responsive-visual.json');assert visual['status']=='PASS_MEASURED_VISUAL_GEOMETRY' and visual['model_outcome']=='NOT_RUN_ZERO_BUDGET'
out=dict(status='ROOT_POSTCHECK_PASS_INDEPENDENT_ACTUAL_REVIEW_PENDING',source_head=reg['main_head'],bundle_files_verified=len(m['files']),source_pins_verified=len(reg['source_sha256']),bundle_manifest_sha256=sha(BUNDLE/'development-manifest.json'),core_sha256=sha(BUNDLE/'apps/desktop/resources/control/researchos-control.exe'),extra_bundle_files=[],outer_scope=outer['scope_sha256'],processes=outer['job_total_processes'],elapsed_seconds=outer['elapsed_seconds'],stop_proved=True,forced=False,scenarios=len(visual['scenarios']),screenshots=len(list((RUN/'screenshots').glob('*.png'))),task_submissions=0,model_calls=0,formal_increment=0,product_increment=0)
OUT.mkdir();(OUT/'POSTCHECK.json').write_bytes((json.dumps(out,indent=2)+'\n').encode('utf8'))
files=[Path(__file__),OUT/'POSTCHECK.json']+[p for p in (RUN/'receipts').iterdir() if p.is_file()]+list((RUN/'screenshots').glob('*.png'))+[CONTROL/'runs/product-v1-layout-visual-05'/n for n in ('RESULT.json','stdout.raw','stderr.raw')]+[CONTROL/'runs/product-v1-layout-visual-04'/n for n in ('RESULT.json','stdout.raw','stderr.raw')]
sel=HERE/'product-v1-visual05-root-archive-selection.json';assert not sel.exists();sel.write_bytes((json.dumps(dict(root=str(HERE),files=[dict(path=p.relative_to(HERE).as_posix(),sha256=sha(p)) for p in files]),indent=2)+'\n').encode('utf8'));print(json.dumps(dict(postcheck=out,selection=str(sel),selection_sha256=sha(sel))))
