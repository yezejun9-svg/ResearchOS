"""Independent Source review: AST/expression-only counterexamples, no candidate entry."""
import ast, hashlib, json, shutil
from pathlib import Path, PureWindowsPath
from types import SimpleNamespace
from datetime import datetime, timezone
OUT=Path(__file__).resolve().parent
ROOT=Path("D:/作品集/ResearchOS/research-os")
BASE=ROOT/"execution/v2.4/receipts/W05/W05-99/mu_sdk_root_coordinator_source_v2_codex/6d87bf2c319543ca95b92efc8d2a3b58"
ACTOR="codex:/root/w05_merge_review"
def pin(p):
    p=Path(p); h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return {"path":str(p),"sha256":h.hexdigest(),"bytes":p.stat().st_size}
def put(name,obj):
    p=OUT/name
    with p.open("x",encoding="utf-8",newline="\n") as f: f.write(json.dumps(obj,ensure_ascii=False,indent=2)+"\n")
    return pin(p)
def verify(ref):
    got=pin(ref["path"])
    if got["sha256"]!=ref["sha256"] or got["bytes"]!=ref["bytes"]: raise RuntimeError("Source pin drift: "+ref["path"])
    return got
hdf=json.loads((BASE/"handoff.json").read_bytes())
manifest=json.loads((BASE/"manifest.json").read_bytes())
fixed=json.loads((BASE/"fixed-pins.json").read_bytes())
checked=[verify(ref) for ref in manifest["members"]]+[verify(ref) for ref in fixed.values()]
coordinator=(BASE/"root_coordinator.py").read_text(encoding="utf-8")
runner=Path(fixed["runner"]["path"]).read_text(encoding="utf-8")
tree=ast.parse(coordinator); rt=ast.parse(runner)
klass=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=="RootResidentCoordinator")
method=next(n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name=="execute_c7")
doc_assignment=next(n for n in method.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="doc" for t in n.targets))
values={k.value:v for k,v in zip(doc_assignment.value.keys,doc_assignment.value.values)}
def expression(node,context):
    return eval(compile(ast.Expression(node),"<independent extracted pure expression>","eval"),context)
authority=next(n for n in rt.body if isinstance(n,ast.FunctionDef) and n.name=="authority_binding")
once_check=next(n for n in ast.walk(authority) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="require" and any(isinstance(a,ast.Constant) and a.value=="Root one-time grant already consumed or foreign" for a in n.args))
class PathFixture:
    """Pure path algebra. Assume directory exists and once file absent; no filesystem calls."""
    def __init__(self,p): self.p=PureWindowsPath(p)
    def __truediv__(self,p): return PathFixture(self.p/p)
    def __eq__(self,other): return isinstance(other,PathFixture) and self.p==other.p
    @property
    def parent(self): return PathFixture(self.p.parent)
    @property
    def name(self): return self.p.name
    def is_absolute(self): return self.p.is_absolute()
    def is_dir(self): return True
    def exists(self): return False
    def __str__(self): return str(self.p)
