from pathlib import Path
import json,ast
R=Path('D:/作品集/ResearchOS/research-os');N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r339-9eccde97a9fa4815941768cacaf590dc'
p=json.loads((N/'prepared_refs.json').read_bytes());b=json.loads((N/'binding.json').read_bytes())
print(json.dumps({'prepared_keys':list(p),'before':p['expected_before'],'after':p['expected_after'],'canonical_before':p['canonical_before'],'original_refs':p['original_refs'],'desired_refs':p['desired_refs'],'verified_count':len(p['verified_refs']),'origin_count':len(p['origins']),'scope_ref':p['scope_ref'],'metadata_refs':b['metadata_code_refs']},ensure_ascii=False))
for kind in ('head','status','index'):
    v=json.loads((N/('prepare.'+kind+'.invocation.json')).read_bytes())
    print(json.dumps({'kind':kind,'keys':list(v),'result':v.get('result'),'argv':v.get('argv'),'wrapper_error':v.get('wrapper_error'),'actual_stage_native_exit':v.get('actual_stage_native_exit')},ensure_ascii=False))
modules=[r for r in b['metadata_code_refs'] if r['sha256']=='c0a085f9b720ebdb89a78fb5cf367bd262d2823fe15a9f2686545b99aebe7755']
mp=Path(modules[0]['path']);mp=mp if mp.is_absolute() else R/mp
txt=mp.read_text();tree=ast.parse(txt)
for v in tree.body:
    if isinstance(v,ast.FunctionDef) and v.name in ('registration_review','register','run','prepare','seal','wip_values','desktop_lease'):
        print('FUNCTION '+v.name+' line '+str(v.lineno));print(ast.get_source_segment(txt,v))
