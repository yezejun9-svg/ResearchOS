from pathlib import Path
import ast,difflib,hashlib,json,re
ROOT=Path("D:/作品集/ResearchOS/research-os")
OUT=Path(__file__).parent
NS=ROOT/"execution/v2.4/receipts/W05/W05-99/wholeGo_root_cap_producer_source_v3_codex/baa0423d87784ee0bbf526de45a20a8c"
checks=[]
def pin(p):
    b=p.read_bytes()
    return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def check(name,value,detail=None):
    checks.append({"check":name,"pass":bool(value),"detail":detail})
def get(ref):
    p=Path(ref["path"]); b=p.read_bytes()
    check("ref:"+str(p),hashlib.sha256(b).hexdigest()==ref["sha256"] and len(b)==ref["bytes"])
    return b
def write(name,value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode()
    with (OUT/name).open("xb") as f:f.write(raw)
    return pin(OUT/name)
handoff=json.loads((NS/"handoff.json").read_bytes())
check("handoff fixed",pin(NS/"handoff.json")["sha256"]=="210006ef0173b0a6682f2f84e79bad70c228fb984e5917811cda53e17bc290c4")
mf=json.loads(get(handoff["manifest_ref"]))
check("manifest actual cardinality",mf["count"]==len(mf["members"])==9)
for r in mf["members"]:get(r)
report=json.loads(get(handoff["report_ref"]))
old=get(report["basis"]["previous_source"])
get(report["basis"]["independent_request"])
new=get(handoff["source_ref"])
tree=ast.parse(new.decode()); oldtree=ast.parse(old.decode())
funcs={x.name:x for x in tree.body if isinstance(x,ast.FunctionDef)}
check("candidate AST parse",bool(funcs))
patch=get(handoff["inverse_ref"]).decode().splitlines(keepends=True)
def apply_patch_data(base,patch):
    lines=base.decode().splitlines(keepends=True); result=[]; pos=0; i=2
    while i<len(patch):
        m=re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@",patch[i])
        if not m: raise ValueError("non-hunk patch")
        start=int(m[1])-1; result.extend(lines[pos:start]);pos=start;i+=1;rem=add=0
        while i<len(patch) and not patch[i].startswith("@@ "):
            row=patch[i]; i+=1
            if row[0] in " -":
                if lines[pos]!=row[1:]:raise ValueError("patch original mismatch")
                pos+=1;rem+=1
            if row[0] in " +":result.append(row[1:]);add+=1
        if rem!=int(m[2] or 1) or add!=int(m[4] or 1):raise ValueError("hunk count mismatch")
    result.extend(lines[pos:]);return "".join(result).encode()
check("whole inverse v3 to v2 exact",apply_patch_data(new,patch)==old)
forward=get(handoff["forward_ref"]).decode().splitlines(keepends=True)
check("whole forward v2 to v3 exact",apply_patch_data(old,forward)==new)
def calls(name,method):
    return [x for x in ast.walk(funcs[name]) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr==method]
check("verified_raw exactly one read_bytes",len(calls("verified_raw","read_bytes"))==1)
check("verified_json no filesystem reread",len(calls("verified_json","read_bytes"))==0)
check("verified_json parses returned verified raw","return unique_json(verified_raw(ref))" in ast.get_source_segment(new.decode(),funcs["verified_json"]))
check("implementation consumed as raw","verified_raw(source[\"implementation_ref\"])" in new.decode())
check("controller consumed as raw","verified_raw(controller_source)" in new.decode())
check("canonical reparse guard before read",new.index(b"p = canonical(ref[\"path\"])")<new.index(b"raw = p.read_bytes()",new.index(b"def verified_raw")))
check("output identity before producer and writes",new.index(b"identity(source, stage, output_dir)")<new.index(b'output = {"attestation.json"')<new.index(b"refs = {name: put_new"))
check("output files exclusive create",'path.open("xb")' in new.decode())
selected=ROOT/"execution/v2.4/receipts/W05/W05-99/current58_whole_go_suite_configuration_sync_source_preparation_codex/4a8dca58606d4a4db695aa6dc9f082cb"
sh=json.loads((selected/"handoff.selected.json").read_bytes())
for r in sh["selected_source_refs"].values():get(r)
execution=json.loads(get(sh["selected_source_refs"]["execution_contract"]))
gate=get(sh["selected_source_refs"]["gate"]).decode()
runner=get(sh["selected_source_refs"]["runner"]).decode()
for key in ("execution_contract","runner","gate"):
    ref=sh["selected_source_refs"][key]
    check("fixed selected path/hash:"+key,Path(ref["path"]).name in new.decode() and ref["sha256"] in new.decode())
check("13 declared budget keys",len(execution["numeric_budget_keys"])==13)
for field in ("scope_ref","registration_ref","grant_ref","owner_lease_ref","source_review_ref","outer_job_ref","meter_ref","path_authority_ref","checkpoint_ref"):
    check("authority producer/consumer field:"+field,('"'+field+'"') in ast.get_source_segment(new.decode(),funcs["arm"]) and ('"'+field+'"') in gate)
for field in ("runner_report_ref","runner_terminal_ref","root_invocation_ref","outer_job_final_ref","meter_final_ref","authority_bundle_ref"):
    check("closure independently pinned:"+field,('"'+field+'"') in ast.get_source_segment(new.decode(),funcs["close"]))
check("same report and terminal actual basenames",'run_output / "report.json"' in new.decode() and 'run_output / "terminal.json"' in new.decode() and 'output / "report.json"' in runner and 'output / "terminal.json"' in runner)
check("canonical checkpoint anchored",str(CHECKPOINT:="execution/v2.4/checkpoint.json") in new.decode())
check("actual controller and review required",'controller_actual_review_ref' in new.decode() and 'ACTUAL_CONTROLLER_RECEIPT_REVIEWED' in new.decode())
check("precise creation integer",'"pid_creation_filetime_100ns")) is int' in new.decode())
check("heartbeat typed fresh",'"monotonic_tick")) in (int, float)' in new.decode() and "0 <= age <= 5" in new.decode())
check("two-phase attestation review acyclic",new.index(b"def attest")<new.index(b"def scope") and '"attestation_ref") == source["go_tree_attestation_ref"]' in new.decode())
template=json.loads(get(handoff["root_input_template_ref"]))
for k in ("run_uuid","scope_ref","grant_ref","controller_source_ref","controller_actual_receipt_ref","root_allocation_ref","root_allocation_review_ref"):
    check("future open:"+k,template[k] is None)
check("no process spawn in proposal",not any(isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr in ("Popen","run","CreateProcessW") for x in ast.walk(tree)))
proc=ast.get_source_segment(new.decode(),funcs["observed_windows_process"])
check("known limitation no exited status guard","GetExitCodeProcess" not in proc and "exited.high" not in proc and "exited.low" not in proc)
findings=[{"id":"CAP3-R01","severity":"BLOCKER","file_ref":handoff["source_ref"],"lines":[103,124,438,488],
"title":"PID existence and Job membership do not prove that the runner is still active",
"evidence":"GetProcessTimes fills the exited FILETIME but it is never inspected; no GetExitCodeProcess/STILL_ACTIVE check is made. A terminated process retained by an open process/Job handle can still be queried and retain its creation identity and Job membership.",
"impact":"arm may label OBSERVED_LIVE_PID_AND_CREATION and publish an authority bundle for a PID that has already exited; the downstream runner cannot consume this bundle. This does not prove an actual execution bypass, and no candidate was run.",
"requested_change":"After querying identity and membership, require a typed successful liveness observation (e.g. GetExitCodeProcess == STILL_ACTIVE together with zero exit FILETIME) before returning. Keep handle cleanup in finally and label the result point-in-time only. Add a pure-data/structural negative check for an exited PID with retained handle, and a positive suspended/running PID case without importing the candidate."}]
matrix=[
{"prior":"CAP2-R01","status":"CLOSED_STATIC","basis":"verified_raw/verified_json split; implementation/controller source read only as raw; Go executable actual pin"},
{"prior":"CAP2-R02","status":"CLOSED_STATIC","basis":"Each JSON parse uses exactly the bytes returned by verified_raw; repeated validations separately verify their own bytes"},
{"prior":"CAP2-R03","status":"PARTIAL_REQUEST_CAP3_R01","basis":"Selected source constants, canonical checkpoint, active lease/worktree, registration/review/grant joins, actual controller and nonauthor review, creation identity/heartbeat now bound; exited PID not excluded"},
{"prior":"CAP2-R04","status":"CLOSED_STATIC_WITH_RUNTIME_OPEN","basis":"Allocated report/terminal basenames, scope/authority/ref joins, numeric counts, actual nullable exit, ordered monotonic finalization and zero remaining process/handle checks; no workload acceptance promoted"},
{"prior":"CAP2-R05","status":"CLOSED_STATIC","basis":"Root allocation and independent review, all path ancestors reject reparse/alias, stage path exact/fresh, checks before xb writes"}]
audit=write("audit.json",{"schema":"researchos.whole-go-cap-v3-independent-static-audit.v1","checks":checks,"check_count":len(checks),"all_static_checks_pass":all(x["pass"] for x in checks),"candidate_imported":False,"candidate_executed":False,"pure_data_counterexamples":[{"name":"retained handle after process exit","queryable":True,"job_member":True,"creation_filetime_matches":True,"exit_filetime_nonzero":True,"current_predicate_inspects_exit":False,"expected_active":False,"method":"semantic Windows API/source review, no OS query or candidate execution"}]})
review=write("review.json",{"schema":"researchos.whole-go-root-cap-independent-source-review.v1","reviewer":"codex:/root/w05_merge_review","decision":"REQUEST_CHANGES","source_ref":handoff["source_ref"],"source_handoff_ref":pin(NS/"handoff.json"),"source_manifest_ref":handoff["manifest_ref"],"prior_review_ref":report["basis"]["independent_request"],"audit_ref":audit,"requested_changes":findings,"prior_request_disposition":matrix,"positive_chain":"Root allocated paths and review -> native Go hash receipt -> attestation -> independent review -> pinned scope -> registered canonical checkpoint/lease and grant -> suspended/live runner controlled by separately reviewed controller -> actual controller receipt/review -> arm bundle -> one runner -> close.","open_conditions":["Actual Root allocation, limits and reviews remain NULL in template.","Actual native hash/controller/meter/OS lifecycle receipts are not produced by this source proposal.","Root stage/controller/caller must materialize canonical Windows Path string spellings for exact refs; no blanket ABS or slash normalization.","source_manifest must be the Root adopted union with exact selected runner/gate/execution/finite refs and gate-required schema.","Runtime catalog and full current source closure need future live validation; no current resource trees were rehashed here.","Fixed REAL_MODEL_B01_HOLD remains excluded; no SDK substitute or provider call authorized."],"actual_grant":False,"actual_source_acceptance":False,"whole_suite_qualified":False,"formal_case_accepted_delta":0,"new_failure_count":0,"source_actor":"codex:/root/live_resource_lookup","independent":True})
files=[pin(p) for p in sorted(OUT.iterdir()) if p.is_file()]
manifest=write("manifest.json",{"schema":"researchos.public-review-manifest.v1","count":len(files),"entries":files,"self_excluded":True})
h=write("handoff.json",{"schema":"researchos.whole-go-cap-v3-independent-review-handoff.v1","review_ref":review,"manifest_ref":manifest,"audit_ref":audit,"decision":"REQUEST_CHANGES","new_failure_count":0,"status":"STOPPED","candidate_execution_count":0})
print(json.dumps({"review_ref":review,"manifest_ref":manifest,"handoff_ref":h,"check_count":len(checks),"failed_checks":[x for x in checks if not x["pass"]]},ensure_ascii=False))

