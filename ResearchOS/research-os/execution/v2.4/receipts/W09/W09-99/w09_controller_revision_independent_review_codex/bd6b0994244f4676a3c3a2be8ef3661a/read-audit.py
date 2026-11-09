import ast
import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path("D:/作品集/ResearchOS/research-os")
C = ROOT / "execution/v2.4/receipts/W09/W09-99/w09_controller_revision_preparation_codex/c1eefb6423544a4eaf22fb9045692630"
S = C / "selected"
O = ROOT / "execution/v2.4/receipts/W09/W09-99/finite_controller_preparation_codex/2098f8232b5a4331b0cac70eccd32ce0"
OWN = ROOT / "execution/v2.4/receipts/W09/W09-99/w09_controller_revision_independent_review_codex/bd6b0994244f4676a3c3a2be8ef3661a"
ACTOR = "codex:/root/f08_i17_binding_impl"
reads = []

def pin(p):
    p = Path(p)
    raw = p.read_bytes()
    r = {"path":p.as_posix(),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
    reads.append(r)
    return r

def js(p):
    pin(p)
    return json.loads(Path(p).read_bytes())

def check_ref(r):
    a = pin(r["path"])
    return {"original_ref":r,"actual_ref":a,"matches":a["sha256"]==r["sha256"] and a["bytes"]==r["bytes"]}

def create(name,obj):
    p=OWN/name
    if p.exists():raise ValueError("Refuse own overwrite")
    p.write_bytes((json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode("utf-8"))
    return pin(p)

hdf=js(C/"handoff.json");mf=js(C/"manifest.json")
assert pin(C/"handoff.json")["sha256"]=="b105a28528300c250d176941be2c86427bb595ae123e08597f63ff37013c4a57"
assert pin(C/"manifest.json")["sha256"]=="7b3e072c962165ff3fd372dc313e0c371afd79005bd01292fe2e9dc20adac954"
assert pin(C/"postseal-audit.json")["sha256"]=="a68219e764836febbfb78f57c741be13b1e6aef207ce18a35fb69379dcfeb41b"
fixed=[check_ref(hdf[k]) for k in ["selected_spec_ref","original_review_ref","fix_mapping_ref","authority_contract_ref","static_audit_ref","original_manifest_prefix_ref","source_inverse_ref","input_before_ref","input_after_ref","preserved_original_os206_ref"]]
fixed.extend(check_ref(r) for r in hdf["selected_sources"])
new_members=[check_ref(r) for r in mf["members"]]
old_mf=js(O/"manifest.json");old_members=[check_ref(r) for r in old_mf["members"]]
spec=js(S/"spec.proposed.json");oldspec=js(O/"spec.json");grant=js(S/"root-grant.UNAUTHORIZED.proposed.json")
edits=js(S/"edits.json");inverses=[];functions=[];descriptors=[]
changed=[]
def function_map(raw):
    tree=ast.parse(raw)
    lines=raw.splitlines(keepends=True)
    result={}
    def visit(nodes,prefix=""):
        for n in nodes:
            if isinstance(n,(ast.ClassDef,ast.FunctionDef)):
                key=prefix+n.name
                if isinstance(n,ast.FunctionDef):result[key]=b"".join(lines[n.lineno-1:n.end_lineno])
                visit(n.body,key+".")
    visit(tree.body)
    return tree,result
allowed={
 "controller_common.py":{"trusted_module","validate_grant","require_job"},
 "controller.py":{"Controller.__init__","Controller.run","Controller.resources"},
 "case_worker.py":{"main"},
 "seal_readonly.py":{"main"},
 "windows_debug_job_tree.py":{"run_owned","run_owned.pump"}
}
for name in ["controller_common.py","controller.py","case_worker.py","launch.py","seal_readonly.py","windows_debug_job_tree.py","windows_owned_process.py"]:
    p=S/name
    original=O/("inputs/2-windows_owned_process.py" if name=="windows_owned_process.py" else name)
    new=p.read_bytes();old=original.read_bytes()
    tree,nfn=function_map(new);_,ofn=function_map(old)
    descriptors.append({"ref":pin(p),"AST":"PARSED_ONLY_NOT_IMPORTED","functions":[{"name":k,"sha256":hashlib.sha256(v).hexdigest()} for k,v in nfn.items()]})
    if new!=old:changed.append(name)
    restoration=new;steps=[]
    for e in reversed(edits.get(name,[])):
        a=e["after"].encode("utf-8");b=e["before"].encode("utf-8")
        n=restoration.count(a)
        assert n==1,(name,"inverse occurrence",n)
        restoration=restoration.replace(a,b,1)
        steps.append({"after_bytes":len(a),"before_bytes":len(b),"occurrences":n})
    assert restoration==old,(name,"whole byte inverse")
    inverse_file=S/(name+".inverse-original")
    if inverse_file.exists():assert inverse_file.read_bytes()==old
    inverses.append({"name":name,"candidate_ref":pin(p),"original_ref":pin(original),"inverse_sha256":hashlib.sha256(restoration).hexdigest(),"inverse_byte_equal":True,"steps":steps})
    for k,body in ofn.items():
        if k not in allowed.get(name,set()):
            assert body==nfn[k],(name,k,"unrequested function changed")
            functions.append({"file":name,"function":k,"byte_body_unchanged":True,"sha256":hashlib.sha256(body).hexdigest()})
assert set(changed)=={"controller_common.py","controller.py","case_worker.py","seal_readonly.py","windows_debug_job_tree.py"}
rows=spec["roster"]
counts={"total":len(rows),"new":sum(r["new"] for r in rows),"original":sum(not r["new"] for r in rows),"resource_free":sum(not r["requires_resource"] for r in rows),"OS_dependent":sum(bool(r["requires_resource"]) for r in rows),"expected_RUN":sum(len(r["expected_records"]["run_records"]) for r in rows),"expected_PASS":sum(len(r["expected_records"]["pass_records"]) for r in rows),"expected_leaf":sum(len(r["expected_records"]["leaf_records"]) for r in rows)}
checks={
 "all_candidate_fixed_refs_match":all(x["matches"] for x in fixed),
 "64_candidate_manifest_members_match":len(new_members)==mf["member_count"]==64 and all(x["matches"] for x in new_members),
 "43_old_manifest_members_match":len(old_members)==old_mf["member_count"]==43 and all(x["matches"] for x in old_members),
 "49_roster_rows_byte_value_unchanged":rows==oldspec["roster"],
 "all_caps_unchanged":spec["caps"]==oldspec["caps"],
 "roster49_41_8_45_4_89_89_49":counts=={"total":49,"new":41,"original":8,"resource_free":45,"OS_dependent":4,"expected_RUN":89,"expected_PASS":89,"expected_leaf":49},
 "all_actual_rows_NOT_RUN":all(r["execution"]=="NOT_RUN" for r in rows),
 "original_finite_roster_raw_preserved":(S/"finite-roster.original.json").read_bytes()==(O/"finite-roster.json").read_bytes(),
 "exact4_source_pins_unchanged":spec["exact4_pins"]==oldspec["exact4_pins"],
 "false_grant_and_NULL_root_binding":grant["authorized"] is False and spec["root_binding"] is None and all(grant[k] is None for k in ["registration_evidence_ref","controller_review_ref","root_issuance_ref"]),
 "all_seven_role_refs_exact":spec["controller_refs"]==[spec[k] for k in ["common_ref","controller_ref","case_worker_ref","launcher_ref","sealer_ref","normal_helper_ref","debug_helper_ref"]],
 "launcher_and_normal_helper_byte_unchanged":all(x["candidate_ref"]["sha256"]==x["original_ref"]["sha256"] for x in inverses if x["name"] in ["launch.py","windows_owned_process.py"])
}
assert all(checks.values())
anchors=[]
for name,ranges in {"windows_debug_job_tree.py":[(108,119),(334,454),(550,616)],"controller_common.py":[(58,155),(157,208)],"controller.py":[(45,87),(155,185)],"seal_readonly.py":[(19,46)],"case_worker.py":[(9,29)]}.items():
    lines=(S/name).read_text(encoding="utf-8").splitlines()
    for a,z in ranges:anchors.append({"file":(S/name).as_posix(),"start":a,"end":z,"raw_lines":lines[a-1:z]})
treefiles={p.resolve() for p in C.rglob("*") if p.is_file() and p.name!="manifest.json"}
pinned={Path(r["path"]).resolve() for r in mf["members"]}
annexes=[pin(p) for p in sorted(treefiles-pinned)]
assert [Path(p["path"]).name for p in annexes]==["postseal-audit.json"]
before=create("inputs.before.json",{"schema":"researchos.w09.revision-review-inputs.v1","reviewer":ACTOR,"refs":reads[:]})
audit=create("static-source-audit.json",{"schema":"researchos.w09.controller-revision-independent-static-audit.v1","reviewer":ACTOR,
 "checks":checks,"candidate_original_ref_checks":fixed,"candidate_manifest_checks":new_members,"original_manifest_checks":old_members,
 "whole_byte_inverses":inverses,"unrequested_functions_byte_unchanged":functions,"parsed_AST_sources":descriptors,
 "counts":counts,"changed_modules":changed,"source_anchors":anchors,"candidate_manifest_scope":{"declared_members":64,"all_declared_members_verified":True,"postseal_annex_external_to_manifest":annexes,"actual_files_excluding_manifest":len(treefiles),"note":"Candidate handoff says excludes only itself, while postseal-audit is a separately pinned postseal annex, not one of64; do not count64 as65 or silently call manifest exhaustive over annex."},
 "C05_real_root_producer_currently_present":False,"candidate_imported_or_executed":False,"actual_target_exit":None,
 "candidate_tool_failure_origins":hdf["new_failure_origins"],"old_os206_recounted":False,
 "local_exec_command_failures":0,"coordination_failure_separate_ref":pin(OWN/"coordination-failure-origin.json"),
 "execution_counts":{"controller":0,"Job":0,"helper":0,"Go":0,"SQL":0,"network":0,"SDK_MODEL":0,"CAS":0,"Main_state_reads":0}})
afterchecks=[]
for r in reads[:]:
    p=Path(r["path"])
    if p.is_relative_to(OWN):continue
    a=pin(p);afterchecks.append({"before":r,"after":a,"unchanged":r==a})
assert all(x["unchanged"] for x in afterchecks)
after=create("inputs.after.json",{"schema":"researchos.w09.revision-review-input-stability.v1","checks":afterchecks,"all_fixed_inputs_unchanged":True})
print(json.dumps({"audit_ref":audit,"input_before_ref":before,"input_after_ref":after,"static_checks":checks,"unchanged_function_bodies":len(functions),"counts":counts},ensure_ascii=False))

