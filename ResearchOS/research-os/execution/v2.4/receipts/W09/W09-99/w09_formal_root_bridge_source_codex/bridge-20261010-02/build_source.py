"""Build a new Source candidate from exact bridge01 bytes; no runtime imports."""
import hashlib,json,os
from pathlib import Path
N=Path(__file__).resolve().parent
OLD=N.parent/"bridge-20261010-01"
def sha(raw):return hashlib.sha256(raw).hexdigest()
def pin(path):
 p=Path(path);b=p.read_bytes();return {"path":str(p),"sha256":sha(b),"bytes":len(b)}
def write(path,data,raw=False):
 with Path(path).open("xb") as out:
  out.write(data if raw else (json.dumps(data,ensure_ascii=False,indent=2)+"\n").encode());out.flush();os.fsync(out.fileno())
 return pin(path)
raw=(OLD/"w09_root_bridge.source.py").read_bytes()
assert sha(raw)=="7b11082d9938d1611fb74bca12945d188436501d5e905b97b0ee828939810a53" and len(raw)==36616
source=raw.decode();changes=[]
def replace(before,after):
 global source
 assert source.count(before)==1, before[:80]
 source=source.replace(before,after)
 changes.append({"before":before,"after":after})
replace('    for row in rows:\n        # All real Native runs/modes must pass Main before a new Scope or child.\n        profile._native(api._profile_api(), reader, row, closure, router, pinned, sources)\n',
'''    reader.bridge_native_checks = {}
    for row in rows:
        # All four selector Native runs must pass Main current Source21/mode gates.
        route = tuple(row[k] for k in ("command_key","check_id","case_id"))
        reader.bridge_native_checks[route] = profile._native(
            api._profile_api(), reader, row, closure, router, pinned, sources)
''')
helper='''
def consumer_plan(req, eng, context, pinned):
    """Choose four or six consumers only after Main has checked current Native evidence."""
    api, reader, profile = eng
    policy = req["c19_policy"]
    need(policy in {"REUSE_CURRENT_SOURCE21", "RUN_CURRENT_CM40"}, "C19_POLICY")
    proofs = getattr(reader, "bridge_native_checks", {})
    need(set(proofs) == set(ROUTES), "MAIN_CURRENT_NATIVE_GATE_REQUIRED")
    # Report identity and selector semantics are validated by Main _native, not by this map.
    selected = {}
    for row in context["registered_commands"]:
        key = row["check_id"] or row["case_id"]
        pair = (row["native_report_ref"]["path"], row["native_report_ref"]["sha256"],
                row["native_tool_run_ref"]["path"], row["native_tool_run_ref"]["sha256"])
        need(key not in selected or selected[key] == pair, "SAME_SELECTOR_NATIVE_BUNDLE")
        selected[key] = pair
    need(set(selected) == {"W09-G01","W09-G02","C19","A06"}
         and len({value[0] for value in selected.values()}) == 4, "FOUR_CURRENT_NATIVE_REPORTS")
    if policy == "RUN_CURRENT_CM40":
        return ROUTES
    # No fallback to stale history: a rejected Source21 or historical pin stops the stage.
    registry_path = reader.path("execution/v2.4/commands.json")
    registry = reader.read(registry_path)
    authority = document(req["c19_reuse_registry_ref"])
    need(authority["roles"]["executor"] == ROOT_ACTOR, "C19_REUSE_ACTUAL_EXECUTOR")
    for row in context["registered_commands"]:
        route = tuple(row[k] for k in ("command_key","check_id","case_id"))
        if route[2] != "C19":
            continue
        receipt = profile._doc(api._profile_api(), reader, row["receipt_ref"], "execution/invocations/")
        need(profile._historical_registry(api._profile_api(), reader, row, receipt, registry,
                                         pinned[registry_path]) is True, "ONLY_FIXED_CM39_C19_REUSE")
        report, native, mode, intervals = proofs[route]
        output = reader.document(receipt["stdout"])
        need(output.get("native_tool_run_ref") == row["native_tool_run_ref"]["path"]
             and output.get("mode_evidence") == mode
             and any(ref.get("path") == row["native_report_ref"]["path"]
                     and ref.get("sha256") == row["native_report_ref"]["sha256"]
                     for ref in output.get("source_pins", [])), "HISTORICAL_CONSUMER_SAME_NATIVE")
        decision = document(row["mode_decision_ref"])
        profile._route_execution_actor(api._profile_api(), reader, row, receipt, decision, authority)
    return NEW

'''
replace("def seed(req, out, eng):",helper+"def seed(req, out, eng):")
replace("    context, *_ = native_inputs(req, eng)\n    need(context[\"executor_id\"] == ROOT_ACTOR, \"ROOT_EXECUTOR\")",
'''    context, pinned, *_ = native_inputs(req, eng)
    planned = consumer_plan(req, eng, context, pinned)
    need(context["executor_id"] == ROOT_ACTOR, "ROOT_EXECUTOR")''')
