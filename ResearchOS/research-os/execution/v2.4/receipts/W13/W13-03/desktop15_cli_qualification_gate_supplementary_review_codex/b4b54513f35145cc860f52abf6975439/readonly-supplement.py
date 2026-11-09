from pathlib import Path
import ast
import hashlib
import json

ROOT = Path("D:/作品集/ResearchOS/research-os").resolve()
OWN = Path(__file__).resolve().parent
P13 = ROOT / "execution/v2.4/receipts/W13/W13-03"
C = P13 / "desktop15_cli_qualification_gate_preparation_codex/0293420914814321ac0897bdfa7d9ee7"
B = P13 / "desktop15_root_scope_binding_preparation_codex/5097ef19e4414a81b6457363a3b76060"
OLD = P13 / "desktop_exact15_integration_preparation_revision_codex/e908291811794b64874f5f6f66507916"
Q = ROOT / "execution/v2.4/receipts/W05/W05-99/cli43_successful_execution_independent_review_codex/6f07498ca19a49c7866b9e528d401aa0"
ACTOR = "codex:/root/f08_i17_binding_impl"
READS, CHECKS = {}, {}

def need(value, why):
    if not value:
        raise RuntimeError(why)

def path(value):
    p = Path(value)
    return (p if p.is_absolute() else ROOT / p).resolve()

