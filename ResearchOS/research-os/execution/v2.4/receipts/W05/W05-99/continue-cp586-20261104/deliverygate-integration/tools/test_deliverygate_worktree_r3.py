import hashlib,json,os
from pathlib import Path
root=Path('D:/作品集/ResearchOS/research-os')
out=root/'execution/v2.4/receipts/W05/W05-99/continue-cp586-20261104/deliverygate-integration'
scopefile=out/'scope.json';scope_raw=scopefile.read_bytes();scope=json.loads(scope_raw);wt=Path(scope['worktree'])
test=wt/'internal/deliverygate/validate_test.go';before=test.read_bytes()
assert hashlib.sha256(before).hexdigest()==scope['files']['internal/deliverygate/validate_test.go']
assert before.count(b'researchos.local/pure-scalar-pilot')==1
(out/'scope.before-import-adaptation.json').write_bytes(scope_raw)
(out/'test.before-import-adaptation.go.txt').write_bytes(before)
after=before.replace(b'researchos.local/pure-scalar-pilot',b'researchos.local/research-os/internal/deliverygate')
test.write_bytes(after)
scope['files']['internal/deliverygate/validate_test.go']=hashlib.sha256(after).hexdigest()
scope['import_adaptation']={'test_only':'standalone C module import changed to actual product package import','implementation_unchanged':True,'old_sha256':hashlib.sha256(before).hexdigest(),'new_sha256':hashlib.sha256(after).hexdigest(),'failed_checks02_preserved':True,'go_tests_executed_in_checks02':0,'network':False}
tmp=scopefile.with_name(scopefile.name+'.new');tmp.write_text(json.dumps(scope,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(tmp,scopefile)
(out/'import-adaptation.json').write_text(json.dumps(scope['import_adaptation'],indent=2)+'\n',encoding='utf-8')
source=Path(__file__).with_name('test_deliverygate_worktree.py').read_text(encoding='utf-8')
source=source.replace("target=out/'checks-01'","target=out/'checks-03'").replace("private=wt/'.local/deliverygate-checks-01';private.mkdir()","private=wt/'.local/deliverygate-checks-03';private.mkdir(parents=True)")
source=source.replace("'GOSUMDB':'off'","'GOSUMDB':'off','GOMODCACHE':str(root/'.local/tools/gopath/pkg/mod')")
exec(compile(source,'test_deliverygate_worktree_r3.generated','exec'))
