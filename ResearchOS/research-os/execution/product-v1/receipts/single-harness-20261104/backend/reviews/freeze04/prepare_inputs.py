from pathlib import Path
import hashlib, json

root = Path('D:/作品集/ResearchOS/research-os')
out = Path(__file__).resolve().parent
scope = root/'execution/product-v1/receipts/single-harness-20261104/backend/scope.json'
interface = root/'execution/product-v1/contracts/harness.v1.interface.rev2.json'
decision = root/'execution/product-v1/receipts/single-harness-20261104/interface-root-decision.rev2.json'

def pin(p):
    raw=p.read_bytes()
    return {'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}

expected='046a49b2b1f82593fe86924913b2ee4d77152ac1cef7dbbb86562f6dfe0cfa1c'
assert pin(interface)['sha256']==expected
doc=json.loads(interface.read_bytes())
sc=json.loads(scope.read_bytes())
assert doc['contract_revision']==2
assert len(sc['production_paths'])==13 and len(sc['test_paths'])==5
inputs={}
for name,p in [('scope.json',scope),('interface.rev2.json',interface),('interface-decision.rev2.json',decision)]:
    target=out/'prepared-inputs'/name
    assert not target.exists(), 'Never overwrite prepared input: '+str(target)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(p.read_bytes())
    inputs[name]={'source':str(p),**pin(target)}
for name in ['SubmitRequest','CancelRequest','TaskData','EventsData','Event','Task','CapabilitiesResponse']:
    definition=doc['$defs'].get(name)
    if definition is not None:
        inputs['definition:'+name]=definition
inputs['source_candidate_read']=False
inputs['tests_run']=0
inputs['formal_increment']=0
manifest=out/'prepared-inputs.json'
assert not manifest.exists()
manifest.write_text(json.dumps(inputs,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'prepared':True,'manifest':str(manifest),**pin(manifest),'interface_sha256':expected,'definition_names':list(doc['$defs'])},ensure_ascii=True))
