import sys
sys.dont_write_bytecode=True
import ast,hashlib,json,re
from pathlib import Path
O=Path(__file__).resolve().parent;B=O.parents[1];R=B.parents[4]
A=B/"integration_codex/native-cleanup-compile-source-root-1791516889000"
C=B/"integration_codex/native-cleanup-controller-source-root-1791517434000"
ISO=B/"integration_codex/native-cleanup-sparse-isolation-root-1791516889000"
PRE=B/"native_ctl4_n12_independent_review_codex/cn-20261009-source-review"
refs={};checks=[]
def read(p):
    p=Path(p).resolve();raw=p.read_bytes();r=dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
    if str(p) in refs:assert refs[str(p)]==r
    refs[str(p)]=r;return raw
def pin(p):
    p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def check(n,ok):
    checks.append(dict(name=n,passed=bool(ok)));assert ok,n
def obj(p):return json.loads(read(p))
def verify(r):
    raw=read(r["path"]);check("ref:"+Path(r["path"]).name,(hashlib.sha256(raw).hexdigest(),len(raw))==(r["sha256"].removeprefix("sha256:"),r["bytes"]));return raw
def write(n,v):
    with (O/n).open("x",encoding="utf-8",newline="\n") as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write("\n")
raw=read(A/"validation.closed.json")
check("N12-fixed-actual-closure",(hashlib.sha256(raw).hexdigest(),len(raw))==("cb2459bafde88bf99ab33bd34212fd2986e93e287fab1ad940437be9e3531d67",10936))
actual=json.loads(raw);io=obj(A/"postseal-root-actual-original-io.json")
check("Root-explicit-python-exits",io["explicit_python_exit"]=={"isolation":0,"validation":0})
check("Root-session99431-completion077758",io["validation_initial"]["session_id"]==99431 and io["validation_completion"]["chunk_id"]=="077758" and io["validation_completion"]["exit_code"]==0 and "ROOT_PYTHON_EXIT=0" in io["validation_completion"]["output"])
check("Root-isolation47252-completion35a0a8",io["isolation_initial"]["session_id"]==47252 and io["isolation_completion"]["chunk_id"]=="35a0a8" and io["isolation_completion"]["exit_code"]==0 and "ROOT_PYTHON_EXIT=0" in io["isolation_completion"]["output"])
prior_manifest=obj(PRE/"MF.json")
for r in prior_manifest["members"].values():verify(r)
check("prior-independent-source-acceptance",obj(PRE/"HDF.json")["N12_decision"]=="SOURCE_ACCEPTED_FOR_ROOT_BUILD_AND_PURE_UNITS")
ready=obj(ISO/"isolation.ready.json");check("six-Git-eight-build",len(ready["invocation_refs"])==6 and len(actual["invocation_refs"])==8)
jobs=[];invs={}
for r in ready["invocation_refs"]+actual["invocation_refs"]:
    v=json.loads(verify(r));res=v["result"];j=res["job_cleanup"]
    check("native-zero-closed:"+Path(r["path"]).name,type(res["actual_exit"]) is int and res["actual_exit"]==v["actual_native_exit"]==0 and res["timed_out"] is False and res["error"] is None and v["exception"] is None and type(res["owned_child_pid"]) is int and res["owned_child_pid"]>0 and type(res["creation_time_100ns"]) is int and res["creation_time_100ns"]>0 and j["active_processes_last_observed"]==0 and j["errors"]==[] and all(j[k] is True for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed")))
    verify(v["stdout_ref"]);verify(v["stderr_ref"])
    jobs.append(dict(receipt_ref=r,pid=res["owned_child_pid"],FILETIME_decimal=str(res["creation_time_100ns"]),native_exit=0,job_closed=True))
    invs[Path(r["path"]).name]=v
check("14-unique-process-identities",len({(x["pid"],x["FILETIME_decimal"]) for x in jobs})==14)
guards=[]
for root,names in ((A,["runtime","binary","compiler","candidate","input"]),(ISO,["runtime",""])):
    for name in names:
        p=root/((name+"-source-guard.cleanup.actual.json") if name else "source-guard.cleanup.actual.json")
        g=obj(p)
        check("guard-closure:"+root.name+":"+name,g["closed"] is True and g["retained_handles_count"]==0 and g["errors"]==[] and all(x["verified"] is True and x["final_path_match"] is True and x["closed"] is True for x in g["entries"]))
        guards.append(dict(path=str(p),entries=len(g["entries"]),bytes=sum(x["bytes"] for x in g["entries"])))
# All resulting source bytes and all five executables, without execution.
formatted=json.loads(verify(actual["formatted_source_ref"]));overlay=json.loads(verify(actual["source_overlay_ref"]))
check("43-actual-formatted-members",len(formatted)==43 and len(overlay["sources"])==43)
root=Path(actual["current_source_root"]);changed=[]
for r in formatted:
    raw=verify(r);key=Path(r["path"]).relative_to(root).as_posix();original=verify(overlay["sources"][key])
    if raw!=original:changed.append(key)
check("gofmt-zero-byte-changes",changed==[])
base43=json.loads(verify(actual["base43_formatted_ref"]))
base_by_name={Path(r["path"]).relative_to(Path(base43[0]["path"]).parents[0]).as_posix():r for r in []}
# Relative path is taken from the known old worktree, not guessed per member.
oldroot=Path("D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-native-temp-1791506570123")
base_by_name={Path(r["path"]).relative_to(oldroot).as_posix():r for r in base43}
deltas=[key for key,r in overlay["sources"].items() if (r["sha256"],r["bytes"])!=(base_by_name[key]["sha256"],base_by_name[key]["bytes"])]
check("42-same-one-CL-replacement",deltas==["internal/domain/native_migration_authority_harness_windows_test.go"])
fmtproof=obj(A/"owned-gofmt-output-scope.json");check("gofmt-proof-exact",fmtproof["unmodified_42_byte_equal"] is True and all(v["different_bytes"] is False for v in fmtproof["changed_source_refs"].values()))
n8=obj(B/"integration_codex/native-temp-compile-unit-root-1791508539969/revision-list-manifest/validation.closed.json")
for name,r in actual["binary_refs"].items():
    verify(r)
    expected_name="tagged-test-binary-compile" if name=="tagged-test-harness" else name
    inv=invs[expected_name+".invocation.json"];argv=inv["argv"]
    check("actual-output-bound:"+name,argv.count("-o")==1 and Path(argv[argv.index("-o")+1])==Path(r["path"]))
    check("fresh-program-namespace:"+name,Path(r["path"]).parent==Path("D:/作品集/ResearchOS/research-os/.local/native-cleanup-compile-env-1791516889000/programs"))
    if name!="tagged-test-harness":check("four-program-content-equal-N8:"+name,(r["sha256"],r["bytes"])==(n8["binary_refs"][name]["sha256"],n8["binary_refs"][name]["bytes"]))
check("actual-new-tagged-harness-pin",(actual["binary_refs"]["tagged-test-harness"]["sha256"],actual["binary_refs"]["tagged-test-harness"]["bytes"])==("74c14e02cb1394439e08d215781ca0af83512303db072342acd289fc02cd20f8",42295296))
verify(actual["official_test2json_ref"])
unit=json.loads(verify(actual["unit_detail_ref"]));events=[json.loads(x) for x in verify(unit["original_jsonl_ref"]).decode("utf-8").splitlines() if x.strip()]
term={}
for event in events:
    if event.get("Test") and event.get("Action") in ("pass","fail","skip"):
        check("unique-terminal:"+event["Test"],event["Test"] not in term);term[event["Test"]]=event["Action"]
expected=obj(PRE/"expected-units.source-only.json")
check("actual-exact-35-test-names",term==expected["expected_actions"]==actual["unit_actions"]==unit["actions"])
check("32leaves3roots35PASS0FAIL0SKIP",len(term)==35 and sum("/" in n for n in term)==32 and all(v=="pass" for v in term.values()) and (actual["unit_pass_count"],actual["unit_fail_count"],actual["unit_skip_count"])==(35,0,0))
check("no-native-case-event",not any(e.get("Test","").split("/")[0]=="TestNativeMigrationAuthorityHarness" for e in events))
uargv=invs["broker-temp-units.invocation.json"]["argv"]
check("official-test2json-and-fixed-selector",uargv[0]==actual["official_test2json_ref"]["path"] and "-test.run="+expected["selector"] in uargv)
# Reconstruct every compiler path plus embed record from the raw go list stream.
inventory=json.loads(verify(actual["compiler_input_inventory_ref"]))
check("actual-inventory-counts",(inventory["package_count"],inventory["build_input_count"],inventory["product_inventory_count"])==(364,3793,599))
for r in inventory["build_inputs"]+inventory["product_inventory"]+inventory["compiler_tool_refs"]+[inventory["GoRef"]]:verify(r)
raw=verify(invs["tagged-compiler-input-list.invocation.json"]["stdout_ref"]).decode("utf-8")
decoder=json.JSONDecoder();pos=0;packages=[];found={};embeds=[]
fields=("GoFiles","CgoFiles","CFiles","CXXFiles","MFiles","HFiles","FFiles","SFiles","SwigFiles","SwigCXXFiles","SysoFiles","CompiledGoFiles","TestGoFiles","XTestGoFiles","EmbedFiles","TestEmbedFiles","XTestEmbedFiles")
while pos<len(raw):
    while pos<len(raw) and raw[pos].isspace():pos+=1
    if pos==len(raw):break
    pkg,pos=decoder.raw_decode(raw,pos);check("go-list-package-clean:"+pkg.get("ImportPath",""),not pkg.get("Error") and not pkg.get("DepsErrors"));packages.append(pkg.get("ImportPath"))
    if not pkg.get("Dir"):continue
    for field in fields:
        for name in pkg.get(field,[]):
            path=Path(name);path=path if path.is_absolute() else Path(pkg["Dir"])/path
            pr=pin(path);found[str(path)]=pr
            if field.endswith("EmbedFiles"):embeds.append(dict(package=pkg["ImportPath"],ref=pr,field=field))
check("raw-go-list-364packages-exact",packages==inventory["packages"])
check("raw-go-list-3793inputs-exact",list(found.values())==inventory["build_inputs"])
check("raw-go-list-38embeds-exact",embeds==inventory["actual_embed_files"] and len(embeds)==38)
product={}
for relative in ("apps/control","internal","adapters","evaluation","ops","migrations/sqlite","spec/v2.0/contracts"):
    for path in (root/relative).rglob("*"):
        check("product-no-symlink:"+str(path.relative_to(root)),not path.is_symlink())
        if path.is_file():product[str(path)]=pin(path)
for relative in ("go.mod","go.sum","execution/toolchains/locked.json"):product[str(root/relative)]=pin(root/relative)
check("whole-product599-exact",product=={r["path"]:r for r in inventory["product_inventory"]})
pre=json.loads(verify(actual["canonical_pre_run_ref"]))
check("N12-CP363",pre["checkpoint_revision"]==363)
for r in pre["refs"]:verify(r)
check("no-native-private-provider-claims",actual["native_migration_cases_executed"]==actual["issuer_signatures_created"]==actual["production_db_writes"]==actual["external_model_provider_requests"]==0 and actual["real_owner_private_input_used"] is False and actual["formal_acceptance"] is False)

# C12 Source-only, never executing the builder or controller.
for name,h,z in [("HDF.json","5df195b58213bb884c1df02d9572b5c173758c5a4d38fdb277c0f7b41a5481b9",790),("MF.json","5ec35be4fc57653f364e0765a30d7953d3a92133efc9e7cdbe96832d04887cc8",1038)]:
    raw=read(C/name);check("C12-fixed:"+name,(hashlib.sha256(raw).hexdigest(),len(raw))==(h,z))
for r in obj(C/"MF.json")["members"]:verify(r)
prov=obj(C/"adaptation.provenance.json");old=verify(prov["base_ref"]).decode("utf-8");new=verify(prov["new_ref"]).decode("utf-8")
work=old
for row in prov["changes"]:
    check("C12-replacement-count:"+row["before"][:90],work.count(row["before"])==row["count"])
    work=work.replace(row["before"],row["after"])
check("C12-whole-forward-proof",work==new)
for row in reversed(prov["changes"]):work=work.replace(row["after"],row["before"])
check("C12-whole-inverse-proof",work==old)
ot=ast.parse(old);nt=ast.parse(new)
of={n.name:n for n in ot.body if isinstance(n,ast.FunctionDef)};nf={n.name:n for n in nt.body if isinstance(n,ast.FunctionDef)}
check("C12-all-original-functions-byte-exact",of.keys()==nf.keys() and all(ast.get_source_segment(old,of[n])==ast.get_source_segment(new,nf[n]) for n in of))
check("C12-dynamic-checkpoint", 'assert len(sys.argv)==4' in new and 'before[0]["sha256"]==sys.argv[1]' in new and '["revision"]==int(sys.argv[3])' in new)
check("C12-single-cold-context-only",sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=="cm" and n.func.attr=="context" for n in ast.walk(nt))==1 and not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in {"serve","sign_reviewed","publish_signed","release_fixture","run_owned","run_owned_observed","connect","Popen","system"} for n in ast.walk(nt)))
check("C12-no-auto-helper-exec",'phase_source/' in new and 'phase_review/' in new and 'module(phase_source' not in new)
check("C12-freezes-all-phase-manifest-members",'for d in (phase_source,phase_review):' in new and 'bootstrap_refs += [verify(v) for v in m]' in new and 'for v in bootstrap_refs:add(v)' in new)
check("C12-freezes-compiler-product-tools",'inventory["build_inputs"]+inventory["product_inventory"]+inventory["compiler_tool_refs"]' in new)
check("C12-fresh-case-and-temp",'hc["CaseID"]="t12cl149d6f49321"' in new and '"native-cleanup-controller-env-1791517434000"' in new and 'assert not Path(cfg["ControllerDirectory"]).exists() and not Path(hc["OutputDirectory"]).exists()' in new)
check("C12-bounded-read-guards",new.count("per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024")==2)
check("C12-finally-both-guards-close",'for g,n in ((fullguard,"config-input"),(bootstrap,"bootstrap")):' in new and 'assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0' in new)
# Resolve only literal Path assignments from Source without importing candidate.
env={"R":Path("D:/作品集/ResearchOS/research-os"),"B":B,"O":C}
def literal_path(node):
    if isinstance(node,ast.Constant) and isinstance(node.value,str):return node.value
    if isinstance(node,ast.Name) and node.id in env:return env[node.id]
    if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Div):return Path(literal_path(node.left))/literal_path(node.right)
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=="Path" and len(node.args)==1:return Path(literal_path(node.args[0]))
    raise ValueError("not literal path expression")
