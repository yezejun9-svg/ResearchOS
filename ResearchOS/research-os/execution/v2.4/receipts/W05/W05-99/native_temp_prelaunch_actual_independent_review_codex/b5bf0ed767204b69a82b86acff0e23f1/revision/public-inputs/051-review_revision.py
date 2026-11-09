import sys
sys.dont_write_bytecode=True
import ast,difflib,hashlib,json,os,re,subprocess,traceback,types
from pathlib import Path
BASE=Path(__file__).resolve().parent
O=BASE/'revision'
O.mkdir(exist_ok=False)
R=Path("D:/作品集/ResearchOS/research-os")
B=R/"execution/v2.4/receipts/W05/W05-99"
A=B/"integration_codex/native-temp-compile-unit-root-1791508539969/revision-list-manifest"
C=B/"integration_codex/native-temp-controller-config-root-1791508950616"
S=B/"integration_codex/native-temp-positive-serve-root-1791509017626"
P=B/"integration_codex/native-temp-positive-root-api-1791509017626"
KEY="RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT"
TRIAL=R/".local/mu-sdk-isolated-project-ed84838046934329a76733a005c9b162"
checks=[]
def check(ok,label,detail=None):
    checks.append({"check":label,"passed":bool(ok),"detail":detail})
def pin(p):
    p=Path(p); raw=p.read_bytes()
    return {"path":str(p),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def norm(r):
    return {"path":str(Path(r["path"])),"sha256":r["sha256"].removeprefix("sha256:"),"bytes":r["bytes"]}
def key(p):
    return str(Path(p)).casefold()
def same(a,b):
    return key(a["path"])==key(b["path"]) and a["sha256"].removeprefix("sha256:")==b["sha256"].removeprefix("sha256:") and a["bytes"]==b["bytes"]
def write(n,v):
    p=O/n;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
    return pin(p)
def exact(p,h,n):
    r=pin(p)
    if r["sha256"]!=h or r["bytes"]!=n:raise ValueError("anchor mismatch: "+str(p))
    return r
def unique(refs):
    out={}
    for rr in refs:
        r=norm(rr);k=key(r["path"])
        if k in out and not same(out[k],r):raise ValueError("conflicting pinned input: "+r["path"])
        out[k]=r
    return list(out.values())
def walk(o):
    if isinstance(o,dict):
        if {"path","sha256","bytes"}.issubset(o):yield norm(o)
        for v in o.values():yield from walk(v)
    elif isinstance(o,list):
        for v in o:yield from walk(v)
def closed(g):
    return g.get("verification")=="PASSED" and g.get("closed") is True and g.get("retained_handles_count")==0 and not g.get("errors") and all(x.get("verified") and x.get("final_path_match") and x.get("closed") for x in g.get("entries",[]))
def git_state():
    commands=[["git","--no-optional-locks","-C",str(R),"status","--porcelain=v1","--untracked-files=no"],["git","--no-optional-locks","-C",str(R),"diff","--cached","--name-only"]]
    result=[]
    for cmd in commands:
        p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
        result.append({"argv":cmd,"exit_code":p.returncode,"stdout":p.stdout.decode("utf-8"),"stderr":p.stderr.decode("utf-8")})
    return result
def shape_source(s):
    # Remove only whitespace outside Go quoted strings and comments.
    out=[];i=0
    while i<len(s):
        if s.startswith("//",i):
            end=s.find("\n",i)
            if end<0:end=len(s)
            out.append(s[i:end]);i=end
        elif s.startswith("/*",i):
            end=s.find("*/",i+2)
            if end<0:raise ValueError("unclosed Go comment")
            out.append(s[i:end+2]);i=end+2
        elif s[i] in ('"', "'", chr(96)):
            quote=s[i];start=i;i+=1
            while i<len(s):
                if s[i]==quote:
                    i+=1;break
                if quote!=chr(96) and s[i]=="\\":
                    i+=2
                else:i+=1
            out.append(s[start:i])
        elif s[i].isspace():i+=1
        else:out.append(s[i]);i+=1
    return "".join(out)
def main():
    anchors=[
        exact(A/"validation.closed.json","9ecbf95ad3c89757479f611742a081d31aff0bbffbd1277aa1d10e0e82d52f5d",10813),
        exact(C/"controller.public.config.json","19c92dc0af96281b0d00b1cb767ef3715e9f97102669722550e07888213808af",1163646),
        exact(C/"controller-config.prepared.json","32357731804254230447606b6e3e95d3fa325bc8c6320d968548deeca67c4a9f",3645)]
    cfg=json.loads((C/"controller.public.config.json").read_bytes())
    gref=norm(cfg["SourceReadGuard"])
    graw=Path(gref["path"]).read_bytes()
    if hashlib.sha256(graw).hexdigest()!="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85":raise ValueError("guard pin")
    gm=types.ModuleType("independent_prelaunch_source_guard")
    exec(compile(graw,gref["path"],"exec"),gm.__dict__)
    members=[]
    for directory in (A,C,S,P):
        members.extend(pin(p) for p in sorted(directory.iterdir()) if p.is_file())
    metadata=unique(anchors+members+[gref,pin(__file__)])
    guards=[];observations=[]
    baseline_git=git_state()
    write("git-baseline.original-io.json",baseline_git)
    try:
        boot=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
        guards.append(boot);boot.acquire(metadata)
        def bobj(p):return json.loads(boot.get_buffer(str(p)))
        actual=bobj(A/"validation.closed.json");prepared=bobj(C/"controller-config.prepared.json")
        caller=bobj(S/"caller-adaptation.provenance.json")
        hc=bobj(C/"native-harness.public.config.json")
        refs=metadata+[norm(x) for x in cfg["FrozenInputs"]]+list(walk(actual))
        refs += [pin(caller["serve_base"]),pin(caller["api_base"])]
        refs += list(walk(bobj(A/"source-overlay.json")))
        receipts={}
        for p in (A,C):
            for file in sorted(p.glob("*source-guard.cleanup.actual.json")):
                g=bobj(file);receipts[str(file)]=g
                refs+=list(walk(g.get("entries",[])))
        for p in (R/"execution/v2.4"/(n+".json") for n in ("checkpoint","path_ownership","commands","step_state")):refs.append(pin(p))
        refs.append(pin(R/"execution/project_identity.json"))
        for m in list(sys.modules.values()):
            for field in ("__file__","__cached__"):
                p=getattr(m,field,None)
                if p and Path(p).is_file():refs.append(pin(p))
        refs.append(pin(sys.executable))
        refs=unique(refs)
        # Source-only/public resources, never original trial files or actual keys.
        for r in refs:
            if Path(r["path"]).is_relative_to(TRIAL):raise ValueError("original trial reference prohibited")
        full=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
        guards.append(full);full.acquire(refs)
        def raw(p):return full.get_buffer(str(p))
        def obj(p):return json.loads(raw(p))
        held={key(r["path"]):r for r in refs}
        # Public metadata copies: do not duplicate SDKs or compiled binary resources.
        copy_paths=set(r["path"] for r in metadata)
        copy_paths.update([caller["serve_base"],caller["api_base"]])
        for i,p in enumerate(sorted(copy_paths)):
            dest=O/"public-inputs"/(str(i).zfill(3)+"-"+Path(p).name)
            dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open("xb") as f:f.write(raw(p))
        check(len(actual["invocation_refs"])==8,"eight_actual_owned_invocations")
        inv_summary=[]
        for rr in actual["invocation_refs"]:
            inv=obj(rr["path"]);res=inv["result"];j=res["job_cleanup"]
            ok=inv["actual_native_exit"]==0 and res["actual_exit"]==0 and res["error"] is None and res["timed_out"] is False and res["resumed"] is True and inv["exception"] is None
            ok=ok and j["active_processes_last_observed"]==0 and not j["errors"] and all(j[n] for n in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed"))
            check(ok,"owned_job_"+Path(rr["path"]).name)
            inv_summary.append({"name":Path(rr["path"]).name,"argv":inv["argv"],"actual_exit":res["actual_exit"],"pid":res["owned_child_pid"],"creation_time_decimal":str(res["creation_time_100ns"]),"closed":ok})
            for n in ("stdout_ref","stderr_ref"):
                check(same(pin(inv[n]["path"]),inv[n]),"actual_stream_pin_"+Path(inv[n]["path"]).name)
        stream=raw(A/"broker-temp-units.stdout.raw").decode("utf-8")
        events=[json.loads(l) for l in stream.splitlines() if l.strip()]
        terminal=[e for e in events if e.get("Test") and e.get("Action") in ("pass","fail","skip")]
        names=[e["Test"] for e in terminal]
        check(len(terminal)==30 and len(set(names))==30 and all(e["Action"]=="pass" for e in terminal),"two_parents_28_leaves_all_pass")
        check(sum("/" in n for n in names)==28,"28_actual_leaf_names")
        check(not any(e.get("Action") in ("fail","skip") for e in events),"zero_actual_FAIL_SKIP")
        expected=obj(B/"native_migration_broker_temp_revision_codex/9beca53ced874c93a6101f451eb33491/public-environment-contract.json")
        check(sorted(n.split("/",1)[1] for n in names if "/" in n)==sorted(expected["new_component_leaf_names"]),"leaf_names_match_accepted_Source")
        unit=obj(A/"broker-temp-units.invocation.json")
        check(unit["argv"][0]==actual["official_test2json_ref"]["path"] and "-test.run="+expected["targeted_component_regex"] in unit["argv"],"explicit_official_test2json_and_exact_selector")
        check(actual["official_test2json_ref"]["sha256"]=="dead8050fd4e0e0471407380898fe9642b9107048e0ad119cb652821dfe58f7c" and actual["official_test2json_ref"]["bytes"]==4932608,"official_T2J_exact_pin")
        overlay=obj(A/"source-overlay.json")["sources"];fmt=obj(A/"formatted.source-members.json")
        t8=Path(actual["current_source_root"]);fmap={Path(r["path"]).relative_to(t8).as_posix():r for r in fmt}
        base_refs=obj(actual["base43_formatted_ref"]["path"]);t7=Path(actual["broker_temp_source_change"]["internal/domain/native_migration_authority_harness_windows_test.go"]["previous_ref"]["path"]).parents[2]
        base_map={Path(r["path"]).relative_to(t7).as_posix():r for r in base_refs}
        changed="internal/domain/native_migration_authority_harness_windows_test.go"
        check(len(overlay)==len(fmt)==len(base_refs)==43 and set(overlay)==set(fmap)==set(base_map),"exact_43_source_members")
        unchanged=[n for n in overlay if n!=changed and overlay[n]["sha256"]==fmap[n]["sha256"]==base_map[n]["sha256"] and overlay[n]["bytes"]==fmap[n]["bytes"]==base_map[n]["bytes"]]
        check(len(unchanged)==42,"42_sources_exact_T7_and_formatted_T8")
        src=raw(overlay[changed]["path"]).decode("utf-8");fmtsrc=raw(fmap[changed]["path"]).decode("utf-8")
        check(overlay[changed]["sha256"]=="eaa745bb2ea461a875bda13bef2495e7a8fb3375446a687e15108021b883ae90","accepted_EnvSource_candidate")
        scope=obj(A/"owned-gofmt-output-scope.json")
        check(scope["changed_source_refs"][changed]["different_bytes"] is True and fmap[changed]["sha256"]=="972166b2744d1048dc747e8a5b4991cd0b06cbbdc8a523c90fef12e27e02e0e9","observed_owned_gofmt_difference")
        check(shape_source(src)==shape_source(fmtsrc),"gofmt_only_whitespace_outside_strings_comments")
        with (O/"gofmt.diff").open("x",encoding="utf-8") as f:f.write("".join(difflib.unified_diff(src.splitlines(True),fmtsrc.splitlines(True),fromfile="acceptedSource",tofile="ownedGofmt")))
        inventory=obj(cfg["CompilerInventory"]["path"])
        frozen={key(r["path"]):norm(r) for r in cfg["FrozenInputs"]}
        check(len(frozen)==len(cfg["FrozenInputs"])==4303,"4303_unique_FrozenInputs")
        check(len(inventory["build_inputs"])==3793 and len(inventory["product_inventory"])==599 and len(inventory["compiler_tool_refs"])==8,"actual_compiler_inventory_counts")
        for group in ("build_inputs","product_inventory","compiler_tool_refs"):
            check(all(key(r["path"]) in frozen and same(frozen[key(r["path"])],r) for r in inventory[group]),"full_frozen_"+group)
        check(all(key(x["ref"]["path"]) in frozen and same(frozen[key(x["ref"]["path"])],x["ref"]) for x in inventory["actual_embed_files"]),"full_actual_embed_pins")
        for k in ("ControllerSource","HarnessConfig","TestProgram","ObservedOwnedHelper","OriginalOwnedHelper","SourceReadGuard","CompilerInventory","BuildInvocation"):
            check(key(cfg[k]["path"]) in frozen and same(cfg[k],frozen[key(cfg[k]["path"])]),"cfg8_ref_"+k)
        for k in ("RootProgram","ControlProgram","BackupProgram","EnrollmentProgram","PythonProgram","BrokerSource","PrivateStdinHelper"):
            check(key(hc[k]["path"]) in frozen and same(hc[k],frozen[key(hc[k]["path"])]),"harness7_RawPin_"+k)
        gopath=Path(inventory["GoRef"]["path"])
        check(all(key(p) in frozen for p in (gopath,gopath.parent.parent/"VERSION",gopath.parent.parent/"src/go.mod",actual["official_test2json_ref"]["path"])),"explicit_Go_VERSION_srcmod_T2J_frozen")
        check(len(cfg)==12 and hc["Case"]=="positive-replay" and hc["CaseID"]=="t8b41a23c5804b67" and key(hc["BuildRoot"])==key(t8),"fresh_fixed_cfg_case_buildroot")
        for k,label in (("RootProgram","maintenance-root-build"),("ControlProgram","control-build"),("BackupProgram","backup-build"),("EnrollmentProgram","enrollment-build")):
            check(same(hc[k],actual["binary_refs"][label]),"fresh_compiled_program_"+k)
        check(len({str(Path(hc[k]["path"]).parent) for k in ("RootProgram","ControlProgram","BackupProgram","EnrollmentProgram")})==1,"fresh_programs_same_directory")
        env=cfg["Environment"];proof=Path(env[KEY])
        check(env[KEY]==env["TEMP"]==env["TMP"],"literal_proof_TEMP_TMP_binding")
        check(proof.is_absolute() and proof.is_dir() and key(proof.resolve())==key(proof) and proof.is_relative_to(R/".local") and proof!=R/".local" and not proof.is_relative_to(TRIAL) and not TRIAL.is_relative_to(proof),"fresh_canonical_local_not_trial")
        check(all(not proof.is_relative_to(Path(env[n])) and not Path(env[n]).is_relative_to(proof) and Path(env[n]).is_dir() for n in ("SystemRoot","WINDIR")),"system_overlap_rejected_actual_paths")
        check(not Path(cfg["ControllerDirectory"]).exists() and not Path(hc["OutputDirectory"]).exists(),"prelaunch_no_runtime_or_harness_facts")
        check(prepared["status"]=="FRESH_CTL3_FIXED_PROOF_TEMP_PUBLIC_CONTEXT_VALIDATED_NO_NATIVE_LAUNCH" and same(prepared["config_ref"],pin(C/"controller.public.config.json")),"prepared_actual_context_bound")
        rootio=obj(C/"original-root-tool-io.json")
        check(rootio["result"]["exit_code"]==0 and "ROOT_PYTHON_EXIT=0" in rootio["result"]["output"] and rootio["actual_python_exit"]==0,"context_original_tool_outer_and_marked_Python_zero")
        for path,g in receipts.items():
            check(closed(g),"historical_guard_closed_"+Path(path).name)
        cg=receipts[str(C/"config-input-source-guard.cleanup.actual.json")]
        cmap={key(x["path"]):x for x in cg["entries"]}
        check(all(key(r["path"]) in cmap and same(r,cmap[key(r["path"])]) for r in cfg["FrozenInputs"]) and len(cmap)==4304,"Root_actual_context_guard_all4303_plus_cfg")
        compiler_guard=receipts[str(A/"compiler-source-guard.cleanup.actual.json")]
        cm={key(r["path"]):r for r in compiler_guard["entries"]}
        check(all(key(r["path"]) in cm and same(r,cm[key(r["path"])]) for r in inventory["build_inputs"]+inventory["product_inventory"]+inventory["compiler_tool_refs"]),"Root_actual_compiler_guard_full_inventory")
        input_guard=receipts[str(A/"input-source-guard.cleanup.actual.json")]
        im={key(r["path"]):r for r in input_guard["entries"]}
        check(key(actual["official_test2json_ref"]["path"]) in im and key(gopath) in im and key(gopath.parent.parent/"src/go.mod") in im,"Root_actual_inputguard_Go_srcmod_T2J")
        # Callers: exact inverse limited to top-level imports, config path, config pin.
        adaptation=[]
        for newpath,oldpath in ((S/"serve_one_positive_temp.actual_owned.py",Path(caller["serve_base"])),(P/"root_public_api_temp.actual.py",Path(caller["api_base"]))):
            old=raw(oldpath).decode("utf-8");new=raw(newpath).decode("utf-8")
            ot,nt=ast.parse(old),ast.parse(new);compile(new,str(newpath),"exec")
            changes=[x for x in difflib.SequenceMatcher(a=old.splitlines(True),b=new.splitlines(True),autojunk=False).get_opcodes() if x[0]!="equal"]
            allowed=True
            oldlines,newlines=old.splitlines(True),new.splitlines(True)
            for op,i1,i2,j1,j2 in changes:
                pair="".join(oldlines[i1:i2]+newlines[j1:j2])
                allowed=allowed and all(line.startswith(("import json,","C=Path(","C=B/","assert config_plain[")) for line in pair.splitlines())
            inverse=newlines[:]
            for op,i1,i2,j1,j2 in reversed(changes):inverse[j1:j2]=oldlines[i1:i2]
            check(allowed and "".join(inverse)==old,"caller_exact_inverse_"+newpath.name)
            check("19c92dc0af96281b0d00b1cb767ef3715e9f97102669722550e07888213808af" in new and "1163646" in new,"caller_exact_cfg_pin_"+newpath.name)
            check("import json,hashlib,types,sqlite3,struct,collections,uuid,subprocess,queue,threading,datetime,ctypes" in new,"caller_preloaded_runtime_"+newpath.name)
            funcs=lambda tree:{n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
            check(funcs(ot)==funcs(nt),"caller_all_functions_unchanged_"+newpath.name)
            patch="".join(difflib.unified_diff(oldlines,newlines,fromfile=str(oldpath),tofile=str(newpath)))
            with (O/(newpath.name+".diff")).open("x",encoding="utf-8") as f:f.write(patch)
            adaptation.append({"base_ref":held[key(oldpath)],"candidate_ref":held[key(newpath)],"inverse_equal":True,"changed_region_count":len(changes)})
        context_src=raw(C/"prepare_native_temp_controller_public_config.actual.py").decode("utf-8")
        check(context_src.index("import json,hashlib,types,uuid,sqlite3,struct,collections,subprocess,queue,threading,datetime,ctypes")<context_src.index("bootstrap.acquire("),"context_runtime_preload_before_bootstrap_freeze")
        check("c=cm.context(cfg_ref)" in context_src and "cm.serve(" not in context_src and "cm.sign_reviewed(" not in context_src,"actual_prepare_context_only_no_launch_or_sign")
        canonical=obj(A/"canonical.pre-run.exact.json")["refs"]
        check(all(same(pin(r["path"]),r) for r in canonical),"canonical_current_matches_CP361_baseline")
        cp=obj(R/"execution/v2.4/checkpoint.json");ow=obj(R/"execution/v2.4/path_ownership.json");commands=obj(R/"execution/v2.4/commands.json")
        check(cp["revision"]==361 and ow["revision"]==168 and commands["revision"]==39,"CP361_OW168_CM39")
        dirty=baseline_git[0]["stdout"].splitlines()
        check(len(dirty)==13 and sum(l.startswith(" D") for l in dirty)==11 and sum(l.startswith(" M") for l in dirty)==2 and baseline_git[1]["stdout"]=="","13_tracked_dirty_11D2M_empty_index")
        after_git=git_state();write("git-final.original-io.json",after_git)
        check(baseline_git==after_git,"tracked_git_baseline_unchanged")
        drift=[r["path"] for r in refs if not same(pin(r["path"]),r)]
        check(not drift,"all_held_inputs_current_no_drift",drift)
        write("input-pins.json",refs)
        write("own-callers-and-baseline-pins.json",{"own_script":pin(__file__),"caller_adaptations":adaptation,"canonical":canonical})
        write("actual-owned-jobs.json",inv_summary)
        write("source-check.json",{"schema":"researchos.independent-native-temp-prelaunch-review.v1","authority":"NONE","formal_acceptance":False,"decision":"COMPONENT_ACCEPTED_PRELAUNCH_CONDITIONAL" if all(c["passed"] for c in checks) else "REQUEST_CHANGES","checks":checks,"actual_compile_context_components_accepted":all(c["passed"] for c in checks),"held_public_inputs":len(refs),"held_total_bytes":sum(r["bytes"] for r in refs),"actual_jobs":8,"unit_parents":2,"unit_leaves":28,"pure_alias_comparison_not_real_junction":True,"actual_context_Run_by_Root_only":True,"reviewer_controller_context_helper_Go_native_SQL_sign_execution":False,"privatekey_DPAPI_originaltrial_contents_read":False,"global_provider_requests":None,"formal_progress":"0/42","native_positive_accepted":False,"new_mechanical_errors":2,"failure_ordinals":[856,858],"Root_next":"At most one Root manually approved fresh synthetic positive with these exact pins; separate per-payload manual signing/publication/release; independent whole SQL and native outcome review required. No automatic acceptance.","stop":True})
    finally:
        for g in reversed(guards):observations.append(g.close())
        write("guard-closure.json",observations)
    if not all(closed(g) for g in observations):raise ValueError("review guard closure")
    print(json.dumps({"decision":"COMPONENT_ACCEPTED_PRELAUNCH_CONDITIONAL" if all(c["passed"] for c in checks) else "REQUEST_CHANGES","failed_checks":[c for c in checks if not c["passed"]],"check_count":len(checks),"input_count":len(refs),"all_guards_closed":True,"source_check_ref":pin(O/"source-check.json")},ensure_ascii=False))
code=0
try:main()
except Exception:
    traceback.print_exc();code=1
finally:print("ROOT_PYTHON_EXIT="+str(code))
sys.exit(code)
