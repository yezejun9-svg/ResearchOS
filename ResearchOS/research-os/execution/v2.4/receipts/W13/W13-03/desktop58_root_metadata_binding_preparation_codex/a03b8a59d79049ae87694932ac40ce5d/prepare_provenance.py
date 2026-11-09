"""Read only already sealed public metadata; no resource rehash or candidate calls."""
import ast,hashlib,json
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');OUT=Path(__file__).resolve().parent
def ref(p):
    raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(n,v):
    with (OUT/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
ns=ROOT/'execution/v2.4/receipts/W05/W05-99/cli58_successful_execution_independent_review_codex/83c89c410a1744b8b77d121fd44e5c5e'
files=[ns/n for n in ('qualification.json','review.json','manifest.json')]
refs=[ref(p) for p in files]
assert [r['sha256'] for r in refs]==['624607c5589a2210254ed4cae8208b5a2251fe09be62117938c2ac5ad9e3b1bc','b638d6dfb8e51412d2893c393e4ff75207c86e7f3776b350dd8a47ebf15b4132','027ac6e548548754487475605546e935a349ea79c06db0ea5893075b7f780d20']
q,r,m=[json.loads(p.read_bytes()) for p in files]
adapter=ROOT/'execution/v2.4/receipts/W13/W13-03/desktop58_root_authority_adapter_revision_preparation_codex/fde71451a31d4404b8e3d57b396f270c/authorization_adapter.v2.proposed.py'
fn=next(n for n in ast.parse(adapter.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='validate_cli2')
required={name:set() for name in ('q','review')}
for n in ast.walk(fn):
    if isinstance(n,ast.Subscript) and isinstance(n.value,ast.Name) and n.value.id in required and isinstance(n.slice,ast.Constant) and isinstance(n.slice.value,str):required[n.value.id].add(n.slice.value)
shape={'q_missing_keys':sorted(required['q']-set(q)),'review_missing_keys':sorted(required['review']-set(r))}
save('current58-CLI2-reference-provenance.json',{'refs':refs,'actual_source':q['source_commit'],'case_ids':q['qualified_case_ids'],'native_calls':q['native_calls'],'actual_reported_qualification':q['current43_fresh_held2_qualified'],'schema_check_only':shape,'template_qualification_fields_still_NULL':True,'candidate_gate_executed':False,'actual_authority_still_requires_Root_scope_CAS_grant':True})
shape_file=OUT/'resource-input-shapes.json';shapes=json.loads(shape_file.read_bytes());inventory_ref=shapes[1]['ref'];inventory=json.loads(Path(inventory_ref['path']).read_bytes())
assert ref(Path(inventory_ref['path']))==inventory_ref
tools=[x for x in inventory if Path(x['path']).name.lower() in ('node.exe','electron.exe','go.exe','git.exe','python.exe')]
module_rows=[x for x in inventory if '/node_modules/' in x['path'].replace('\\','/')]
roots=sorted({x['path'].replace('\\','/').split('/node_modules/')[0]+'/node_modules' for x in module_rows})
save('historical-resource-provenance.json',{'inventory_ref':inventory_ref,'historical_member_count':len(inventory),'tool_rows':tools,'node_module_roots':roots,'node_module_row_count':len(module_rows),'current_resource_closure':False,'individual_resource_files_rehashed':False,'selection_rule':'Root must freeze actual selected current runtime/compiler plus relevant old public Node/Electron/web paths; stale source/cache/output/code rows are not inherited merely by matching count.','resource_stage_source_ref':ref(OUT/'resource_catalog.proposed.py')})
save('additional-inputs.json',refs+[ref(shape_file),ref(adapter),inventory_ref])
print(json.dumps({'current_CLI2_shape':shape,'current_CLI2_refs':refs,'historical_tool_rows':tools,'node_module_roots':roots,'candidate_calls':0},ensure_ascii=False))