for node in nt.body:
    if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
        try:v=literal_path(node.value)
        except ValueError:continue
        if isinstance(v,Path):env[node.targets[0].id]=v
for key in ("V","Z","BP","BR","phase_source","phase_review"):
    directory=env[key]
    for name in ("HDF.json","MF.json"):read(directory/name)
    members=obj(directory/"MF.json")["members"]
    for r in members.values() if isinstance(members,dict) else members:verify(r)
for key in ("OLD","gp","hp","op","ctl"):read(env[key])
read(env["PU"]/"validation.closed.json");read(env["PU"]/"units.results.json")
check("C12-source-bindings-current",env["ctl"].name=="root_native_migration_controller.py" and pin(env["ctl"])["sha256"]=="e7538c580d2e07217512e036e00272b3be94cb11551ace6885cc46316a67b3b3" and obj(env["phase_review"]/"HDF.json")["finding_status"]=="CLOSED_IN_SOURCE")
# Core inventory already measured by N12, plus all reviewed inputs. Cold Python runtime closure remains a Root prepare check.
unique_sizes={r["path"]:r["bytes"] for r in refs.values()}
check("measured-core-inputs-below-2GiB",sum(unique_sizes.values())<2*1024*1024*1024)
check("measured-individual-inputs-below-256MiB",max(unique_sizes.values())<256*1024*1024)
write("actual-job-audit.json",dict(jobs=jobs,guards=guards,unit_terminals=term,actual_inventory=dict(packages=364,build_inputs=3793,product=599,embeds=38),gofmt_changed_members=[],formal_acceptance=False))
write("sourceguard.initial.json",dict(refs=list(refs.values()),method="read-only byte SHA256 before-after"))
for r in list(refs.values()):check("unchanged:"+Path(r["path"]).name,pin(r["path"])==r)
write("sourceguard.final.json",dict(refs=list(refs.values()),unchanged=True))
write("review-result.json",dict(N12_decision="ACCEPTED_BUILD_AND_PURE_UNIT_COMPONENT_ONLY",C12_decision="SOURCE_ACCEPTED_FOR_ROOT_PREPARE_PENDING_FINAL_PRELAUNCH_REVIEW",checks_count=len(checks),source_inputs=len(refs),checks=checks,N12_current_components_observed=True,current_reviewer_Git_Go_native_SQL_model=False,C12_builder_executed_by_reviewer=False,private_read=False,Main_canonical_write=False,full_native_retention_qualified=False,formal_Owner_whole9_acceptance=False,new_mechanical_failures=[]))
print(json.dumps(dict(N12="ACCEPTED_BUILD_AND_PURE_UNIT_COMPONENT_ONLY",C12="SOURCE_ACCEPTED_FOR_ROOT_PREPARE_PENDING_FINAL_PRELAUNCH_REVIEW",checks=len(checks),inputs=len(refs),measured_total_input_bytes=sum(unique_sizes.values()))))

