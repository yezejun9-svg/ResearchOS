import ast, hashlib, json
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os")
P=R/"execution/v2.4/receipts/W05/W05-99"
OUT=Path(__file__).parent
V=P/"wholeGo_root_cap_producer_source_revision_codex/034e52a7a96f4fb6a5f2e90b9e6a6b32"
S=P/"current58_whole_go_suite_configuration_sync_source_preparation_codex/4a8dca58606d4a4db695aa6dc9f082cb"
checks=[]; reads=[]
def pin(p):
 p=Path(p); raw=p.read_bytes()
 return {"path":str(p),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def rawref(ref):
 p=Path(ref["path"]); b=p.read_bytes()
 assert set(ref)=={"path","sha256","bytes"}
 assert hashlib.sha256(b).hexdigest()==ref["sha256"] and len(b)==ref["bytes"],str(p)
 reads.append(ref); checks.append({"check":"pin","ref":ref,"pass":True})
 return b
def read(p): return json.loads(Path(p).read_bytes())
def put(name,value):
 p=OUT/name
 with p.open("xb") as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
h=read(V/"handoff.json"); sm=read(S/"handoff.selected.json")
for path,sha,size in [(V/"handoff.json","05b7a2fed2d4c4627ae9ae9a28131e891b2e15c09cec9b40f97b6c53d7b44720",1971),(V/"manifest.json","2cbc7a4ab036c0b2ffc43601d9e575730fcc8b4df2e5966664734c3d099dc35d",1730)]:
 rawref({"path":str(path),"sha256":sha,"bytes":size})
for mfref in [h["manifest_ref"],sm["manifest_ref"]]:
 mf=json.loads(rawref(mfref)); rows=mf["members"]
 declared=mf.get("member_count",mf.get("count"))
 assert declared==len(rows)
 for ref in rows:rawref(ref)
src=rawref(h["source_ref"]); tree=ast.parse(src)
inv=json.loads(rawref(h["source_inverse_ref"]))
old=rawref(inv["old_ref"])
newblock=inv["exact_new_block"].encode();oldblock=inv["exact_old_block"].encode()
assert src.count(newblock)==1 and src.replace(newblock,oldblock)==old
checks.append({"check":"whole_byte_inverse_to_v1","pass":True})
oldtree=ast.parse(old)
olddefs={n.name:ast.dump(n,include_attributes=False) for n in oldtree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
newdefs={n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
assert set(olddefs)==set(newdefs)
assert [n for n in olddefs if olddefs[n]!=newdefs[n]]==["arm"]
checks.append({"check":"all_other_function_AST_unchanged","pass":True})
selected={k:rawref(v) for k,v in sm["selected_source_refs"].items()}
for k in ["gate","runner"]:ast.parse(selected[k])
contract=json.loads(selected["execution_contract"])
lines=src.decode().splitlines()
def line(fragment):
 hits=[i+1 for i,s in enumerate(lines) if fragment in s]
 assert hits,fragment
 return hits
def issue(id,title,fragments,why,fix):
 return {"id":id,"severity":"BLOCKER","title":title,"source_ref":h["source_ref"],
 "locations":[{"lines":line(x),"text":x} for x in fragments],
 "reason":why,"minimum_correction":fix,"evidence_kind":"STATIC_SOURCE_ANALYSIS_NOT_CANDIDATE_EXECUTION"}
findings=[
issue("CAP2-R01","源码 pin 被无条件作为 JSON 解析，四阶段正向链不可达",
['return unique_json(p.read_bytes())','read_pin(source["implementation_ref"])','read_pin(source["runner_ref"])','read_pin(source["gate_ref"])','read_pin(controller_source)'],
'attest 的 implementation_ref 对应 internal/host/runtime_check_windows.go；scope 的 runner_ref/gate_ref 对应真实 Python，arm 的 controller_source_ref 也是源码。read_pin 必定 json.loads，这些固定源码不是 JSON。真实输入在 attestation/scope/arm 前失败，heartbeat 改动不能修复。',
'分离 verified_raw/ref 与 verified_json；.go/.py 仅验证原字节并按必要 AST/源码 pin 处理。JSON 文件才解析。沿 attest→独审→scope→arm→close 静态逐输入格式列出消费者，保持选定源码完整 hash。'),
issue("CAP2-R02","校验与消费使用两次独立读取，未绑定实际消费字节",
['actual = pin_file(p)','return unique_json(p.read_bytes())'],
'pin_file 读取并校验第一份字节，随后 read_pin 第二次 read_bytes 才解析；文件在两次读取之间变化时，未验 hash 的 JSON 可被消费，包括 budgets/authority/checkpoint。此风险独立于 R01。',
'单次读取到 raw；对同一 raw 核 bytes/hash 后返回或解析，保留父级 reparse/路径约束。不得修成第二次读取或仅再次 stat。'),
issue("CAP2-R03","arm 的实际 Root 权限和19数值来源未锚定可信原件",
['checkpoint = read_pin(source["checkpoint_ref"])','read_pin(source["execution_contract_ref"])' if False else 'execution = read_pin(source["execution_contract_ref"])','os_probe.get("runner_pid") == outer["runner_pid"]','heartbeat = unique_json(heartbeat_path.read_bytes())'],
'arm 接受任意绝对 checkpoint_ref，未像选定 gate 一样限定 ROOT/execution/v2.4/checkpoint.json；execution_contract_ref/source pins 只校调用者自己提供的 hash/schema，不固定 selected 4a8 合同；actor_id 和非作者名字也来自任意 JSON。即使移除 R01，调用者可提供互相一致的离线 JSON 生成 authority-bundle 和名为 actual 的19数值。真实 gate 的 canonical checkpoint/PID/job 检查仍会阻止离线伪造直接运行，因此这里不声称已有 Go 越权。PID无creation identity，heartbeat年龄没有原 heartbeat pin/tick/probe观察时刻，六runtime数字只从声明派生。',
'将 Root 输入/ref 链锚定固定 actual canonical checkpoint 与已审 selected合同/source集合，核项目/当前注册/lease/ref；所有 raw/probe/controller审查与同run真实进程 PID+creation/job identity闭合。19值逐项标明 DECLARED/OBSERVED，heartbeat保留实际raw pin与单调时点，没实际controller/完整witness则HOLD，不以actor字符串当授权。'),
issue("CAP2-R04","close 不验证实际 terminal/退出/期限/清理证据的一致来源",
['terminal.get("schema") == "researchos.current58-whole-go-provisional-terminal.v1"','outer.get("all_owned_processes_exited") is True','"actual_root_outer_exit": invocation.get("actual_outer_exit")'],
'close 对 terminal 只核 schema，没有核来自该scope输出根的真实 report/terminal原文件、report_written/within_absolute_deadline及runner时点；selected runner terminal 没有run_uuid，因此可以同schema异run terminal替换。authority_bundle_ref未读取验证，outer/meter final不核schema/原preflight身份/实际PID creation/handles与cleanup/退出时刻，model count False==0可通过，actual_primary_go_calls负数/布尔值也未严格类型和下界。发生超时、缺exit字段或伪造cleanup布尔时仍可生成同一 close-observation。它始终不授qualified，风险是封存来源和控制闭合事实不足。',
'固定 report/terminal 到scope.output_root及原Root invocation/raw链，读取绑定authority/preflight和末态资源原件；严格int计数/nullable actualexit、全部子树/handle/cleanup/时点与deadline，保留失败首因和不完整状态而不是以布尔汇总充证据；不要求失败exit0，不将预期失败重写为PASS。'),
issue("CAP2-R05","输出目录未经过同等路径与reparse安全约束",
['stage, input_path, output_dir = sys.argv[1], canonical(sys.argv[2]), Path(sys.argv[3])','output_dir.is_absolute() and output_dir.is_dir() and not list(output_dir.iterdir())'],
'输入文件有逐父级reparse检查，但输出只要求绝对/目录/空，未canonical且未限Root授权命名空间。junction/外部空目录可在最终pin拒绝之前被put_new写入文件。scope.output_root虽canonical也未限定Root分配边界；静态準备不能被解释为任意目录写入许可。',
'写前验证输出及所有父级无reparse/alias，并精确绑定Root allocation/fresh namespace，不重用现有leaf；安全初始化后保留首异常和nullable部分输出原件。')
]
budget_matrix=[{"name":k,"value_origin":"reviewed root_limits_ref.budgets."+k,
 "type":"exact int","required":("0" if k=="max_model_requests" else ">0"),
 "scope_consumer":"scope.budgets","gate_consumer":"validate numeric_budget_keys",
 "observation":"DECLARED_ROOT_LIMIT_NOT_RUNTIME_MEASUREMENT"} for k in contract["numeric_budget_keys"]]
runtime_names=["runner_pid","outer_max_child_processes","meter_max_child_processes","meter_max_local_http_requests","meter_max_model_requests","heartbeat_age_seconds"]
assert len(budget_matrix)==13
runtime_matrix=[{"name":k,"origin":("outer_job_ref" if k.startswith("outer") or k=="runner_pid" else "meter_ref"),
 "observation":"REFERENCED_DECLARATION; heartbeat age calculated from unpinned live raw; requires actual controller/probe chain"} for k in runtime_names]
matrix={"schema":"researchos.whole-go-cap-producer-abi-review.v1","root_budget_fields":budget_matrix,"runtime_fields":runtime_matrix,
"total":19,"phase_matrix":[
 {"phase":"attest","inputs":"tree/native/Go exe/lock/implementation","finding_ids":["CAP2-R01","CAP2-R02","CAP2-R03"],"cycle":"attestation does not contain its independent review; separate review then scope preserves no-backref structure"},
 {"phase":"scope","inputs":"reviewed limits/finite/source/runtime/selected code/attestation+review","finding_ids":["CAP2-R01","CAP2-R02","CAP2-R03","CAP2-R05"]},
 {"phase":"arm","inputs":"scope/registration/grant/review/lease/checkpoint/outer/meter/paths/probe/controller review/heartbeat","finding_ids":["CAP2-R01","CAP2-R02","CAP2-R03"],"future_dependency":"real controller/OS/meter and live runner are required, absent in source proposal"},
 {"phase":"close","inputs":"scope/report/terminal/outerfinal/meterfinal/Rootinvocation","finding_ids":["CAP2-R02","CAP2-R04"]}],
"holds":"REAL_MODEL_B01_HOLD excluded; no SDK substitution or model authorization",
"heartbeat_delta":"monotonic_tick/time.monotonic with ROOT containment matches selected gate, whole inverse confirmed",
"gate_limit":"actual downstream gate separately checks fixed canonical checkpoint, runner current PID and Windows Job; no claim that arbitrary offline bundle passes that gate"}
audit=put("audit.json",{"schema":"researchos.static-source-audit.v1","checks":checks,"passed":len(checks),"failed":0,"candidate_executed":False,"new_tool_failure_count":0,"finding_count":len(findings),"read_refs":reads})
matrix_ref=put("abi-matrix.json",matrix)
report=put("report.json",{"schema":"researchos.whole-go-cap-producer-source-review-report.v1","actor":"codex:/root/w05_merge_review","findings":findings,"audit_ref":audit,"abi_matrix_ref":matrix_ref,"candidate_executed":False,"source_acceptance":False,"formal_case_accepted_delta":0,"new_tool_failure_origins":[]})
review=put("review.json",{"schema":"researchos.whole-go-root-cap-producer-independent-source-review.v1","reviewer":"codex:/root/w05_merge_review","author":"codex:/root/live_resource_lookup","non_author":True,"decision":"REQUEST_CHANGES","requested_changes":findings,
 "source_ref":h["source_ref"],"source_sha256":h["source_ref"]["sha256"],"selected_baseline_handoff_ref":pin(S/"handoff.selected.json"),"selected_source_refs":sm["selected_source_refs"],
 "report_ref":report,"audit_ref":audit,"abi_matrix_ref":matrix_ref,"actual_candidate_execution":False,"actual_grant_issued":False,"source_acceptance":False,"whole_suite_qualified":False,"formal_case_accepted_delta":0,"new_tool_failure_count":0})
handoff=put("handoff.json",{"schema":"researchos.independent-source-review-handoff.v1","review_ref":review,"report_ref":report,"decision":"REQUEST_CHANGES","requested_change_ids":[x["id"] for x in findings],"new_tool_failure_count":0,"status":"STOPPED"})
members=[pin(p) for p in sorted(OUT.iterdir()) if p.is_file()]
mf=put("manifest.json",{"schema":"researchos.public-review-manifest.v1","entries":members,"count":len(members),"self_excluded":True})
print(json.dumps({"review":review,"report":report,"manifest":mf,"handoff":handoff,"checks":len(checks),"findings":len(findings),"new_tool_failure_count":0},ensure_ascii=False))

