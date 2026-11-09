import sys
sys.dont_write_bytecode=True
import ast,hashlib,json,re
from pathlib import Path
O=Path(__file__).resolve().parent;B=O.parents[1]
C=B/"native_controller_retained_window_revision_codex/ctl4-1a11e7f5205729390aaee9f47b28ce6"
N=B/"integration_codex/native-cleanup-compile-source-root-1791516889000"
refs={};checks=[]
def read(p):
    p=Path(p).resolve();raw=p.read_bytes();refs[str(p)]=dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw));return raw
def pin(p):
    p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def check(name,ok):
    checks.append(dict(name=name,passed=bool(ok)));assert ok,name
def obj(p):return json.loads(read(p))
def verified(r):
    raw=read(r["path"]);check("ref:"+Path(r["path"]).name,(hashlib.sha256(raw).hexdigest(),len(raw))==(r["sha256"].removeprefix("sha256:"),r["bytes"]));return raw
def write(name,v):
    with (O/name).open("x",encoding="utf-8",newline="\n") as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write("\n")
for root,items in ((C,{"HDF.json":("9b335e2099575e3737b038ba212315bf4d4f1e2311614961d20bf8770cc578cc",3169),"MF.json":("14a6d3df02728fcc2b675658d4c2247a66f07d271826fd7bbe54c0ac7ad2de03",4028)}),(N,{"HDF.json":("5369fed93f7de95924c85073a5f82733523d1ef01223075ba3f2061d79425218",759),"MF.json":("3f57084fea8633a0d1a36714c3e1e79b51de40ff74f638bf7ca2f39a387a003f",1367)})):
    for name,(h,z) in items.items():
        raw=read(root/name);check("fixed:"+root.name+":"+name,(hashlib.sha256(raw).hexdigest(),len(raw))==(h,z))
    members=obj(root/"MF.json")["members"]
    check("manifest-shape:"+root.name,isinstance(members,dict) if root==C else isinstance(members,list))
    for r in members.values() if isinstance(members,dict) else members:verified(r)
ch=obj(C/"HDF.json");base=verified(ch["base_ref"]).decode("utf-8");ctl=verified(ch["source_ref"]).decode("utf-8")
old=read(B/"native_migration_controller_temp_env_revision_codex/e6a4d23ff0a84a6d9c2905181d97c2e4/root_native_migration_controller.py")
check("CTL3-original-exact",base.encode()==old)
replacements=obj(C/"source-replacements.json");check("CTL4-three-replacements",len(replacements)==3)
rebuilt=base
for row in replacements:
    check("CTL4-single-original:"+row["old"],rebuilt.count(row["old"])==1)
    rebuilt=rebuilt.replace(row["old"],row["new"],1)
check("CTL4-full-forward-byte-proof",rebuilt==ctl)
inverse=ctl
for row in reversed(replacements):inverse=inverse.replace(row["new"],row["old"],1)
check("CTL4-full-inverse-byte-proof",inverse==base)
bt=ast.parse(base);ct=ast.parse(ctl)
bc=[x for x in ast.walk(bt) if isinstance(x,ast.Constant)];cc=[x for x in ast.walk(ct) if isinstance(x,ast.Constant)]
changes=[(a.lineno,a.value,b.value) for a,b in zip(bc,cc) if a.value!=b.value]
check("CTL4-only-runtime-three-constant-values",set(changes)=={(345,1260,1560),(372,1260,1560),(388,1270,1570)})
for a,b in zip(bc,cc):b.value=a.value
check("CTL4-rest-AST-identical",ast.dump(bt)==ast.dump(ct))
check("deadline-hierarchy",1200+240<1500<1560<1800 and 1560<1570<1800)
check("Go25-not-changed",'"-test.timeout=25m"' in ctl)
for r in obj(C/"prerequisites.json").values():
    if isinstance(r,dict) and set(r)>={"path","sha256","bytes"}:verified(r)

p=obj(N/"adaptation.provenance.json")
for change in p["changes"]:
    a=verified(change["base_ref"]).decode("utf-8");b=verified(change["new_ref"]).decode("utf-8")
    derived=a
    for row in change["sequential_replacements"]:
        check("N12-replacement-count:"+row["before"][:80],derived.count(row["before"])==row["count"])
        derived=derived.replace(row["before"],row["after"])
    check("N12-forward:"+Path(change["new_ref"]["path"]).name,derived==b)
    inverse=b
    for row in reversed(change["sequential_replacements"]):inverse=inverse.replace(row["after"],row["before"])
    check("N12-inverse:"+Path(change["new_ref"]["path"]).name,inverse==a)
    ast.parse(b)
