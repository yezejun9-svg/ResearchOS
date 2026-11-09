from pathlib import Path
O=Path(__file__).parent;P=O.parent/'dc4fe023ed714e74b8d3692b504cf55d'
s=(P/'abi_delta.py').read_text(encoding='utf-8')
s=s.replace('desktop58-finite169-go3-r336-','desktop58-finite169-go3-r337-').replace('tool-observations.fifth-construction.closed.original.json','tool-observations.sixth-construction.closed.original.json')
s=s.replace("ob['scope_ref']==sr and set(sr)=={'path','sha256','bytes'}", "sr['sha256']=='0caa54d359072e7200b7cbbc9fb72742ffb325adc82ad3b4622310ac7549e9c1' and set(sr)=={'path','sha256','bytes'}")
s=s.replace("ck('Rootinput exact '+k,ri[k]==b[k])", "ck('Rootinput exact '+k,(Path(ri[k])==(R/b[k]) if k=='registration_namespace' else ri[k]==b[k]))")
s=s.replace('desktop58_root_caller_allocationdc4f_independent_source_review_codex/ca4c76a72d524f459ecf2bef305939c8','desktop58_root_caller_allocationsixth_independent_source_review_codex/afc06b382f074b3fb512ec4f6b64a2e9')
s=s.replace('baaf93516e9d42e2b583972e5a30df91','d8a016ddc71e440fb386a11957c098ea')
s=s.replace("ob['controller_or_launcher_executed'] is False", "ob['product_native_calls']==0")
with (O/'abi_delta.py').open('x',encoding='utf-8',newline='\n') as f:f.write(s)
print('Sixth ABI audit prepared; no target imports.')

