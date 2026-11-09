import hashlib,json,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
OUT=HERE/'product-v1-workbench-refinement-tests03-evidence'
RUN=HERE/'product-v1-owned-verification-20261104/runs/product-v1-workbench-refinement-tests-03'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
assert not OUT.exists();r=read(RUN/'RESULT.json')
assert r['root_exit_code']==0 and r['job_active_zero'] and r['stop_proved'] and not r['input_drift'] and not r['timed_out'] and not r['terminate_job_attempts']
assert r['scope_sha256']=='db2a1a48bb989fab6edefc7cb012b3eee81fec4149629fa25a50863190b74300'
for item in r['raw']:assert sha(RUN/item['file'])==item['sha256']
text=(RUN/'stdout.raw').read_text(encoding='utf8');assert '\u2139 pass 73' in text and '\u2139 fail 0' in text and '\u2139 skipped 0' in text
OUT.mkdir();sources=[(p,'run/'+p.name) for p in RUN.iterdir() if p.is_file()]
sources += [(HERE/'product-v1-owned-verification-20261104/scopes/product-v1-workbench-refinement-tests-03.json','scope.json'),(HERE/'register_product_v1_workbench_refinement_tests03.py','register_product_v1_workbench_refinement_tests03.py')]
freeze=HERE/'product-v1-workbench-assistant-refinement-20261105-freeze-03'
sources += [(p,'freeze03/'+p.relative_to(freeze).as_posix()) for p in freeze.rglob('*') if p.is_file()]
for p,ref in sources:
 dest=OUT/ref;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest);assert sha(p)==sha(dest)
summary=dict(status='TESTS_PASS_INDEPENDENT_REVIEW_AND_VITE_PENDING',scope_sha256=r['scope_sha256'],tests=73,pass_count=73,fail=0,skipped=0,job_total_processes=r['job_total_processes'],job_active_zero=True,stop_proved=True,force_termination=0,new_native_model_calls=0,geometry='NOT_RUN',review_findings=[],next='Root bounded Vite, independent actual review, exact source integration then fresh complete Desktop14; geometry and model remain unverified, no oldTask replay.',formal_increment=0,product_acceptance_increment=0)
(OUT/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8');shutil.copyfile(__file__,OUT/Path(__file__).name)
files=[dict(path=p.relative_to(OUT).as_posix(),sha256=sha(p)) for p in sorted(OUT.rglob('*')) if p.is_file()]
selection=OUT/'archive-file-list.json';selection.write_text(json.dumps(dict(root=str(OUT),files=files),indent=2)+'\n',encoding='utf8');print(json.dumps(dict(selection=str(selection),sha256=sha(selection),files=len(files),summary=summary)))
