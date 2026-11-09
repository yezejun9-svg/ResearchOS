import json
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");E=R/'execution/v2.4/receipts/W05/W05-99/source43_b_stop_finalpath_codex/20261025-current-chat'
for name in ['FINAL-manifest.json','source43-files.json','command-index.json']:
 v=json.loads((E/name).read_text(encoding='utf8'))
 if name=='FINAL-manifest.json':out={k:v[k]for k in ['builds','evidence','authority']}
 elif name=='source43-files.json':out=(v[:2] if isinstance(v,list)else {k:(x[:1] if isinstance(x,list)else x)for k,x in v.items()})
 else:out={'source':v.get('source'),'capture_boundary':v.get('capture_boundary'),'sample':v['recorded_commands'][:2]}
 print(json.dumps({'file':name,'content':out},ensure_ascii=False,indent=2))
v=json.loads((E/'claim-test-matrix.json').read_text(encoding='utf8'))
print(json.dumps({'matrix':[{'receipt':x['receipt'],'exit':x['native_exit'],'pass':len(x['pass_events']),'fail':len(x['fail_events']),'skip':len(x['skip_events'])}for x in v['results']]},ensure_ascii=False))
