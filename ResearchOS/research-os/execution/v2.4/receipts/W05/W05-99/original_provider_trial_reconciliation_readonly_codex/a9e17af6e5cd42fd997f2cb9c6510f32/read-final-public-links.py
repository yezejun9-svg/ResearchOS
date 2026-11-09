import sys
sys.dont_write_bytecode=True
import importlib.util
import json
from pathlib import Path
import re
import traceback

Q=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('trial_public_guard',Q/'guard-library.py')
lib=importlib.util.module_from_spec(spec)
spec.loader.exec_module(lib)

def refs(value,pointer=''):
    result=[]
    if lib.public_ref(value):
        result.append({'pointer':pointer,'ref':{k:value[k] for k in ('path','sha256','bytes')}})
    if isinstance(value,dict):
        for key,child in value.items():
            result.extend(refs(child,pointer+'/'+str(key)))
    elif isinstance(value,list):
        for index,child in enumerate(value):
            result.extend(refs(child,pointer+'/'+str(index)))
    return result

def main():
    guard=lib.Guard()
    finished=False
    try:
        discovery=json.loads((Q/'discovery.json').read_text(encoding='utf-8'))
        rows=discovery['registered_relevant_public_refs']
        entry=next(v for v in rows if '/work_in_progress/mu_sdk_runner_v9_handoff_ref' in v['checkpoint_pointers'])
        raw,actual=guard.read(lib.normalize(entry['registered_ref']['path']),entry['registered_ref'])
        value=json.loads(raw.decode('utf-8'))
        links=refs(value)
        detail=json.loads((Q/'trial-detail-safe-metadata.json').read_text(encoding='utf-8'))
        coordinator_ref={'path':'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_root_coordinator_source_v5_codex/14882883e85f4e849eb087a01800e22d/root_coordinator.py','sha256':'12a7c6e78b80a56860ecdef97d29460322bdaeede17be22d3c171dbd6b35ea9a','bytes':55715}
        craw,cref=guard.read(coordinator_ref['path'],coordinator_ref)
        lines=craw.decode('utf-8').splitlines()
        excerpts=[]
        for index,line in enumerate(lines):
            if re.search(r'host.?capt|request.?count|provider_requests|billing|stderr|stdout|capture_dir|runtime_transcript|root-coordinator.lifecycle',line,re.I):
                excerpts.append({'line':index+1,'text':line.strip()[:500]})
        result={'schema':'researchos.original-trial-final-public-links.v1','authority':'NONE','runner_v9_handoff_ref':actual,'runner_v9_top_level_keys':sorted(value),'runner_v9_linked_public_refs':links,'actual_trial_coordinator_source_ref':cref,'coordinator_public_capture_selectors':excerpts,'account_model_requests':0,'private_reads':0}
        result_ref=lib.save('final-public-links.json',result)
        closed=guard.close();finished=True
        closed_ref=lib.save('final-public-links-source-guard.closed.json',closed)
        print(json.dumps({'result_ref':result_ref,'guard_ref':closed_ref,'runner_v9_linked_public_refs':links,'coordinator_public_capture_selectors':excerpts},ensure_ascii=False))
    finally:
        if not finished:
            for stream in guard.held:
                stream.close()

code=0
try:
    main()
except Exception:
    traceback.print_exc()
    code=1
print('ROOT_PYTHON_EXIT='+str(code))
sys.exit(code)
