"""Pure IO/AST adaptation of pinned builder; no imports of generated code."""
import ast,difflib,hashlib,json
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os')
P13=ROOT/'execution/v2.4/receipts/W13/W13-03'
BASE=P13/'fresh58_cli2_root_metadata_preparation_codex/900837a405be433f83524eddcc1c6bd8'
ADAPTER=P13/'desktop58_root_authority_adapter_revision_preparation_codex/fde71451a31d4404b8e3d57b396f270c'
OUT=Path(__file__).resolve().parent
def ref(p):
    raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(n,v):
    with (OUT/n).open('xb') as f:f.write(v if isinstance(v,bytes) else (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
old=(BASE/'build_binding.current58.proposed.py').read_bytes();text=old.decode();edits=[]
def swap(a,b):
    global text
    assert text.count(a)==1,(a[:100],text.count(a));text=text.replace(a,b);edits.append({'before':a,'after':b})
swap("V3_GATE_SHA='6ff7a907980da9ffe50a7a2f3ba5669820cd1d99a820be476e5327abd0dec782'", "V3_GATE_SHA='6a8b87dd4b1edfcbe669a656d02fe5b0bc16a7ac1eca1412be5d737e1c4dadd8'")
swap("'origin-cut-ref','canonical-before-ref','source-inputs-ref','metadata-code-refs-ref','failure-prefix430-ref')", "'origin-cut-ref','canonical-before-ref','source-inputs-ref','metadata-code-refs-ref','failure-prefix430-ref',\n                 'desktop-values-ref','toolchain-lock-ref')")
swap("s['authorization_gate_ref']['sha256']", "s['authorization_verifier_ref']['sha256']")
swap("roots[4].is_relative_to(ROOT/'execution/v2.4/receipts/W05/W05-99')", "roots[4].is_relative_to(ROOT/'execution/v2.4/receipts/W13/W13-03')")
swap("    b={k:s[k] for k in ('runner_ref','launcher_ref','authorization_gate_ref','owned_process_helper_ref',\n        'debug_tree_helper_ref','toolchain_lock_ref','python_flags')}", """    aliases={'runner_ref':'controller_ref','authorization_gate_ref':'authorization_verifier_ref',
             'owned_process_helper_ref':'owned_helper_ref','debug_tree_helper_ref':'debug_helper_ref',
             'launcher_ref':'launcher_ref','utility_ref':'utility_ref','python_flags':'python_flags'}
    b={key:s[value] for key,value in aliases.items()}
    b['toolchain_lock_ref']=a.toolchain_lock_ref
    b['desktop_scope_values']=strict(verified_bytes(a.desktop_values_ref))
    need(type(b['desktop_scope_values'])is dict and b['desktop_scope_values'] and
         all(v is not None for v in b['desktop_scope_values'].values()),'all Desktop values required')
    # Exact key set, per-field budgets, aliases, CLI2 and resource semantics are checked by pipeline/gate.
    for k,v in b['desktop_scope_values'].items():
        if k.endswith('_ref'):pinned(json.dumps(v))""")
swap("schema='researchos.cli43-root-metadata-binding.v1'", "schema='researchos.desktop58-root-metadata-binding.v1'")
new=text.encode();ast.parse(new)
back=text
for e in reversed(edits):assert back.count(e['after'])==1;back=back.replace(e['after'],e['before'])
assert back.encode()==old
save('build_binding.desktop58.proposed.py',new)
save('builder.inverse.json',{'old_ref':ref(BASE/'build_binding.current58.proposed.py'),'new_ref':ref(OUT/'build_binding.desktop58.proposed.py'),'edits':edits,'whole_byte_inverse_equal':True})
save('builder.diff',''.join(difflib.unified_diff(old.decode().splitlines(True),text.splitlines(True),fromfile='old.binding.py',tofile='desktop58.binding.py')).encode())
olddefs={x.name:ast.dump(x,include_attributes=False) for x in ast.parse(old).body if isinstance(x,ast.FunctionDef)}
newdefs={x.name:ast.dump(x,include_attributes=False) for x in ast.parse(new).body if isinstance(x,ast.FunctionDef)}
assert all(olddefs[k]==newdefs[k] for k in olddefs if k!='main')
template=json.loads((ADAPTER/'scope.v2.proposed.json').read_bytes())
template.update(new_grant_preflight_root=None,toolchain_lock_ref=None,runtime_observation_phases=None)
save('scope.desktop58.template.json',template)
keys=['source_catalog_ref','resource_catalog_ref','current58_CLI2_qualification_ref','current58_CLI2_review_ref',
    'current58_CLI2_manifest_ref','Root_forward_head_seal_ref','Root_forward_head_review_ref','negative_alias_declarations',
    'inner_seconds','outer_seconds','builder_seconds','controller_evidence_reserve_seconds','launcher_evidence_reserve_seconds',
    'expected_runtime_observation_paths','runtime_observation_phases']
save('desktop-values.proposed.json',{k:None for k in keys})
save('binding-interface.json',{'args_required':['scope-template-ref','runtime-resources-ref','compiler-resources-ref','current43-authority-ref','origin-cut-ref','canonical-before-ref','source-inputs-ref','metadata-code-refs-ref','failure-prefix430-ref','desktop-values-ref','toolchain-lock-ref','controller-review-ref','before','after','main-git','public-environment','run-uuid','registration-namespace','controller-review-path','new-output-root','new-wrapper-root','new-export-root','new-authorization-root','new-grant-preflight-root','output'],'wire_aliases':{'current43-authority-ref':'actual e2 current58 authority only','new-output-root':'Desktop output_root','new-wrapper-root':'Desktop outer_output_root','new-export-root':'Desktop export_root','runner_ref':'Desktop controller_ref','utility_ref':'module_observation implementation only'},'future_values':'All Desktop value fields NULL in preparation. Root actual refs/tuple/cut/budgets/paths required.','cycle_free_order':['Root public resource freeze including current code and wrappers','explicit binding(template) plus Desktop values and predetermined review path','full scope materialization','independent full scope review exactSHA','new final binding containing that review ref','prepare originals/desired/audit','independent registration review','Root owned run/CAS','seal','preflight real authority and Git/live4','create auth leaf then second Git/time observations','actual observation refs copied into prelaunch and grant','gate validates exact full grant','separate authorized once launcher'], 'unused_old_overlay':'No inherited old8 metadata catalogue accepted; runtime requires actual current builder/module/wrappers/util/controller refs.'})
print(json.dumps({'builder_ref':ref(OUT/'build_binding.desktop58.proposed.py'),'scope_template_ref':ref(OUT/'scope.desktop58.template.json'),'target_calls':0},ensure_ascii=False))
