"""Scope7 failed-once lease close. Draft is metadata only; CAS is Root-only."""
import sys
sys.dont_write_bytecode = True
import argparse, copy, datetime, hashlib, json, os, traceback, types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[7]
SRC = Path(__file__).resolve().parent
CAS = ROOT / "execution/v2.4/receipts/W13/W13-03/desktop58_scope7_failed_lease_close_cas_codex/b342fa5adb1e42d8813317e11e9f22c0"
CANON = [f"execution/v2.4/{name}.json" for name in ("checkpoint", "path_ownership", "step_state", "commands")]
BEFORE = [339, 167, 645]
AFTER = [340, 168, 672]
UID = "9eccde97a9fa4815941768cacaf590dc"
STATE = "FAILED_EXECUTION_CLOSED_QUALIFICATION_WITHHELD"

def need(condition, message):
    if not condition: raise RuntimeError(message)

def safe(value, exists=True):
    p = Path(value)
    if not p.is_absolute(): p = ROOT / p
    need(".." not in p.parts and p.is_relative_to(ROOT) and p != ROOT, "outside ResearchOS")
    need(p.resolve(strict=exists) == p.absolute(), "path alias")
    for x in (p, *p.parents):
        if os.path.lexists(x): need(not x.is_symlink() and not (getattr(x.lstat(), "st_file_attributes", 0) & 0x400), "reparse path")
        if x == ROOT: break
    return p

def parse(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            need(key not in out, "duplicate JSON key"); out[key] = value
        return out
    return json.loads(raw.decode("utf8"), object_pairs_hook=pairs, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))

def encode(value): return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf8")

