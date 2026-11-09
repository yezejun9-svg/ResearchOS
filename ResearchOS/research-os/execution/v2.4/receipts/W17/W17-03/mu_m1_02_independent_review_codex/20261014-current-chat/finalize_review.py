from review_tools import E,W,A,S,HEAD,TREE,read,write,pin,guards
import json

attempts=[]
for entry in read(E/'review-ledger.json')['attempts']:
    root=E/entry['name']; results=[]
    for line in (root/'stdout.jsonl').read_text(encoding='utf-8').splitlines():
        try: row=json.loads(line)
        except json.JSONDecodeError: continue
        if row.get('Action') in ('pass','fail','skip') and row.get('Test') and '/' not in row['Test']:
            results.append({'name':row['Test'],'result':row['Action']})
    attempts.append(dict(name=entry['name'],exit=entry['exit'],tests=results))
write(E/'final-source-guard.json',guards())
assets=W.parent/'mu-m1-wire-20261014/.local/m1-01'
write(E/'runtime-inputs.json',{'classification':'READ_ONLY_FROZEN_PUBLIC_RUNTIME_ASSETS', 'inputs':[pin(assets/'node.exe'),pin(assets/'mu-worker.mjs'),pin(__import__('pathlib').Path('D:/作品集/ResearchOS/research-os/.local/mu-m1-core-20261014/runtime-verifier.exe'))]})
finding={
 'id':'M1-02-R1','priority':'P2','title':'已恢复的 Run 再次 PAUSE 会进入不可恢复的 RECONCILING',
 'file':'internal/domain/runtime_pause_windows.go','line_start':806,'line_end':807,
 'related':['internal/domain/runtime_pause.go:294-300','internal/domain/runtime_pause_windows.go:143-157','internal/domain/runtime_coordinator_windows.go:525'],
 'trigger':'第一次原生 PAUSE/RESUME 完成、同一 Run 的 epoch2 模型请求正在执行时，当前有效 Owner 从普通 /v1/projects/{project}/tasks/{task}/actions 发送第二次 PAUSE。',
 'observed':'HTTP 200/Task BLOCKED；epoch2 intent RECONCILING、checkpoint_hash=null；epoch2 dispatch UNKNOWN/protocol not reconciled；模型调用4、Host工具调用1。',
 'cause':'requestRuntimePause 允许运行中的继任 epoch 并提交 Task BLOCKED，但 pauseCheckpoint 调用通用 dispatchGate，持久 activation 的 pauseActivationGate 仍要求 Task RUNNING，拒绝这一合法暂停阶段。',
 'fix':'将第二次暂停纳入精确绑定的暂停阶段门禁，并覆盖第二轮 seal/confirm/resume；若该卡仅支持一次周期，则必须在提交任何 pause intent/Task/control 之前明确拒绝二次 PAUSE，保留当前运行状态。不得泛化放宽 Owner/Goal/lease/activation/queue 绑定。',
 'evidence':'native/TestReviewMuSecondPauseNative/canonical-evidence.json',
 'raw_test':'04-second-pause-native/stdout.jsonl','command':'04-second-pause-native/command.json',
 'observed_vs_inferred':'HTTP/canonical states 是独立原生实测；门禁因果来自冻结源码逐行追踪。'
}
report={'schema':'researchos.mu-m1-02-independent-review.v1','verdict':'NEEDS_CHANGES','source':{'worktree':str(W),'base':'60f8c81a7529081eb51d525ab913d63102148a46','head':HEAD,'tree':TREE,'exact_source_paths':17,'clean':True,'scope':pin(S)},'author_evidence':{'manifest':pin(A/'evidence-manifest.json'),'verified_members':30,'frozen_dependencies_verified':9,'attempt_count':18,'failed_attempts':7,'build_failures':1,'test_failures':6},'independent_attempts':attempts,'independent_failed_attempts':2,'failure_classification':{'02-independent-verifier-build':'review tooling path error: nonexistent ops/runtime_verifier; no product finding; retained numeric exit1','04-second-pause-native':'real AppContainer/public HTTP repro of M1-02-R1; retained numeric exit1'},'findings':[finding],'limitations':['synthetic local model only; no external live model qualification','reused independently hash-verified verifier binary; initial independent rebuild path attempt failed','legacy inline checkpoint failures are known frozen M1-01 debt under a separate compatibility card, not resolved here','author native attempt017 raw file lacks complete argv/environment; this review supplements full fresh argv/environment/exit/source guards','no GUI/Desktop launch, no private key/configuration/grant changes, no Main merge, no parent/formal acceptance'],'formal_increment':0,'main_merged':False,'production_source_modified':False}
write(E/'report.json',report)
text='''# Core Mu M1-02 独立审查

结论：**NEEDS_CHANGES**。冻结源码 exact17 范围与身份一致；首次原生暂停、恢复、取消和未启动继任进程恢复均复跑通过。新增一个已用真实 AppContainer 和普通 HTTP API 复现的 P2 问题，当前源码不能接受。正式验收增量 0，未合并 Main。

## M1-02-R1 / P2：恢复后的第二次暂停失去可恢复检查点

位置：`internal/domain/runtime_pause_windows.go:806-807`；请求入口 `runtime_pause.go:294-300`，检查点入口 `runtime_pause_windows.go:143-157`。

在同一个 Run 完成第一次 PAUSE→RESUME、epoch2 模型请求执行期间，当前有效 Owner 通过公开 HTTP 接口发送第二次 PAUSE。服务返回 **200 / Task BLOCKED**，随后 epoch2 pause intent 进入 **RECONCILING**，`checkpoint_hash=null`，dispatch 进入 **UNKNOWN / protocol not reconciled**。模型调用为4、实际 Host 工具调用为1，没有第二轮确认暂停。这是独立补充用例的 canonical DB 实测结果，不是静态猜测。

源码因果：请求函数允许活动继任 epoch 并将 Task 提交为 BLOCKED；`pauseCheckpoint` 仍调用通用 `dispatchGate`，后者执行持久 activation 的 `pauseActivationGate`；该门禁在806行无条件要求 Task RUNNING，因而拒绝第二轮合法暂停阶段。复现等待15秒只是采证窗口；UNKNOWN 与无 checkpoint 是失败终态证据，不把超时本身当根因。

修复应支持精确绑定的第二轮暂停阶段并测试第二轮 seal/confirm/resume，或者若卡片明确只实现一次周期，在提交 intent/Task/control 之前拒绝第二次 PAUSE，保持原有运行状态。不能为了通过复现放宽 Owner、Goal、lease、activation 或 queue 绑定。

复现未修改任何生产源码。`review-overlay.json` 将原 Host 测试文件映射到审查目录副本，仅增加第二轮调用和采证。完整命令、环境、数字退出码、原始输出与前后源码 guard 位于 `04-second-pause-native/`；DB 行位于 `native/TestReviewMuSecondPauseNative/canonical-evidence.json`。源码原因与运行观察分别记录在 `report.json`。

## 通过的验证与保留的失败

- `01-domain-pause-boundaries`：9个顶层用例通过、0跳过，涵盖 CAS/witness、Task activation、普通恢复不可越权、当前 Owner 撤销、effect cutoff、文件边界、缺失 activation、未启动恢复和 queue cut。
- `03-native-host`：3个顶层用例通过、0跳过。真实 Host/API/DB/verifier/AppContainer，synthetic model。恢复和租约恢复各模型6次、Host写工具1次，四条队列命令各消费一次；取消路径无继任 epoch/无重放。首次暂停 typed ACK、stopped/drained、原 epoch 回放两次、Owner撤销、拒绝请求不得自动重放、activation事务回滚均在原生用例中断言。
- `05-native-queue`：3个顶层用例通过、0跳过，包含实际 Mu 同进程队列、取消 unknown effect、Goal取消与claim两个顺序。
- `04-second-pause-native`：新增独立原生用例失败，对应上述P2。
- `02-independent-verifier-build`：审查构建命令错用不存在的目录，exit1已保留；随后核对并复用公开 verifier SHA-256 `e7bb47ab866cd887499d3cea995a1465643eee9ab4ecadce2e430bccd41500a2`，不把失败算成产品缺陷。

独立尝试5次，其中2次失败，未重置。作者18次尝试、7次失败（构建1、测试6）保留。作者末次原生日志缺完整argv/环境，本审查的新鲜运行补齐这些字段。

## 范围与证据身份

源码 HEAD `ff5ac2047566a52388188b84f267217d8582c571`，tree `e5792b72e0380af65fa1cc5f8b122399c1366d9b`，base `60f8c81a7529081eb51d525ab913d63102148a46`。scope-v4 SHA-256 `a3717a29e1b236e790cc5d639adf2603ddb0935c8307164f2fc2af9654b1e1f5`。精确17文件、9个冻结依赖哈希、作者证据manifest全部30成员已核对，运行前后worktree clean。

作者manifest SHA-256 `2734959da15fcb48765ae5d62b6e782a096cb2b930ec37e5b592743eb4af0193`。独立源码快照、binary diff、输入核验、脚本、测试输出、canonical证据统一由本目录 `evidence-manifest.json` 绑定。

旧 inline checkpoint 两项失败已在作者冻结 M1-01 基线上定位，属于另一张 Bridge 兼容卡；本审查未修复、未把另一张卡的结果混入 Core 接受。当前只验证 synthetic/native；没有 GUI、真实外部模型或正式用例接受，没有更改私钥、Host grants、生产数据库或Main源码。
'''
(E/'report.md').write_text(text,encoding='utf-8')
files=[]
for p in sorted(E.rglob('*')):
    if p.is_file() and p.name!='evidence-manifest.json' and '__pycache__' not in p.parts:
        item=pin(p);item['path']=p.relative_to(E).as_posix();files.append(item)
write(E/'evidence-manifest.json',{'schema':'researchos.independent-review-evidence.v1','files':files,'verdict':'NEEDS_CHANGES','findings':1,'formal_increment':0})
print(json.dumps({'manifest':pin(E/'evidence-manifest.json'),'report':pin(E/'report.md'),'members':len(files),'tests':attempts},ensure_ascii=True))
