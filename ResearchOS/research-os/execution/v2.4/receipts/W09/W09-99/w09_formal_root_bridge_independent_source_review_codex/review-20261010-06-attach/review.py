from pathlib import Path
import ast,copy,hashlib,json,types,datetime
R=Path(r"D:\作品集\ResearchOS\research-os")
S=R/"execution/v2.4/receipts/W09/W09-99/w09_formal_root_bridge_source_codex/bridge-20261010-06"
O=Path(__file__).parent
G=R/"execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p):
    p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=sha(b),bytes=len(b))
def save(n,v):
    p=O/n
    with p.open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
    return pin(p)
def verified(ref):
    b=Path(ref["path"]).read_bytes()
    assert sha(b)==ref["sha256"] and len(b)==ref["bytes"],ref["path"]
    return b
checks=[]
def check(n,ok,detail=None):
    checks.append(dict(name=n,passed=bool(ok),detail=detail))
    assert ok,n
expected={"HDF.json":("0fda15ff927c164aca24e27a1ef92691f5a81e20838ac263a25fbcb0c9be265d",12135),
"MF.json":("26c766cfe71628f12f95efcbe13b9bd28a3c14c8adcab7fc28d911d2ae373962",9036),
"root-calling-contract.source.json":("435ffbc1df473b185aeef4747c34827241389b3ce5c0848039074a8fefb761fc",8278),
"w09_root_bridge.source.py":("59943073eb7c2e745d68acbe8b46e0031617de6d87fbe675584cb172de6ccd55",54832),
"consumer_launch.source.py":("c64deb904e746fd2d5df6775e0b96375ce36741315109d47ab86408360de5011",1493)}
for name,(digest,size) in expected.items():verified(dict(path=str(S/name),sha256=digest,bytes=size))
h=json.loads((S/"HDF.json").read_bytes());mf=json.loads((S/"MF.json").read_bytes())
refs={x["path"]:x for x in mf["members"]}
for name in ("HDF.json","MF.json"):refs[str(S/name)]=pin(S/name)
for key in ("base_source_ref","base_hdf_ref","base_mf_ref","independent_Request_Changes_decision_ref","independent_findings_ref","reused_BR5_controls_ref"):
    refs[h[key]["path"]]=h[key]