def pin(p):
    p = safe(p)
    raw = p.read_bytes()
    return {"path": p.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def verify(ref):
    need(type(ref) is dict and set(ref) == {"path", "sha256", "bytes"}, "exact three-field pin")
    p = Path(ref["path"])
    p = safe(p) if not p.is_absolute() or p.is_relative_to(ROOT) else p
    raw = p.read_bytes()
    need(len(raw) == ref["bytes"] and hashlib.sha256(raw).hexdigest() == ref["sha256"], "pin mismatch: " + str(p))
    return raw

def doc(ref): return parse(verify(ref))

def save(p, raw):
    p = safe(p, False)
    if not isinstance(raw, bytes): raw = encode(raw)
    with p.open("xb") as f: f.write(raw); f.flush(); os.fsync(f.fileno())
    return pin(p)

def load(ref, name):
    raw = verify(ref)
    mod = types.ModuleType(name); mod.__file__ = str(Path(ref["path"]) if Path(ref["path"]).is_absolute() else safe(ref["path"]))
    exec(compile(raw, mod.__file__, "exec"), mod.__dict__)
    return mod

def differences(a, b, path=""):
    if a == b: return []
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for key in sorted(set(a) | set(b)):
            child = path + "/" + key.replace("~", "~0").replace("/", "~1")
            if key not in a or key not in b: out.append(child)
            else: out += differences(a[key], b[key], child)
        return out
    return [path]

def live_four(raws):
    need(len(raws) == 4 and all(safe(path).read_bytes() == raw for path, raw in zip(CANON, raws)), "four canonical byte pins changed")

def preflight(q, request_hash, source_hash):
    keys = {"schema", "actor", "namespace", "run_uuid", "before", "after", "main_git", "canonical_before", "scope_ref", "binding_ref", "review_ref", "root_resume_ref", "origin_map_ref", "pipeline_ref", "helper_ref", "python_pin", "formal_increment", "execution_grant", "counter_reset", "automatic_retry", "amended_at", "source_ref"}
    need(set(q) == keys and q["schema"] == "researchos.scope7-failed-lease-close-input.v1", "request shape")
    need(q["actor"] == "codex:/root" and q["namespace"] == CAS.relative_to(ROOT).as_posix() and q["run_uuid"] == UID, "actor/namespace/uid")
    need(q["before"] == BEFORE and q["after"] == AFTER and q["formal_increment"] == 0 and q["execution_grant"] is False and q["counter_reset"] is False and q["automatic_retry"] is False, "fixed transition")
    need(hashlib.sha256(safe(CAS / "original-input.json").read_bytes()).hexdigest() == request_hash, "request hash")
    need(q["source_ref"] == pin(__file__) and q["source_ref"]["sha256"] == source_hash, "source hash")
    need(sys.flags.isolated == 1 and sys.flags.no_site == 1 and sys.flags.utf8_mode == 1, "pinned isolated Python flags")
    verify(q["python_pin"])
    need(Path(sys.executable).resolve() == Path(q["python_pin"]["path"]).resolve(), "Python executable")
    need(datetime.datetime.fromisoformat(q["amended_at"]).utcoffset() == datetime.timedelta(0), "UTC amendment")
    need([r["path"] for r in q["canonical_before"]] == CANON, "canonical order")
    before = [verify(ref) for ref in q["canonical_before"]]
    live_four(before)
    cp, ow = map(parse, before[:2]); lease = ow["card_path_bindings"]["W13-03"]["subtasks"]["desktop58_finite_validation"]
    need([cp["revision"], ow["revision"], len(cp["failure_counters"])] == BEFORE and cp["head"] == q["main_git"]["head"], "current tuple/head")
    need(cp["work_in_progress"]["desktop58_finite_validation_state"] == "REGISTERED_PENDING_ONCE_EXECUTION", "current WIP")
    need(lease == {"owner":"codex:/root", "current_source_writer":None, "state":"REGISTERED_PENDING_ONCE_EXECUTION", "scope_ref":q["scope_ref"], "run_uuid":UID, "source_commit":q["main_git"]["head"]}, "exact active Scope7 lease")
    need(cp["work_in_progress"]["desktop58_finite_validation_scope_ref"] == q["scope_ref"], "Scope7 current ref")
    scope = doc(q["scope_ref"]); binding = doc(q["binding_ref"])
    need(binding["run_uuid"] == UID and binding["main_git"] == q["main_git"] and binding["owned_process_helper_ref"] == q["helper_ref"] and q["pipeline_ref"] in binding["metadata_code_refs"], "original binding")
    need(scope["run_uuid"] == UID and scope["main_git"] == q["main_git"], "original scope")
    prefix = doc(binding["failure_prefix430_ref"])["failure_counters"]
    need(len(prefix) == 430 and cp["failure_counters"][:430] == prefix, "original 430 prefix")
    review = doc(q["review_ref"])
    need(review["reviewer_id"] == "codex:/root/w05_merge_review" and review["decision"] == "FAILED_ONCE_EVIDENCE_CLOSED_FOR_LEASE_REVIEW" and review["independent_checks"] == 49 and review["failed_checks"] == [], "independent failure review")
    need(review["run_uuid"] == UID and review["scope_ref"] == q["scope_ref"] and review["failure_count"] == 669 and review["frozen_origin_cut"] == 645, "review scope/cut")
    need(review["actual_exit_chain"] == {"outer_tool":1,"root_python":1,"launcher_native":1,"controller_native":1,"builder_native":3758097160}, "failed native exit chain")
    need(review["first_rejected_load"]["before"] == {"sha256":"bb3e638c8b5b6ef80847e364aeef2796cad25d3539cf9b41d3820fa48943e777","bytes":81920}, "unexpected net.exe pin")
    need(review["lifecycle_closure"]["create_events"] == 806 and review["lifecycle_closure"]["exit_events"] == 806 and review["lifecycle_closure"]["owned_handle_count"] == 8967, "paired process evidence")
    need(review["incomplete_qualification_preserved"]["debug_complete"] is False and review["not_started"]["remaining_top_native_commands"] == 173 and review["not_started"]["offscreen_controls_declared"] == 2, "failed capture/not-started evidence")
    need(review["source_acceptance"] is False and review["formal_increment"] == 0 and review["zero_later_results"]["case_rows"] == 0, "qualification withheld")
    root_resume = doc(q["root_resume_ref"])
    need(root_resume["canonical_tuple"] == BEFORE, "Root observed preclose tuple")
    origins = doc(q["origin_map_ref"])
    need(origins["run_uuid"] == UID and origins["frozen_before"] == 645 and origins["observed_through"] == 672 and origins["row_count"] == 27, "full origin map cut")
    need([x["failure_index"] for x in origins["rows"]] == list(range(646,673)), "27 contiguous origins")
    old = {x.get("origin_key") or x.get("evidence_ref", {}).get("sha256") for x in cp["failure_counters"]}; rows = []
    for entry in origins["rows"]:
        ref = entry["evidence_ref"]; payload = doc(ref)
        need(ref["sha256"] not in old, "already registered origin")
        old.add(ref["sha256"])
        provenance = entry["count_provenance"]
        if provenance.get("mapping_ref") is not None: verify(provenance["mapping_ref"])
        rows.append({"origin_key":ref["sha256"],"evidence_ref":ref,"original_payload":payload,"counter_reset":False,"counted_once":True,"automatic_retry":False})
    return before, cp, ow, binding, rows

def desired(q, cp, ow, rows):
    nc, no = copy.deepcopy(cp), copy.deepcopy(ow)
    nc.update(revision=340, expected_previous_revision=339, updated_at=q["amended_at"], updated_by="codex:/root")
    nc["failure_counters"].extend(copy.deepcopy(rows))
    nc["work_in_progress"].update(desktop58_finite_validation_state=STATE, desktop58_finite_validation_failed_closure_review_ref=q["review_ref"], desktop58_finite_validation_failed_closure_root_ref=q["root_resume_ref"])
    no.update(revision=168, amended_at=q["amended_at"], amended_by="codex:/root")
    lease = no["card_path_bindings"]["W13-03"]["subtasks"]["desktop58_finite_validation"]
    lease.update(state=STATE, failed_closure_review_ref=q["review_ref"], failed_closure_root_ref=q["root_resume_ref"], execution_grant=False, qualification=False, formal_increment=0)
    need(nc["failure_counters"][:645] == cp["failure_counters"] and len(nc["failure_counters"]) == 672, "645 exact prefix plus 27")
    cd, od = differences(cp,nc), differences(ow,no)
    ca = {"/revision","/expected_previous_revision","/updated_at","/updated_by","/failure_counters","/work_in_progress/desktop58_finite_validation_state","/work_in_progress/desktop58_finite_validation_failed_closure_review_ref","/work_in_progress/desktop58_finite_validation_failed_closure_root_ref"}
    ob = "/card_path_bindings/W13-03/subtasks/desktop58_finite_validation/"
    oa = {"/revision","/amended_at","/amended_by",ob+"state",ob+"failed_closure_review_ref",ob+"failed_closure_root_ref",ob+"execution_grant",ob+"qualification",ob+"formal_increment"}
    for base in ("/work_in_progress/desktop58_finite_validation_failed_closure_review_ref/","/work_in_progress/desktop58_finite_validation_failed_closure_root_ref/"): ca.update(base + x for x in ("path","sha256","bytes"))
    need(set(cd) <= ca and set(od) <= oa, "pointer allowlist")
    return nc,no,cd,od

def draft(q, ctx):
    before, cp, ow, binding, rows = ctx
    need({x.name for x in CAS.iterdir()} == {"original-input.json"}, "fresh draft namespace")
    save(CAS / "draft.started.json", {"actor":"codex:/root","once":True,"input_ref":pin(CAS/"original-input.json"),"source_ref":pin(__file__)})
    cut = save(CAS/"origin-cut.json", {"schema":"researchos.failure-origin-cut.v1","owner":"codex:/root","before":BEFORE,"after":AFTER,"origins":rows,"counter_reset":False})
    pipeline = load(q["pipeline_ref"], "reviewed_metadata_pipeline")
    need(pipeline.origins({"origin_cut_ref":cut,"before":BEFORE,"after":AFTER}, cp) == rows, "reviewed opaque pipeline origins")
    nc,no,cd,od = desired(q,cp,ow,rows)
    targets = [encode(nc),encode(no),before[2],before[3]]
    originals = [save(CAS/(Path(path).stem+".before.json"),raw) for path,raw in zip(CANON,before)]
    desired_refs = [save(CAS/(Path(path).stem+".desired.json"),raw) for path,raw in zip(CANON,targets)]
    audit = save(CAS/"audit.json", {"schema":"researchos.scope7-failed-lease-close-audit.v1","actor":"codex:/root","before":BEFORE,"after":AFTER,"changed_checkpoint_pointers":cd,"changed_ownership_pointers":od,"original_645_prefix_equal":True,"append_origin_indices":list(range(646,673)),"origin_map_ref":q["origin_map_ref"],"failure_review_ref":q["review_ref"],"root_resume_ref":q["root_resume_ref"],"step_state_commands_byte_identical":True,"first_cause":"net.exe outside frozen runtime universe","debug_complete":False,"remaining_top_native_commands":173,"offscreen_controls_separate":2,"formal_increment":0,"source_acceptance":False,"execution_grant":False,"automatic_retry":False,"counter_reset":False,"canonical_writes":0,"native_product_calls":0})
    live_four(before)
    prepared = save(CAS/"prepared.json", {"schema":"researchos.scope7-failed-lease-close-prepared.v1","actor":"codex:/root","input_ref":pin(CAS/"original-input.json"),"source_ref":pin(__file__),"before":BEFORE,"after":AFTER,"original_refs":originals,"desired_refs":desired_refs,"origin_cut_ref":cut,"audit_ref":audit,"formal_increment":0,"execution_grant":False})
    manifest = save(CAS/"manifest.draft.json", {"schema":"researchos.receipt-manifest.v1","owner":"codex:/root","purpose":"Scope7 failed-once metadata lease close","members":[pin(p) for p in sorted(CAS.iterdir()) if p.is_file()],"self_excluded":True})
    print(json.dumps({"prepared_ref":prepared,"manifest_ref":manifest,"audit_ref":audit,"canonical_writes":0,"native_product_calls":0},ensure_ascii=False))

def job_ok(r):
    need(isinstance(r,dict) and r["actual_exit"] == 0 and r["error"] is None and not r["timed_out"] and r["resumed"] is True, "owned Git native exit")
    c = r["job_cleanup"]
    need(c["errors"] == [] and c["active_processes_last_observed"] == 0 and all(c[k] is True for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed")), "owned Git cleanup")

def git_guard(q,b,label):
    helper = load(q["helper_ref"], "scope7_owned_git")
    lock = doc(b["toolchain_lock_ref"])["tools"]
    git = lock["git"]
    verify({"path":git["path"],"sha256":git["sha256"],"bytes":46480})
    env = dict(b["public_environment"])
    env.update(GIT_OPTIONAL_LOCKS="0",GIT_NO_REPLACE_OBJECTS="1",GIT_CONFIG_NOSYSTEM="1",GIT_CONFIG_GLOBAL="nul",GIT_TERMINAL_PROMPT="0",GIT_CONFIG_COUNT="2",GIT_CONFIG_KEY_0="core.fsmonitor",GIT_CONFIG_VALUE_0="false",GIT_CONFIG_KEY_1="core.untrackedCache",GIT_CONFIG_VALUE_1="false")
    outputs = []
    for kind,args in (("head",["rev-parse","HEAD"]),("status",["status","--porcelain=v1","--untracked-files=no"]),("index",["diff","--cached","--name-only"])):
        stdout = CAS/(label+"."+kind+".stdout.raw"); stderr = CAS/(label+"."+kind+".stderr.raw")
        argv = [git["path"]]+args; result = None; error = None
        try:
            with stdout.open("xb") as out, stderr.open("xb") as err: result = helper.run_owned(argv,str(ROOT),env,out,err,30)
        except BaseException as exc: error = repr(exc); raise
        finally:
            save(CAS/(label+"."+kind+".invocation.json"),{"actor":"codex:/root","argv":argv,"cwd":str(ROOT),"public_environment":env,"result":result,"wrapper_error":error,"actual_stage_native_exit":result["actual_exit"] if result else None,"stdout_ref":pin(stdout) if stdout.exists() else None,"stderr_ref":pin(stderr) if stderr.exists() else None,"qualifies_product_runtime":False})
        job_ok(result); outputs.append(stdout.read_bytes())
    need(outputs[0].decode("ascii").strip() == q["main_git"]["head"] and outputs[2] == b"", "Main head/index")
    need(hashlib.sha256(outputs[1]).hexdigest() == q["main_git"]["status_sha256"] and len(outputs[1]) == q["main_git"]["status_bytes"], "tracked Git status")

def commit(q,review_ref,ctx):
    before,cp,ow,b,rows = ctx
    prepared_ref = pin(CAS/"prepared.json"); p = doc(prepared_ref); review = doc(review_ref)
    need(review["schema"] == "researchos.scope7-failed-lease-close-cas-review.v1" and review["reviewer_id"] == "codex:/root/w05_merge_review" and review["decision"] == "READY_FOR_ROOT_SCOPE7_FAILED_LEASE_CLOSE_CAS_ONCE" and review["requested_changes"] == [] and review["actual_cas_executed"] is False, "independent Source/CAS review")
    need(review["prepared_ref"] == prepared_ref and review["source_ref"] == pin(__file__) and review["input_ref"] == pin(CAS/"original-input.json") and review["manifest_ref"] == pin(CAS/"manifest.draft.json"), "reviewed exact draft")
    need(p["source_ref"] == pin(__file__) and p["input_ref"] == pin(CAS/"original-input.json") and p["before"] == BEFORE and p["after"] == AFTER, "prepared exact Source/request")
    for ref in doc(pin(CAS/"manifest.draft.json"))["members"]: verify(ref)
    need([verify(ref) for ref in p["original_refs"]] == before, "prepared before")
    nc,no,cd,od = desired(q,cp,ow,rows)
    targets = [encode(nc),encode(no),before[2],before[3]]
    need([verify(ref) for ref in p["desired_refs"]] == targets, "prepared desired")
    need(doc(p["origin_cut_ref"]) == {"schema":"researchos.failure-origin-cut.v1","owner":"codex:/root","before":BEFORE,"after":AFTER,"origins":rows,"counter_reset":False}, "origin cut")
    audit = doc(p["audit_ref"])
    need(audit["changed_checkpoint_pointers"] == cd and audit["changed_ownership_pointers"] == od, "audit changes")
    live_four(before)
    save(CAS/"commit.started.json",{"actor":"codex:/root","once":True,"review_ref":review_ref,"prepared_ref":prepared_ref})
    git_guard(q,b,"commit.before")
    live_four(before)
    intent = save(CAS/"canonical-write.intent.json",{"actor":"codex:/root","prepared_ref":prepared_ref,"review_ref":review_ref,"before":BEFORE,"after":AFTER,"write_paths":CANON[:2],"unchanged_paths":CANON[2:],"recovery":"FORWARD_ONLY_SEPARATE_ROOT_DECISION_NO_ROLLBACK"})
    expected = list(before)
    for i,path in enumerate(CANON[:2]):
        target = safe(path); tmp = target.with_name(target.name+"."+UID+".tmp")
        save(tmp,targets[i])
        git_guard(q,b,"commit.pre-replace-"+str(i))
        live_four(expected)
        os.replace(tmp,target); expected[i] = targets[i]
        need(target.read_bytes() == targets[i], "individual CAS write")
        save(CAS/(target.stem+".write.done.json"),{"intent_ref":intent,"desired_ref":p["desired_refs"][i]})
    git_guard(q,b,"commit.after")
    live_four(targets)
    verified = save(CAS/"canonical-write.verified.json",{"schema":"researchos.scope7-failed-lease-close-cas-verified.v1","actor":"codex:/root","before":BEFORE,"after":AFTER,"review_ref":review_ref,"intent_ref":intent,"canonical_refs":[pin(safe(x)) for x in CANON],"step_state_commands_unchanged":True,"old_lease_closed_failed":True,"formal_increment":0,"execution_grant":False,"counter_reset":False})
    save(CAS/"manifest.closed.json",{"schema":"researchos.receipt-manifest.v1","owner":"codex:/root","members":[pin(x) for x in sorted(CAS.iterdir()) if x.is_file()],"self_excluded":True})
    print(json.dumps({"verified_ref":verified,"canonical_tuple":AFTER},ensure_ascii=False))

def main():
    ap = argparse.ArgumentParser(); modes = ap.add_mutually_exclusive_group(required=True)
    modes.add_argument("--draft",action="store_true"); modes.add_argument("--commit-review-ref")
    ap.add_argument("--request-sha256",required=True); ap.add_argument("--source-sha256",required=True)
    args = ap.parse_args()
    q = parse(safe(CAS/"original-input.json").read_bytes())
    ctx = preflight(q,args.request_sha256,args.source_sha256)
    if args.draft: draft(q,ctx)
    else: commit(q,parse(args.commit_review_ref.encode("utf8")),ctx)

if __name__ == "__main__":
    try: main()
    except BaseException as exc:
        print(repr(exc),file=sys.stderr); traceback.print_exc(); raise