def raw(value):
    p = path(value)
    need(p.is_relative_to(ROOT / "execution/v2.4/receipts"), "Frozen receipts only")
    b = p.read_bytes()
    r = {"path":p.as_posix(),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
    need(p not in READS or READS[p] == r, "Frozen input drift")
    READS[p] = r
    return b

def ref(value):
    raw(value)
    return dict(READS[path(value)])

def verify(r):
    b = raw(r["path"])
    need(hashlib.sha256(b).hexdigest() == r["sha256"] and len(b) == r["bytes"], "Original ref drift")
    return b

def doc(value):
    return json.loads(verify(value) if isinstance(value,dict) else raw(value))

def pin(value, digest, size):
    r = ref(value)
    need(r["sha256"] == digest and r["bytes"] == size, "Fixed pin differs")
    return r

def check(name, passed):
    need(passed, "Supplement check: " + name)
    CHECKS[name] = True

def write(name, value):
    p = OWN / name
    b = (json.dumps(value,ensure_ascii=False,indent=2) + "\n").encode("utf-8")
    with p.open("xb") as f:
        f.write(b)
    return {"path":p.as_posix(),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}

def function_bytes(b, name):
    tree = ast.parse(b)
    rows = b.splitlines(keepends=True)
    nodes = [n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name == name]
    need(len(nodes) == 1, "One exact named source function")
    node = nodes[0]
    return b"".join(rows[node.lineno-1:node.end_lineno]), node

def same_ref(a,b):
    return path(a["path"]) == path(b["path"]) and a["sha256"] == b["sha256"] and a["bytes"] == b["bytes"]

need(OWN.name == "b4b54513f35145cc860f52abf6975439", "Owned supplement namespace")
hdf_ref = pin(C/"handoff.complete.json","3e9b7fa338f737a229a520de6c0148d0bf4d1c1ed8c5b0c22dffd76dddcbb91c",3196)
mf_ref = pin(C/"manifest.complete.json","63dbc6099d83a0d117d4d1f6835f0d12844924623c946217e294bdee2d91b417",8522)
hdf, mf = doc(hdf_ref), doc(mf_ref)
need(hdf["actor"] != ACTOR, "Non-author supplement")
check("complete_manifest26_exact", type(mf["count"]) is int and mf["count"] == len(mf["entries"]) == 26)
seen = set()
for item in mf["entries"]:
    p = path(item["path"])
    need(p.parent == C and p not in seen, "Complete MF namespace/duplicate")
    verify(item)
    seen.add(p)
check("complete_manifest_all26_bytes_match", True)
check("complete_manifest_seals_selected_packets", path(hdf["selected_handoff_ref"]["path"]) in seen and path(hdf["selected_manifest_ref"]["path"]) in seen)
selected = doc(hdf["selected_handoff_ref"])
selected_mf = doc(hdf["selected_manifest_ref"])
check("selected_manifest22_unmodified", selected_mf["count"] == len(selected_mf["entries"]) == 22)
for item in selected_mf["entries"]:
    verify(item)
builder = verify(hdf["builder_ref"])
controller = verify(hdf["controller_ref"])
old_builder = raw(B/"build-scope.py")
old_controller = raw(OLD/"integrate_desktop15.v2.py")
scope, old_scope = doc(hdf["scope_ref"]), doc(OLD/"scope.v3.proposed.json")
check("original_builder_and_controller_copies_exact", raw(C/"original.builder.py.txt") == old_builder and raw(C/"original.controller.py.txt") == old_controller)
blocks = []
for role, before, after, start, end in [
    ("builder.CLI43",old_builder,builder,199,210),
    ("controller.CLI43",old_controller,controller,234,250),
    ("controller.Main38",old_controller,controller,209,233),
]:
    block = b"".join(before.splitlines(keepends=True)[start-1:end])
    check(role+"_old_predicate_byteblock_contiguous_once", after.count(block) == 1)
    blocks.append({"role":role,"old_start":start,"old_end":end,"raw_sha256":hashlib.sha256(block).hexdigest(),"bytes":len(block),"candidate_occurrences":after.count(block),"original_raw_text":block.decode("utf-8")})
check("all_source_line_endings_LF_preserved", b"\r" not in old_builder+old_controller+builder+controller)
check("controller_execute_whole_raw_body_unchanged", function_bytes(old_controller,"execute")[0] == function_bytes(controller,"execute")[0])
check("controller_budget_whole_raw_body_unchanged", function_bytes(old_controller,"budget")[0] == function_bytes(controller,"budget")[0])
launcher_ref = pin(OLD/"launch_desktop15.v2.py","3669c0c76413728de8157b4f03e27773b25f3c9ad6da600d237629df2c4ae87b",10518)
check("launcher_copy_and_scope_exact_reuse", raw(C/"original.launcher.py.txt") == verify(launcher_ref) and same_ref(scope["launcher_ref"],old_scope["launcher_ref"]))
check("metadata_builder_exact_reuse", raw(C/"original.metadata_builder.py.txt") == raw(B/"build-metadata-templates.py"))
check("metadata_engine_exact_reuse", raw(C/"original.metadata_engine.py.txt") == raw(B/"metadata-engine.template.py"))
delta = {k:{"before":old_scope.get(k),"after":scope.get(k)} for k in set(scope)|set(old_scope) if old_scope.get(k) != scope.get(k)}
check("scope_only_controller_and_qualification_bundle_changed", set(delta) == {"controller_ref","cli43_bounded_qualification_refs"})
check("scope_controller_matches_selected_new_bytes", same_ref(scope["controller_ref"],hdf["controller_ref"]))
for k in ["exact_paths","union_paths","apply_cap","commit_cap","git_step_cap","product_tests_HTTP_SQL_models","limits",
          "source_acceptance","formal_increment","fresh43_validation_authorized","fresh58_validation_authorized",
          "Desktop_GUI_install_NVDA_authorized","author169_inherited_as_Root_current","old_Go3_normal_OS_gap_retained","new_Go3_boundeddebug_separate"]:
    check("original_scope_field_preserved_"+k, scope[k] == old_scope[k])
gate_b, node_b = function_bytes(builder,"cli43_bounded_qualification_gate")
gate_c, node_c = function_bytes(controller,"cli43_bounded_qualification_gate")
check("builder_and_controller_gate_raw_bodies_identical", gate_b == gate_c)
b_ast, c_ast = ast.parse(builder), ast.parse(controller)
def literal_qualification_refs(tree):
    nodes = [n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="CLI43_BOUNDED_QUALIFICATION_REFS" for t in n.targets)]
    need(len(nodes)==1,"One gate fixed-ref declaration")
    return ast.literal_eval(nodes[0].value)