check("preparer-two-literals-only",len(p["changes"][0]["sequential_replacements"])==2)
for key in ("base43_source_ref","base_actual_closed_ref","cleanup_source_handoff_ref","cleanup_source_manifest_ref","cleanup_independent_ref","cleanup_independent_manifest_ref"):verified(p[key])
source43=json.loads(verified(p["base43_source_ref"]))
check("base43-list",isinstance(source43,list) and len(source43)==43)
for r in source43:verified(r)
check("base43-paths-unique",len({r["path"].casefold() for r in source43})==43)
clmf=json.loads(verified(p["cleanup_source_manifest_ref"]))
check("cleanup-manifest-actual-dict",isinstance(clmf["members"],dict))
new_candidates=[(k,r) for k,r in clmf["members"].items() if k.startswith("candidate-root/")]
check("one-cleanup-candidate",len(new_candidates)==1 and new_candidates[0][0]=="candidate-root/internal/domain/native_migration_authority_harness_windows_test.go")
cl_source=verified(new_candidates[0][1]).decode("utf-8")
old_member=[r for r in source43 if r["path"].replace("\\","/").endswith("/internal/domain/native_migration_authority_harness_windows_test.go")]
check("original-one-harness",len(old_member)==1 and old_member[0]["sha256"]=="972166b2744d1048dc747e8a5b4991cd0b06cbbdc8a523c90fef12e27e02e0e9")
check("reviewed-cleanup-candidate-exact",new_candidates[0][1]["sha256"]=="bbccac67b4143632160defb5ecf2c1697a062e448e793d8fbfed8070d3b68f73")
review=json.loads(verified(p["cleanup_independent_ref"]))
check("cleanup-status-field-matches",review["status"]=="SOURCE_ACCEPTED_PENDING_RESOURCE_PREREQUISITE_AND_ROOT_ACTUAL")
rm=json.loads(verified(p["cleanup_independent_manifest_ref"]))
check("review-manifest-actual-dict",isinstance(rm["members"],dict))
for r in rm["members"].values():verified(r)