LIVE=[R/"execution/v2.4"/(n+".json") for n in ("checkpoint","path_ownership","step_state","commands")]
check("no_live_Canon_refs",all(Path(x["path"]) not in LIVE for x in refs.values()))
raw=G.read_bytes();check("guard_source_pin",sha(raw)=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85")
gm=types.ModuleType("br6_review_guard");exec(compile(raw,str(G),"exec"),gm.__dict__);guard=gm.SourceReadGuard()
error=None;closed=None
try:
    guard.acquire(list(refs.values()))
    source=guard.get_buffer(str(S/"w09_root_bridge.source.py"));base=guard.get_buffer(h["base_source_ref"]["path"])
    inv=json.loads(guard.get_buffer(str(S/"exact-inverse.json")))
    restored=source
    for index,block in enumerate(reversed(inv["replacement_blocks"])):
        after,before=block["after"].encode(),block["before"].encode()
        check("inverse_anchor_"+str(index),restored.count(after)==1)
        restored=restored.replace(after,before,1)
    check("complete_BR5_bytes_restored",restored==base)
    tree=ast.parse(source);oldtree=ast.parse(base)
    funcs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    oldfuncs={n.name:n for n in oldtree.body if isinstance(n,ast.FunctionDef)}
    changed=[n for n in oldfuncs if ast.dump(oldfuncs[n],include_attributes=False)!=ast.dump(funcs[n],include_attributes=False)]
    check("only_canonical_identity_changed",changed==["canonical_identity"] and set(funcs)==set(oldfuncs),changed)
    for t in (tree,oldtree):
        t.body=[n for n in t.body if not(isinstance(n,ast.FunctionDef) and n.name=="canonical_identity") and not(isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=="BRIDGE_GENERATION" for x in n.targets))]
    check("all_other_top_level_AST_unchanged",ast.dump(tree,include_attributes=False)==ast.dump(oldtree,include_attributes=False))
    base_launcher=Path(h["base_source_ref"]["path"]).with_name("consumer_launch.source.py")
    check("launcher_unchanged",guard.get_buffer(str(S/"consumer_launch.source.py"))==base_launcher.read_bytes())
    c=json.loads(guard.get_buffer(str(S/"delta-controls.json")))
    check("author22_reused_no_execution",c["count"]==c["passed"]==22 and c["failure"] is None and all(x["passed"] for x in c["checks"]))
    old=json.loads(guard.get_buffer(h["reused_BR5_controls_ref"]["path"]))
    check("BR5_36_reused",old["count"]==old["passed"]==36 and old["failure"] is None)
    for name in ("source-guard.closed.json","delta-source-guard.closed.json","seal-source-guard.closed.json"):
        v=json.loads(guard.get_buffer(str(S/name)))
        check(name,v["closed"] and v["retained_handles_count"]==0 and not v["errors"])
    # Extra independent path uses OW, whereas author's principal counterexample uses CP.
    fixture=S/"alias-fixture"
    names=("need","references","canonical_identity","validate_persistent_snapshot","historical_dependency_refs","request_dependency_refs","physical")
    ntree=ast.parse(source);nmap={n.name:n for n in ntree.body if isinstance(n,ast.FunctionDef)}
    canon=[fixture/"execution/v2.4"/(n+".json") for n in ("checkpoint","path_ownership","step_state","commands")]
    ns=dict(Path=Path,ROOT=fixture,CANON=canon,copy=copy,PLAN=fixture/"unused-plan")
    exec(compile(ast.Module(body=[nmap[n] for n in names],type_ignores=[]),"<BR6 independent pure OW edge>","exec"),ns)
    spelling="execution/v2.4/../../execution/v2.4/path_ownership.json"
    alias=dict(pin(canon[1]),path=spelling)
    req={"current4":[pin(p) for p in canon]}
    check("OW_nested_alias_agrees_with_physical",ns["canonical_identity"](spelling)==ns["physical"](spelling)==canon[1])
    def refusal(name,call,want):
        observed=None
        try:call()
        except ValueError as e:observed=str(e)
        check(name,observed==want,dict(observed=observed,expected=want,input_reference=alias))
    for kind in ("publication_ref","role_registry_input_ref"):
        refusal(kind+"_OW_alias",lambda kind=kind:ns["historical_dependency_refs"]({"nested":[{"origin":alias}]},{},req,kind),"UNDECLARED_HISTORICAL_CANONICAL_REFERENCE")
    refusal("snapshot_OW_alias",lambda:ns["validate_persistent_snapshot"]({"files":{spelling:alias["sha256"]}}),"HISTORICAL_SNAPSHOT_CONTAINS_CANON")
    refusal("request_OW_alias_exact_sha_conflict",lambda:ns["request_dependency_refs"](dict(req,extra=alias)),"REQUEST_CANONICAL_AUTHORITY_CONFLICT")
    check("literal_reference_spelling_retained",alias["path"]==spelling)
    binding=json.loads(guard.get_buffer(str(S/"actual-dcc9e2.binding.json")))
    lines=guard.get_buffer(str(S/"actual-dcc9e2.raw.jsonl")).splitlines(keepends=True)
    check("source_build_three_LF",len(lines)==3 and all(x.endswith(b"\n") for x in lines))
    with Path(binding["source_audit_path"]).open("rb") as f:
        for offset,digest,length,line in zip(binding["source_line_offsets"],binding["original_line_sha256"],binding["original_line_bytes"],lines):
            f.seek(offset)
            check("source_build_range_"+str(offset),f.readline()==line and sha(line)==digest and len(line)==length and offset+length<=binding["source_prefix_size_observed"])
    rows=[json.loads(x) for x in lines]
    check("source_build_actual_call_pair",rows[1]["payload"]["call_id"]==rows[2]["payload"]["call_id"]==binding["actual_call_id"])
    check("source_build_actual_0",binding["actual_outer_exit"]==binding["actual_python_exit"]==0 and "PYTHON_EXIT=0" in str(rows[2]["payload"]["output"]))
    contract=json.loads(guard.get_buffer(str(S/"root-calling-contract.source.json")))
    check("contract_exact_source_and_actor",contract["source_ref"]==h["source_ref"] and contract["consumer_launcher_ref"]==h["consumer_launcher_ref"] and contract["source_author_backend"]=="/root/full_w09_source_review" and contract["verifier_backend"]=="/root/backup_regression_resources")
except BaseException as exc:
    error=dict(type=type(exc).__name__,message=str(exc))
    raise