fixed = literal_qualification_refs(b_ast)
check("controller_and_builder_fixed_refs_identical", fixed == literal_qualification_refs(c_ast) == scope["cli43_bounded_qualification_refs"])
q, review, qh = [doc(fixed[k]) for k in ["qualification_ref","review_ref","handoff_ref"]]
qmf = doc(fixed["manifest_ref"])
check("fixed_real_qualification_four_refs", all(same_ref(fixed[k],ref(Q/n)) for k,n in [("qualification_ref","qualification.json"),("review_ref","review.json"),("manifest_ref","manifest.json"),("handoff_ref","handoff.json")]))
actual_shapes = {"entries":len(qmf["entries"])}
shape_docs = [("qualification",fixed["manifest_ref"],"entries",18),
              ("executor",q["evidence_refs"]["executor_manifest_ref"],"files",125),
              ("launcher",q["evidence_refs"]["launcher_manifest_ref"],"files",7),
              ("Root",q["evidence_refs"]["root_closed_manifest_ref"],"members",11)]
manifest_shapes = []
for label,mref,field,count in shape_docs:
    m = doc(mref)
    check("actual_manifest_shape_"+label,len(m[field])==count and (field=="members" or type(m["count"]) is int and m["count"]==count))
    manifest_shapes.append({"role":label,"ref":mref,"keys":list(m),"field":field,"actual_members":len(m[field]),"count":m.get("count")})
calls = [(n.args[1].value,n.args[2].value) for n in ast.walk(node_b) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="sealed" and len(n.args)==4 and isinstance(n.args[1],ast.Constant) and isinstance(n.args[2],ast.Constant)]
check("source_manifest_cardinalities_match_actual", calls == [("entries",18),("files",125),("files",7),("members",11)])
check("real_schema_and_decision_literals_present",
      all(text in gate_b.decode("utf-8") for text in [q["schema"],review["schema"],review["decision"]]))
check("qualification_boundary_and_exact_case_fields_present",
      all(text in gate_b.decode("utf-8") for text in ["current43_fresh_held2_qualified","desktop15_new_scope_preparation_permitted","whole43_test_suite_qualified","Main_integration_authorized","desktop15_execution_authorized","actual_execution_authorized","real-existing-open-readonly","real-existing-self-send","CLI_exit_codes","[0, 3]","native_test_exit","source_acceptance","formal_increment"]))
