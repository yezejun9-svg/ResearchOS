from pathlib import Path
import json,hashlib
root=Path('D:/作品集/ResearchOS/research-os')
out=root/'execution/v2.4/receipts/W05/W05-99/continue-cp586-20261104/deliverygate-integration'
original=Path(__file__).with_name('test_deliverygate_worktree.py')
raw=original.read_bytes()
record={'failure_origin':'deliverygate-worktree-test-harness-missing-parent-20261104','attempt_index':1,'tool_chunk':'a963be','python_exit':1,'go_test_executed':False,'error':'FileNotFoundError creating worktree .local/deliverygate-checks-01 because .local parent absent','controller_sha256':hashlib.sha256(raw).hexdigest(),'counter_reset':False}
file=out/'checks-01/controller-failed.json';assert not file.exists();file.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
source=raw.decode('utf-8').replace("target=out/'checks-01'","target=out/'checks-02'").replace("private=wt/'.local/deliverygate-checks-01';private.mkdir()","private=wt/'.local/deliverygate-checks-02';private.mkdir(parents=True)")
exec(compile(source,'test_deliverygate_worktree_r2.generated','exec'))
