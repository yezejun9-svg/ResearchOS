from review_driver import *
# Final source and evidence verification is read-only; no source edit or integration.
head=git('027-final-head',['rev-parse','HEAD']);clean=git('028-final-status',['status','--porcelain=v1']);assert head==SHA and clean==''
scope=MAIN/'execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp535/React-source14-independent-review-scope.json'
assert hashlib.sha256(scope.read_bytes()).hexdigest()=='859ea46d295cdaa1508cf85c7433b3e5383bedfb952f4ad0c1a36cad60a267f0'
scope_json=json.loads(scope.read_text());refs={}
for key in ['candidate_ref','source_scope','root_browser_evidence']:
 v=scope_json[key];p=MAIN/v['path'];actual=hashlib.sha256(p.read_bytes()).hexdigest();assert actual==v['sha256'];refs[v['path']]={'sha256':actual,'bytes':p.stat().st_size}
for rel in ['SOURCE14-SEAL.json','SOURCE14-CI-PROBE.json','CI-REFS.json','LEDGER.jsonl','LEDGER-SUPPLEMENT.json','FINAL-SOURCE14.md','FINAL.md','source14-full.patch','source14-ci.patch','browser-fixture-05/report.json','real-isolated-03/report.json',*[f'real-isolated-{i}/commands/02-core-service/stop.json' for i in ['01','02','03']]]:
 p=AUTHOR/rel;refs[str(p)]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
for i in ['01','02','03']:
 stop=json.loads((AUTHOR/f'real-isolated-{i}/commands/02-core-service/stop.json').read_text());assert type(stop['native_exit']) is int
