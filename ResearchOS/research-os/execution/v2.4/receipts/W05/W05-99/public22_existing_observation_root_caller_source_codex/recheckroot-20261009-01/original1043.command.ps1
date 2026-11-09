@'
import json,types
from pathlib import Path
p=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/public22_existing_observation_root_caller_source_codex/recheckroot-20261009-01/public22_recheck_root.source.py')
m=types.ModuleType('root_runtime_resource_check');m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__)
i=m.inputs();m.load(i['leaf_runner_ref'],'preload_leaf');m.load(m.TP_REF,'preload_TP');m.load(m.GUARD_REF,'preload_guard')
refs=m.runtime_refs(i)
result=m.save(p.parent,'runtime-closure-control.json',dict(status='PASS_SOURCE_ONLY',verified_resource_refs=refs,SQL_queries=0,new_native_children=0,actual_registration=False))
print(json.dumps(dict(status='PASS_SOURCE_ONLY',resource_count=len(refs),result_ref=result),ensure_ascii=False))
'@ | & 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe' -I -S -B -X utf8 -
