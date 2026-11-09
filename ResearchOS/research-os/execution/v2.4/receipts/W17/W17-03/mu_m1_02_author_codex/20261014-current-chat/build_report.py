import hashlib, json, pathlib, re, subprocess
from datetime import datetime, timezone

root=pathlib.Path.cwd()
out=root/'.local/m1-02'
scope_path=pathlib.Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261014-current-chat/continuation-cp473/mu-m1-02-source-scope-v4.json')
scope=json.loads(scope_path.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def item(p):return {'path':str(p.resolve()),'sha256':sha(p),'bytes':p.stat().st_size}
def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
def write(name,obj):
    p=out/name
    p.write_bytes((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
    return item(p)
assert sha(scope_path)=='a3717a29e1b236e790cc5d639adf2603ddb0935c8307164f2fc2af9654b1e1f5'
assert git('status','--porcelain')==''
paths=git('diff-tree','--no-commit-id','--name-only','-r','HEAD').splitlines()
assert set(paths)==set(scope['paths']) and len(paths)==17
dependencies=[]
for dep in scope['dependency_source9']:
    p=root/dep['path'];assert sha(p)==dep['sha256']
    dependencies.append(item(p))
source=[dict(item(root/p),repo_path=p) for p in paths]
patch=out/'source.patch'
patch.write_bytes(subprocess.check_output(['git','diff','--binary',scope['base_commit'],'HEAD','--',*paths]))
manifest=write('source-manifest.json',{'schema':'researchos.mu-m1-02-source-manifest/1','scope':item(scope_path),'base_commit':scope['base_commit'],'commit':git('rev-parse','HEAD'),'tree':git('rev-parse','HEAD^{tree}'),'exact_source_count':17,'sources':source,'frozen_dependencies_unchanged':dependencies,'patch':item(patch)})
meaning={
1:'Compile only, before new tests existed; zero tests, not test proof.',
2:'Initial portable pause CAS/current authority/effect cutoff tests.',
3:'Independent verifier executable built from isolated composition.',
4:'Native attempt reached confirmed pause; general supports_resume gate rejected successor.',
5:'One unstarted fixture failure: placeholder immutable manifest hash rejected.',
6:'Native confirmed pause, old journal recovery twice, actual HTTP cancellation dominates.',
7:'Fixture correction attempted immutable manifest UPDATE; storage trigger rejected setup for all 13 subcases.',
8:'Correct fresh immutable-manifest fixture; pause tests pass.',
9:'Required activation proof passed; ordinary Task graph rejected BLOCKED to RUNNING; transaction rolled back.',
10:'Pause and ordinary control/cancel/context-resume regression set.',
11:'First complete real Host/API/SDK/AppContainer same-Run epoch 1 to 2 restore.',
12:'Build failure only: test referred to nonexistent PausedSequence; corrected to Paused and exact final frame.',
13:'Native activation rollback and loss of volatile prepared lease; same epoch replacement, no extra activation/carry.',
14:'Pause, state graph, ordinary controls, storage25 and command queue backup regressions.',
15:'Legacy/native coordinator regressions: two old inline checkpoint cases fail; unrelated controller/effect recovery pass.',
16:'Frozen M1-01 baseline c6f39e84: independently reproduces old inline checkpoint rejection.',
17:'Final exact-source native three-case suite: resume, cancel, prepared lease recovery; all pass.',
18:'Final exact-source pause tests and actual pinned Mu SDK queue/cancel/Goal ordering regressions; all pass.'}
fail={4,5,7,9,12,15,16}
attempts=[]
for p in sorted(out.glob('attempt-*.log')):
    n=int(p.name.split('-')[1]);text=p.read_text(encoding='utf-8-sig')
    statuses=re.findall(r'^--- (PASS|FAIL|SKIP): (\S+)',text,re.M)
    attempts.append(dict(item(p),attempt=n,exit_code=1 if n in fail else 0,classification='BUILD_FAILURE' if n==12 else 'COMPILE_ONLY' if n in (1,3) else 'TEST_FAILURE' if n in fail else 'TEST_PASS',top_level_pass=sum(s=='PASS' for s,_ in statuses),top_level_fail=sum(s=='FAIL' for s,_ in statuses),top_level_skip=sum(s=='SKIP' for s,_ in statuses),top_level_tests=[{'name':name,'status':status} for status,name in statuses],meaning=meaning[n]))
ledger=write('attempt-ledger.json',{'schema':'researchos.mu-m1-02-attempt-ledger/1','append_only_raw_logs':True,'attempt_count':18,'failed_invocations':7,'build_failed_invocations':1,'test_failed_invocations':6,'historical_failures_preserved':True,'attempts':attempts})
evidence_root=pathlib.Path('D:/作品集/ResearchOS/research-os/.local/mu-m1-core-20261014/native-attempt-017')
evidence=[item(p) for p in sorted(evidence_root.rglob('*.json'))]
assert len(evidence)==5
results={}
for p in evidence_root.rglob('canonical-evidence.json'):
    o=json.loads(p.read_bytes());assert o['live_model_calls']==0 and o['formal_increment']==0
    results[p.parent.name]={'synthetic_model_calls':o['synthetic_model_calls'],'actual_host_tool_calls':o['actual_host_tool_calls'],'activation_rollback_proven':o.get('activation_rollback_proven'), 'prepared_lease_recovery':o.get('prepared_lease_recovery'),'commands_consumed_once':o.get('commands_consumed_once'),'pause_state':o.get('pause_state'),'queue_fence':o.get('queue_fence')}
report={
 'schema':'researchos.mu-m1-02-author-report/1','at':datetime.now(timezone.utc).isoformat(),
 'status':'AUTHOR_IMPLEMENTED_REQUIRES_INDEPENDENT_REVIEW','commit':git('rev-parse','HEAD'),'tree':git('rev-parse','HEAD^{tree}'),'worktree':str(root),'source_manifest':manifest,'attempt_ledger':ledger,
 'authorization':'CP466 exact15, CP469 effect cut exact16, sealed activation architecture addendum, CP473 exact17 Task lifecycle hook',
 'exact_source_count':17,'frozen_M1_01_source_unchanged':True,'frozen_schema25_source9_unchanged':True,
 'scope':'Isolated fresh schema25 + accepted M1 assets + synthetic model real Host/API/coordinator/AppContainer; no production DB/API/provider/GUI or normal Main/package mutation.',
 'proof_class':'NATIVE_SYNTHETIC plus SOURCE/FIXTURE regression evidence','native_results':results,'native_evidence':evidence,
 'covered':['HTTP current Owner and resume requester revocation; exact idempotent pause replay and changed hash rejection','effect cut: only old prepared admission may begin once; no new effects after pause','bounded trusted checkpoint bytes, durable Artifact/use then typed ACK once, actual stopped/drained/cleaned process','same Run epoch plus one; original SDK session/header/lease binding restored, attempt unchanged; no original prompt or tool replay','CONSUMED 1 / SDK_ACCEPTED 2 / ENQUEUED 1 at pause, exactly four eventual consumption receipts','atomic activation/carry/epoch/fence rollback under injected failure','prepared committed but unstarted activation: simulated volatile lease loss through last-write actor revocation, no process or journal; current proof rechecked, same epoch new lease, one activation/carry','STARTED/worker/identity/journal/cancel/restored/foreign-fence cannot use prepared restart path','actual HTTP cancellation after native pause dominates later resume; old terminal journal recovery twice does not renew execution','general supports_resume false path unchanged; generic blocked Task cannot jump to RUNNING','root schema25 backup validator accepts Core full-row witness; storage25 and command queue backup regressions'],
 'limitations':['No real model/provider qualification or formal case acceptance.','Prepared loss test is a post-commit before-launch refusal/lost in-memory lease injection, not an operating-system crash of the whole application. STARTED ambiguity is fixture refusal coverage.','Two legacy inline checkpoint regressions remain in frozen M1-01 Bridge; author did not modify dependency or stale tests.','No production schema24-to25 migration, normal Main package integration, UI pause controls, or GUI acceptance.','SENDING/UNKNOWN at checkpoint validation are conservatively blocked unless original receipt recovery has already established canonical state; no blind queue replay.'],
 'known_baseline_debt':item(out/'legacy-checkpoint-compatibility.md'),'independent_implementation_review':'PENDING','formal_increment':0,'formal_accepted_cases':0,'parent_tasks_complete':False,'live_model_calls':0,
 'freeze':'Source commit and raw logs frozen; Root is sole integrator. No self-acceptance.'}
report_item=write('report.json',report)
summary=f'''# M1-02 作者交付，等待独立实现复核

隔离组合已实现 canonical PAUSE、durable checkpoint seal、同一 Run 的原生 SDK 续跑和队列恢复。源码冻结为 `{report['commit']}`，tree `{report['tree']}`，精确 17 文件；schema25 的 9 个依赖和 M1-01 未改。Root 是唯一集成者。本报告不是独立接受，正式增量 0。

最终真实 Host / HTTP / coordinator / AppContainer 三用例全部通过（attempt-017，51.035s）：暂停后续跑、暂停后取消、提交后的 PREPARED lease 丢失恢复。续跑保持 Run id 和 attempt，epoch 1→2，原生 stop/drain/cleanup 成立，typed seal ACK 后恰有一个 turn.paused；实际 Host write 仅一次。暂停队列 CONSUMED/SDK_ACCEPTED/ENQUEUED 为 1/2/1，最终四条各消费一次。模型为本地 synthetic；两条续跑用例各 6 次模型调用（含资格 1 次），取消用例 3 次，无真实 provider 调用。

事务回滚用例在 activation INSERT 注入失败，证明 epoch/activation/carry 全部回滚。prepared 恢复用例在最后 Task 写入撤销 requester，让新进程启动前拒绝并失去内存 lease；重新确认当前权限后，在同一个 epoch=2 更换 lease，activation/carry 仍各一条。这是提交后未启动故障注入，不宣传为整应用 OS crash。STARTED、worker/identity/journal 已存在及取消/restore/foreign fence 的禁止重启另有边界夹具。

最终 domain pause + 真实 pinned Mu queue/cancel/Goal 排序回归通过（attempt-018，33.295s）；此前 ordinary controls、checkpoint rebuild、schema25、队列备份回归通过（attempt-014，21.320s）。所有 18 次执行日志完整保留；7 次失败调用中含 1 次编译失败、6 次测试失败，详见 attempt-ledger。没有删除失败或重置计数。

旧 coordinator 回归中两项未通过：`TestRuntimeCoordinatorCheckpointResume`、`TestRuntimeCoordinatorCheckpointCrashRecovery`。根因为冻结 M1-01 对旧 inline checkpoint 无条件采用 V1 file checkpoint；在冻结 M1-01 worktree 已直接复现第一项同样失败。其余该轮原生 qualification、typed broker、purpose revoke、heartbeat、effect crash、controller crash 回归通过。详见 legacy-checkpoint-compatibility.md；Root 已另行登记兼容债，不在本次 exact17 内修改。

实现入口：runtime_pause.go 保存当前 Owner 授权、CAS/full-row witness、effects cut 和严格 Task 生命周期例外；runtime_pause_windows.go 处理 captured bytes、seal ACK、confirmed native stop、窄 sealed activation gate、原子 successor 和无启动证据的 lease 恢复。窄 gate 重新验证初始化能力回执、原 dispatch/process/input、原 sealed bytes/use、STOPPED/typed ACK、SDK metadata、旧/新 use principal、immutable activation/request/carry、当前 session/Goal/Owner/cancel/queue。新 manifest 带必须存在 activation 的 marker；缺 schema/activation 不得退回普通执行。普通 supports_resume=false/null 与公共状态图保持原契约。

边界：未做生产 DB、API/provider、GUI 操作；未发布普通 Main/package，未执行真实 schema24 升级。SENDING/UNKNOWN 若原回执恢复仍无法确认则阻塞，不盲重发。所有成功证据为 NATIVE_SYNTHETIC 或 fixture/source，不能替代 LIVE、独立实现复核、22 父任务或 42 正式用例接受。

审查定位：`source-manifest.json`、`source.patch`、`attempt-ledger.json`、`report.json`。最终 native 证据目录：`{evidence_root}`。report.json SHA-256 `{report_item['sha256']}`。
'''
(out/'report.md').write_bytes(summary.encode())
print(json.dumps({'report_json':report_item,'report_md':item(out/'report.md'),'manifest':manifest,'ledger':ledger,'patch':item(patch),'native_evidence_count':len(evidence),'final_test_counts':{str(a['attempt']):{'pass':a['top_level_pass'],'fail':a['top_level_fail'],'skip':a['top_level_skip']} for a in attempts if a['attempt'] in (14,15,17,18)}},ensure_ascii=False,indent=2))