save(E/'INPUT-REFS.json',refs)
report=json.loads((E/'browser-independent-01/report.json').read_text());real=json.loads((E/'real-isolated-01/report.json').read_text());static=json.loads((E/'STATIC-COMPARISON-FINAL.json').read_text());geom=json.loads((E/'expanded-forms-01/report.json').read_text())
assert report['status']=='PASS' and all(c['status']=='PASS' for c in report['checks']);assert real['status']=='PASS'
assert all(m['width']==m['document'] and all(not c['outOfPanel'] for c in m['controls']) for m in geom['measurements'])
dist={str(p.relative_to(WT/'apps/web/dist')).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in (WT/'apps/web/dist').rglob('*') if p.is_file()}
review=dict(schema='researchos.react-source14-independent-review.v1',reviewer=scope_json['owner'],model=scope_json['model'],reasoning_effort=scope_json['reasoning_effort'],candidate_commit=SHA,candidate_tree='de59625ee5c1d360c741c95ec3f84b6f2764bb0e',base=BASE,source_changed_paths=12,allowed_paths=14,verdict='NO_BLOCKING_FINDINGS',findings=[],recommendation='Root may perform exact local fast-forward integration after its current Main HEAD/dirty and source-allowlist preflight; reviewer did not integrate or grant formal acceptance.',formal_increment=0,source_edit_authority=False,matrix=[{'area':'source pins and static substantive review','status':'PASS','checks':len(static['checks']),'evidence':'STATIC-COMPARISON-FINAL.json'},{'area':'independent pinned web production build','status':'PASS','evidence':'commands/011-web-build'},{'area':'existing w13-react tests','status':'PASS','tests':5,'evidence':'commands/012-w13-react'},{'area':'independent Core compilation','status':'PASS_AFTER_SPARSE_INPUT_REPAIR','evidence':'commands/015-core-build'},{'area':'own preview native-shaped/browser interaction fixture','status':'PASS','checks':len(report['checks']),'evidence':'browser-independent-01/report.json'},{'area':'expanded session/coding forms','status':'PASS','widths':[320,1024,1440],'controls_observed':sum(len(m['controls']) for m in geom['measurements']),'evidence':'expanded-forms-01/report.json'},{'area':'real isolated Core SQLite Owner browser project flow','status':'PASS','checks':len(real['checks']),'evidence':'real-isolated-01/report.json'},{'area':'native packaged Desktop and real provider/model qualification','status':'NOT_RUN'},{'area':'full registered W13/formal parent-case acceptance','status':'NOT_RUN'}],build_artifact_sha256=dist,limits=['Browser bridge fixture uses real React bundle but synthetic intercepted bridge responses; not native Desktop success.','ProfileDraft/resource recovery/session-continuation and role boundaries were code-reviewed and preserved, not re-exercised as exhaustive real workflows.','Actual provider/model/worker operations and original data/processes were not touched.','The historical 571 count is an author sparse snapshot, not an acceptance threshold; own573 equals author571 plus two unchanged execution input files.'])
save(E/'REVIEW.json',review)
ledger('INITIAL_OPTIONAL_PARENT_RULE_PATH','NOT_PRESENT','D:/作品集/ResearchOS/AGENTS.md did not exist; canonical user and repository AGENTS.md were read.')
ledger('EXPECTED_REFUSAL_AND_UNKNOWN','EXPECTED','Fixture deliberately exercised explicit confirmation refusal and UNKNOWN result, proving no optimistic success and retained draft.')
ledger('OWN_SERVICE_STOP','EXPECTED_TERMINATION','Owned Core and both previews terminated and wait returned native_exit=1 on Windows; retained numeric stop receipts, not product failures.')
ledger('INDEPENDENT_REVIEW','NO_BLOCKING_FINDINGS','37 browser checks, 7 real isolated checks, 16 static comparison checks; no source edits or Main integration; formal increment zero.')
final='''# Source14 React 独立复核

结论：**未发现阻止精确本地集成的 P0/P1/P2 问题**。冻结候选 `7d1e3ff288f91254c7304dd32f6e5bb4b66b8f1e`、tree `de59625ee5c1d360c741c95ec3f84b6f2764bb0e` 与登记范围一致；14 个允许路径中实际改动 12 个。复核 worktree 最终 clean，未修改源码、Main 或其他协作者目录。建议 Root 在当前 Main HEAD/dirty/allowlist 再校验后作精确本地 fast-forward；本报告不代 Root 整合或签发正式接受，formal increment = 0。

## 实质代码判断

- `apps/web/src/main.jsx:19` 的状态、主题、设备续期、事件连接、抽屉焦点、反馈与变更调用逻辑保持；`navigation.jsx:11` 的解析、history 和 Link 行为与旧入口等价，解除了入口/页面循环导入。`components/app-shell.jsx:50` 保留通知、项目切换、原生/浏览器导航和设备角色提示；UI primitives 只组合呈现，未新增传输协议。
- `apps/web/src/workbench.jsx:394` 的 `current.generation`、项目/会话一致性、host identity、轮询和命令互斥未变；`:530` 的 writer client/expiry 判断未变。`NativeModelConfiguration`、`NativeProjectEntry`、资格与编码授权的控制逻辑逐段比较保持一致；只移动 JSX、中文主状态与披露区。`session.send/control/permission.respond` 回调和 pending/unknown 处理保留，未把消息接收或配置保存写成业务验收。
- `workbench.jsx:577` 后的受控产物、权限与文件冲突处理完整保持。`screens.jsx:114` 后的周期、任务、成果、资源、设置与路由分发未变；ProfileDraft、ResourceRecovery、SessionContinuation 保留原调用位置/项目身份绑定。未对这些未改工作流作新的穷尽真实验收。
- `screens.jsx:65` 工作台仍分别计算规划任务、业务 ACCEPTED、待评审与当前周期；规划检查通过和执行结束均未合并为业务验收。AuthGate、PairingGate、native/browser split 以及 transport/If-Match/Idempotency/SSE 源文件保持。
- `ops/ci/ui.py:38` 保留旧 17 个 patterns，加 3 个递归 JSX/JS/CJS 输入模式；排除这个列表后，前后 Python AST 完全相同。选择器、断言、阈值、exit 语义未改。作者 571 项来自 sparse 快照；本复核 573 项仅增加 `execution/commands.json` 与 `execution/toolchains/locked.json`，共同 571 项哈希逐项一致。**数量不作为 CI 验收阈值。**

## 独立验证矩阵

| 层次 | 结果 | 证据 |
|---|---|---|
| Commit/tree/allowlist/hash/clean | PASS | PIN-CHECKS.json、INPUT-REFS.json |
| 状态/路由/协议保持及 CI AST/源集合 | 16 项 PASS | STATIC-COMPARISON-FINAL.json |
| pinned production Web build | PASS | commands/011-web-build |
| 现有 W13 React test | 5/5 PASS | commands/012-w13-react |
| own candidate Core build | PASS，首轮 sparse 缺项保留 | commands/013-core-build、015-core-build |
| own preview 浏览器/native-shaped 流程 | 37 项 PASS | browser-independent-01/report.json |
| 展开新会话和编码授权表单 | 320/1024/1440，51 个控件均未越界 | expanded-forms-01/report.json |
| 真正隔离 Core/SQLite/Owner | 7 项 PASS | real-isolated-01/report.json |
| packaged native Desktop、真实模型/provider | NOT_RUN | 不作成功主张 |
| 完整 registered W13/父任务/正式用例 | NOT_RUN | formal increment = 0 |

浏览器验证使用本复核 worktree 自建 bundle 和独立 loopback preview，未使用作者 preview。核对 320/1440 导航焦点与正反 Tab trap、Escape 恢复、路由/history、主题；native-shaped 回调验证明确取消零调用、明确确认后拒绝可见、UNKNOWN 保留草稿、pending 可见、失效 writer 禁发、资料部分失败重试入口。另验证 browser/native 分流、项目入口、目标/任务/验收区别及 pairing gate。fixture 全部业务请求被拦截；没有落到真实 provider。截图已人工查看：`native-1440-light.png`、`native-320-dark.png`、展开表单图与真实项目图。右卡标题和按钮可读、连接点状态一致、可写为状态而非假按钮、资格详情可展开。展开截图因滚动后的 sticky 顶栏位置而出现顶栏位于长图中段，这是 full-page capture 的滚动位置，不是页面重复顶栏。

真实流程使用新建 Owner 凭据、ASCII 数据根、独占随机端口和自己的 discovery：UI 创建“独立隔离河流研究”，打开周期页、返回、切换深浅主题并确认真实 SSE 连接。SQLite 只读汇总证明 1 个 ProjectProfile，且 runtime_dispatches / host_model_configurations / client_sessions 均为 0；未发模型、provider 或 worker。数据库、Owner 凭据、Core 二进制与 owned temporary root 已删除，截图/原始流/配方保留。

## 失败与证据边界

1. `013-core-build` native_exit=1：sparse 缺 `ops/experiment_sandbox` 与 `ops/supervisor`，补检出原始只读依赖后 `015` 成功；无源码改动。
2. `023-static-review` native_exit=1：本复核一度把作者 571 快照计数写成预期；真实 573 的多出两文件已精确比较并由 `024` 解释。原报告和 raw streams 保留，不改阈值、不冒充产品缺陷。
3. own Core 与两次 preview 显式 terminate + wait，Windows 返回 native_exit=1，均有真实 stop receipt；这是主动结束服务。fixture 的确认拒绝与 UNKNOWN 是期望分支。
4. 作者 `LEDGER-SUPPLEMENT.json` 已读取并绑定：追加遗漏的 diff-check exit2，原 ledger/seal 不改；3 份 Core stop.json 的真实 wait exit=1 已存在。作者仍运行 preview 的退出状态是 NOT_CAPTURED_RUNNING，不推测成功。

每个实际构建/测试/服务动作保留 argv/cwd/relevant env、raw stdout/stderr 与 native exit；预检读取和规则发现见本次工具记录。所有新增证据只写入登记 own_receipts。未触碰原始数据、Desktop、Main checkpoint 或 C57。最终建议仅覆盖此冻结源码的受控本地集成，不扩大为原生产品或正式完成结论。
'''
(E/'FINAL.md').write_text(final,encoding='utf-8')
# One finalizer seal, intentionally excluding its own bytes and in-flight finalizer command streams.
files={p.relative_to(E).as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in E.rglob('*') if p.is_file() and p.name!='FINAL-SEAL.json' and 'commands/029-finalize/' not in p.relative_to(E).as_posix()}
save(E/'FINAL-SEAL.json',dict(schema='researchos.react-source14-independent-review-seal.v1',candidate_commit=SHA,candidate_tree=review['candidate_tree'],scope_sha256=hashlib.sha256(scope.read_bytes()).hexdigest(),verdict=review['verdict'],formal_increment=0,manifest=files,excluded=['FINAL-SEAL.json (self)','commands/029-finalize/* (in-flight finalizer raw streams and result; preserved separately)']))
print(json.dumps(dict(verdict=review['verdict'],seal_sha256=hashlib.sha256((E/'FINAL-SEAL.json').read_bytes()).hexdigest(),files=len(files),formal_increment=0)))
