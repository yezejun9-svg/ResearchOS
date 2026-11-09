import hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
Q=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/workspace_epoch_fixture_source_codex/fa7c40fcaeed4dd5bdb649c9a77d393c")
T5=Path("D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2")
CAUSE=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/remaining_full_failure_cause_review_codex/8c83a215358ce0e859da44f08b8a69d3")
def pin(p):
 b=p.read_bytes();return {"path":p.as_posix(),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def write_new(name,value):
 raw=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2)+"\n"
 with (Q/name).open("x",encoding="utf-8",newline="\n") as f:f.write(raw)
base=json.loads((Q/"base-refs.json").read_text(encoding="utf-8"))
source=json.loads((Q/"source-refs.json").read_text(encoding="utf-8"))
static=json.loads((Q/"static-checks.json").read_text(encoding="utf-8"))
facts=json.loads((Q/"epoch-input-facts.json").read_text(encoding="utf-8"))
for member in base["refs"]+source["refs"]:
 assert pin(Path(member["path"]))==member,member
assert facts["scope_failed_leaf_count"]==1
target="TestClientWorkspaceImportExactBytesReplayAndEpoch"
candidate=Path(source["refs"][0]["path"])
candidate_text=candidate.read_text(encoding="utf-8")
line_refs={}
for i,line in enumerate(candidate_text.splitlines(),1):
 if "clientWorkspaceFixtureForEpoch" in line or "const currentEpoch" in line or "const oldEpoch" in line or "SELECT writer_epoch,revision" in line or "mapped current writer fixture" in line or "env.WriterEpoch =" in line:
  line_refs[str(i)]=line.strip()