check("no_Root_observation_booleans_rewritten_as_qualification", all(text not in gate_b.decode("utf-8") for text in ["fresh_compile_qualification","caller_OS_lifecycle_qualification","complete_current43_source_validation"]))
check("original_qualification_snapshot_source_and_scope", q["source_commit"]==review["source_commit"]=="a510dbef4a7e08fb5c428df44c39b133f3ffa856" and q["qualified_case_ids"]==review["case_ids"]==["real-existing-open-readonly","real-existing-self-send"] and q["whole43_test_suite_qualified"] is False)
result = doc(q["evidence_refs"]["result_ref"])
labels_node = [n for n in ast.walk(node_b) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="labels" for t in n.targets)]
need(len(labels_node)==1,"One exact stage label declaration")
labels = ast.literal_eval(labels_node[0].value)
check("exact14_stage_labels_bind_actual_result", [x["label"] for x in result["stages"]]==labels and len(labels)==14)
input_refs = [READS[p] for p in sorted(READS)]
before_ref = write("inputs.before.json",{"refs":input_refs})
after_refs=[]
for item in input_refs:
    b=path(item["path"]).read_bytes()
    after_refs.append({"path":item["path"],"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)})
check("all_frozen_inputs_unchanged",input_refs==after_refs)
after_ref = write("inputs.after.json",{"refs":after_refs})
audit_ref = write("supplement-audit.json",{
    "schema":"researchos.desktop15-qualification-source-supplement-audit.v1","reviewer":ACTOR,
    "checks":CHECKS,"count":len(CHECKS),"source_byte_blocks":blocks,"scope_delta":delta,
    "gate_definition_locations":{"builder":[node_b.lineno,node_b.end_lineno],"controller":[node_c.lineno,node_c.end_lineno]},
    "manifest_shapes":manifest_shapes,"AST_only":True,"candidate_executed":False,
    "full_wholeinverse_and_14_invocation_reaudit":"Not repeated; primary W05 reviewer covers these",
    "input_before_ref":before_ref,"input_after_ref":after_ref,"new_failed_tools":0,
})
review_ref = write("supplementary-review.json",{
    "schema":"researchos.desktop15-cli-qualification-gate-nonauthor-supplement-review.v1",
    "reviewer":ACTOR,"candidate_author":hdf["actor"],
    "decision":"NO_REQUEST_WITHIN_SUPPLEMENT_SCOPE","status":"STOPPED",
    "review_scope":["actual qualification field mapping","actual manifest fields/cardinality","original CLI43/Main38 predicate byte blocks","scope delta/budget/launcher/metadata byte reuse"],
    "primary_reviewer":"codex:/root/w05_merge_review","primary_review_ref":None,
    "primary_review_note":"This supplement does not replace main source/controller review or review the future actual Root bound scope.",
    "candidate_complete_handoff_ref":hdf_ref,"candidate_complete_manifest_ref":mf_ref,
    "candidate_builder_ref":hdf["builder_ref"],"candidate_controller_ref":hdf["controller_ref"],"candidate_scope_ref":hdf["scope_ref"],
    "source_qualification_refs":fixed,"audit_ref":audit_ref,"input_before_ref":before_ref,"input_after_ref":after_ref,
    "requested_changes":[],"new_failed_tools":0,"new_failure_origins":[],
    "preexisting_mapping_2fe4_coordination_W05_author_origins_recounted":False,
    "actual_execution_authorized":False,"source_acceptance":False,"formal_increment":0,"candidate_imports":0,
    "Go_Node_SQL_Job_network_CAS_Git_writes":0,"actual_target_native_exit":None,
    "open_conditions":["New nonauthor main source/controller review","Future actual Root tuple/resources/full scope review","Real reviewed CAS/seal/exclusive once grant","Fresh combined58/Root169/GUI/install/NVDA/provider/P02/formal gates"],
})
handoff_ref = write("handoff.json",{
    "schema":"researchos.desktop15-cli-qualification-gate-supplement-handoff.v1","reviewer":ACTOR,
    "decision":"NO_REQUEST_WITHIN_SUPPLEMENT_SCOPE","status":"STOPPED",
    "review_ref":review_ref,"audit_ref":audit_ref,"candidate_handoff_ref":hdf_ref,"candidate_manifest_ref":mf_ref,
    "source_only":True,"requested_changes":[],"new_failed_tools":0,"new_failure_origins":[],
    "old_origins_recounted":False,"primary_reviewer":"codex:/root/w05_merge_review","primary_review_ref":None,
    "source_acceptance":False,"formal_increment":0,"execution_authorized":False,
    "metadata_sealer_actual_native_exit_at_write":None,
})
members=[]
for p in sorted(OWN.iterdir()):
    if p.is_file() and p.name!="manifest.json":
        b=p.read_bytes()
        members.append({"path":p.as_posix(),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)})
ownmf_ref=write("manifest.json",{"schema":"researchos.immutable-public-receipt-manifest.v1","members":members,"member_count":len(members),"self_excluded":True})
print(json.dumps({"status":"STOPPED","decision":"NO_REQUEST_WITHIN_SUPPLEMENT_SCOPE","review_ref":review_ref,"handoff_ref":handoff_ref,"audit_ref":audit_ref,"manifest_ref":ownmf_ref,"manifest_members":len(members),"checks":len(CHECKS),"new_failed_tools":0,"target_calls":0},ensure_ascii=False,indent=2))