run_uuid="0123456789abcdef0123456789abcdef"
data=PathFixture(str(ROOT/".local/review-fixture-unused"))
output=PureWindowsPath(str(ROOT/"execution/v2.4/receipts/W05/W05-99/review-fixture-unused"))
self_fixture=SimpleNamespace(output=output,run_uuid=run_uuid,admitted={})
bad_once=expression(values["once_path"],{"self":self_fixture})
good_once=str(data/"trial-once"/(run_uuid+".json"))
once_bad=expression(once_check.args[0],{"once":PathFixture(bad_once),"data":data,"uuid":run_uuid})
once_good=expression(once_check.args[0],{"once":PathFixture(good_once),"data":data,"uuid":run_uuid})
hash_fn=next(n for n in rt.body if isinstance(n,ast.FunctionDef) and n.name=="go_hash")
hash_ns={"json":json,"hashlib":hashlib}
exec(compile(ast.Module(body=[hash_fn],type_ignores=[]),"<independent extracted pure hash helper>","exec"),hash_ns)
raw_profile=b'{"fixture":"synthetic-profile-for-contract-only"}'
content_hash="sha256:"+hashlib.sha256(raw_profile).hexdigest()
profile_ref={"kind":"Artifact","id":"synthetic-profile","revision":1,"content_hash":content_hash}
ref_hash=hash_ns["go_hash"](profile_ref)
self_fixture.admitted={"profile_hash":content_hash}
bad_hash=expression(values["qualification_profile_hash"],{"self":self_fixture})
qual=next(n for n in rt.body if isinstance(n,ast.FunctionDef) and n.name=="exact_qualification")
hash_check=next(n for n in ast.walk(qual) if isinstance(n,ast.Compare) and ast.unparse(n).startswith("bindings[0][1] == marker[5] =="))
marker=[None]*10; marker[5]=ref_hash
ctx={"bindings":[(None,ref_hash)],"marker":marker,"doc":{"qualification_profile_hash":bad_hash}}
hash_bad=expression(hash_check,ctx)
ctx["doc"]["qualification_profile_hash"]=ref_hash
hash_good=expression(hash_check,ctx)
assert once_bad is False and once_good is True and hash_bad is False and hash_good is True and content_hash!=ref_hash
counter=put("pure-interface-counterexamples.json",{
 "schema":"researchos.independent-source-counterexamples.v1","actor_id":ACTOR,
 "method":"AST-extracted expressions only; synthetic values; no candidate import, entry, SQL, WinAPI or provider",
 "cases":[
  {"id":"R01","caller_line":doc_assignment.lineno,"caller_expression":ast.unparse(values["once_path"]),"consumer_line":once_check.lineno,"consumer_predicate":ast.unparse(once_check.args[0]),"synthetic_candidate_path":bad_once,"required_fixture_path":good_once,"candidate_accepted":once_bad,"corrected_accepted":once_good,"filesystem_queries":0,"fixture_directory_exists_assumed":True},
  {"id":"R02","caller_line":doc_assignment.lineno,"caller_expression":ast.unparse(values["qualification_profile_hash"]),"consumer_line":hash_check.lineno,"consumer_predicate":ast.unparse(hash_check),"synthetic_content_hash":content_hash,"synthetic_ArtifactRef_hash":ref_hash,"candidate_accepted":hash_bad,"corrected_accepted":hash_good,"SQL_calls":0}],
 "cases_passed":2,"cases_total":2,"candidate_native_calls":0,"formal_acceptance":False})
snapshots=[]
for name,p in [
 ("root_coordinator.py.source",BASE/"root_coordinator.py"),
 ("runner-v9.py.source",fixed["runner"]["path"]),
 ("controller-C7.py.source",fixed["controller"]["path"]),
 ("trusted-host-prepare.go.source",fixed["trusted_host_prepare_go"]["path"]),
 ("trusted-host-execute.go.source",fixed["trusted_host_execute_go"]["path"]),
 ("domain-runtime-qualification.go.source",ROOT/"internal/domain/runtime_qualification.go"),
 ("bootstrap-v3.py.source",ROOT/"execution/v2.4/receipts/W05/W05-99/sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d/actual-cli-bootstrap-v3-80c7b29a01c341a884597b7da9e17c4a/bootstrap_actual_cli.v3.py")]:
    raw=Path(p).read_bytes()
    with (OUT/name).open("xb") as f:f.write(raw)
    snapshots.append({"source_ref":pin(p),"snapshot_ref":pin(OUT/name)})
