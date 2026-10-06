from pathlib import Path
import json,hashlib,uuid
root=Path(__file__).resolve().parents[7];here=Path(__file__).resolve().parent
manifest=json.loads((here/'candidate-10-project-fixture-source.json').read_text(encoding='utf-8'))
paths=['adapters/runtime/mu/worker.mjs','internal/domain/runtime_model.go','internal/domain/runtime_broker_windows.go','internal/domain/runtime_model_windows.go','internal/domain/runtime_model_verification.go','internal/domain/runtime_model_stream.go','internal/domain/runtime_provider_binding_test.go','internal/domain/runtime_provider_binding_windows_test.go','adapters/runtime/mu/worker-provider-binding.test.mjs']
out=here/'sealed-candidate-10';out.mkdir(exist_ok=True)
results=[]
for rel in paths:
 raw=(root/rel).read_bytes()
 if rel.endswith('runtime_model_verification.go'):
  raw=raw.replace(b'\tif len(cwd)==1 && !seen { return nil,historyInvalid("provider Host instruction missing") }\n',b'')
 if rel.endswith('runtime_provider_binding_windows_test.go'):
  text=raw.decode('utf-8')
  text=text.replace('\tvar prepared atomic.Value\n','')
  start=text.index('\t\toriginal,ok:=prepared.Load().(Object)');end=text.index('\n\t\tif respond != nil',start);text=text[:start]+text[end+1:]
  start=text.index('\tc.boundaryHook=func(name string,intent Object)');end=text.index('\n',start);text=text[:start]+text[end+1:]
  text=text.replace('} else if n != 1 && n != 4 {','} else if n != 1 {')
  start=text.index('\tvar revision,writer int64;');end=text.index('\n\tt.Log("real SDK qualification',start);text=text[:start]+text[end+1:]
  text=text.replace('\t\t\toriginalBoundary:=c.boundaryHook\n','')
  raw=text.encode('utf-8')
 actual=hashlib.sha256(raw).hexdigest();expected=manifest['files'][rel]
 results.append({'path':rel,'expected':expected,'actual':actual,'equal':actual==expected})
 if actual==expected:
  target=out/rel;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists() and target.read_bytes()!=raw:raise RuntimeError('immutable target differs')
  if not target.exists():target.write_bytes(raw)
(out/('reconstruction-audit-'+uuid.uuid4().hex+'.json')).write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
print(json.dumps(results,indent=2))
if not all(x['equal'] for x in results):raise SystemExit(1)
