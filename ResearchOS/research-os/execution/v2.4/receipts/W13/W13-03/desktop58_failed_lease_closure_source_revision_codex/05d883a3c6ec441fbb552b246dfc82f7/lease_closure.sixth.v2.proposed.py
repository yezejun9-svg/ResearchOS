"""Root-only narrow failed-lease metadata CAS. No product or model invocation."""
import sys
sys.dont_write_bytecode = True
import argparse, copy, datetime, hashlib, json, os, traceback, types
from pathlib import Path
ROOT=Path("D:/作品集/ResearchOS/research-os")
NS=ROOT/'execution/v2.4/receipts/W13/W13-03/desktop58_failed_lease_closure_cas_codex/c550b87c595048dca4187601e57ecf24'
CANON=["execution/v2.4/"+x+".json" for x in ("checkpoint","path_ownership","step_state","commands")]

INPUT_BASE={'schema': 'researchos.desktop58-failed-lease-closure-input.v1', 'actor': 'codex:/root', 'namespace': 'execution/v2.4/receipts/W13/W13-03/desktop58_failed_lease_closure_cas_codex/c550b87c595048dca4187601e57ecf24', 'run_uuid': 'c550b87c595048dca4187601e57ecf24', 'old_run_uuid': 'b4d53db07f1e4ab8b9c0b37e291a6da5', 'before': [337, 165, 617], 'after': [338, 166, 635], 'main_head': 'e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7', 'main_git': {'head': 'e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7', 'status_sha256': 'e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4', 'status_bytes': 894, 'status_rows': 13, 'deleted_rows': 11, 'index_empty': True}, 'canonical_before': [{'path': 'execution/v2.4/checkpoint.json', 'sha256': '66853574c7cedaf8df6371fd5b68936d99d82dd02cd84725187ec6ec244aa996', 'bytes': 2879734}, {'path': 'execution/v2.4/path_ownership.json', 'sha256': '172b8798c3f8c2f28994fb66698bc68b3c8d44d5a52da9523612496e08a3c0c4', 'bytes': 192055}, {'path': 'execution/v2.4/step_state.json', 'sha256': 'fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149', 'bytes': 257446}, {'path': 'execution/v2.4/commands.json', 'sha256': 'b357f60a9463b1a7504487bd8debf2b55f87f35938a26fe68a495aa834794129', 'bytes': 68156}], 'binding_ref': {'path': 'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r337-b4d53db07f1e4ab8b9c0b37e291a6da5/binding.json', 'sha256': 'edf1a088cb36f178333132d5cbad395a7b052329969a649f5da26aa14edffdd6', 'bytes': 22067}, 'closure_review_ref': {'path': 'execution/v2.4/receipts/W13/W13-03/desktop58_failed_execution_independent_review_codex/884be18fbe7248a693e64774987db31c/review.json', 'sha256': '86cfc1585ae3f1eac5c9f2e10d5dd809f6577b734738b01f311dfa2cc293a2c8', 'bytes': 8065}, 'closure_report_ref': {'path': 'execution/v2.4/receipts/W13/W13-03/desktop58_failed_execution_root_closure_codex/93044794230d43ba9a169420a8cf45d1/report.json', 'sha256': '3b2dceea5fb2334130f7d0bfad12c3703bb0495b521173944699218f2646baad', 'bytes': 49013}, 'closure_manifest_ref': {'path': 'execution/v2.4/receipts/W13/W13-03/desktop58_failed_execution_root_closure_codex/93044794230d43ba9a169420a8cf45d1/manifest.json', 'sha256': '05f96426367fff25cf459134a60f445588b49225734ecf3da69592fa38db77d9', 'bytes': 31154}, 'closure_handoff_ref': {'path': 'execution/v2.4/receipts/W13/W13-03/desktop58_failed_execution_root_closure_codex/93044794230d43ba9a169420a8cf45d1/handoff.json', 'sha256': 'f19092f4ff6a1340cb6487f117aa56e32fb6ccb8c6831736d86381215591b842', 'bytes': 11663}, 'pending_origin_refs': [{'path': 'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r337-b4d53db07f1e4ab8b9c0b37e291a6da5/failure-origin-618.query.original.json', 'sha256': '6d5853981709358ce29e7737a7b5cf66d2f2f2bf13563223352406a8a3e00ebf', 'bytes': 939}, {'path': 'execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_executable_source_codex/1b8bc13521764e508f540dc2399ac33d/failure-origin-003.json', 'sha256': '6bfdb3edf583cc6d2dd1f1aec92a5a371ca13aa4490516f5cc03d8a6aa38eaa3', 'bytes': 1236}, {'path': 'execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_executable_source_codex/1b8bc13521764e508f540dc2399ac33d/failure-origin-004.json', 'sha256': 'a898021007c5ded9df3fc8bb385c29d85a5d935946a5809f08335f67c08a609a', 'bytes': 1139}, {'path': 'execution/v2.4/receipts/W05/W05-99/mu_model_sdk_trial_source_metadata_correction_codex/301af11689544b3883847a3fbdb35969/failure-origin-005.json', 'sha256': '0fe9e60e9e1a27c5de127cbccb5f82f3acb7e00500d9348cc08f45e7c7a24f3b', 'bytes': 1398}, {'path': 'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r337-b4d53db07f1e4ab8b9c0b37e291a6da5/failure-origin-622.pre-scope.original.json', 'sha256': '3a65ae2db2894d568a43e63e86b61dd534601b61a37c1b68e6cec4577c984d75', 'bytes': 4606}, {'path': 'execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_independent_source_review_codex/33477ff3f8a94e57b4d9fdaabf3aa19e/failure-origin.js-unbound-ns.json', 'sha256': '60702dc236f0d0f2700dd4ca1effe96d0cc6a6834cdaff653700a4ea14366948', 'bytes': 2606}, {'path': 'execution/v2.4/receipts/W05/W05-99/wholeGo_root_cap_producer_source_preparation_codex/a378e6d62865446ab78312d5efabb458/failure-origin-001.json', 'sha256': '9608539a454c87cdb096309c7803ace843351361829493d9a810a517abdd5033', 'bytes': 1193}, {'path': 'execution/v2.4/receipts/W05/W05-99/wholeGo_root_cap_producer_source_preparation_codex/a378e6d62865446ab78312d5efabb458/failure-origin-002.json', 'sha256': 'f1052da319eb77694bea6e24af671d932ea1e3de93466d5d4e1cc04d161ffd72', 'bytes': 1195}, {'path': 'execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_revision_source_codex/1ccdc0cec995488c82400608ed275029/tool-failure-origin-001.json', 'sha256': 'a449ca1c1246f8f3080fd25abb43a921aaa360ba8bbde5497b8bcd4dfc510520', 'bytes': 2825}, {'path': 'execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_independent_source_review_codex/33477ff3f8a94e57b4d9fdaabf3aa19e/failure-origin.command-length.json', 'sha256': 'faed5c19afb244e4ce47bad6b33e48495e44c44940f2b7f30fd18aa0478d9594', 'bytes': 439131}, {'path': 'execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_revision_source_codex/1ccdc0cec995488c82400608ed275029/tool-failure-origin-002.json', 'sha256': '773560b30a903b5157febcb834b15be972b585642fd830989f19c43aa2776dcb', 'bytes': 703}, {'path': 'execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_revision_source_codex/1ccdc0cec995488c82400608ed275029/tool-failure-origin-003.json', 'sha256': '89bf36b5350cfbc31964c0c3300c22d37aa1bec7f2fafa2f8ee97db3c35b0488', 'bytes': 2541}, {'path': 'D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W13\\W13-03\\desktop58_root_caller_allocationsixth_source_preparation_codex\\b4d53db07f1e4ab8b9c0b37e291a6da5\\failure-origin-630.grant-metadata-comparison.original.json', 'sha256': '123d378071ead6201bde7ce412b76bd8cb3c480ed891cb04d18c1362203fd84d', 'bytes': 5356}, {'path': 'execution/v2.4/receipts/W13/W13-03/desktop58_failed_execution_root_closure_codex/93044794230d43ba9a169420a8cf45d1/failure-origin-631.original.json', 'sha256': 'fc1d3747ada2821c5a7144df2851d5384b4801c28382e70e48cf11915c7f1bb1', 'bytes': 7878}, {'path': 'execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v3_source_codex/06f264848e274b198f3e03a1c072e44e/tool-failure-origin-001.json', 'sha256': 'ecfdc7170a08f0d191b5e43da84349d23fbab2dfa638dcc076cedb239127dbbd', 'bytes': 3034}, {'path': 'execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v3_source_codex/06f264848e274b198f3e03a1c072e44e/tool-failure-origin-002.json', 'sha256': 'e8d28dd2b7e552d6bda379390dcd5a35c120515aa32fa1cc41f630afec672d0f', 'bytes': 2334}, {'path': 'execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v3_source_codex/06f264848e274b198f3e03a1c072e44e/tool-failure-origin-003.json', 'sha256': '041f57bc545324295600fb93dad608a4a2974bb49e2082ca12b08d2f504221cd', 'bytes': 2191}, {'path': 'D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W13\\W13-03\\desktop58_failed_execution_root_closure_codex\\93044794230d43ba9a169420a8cf45d1\\failure-origin-635.sealer-guard.original.json', 'sha256': 'a3b01853b26d005c21bcdc50938117f525a545f99f9ac7784435701329d2b7e0', 'bytes': 3580}], 'pipeline_ref': {'path': 'execution/v2.4/receipts/W13/W13-03/desktop58_cli2_fact_abi_revision_preparation_codex/ddc11e9721a6490baf1f0032c6bf6d16/metadata_pipeline.desktop58.bound.v4.proposed.py', 'sha256': 'c0a085f9b720ebdb89a78fb5cf367bd262d2823fe15a9f2686545b99aebe7755', 'bytes': 38316}, 'helper_ref': {'path': 'D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\integration_codex\\independent-cli-list-scopes-r308\\windows_owned_process.py', 'sha256': '6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad', 'bytes': 18901}, 'python_pin': {'path': 'C:\\Users\\yqyyds\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe', 'sha256': 'cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b', 'bytes': 106328}, 'formal_increment': 0, 'source_execution_grant': False, 'parent_acceptance_increment': 0, 'automatic_retry': False, 'counter_reset': False}

