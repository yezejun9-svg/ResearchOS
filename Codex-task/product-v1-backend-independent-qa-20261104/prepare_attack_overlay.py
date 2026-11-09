from pathlib import Path
import hashlib,json
here=Path(__file__).resolve().parent
run=here/'run-01'
inputs=json.loads((run/'inputs.json').read_bytes())
wt=Path(inputs['worktree'])
replace={}
for name,pin in inputs['source'].items():
    source=run/'frozen-source'/name
    assert hashlib.sha256(source.read_bytes()).hexdigest()==pin['sha256']
    replace[str(wt/name)]=str(source)
extra=run/'independent_driver_test.go'
replace[str(wt/'adapters/runtime/independent_harness_boundary_test.go')]=str(extra)
target=run/'overlay.json'
assert not target.exists()
target.write_text(json.dumps({'Replace':replace},ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'source_files':18,'extra_tests':1,'overlay_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'test_sha256':hashlib.sha256(extra.read_bytes()).hexdigest()}))
