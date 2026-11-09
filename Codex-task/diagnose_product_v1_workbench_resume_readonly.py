"""Run only the immutable resume preconditions, ending before every mutation."""
import contextlib,hashlib,json,sys,traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent;source=HERE/'resume_product_v1_workbench_newline_integration.py';out=HERE/'product-v1-workbench-newline-resume-readonly-diagnostic-01'
assert not out.exists() and hashlib.sha256(source.read_bytes()).hexdigest()=='64b4cd34cdab8b0272d25a769af7b5d3dc8311d39d90d38f3a206084630011ce'
text=source.read_text(encoding='utf8');boundary='now=datetime.now(timezone.utc).isoformat();rev=cp[\'revision\']+1;resume.mkdir();';assert text.count(boundary)==1;prefix=text.split(boundary,1)[0]
assert not any(line.startswith(('resume.mkdir','(wt/JSX).write_bytes','commit=git(')) for line in prefix.splitlines())
out.mkdir();(out/'reviewed-source.py').write_bytes(source.read_bytes());sys.argv=[str(source),'--review-ref','execution/product-v1/receipts/single-harness-20261104/workbench-assistant-refinement/newline-amendment-reviewed/researchos-workbench-assistant-newline-amended-review-20261105/review.json','--review-sha','4a79141a4c140828486a48b79547844b8e78f6851a8b20214f5433ac159bd4be']
ok=False;error=None
with (out/'stdout.raw').open('w',encoding='utf8') as stdout,(out/'stderr.raw').open('w',encoding='utf8') as stderr:
 with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
  try:exec(compile(prefix,str(source),'exec'),{'__file__':str(source),'__name__':'__main__'});ok=True
  except BaseException as exc:error=type(exc).__name__;traceback.print_exc()
result=dict(status='PRECONDITIONS_PASS_NO_D_MUTATION' if ok else 'PRECONDITION_FAILED_NO_D_MUTATION',exception=error,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),mutations_to_D=0,actual_models=0)
(out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps(result));raise SystemExit(0 if ok else 1)
