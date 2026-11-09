import ast,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
N=Path(__file__).parent
G=N.parents[1]/"native_grant_bounded_read_revision_codex/gbr-1a11ee4f162766098eda3028b0679f2"
p=N/"root_build_grant_archive_request.py"
s=p.read_text(encoding="utf-8")
h=(G/"native_grant_public_pin_archive.py").read_text(encoding="utf-8")
tree=ast.parse(h)
functions={"pairs","decode","digest","canonical","inside","exact","ref","rawpin","plain","same","counter",
 "inventory_roles","validate_grant","validate_selection","lifecycle","output_boundary"}
constants={"CONFIG_SHA","CONFIG_BYTES","HARNESS_SHA","HARNESS_BYTES","CASE_ID","INVENTORY","ALIAS_ROLE","ALIAS_TARGET","PLAN"}
pieces=[]
for node in tree.body:
 if isinstance(node,ast.FunctionDef) and node.name in functions:
  pieces.append(ast.get_source_segment(h,node))
 elif isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in constants for t in node.targets):
  pieces.append(ast.get_source_segment(h,node))
assert len(pieces)==len(functions)+len(constants)
a=s.index("def canonical(");z=s.index("def validate_ref(",a)
s=s[:a]+"\n\n".join(pieces)+"\n\n"+s[z:]
a=s.index("def load_helper(");z=s.index("def select_full(",a)
s=s[:a]+s[z:]
s=s.replace("import types\n","import collections\n")
s=s.replace("def select_full(m, payload,", "def select_full(payload,")
a=s.index("    m = load_helper()");z=s.index("    frozen = {}",a)
s=s[:a]+"    bounded_read(HELPER)  # Verify Source bytes only; never import or invoke it.\n"+s[z:]
s=s.replace("select_full(m,payload,","select_full(payload,").replace("m.validate_grant(","validate_grant(").replace("m.validate_selection(","validate_selection(").replace("m.lifecycle(","lifecycle(").replace("m.output_boundary(","output_boundary(").replace("m.inside(","inside(")
assert "m." not in s.replace("stream.","") and "exec(" not in s and "compile(" not in s and "import types" not in s
assert ".read_bytes(" not in s and ".read()" not in s
ast.parse(s)
p.write_text(s,encoding="utf-8",newline="\n")
provenance=json.loads((N/"source-provenance.json").read_bytes())
provenance.update(runtime_helper_import_or_invocation=False,
 pure_metadata_functions_statically_embedded=sorted(functions),
 pure_metadata_constants_statically_embedded=sorted(constants),
 helper_Source_read_is_pin_verification_only=True)
(N/"source-provenance.json").write_text(json.dumps(provenance,ensure_ascii=True,indent=2)+"\n",encoding="utf-8")
test=G/"pure_source_controls.py"
old=test.read_text(encoding="utf-8")
(G/"pure_source_controls.initial.py").write_text(old,encoding="utf-8",newline="\n")
new=old.replace('b.select_full(m,','b.select_full(')
new=new.replace('original_canonical=m.canonical\nm.canonical=lambda p:original_canonical(p,False)',
 'original_canonical=m.canonical\nm.canonical=lambda p:original_canonical(p,False)\nbuilder_canonical=b.canonical\nb.canonical=lambda p:builder_canonical(p,False)')
new=new.replace('m.canonical=original_canonical\nfor folder','m.canonical=original_canonical\nb.canonical=builder_canonical\nfor folder')
new=new.replace('"bounded-controls.results.json"','"bounded-controls.results.final.json"').replace('"builder-controls.results.json"','"builder-controls.results.final.json"')
new=new.replace('expect("no_archive_run_or_child_process",lambda:yes("m.run(" not in source and "m.main(" not in source and "subprocess" not in source and ".mkdir(" not in source))',
 'expect("no_archive_run_or_child_process",lambda:yes("exec(" not in source and "compile(" not in source and "load_helper" not in source and "subprocess" not in source and ".mkdir(" not in source))')
ast.parse(new);test.write_text(new,encoding="utf-8",newline="\n")
print("REQUEST_BUILDER_INERT_REFINEMENT_OK")