a=Path(p["base_actual_closed_ref"]["path"]).parent
closed=json.loads(verified(p["base_actual_closed_ref"]))
check("N8-actual-8-jobs",len(closed["invocation_refs"])==8)
native_jobs=[]
for r in closed["invocation_refs"]:
    inv=json.loads(verified(r));res=inv["result"];j=res["job_cleanup"]
    check("historical-owned-zero:"+Path(r["path"]).name,res["actual_exit"]==0 and inv["actual_native_exit"]==0 and res["error"] is None and res["timed_out"] is False and j["active_processes_last_observed"]==0 and j["errors"]==[] and all(j[k] is True for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed")))
    native_jobs.append(dict(argv=inv["argv"],receipt_ref=r))
for name in ("runtime","binary","compiler","candidate","input"):
    g=obj(a/(name+"-source-guard.cleanup.actual.json"))
    check("historical-guard:"+name,g["closed"] is True and g["errors"]==[] and g["retained_handles_count"]==0)
units=json.loads(verified(closed["unit_detail_ref"]))
oldactions=units["actions"]
check("N8-historical-28leaves-2parents",len(oldactions)==30 and sum("/" in n for n in oldactions)==28 and all(v=="pass" for v in oldactions.values()))
tail=cl_source[cl_source.index("func TestNativeHarnessCleanupReviewContext("):]
children=re.findall(r't.Run\("([^"]+)"',tail)
check("new-four-exact-children",children==["expired-main-deadline","main-cancel-does-not-end-cleanup","cleanup-cancel-does-not-cancel-main","fresh-four-minute-deadline"])
expected=dict(oldactions);expected["TestNativeHarnessCleanupReviewContext"]="pass"
for name in children:expected["TestNativeHarnessCleanupReviewContext/"+name]="pass"
check("expected35terminal32leaf3root",len(expected)==35 and sum("/" in n for n in expected)==32 and sum("/" not in n for n in expected)==3)

driver=read(N/"validate_native_cleanup_compile_units.actual_owned.py").decode("utf-8")
prep=read(N/"prepare_native_cleanup_sparse.actual_owned.py").decode("utf-8")
dt=ast.parse(driver);pt=ast.parse(prep)
parents=next(ast.literal_eval(node.value) for node in ast.walk(dt) if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="unit_parents" for t in node.targets))
check("three-source-selected-parents",set(parents)=={n for n in expected if "/" not in n} and len(parents)==3)
selector="^("+"|".join(parents)+")$"
check("selector-excludes-native-harness",re.fullmatch(selector,"TestNativeMigrationAuthorityHarness") is None and all(re.fullmatch(selector,n) for n in parents))
check("entire-terminal-set-no-fail-skip",'assert len(actions)==35 and sum("/" in n for n in actions)==32 and all(a=="pass" for a in actions.values())' in driver and 'assert set(n for n in actions if "/" not in n)==set(unit_parents)' in driver and 'assert all(n.split("/",1)[0] in unit_parents for n in actions)' in driver and '"duplicate test terminal"' in driver)
check("dynamic-checkpoint-no361",'cp_sha,cp_bytes,cp_rev=sys.argv[3],int(sys.argv[4]),int(sys.argv[5])' in driver and 'checkpoint_revision=cp_rev' in driver and '==361' not in driver)
check("compiler-actual-test-and-embed-fields",all('"'+n+'"' in driver for n in ("TestGoFiles","XTestGoFiles","EmbedFiles","TestEmbedFiles","XTestEmbedFiles","CompiledGoFiles")))
check("five-guards-finally-closure",'((runtime_guard,"runtime"),(binary_guard,"binary"),(compiled,"compiler"),(candidate,"candidate"),(guard,"input"))' in driver and 'assert c["closed"] and not c["errors"] and c["retained_handles_count"]==0' in driver)
buildloop=next(n for n in ast.walk(dt) if isinstance(n,ast.For) and isinstance(n.target,ast.Tuple) and [ast.unparse(t) for t in n.target.elts]==["label","target"])
builds=ast.literal_eval(buildloop.iter)
check("four-program-build-targets",builds==(("control-build","./apps/control"),("maintenance-root-build","./ops/supervisor/recovery_root"),("enrollment-build","./ops/supervisor/recovery_enrollment"),("backup-build","./ops/backup")))
calls=[n for n in ast.walk(dt) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="success"]
literal_labels=[n.args[0].value for n in calls if isinstance(n.args[0],ast.Constant)]
check("eight-owned-build-jobs",set(literal_labels)=={"format","tagged-compiler-input-list","tagged-test-binary-compile","broker-temp-units"} and len(literal_labels)+len(builds)==8)
pcalls=[n for n in ast.walk(pt) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="invoke"]
check("six-owned-Git-jobs",len(pcalls)==6 and {n.args[0].value for n in pcalls}=={"head-before","tracked-status","staged-status","create-worktree","checkout-product-source","head-after"})
check("fresh-program-directory",'scratch=R/".local/native-cleanup-compile-env-1791516889000";scratch.mkdir(parents=True,exist_ok=False)' in driver)
check("42-formatted-sources-stay-exact",'if n not in changes:assert pin(T/n)["sha256"]==ref["sha256"] and pin(T/n)["bytes"]==ref["bytes"]' in driver)
check("runtime-claims-nativezero-not-executed",'native_migration_cases_executed=0' in driver and 'real_owner_private_input_used=False' in driver and 'issuer_signatures_created=0' in driver)
write("expected-units.source-only.json",dict(selector=selector,expected_actions=expected,parents=3,leaves=32,terminals=35,current_actual_run=False))
write("sourceguard.initial.json",dict(refs=list(refs.values()),method="read-only byte SHA256 before-after"))
for r in list(refs.values()):check("unchanged:"+Path(r["path"]).name,pin(r["path"])==r)
write("sourceguard.final.json",dict(refs=list(refs.values()),unchanged=True))
write("review-result.json",dict(CTL4_decision="SOURCE_ACCEPTED_PENDING_FRESH_CONFIG_AND_ROOT_ACTUAL",N12_decision="SOURCE_ACCEPTED_FOR_ROOT_BUILD_AND_PURE_UNITS",checks_count=len(checks),checks=checks,source_inputs=len(refs),Go_AST_compile_units_run=False,current_Git_Go_native_SQL_model=False,private_read=False,Main_canonical_write=False,full_native_retention_qualified=False,formal_Owner_whole9_acceptance=False,new_mechanical_failures=[]))
print(json.dumps(dict(CTL4="SOURCE_ACCEPTED_PENDING_FRESH_CONFIG_AND_ROOT_ACTUAL",N12="SOURCE_ACCEPTED_FOR_ROOT_BUILD_AND_PURE_UNITS",checks=len(checks),inputs=len(refs))))