def need(ok,msg):
    if not ok: raise RuntimeError(msg)
def safe(p,existing=True):
    p=Path(p)
    if not p.is_absolute(): p=ROOT/p
    need(".." not in p.parts and p.is_relative_to(ROOT) and p!=ROOT,"outside Root")
    need(p.resolve(strict=existing)==p.absolute(),"alias")
    for a in [p,*p.parents]:
        if os.path.lexists(a): need(not a.is_symlink() and not (getattr(a.lstat(),"st_file_attributes",0)&0x400),"reparse")
        if a==ROOT: break
    return p
def parse(raw):
    def pairs(items):
        d={}
        for k,v in items: need(k not in d,"duplicate JSON key"); d[k]=v
        return d
    return json.loads(raw.decode("utf8"),object_pairs_hook=pairs,parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
def encode(d): return (json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode("utf8")
def pin(p):
    p=Path(p); raw=p.read_bytes()
    return {"path":p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else str(p),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def verify(r):
    need(type(r)is dict and set(r)=={"path","sha256","bytes"},"exact ref")
    p=Path(r["path"])
    if not p.is_absolute(): p=ROOT/p
    if p.is_relative_to(ROOT): p=safe(p)
    raw=p.read_bytes()
    need(len(raw)==r["bytes"] and hashlib.sha256(raw).hexdigest()==r["sha256"],"pin mismatch: "+str(p))
    return raw
def doc(r): return parse(verify(r))
def save(p,d):
    p=safe(p,False); raw=encode(d)
    with p.open("xb") as f: f.write(raw); f.flush(); os.fsync(f.fileno())
    return pin(p)
def copy_bytes(p,raw):
    with safe(p,False).open("xb") as f: f.write(raw); f.flush(); os.fsync(f.fileno())
    return pin(p)
def load_module(r,name):
    raw=verify(r); m=types.ModuleType(name); m.__file__=str(safe(r["path"]))
    exec(compile(raw,m.__file__,"exec"),m.__dict__); return m
def differences(a,b,path=""):
    if a==b:return []
    if isinstance(a,dict) and isinstance(b,dict):
        rows=[]
        for k in sorted(set(a)|set(b)):
            child=path+"/"+k.replace("~","~0").replace("/","~1")
            if k not in a or k not in b: rows.append(child)
            else: rows.extend(differences(a[k],b[k],child))
        return rows
    return [path]
def all_refs(value):
    if isinstance(value,dict):
        if set(value)=={"path","sha256","bytes"}:
            yield value
        else:
            for item in value.values(): yield from all_refs(item)
    elif isinstance(value,list):
        for item in value: yield from all_refs(item)
def live_four(expected):
    need(len(expected)==4 and all(safe(name).read_bytes()==raw for name,raw in zip(CANON,expected)),"current exact ordered four")
def preflight(q,request_sha256,self_sha256):
    # No output, sentinel, helper import, native process, temp or CAS before all pins bind.
    need(type(q)is dict and set(q)==set(INPUT_BASE)|{"source_ref","amended_at"},"exact request keys")
    need(all(q[k]==v for k,v in INPUT_BASE.items()),"all fixed request fields/refs")
    need(q["source_ref"]==pin(safe(__file__)) and q["source_ref"]["sha256"]==self_sha256,"actual candidate self hash")
    raw=safe(NS/"original-input.json").read_bytes()
    need(hashlib.sha256(raw).hexdigest()==request_sha256 and parse(raw)==q,"actual request raw hash/value")
    need(sys.flags.isolated==1 and sys.flags.no_site==1 and sys.flags.utf8_mode==1,"isolated no-site utf8 Python")
    need(Path(sys.executable).resolve()==Path(q["python_pin"]["path"]).resolve(),"pinned Python identity")
    stamp=datetime.datetime.fromisoformat(q["amended_at"])
    need(stamp.utcoffset()==datetime.timedelta(0),"Root explicit UTC amendment")
    for r in all_refs(q): verify(r)
    need([r["path"] for r in q["canonical_before"]]==CANON,"ordered canonical input refs")
    before=[verify(r) for r in q["canonical_before"]]
    live_four(before)
    cp,ow=map(parse,before[:2])
    need([cp["revision"],ow["revision"],len(cp["failure_counters"])]==q["before"] and cp["head"]==q["main_head"],"actual current tuple/head")
    b=doc(q["binding_ref"])
    # This binding was made at revision336. It supplies tools/430prefix, never current-before.
    need(b["main_git"]==q["main_git"] and b["owned_process_helper_ref"]==q["helper_ref"] and q["pipeline_ref"] in b["metadata_code_refs"],"original tool/binding source")
    verify(b["toolchain_lock_ref"])
    lock=doc(b["toolchain_lock_ref"])["tools"]
    need(lock["python"]["path"]==q["python_pin"]["path"] and lock["python"]["sha256"]==q["python_pin"]["sha256"],"locked Python pin")
    verify({"path":lock["git"]["path"],"sha256":lock["git"]["sha256"],"bytes":46480})
    prefix=doc(b["failure_prefix430_ref"])["failure_counters"]
    need(len(prefix)==430 and cp["failure_counters"][:430]==prefix,"original430 prefix")
    closure=doc(q["closure_review_ref"]);root_closure=doc(q["closure_report_ref"])
    need(closure["reviewer"]=="codex:/root/w05_merge_review" and closure["decision"]=="FAILED_EXECUTION_EVIDENCE_CLOSED_QUALIFICATION_WITHHELD" and closure["requested_changes"]==[],"real independent execution closure")
    need(closure["scope_ref"]==cp["work_in_progress"]["desktop58_finite_validation_scope_ref"],"closed exact scope")
    need(closure["report_ref"]==q["closure_report_ref"] and closure["root_manifest_ref"]==q["closure_manifest_ref"],"independent closure exact root evidence")
    need(closure["qualification"] is False and closure["source_acceptance"] is False and closure["formal_increment"]==0 and closure["same_scope_rerun_allowed"] is False,"failed qualification remains withheld")
    need(root_closure["scope_uid"]==q["old_run_uuid"] and root_closure["scope_ref"]==closure["scope_ref"] and root_closure["canonical_tuple"]==q["before"],"failed run identity/current tuple")
    need(root_closure["root_native_session_active"] is False and root_closure["case_state_counts"]=={"NOT_STARTED":170} and root_closure["qualified_case_count"]==0 and root_closure["actual_observed_HTTP_total"]==0,"closed failure not runtime success")
    need(root_closure["builder_job_cleanup"]["job_idle_confirmed"] is True and root_closure["builder_job_cleanup"]["explicit_owned_handles_remaining"]==0 and root_closure["builder_debug_capture_summary"]["complete"] is False,"failed job closed without capture promotion")
    mf=doc(q["closure_manifest_ref"]);h=doc(q["closure_handoff_ref"])
    need(h["report_ref"]==q["closure_report_ref"] and h["manifest_ref"]==q["closure_manifest_ref"] and q["closure_report_ref"] in mf["entries"],"sealed root report membership")
    for r in mf["entries"]: verify(r)
    records=root_closure["pending_failure_origin_records"]
    need([x["failure_index"] for x in records]==list(range(618,636)) and [x["origin_ref"] for x in records]==q["pending_origin_refs"],"exact18 pending origins618..635")
    seen=set();rows=[]
    for r in q["pending_origin_refs"]:
        payload=doc(r)
        need(r["sha256"] not in seen and all(old.get("evidence_ref",{}).get("sha256")!=r["sha256"] for old in cp["failure_counters"]),"origin is unique and not already registered")
        seen.add(r["sha256"])
        rows.append({"origin_key":r["sha256"],"evidence_ref":r,"original_payload":payload,"counter_reset":False,"counted_once":True,"automatic_retry":False})
    lease=ow["card_path_bindings"]["W13-03"]["subtasks"]["desktop58_finite_validation"]
    need(lease["run_uuid"]==q["old_run_uuid"] and lease["state"]=="REGISTERED_PENDING_ONCE_EXECUTION" and lease["scope_ref"]==closure["scope_ref"] and lease["source_commit"]==q["main_head"] and lease["owner"]=="codex:/root" and lease["current_source_writer"] is None,"exact failed b4d lease")
    need(cp["work_in_progress"]["desktop58_finite_validation_state"]=="REGISTERED_PENDING_ONCE_EXECUTION","pending WIP")
    return before,cp,ow,b,rows
def desired_values(q,cp,ow,rows):
    newcp,newow=copy.deepcopy(cp),copy.deepcopy(ow)
    newcp.update(revision=q["after"][0],expected_previous_revision=q["before"][0],updated_at=q["amended_at"],updated_by="codex:/root")
    newcp["failure_counters"].extend(copy.deepcopy(rows))
    newcp["work_in_progress"].update(desktop58_finite_validation_state="FAILED_EXECUTION_CLOSED_QUALIFICATION_WITHHELD",desktop58_finite_validation_failed_closure_review_ref=q["closure_review_ref"],desktop58_finite_validation_failed_closure_root_ref=q["closure_report_ref"])
    newow.update(revision=q["after"][1],amended_at=q["amended_at"],amended_by="codex:/root")
    lease=newow["card_path_bindings"]["W13-03"]["subtasks"]["desktop58_finite_validation"]
    lease.update(state="FAILED_EXECUTION_CLOSED_QUALIFICATION_WITHHELD",failed_closure_review_ref=q["closure_review_ref"],failed_closure_root_ref=q["closure_report_ref"],execution_grant=False,qualification=False,formal_increment=0)
    need(newcp["failure_counters"][:617]==cp["failure_counters"] and len(newcp["failure_counters"])==635,"all617 and18 exact append")
    cd=differences(cp,newcp);od=differences(ow,newow)
    ca={"/revision","/expected_previous_revision","/updated_at","/updated_by","/failure_counters","/work_in_progress/desktop58_finite_validation_state","/work_in_progress/desktop58_finite_validation_failed_closure_review_ref","/work_in_progress/desktop58_finite_validation_failed_closure_root_ref"}
    for key,qkey in (("desktop58_finite_validation_failed_closure_review_ref","closure_review_ref"),("desktop58_finite_validation_failed_closure_root_ref","closure_report_ref")):
        expected=q[qkey]
        need(type(expected)is dict and set(expected)=={"path","sha256","bytes"},"fixed closure exact3key ref")
        actual=newcp["work_in_progress"][key]
        need(type(actual)is dict and set(actual)=={"path","sha256","bytes"} and actual==expected,"new closure ref exact q pin")
        ca.update("/work_in_progress/"+key+"/"+leaf for leaf in ("path","sha256","bytes"))
    ob="/card_path_bindings/W13-03/subtasks/desktop58_finite_validation/"
    oa={"/revision","/amended_at","/amended_by",ob+"state",ob+"failed_closure_review_ref",ob+"failed_closure_root_ref",ob+"execution_grant",ob+"qualification",ob+"formal_increment"}
    need(set(cd)<=ca and set(od)<=oa,"exact allowed pointer changes")
    return newcp,newow,cd,od
def draft(q,context):
    before,cp,ow,b,rows=context
    need({x.name for x in NS.iterdir()}=={"original-input.json"},"allocated draft output only exact request; no retry")
    save(NS/"draft.started.json",{"actor":"codex:/root","once":True,"input_ref":pin(NS/"original-input.json"),"source_ref":pin(__file__)})
    cut=save(NS/"origin-cut.json",{"schema":"researchos.failure-origin-cut.v1","owner":"codex:/root","before":q["before"],"after":q["after"],"origins":rows,"counter_reset":False})
    pipeline=load_module(q["pipeline_ref"],"reviewed_desktop_metadata_origin_formatter")
    need(pipeline.origins({"origin_cut_ref":cut,"before":q["before"],"after":q["after"]},cp)==rows,"original pipeline opaque verifier")
    nc,no,cd,od=desired_values(q,cp,ow,rows)
    desired=[encode(nc),encode(no),before[2],before[3]]
    originals=[copy_bytes(NS/(Path(n).stem+".before.json"),v) for n,v in zip(CANON,before)]
    targets=[copy_bytes(NS/(Path(n).stem+".desired.json"),v) for n,v in zip(CANON,desired)]
    audit=save(NS/"audit.json",{"schema":"researchos.desktop58-failed-lease-closure-cas-audit.v1","author":"codex:/root","before":q["before"],"after":q["after"],"checkpoint_changed_pointers":cd,"ownership_changed_pointers":od,"original_failure_prefix617_equal":True,"original_failure_prefix430_equal":True,"original_origin_count":18,"step_state_commands_byte_identical":True,"main_source_head":q["main_head"],"closed_run_uuid":q["old_run_uuid"],"failed_closure_review_ref":q["closure_review_ref"],"qualification_granted":False,"formal_increment":0,"parent_acceptance_increment":0,"new_execution_scope":False,"new_execution_grant":False,"counter_reset":False,"automatic_retry":False})
    live_four(before)
    prepared=save(NS/"prepared.json",{"schema":"researchos.desktop58-failed-lease-closure-cas-prepared.v1","author":"codex:/root","input_ref":pin(NS/"original-input.json"),"source_ref":pin(__file__),"before":q["before"],"after":q["after"],"original_refs":originals,"desired_refs":targets,"origin_cut_ref":cut,"audit_ref":audit,"old_closed_run_review_ref":q["closure_review_ref"],"formal_increment":0,"execution_grant":False})
    mf=save(NS/"manifest.draft.json",{"schema":"researchos.receipt-manifest.v1","owner":"codex:/root","purpose":"failed_lease_closure_metadata_only","members":[pin(x) for x in sorted(NS.iterdir()) if x.is_file()],"self_excluded":True})
    print(json.dumps({"prepared_ref":prepared,"audit_ref":audit,"manifest_ref":mf,"before":q["before"],"after":q["after"],"native_product_calls":0,"canonical_writes":0},ensure_ascii=False))
def job_ok(r):
    need(isinstance(r,dict) and r["actual_exit"]==0 and r["error"] is None and not r["timed_out"] and r["resumed"] is True,"metadata Git native failure")
    c=r["job_cleanup"]
    need(c["errors"]==[] and c["active_processes_last_observed"]==0 and all(c[k] is True for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed")),"metadata Git cleanup")
def git_guard(q,b,label):
    helper=load_module(q["helper_ref"],"old_failed_lease_owned_git")
    lock=doc(b["toolchain_lock_ref"])["tools"]
    verify({"path":lock["git"]["path"],"sha256":lock["git"]["sha256"],"bytes":46480})
    env=dict(b["public_environment"]);env.update(GIT_OPTIONAL_LOCKS="0",GIT_NO_REPLACE_OBJECTS="1",GIT_CONFIG_NOSYSTEM="1",GIT_CONFIG_GLOBAL="nul",GIT_TERMINAL_PROMPT="0",GIT_CONFIG_COUNT="2",GIT_CONFIG_KEY_0="core.fsmonitor",GIT_CONFIG_VALUE_0="false",GIT_CONFIG_KEY_1="core.untrackedCache",GIT_CONFIG_VALUE_1="false")
    outputs=[]
    for kind,args in [("head",["rev-parse","HEAD"]),("status",["status","--porcelain=v1","--untracked-files=no"]),("index",["diff","--cached","--name-only"])]:
        a=NS/(label+"."+kind+".stdout.raw");z=NS/(label+"."+kind+".stderr.raw")
        argv=[lock["git"]["path"]]+args;result=None;error=None
        try:
            with a.open("xb") as out,z.open("xb") as err: result=helper.run_owned(argv,str(ROOT),env,out,err,30)
        except BaseException as e: error=repr(e);raise
        finally:
            save(NS/(label+"."+kind+".invocation.json"),{"actor":"codex:/root","metadata_only":True,"argv":argv,"cwd":str(ROOT),"public_environment":env,"result":result,"wrapper_error":error,"actual_stage_native_exit":result["actual_exit"] if result else None,"stdout_ref":pin(a) if a.exists() else None,"stderr_ref":pin(z) if z.exists() else None,"qualifies_product_runtime":False})
        job_ok(result);outputs.append(a.read_bytes())
    need(outputs[0].decode("ascii").strip()==q["main_head"] and outputs[2]==b"","Main/index")
    need(hashlib.sha256(outputs[1]).hexdigest()==q["main_git"]["status_sha256"] and len(outputs[1])==q["main_git"]["status_bytes"],"protected tracked Git")
def commit(q,review_ref,context):
    before,cp,ow,b,rows=context
    prepared_ref=pin(safe(NS/"prepared.json"));p=doc(prepared_ref);rev=doc(review_ref)
    need(rev["schema"]=="researchos.desktop58-failed-lease-closure-cas-review.v1" and rev["reviewer"]=="codex:/root/f08_whole_scope_review" and rev["decision"]=="READY_FOR_ROOT_OLD_FAILED_LEASE_CLOSURE_CAS_ONCE" and rev["requested_changes"]==[] and rev["actual_registration_executed"] is False,"actual independent F08 CAS review")
    need(rev["prepared_ref"]==prepared_ref and rev["source_ref"]==pin(__file__) and rev["input_ref"]==pin(NS/"original-input.json") and rev["audit_ref"]==p["audit_ref"] and rev["manifest_ref"]==pin(NS/"manifest.draft.json"),"review all prepared pins")
    need(rev["expected_before"]==q["before"] and rev["expected_after"]==q["after"] and rev["original_refs"]==p["original_refs"] and rev["desired_refs"]==p["desired_refs"],"review exact targets/transition")
    need(p["input_ref"]==pin(NS/"original-input.json") and q==doc(p["input_ref"]) and p["source_ref"]==pin(__file__),"prepared source and request")
    need(p["before"]==q["before"] and p["after"]==q["after"] and p["formal_increment"]==0 and p["execution_grant"] is False,"narrow prepared")
    for x in doc(pin(NS/"manifest.draft.json"))["members"]: verify(x)
    need([verify(x) for x in p["original_refs"]]==before,"prepared originals exact current input")
    nc,no,cd,od=desired_values(q,cp,ow,rows)
    desired=[encode(nc),encode(no),before[2],before[3]]
    need([verify(x) for x in p["desired_refs"]]==desired,"prepared desired recomputed exact")
    cut=doc(p["origin_cut_ref"])
    need(cut=={"schema":"researchos.failure-origin-cut.v1","owner":"codex:/root","before":q["before"],"after":q["after"],"origins":rows,"counter_reset":False},"prepared origin cut exact")
    audit=doc(p["audit_ref"])
    need(audit["checkpoint_changed_pointers"]==cd and audit["ownership_changed_pointers"]==od,"reviewed exact change pointers")
    live_four(before)
    save(NS/"commit.started.json",{"actor":"codex:/root","once":True,"review_ref":review_ref,"input_ref":p["input_ref"],"source_ref":p["source_ref"]})
    git_guard(q,b,"commit.before")
    live_four(before)
    intent=save(NS/"canonical-write.intent.json",{"actor":"codex:/root","prepared_ref":prepared_ref,"review_ref":review_ref,"before":q["before"],"after":q["after"],"write_paths":CANON[:2],"unchanged_paths":CANON[2:],"automatic_retry":False,"counter_reset":False,"recovery":"FORWARD_ONLY_SEPARATE_ROOT_DECISION_NO_ROLLBACK"})
    expected=list(before)
    for i,name in enumerate(CANON[:2]):
        target=safe(name);tmp=target.with_name(target.name+"."+q["run_uuid"]+".tmp")
        copy_bytes(tmp,desired[i])
        git_guard(q,b,"commit.pre-replace-"+str(i))
        live_four(expected)
        os.replace(tmp,target);expected[i]=desired[i]
        need(target.read_bytes()==desired[i],"verified individual write")
        save(NS/("canonical-write."+target.stem+".done.json"),{"intent_ref":intent,"desired_ref":p["desired_refs"][i]})
    git_guard(q,b,"commit.after")
    live_four(desired)
    verified=save(NS/"canonical-write.verified.json",{"schema":"researchos.desktop58-failed-lease-closure-cas-verified.v1","actor":"codex:/root","before":q["before"],"after":q["after"],"intent_ref":intent,"review_ref":review_ref,"canonical_refs":[pin(safe(x)) for x in CANON],"step_state_commands_unchanged":True,"old_lease_closed_failed":True,"execution_grant":False,"formal_increment":0,"counter_reset":False})
    resume=save(NS/"RESUME.failed-lease.closed.json",{"schema":"researchos.resume.v1","actor":"codex:/root","canonical_tuple":q["after"],"closed_run_uuid":q["old_run_uuid"],"old_state":"FAILED_EXECUTION_CLOSED_QUALIFICATION_WITHHELD","next_action":"Separate fresh Root scope/UUID only after resource Source review; retain post635 origin refs outside this immutable cut","goal_status":"ACTIVE","parent_accepted":6,"parents_total":22,"formal_accepted":0,"formal_total":42,"verified_ref":verified})
    mf=save(NS/"manifest.closed.json",{"schema":"researchos.receipt-manifest.v1","owner":"codex:/root","members":[pin(x) for x in sorted(NS.iterdir()) if x.is_file()],"self_excluded":True,"metadata_only":True,"formal_increment":0})
    print(json.dumps({"verified_ref":verified,"resume_ref":resume,"manifest_ref":mf,"canonical_tuple":q["after"],"canonical_refs":[pin(safe(x)) for x in CANON]},ensure_ascii=False))
def main():
    ap=argparse.ArgumentParser()
    mode=ap.add_mutually_exclusive_group(required=True);mode.add_argument("--draft",action="store_true");mode.add_argument("--commit-review-ref")
    ap.add_argument("--request-sha256",required=True);ap.add_argument("--source-sha256",required=True)
    a=ap.parse_args()
    q=parse(safe(NS/"original-input.json").read_bytes())
    context=preflight(q,a.request_sha256,a.source_sha256)
    if a.draft: draft(q,context)
    else: commit(q,parse(a.commit_review_ref.encode("utf8")),context)
if __name__=="__main__":
    try: main()
    except BaseException as e:
        print(repr(e),file=sys.stderr);traceback.print_exc()
        raise

