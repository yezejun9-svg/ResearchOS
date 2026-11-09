from pathlib import Path
import ast,copy,hashlib,json,types,os,datetime
R=Path(r"D:\作品集\ResearchOS\research-os")
S=R/"execution/v2.4/receipts/W09/W09-99/w09_formal_root_bridge_source_codex/bridge-20261010-05"
O=Path(__file__).parent
AUDIT=Path(r"C:\Users\yqyyds\.codex\sessions\2026\10\09\rollout-2026-10-09T08-25-26-01a11e0c-eef6-7363-a5b1-da61d6ae7f4c.jsonl")
G=R/"execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
def digest(b):return hashlib.sha256(b).hexdigest()
def enc(v):return (json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode()
def pin(p):
    p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=digest(b),bytes=len(b))
def save(name,v,raw=False):
    p=O/name
    with p.open("xb") as f:f.write(v if raw else enc(v))
    return pin(p)
def verify(ref):
    b=Path(ref["path"]).read_bytes()
    assert digest(b)==ref["sha256"] and len(b)==ref["bytes"],ref["path"]
    return b
checks=[];findings=[]
def check(name,ok,detail=None):
    checks.append(dict(name=name,passed=bool(ok),detail=detail))
    assert ok,name
expected={"HDF.json":("7cac259f230b60c691418b33495f4ae556efc310389e981018163825bce42147",9781),
"MF.json":("cb44561b31ca2e717ed56d644c0ef19ea0d7364c6367c6d65b7d8c4eadf98665",5499),
"root-calling-contract.source.json":("6205040fb970072529a109c802d44a50f155e130453d94d2a1aa342abf68a668",4652),
"w09_root_bridge.source.py":("e9e6aebaa88eb749576be8b68ebdd4fdeb202213111546437153d1d0739836b3",54789),
"consumer_launch.source.py":("c64deb904e746fd2d5df6775e0b96375ce36741315109d47ab86408360de5011",1493)}
for name,(sha,size) in expected.items():verify(dict(path=str(S/name),sha256=sha,bytes=size))
h=json.loads((S/"HDF.json").read_bytes());mf=json.loads((S/"MF.json").read_bytes())
refs={x["path"]:x for x in mf["members"]}
for name in ("HDF.json","MF.json"):refs[str(S/name)]=pin(S/name)
for key in ("base_source_ref","base_hdf_ref","base_mf_ref"):refs[h[key]["path"]]=h[key]
gb=G.read_bytes();check("pinned_guard_source",digest(gb)=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85")
gm=types.ModuleType("independent_br5_guard");exec(compile(gb,str(G),"exec"),gm.__dict__)
guard=gm.SourceReadGuard()
CANON=[R/"execution/v2.4"/(n+".json") for n in ("checkpoint","path_ownership","step_state","commands")]
check("no_live_canonical_pins",all(Path(x["path"]) not in CANON for x in refs.values()))
closed=None
try:
    guard.acquire(list(refs.values()))
    src=guard.get_buffer(str(S/"w09_root_bridge.source.py"))
    base=guard.get_buffer(h["base_source_ref"]["path"])
    inverse=json.loads(guard.get_buffer(str(S/"exact-inverse.json")))
    restored=src
    for block in reversed(inverse["replacement_blocks"]):
        a,b=block["after"].encode(),block["before"].encode()
        check("inverse_block_"+str(len(checks)),restored.count(a)==1)
        restored=restored.replace(a,b,1)
    check("independent_full_byte_inverse",restored==base)
    tree=ast.parse(src);oldtree=ast.parse(base)
    funcs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    oldfuncs={n.name:n for n in oldtree.body if isinstance(n,ast.FunctionDef)}
    changed=[k for k in oldfuncs if ast.dump(oldfuncs[k],include_attributes=False)!=ast.dump(funcs[k],include_attributes=False)]
    check("independent_changed_functions_exact",set(changed)=={"snapshot","propose","registration","registered","publish_registration","main"},changed)
    check("unchanged_launcher",guard.get_buffer(str(S/"consumer_launch.source.py"))==Path(h["base_source_ref"]["path"]).with_name("consumer_launch.source.py").read_bytes())
    controls=json.loads(guard.get_buffer(str(S/"delta-controls.json")))
    check("reuse_author_36_controls_without_replay",controls["passed"]==controls["count"]==36 and controls["failure"] is None and all(x["passed"] for x in controls["checks"]))
    for f in ("source-guard.closed.json","seal-source-guard.closed.json"):
        v=json.loads(guard.get_buffer(str(S/f)))
        check(f,v["closed"] and v["retained_handles_count"]==0 and not v["errors"])
    # Execute only four newly introduced pure classifiers and references/need.
    names=("need","references","canonical_identity","validate_persistent_snapshot","historical_dependency_refs","request_dependency_refs")
    ns={"Path":Path,"ROOT":R,"CANON":CANON,"copy":copy}
    exec(compile(ast.Module(body=[funcs[n] for n in names],type_ignores=[]),"<independent BR5 pure classifiers>","exec"),ns)
    req={"current4":[dict(path=str(p),sha256=str(i)*64,bytes=10) for i,p in enumerate(CANON)]}
    old=dict(req["current4"][0],sha256="f"*64)
    alias=R/"execution/v2.4/../v2.4/checkpoint.json"
    aliased=dict(old,path=str(alias))
    def rejects(call):
        try:call()
        except ValueError as e:return str(e)
        return None
    canonical_error=rejects(lambda:ns["historical_dependency_refs"]({"undeclared":old},{},req,"publication_ref"))
    check("exact_historical_canonical_reference_rejected",canonical_error=="UNDECLARED_HISTORICAL_CANONICAL_REFERENCE",canonical_error)
    outcomes={}
    for kind in ("publication_ref","role_registry_input_ref"):
        out=ns["historical_dependency_refs"]({"undeclared":aliased},{},req,kind)
        outcomes[kind]={"accepted":aliased in out,"normalized_identity":os.path.normpath(aliased["path"])}
    snapshot_out=ns["validate_persistent_snapshot"]({"files":{aliased["path"]:aliased["sha256"]}})
    request_out=ns["request_dependency_refs"](dict(req,extra=aliased))
    check("alias_counterexample_is_same_windows_path",Path(os.path.normpath(alias))==CANON[0])
    check("alias_counterexample_reproduced_without_live_reads",
          all(v["accepted"] for v in outcomes.values()) and aliased in request_out and aliased["path"] in snapshot_out["files"],
          outcomes)
    physical_text=ast.get_source_segment(src.decode(),funcs["physical"])
    main_text=ast.get_source_segment(src.decode(),funcs["main"])
    check("downstream_resolves_before_TP_skip",
          'path.resolve(strict=True)' in physical_text and
          'path=physical(ref["path"])' in main_text and
          'if args.stage in {"activate","publish-registration"} and path in CANON[:2]:' in main_text)
    findings.append(dict(id="BR5-HISTORICAL-CANON-ALIAS-001",priority="P2",
        title="Unnormalized historical Canon paths bypass explicit archive coverage rejection",
        source_ref=h["source_ref"],line=317,
        affected_functions=["canonical_identity","validate_persistent_snapshot","historical_dependency_refs","request_dependency_refs"],
        input=aliased,outcomes=outcomes,
        impact="An inline CP reference using ../ is not classified as Canon; main subsequently resolves it to CP and skips it for activate/publish-registration. The historical pin is neither archive-covered nor checked. Persistent snapshot aliases are also accepted. Fresh req.current4/TP CAS remain required; no claim of arbitrary Canon write bypass.",
        recommendation="Normalize or reject path aliases consistently before identity classification; retain fresh current4 physical checks and stage TP CAS. Reject undeclared historical Canon references and snapshot keys under all equivalent accepted path spellings.",
        pure_Source_fixture_only=True,actual_Root_stage_executed=False))
    # Verify actual Source build and original1185 provenance using captured byte ranges.
    for name in ("actual-233c90.binding.json","original-1185.binding.json"):
        binding=json.loads(guard.get_buffer(str(S/name)))
        raw=verify(binding["original_raw_ref"]);lines=raw.splitlines(keepends=True)
        check(name+"_three_LF",len(lines)==3 and all(x.endswith(b"\n") for x in lines))
        with Path(binding["source_audit_path"]).open("rb") as f:
            for offset,sha,size,line in zip(binding["source_line_offsets"],binding["original_line_sha256"],binding["original_line_bytes"],lines):
                f.seek(offset);got=f.readline()
                check(name+"_range_"+str(offset),got==line and digest(line)==sha and len(line)==size and offset+size<=binding["source_prefix_size_observed"])
        rows=[json.loads(x) for x in lines]
        check(name+"_call_identity",rows[1]["payload"]["call_id"]==rows[2]["payload"]["call_id"]==binding["actual_call_id"])
        if name.startswith("original"):
            check("original1185_exit_preserved",binding["actual_outer_exit"]==1 and all(binding[k] is None for k in ("actual_python_exit","actual_native_exit","actual_go_exit","actual_sql_exit","actual_dispatcher_exit","actual_model_exit")))
finally:
    closed=guard.close();save("source-guard.closed.json",closed)
check("independent_guard_closed_zero",closed["closed"] and closed["retained_handles_count"]==0 and not closed["errors"])
# Capture the two real reviewer read diagnostics without changing original evidence.
def capture_diagnostic(ordinal,needle,chunk=None):
    header=None;call=None;pair=None
    with AUDIT.open("rb") as f:
        while True:
            offset=f.tell();line=f.readline()
            if not line:break
            item=json.loads(line)
            if header is None:header=(offset,line,item)
            payload=item.get("payload",{})
            if payload.get("type") in ("function_call","custom_tool_call") and needle in line.decode("utf-8"):
                call=(offset,line,item)
            if call and payload.get("type") in ("function_call_output","custom_tool_call_output") and payload.get("call_id")==call[2]["payload"].get("call_id") and ((ordinal==1186 and b'Cannot find path' in line) or (ordinal==1187 and b'os error 123' in line)):
                pair=(call,(offset,line,item));break
    assert pair is not None,ordinal
    entries=[header,*pair];raw=b"".join(x[1] for x in entries)
    rr=save("original-"+str(ordinal)+".raw.jsonl",raw,True)
    binding=dict(schema="researchos.w09-resource-readonly-host-binding.v1",
        actor_id="/root/attach_restore_independent_review",actor_thread_id=header[2]["payload"]["id"],
        source_audit_path=str(AUDIT),source_prefix_size_observed=AUDIT.stat().st_size,
        source_line_offsets=[x[0] for x in entries],original_line_sha256=[digest(x[1]) for x in entries],
        original_line_bytes=[len(x[1]) for x in entries],original_raw_ref=rr,
        actual_call_id=pair[0][2]["payload"]["call_id"],original_ordinal=ordinal,
        actual_outer_exit=0,actual_python_exit=None,actual_native_exit=None,actual_go_exit=None,
        actual_sql_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,actual_TP_exit=None,
        product_calls=0,execution_grant=False,formal_acceptance=False)
    save("original-"+str(ordinal)+".binding.json",binding)
    return binding
diag1186=capture_diagnostic(1186,'Get-Content -LiteralPath \\"$p/calling-contract.json\\"')
diag1187=capture_diagnostic(1187,'review-20261010-04*')
report=dict(schema="researchos.w09-br5-independent-source-review.v1",
    reviewer_id="/root/attach_restore_independent_review",review_scope="BR5 delta authored by Full; inherited BR3 Attach contribution not self-certified",
    source_hdf_ref=pin(S/"HDF.json"),source_mf_ref=pin(S/"MF.json"),source_ref=h["source_ref"],
    decision="REQUEST_CHANGES",checks=checks,findings=findings,
    author_controls_reused=36,author_controls_rerun=False,actual_Root_stages=0,
    actual_Main_Native_Go_SQL_TP_model_calls=0,live_Canon_readlocks=0,
    new_original_diagnostics=[1186,1187],source_original_failure_preserved=1185,
    source_guard_ref=pin(O/"source-guard.closed.json"),formal_acceptance=False,execution_grant=False)
save("review-report.json",report)
save("review-decision.json",dict(schema="researchos.w09-bridge-independent-source-review.v1",
    reviewer_id="/root/attach_restore_independent_review",source_ref=h["source_ref"],
    consumer_launcher_ref=h["consumer_launcher_ref"],source_hdf_ref=pin(S/"HDF.json"),
    source_mf_ref=pin(S/"MF.json"),decision="REQUEST_CHANGES",formal_acceptance=False,
    findings=findings,report_ref=pin(O/"review-report.json")))
print(json.dumps(dict(decision="REQUEST_CHANGES",report_ref=pin(O/"review-report.json"),
decision_ref=pin(O/"review-decision.json"),checks=len(checks),findings=[x["id"] for x in findings],
closed=closed["closed"],retained_handles_count=closed["retained_handles_count"]),ensure_ascii=False))

