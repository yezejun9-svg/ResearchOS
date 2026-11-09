import json,collections
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W13/W13-03';O=Path(__file__).parent
i=json.loads((P/'desktop58_finite_executor_codex/72ff32d0d24a42c4a8effd849d54f882/build-current58.invocation.json').read_bytes());d=i['result']['debug_capture'];c=[x for x in d['events'] if x['code']==3];e=[x for x in d['events'] if x['code']==5]
out={'create_first2':c[:2],'exit_first2':e[:2],'create_last':c[-1],'exit_last':e[-1],'PID_multiset_equal':collections.Counter(x['pid'] for x in c)==collections.Counter(x['pid'] for x in e),'unique_createPID':len(set(x['pid'] for x in c)),'create_fields':sorted(set(k for x in c for k in x)),'exit_fields':sorted(set(k for x in e for k in x))}
s=json.loads((R/'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r335-72ff32d0d24a42c4a8effd849d54f882/scope_registration.json').read_bytes());p=Path(s['debug_helper_ref']['path']);lines=p.read_text().splitlines();out['helper_ref']=s['debug_helper_ref'];out['source_snippets']=[{'line':n+1,'text':line} for n,line in enumerate(lines) if 'process_generation' in line or 'EXIT_PROCESS_DEBUG_EVENT' in line or 'exit_process_count' in line]
with (O/'event-identity.shape.json').open('xb') as f:f.write((json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(out,ensure_ascii=False))