replace('    routes = [dict(zip(("command_key","check_id","case_id"), route)) for route in NEW]',
'''    route_bindings = [dict(zip(("command_key","check_id","case_id"), route)) for route in planned]
    routes = list(dict.fromkeys(route[0] for route in planned))''')
replace('                 slice_id="W09_FULL_FORMAL_CONSUMERS", routes=routes)',
'                 slice_id="W09_FULL_FORMAL_CONSUMERS", routes=routes, route_bindings=route_bindings)')
replace('                 "source_ref": req["bridge_source_ref"], "source_review_ref": req["source_review_ref"]}',
'''                 "source_ref": req["bridge_source_ref"], "source_review_ref": req["source_review_ref"],
                 "route_bindings": route_bindings if name == "consumers" else []}''')
replace('    return {"schema": "researchos.w09-bridge-proposal.v1", "documents": docs,',
'''    return {"schema": "researchos.w09-bridge-proposal.v1", "documents": docs,
            "c19_policy": req["c19_policy"], "planned_routes": route_bindings,''')
replace('    proposal = document(req["proposal_ref"])\n    need(proposal["source_ref"]',
'''    proposal = document(req["proposal_ref"])
    need(proposal["c19_policy"] == req["c19_policy"], "PROPOSAL_C19_POLICY")
    need(proposal["source_ref"]''')
replace('    proposal = document(ref)\n    for name, refs in proposal["documents"].items():',
'''    proposal = document(ref)
    need(proposal["c19_policy"] == req["c19_policy"], "REGISTERED_C19_POLICY")
    for name, refs in proposal["documents"].items():''')
replace('    registered(req)\n    context, *_ = native_inputs(req, eng)\n    snap = snapshot(api, reader, context)',
'''    proposal = registered(req)
    context, pinned, *_ = native_inputs(req, eng)
    planned = consumer_plan(req, eng, context, pinned)
    need(proposal["planned_routes"] == [dict(zip(("command_key","check_id","case_id"), r)) for r in planned],
         "REGISTERED_EXACT_CONSUMER_ROUTES")
    snap = snapshot(api, reader, context)''')
replace('        if route[2] == "C19":\n            checked(row["receipt_ref"])  # Preserved exactly; never invoke old C19.\n            continue',
'''        if route not in planned:
            checked(row["receipt_ref"])  # Exact fixed history already passed Main current Source21 gates.
            continue''')
replace('            "formal_acceptance":False,"producer_rerun":False}',
'''            "formal_acceptance":False,"producer_rerun":False,"c19_policy":req["c19_policy"],
            "executed_consumer_routes":[list(route) for route in planned]}''')
candidate=source.encode()
inverse=source
for change in reversed(changes):
 assert inverse.count(change["after"])==1
 inverse=inverse.replace(change["after"],change["before"])
assert inverse.encode()==raw
write(N/"w09_root_bridge.source.py",candidate,True)
write(N/"exact-inverse.json",{"schema":"researchos.w09-bridge-c19-delta-inverse.v1",
 "base_ref":pin(OLD/"w09_root_bridge.source.py"),"candidate_ref":pin(N/"w09_root_bridge.source.py"),
 "edits":changes,"inverse_sha256":sha(inverse.encode()),"exact_inverse":True,
 "unmodified_base_hdf_ref":pin(OLD/"HDF.json"),"unmodified_base_mf_ref":pin(OLD/"MF.json")})
print(json.dumps({"candidate":pin(N/"w09_root_bridge.source.py"),"edits":len(changes),"exact_inverse":True},ensure_ascii=False))