put("source-verification.json",{"verified_manifest_members":len(manifest["members"]),"verified_fixed_roles":len(fixed),"checked_refs":checked,"snapshots":snapshots,"native_binaries_executed":False})
review={
 "schema":"researchos.root-sdk-coordinator-source-review.v1","actor_id":ACTOR,
 "decision":"BLOCKED_SOURCE","source_ref":hdf["source_ref"],"fixed_pins_ref":hdf["fixed_pins_ref"],
 "scope":"Complete coordinator v2 Source and actual pinned TrustedHost v2/C7/v9 interface integration",
 "authorship":{"candidate_authors":["codex:/root","codex:/root/command_queue_impl"],"reviewer_is_candidate_author":False,"observer_O4_not_re_reviewed":True,"reused_controller_review_ref":fixed["controller_review"]},
 "findings":[
 {"id":"R01","priority":"BLOCKER","title":"C7 once_path cannot pass pinned v9 authority contract","caller_lines":[334],"consumer_lines":[668,669,670],"trigger":"Any MODEL_TRIAL reaching C7 after successful Host qualification","actual":"Caller puts once file under receipts output with fixed c7-execute.once.json filename. v9 requires data_root/trial-once/<run_uuid>.json and an existing trial-once directory. Bootstrap v3 only creates trial-control.","impact":"C7 precheck fails after the qualification provider request; no ordinary model turn can run.","minimal_fix":"During provider-free setup create/validate the isolated data_root/trial-once directory; construct once_path with current run_uuid filename under that directory, leave the file absent until v9 consume_once. Freeze this exact path in basis/registration/grant; never delete or reset an existing once file."},
 {"id":"R02","priority":"BLOCKER","title":"Content hash passed as qualification ArtifactRef hash","caller_lines":[334],"host_prepare_lines":[143,151],"domain_lines":[152,341],"consumer_lines":[1191,1198],"trigger":"After R01 is fixed, any valid qualification with different content and ArtifactRef digests","actual":"Host admitted.profile_hash derives from Artifact.content_hash. Domain runtime_bindings and runtime_qualification_runs store Hash(ArtifactRef), as v9 explicitly requires. Caller forwards the content hash into qualification_profile_hash.","impact":"v9 exact_qualification rejects valid completed qualification and wait_qualification retries that predicate until the shared deadline; ordinary requests remain unstarted.","minimal_fix":"Keep Host content-hash fields and GO contract unchanged. Populate C7 qualification_profile_hash from the exact actual ArtifactRef digest (engine.go_hash(profile_entity_ref)); before GO, read and cross-check that digest with the current project/runtime binding and admitted qualification marker. Preserve original profile byte hash separately."}],
 "counterexample_ref":counter,"findings_total":2,"remaining_blockers":2,
 "reviewed_without_additional_findings":[
 "Host seven-pin GO fields and Host READY/discovery/PID identity match the pinned consumer",
 "prepare precedes one shared 300s admission/qualification/C7 clock; C7 uses same monotonic bounds and UTC origin",
 "Host execution authority is separate from Source review; C7 ordinary phase authority is generated only after READY_FOR_ORDINARY",
 "Root holds reviewed sources, own suspended Host Jobs, cleanup producers and watchdogs in one anchored parent",
 "stdin closes for cancellation before Host teardown; ambiguous GO is never retried; unknown cleanup retains same parent and source owners",
 "v2 run_resident retains parent in finally when retained-status serialization or stdout fails",
 "provider count remains unknown after any GO; full count and UNKNOWN ledger claims require original v9 evidence; Source does not establish them",
 "native exit is preserved in invocations; parent Python exit is not invented"
 ],
 "bootstrap_runtime_status":"No successful actual bootstrap result currently available; parent reported Goal Native3 RESOURCE_BLOCKED with closed Jobs and no provider",
 "candidate_native_WinAPI_SQL_provider_calls":0,"canonical_writes":0,"runtime_qualification":False,
 "formal_acceptance":False,"execution_authority":False,"new_tool_failures":[724,726],
 "minimum_revision_scope":["new coordinator Source version","provider-free once-directory/path preparation","C7 ArtifactRef-hash translation and actual binding checks","two focused pure expression controls","updated source pins/handoff and independent delta review"],
 "prohibited_inferred_actions":["no candidate execution","no automatic GO","no provider call","no canonical change","no O4 self-review","no actual lifecycle acceptance"],
 "stopped":True}
put("independent-source-review.json",review)
report="""完整源码与实际接口组合审查结论：BLOCKED_SOURCE，2 个阻断项。

R01（root_coordinator.py:334）：once_path 指向 receipts output/c7-execute.once.json；固定 v9 在 668–670 行要求 data_root/trial-once/<run_uuid>.json，且父目录必须存在。bootstrap v3 只创建 trial-control。即使父目录乐观假设存在，当前路径仍不可能通过。Host qualification 完成后，C7 第一遍预检便停止。

R02（root_coordinator.py:334）：qualification_profile_hash 取 Host admitted.profile_hash。Host prepare.go:143 的来源是 Artifact.content_hash；实际 domain/runtime_qualification.go:152、341 和 v9:1191、1198 要求 Hash(ArtifactRef)。修好路径后，此错配仍使有效资格被反复拒绝直至共用时限到期。

最小修改：coordinator 在 provider-free 准备阶段建立隔离 trial-once 目录，用 current run_uuid 构造一次性文件路径，并保持文件由 v9 独占消费；给 C7 传入实际 ArtifactRef 的散列，事先与当前 binding/qualification marker 交叉校验。Host GO 内原有内容散列含义不变。无需修改 C7、v9 或 O4。

七份 GO 证据、qualification 到普通 phase 顺序、共享时限、同父进程 Source/Job 保留、stdout 异常保活、计数未知和原始退出层已完成源码核对，未发现额外阻断项。两例均以源码抽取的纯表达式重现，使用显式 synthetic 数据；未运行候选入口、WinAPI、SQL 或 provider，也未修改 canonical。

原有 O4/C7 非作者审查只复用，没有自审 O4。现有 bootstrap 仍未成功，本回执不授予执行、runtime qualification 或 formal acceptance。两个实际读取工具错误为724和726，原始可得I/O已保留。STOP。
"""
with (OUT/"REVIEW.md").open("x",encoding="utf-8",newline="\n") as f:f.write(report)
print(json.dumps({"decision":"BLOCKED_SOURCE","findings":2,"pure_counterexamples_passed":2,"review_ref":pin(OUT/"independent-source-review.json"),"candidate_calls":0},ensure_ascii=False))