finally:
    closed=guard.close()
    save("source-guard.closed.json",closed)
    save("independent-checks.json",dict(schema="researchos.w09-br6-independent-source-checks.v1",checks=checks,passed=sum(x["passed"] for x in checks),count=len(checks),failure=error,
        author22_rerun=False,BR5_36_rerun=False,actual_Root_stages=0,actual_Main_calls=0,actual_Native_Go_SQL_TP_model_calls=0,live_Canon_readlocks=0))
assert closed["closed"] and closed["retained_handles_count"]==0 and not closed["errors"]
report=save("review-report.json",dict(schema="researchos.w09-br6-independent-source-review.v1",
    reviewer_id="/root/attach_restore_independent_review",reviewed_author="/root/full_w09_source_review",
    scope="BR5 history boundary plus BR6 alias remediation; historical Attach BR3 contribution disclosed and not newly self-certified.",
    decision="ACCEPTED_SOURCE_ONLY",closed_finding="BR5-HISTORICAL-CANON-ALIAS-001",
    source_hdf_ref=pin(S/"HDF.json"),source_mf_ref=pin(S/"MF.json"),source_ref=h["source_ref"],
    checks_ref=pin(O/"independent-checks.json"),source_guard_ref=pin(O/"source-guard.closed.json"),
    findings=[],new_original_failures=[],original1190_preserved=h["original1190_io"],
    original1185_preserved=h["original1185_io_preserved"],
    original1186_1187_1188_preserved=True,Source_build_outer_exit=0,Source_build_python_exit=0,
    author_controls_reused=22,BR5_controls_reused=36,old_controls_rerun=False,
    actual_Root_stages=0,actual_Main_Native_Go_SQL_TP_model_calls=0,live_Canon_readlocks=0,
    Main_Canon_Scope_written=False,formal_acceptance=False,execution_grant=False,STOP=True))
decision=save("review-decision.json",dict(schema="researchos.w09-bridge-independent-source-review.v1",
    reviewer_id="/root/attach_restore_independent_review",actor_role="INDEPENDENT_NON_AUTHOR_OF_REVIEWED_DELTA",
    source_ref=h["source_ref"],consumer_launcher_ref=h["consumer_launcher_ref"],
    source_hdf_ref=pin(S/"HDF.json"),source_mf_ref=pin(S/"MF.json"),
    decision="ACCEPTED_SOURCE_ONLY",formal_acceptance=False,execution_grant=False,
    closed_findings=["BR5-HISTORICAL-CANON-ALIAS-001"],findings=[],report_ref=report))
members=[pin(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in ("HDF.json","MF.json","postseal-tool-io.json")]
manifest=save("MF.json",dict(schema="researchos.w09-independent-source-review-manifest.v1",members=members,exclusions=["HDF.json","MF.json","postseal-tool-io.json"]))
handoff=save("HDF.json",dict(schema="researchos.w09-independent-source-review-handoff.v1",
    reviewer_id="/root/attach_restore_independent_review",reviewed_author="/root/full_w09_source_review",
    decision="ACCEPTED_SOURCE_ONLY",source_hdf_ref=pin(S/"HDF.json"),source_mf_ref=pin(S/"MF.json"),
    source_ref=h["source_ref"],consumer_launcher_ref=h["consumer_launcher_ref"],
    decision_ref=decision,report_ref=report,checks_ref=pin(O/"independent-checks.json"),
    manifest_ref=manifest,source_guard_ref=pin(O/"source-guard.closed.json"),
    closed_findings=["BR5-HISTORICAL-CANON-ALIAS-001"],independent_checks=len(checks),
    reused_author_controls=22,reused_BR5_controls=36,new_original_failures=[],
    guards_closed_zero=True,retained_handles_count=0,live_Canon_readlocks=0,
    actual_Root_stages=0,actual_Main_Native_Go_SQL_TP_model_calls=0,Main_Canon_Scope_written=False,
    formal_acceptance=False,parent_acceptance=False,execution_grant=False,
    actual_product_exits={k:None for k in ("Native","Go","SQL","dispatcher","model","TP")},STOP=True))
for r in members:verified(r)
print(json.dumps(dict(HDF=handoff,MF=manifest,decision=decision,report=report,checks=len(checks),
    decision_text="ACCEPTED_SOURCE_ONLY",closed=True,retained_handles_count=0),ensure_ascii=False))

