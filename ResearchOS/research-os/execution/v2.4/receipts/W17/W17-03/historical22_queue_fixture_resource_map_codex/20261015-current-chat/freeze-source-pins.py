"""Add the complete 502-file path/size/hash inventory without changing prior receipts."""
import hashlib
import json
from pathlib import Path

ROOT=Path('D:/作品集/ResearchOS/research-os')
HERE=Path(__file__).resolve().parent
OLD=ROOT/'execution/v2.4/receipts/W05/W05-99/host_configuration_upgrade_executor_codex/old22-build-40e94f3f6e53442fa07068089c0de64a'

def ref(path):
    raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def save(name,value):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,ensure_ascii=False,indent=2)
        f.write('\n')

manifest=json.loads((OLD/'git_source.json').read_bytes())
root=OLD/'frozen_source'
files=[]
for name,expected in sorted(manifest['files'].items()):
    item=ref(root/name)
    if item['sha256']!=expected:
        raise RuntimeError('source22 pin drift '+name)
    files.append({'relative_path':name,**item})
if len(files)!=502:
    raise RuntimeError('wrong selected source count')
save('SOURCE-PINS-502.json',{'schema':'researchos.historical22-selected-source-pins/1',
     'commit_claim_from_prior_archive':'396287cc5427eb125aaedb8a2b7fadf63e6b9322',
     'archive_manifest':ref(OLD/'git_source.json'),'count':len(files),
     'files':files,'formal_increment':0})
save('RESOURCE-MAP-ADDENDUM.json',{'schema':'researchos.historical22-resource-map-addendum/1',
     'base_map':ref(HERE/'RESOURCE-MAP.json'),
     'complete_selected_source_pins':ref(HERE/'SOURCE-PINS-502.json'),
     'clarification':'Complete current path/byte/hash inventory for all 502 selected frozen source files; base map holds representative pins and full archive/manifests.',
     'formal_increment':0})
print(json.dumps({'source_files':len(files),
                  'source_pins':ref(HERE/'SOURCE-PINS-502.json'),
                  'addendum':ref(HERE/'RESOURCE-MAP-ADDENDUM.json')},ensure_ascii=False))
