import hashlib,json,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
OUT=HERE/'product-v1-workbench-refinement-tests02-evidence'
RUN=HERE/'product-v1-owned-verification-20261104/runs/product-v1-workbench-refinement-tests-02'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
assert not OUT.exists();r=read(RUN/'RESULT.json')
assert r['root_exit_code']==0 and r['job_active_zero'] and r['stop_proved'] and not r['input_drift'] and not r['timed_out'] and not r['terminate_job_attempts']
assert r['scope_sha256']=='9839c06caacfdc786313f0a7523b075e84726e16048983257bb958491b9369a1'
for item in r['raw']:assert sha(RUN/item['file'])==item['sha256']
text=(RUN/'stdout.raw').read_text(encoding='utf8');assert '\u2139 pass 71' in text and '\u2139 fail 0' in text and '\u2139 skipped 0' in text
OUT.mkdir();sources=[(p,'run/'+p.name) for p in RUN.iterdir() if p.is_file()]
sources += [(HERE/'product-v1-owned-verification-20261104/scopes/product-v1-workbench-refinement-tests-02.json','scope.json'),(HERE/'register_product_v1_workbench_refinement_tests02.py','register_product_v1_workbench_refinement_tests02.py')]
freeze=HERE/'product-v1-workbench-assistant-refinement-20261105-freeze-02'
sources += [(p,'freeze02/'+p.relative_to(freeze).as_posix()) for p in freeze.rglob('*') if p.is_file()]
for p,ref in sources:
 dest=OUT/ref;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest);assert sha(p)==sha(dest)
summary=dict(status='TESTS_PASS_SOURCE_REVIEW_REVISIONS_REQUIRED',scope_sha256=r['scope_sha256'],tests=71,pass_count=71,fail=0,skipped=0,job_total_processes=r['job_total_processes'],job_active_zero=True,stop_proved=True,force_termination=0,new_native_model_calls=0,geometry='NOT_RUN',review_findings=['Successful submit followed by cancel keeps previous submit ACK and can mislabel cancel errors as read errors; needs real send-to-cancel regression'],next='Exact6 owner fixes independently found combinations and freezes revision03; fresh scope only after source change, no replay of old real Task or tests02.',formal_increment=0,product_acceptance_increment=0)
(OUT/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8');shutil.copyfile(__file__,OUT/Path(__file__).name)
files=[dict(path=p.relative_to(OUT).as_posix(),sha256=sha(p)) for p in sorted(OUT.rglob('*')) if p.is_file()]
selection=OUT/'archive-file-list.json';selection.write_text(json.dumps(dict(root=str(OUT),files=files),indent=2)+'\n',encoding='utf8');print(json.dumps(dict(selection=str(selection),sha256=sha(selection),files=len(files),summary=summary)))
