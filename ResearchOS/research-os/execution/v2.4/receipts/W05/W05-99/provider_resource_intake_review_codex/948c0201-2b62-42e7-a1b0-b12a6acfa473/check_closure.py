from pathlib import Path
import json,hashlib
ROOT=Path('D:/作品集/ResearchOS/research-os');D=Path(__file__).resolve().parent;P=ROOT/'execution/v2.4/receipts/W05/W05-99/provider_resource_intake_codex/20261006-opencode-go';F=P/'thinking-disabled-repair';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
proof=[]
for base in [P,F]:
 v=json.loads((base/'source-before.json').read_bytes());text=(base/'go-list-a3.stdout.raw').read_text(encoding='utf8');dec=json.JSONDecoder();offset=0;expected=set();packages=0
 while offset<len(text):
  while offset<len(text) and text[offset].isspace():offset+=1
  if offset==len(text):break
  row,offset=dec.raw_decode(text,offset);packages+=1;directory=Path(row['Dir'])
  for field in ['GoFiles','CgoFiles','EmbedFiles','CFiles','HFiles','SFiles','SysoFiles']:
   expected.update(str(directory/name) for name in row.get(field,[]))
  for mod in [row.get('Module',{}),row.get('Module',{}).get('Replace',{})]:
   if mod.get('GoMod'):expected.add(str(Path(mod['GoMod'])))
 absent=sorted(expected-set(v));assert not absent
 runtime=set(str(p) for path in [ROOT/'spec/v2.0/contracts',ROOT/'internal/api/contracts'] for p in path.glob('*.json'))|set(str(p) for p in (ROOT/'migrations/sqlite').glob('*.sql'))
 assert not runtime-set(v)
 sourcepath=[p for p in expected if '/.local/provider-resource' in p.replace('\\','/') and p.endswith('main.go')];assert len(sourcepath)==1 and sha(Path(sourcepath[0]))==sha(base/'intake/main.go')
 proof.append({'directory':str(base),'go_list_sha256':sha(base/'go-list-a3.stdout.raw'),'packages':packages,'selected_compiled_inputs':len(expected),'missing_selected':absent,'runtime_contract_and_sql_count':len(runtime),'missing_runtime_inputs':[],'published_source_equals_compiled_source':True,'source_sha256':sha(base/'intake/main.go')})
sources=[ROOT/p for p in ['internal/host/host.go','internal/host/native.go','internal/host/vault.go','internal/host/dpiapi_windows.go','internal/host/model_credential.go','internal/domain/store.go','internal/store/sqlite.go']]
r={'compiled_closure_recomputed_from_actual_go_list':proof,'source_review_refs':[{'path':str(p),'sha256':sha(p)} for p in sources],'review_public_docs_only':[{'url':'https://opencode.ai/docs/go/','supports':'deepseek-v4.1-flash endpoint /zen/go/v1/chat/completions, catalog /models, own User-Agent and stable x-opencode-session.'},{'url':'https://api-docs.deepseek.com/guides/thinking_mode/','supports':'Thinking defaults enabled/high; explicit thinking.type disabled controls the short access probe. Proxy behavior evidenced separately by actual returned usage.'}],'original_stdin_metadata_discrepancy':'intake.invocation.json stdin=AUTHORIZED_SECRET_PIPE_NOT_LOGGED is a legacy label. Executed source uses sys.stdin inherited console, GoGetConsoleMode+SetConsoleMode(ENABLE_ECHO_INPUT off), then readiness marker and bounded read; stdout contains marker only. No original metadata overwritten.'}
(D/'supplement.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'supplement_sha256':sha(D/'supplement.json'),'closure':proof}))
