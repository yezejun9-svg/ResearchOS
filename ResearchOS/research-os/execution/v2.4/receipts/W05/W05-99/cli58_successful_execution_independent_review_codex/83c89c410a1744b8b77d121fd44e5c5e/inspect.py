import json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99';U='0e298790cd484ec9ba319a379e7e34ed';E=P/'cli58_fresh_compiler_executor_codex'/U;O=Path(__file__).parent
out={}
for name in ['compiled-closure.json','after-finally.vector.json','build-cli.invocation.json','case-00.invocation.json','go-graph.actual.json','test2json-graph.actual.json']:
 d=json.loads((E/name).read_bytes());out[name]={'keys':list(d),'sizes':{k:len(v) if isinstance(v,(list,dict)) else v for k,v in d.items()}}
 if name.endswith('invocation.json'):
  q=d['result']['debug_capture'];out[name]={'keys':list(d),'debug_keys':list(q),'module_sample':q['modules'][:1],'generation_sample':q['process_generations'][:1]}
 if name=='compiled-closure.json':out[name]['artifact_refs']={k:d[k] for k in ['cli','testexe','test2json']}
save=O/'inspection.json'
with save.open('xb') as f:f.write((json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(out,ensure_ascii=False))
