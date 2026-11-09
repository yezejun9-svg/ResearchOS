"""Finite public Source/schema metadata only. No Canon or SQL/process call."""
import json, sys
from pathlib import Path
B=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99')
bound_path=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/old21.programme.qualification.bound.actual.root.json')
bound=json.loads(bound_path.read_bytes())
result={'bound_schema':bound['schema'],'root_payload':json.loads(Path(bound['payload_ref']['path']).read_bytes())}
binding=json.loads(Path(bound['root_issuance_binding_ref']['path']).read_bytes())
rows=[json.loads(x) for x in Path(binding['original_capture_ref']['path']).read_bytes().splitlines()]
texts=rows[-1]['payload']['output']
for x in texts:
    try:host=json.loads(x['text'])
    except (ValueError,KeyError):continue
    if type(host) is dict and type(host.get('output')) is str:
        for line in host['output'].splitlines():
            try:typed=json.loads(line)
            except ValueError:continue
            if type(typed) is dict and 'observer_input_ref' in typed:
                obj=json.loads(Path(typed['observer_input_ref']['path']).read_bytes())
                result['observer_input_ref']=typed['observer_input_ref'];result['observer_input_keys']=sorted(obj)
                result['observer_input_public_scalars']={k:v for k,v in obj.items() if type(v) in (str,int,bool) or v is None}
                result['observer_input_lists']={k:{'count':len(v),'first_keys':sorted(v[0]) if v and type(v[0]) is dict else None} for k,v in obj.items() if type(v) is list}
tp=B/'mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py'
result['tp_source']=tp.read_text(encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,sort_keys=True))
print('ROOT_PYTHON_EXIT=0')
