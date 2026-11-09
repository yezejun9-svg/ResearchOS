import hashlib,json
from pathlib import Path
E=Path(__file__).parent
def ref(p):
 b=p.read_bytes();return {'path':str(p.resolve()),'sha256':'sha256:'+hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=True,indent=2);f.write('\n')
for folder in [E.parent/'operation-wrapper-path-review',E]:
 report={'state':'PUBLIC_PATH_DIAGNOSIS_ONLY' if folder!=E else 'PUBLIC_READINESS_CASE02_PASS','evidence':ref(folder/('path-diagnosis.json' if folder!=E else 'review-result.json')),'reviewer':'native25_controller_review','limitations':['Case01 signer exit 1 stderr was discarded, so path rejection is a conditional causal diagnosis rather than direct sole-cause proof.','No private authority resources or product database read; no signing, publishing, serving, Root approval or fixture release.','Case01 consumed approval/failure retained; case02 readiness is not Native PASS or formal acceptance.'],'formal_increment':0,'formal_accepted':0,'formal_total':42,'open_parents':22}
 write(folder/'FINAL-report.json',report)
 pins=[ref(p) for p in sorted(folder.rglob('*')) if p.is_file() and p.name!='manifest.json']
 write(folder/'manifest.json',{'schema':'researchos.independent-public-evidence-manifest/1','files':pins,'file_count':len(pins)})
 print(json.dumps({'directory':str(folder),'report':ref(folder/'FINAL-report.json'),'manifest':ref(folder/'manifest.json'),'files':len(pins)}))
