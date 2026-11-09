from pathlib import Path
import json,hashlib
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';O=B/'typed_q3_epoch_actual_independent_review_codex/7340313b128c426b97c9acb20731fa73'
D=B/'checkpoint_r357_independent_review_codex/1a11db9e0dff7ad081d6e06d';A=B/'sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d/checkpoint-r357-atomic-closed-tool-qualified-fixture-revision-open'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def pin(p):
 p=Path(p).resolve();data=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
def save(name,value):
 p=O/name
 with p.open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
 return pin(p)
def refs(value):
 if isinstance(value,dict):
  if all(k in value for k in ('path','sha256','bytes')):yield value
  for v in value.values():yield from refs(v)
 elif isinstance(value,list):
  for v in value:yield from refs(v)
def verify(ref):
 result=pin(ref['path']);assert result['sha256']==ref['sha256'].removeprefix('sha256:') and result['bytes']==ref['bytes'];return result
checks=read(O/'checks.json');assert checks['all_static_checks_passed']
mf=read(D/'MF.json');old_refs=list(refs(mf));old_by_path={str(Path(x['path']).resolve()):x for x in old_refs}
selected=[D/n for n in ('HDF.json','MF.json','evidence.json')]+[A/n for n in ('canonical_pair.actual.json','RESUME.r357.original.json')]
assert pin(D/'MF.json')['sha256']=='a96ce0319a0d9c5be58f28b68e81bca08edb501ec689ce41baf285c5c35a564c'
canonical_evidence=[]
for source in selected:
 if str(source.resolve()) in old_by_path:verify(old_by_path[str(source.resolve())])
 target=O/'canonical-evidence'/source.name;target.parent.mkdir(parents=True,exist_ok=True)
 with target.open('xb') as f:f.write(source.read_bytes())
 canonical_evidence.append(dict(original=pin(source),copy=pin(target)))
canonical=[]
for name in ('checkpoint','path_ownership','step_state','commands'):
 p=R/'execution/v2.4'/(name+'.json');ref=old_by_path[str(p.resolve())];canonical.append(verify(ref))
assert canonical==checks['canonical_before']==checks['canonical_after']
canref=save('canonical-verification.json',dict(schema='researchos.independent-canonical-corroboration.v1',current_matches_earlier_r357_sealed_refs=True,canonical_refs=canonical,earlier_evidence_copies=canonical_evidence,Root_T6_before_after_byte_assertion_passed=True,independent_T6_pre_run_byte_capture_available=False,review_interval_before_after_equal=True,limitation='T6 script retained canonical bytes in process memory and its closure asserted equality. It did not emit a separate pre-run canonical hash receipt. Current independent hashes equal earlier independently sealed CP357/OW/SS/CM.',Main_adopted=False,formal_acceptance=False))
temp=Path('C:/Users/yqyyds/AppData/Local/Temp')
for name in ('w0599_actual_read.py','w0599_actual_probe.py','w0599_actual_focus.py','w0599_actual_canonical.py','w0599_actual_seal.py'):
 target=O/name
 with target.open('xb') as f:f.write((temp/name).read_bytes())
