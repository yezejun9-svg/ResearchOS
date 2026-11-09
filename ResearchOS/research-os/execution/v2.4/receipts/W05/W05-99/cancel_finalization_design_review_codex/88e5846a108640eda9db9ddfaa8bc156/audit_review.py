import datetime, hashlib, json, pathlib, subprocess, sys

MAIN = pathlib.Path('D:/作品集/ResearchOS/research-os')
WT = MAIN / '.local/worktrees/codex-w0599-host-configuration-upgrade'
PACKAGE = pathlib.Path('D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4')
OUT = pathlib.Path(__file__).resolve().parent
REL = OUT.relative_to(MAIN).as_posix()
PROPOSAL = 'execution/v2.4/receipts/W05/W05-99/cancel_finalization_upgrade_scope_readonly_codex/78f08cbbf58d4e21ab51c605801103d9/source_proposal.v2.json'
OLD = 'execution/v2.4/receipts/W05/W05-99/cancel_finalization_scope_readonly_codex/4e3160d75a2a444cb048798da12f567a'
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def write(name, value):
    p = OUT/name
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as f: f.write(value if isinstance(value, bytes) else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
    return {'path':p.relative_to(MAIN).as_posix(),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
def ref(name):
    p=OUT/name
    return {'path':p.relative_to(MAIN).as_posix(),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
calls=[]
def git(root, *args):
    argv=['git','-C',str(root),*args]; start=now()
    p=subprocess.run(argv,capture_output=True)
    i=len(calls); so=write(f'raw/git-{i}.stdout',p.stdout); se=write(f'raw/git-{i}.stderr',p.stderr)
    calls.append({'actualargv':argv,'cwd':str(MAIN),'started_at':start,'ended_at':now(),'exit':p.returncode,'stdout_ref':so,'stderr_ref':se})
    if p.returncode: raise RuntimeError(argv)
    return p.stdout
started=now()
heads={'main':git(MAIN,'rev-parse','HEAD').decode().strip(),'candidate23':git(WT,'rev-parse','HEAD').decode().strip()}
git(MAIN,'status','--short','--untracked-files=no')
git(WT,'status','--short','--untracked-files=no')
proposal_bytes=(MAIN/PROPOSAL).read_bytes()
assert sha(proposal_bytes)=='a7e2055def8bded4bdb28230f4d52031c8dd987bf4587522792b2ec6aa580ba8'
proposal=json.loads(proposal_bytes)
main_files=['AGENTS.md','execution/project_identity.json',PROPOSAL,
 OLD+'/source_proposal.json',OLD+'/foundation-blob-4.stdout.raw',OLD+'/foundation-blob-5.stdout.raw',OLD+'/foundation-blob-6.stdout.raw',OLD+'/historical-original-invocation.stdout.raw',
 'execution/v2.4/receipts/W05/W05-99/host_configuration_foundation_source_review_codex/c4ca3130-f842-454f-96d9-39df9ea53644/source_review.json',
 'internal/domain/client_protocol.go','internal/domain/client_protocol_queue_control.go','internal/domain/client_command_queue.go','internal/domain/client_protocol_control_windows_test.go',
 'internal/domain/backup_command_queue.go','internal/domain/runtime_command_queue_windows.go','internal/domain/runtime_model_stream_windows.go','internal/domain/runtime_dispatch.go','internal/domain/runtime.go','internal/domain/durability.go','internal/domain/operations.go',
 'internal/domain/backup_recovery.go','internal/domain/backup_queue_upgrade.go','internal/store/sqlite.go','migrations/sqlite/0002_domain.sql','migrations/sqlite/0011_resources.sql','migrations/sqlite/0017_runtime_dispatch.sql','migrations/sqlite/0022_client_command_queue.sql',
 'internal/api/contracts/client.protocol.schema.json','internal/api/contracts/domain.schema.json','go.mod','go.sum']
candidate_files=['internal/domain/backup_upgrade.go','internal/domain/backup_migration.go','internal/domain/backup.go','internal/domain/store.go','internal/domain/backup_configuration_upgrade.go','internal/domain/backup_configuration_upgrade_test.go','internal/domain/backup_host_configuration.go','internal/domain/backup_host_configuration_test.go','internal/domain/client_configuration.go','internal/domain/client_configuration_test.go','internal/domain/client_command_identity.go','internal/domain/client_command_identity_test.go','internal/domain/backup_command_queue_test.go','migrations/sqlite/0023_host_model_configuration.sql']
package_files=['22_CLIENT_INTERFACE_DETAILS.md','06_ACCEPTANCE_TESTS.md','tasks/steps/W05-99.md','contracts/client.protocol.schema.json']
entries=[]
for label,root,paths in [('main',MAIN,main_files),('candidate23',WT,candidate_files),('frozen_package',PACKAGE,package_files)]:
    for name in paths:
        p=root/name; raw=p.read_bytes(); snapshot=write('snapshots/'+label+'/'+name,raw)
        entries.append({'group':label,'path':name,'original_absolute_path':str(p),'sha256':sha(raw),'bytes':len(raw),'snapshot_ref':snapshot})
before=write('input.before.json',{'schema':'researchos.readonly.input-vector.v1','captured_at':now(),'heads':heads,'entries':entries,'timing':'Captured after exploratory read-only tool calls; this vector covers sealed reread and report assembly, not earlier reads.'})
index={(x['group'],x['path']):x for x in entries}
def evidence(group,path,lines=None,pointer=None):
    r=dict(index[group,path]['snapshot_ref'])
    r['locator']={'lines':lines} if lines else {'json_pointer':pointer or ''}
    return r
def main(path,lines): return evidence('main',path,lines)
def candidate(path,lines): return evidence('candidate23',path,lines)
def prop(pointer): return evidence('main',PROPOSAL,pointer=pointer)
blob_rows=[]
for path in candidate_files:
    b=git(WT,'show',heads['candidate23']+':'+path)
    row={'path':path,'commit':heads['candidate23'],'git_blob_sha256':sha(b),'actual_file_sha256':index['candidate23',path]['sha256']}
    row['equal']=row['git_blob_sha256']==row['actual_file_sha256']; blob_rows.append(row)
    assert row['equal']
write('candidate23.git-blobs.json',blob_rows)
new_path_truth=[{'path':p['path'],'exists_main':(MAIN/p['path']).exists(),'exists_candidate23':(WT/p['path']).exists()} for p in proposal['proposed_core8']+proposal['proposed_upgrade6_after_accepted23'] if p['new']]
write('proposed_new_paths.actual.json',new_path_truth)
sqlite=MAIN/'.local/gopath/pkg/mod/modernc.org/sqlite@v1.60.1/lib/sqlite_windows.go'
sqlraw=sqlite.read_bytes(); lines=sqlraw.decode().splitlines()
sqlite_ref=write('sqlite-replace-primary-source.txt',('\n'.join(f'{i+1}: {lines[i]}' for i in range(81970,82010))+'\n').encode())
write('sqlite-primary-source.identity.json',{'path':str(sqlite),'sha256':sha(sqlraw),'bytes':len(sqlraw),'excerpt_ref':sqlite_ref,'interpretation':'The pinned engine conditions REPLACE delete-trigger lookup on SQLITE_RecTriggers; product Open does not explicitly set recursive_triggers. This is static source evidence, no SQLite control was executed here.'})
findings=[]
def finding(id,severity,title,scope,actual,required,refs):
    findings.append({'id':id,'severity':severity,'title':title,'assessment_scope':scope,'observed_fact_or_inference':actual,'required_revision':required,'evidence_refs':refs,'product_test_executed':False})
finding('D01','BLOCKING_DESIGN','ADMITTED 必须覆盖初始 Execute 提交链，当前路径函数边界不足','Independent assessment of Cmd new admission witness; old Execute facts only',
 'v2 仅许可 Execute 的既有 ACK replay 分支；实际初始路径先 dispatch（其中已修改 Goal/Task/fence、尝试立即完成），之后验证响应、保留 original_response、插入原 idempotency。仅改 replay 无法在取消前冻结成员且把 ADMITTED 与真实原响应同事务绑定。',
 ['同一 client_protocol.go 路径补充初次 session.control CANCEL 的 dispatch/canonical-response/original-journal insertion 边界；保留所有其他方法和 savepoint rejection 语义。',
  'cancelClientTarget 在任何 Goal/Task/queue 修改前读取并冻结完整、排序去重的成员与 Task/Run/session/generation/epoch/dispatch 身份；不得在 finalizer 才重建。',
  '明确临时准入快照、原 canonical response 和 journal 插入、ADMITTED INSERT 的确切顺序。ADMITTED INSERT 需现存 journal 时应在其后执行但仍在同一 caller transaction 内；不可先要求不存在的 ACK。',
  '单独定义新24 immediate COMPLETED 原始 INSERT 顺序及 proof；不制造 ACK，不借 legacy exception 绕过准入。最终转移在同事务完成全量再验证、FINALIZED、control 单赋值和 old-body CAS，RowsAffected=1；任一失败全部回滚。'],
 [prop('/proposed_core8/1'),prop('/recommended_witness_protocol/phase'),main('internal/domain/client_protocol.go',[703,808]),main('internal/domain/client_protocol_queue_control.go',[112,213])])
finding('D02','BLOCKING_DESIGN','Run 已建立但尚无 dispatch 的真实分支未定义','Independent four-variant coverage assessment',
 'createRuntimeRun 先创建 QUEUED Run 并写 Task.active_run_id，函数本身不创建 runtime_dispatches。v2 的 UNQUEUED_RUN 要求实际 dispatch；NO_RUN 又要求零原始 Run。已领取尚未启动的 Run 不能伪造成 noRun 或虚构 dispatch。',
 ['保留四大类也可，但补 dispatch stage 的严格子形状：未提交 dispatch、PREPARED/未启动、真实启动、已终结。每类证明真实无子进程/未发送或匹配原 process/SDK settlement。',
  '如果既有事实不足，明确该分支维持 ACK/RECONCILING 并报告功能缺口；若完整 F08 要求此分支完成，先提出准确 producer path 扩围，不以标签或空字段补证。',
  '准入时记录真实已有 generation 与取消过程中新建 fence 的因果关系。无 Task client-session 的分支不得调用 ensureClientQueue 造 generation；缺 fence 不是 queue_empty 证据。'],
 [prop('/recommended_witness_protocol/null_semantics'),main('internal/domain/runtime.go',[41,65]),main('internal/domain/client_protocol_queue_control.go',[44,108]),main('internal/domain/client_command_queue.go',[146,161])])
finding('D03','BLOCKING_DESIGN','完整成员及原始身份需要可重算的准入锚点定义','Independent new typed witness assessment',
 'typed_columns 允许 canonical_body 承载其余字段，但未指定 session/client/writer epoch/accepted watermark/Goal version 及完整 request、原始响应的精确绑定。普通 Task/Run 存在和相近时间不证明其属于该次 CANCEL；old23 control.task_ids 当时并无不可变保护。',
 ['指定每一字段、类型、null 条件、版本化对象引用和摘要算法，以及 complete Goal membership 与原 command 的同事务来源。完整成员集需独立校验，不只每条 witness 相互同意同一个 hash。',
  '明确现有 client_command_identities 全 envelope identity 与 journal locator/request_hash 的对应；跨 principal/project/session/client/target/epoch 的复制应拒绝。',
  'old23 不迁移填充 ADMITTED。列出能唯一恢复原 membership 的具体 immutable joins；缺失或多个匹配维持原 ACK/RECONCILING。新24准入不能被伪标为 legacy。'],
 [prop('/recommended_witness_protocol/typed_columns'),prop('/recommended_witness_protocol/historical_snapshots'),main('internal/domain/client_protocol_queue_control.go',[112,213]),candidate('migrations/sqlite/0023_host_model_configuration.sql',[1,120])])
finding('D04','BLOCKING_DESIGN','更新不可变不等于删除、替换或伪造不可行','Independent assessment of new SQL24 witness threat boundary; old guard facts only',
 '0002 idempotency_immutable 仅拒绝 UPDATE；domain_objects immutable 也只是 UPDATE，不能笼统称所有 canonical facts 不可删除。原 queue receipt 与 resource_effects 有 UPDATE/DELETE 保护但没有 host-authenticated INSERT。SQLite REPLACE 的 DELETE trigger 路径受 recursive_triggers 影响，产品 Open 未固定该开关。',
 ['SQL24 为所保护 CANCEL journal/control/witness 明确 DELETE 与所有主键/唯一键冲突 INSERT guards；INSERT OR REPLACE/UPSERT/REPLACE 不依赖递归触发器偶然开启。所有 unrelated generic1811 UPDATE 继续拒绝。',
  '分别列出触发器保护、Go语义校验、备份认证与可信 host producer 的保证，不能把同库 hash 或 FK 称为 host attestation。',
  '负例至少覆盖只伪造 witness/control、复制另一真实 command 的 proof、错 process/epoch、最新 UNKNOWN effects，以及修改或删除原 anchor。只更改封闭可变部分而保留 authentic anchors 的攻击必须拒绝。',
  '完整复制一个合法备份本身应可合法恢复；如果要求拒绝攻击者任意重写所有 canonical rows 后重算全库 hash，当前14路径没有外部信任锚，不能承诺 tamperproof。要求该更强威胁模型时另行准确 scope/resource 决策。'],
 [main('migrations/sqlite/0002_domain.sql',[1,70]),main('migrations/sqlite/0011_resources.sql',[1,150]),main('migrations/sqlite/0022_client_command_queue.sql',[1,180]),main('internal/store/sqlite.go',[1,95]),sqlite_ref,prop('/limits')])
finding('D05','BLOCKING_DESIGN','SQL 原始更新门与完整 typed Go 校验的职责尚未落地','Independent new raw-SQL refusal design',
 'v2 同时要求 raw SQL 不能伪造完成和完整 frozen CommandResponse 校验。只在 Go helper 验证再插入任意可伪造标志/hash，不能让绕过 helper 的 raw SQL 自动具备同等约束。SQL NULL/重复 JSON key/非canonical body 也不能仅靠 json_extract 部分字段保证。',
 ['提交明确 predicate map：哪些由 SQL INSERT/UPDATE guards 直接重算（原 body、nullable locator/status/headers、身份、完整 witness group、最新 effect/queue/Run 锚点），哪些由 Go frozen schema validator 拒绝。',
  '如果完整门需要 host-only connection function 或新的外部 authority，先报确切 additional path/resource，不能私自扩大 internal/store 或用 ready boolean。',
  '固定允许只改 body 的一次 ACK->COMPLETED；相同 final/noop、ACK->ACK、反向和非 CANCEL 保持1811。SQL完整response identity 与 Go fulltyped结果均须真实 negative controls。'],
 [prop('/sql24_constraints'),prop('/additional_raw_SQL_controls'),main('internal/domain/client_protocol.go',[703,808])])
finding('D06','BLOCKING_DESIGN','历史 FINALIZED 校验必须与恢复后的当前栅栏分开','Independent new witness/backup integration',
 'nativeDispatchProof 读取 dispatch 当前 state/observation_hash；backup 恢复会改变当前 Run、队列、Session、control pending state。原 backup 控制成员还按当前 Task.active_run_id 做 Run 匹配。历史终结若复用这些当前判断会误拒合法历史，若跳过又会接受伪造。',
 ['指定 frozen Run revision、observation artifact bytes/hash、不可变 dispatch identity/manifest、原 queue receipt chain及原 latest resource-effect sequence/hash；清楚区分历史 final proof 与当前 restore fence。',
  '仍须真实 clear/drop、abort_observed、cancelled idle、children/process cleanup 同 generation/Run/epoch；任何 latest STARTED/UNKNOWN 不得 final。不能用 nullable generation 或无 fence 的 count=0 当证据。',
  'backupQueueState 仅 schema24 增 witness inventory；旧22/23四表形状与 digest 不变，不能直接把新表无条件塞进 clientQueueTables。source23 backup 不要求24表。',
  'backup_command_queue 的旧 current-head membership 条件，仅对已验证新 witness 的确切历史分支替换；legacy/model-stream/queue图校验保持。restore 不产生 FINALIZED 或任意补 ADMITTED，已有 final 全字节保留。'],
 [main('internal/domain/runtime_dispatch.go',[184,194]),main('internal/domain/backup_command_queue.go',[1,200]),main('internal/domain/runtime_model_stream_windows.go',[1,48]),main('internal/domain/durability.go',[1,70]),prop('/quiescence_requirements')])
finding('D07','BLOCKING_SCOPE','完整当前回归至少需要另外3个窄测试路径','Independent upgrade6 applicability assessment; own23 code used only as facts',
 'candidate23 的 fresh queue 测试严格读取当前根23 release，configurationMigrationFiles 要求整个实际 SQL 清单23，foundation actual_Service_New 断言23。新增 SQL24 后这三处与实际当前24矛盾。静态发现，未执行新失败，不计新产品 failure。',
 ['另行登记 internal/domain/backup_command_queue_test.go 的 TestClientQueueFreshNumberedSchema：当前24来源于确切已安装清单；固定历史22测试及所有 emptyqueue/0022 checks不变。',
  '另行登记 internal/domain/backup_configuration_upgrade_test.go 的 configurationMigrationFiles 及受影响调用：保留真正冻结23 target fixtures与23安全断言，新增current24在新F08 tests；不能把 release23 guard 放宽为任意未来版本。',
  '另行登记 foundation internal/domain/client_configuration_test.go 仅 actual_Service_New current分支：真实fresh24清单及完整冻结1..23 identity；其它 explicit numbered22->23 和旧字节 guards保留。',
  '最终若要求正常 current suite，无改旧测试的14path方案不足；建议17path精确scope（14+这3测试），由非作者reviewer决定边界，Root登记后才可写。'],
 [candidate('internal/domain/backup_command_queue_test.go',[118,177]),candidate('internal/domain/backup_configuration_upgrade_test.go',[19,27]),candidate('internal/domain/client_configuration_test.go',[222,280]),prop('/discovery/not_needed_to_modify_now'),prop('/controls/14')])
finding('D08','REQUIRED_CLARIFICATION','U13 必须验证旧 writer 拒绝，而非声称所有 WAL 读取都拒绝','Independent upgrade6 control correctness',
 'U13 写 read/write 均 denied/busy；WAL BEGIN EXCLUSIVE 不保证其它读连接被阻断，产品 Open 已选择 WAL。读成功不意味着独占写锁失败。',
 ['用接受且源码/编译输入绑定的真实 old23 program 执行匹配23访问；记录实际 read 结果，写必须在 snapshot 至 publication 整个持锁阶段拒绝或忙。不可新24 exe内直接旧SQL helper冒充oldprogram。',
  '记录锁释放可重开旧原库、future24 guard在真正old23程序中拒绝24、显式单writer切换。不得声称永久fence或零WAL文件写。',
  'source+binary identity由真实 build/input vector/release hashes外部绑定，当前exe没有自证Gitcommit协议；稳定但错来源binary的可判别边界要如实标出。'],
 [prop('/controls/12'),main('internal/store/sqlite.go',[1,95]),candidate('internal/domain/backup_configuration_upgrade.go',[180,345])])
finding('D09','REQUIRED_CLARIFICATION','23→24 升级不能继承未接受或过期23输入','Independent upgrade6 readiness',
 'v2 的 MAIN1c7和candidate5a076+未提交来源早于本次实际 MAIN/candidate c82f 观察。新路径0实现；23 prerequisites 的测试不等于 F08 接受。',
 ['先非作者完整复核并整合 accepted23/foundation；更新 exact source/program/schema/SQL/root binding，依次使用真实 source23 backup、目标24孤立schema-only迁移、完整 typed inventory、恢复前后精确合法变化。',
  'host-only非空、future/gap/malformed schema要在domainDDL之前拒绝；保持Open/Bootstrap此前可能写文件的事实。',
  'rollback在publication之前不发布target且保留认证snapshot、原源不变；publication之后有新effects不能盲回滚旧23。23→24不得复用22→23空新三表不变量。'],
 [prop('/observed_candidate23_head'),prop('/controls'),candidate('internal/domain/backup_migration.go',[14,149]),candidate('internal/domain/backup_host_configuration.go',[75,260]),candidate('internal/domain/backup.go',[264,287])])
finding('D10','REQUIRED_CLARIFICATION','client_protocol.go 配置与F08必须串行拥有且重新绑定完整请求','Independent coordination recommendation, not ownership registration',
 '未来 configuration handler/global command identity 与 F08 都会修改 Execute/dispatch。现有 foundation 提供 identity helpers，但不能把 helper存在当实际 API已接线。',
 ['建议先 accepted23 prerequisites，再单一配置handler owner完成Execute完整Envelope identity/reservation与host.configure事务；独立冻结后移交F08 owner。',
  'F08从最终main基线rebase并重新审查D01 initial+replay函数边界，保留配置guard、真实writer epoch/principal以及所有其它方法。若Root决定先F08则相反顺序也须独占 lease及后续完整再审；不并行写同文件。',
  'F08 core+upgrade同一串行集成单元，SQL24不能先于validator/backup/upgrade单独进入MAIN；独立全14/17审查由非旧core作者承担。'],
 [main('internal/domain/client_protocol.go',[703,820]),candidate('internal/domain/client_command_identity.go',[1,150]),prop('/serial_sequence')])
gate_dispositions={
 'U01':['DESIGN_CONDITIONALLY_SOUND',['D09','D08']], 'U02':['DESIGN_CONDITIONALLY_SOUND',['D08','D09']],
 'U03':['DESIGN_SOUND_NOT_EXECUTED',['D03','D09']], 'U04':['DESIGN_CONDITIONALLY_SOUND',['D07','D09']],
 'U05':['REVISION_REQUIRED',['D01','D03','D05']], 'U06':['REVISION_REQUIRED',['D04','D05']],
 'U07':['REVISION_REQUIRED',['D01','D05']], 'U08':['REVISION_REQUIRED',['D02','D03','D06']],
 'U09':['REVISION_REQUIRED',['D02']], 'U10':['REVISION_REQUIRED',['D06']],
 'U11':['REVISION_REQUIRED',['D03','D04','D05','D06']], 'U12':['DESIGN_CONDITIONALLY_SOUND',['D06','D09']],
 'U13':['WORDING_AND_CONTROL_REVISION_REQUIRED',['D08']], 'U14':['DESIGN_SOUND_NOT_EXECUTED',['D09']],
 'U15':['SCOPE_REVISION_REQUIRED',['D07','D10']], 'U16':['DESIGN_SOUND_NOT_EXECUTED',[]]}
review={
 'schema':'researchos.cancel-finalization.independent-design-review.v1','status':'DESIGN_REVISION_REQUIRED_NEW_WITNESS_AND_UPGRADE_SCOPE','reviewer_id':'codex:/root/sources_parent_impl','model':'gpt-6-astra','reasoning_effort':'high','reason':'architecture and transaction/integrity design review',
 'independence':{'independent_scope':'Only Cmd-authored new typed ADMITTED/FINALIZED witness protocol, four binding variants, and upgrade6 design additions','excluded_from_independent_certification':'Reviewer authored historical core8 proposal and configuration23 implementation. Those sources are factual audit inputs only. No overall independent SOURCE_READY; nonauthor full14/17 review remains required.','parent_confirmed_limit':True},
 'input_proposal_ref':evidence('main',PROPOSAL),'source_input_ref':before,'actual_heads':heads,'findings':findings,
 'gate_rows':[{'id':x['id'],'subject':x['subject'],'design_disposition':gate_dispositions[x['id']][0],'finding_ids':gate_dispositions[x['id']][1],'executed_here':False,'product_pass_claim':False} for x in proposal['controls']],
 'supported_design_properties':['One append-only typed table addresses legitimate no-generation witnesses without weakening old receipt graph. Table/shape remains a proposal requiring registration.','Original idempotency body stays sole public replay authority; ACK->COMPLETED is body-only once, byte/null-safe other columns preserved.','No old23 ADMITTED migration synthesis; ambiguous historical ACK remains unresolved.','No generation/Run/effect invented; no budget settlement or UNKNOWN-to-confirmed promotion by cancellation.','Dedicated23->24 release/migration/rollback path protects earlier SQL and queue/configuration contracts.'],
 'minimum_scope_decision':{'proposed_product_and_test_paths_14':[x['path'] for x in proposal['proposed_core8']+proposal['proposed_upgrade6_after_accepted23']], 'necessary_additional_test_paths_3':['internal/domain/backup_command_queue_test.go','internal/domain/backup_configuration_upgrade_test.go','internal/domain/client_configuration_test.go'],'necessary_same_path_boundary_amendments':['client_protocol.go: Execute initial CANCEL dispatch-to-journal commit plus existing replay CAS','client_protocol_queue_control.go: pre-mutation admission capture and immediate/final paths; fenceClientTask only if exact initial generation semantics need changes'], 'conditional_additional_paths':'None authorized or automatically proposed. If canonical producer anchors/full SQL guard cannot meet D02-D06, submit concrete missing callsite/amendment; do not weaken gate.'},
 'historical_failure_handling':{'original_1811_refs':[evidence('main',OLD+'/foundation-blob-4.stdout.raw'),evidence('main',OLD+'/foundation-blob-5.stdout.raw'),evidence('main',OLD+'/foundation-blob-6.stdout.raw'),evidence('main',OLD+'/historical-original-invocation.stdout.raw')],'interpretation':'Historical direct UPDATE body=body expected-refusal control, not a new end-to-end CANCEL execution. Original issue and counters unchanged.','new_product_failures_executed':0,'test_counts':{'executed':0,'pass':0,'fail':0,'skip':0},'legacy_14_ActiveRecovery':'Remains open outside this design; no inherited acceptance.'},
 'limitations':['Static source/design review only; no product/SQL/HTTP/worker/provider execution, no private DB/holdout/credential reads.','Current candidate23 Git blobs verified; candidate23 acceptance not supplied by this reviewer.','All proposed raw-SQL attacks are future required controls, not claimed executed here.','No tamperproof claim against unrestricted replacement of all canonical evidence; distinguish authenticated backup origin from consistency hashes.'],
 'mutations':{'owned_new_receipts_only':True,'product_source':0,'sql24':0,'canonical_registry_state':0,'configuration_worktree':0,'paid_calls':0,'formal_increment':0}}
write('source_review.json',review)
write('exploratory_read_diagnostics.json',{'errors_are_tool_discovery_not_product_failures':True,'tool_chunk_ids':['950db5','f5dd23','f6b3db','5e1ad7','0e219e'],'description':'Earlier read-only discovery attempted nonexistent guessed schema/source paths; actual paths were resolved and captured. No original tool output reconstructed or overwritten. These IDs reference conversation tool chunks, not filesystem raw evidence.','clarification':'operations.go active_run_id=nil belongs to new Task construction, not proven reset of existing Task; no existing-Task-reset finding is made.'})
after_entries=[]
for x in entries:
    raw=pathlib.Path(x['original_absolute_path']).read_bytes()
    after_entries.append({'group':x['group'],'path':x['path'],'sha256':sha(raw),'same_as_before':sha(raw)==x['sha256']})
after=write('input.after.json',{'captured_at':now(),'entries':after_entries,'drift_count':sum(not x['same_as_before'] for x in after_entries)})
assert all(x['same_as_before'] for x in after_entries)
git(WT,'status','--short','--untracked-files=no')
git(MAIN,'rev-parse','HEAD')
write('actual_invocations.json',{'read_only_git_invocations':calls,'collector':{'actualargv':[sys.executable,*sys.orig_argv[1:]],'cwd':str(pathlib.Path.cwd()),'started_at':started,'ended_at':now(),'execution_kind':'PUBLIC_FILES_READ_AND_OWN_RECEIPTS_WRITE_ONLY'},'file_reads_are_exact_paths_in_input_before':True})
write('handoff.json',{'schema':'researchos.readonly-review.handoff.v1','status':review['status'],'reviewer_id':review['reviewer_id'],'independence':review['independence'],'review_ref':ref('source_review.json'),'before_ref':before,'after_ref':after,'invocations_ref':ref('actual_invocations.json'),'candidate23_git_blobs_ref':ref('candidate23.git-blobs.json'),'source_drift_count':0,'requires_root_decision':['Revise D01-D06 witness/transaction/threat/restore details','Approve additional3 exact test paths and boundaries or explicitly leave current regression scope blocked','Correct U13 WAL reader wording','Assign nonauthor full14/17 independent scope review then Root registration'],'overall_source_ready':False,'product_acceptance':False,'formal_increment':0})
files=[{'path':p.relative_to(MAIN).as_posix(),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in sorted(OUT.rglob('*')) if p.is_file()]
manifest=write('manifest.json',{'schema':'researchos.receipt-manifest.v1','namespace':REL,'files':files,'excludes_self':True})
print(json.dumps({'namespace':REL,'review':ref('source_review.json'),'handoff':ref('handoff.json'),'manifest':manifest,'input_count':len(entries),'drift_count':0,'heads':heads},ensure_ascii=False))