cause=json.loads((CAUSE/"report.json").read_text(encoding="utf-8"))
original=cause["observed_test_counts"]
report=[
"# Workspace writer epoch fixture Source",
"",
"结论：只修原FULL的WORKSPACE_WRITER_EPOCH单叶；Source候选已封存，authority=NONE / formal_acceptance=false，等待独立复核及Root实际。",
"目标："+target+"；原actual FULL raw2800–2804是唯一该叶run/terminal fail，2802报MISSING_FIELD:writer_epoch，原FAILED事实保留。",
"输入cause包用manifest.json（原包没有HDF/MF命名）；11成员指纹已核对。源report、source-pins、actualFULL完整raw与目标原事件均绑定epoch-input-facts。",
"",
"## 最小夹具修订",
"",
"原revPtr(0)会返回nil，DecodeEnvelope164–169在Execute前拒绝缺字段；不是一次到达STALE_WRITER_EPOCH gate的有效请求。",
"clientWorkspaceFixtureFor保持defaultepoch1，转入同体参数化clientWorkspaceFixtureForEpoch；原其他4Test及envelope/execute/defaultfixture helper字节不变。",
"只目标case通过生产MapClientSession实际映射currentepoch2/revision1。writer_client_id仍workspace-client，project/workspace仍原绑定，LeaseExpiresAt为同Session row的now+1hour，Protocol仍V2。",
"MapClientSession78–111验证epoch/revision>=1和writer/project等并将epoch/writer/lease一起insert；没有生产规则要求此合成currentstate中epoch<=revision。",
"新增Rootactual时执行的query/readback断言：同sid的epoch2、revision1、writer=b.ClientID、project=f.project、workspace=b.AuthorizedRef及futureRFC3339NanoLease。",
"原CONTENT_CONFLICT输入和最终正常import完整envelope明确writer_epoch=current2，negative完整envelopewriter_epoch=old1（非零且1<2），CommandID/project/session/revision仍原helper提供。",
"Execute931–959从同Session加载revision/epoch/client，epoch mismatch在nativeIO前拒绝；workspaceBinding73–90检查同sid/workspace及同row有效lease，未弱化任何gate。",
"此为synthetic当前epoch比较夹具，不是已接受的真实handoff历史。没有直接UPDATE epoch、绕过生产Map或伪造授权；不执行公共handoff。",
"",
"## 原断言与范围",
"",
"全文件16个原t.Fatal/Error/Skip调用、17个原assertion_or_error_if、5个Test名称及顺序完整保留；目标原7calls/7if全保留。",
"STALE_WRITER_EPOCH/noIO、CONTENT_CONFLICT/failed-uploadcount0、COMPLETED且nonreplay/revision2、精确storedbytes、同命令replay结果bytes与noIO、ARTIFACT journalcount1全部原字节断言保留。",
"默认helper其他case仍epoch1及原完整mapping体；只增加目标case前置coherence断言和正/负epoch字段。没有并吞其他FULL失败、skip、Q3/native、ledger、历史、W16或生产分支。",
"",
"## 验证与交接",
"",
"本轮固定Python短script指纹、PythonAST提取已pin纯词法工具、Go文本/分隔符检查；没有GoAST/compiler/gofmt/native/SQL/model/provider/private/sign/canonical执行。",
"Main/T4/T5/旧cause包/原FULL/Q3均只读，Root当前全局状态由Root维护，本包不复算成正式接受。原FULL计数："+json.dumps(original,ensure_ascii=False)+"。",
"source-refs、base-refs、static-checks、最小client_workspace_test.patch、完整工具IO随HDF/MF封存；新机械错误0，不reset历史failure。",
"实际候选行号："+json.dumps(line_refs,ensure_ascii=False),
"下一步Root独立Sourcereview→fresh isolatedcomposition→actual目标叶及必要默认fixture回归→independent actualreview；未执行不得PASS。",
"作者完成Source封存后STOP。",
""
]
write_new("report.md","\n".join(report))
hdf={
"schema":"researchos.workspace_epoch_fixture_source_hdf.v1","status":"SEALED_SOURCE_CANDIDATE_NOT_EXECUTED","authority":"NONE","formal_acceptance":False,"namespace":Q.as_posix(),
"root_base":T5.as_posix(),"scope":{"failed_leaf_count":1,"test":target,"cause_id":"WORKSPACE_WRITER_EPOCH","changed_test_files":1,"production_members":0},
"original_actual":{"FULL":facts["actual_FULL"],"leaf_events":facts["actual_events"],"original_counts":original,"status":"FAILED_NOT_UPGRADED"},
"cause_inputs":{"manifest":facts["cause_manifest"],"report":facts["report_ref"],"source_pins":facts["source_pins_ref"],"extracted_facts":pin(Q/"epoch-input-facts.json")},
"members":source["refs"],"base_refs":pin(Q/"base-refs.json"),"static_checks":pin(Q/"static-checks.json"),"diff":pin(Q/"client_workspace_test.patch"),"report":pin(Q/"report.md"),"tool_io":pin(Q/"tool-io.json"),
"fixture":{"evidence_kind":"SYNTHETIC_CURRENT_STATE_EPOCH_COMPARISON_NOT_HISTORICAL_HANDOFF","current_DB_epoch":2,"current_DB_revision":1,"old_negative_epoch":1,"current_positive_envelope_epoch":2,"default_other_fixture_epoch":1,"writer_same_as_envelope":"workspace-client","project_workspace_principal_binding":"unchanged originalfixture","lease":"same ClientSession row future now+1hour","protocol":"V2 unchanged","Root_actual_readback_fields":["writer_epoch","revision","writer_client_id","project_id","workspace_ref","lease_expires_at"],"producer":"production MapClientSession, not manual epoch UPDATE","public_handoff_executed":False},
"production_contract_refs":{"DecodeEnvelope_missing_writer":[164,169],"revPtr_nonpositive_is_nil":[1264,1268],"ClientService_live_revision_epoch_client":[931,959],"MapClientSession_validity_and_same_row_insert":[78,111],"workspace_lease_scope":[73,90]},
"preserved_assertions":{"all_file_calls":16,"all_file_assertion_or_error_if_nodes":17,"all_test_names":5,"scope_calls":7,"scope_if_nodes":7,"all_original_token_nodes_preserved":True,"other_test_bodies_byte_equal":True,"default_shared_fixture_semantics_epoch1_body_unchanged":True,"conditions":["CONTENT_CONFLICT","uploaded_content count0 on failure","STALE_WRITER_EPOCH and no I/O","COMPLETED non-replay revision2","exact sealed bytes","identical replay and no extra I/O","ARTIFACT outbox count1"]},
"candidate_line_refs":line_refs,
"execution":{"Go_AST":False,"Go_compiler":False,"Go_test":False,"gofmt":False,"native":False,"SQL":False,"model_provider":False,"private_credential":False,"sign":False,"canonical_write":False},
"protected_writes":[],"new_mechanical_failures":[],"failure_counter_reset":False,"remaining_required_work":["independent Source review","Root fresh integration","Root actual target/default fixture validation","independent actual review"],
"excluded_scope":["other FULL failure groups","Q3 native fixture revisions","ledger","historical source","W16","formal holdout or product acceptance"]}
write_new("HDF.json",hdf)
members=[pin(p) for p in sorted(Q.rglob("*")) if p.is_file()]
mf={"schema":"researchos.immutable_test_source_manifest.v1","status":"SEALED_SOURCE_CANDIDATE_NOT_EXECUTED","authority":"NONE","formal_acceptance":False,"namespace":Q.as_posix(),"source_member_count":1,"production_member_count":0,"members":members,"self_hash_excluded":["MF.json"],"postseal_IO_excluded":["seal-tool-io.json"]}
write_new("MF.json",mf)
assert all(pin(Path(m["path"]))==m for m in members)
assert all(pin(Path(m["path"]))==m for m in base["refs"])
print(json.dumps({"namespace":Q.as_posix(),"MF":pin(Q/"MF.json"),"HDF":pin(Q/"HDF.json"),"report":pin(Q/"report.md"),"source":source["refs"][0],"diff":pin(Q/"client_workspace_test.patch"),"static_checks":pin(Q/"static-checks.json"),"tool_io":pin(Q/"tool-io.json"),"members":len(members),"member_drift":0,"base_drift":0,"original_calls":16,"scope_original_calls":7,"original_if_nodes":17,"scope_original_if_nodes":7,"original_Test_names":5,"new_mechanical_failures":0,"Go_native_SQL_model_execution":0,"authority":"NONE","formal_acceptance":False},ensure_ascii=False))