report='''## Review Summary

**Verdict:** REQUEST CHANGES

**Overview:** Root T6 的 Q3 + epoch 49 Source 实际组合已执行并完整关闭，独立判定为 `FAILED_EXECUTION_CLOSED`。Goal 与 workspace epoch 的实际通过可作为限定范围的分项证据；6 个 runtime 父包装、8 个子叶用例失败，整体 typed runtime/native/FULL/formal 均未通过。

### Critical Issues

- `candidate-root/internal/domain/runtime_tool_integration_windows_test.go:40` 与 `runtime_typed_client_fixture_windows_test.go:571`：`muClientCall` 只允许 `COMPLETED`，却被用于实际返回 `ACKNOWLEDGED`、revision 3 的 `session.attach`。6 个 fresh child runner 下的 8 个叶用例都在该阶段报错，因此后续 runtime 行为尚未获得这次测试证明。应给 attach 使用符合其契约的专用检查，核验 accepted operation、Session 身份、owner/lease 与真实 revision；再在新的 Source 及新的实际组合中验证，保留本次 failure823 与原始事件。不要把通用 helper 放宽为无条件接受任意状态。

### Important Issues

- `candidate-root/internal/domain/runtime_typed_client_fixture_windows_test.go:572`：attach helper 还要求响应 revision 等于 created revision。该断言本次未执行到，不能声称已经实际失败；修复状态检查时应结合 attach 的真实写入/lease 状态确认 revision 契约，并用响应与事务读回保持后续命令版本一致。

### Suggestions

- `validate_q3_epoch.actual_owned.py:94`：下次实际运行可把 canonical 的 pre-run hash/bytes 单独落盘。本次 Root 的内存前后比较断言确实通过，当前独立 hash 也匹配旧 CP357 封存，但没有独立保存的 T6 pre-run receipt；本报告保留该边界。

### What's Done Well

- 官方 pinned test2json 输出中的实际 `fail` 没有被文本日志或部分通过覆盖；父包装严格失败，最终 runner exit 1 被完整保留。
- 4 个 owned Job 均关闭，5 组 SourceReadGuard 共用精确输入并全部释放。50 个公开 child evidence 文件已经逐字节复制进正式独立审查包及 MF，包含全部 raw/JSONL/result 和 8 份公开 TLS 证书，不再依赖 `.local` 作为唯一证据。

### Verification Story

- Tests reviewed: yes。从 Source 重建精确 25 父 scope；parent JSONL 有 61 pass、6 fail、0 skip，67 个 run 各有唯一 terminal，package terminal 为 fail。6 个 child runner 为独立 PID，8 个叶全部因 attach 返回状态失败；每个 runner exit 1。native child PID/exit 原字段为 null，未虚构直接观测；官方 reporter 的退出传播只支持静态推断。
- Build verified: yes，复核 Root 实际 receipts/raw 及输入，未重跑。fmt/list/compile/parent exits 为 0/0/0/1。352 packages、3,726 build inputs、600 product inventory、8 compiler tools、36 embeds 均复算并与 Go list、guard 集合相符；总计独立核验 4,141 个唯一文件的精确 hash/bytes。
- Security checked: yes，限定公开证据与 Source。Go/Node/Mu/test2json 由 held input refs 固定；test2json 直接使用官方冻结二进制。此次提供者仅 synthetic loopback TLS，Root 记录 external provider requests 0、original trial provider requests null、original trial DB untouched；未执行新的 Go/native/SQL/model/private workload。
- Main/canonical: 当前 Main 输入匹配 T6 input guard 固定值；CP357/OW/SS/CM 与此前封存精确一致，且本次审查前后无变化。T6 的 closure 在完整内存前后比较通过后写出失败闭合记录。Main 未采纳、formal_acceptance=false。

Goal 的 expired_lease、missing_lease 与 workspace import epoch 均有独立 run/pass 事件，接受仅限本次 synthetic component observed scope。没有把它们升格为 native/runtime/FULL 或产品正式验收。
'''
with (O/'report.md').open('xb') as f:f.write(report.encode('utf-8'))
hdf=save('HDF.json',dict(schema='researchos.independent-actual-review-handoff.v1',verdict='FAILED_EXECUTION_CLOSED',code_review_verdict='REQUEST_CHANGES',root_actual_closed_ref=pin(O/'root-actual-evidence/validation.closed.json'),failure_origin_823_ref=pin(O/'root-actual-evidence/failure-origin.823.json'),checks_ref=pin(O/'checks.json'),canonical_verification_ref=canref,report_ref=pin(O/'report.md'),manifest_path=str(O/'MF.json'),source_count=49,package_count=352,build_input_count=3726,unique_file_hashes_verified=4141,root_owned_jobs=4,root_actual_exits=[0,0,0,1],all_owned_jobs_closed=True,source_guards_closed=5,parent_scope_count=25,parent_test_node_counts={'pass':61,'fail':6,'skip':0},child_runner_scope_count=6,native_leaf_failure_count=8,public_child_evidence_count=50,Goal_observed_scope='ACCEPTED_COMPONENT_OBSERVED_ONLY',workspace_epoch_observed_scope='ACCEPTED_COMPONENT_OBSERVED_ONLY',typed_runtime_pass=False,native_pass=False,FULL_pass=False,formal_acceptance=False,Main_adopted=False,original_failure_counter_reset=False,actual_native_child_pid=None,actual_native_child_exit=None,native_child_exit_inference='Official pinned test2json exit propagation supports inferred exit 1; this is not an independently observed native child exit.',first_failure_cause='session.attach returned ACKNOWLEDGED revision3; muClientCall required COMPLETED',canonical_refs=canonical,independent_T6_pre_run_canonical_receipt_available=False,authority='NONE',STOP=True))
manifest=save('MF.json',dict(schema='researchos.independent-review-manifest.v1',members=[pin(p) for p in sorted(O.rglob('*')) if p.is_file()],exclusions=['MF.json self hash','seal-tool-io.json added after seal'],formal_acceptance=False))
for ref in read(O/'MF.json')['members']:verify(ref)
print(json.dumps(dict(HDF=hdf,MF=manifest,report=pin(O/'report.md'),verdict='FAILED_EXECUTION_CLOSED',all_manifest_members_verified=True,member_count=len(read(O/'MF.json')['members'])),ensure_ascii=False))
