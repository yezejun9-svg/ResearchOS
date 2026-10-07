# 06 · 验收标准与测试用例

包版本：`2.4.0`。产品测试状态：**全部 NOT_RUN**。本文件定义实施后的验收，不声称已经安装、运行、校准或证明产品可靠。

## 1. 判定与证据规则

`contracts/acceptance.json` 是本文件逐例目录的机器可读副本，编号、需求和预期必须同步。C01–C20 保留设计主稿 §13.8 的原始语义，A01–A16 补齐真实运行、接口、资格、发布和恢复。每例 `mandatory_gate=true`：正式 v2 交付要求对应运行判据 PASS。某候选应被拒绝的负例中，**成功拒绝**才是测试 PASS；不把被测候选状态改成 PASS。

测试结果仅有 `NOT_RUN / PASS / FAIL / BLOCKED`，与业务 Task 状态分开。初始目录不可因文档校验成功而批量改 PASS。执行结果写入独立运行目录及不可变回执，保留冻结目录hash；重跑不能覆盖失败历史。缺账户、额度、设备、独立标签或必需来源时记 BLOCKED、具体 ResourceRequest 和可继续支路；不反复要求用户提供已有材料。独立开发/fixture 可以继续，但最终 live gate 未通过。

逻辑 command key 对照 `05_WBS.md`。W02 将其落实为 `execution/v2.4/commands.json` 的实际命令和脚本；此时尚未承诺这些命令已经存在。W01 的资格探针先保存真实一次性命令，再由 W02 收编。测试未实现必须非零 `NOT_IMPLEMENTED`，不能以空套件、打印 PASS、工具 exit 0、模型“完成了”代替断言。

| 模式 | 有效证据 | 不能证明 |
|---|---|---|
| FIXTURE | 真实实现处理固定输入、并发与故障注入的实际结果 | 外部服务可用、Windows隔夜能力、真实业务收益 |
| LIVE_WINDOWS | Windows 11 x64 的真实进程/存储/浏览器操作及必要实机手机 | 未实际调用的外部来源或模型能力 |
| LIVE_SERVICE | 已授权外部服务真实请求/响应，失败与注入分开 | 未实测的Windows恢复或完整闭环 |
| LIVE_WINDOWS_AND_SERVICE | 同一trace串联Windows与真实服务 | 其他环境、其他模型/用途自动具备相同资格 |

fixture 输入标为 GENERATED/fixture；在该环境真实执行得到的观察可以留运行证据，但必须保留 `environment_mode=FIXTURE`，不能转成真实来源证据。模拟社会/Agent对话保持 SIMULATED，不能通过多个模拟角色一致成为独立 OBSERVED 证据。

每例均必须包含以下 GLOBAL_EVIDENCE_V1，不得只给一张绿色截图：

1. run_receipt：case_id、run_id、environment_mode、OS/架构、时区、started_at/ended_at、执行者和独立验收者身份。
2. version_manifest：规格包版本/hash、代码commit及dirty状态、锁文件hash、输入快照/hash、模型/适配器/rubric/策略版本；未用字段显式not_applicable及理由。
3. command_receipt：command_key、实际argv/cwd、脱敏环境变量名、退出码、stdout/stderr文件hash；只记录计划命令或工具摘要不合格。
4. assertion_results：每项断言的expected/actual/status、原始证据定位及sha256；负例的拒绝/阻塞回执。
5. acceptance_receipt：独立验证身份、所用验收基线hash、证据索引hash、结论和阻塞项；执行者不能签发自身最终ACCEPTED。

证据文件以 SHA-256 校验，引用指向固定版本而非可覆盖的“latest”。输出中密钥、cookie、个人凭据必须脱敏；保留可核验请求ID/时间/模型revision，不通过删除失败日志美化结论。不可变验收回执绑定输入、规则、产物与验证身份。执行者与最终验证身份不同，不能接受自己的结果；模型评审需在相应用途资格范围内，程序硬门始终独立。

数据实体 `AcceptanceReceipt.measurement_mode` 使用 `FIXTURE / LIVE` 两值：本目录的三种 LIVE_* 环境映射为 LIVE，细分环境写入运行回执。实体检查项状态依 `03_DATA_CONTRACTS.md` 使用 `PASS / FAIL / NOT_RUN / NOT_APPLICABLE`，用例整体 BLOCKED 写在本目录运行结果及阻塞原因中，不新增实体枚举。

## 2. 产品总完成定义（DoD）

1. W00–W21 依赖与回执齐全；R01–R20 有实现和验收映射。当前有效迁移/路线ADR及execution/v2.4/route.json 选定一条底座路线，系统只有一个权威调度和 ProjectState。
2. 本目录 42 个必需用例在匹配版本上 PASS；不存在严重错误采信、跨项目数据泄露、越权执行、旧输入误晋升、重复外部副作用或不可恢复数据损坏。任何此类严重错误阻止交付，不以平均分抵消。
3. GitHub、X、论文的真实来源探针、一次完整真实研究与实际有界实验通过。允许 REJECT/WATCH/INCONCLUSIVE 或零提升结果；不要求为了显示“飞轮”而采用技术。
4. Jev 真实调用、冻结中文/混合评测和故障降级完成。`qualification=FAILED` 可伴随测试 PASS，条件是失败已准确报告且系统留在 ADVISORY/SHADOW。未取得明确用途资格不得启用该用途 BOUNDED_AUTO；v1 不承诺全部用途自动化。
5. Windows 至少 8 小时真实墙钟隔夜观察、真实中断/重启恢复、手机监督、备份恢复、候选代码独立回滚都通过。模拟时钟和Linux单测只是补充。
6. 干净Windows复现、真实命令registry、锁文件、配置模板、可核验构建包、秘密扫描和验收索引齐全。把已知限制与缺失资源写进交付说明；缺必需 live gate 时只能声明“实现/fixture阶段完成，产品交付阻塞”。
7. 发布报告的收益来自固定样本与实际观测，保留基线及未知费用；只改rubric、自评分提高或升级次数不能算改善。首轮无既有数据时报告基线，不造提升百分比。

上述“独立验收服务”指建成产品运行时对研究、采用及产品成果的验收。施工期W00–W21由外部独立评审Agent/程序检查签发回执，写入隔离的bootstrap ledger推进；执行者不得自批，但无需等待尚未实现的产品验收服务。产品验收服务建成后导入带来源的施工记录，不追溯伪造产品已运行。正式产品发布仍需上述DoD全部成立。`tools/validate_package.py` 只检查规格包内部一致性，其 `status=PASS` 仅属于 `scope=SPECIFICATION_PACKAGE_ONLY`，并明确 `product_tests=NOT_RUN`；不会批准上线、自动采用或模型资格。

## 3. Jev 冻结校准的解释

A08 默认门槛是本实施包拟定的初始资格合同，**不是已测成绩，也不是用户指定的统计保证**。初轮整体评测至少60条开发/校准样例，另设完全独立holdout至少30条，总计至少90条；中文与中英混合均衡，初轮holdout各不少于15条。这个整体规模用于发现问题与测试降级，**不能自动授予任何单语言、单用途的自动化资格**。

资格键为 `task_type × language × provider × model_revision × rubric_revision`。每一个拟启用 BOUNDED_AUTO 的键，必须**各自**具备至少60条开发样例和30条独立holdout，且该键严重错误采信为0、`false_accept_count / 该键holdout_count ≤ 5%`。中文与中英混合两个键都晋升时，各自需要至少90条，即至少180条；额外用途/provider/模型/rubric键也必须独立满足要求。聚合统计只作报告，不能以总体均值隐藏某一键样本不足或错误。不足样本或未测键保持 ADVISORY/SHADOW；v1 不要求所有键都取得自动资格。

开发与留出集按来源族/同义改写组隔离，内容覆盖正确采用、拒绝、缺证据、矛盾、注入、数值/日期等反例。模型不能看到holdout标签并据此调参；一旦使用holdout调优，该集合失去留出资格，必须准备新集合。独立标签来自可追溯人工标注或可重算客观结果，多模型投票不能独自作为真值。

每键另报告以负标签数量为分母的错误采信率、漏选、弃权、自动动作覆盖率、费用和延迟。全部弃权/没有可验证自动动作样本不产生自动执行资格。上述样本量只是初始资格规模，并不证明罕见风险消失；真实运行继续观测，发生严重错误立刻撤销相应键资格。

没有真实Jev回执、足够初轮样本或独立标签时，A08保持BLOCKED；可以继续开发/fixture。某键资格失败但真实评测及安全降级均正确时，A08可PASS并交付advisory路线，不能调低同次冻结门槛。硬程序检查、引用存在性、版本匹配、权限和预算始终不被Jev评分覆盖。

任务追踪关系不等于前置过门条件：`wbs_ids`/WBS的`acceptance_ids`表示贡献关系，早期任务通过自身`task_gate_checks`；完整用例仅在`final_owner_task`及必要实现可用后执行。W00只做隔离工作区与包导入前检查，A01的真实导入最终归W04；A02的资格原型在W01完成，真实唯一调度最终在W06验证。C01 的新会话执行与 A03 的完整接受门最终归 W06；W04/W03 先验证上下文/API 阶段子门，不提前要求完整产品用例通过。不得前置标PASS消除依赖死锁。


C21–C26 是本版新增的评测与UI门，全部是首版交付必需用例；组件资格失败可保留负结果，产品合同能力仍必须满足。

## 4. 用例索引

v2.4保留42例，P01–P07/B01–B02和J01–J04是其中的能力断言，不另计用例。W06的P02使用共享核心协议fixture；真实CLI/Desktop接续须在W14/P06实跑，W20验证发行件。桌面验收必须使用实际Desktop安装/进程，浏览器仅作为手机监督与补充。

| ID | 名称 | 最终负责 | 模式 | 状态 |
|---|---|---|---|---|
| C01 | 跨会话接手不丢背景 | W06 | FIXTURE | NOT_RUN |
| C02 | 同名项目材料隔离 | W17 | FIXTURE | NOT_RUN |
| C03 | 变更精确传播并阻止旧成果覆盖 | W04 | FIXTURE | NOT_RUN |
| C04 | 并发冲突与乱序重复事件 | W04 | FIXTURE | NOT_RUN |
| C05 | 没有可采用候选也可真实完成 | W08 | FIXTURE | NOT_RUN |
| C06 | X缺失或限流时准确显示覆盖 | W08 | FIXTURE | NOT_RUN |
| C07 | 高模型评分不能覆盖失败硬证据 | W11 | FIXTURE | NOT_RUN |
| C08 | Jev故障和用途资格变更降级 | W11 | FIXTURE | NOT_RUN |
| C09 | 局部高分不能掩盖系统回归 | W16 | FIXTURE | NOT_RUN |
| C10 | 禁止修改自己的验收门并自证 | W16 | FIXTURE | NOT_RUN |
| C11 | 中断恢复与重复回调对账 | W12 | FIXTURE | NOT_RUN |
| C12 | 真实退化触发回退并冻结候选 | W16 | FIXTURE | NOT_RUN |
| C13 | 默认不限金额与跨会话连续执行 | W12 | FIXTURE | NOT_RUN |
| C14 | 运行中收紧预算与并发预留 | W12 | FIXTURE | NOT_RUN |
| C15 | 额度耗尽后合资格替代或去重请求 | W12 | FIXTURE | NOT_RUN |
| C16 | 有界重试与不能重置的无进展计数 | W12 | FIXTURE | NOT_RUN |
| C17 | 成果通知去重与离线补看 | W13 | FIXTURE | NOT_RUN |
| C18 | 动态计划显示真实计数 | W13 | FIXTURE | NOT_RUN |
| C19 | 转载不增加独立证据数量 | W09 | FIXTURE | NOT_RUN |
| C20 | 改评分规则不等于系统改善 | W16 | FIXTURE | NOT_RUN |
| C21 | 评测结果完整性、硬门与适配资格 | W10 | FIXTURE | NOT_RUN |
| C22 | 正式留出集及派生结果的权限隔离 | W17 | FIXTURE | NOT_RUN |
| C23 | 工作台路由、状态与操作合同 | W13 | FIXTURE | NOT_RUN |
| C24 | 统一视觉、响应式与键盘可用性 | W13 | FIXTURE | NOT_RUN |
| C25 | 成果预览、版本冲突与不可信内容 | W13 | FIXTURE | NOT_RUN |
| C26 | 进度投影、断线补齐与通知一致性 | W13 | FIXTURE | NOT_RUN |
| A01 | 隔离工作区与规格导入完整性 | W04 | FIXTURE | NOT_RUN |
| A02 | 底座资格门与唯一调度路线 | W06 | LIVE_WINDOWS | NOT_RUN |
| A03 | 数据/API约束与事务并发 | W06 | FIXTURE | NOT_RUN |
| A04 | 真实执行器生命周期与取消 | W05 | LIVE_WINDOWS | NOT_RUN |
| A05 | GitHub/X/论文真实来源与故障探针 | W07 | LIVE_SERVICE | NOT_RUN |
| A06 | 检索权限、增量更新与缓存失效 | W09 | FIXTURE | NOT_RUN |
| A07 | 冻结实验、负结果与无法确定 | W10 | FIXTURE | NOT_RUN |
| A08 | Jev中文与混合语言冻结留出评测 | W11 | LIVE_SERVICE | NOT_RUN |
| A09 | 资料到技能的覆盖与晋升 | W15 | FIXTURE | NOT_RUN |
| A10 | 真实Windows Desktop与手机监督可用性 | W17 | LIVE_WINDOWS | NOT_RUN |
| A11 | 密钥保护、设备配对与撤销 | W17 | LIVE_WINDOWS | NOT_RUN |
| A12 | 备份恢复与迁移失败回退 | W18 | LIVE_WINDOWS | NOT_RUN |
| A13 | 首个真实项目完整研究周期 | W14 | LIVE_WINDOWS_AND_SERVICE | NOT_RUN |
| A14 | Windows隔夜运行与真实中断恢复 | W19 | LIVE_WINDOWS_AND_SERVICE | NOT_RUN |
| A15 | 可复现安装、交付与验收索引 | W20 | LIVE_WINDOWS | NOT_RUN |
| A16 | 系统代码候选与独立控制面回滚 | W16 | LIVE_WINDOWS | NOT_RUN |

## 5. 用例细则


### C01 · 跨会话接手不丢背景

模式：FIXTURE；唯一最终负责人：W06；状态：NOT_RUN。

固定输入：

```json
{
  "project": "fixture_project_a",
  "decision_revisions": [
    1,
    2
  ],
  "task_states": [
    "ACCEPTED",
    "READY"
  ],
  "superseded_decision": "decision_old",
  "harness_replays": {
    "H01": {
      "fresh_worker": true,
      "required_context_missing": true,
      "archive_pointer_missing": true
    }
  },
  "product_replays": {
    "P02": {
      "directions": [
        "cli_to_desktop",
        "desktop_to_cli"
      ],
      "same_active_session": true,
      "simultaneous_writers": 2,
      "desktop_stage": "PROTOCOL_FIXTURE_AT_W06_REAL_DESKTOP_AT_W14"
    }
  }
}
```

完整合同：

```json
{
  "id": "C01",
  "title": "跨会话接手不丢背景",
  "requirement_ids": [
    "R01",
    "R02",
    "R03"
  ],
  "wbs_ids": [
    "W04",
    "W06"
  ],
  "setup": [
    "建立一个项目、一个未完成Goal、一个已验收Task及被新决定取代的旧决定；所有材料已在授权存储。",
    "清除Agent会话记忆，保留ProjectState和产物。"
  ],
  "input": {
    "project": "fixture_project_a",
    "decision_revisions": [
      1,
      2
    ],
    "task_states": [
      "ACCEPTED",
      "READY"
    ],
    "superseded_decision": "decision_old",
    "harness_replays": {
      "H01": {
        "fresh_worker": true,
        "required_context_missing": true,
        "archive_pointer_missing": true
      }
    },
    "product_replays": {
      "P02": {
        "directions": [
          "cli_to_desktop",
          "desktop_to_cli"
        ],
        "same_active_session": true,
        "simultaneous_writers": 2,
        "desktop_stage": "PROTOCOL_FIXTURE_AT_W06_REAL_DESKTOP_AT_W14"
      }
    }
  },
  "actions": [
    "启动全新Agent会话读取当前ContextBundle。",
    "要求它说明目标、未完成下一步与有效决定，并执行一个无副作用后续任务。",
    "给全新/空工作区执行器注入bundle，再分别移除必需合同、原文对象和授权记录。",
    "W06用真实CLI与桌面协议测试客户端双向接续同一project/session/Goal，并发发消息/控制和重发command_id；W14再使用真实Desktop复验。"
  ],
  "expected": [
    "目标、未完成任务ID、有效决定revision全部一致。",
    "旧决定只可作为历史显示；不会恢复为生效决定；向用户索取已存在材料次数为0。",
    "ContextBundle包含原始记录引用及快照hash，能回查每个引用。",
    "正常分支复核bundle revision/hash并运行；必需上下文缺失时阻塞受影响调用，不以记忆fail-open继续；可选召回失败只降低覆盖。",
    "两端core_build_id/协议/配置/输入版本一致；同一会话最多一个有效写入owner，重复命令重放原回执；事件、工具结果、费用及产物hash收敛，不能各自启动一个写同一会话的Agent。 W06只证明协议与共享核心，真实Desktop体验和双端接续仍待P03/P06，不提前记为产品UI已通过。"
  ],
  "assertions": [
    {
      "id": "C01-01",
      "check": "当前目标及下一步与项目总账比对",
      "expected": "目标、未完成任务ID、有效决定revision全部一致。"
    },
    {
      "id": "C01-02",
      "check": "废弃信息与索取背景检查",
      "expected": "旧决定只可作为历史显示；不会恢复为生效决定；向用户索取已存在材料次数为0。"
    },
    {
      "id": "C01-03",
      "check": "上下文来源检查",
      "expected": "ContextBundle包含原始记录引用及快照hash，能回查每个引用。"
    },
    {
      "id": "C01-04",
      "check": "冻结上下文与工作区注入",
      "expected": "正常分支复核bundle revision/hash并运行；必需上下文缺失时阻塞受影响调用，不以记忆fail-open继续；可选召回失败只降低覆盖。"
    },
    {
      "id": "C01-05",
      "check": "双端同会话接续与单写入者",
      "expected": "两端core_build_id/协议/配置/输入版本一致；同一会话最多一个有效写入owner，重复命令重放原回执；事件、工具结果、费用及产物hash收敛，不能各自启动一个写同一会话的Agent。 W06只证明协议与共享核心，真实Desktop体验和双端接续仍待P03/P06，不提前记为产品UI已通过。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "会话启动前后ContextBundle、结构化Agent回执、用户输入请求事件计数。",
    "H01重放输入、判断/执行事件、确定性检查与原始输出hash。",
    "P02实际客户端/项目初始化记录、输入版本、命令/事件与证据hash。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.context"
  ],
  "final_owner_task": "W06"
}
```

### C02 · 同名项目材料隔离

模式：FIXTURE；唯一最终负责人：W17；状态：NOT_RUN。

固定输入：

```json
{
  "private_marker": "fixture_b_private_marker",
  "shared_knowledge_scope": [
    "fixture_project_a",
    "fixture_project_b"
  ]
}
```

完整合同：

```json
{
  "id": "C02",
  "title": "同名项目材料隔离",
  "requirement_ids": [
    "R02",
    "R17"
  ],
  "wbs_ids": [
    "W00",
    "W04",
    "W17"
  ],
  "setup": [
    "项目A/B具有同名Task及近似文档，B含独有秘密标记；运行主体仅授权A。",
    "另建明确授权跨项目共享的通用知识项。"
  ],
  "input": {
    "private_marker": "fixture_b_private_marker",
    "shared_knowledge_scope": [
      "fixture_project_a",
      "fixture_project_b"
    ]
  },
  "actions": [
    "从A执行状态读取、ID直读、全文检索、上下文构建和产物下载。",
    "尝试使用B的已知ID及路径越权读取。"
  ],
  "expected": [
    "所有A的响应/日志/ContextBundle不含B的秘密标记；越权请求不返回B正文。",
    "通用知识可读且保留来源、授权范围、版本；共享不扩大为B全项目权限。"
  ],
  "assertions": [
    {
      "id": "C02-01",
      "check": "越权内容检查",
      "expected": "所有A的响应/日志/ContextBundle不含B的秘密标记；越权请求不返回B正文。"
    },
    {
      "id": "C02-02",
      "check": "授权共享检查",
      "expected": "通用知识可读且保留来源、授权范围、版本；共享不扩大为B全项目权限。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "权限矩阵、全部查询请求/响应脱敏件、秘密标记扫描报告。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.context",
    "test.security"
  ],
  "final_owner_task": "W17"
}
```

### C03 · 变更精确传播并阻止旧成果覆盖

模式：FIXTURE；唯一最终负责人：W04；状态：NOT_RUN。

固定输入：

```json
{
  "changed_decision": "D",
  "affected": [
    "T1",
    "A1"
  ],
  "unaffected": [
    "T2"
  ],
  "new_revision": 2
}
```

完整合同：

```json
{
  "id": "C03",
  "title": "变更精确传播并阻止旧成果覆盖",
  "requirement_ids": [
    "R03",
    "R04",
    "R09"
  ],
  "wbs_ids": [
    "W04"
  ],
  "setup": [
    "决定D revision1登记影响任务T1和产物A1；T2无依赖；旧执行器持有revision1快照。"
  ],
  "input": {
    "changed_decision": "D",
    "affected": [
      "T1",
      "A1"
    ],
    "unaffected": [
      "T2"
    ],
    "new_revision": 2
  },
  "actions": [
    "接受D revision2并提交影响传播。",
    "旧执行器提交revision1产物，另让T2继续执行。"
  ],
  "expected": [
    "T1为NEEDS_REVALIDATION，A1为STALE；集合恰为两个受影响对象。",
    "T2可继续且不因本次变更进入NEEDS_REVALIDATION。",
    "旧结果可封存为历史，但不能成为current或ACCEPTED；过期If-Match写入返回412，状态不兼容提交返回409。"
  ],
  "assertions": [
    {
      "id": "C03-01",
      "check": "已登记影响集合",
      "expected": "T1为NEEDS_REVALIDATION，A1为STALE；集合恰为两个受影响对象。"
    },
    {
      "id": "C03-02",
      "check": "无关任务",
      "expected": "T2可继续且不因本次变更进入NEEDS_REVALIDATION。"
    },
    {
      "id": "C03-03",
      "check": "旧结果晋升",
      "expected": "旧结果可封存为历史，但不能成为current或ACCEPTED；过期If-Match写入返回412，状态不兼容提交返回409。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "ImpactLink快照、传播事件、旧提交拒绝回执、T2后续成功回执。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.context",
    "test.domain"
  ],
  "final_owner_task": "W04"
}
```

### C04 · 并发冲突与乱序重复事件

模式：FIXTURE；唯一最终负责人：W04；状态：NOT_RUN。

固定输入：

```json
{
  "writers": 2,
  "duplicate_delivery_count": 3,
  "same_idempotency_key_different_body": true
}
```

完整合同：

```json
{
  "id": "C04",
  "title": "并发冲突与乱序重复事件",
  "requirement_ids": [
    "R04",
    "R10",
    "R12"
  ],
  "wbs_ids": [
    "W03",
    "W04"
  ],
  "setup": [
    "两个执行器取得同一ProjectState revision并提交不兼容的决定；事件通道可重放/乱序。"
  ],
  "input": {
    "writers": 2,
    "duplicate_delivery_count": 3,
    "same_idempotency_key_different_body": true
  },
  "actions": [
    "并发提交冲突变更。",
    "对已提交消息重复三次并逆序发送依赖事件；创建显式整合任务。"
  ],
  "expected": [
    "只有一个同revision写入成功；另一请求412且不覆盖；整合后恰有一个当前生效决定。",
    "相同事件ID最多产生一次业务副作用；缺前序事件先补取/等待，不倒退状态。",
    "相同幂等键/相同请求重放原结果；同键不同请求返回409。"
  ],
  "assertions": [
    {
      "id": "C04-01",
      "check": "并发写仲裁",
      "expected": "只有一个同revision写入成功；另一请求412且不覆盖；整合后恰有一个当前生效决定。"
    },
    {
      "id": "C04-02",
      "check": "重复与乱序",
      "expected": "相同事件ID最多产生一次业务副作用；缺前序事件先补取/等待，不倒退状态。"
    },
    {
      "id": "C04-03",
      "check": "幂等冲突",
      "expected": "相同幂等键/相同请求重放原结果；同键不同请求返回409。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "并发时序、事件ID/序号、幂等表和业务副作用计数、整合决定。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.domain",
    "test.context"
  ],
  "final_owner_task": "W04"
}
```

### C05 · 没有可采用候选也可真实完成

模式：FIXTURE；唯一最终负责人：W08；状态：NOT_RUN。

固定输入：

```json
{
  "candidate_outcomes": [
    "REJECT",
    "WATCH",
    "INCONCLUSIVE"
  ],
  "required_sources": [
    "github",
    "x",
    "papers"
  ],
  "product_replays": {
    "B02": {
      "scenarios": [
        "local_fit",
        "upstream_fit",
        "custom_gap",
        "research_blocked"
      ],
      "blank_custom_reason": true
    }
  },
  "adoption_replays": {
    "J01": {
      "scenarios": [
        "local_fit",
        "popular_wrong_fit",
        "license_unknown",
        "high_score_hard_fail",
        "no_candidate",
        "inspection_clone_only"
      ],
      "required_check_ids": [
        "G01",
        "G02",
        "G03",
        "G04",
        "G05",
        "G06",
        "G07"
      ]
    }
  }
}
```

完整合同：

```json
{
  "id": "C05",
  "title": "没有可采用候选也可真实完成",
  "requirement_ids": [
    "R05",
    "R07",
    "R09",
    "R20"
  ],
  "wbs_ids": [
    "W08",
    "W10",
    "W21"
  ],
  "setup": [
    "三个必需来源均有覆盖回执；所有候选分别不适用、实验失败或无足够采用收益；必需实验已完成。"
  ],
  "input": {
    "candidate_outcomes": [
      "REJECT",
      "WATCH",
      "INCONCLUSIVE"
    ],
    "required_sources": [
      "github",
      "x",
      "papers"
    ],
    "product_replays": {
      "B02": {
        "scenarios": [
          "local_fit",
          "upstream_fit",
          "custom_gap",
          "research_blocked"
        ],
        "blank_custom_reason": true
      }
    },
    "adoption_replays": {
      "J01": {
        "scenarios": [
          "local_fit",
          "popular_wrong_fit",
          "license_unknown",
          "high_score_hard_fail",
          "no_candidate",
          "inspection_clone_only"
        ],
        "required_check_ids": [
          "G01",
          "G02",
          "G03",
          "G04",
          "G05",
          "G06",
          "G07"
        ]
      }
    }
  },
  "actions": [
    "执行候选审查及本轮关闭。",
    "检查采用写入、成果摘要和下一次复查。",
    "对本地足够、上游可改、具体缺口、外部研究受阻四种情况生成ReuseDecision，再尝试跳过记录直接批准从零实现。",
    "回放本地足够、热门但不适配、缺许可证据、高分硬失败、无合格候选和仅调查clone，检查采用前的硬门及独立审查。"
  ],
  "expected": [
    "本轮COMPLETE，必需来源/实验均已完成且游标已保存；负结果不被标为执行错误。",
    "ADOPT数量为0，项目实现版本不变；结论保留证据和原因，不声称功能/质量已提升。",
    "WATCH/INCONCLUSIVE有明确缺口及复查触发；重要排除可形成里程碑，普通空轮不强制通知。",
    "分别复用本地、复用/适配上游、按证据仅自研缺口、保留研究阻塞；无证据CUSTOM_GAP拒绝；零合格候选可为合法结论，但未调研不等于没有现成方案。",
    "调查clone不写ADOPT或稳定项目；合适才整仓/模块/依赖复用；高分不能覆盖G01–G07失败、缺证据、过期hash或自批；REJECT/WATCH/INCONCLUSIVE合法且保留原因。"
  ],
  "assertions": [
    {
      "id": "C05-01",
      "check": "周期完成条件",
      "expected": "本轮COMPLETE，必需来源/实验均已完成且游标已保存；负结果不被标为执行错误。"
    },
    {
      "id": "C05-02",
      "check": "不制造改进",
      "expected": "ADOPT数量为0，项目实现版本不变；结论保留证据和原因，不声称功能/质量已提升。"
    },
    {
      "id": "C05-03",
      "check": "后续安排",
      "expected": "WATCH/INCONCLUSIVE有明确缺口及复查触发；重要排除可形成里程碑，普通空轮不强制通知。"
    },
    {
      "id": "C05-04",
      "check": "缺口自研不能跳过复用",
      "expected": "分别复用本地、复用/适配上游、按证据仅自研缺口、保留研究阻塞；无证据CUSTOM_GAP拒绝；零合格候选可为合法结论，但未调研不等于没有现成方案。"
    },
    {
      "id": "C05-05",
      "check": "判断后再复用",
      "expected": "调查clone不写ADOPT或稳定项目；合适才整仓/模块/依赖复用；高分不能覆盖G01–G07失败、缺证据、过期hash或自批；REJECT/WATCH/INCONCLUSIVE合法且保留原因。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "覆盖/实验回执、候选处置表、关闭事务及成果摘要。",
    "B02实际客户端/项目初始化记录、输入版本、命令/事件与证据hash。",
    "J01冻结候选/输入/判据、来源及实际模式、原始输出、独立检查与动作回执。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.research.fixture",
    "test.experiments"
  ],
  "final_owner_task": "W08"
}
```

### C06 · X缺失或限流时准确显示覆盖

模式：FIXTURE；唯一最终负责人：W08；状态：NOT_RUN。

固定输入：

```json
{
  "x_faults": [
    "NOT_CONFIGURED",
    "RATE_LIMITED"
  ],
  "retry_after_seconds": 60
}
```

完整合同：

```json
{
  "id": "C06",
  "title": "X缺失或限流时准确显示覆盖",
  "requirement_ids": [
    "R05",
    "R06",
    "R12"
  ],
  "wbs_ids": [
    "W07",
    "W08"
  ],
  "setup": [
    "GitHub和论文适配器可用；两次子场景分别X未配置与429限流。"
  ],
  "input": {
    "x_faults": [
      "NOT_CONFIGURED",
      "RATE_LIMITED"
    ],
    "retry_after_seconds": 60
  },
  "actions": [
    "执行两次各自独立研究周期并查看来源覆盖。",
    "在限流等待内重复触发研究。"
  ],
  "expected": [
    "GitHub/论文继续且保存回执、时间窗口和游标；不因X失败全部中止。",
    "必需X未完成时周期为PARTIAL；仅当无任何实质工作可推进才BLOCKED；界面不得称全面扫描或COMPLETE。",
    "429遵守Retry-After，不形成忙重试；缺配置生成去重ResourceRequest，覆盖缺口不被隐藏。"
  ],
  "assertions": [
    {
      "id": "C06-01",
      "check": "独立来源继续",
      "expected": "GitHub/论文继续且保存回执、时间窗口和游标；不因X失败全部中止。"
    },
    {
      "id": "C06-02",
      "check": "覆盖和状态",
      "expected": "必需X未完成时周期为PARTIAL；仅当无任何实质工作可推进才BLOCKED；界面不得称全面扫描或COMPLETE。"
    },
    {
      "id": "C06-03",
      "check": "限流和配置行为",
      "expected": "429遵守Retry-After，不形成忙重试；缺配置生成去重ResourceRequest，覆盖缺口不被隐藏。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "两个故障子场景回执、覆盖表、请求时间戳、资源请求去重计数。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.sources.fixture",
    "test.research.fixture"
  ],
  "final_owner_task": "W08"
}
```

### C07 · 高模型评分不能覆盖失败硬证据

模式：FIXTURE；唯一最终负责人：W11；状态：NOT_RUN。

固定输入：

```json
{
  "model_score": "maximum",
  "fault_cases": [
    "experiment_failed",
    "citation_missing",
    "artifact_hash_mismatch"
  ],
  "harness_replays": {
    "H02": {
      "judge_verdict": "met",
      "last_check_passed": true,
      "earlier_required_check_failed": true,
      "edit_after_check": true,
      "goal_tail_requirement_open": true
    }
  }
}
```

完整合同：

```json
{
  "id": "C07",
  "title": "高模型评分不能覆盖失败硬证据",
  "requirement_ids": [
    "R07",
    "R08",
    "R09"
  ],
  "wbs_ids": [
    "W06",
    "W10",
    "W11"
  ],
  "setup": [
    "已冻结验收规则；Jev适配器fixture返回最高分。"
  ],
  "input": {
    "model_score": "maximum",
    "fault_cases": [
      "experiment_failed",
      "citation_missing",
      "artifact_hash_mismatch"
    ],
    "harness_replays": {
      "H02": {
        "judge_verdict": "met",
        "last_check_passed": true,
        "earlier_required_check_failed": true,
        "edit_after_check": true,
        "goal_tail_requirement_open": true
      }
    }
  },
  "actions": [
    "分别注入实验失败、引用不存在、产物hash不符。",
    "提交正式验收与采用请求。",
    "重放Mu/QM风格met回执：最后lint成功但前一必需测试失败；再测检查后改文件、长目标尾部仍有未完成要求。"
  ],
  "expected": [
    "三种子场景全部拒绝ACCEPTED/ADOPT；高分不修改必需测试结果。",
    "DecisionReceipt同时保留高分、模型版本、反证、失败检查与拒绝原因。",
    "当前正式产物/版本不变，采用动作计数0。",
    "各反例均拒绝完成/ACCEPTED；按完整冻结验收ID与当前代码/输入/产物hash检查，最后命令、模型分数和截短目标不能替代全量证据。"
  ],
  "assertions": [
    {
      "id": "C07-01",
      "check": "硬门独立",
      "expected": "三种子场景全部拒绝ACCEPTED/ADOPT；高分不修改必需测试结果。"
    },
    {
      "id": "C07-02",
      "check": "依据完整",
      "expected": "DecisionReceipt同时保留高分、模型版本、反证、失败检查与拒绝原因。"
    },
    {
      "id": "C07-03",
      "check": "无采用副作用",
      "expected": "当前正式产物/版本不变，采用动作计数0。"
    },
    {
      "id": "C07-04",
      "check": "模型完成声明服从硬门",
      "expected": "各反例均拒绝完成/ACCEPTED；按完整冻结验收ID与当前代码/输入/产物hash检查，最后命令、模型分数和截短目标不能替代全量证据。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "Jev fixture原始响应、失败测试/404引用/hash校验、验收拒绝回执。",
    "H02重放输入、判断/执行事件、确定性检查与原始输出hash。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.orchestration",
    "test.jev.fixture"
  ],
  "final_owner_task": "W11"
}
```

### C08 · Jev故障和用途资格变更降级

模式：FIXTURE；唯一最终负责人：W11；状态：NOT_RUN。

固定输入：

```json
{
  "fault_cases": [
    "timeout",
    "model_revision_changed",
    "chinese_low_confidence",
    "contradictory_evidence"
  ]
}
```

完整合同：

```json
{
  "id": "C08",
  "title": "Jev故障和用途资格变更降级",
  "requirement_ids": [
    "R08",
    "R09",
    "R12"
  ],
  "wbs_ids": [
    "W11"
  ],
  "setup": [
    "某任务类型/语言/model_revision/rubric_revision有固定资格；基础状态和研究读取可独立运行。"
  ],
  "input": {
    "fault_cases": [
      "timeout",
      "model_revision_changed",
      "chinese_low_confidence",
      "contradictory_evidence"
    ]
  },
  "actions": [
    "逐一注入四类故障并请求决策。",
    "检查补证、规则回退、资格状态及原有任务。"
  ],
  "expected": [
    "四种故障均不会扩大BOUNDED_AUTO范围；版本变化不继承旧模型资格。",
    "产生ABSTAIN/补证/重评或已接受确定性规则回执；原ProjectState和历史证据不清空。",
    "已有状态可读、独立来源继续；真正需要模型的步骤标明确阻塞而非编造响应。"
  ],
  "assertions": [
    {
      "id": "C08-01",
      "check": "动作范围",
      "expected": "四种故障均不会扩大BOUNDED_AUTO范围；版本变化不继承旧模型资格。"
    },
    {
      "id": "C08-02",
      "check": "回退与保留",
      "expected": "产生ABSTAIN/补证/重评或已接受确定性规则回执；原ProjectState和历史证据不清空。"
    },
    {
      "id": "C08-03",
      "check": "服务降级",
      "expected": "已有状态可读、独立来源继续；真正需要模型的步骤标明确阻塞而非编造响应。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "各故障注入定义、资格前后快照、决策/资源回执及继续执行证据。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.jev.fixture"
  ],
  "final_owner_task": "W11"
}
```

### C09 · 局部高分不能掩盖系统回归

模式：FIXTURE；唯一最终负责人：W16；状态：NOT_RUN。

固定输入：

```json
{
  "candidate_metric_delta": "+fixture_value",
  "regression": "required_existing_feature_failed"
}
```

完整合同：

```json
{
  "id": "C09",
  "title": "局部高分不能掩盖系统回归",
  "requirement_ids": [
    "R16",
    "R20"
  ],
  "wbs_ids": [
    "W16"
  ],
  "setup": [
    "稳定版本基线全通过；候选在一个优化指标得分更高，但使既有硬功能失败。"
  ],
  "input": {
    "candidate_metric_delta": "+fixture_value",
    "regression": "required_existing_feature_failed"
  },
  "actions": [
    "按冻结套件比较稳定版与候选版。",
    "向独立发布服务申请晋升。"
  ],
  "expected": [
    "候选不晋升；回归必须作为阻塞项，不能加权抵消。",
    "稳定版本hash/活动控制进程不被替换，仍可接受新无关任务。"
  ],
  "assertions": [
    {
      "id": "C09-01",
      "check": "候选阻止",
      "expected": "候选不晋升；回归必须作为阻塞项，不能加权抵消。"
    },
    {
      "id": "C09-02",
      "check": "稳定版连续",
      "expected": "稳定版本hash/活动控制进程不被替换，仍可接受新无关任务。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "同输入比较报告、失败回归、晋升拒绝及稳定版本健康回执。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.evolution"
  ],
  "final_owner_task": "W16"
}
```

### C10 · 禁止修改自己的验收门并自证

模式：FIXTURE；唯一最终负责人：W16；状态：NOT_RUN。

固定输入：

```json
{
  "attacks": [
    "delete_required_test",
    "change_expected_label",
    "grant_publish_permission",
    "forge_acceptance_receipt"
  ]
}
```

完整合同：

```json
{
  "id": "C10",
  "title": "禁止修改自己的验收门并自证",
  "requirement_ids": [
    "R09",
    "R16",
    "R17"
  ],
  "wbs_ids": [
    "W06",
    "W16"
  ],
  "setup": [
    "验收基线由独立验证身份只读挂载；候选只能写隔离候选目录。"
  ],
  "input": {
    "attacks": [
      "delete_required_test",
      "change_expected_label",
      "grant_publish_permission",
      "forge_acceptance_receipt"
    ]
  },
  "actions": [
    "依次提交四类候选变更/请求。",
    "尝试以执行者身份签发ACCEPTED；另测试独立规则变更提案入口。"
  ],
  "expected": [
    "四类攻击均不改动当前验收集hash、标签、权限和稳定版本。",
    "执行者伪造/自签回执不能生效；独立服务按身份、hash及签名/可信存储校验拒绝。",
    "规则修改只能作为独立提案，保留旧规则评测与独立样例，不与候选同事务自批。"
  ],
  "assertions": [
    {
      "id": "C10-01",
      "check": "既有基线",
      "expected": "四类攻击均不改动当前验收集hash、标签、权限和稳定版本。"
    },
    {
      "id": "C10-02",
      "check": "自证阻断",
      "expected": "执行者伪造/自签回执不能生效；独立服务按身份、hash及签名/可信存储校验拒绝。"
    },
    {
      "id": "C10-03",
      "check": "合法规则变更",
      "expected": "规则修改只能作为独立提案，保留旧规则评测与独立样例，不与候选同事务自批。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "访问拒绝日志、前后基线hash、伪造回执拒绝、规则变更提案状态。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.orchestration",
    "test.evolution"
  ],
  "final_owner_task": "W16"
}
```

### C11 · 中断恢复与重复回调对账

模式：FIXTURE；唯一最终负责人：W12；状态：NOT_RUN。

固定输入：

```json
{
  "duplicate_source_pages": 2,
  "duplicate_callbacks": 3,
  "crash_point": "after_external_effect_before_local_ack",
  "harness_replays": {
    "H03": {
      "lease_expires_during_effect": true,
      "effect_response_lost": true,
      "provider_supports_lookup": false
    }
  }
}
```

完整合同：

```json
{
  "id": "C11",
  "title": "中断恢复与重复回调对账",
  "requirement_ids": [
    "R03",
    "R12",
    "R18"
  ],
  "wbs_ids": [
    "W05",
    "W12",
    "W19"
  ],
  "setup": [
    "一轮研究执行到已持久化检查点，某副作用已在外部fixture提交但本地确认尚未落盘。"
  ],
  "input": {
    "duplicate_source_pages": 2,
    "duplicate_callbacks": 3,
    "crash_point": "after_external_effect_before_local_ack",
    "harness_replays": {
      "H03": {
        "lease_expires_during_effect": true,
        "effect_response_lost": true,
        "provider_supports_lookup": false
      }
    }
  },
  "actions": [
    "杀死执行进程后重新启动宿主。",
    "重放来源页和实验回调并运行恢复对账。",
    "外部动作已提交后丢响应、租约过期，旧worker迟到回报；模拟QM once()跨attempt重放。"
  ],
  "expected": [
    "project/goal/cycle/task ID保持不变，恢复后使用最新ContextBundle。",
    "每个幂等副作用实际发生恰一次；未知结果先对账，无法查询的外部动作BLOCKED而非盲重试。",
    "证据去重，游标单调推进；重复回调不生成多份ACCEPTED或里程碑。",
    "新租约可合法重领，但同时最多一个有效owner；旧epoch不能提交当前成果；无供应商幂等/查询依据时保存UNKNOWN_EFFECT并阻塞动作，不能宣称once()保证恰好一次。"
  ],
  "assertions": [
    {
      "id": "C11-01",
      "check": "业务身份",
      "expected": "project/goal/cycle/task ID保持不变，恢复后使用最新ContextBundle。"
    },
    {
      "id": "C11-02",
      "check": "副作用唯一",
      "expected": "每个幂等副作用实际发生恰一次；未知结果先对账，无法查询的外部动作BLOCKED而非盲重试。"
    },
    {
      "id": "C11-03",
      "check": "来源与回执",
      "expected": "证据去重，游标单调推进；重复回调不生成多份ACCEPTED或里程碑。"
    },
    {
      "id": "C11-04",
      "check": "未知副作用与租约恢复",
      "expected": "新租约可合法重领，但同时最多一个有效owner；旧epoch不能提交当前成果；无供应商幂等/查询依据时保存UNKNOWN_EFFECT并阻塞动作，不能宣称once()保证恰好一次。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "故障点日志、持久化检查点、外部副作用ledger、恢复后ID及去重表。",
    "H03重放输入、判断/执行事件、确定性检查与原始输出hash。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.runtime",
    "test.resources"
  ],
  "final_owner_task": "W12"
}
```

### C12 · 真实退化触发回退并冻结候选

模式：FIXTURE；唯一最终负责人：W16；状态：NOT_RUN。

固定输入：

```json
{
  "observed_outcome": "regression_beyond_frozen_threshold",
  "model_score": "maximum"
}
```

完整合同：

```json
{
  "id": "C12",
  "title": "真实退化触发回退并冻结候选",
  "requirement_ids": [
    "R16",
    "R20"
  ],
  "wbs_ids": [
    "W16"
  ],
  "setup": [
    "候选已在有限试用范围启用；冻结关键结果指标和回退条件。"
  ],
  "input": {
    "observed_outcome": "regression_beyond_frozen_threshold",
    "model_score": "maximum"
  },
  "actions": [
    "输入触发回退的观测结果。",
    "保留候选高分并再次请求晋升。"
  ],
  "expected": [
    "满足阈值后回退到先前已接受hash；模型高分不能阻止。",
    "候选被标冻结/禁止晋升，重复申请被拒绝；有新的修复输入/复查依据前不自动重试。",
    "记录触发指标、实际值、阈值、旧新hash、回退回执与恢复资格条件。"
  ],
  "assertions": [
    {
      "id": "C12-01",
      "check": "观测优先",
      "expected": "满足阈值后回退到先前已接受hash；模型高分不能阻止。"
    },
    {
      "id": "C12-02",
      "check": "防反复晋升",
      "expected": "候选被标冻结/禁止晋升，重复申请被拒绝；有新的修复输入/复查依据前不自动重试。"
    },
    {
      "id": "C12-03",
      "check": "失败保留",
      "expected": "记录触发指标、实际值、阈值、旧新hash、回退回执与恢复资格条件。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "冻结阈值、观测结果、回退及重试拒绝回执、候选冻结记录。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.evolution"
  ],
  "final_owner_task": "W16"
}
```

### C13 · 默认不限金额与跨会话连续执行

模式：FIXTURE；唯一最终负责人：W12；状态：NOT_RUN。

固定输入：

```json
{
  "budget_mode": "UNLIMITED_AMOUNT",
  "cap": null,
  "session_end_before_goal_end": true
}
```

完整合同：

```json
{
  "id": "C13",
  "title": "默认不限金额与跨会话连续执行",
  "requirement_ids": [
    "R03",
    "R11",
    "R12"
  ],
  "wbs_ids": [
    "W12",
    "W19"
  ],
  "setup": [
    "初始BudgetPolicy为UNLIMITED_AMOUNT，cap=null；任务已有授权和可用资源。"
  ],
  "input": {
    "budget_mode": "UNLIMITED_AMOUNT",
    "cap": null,
    "session_end_before_goal_end": true
  },
  "actions": [
    "启动耗时任务并结束单个Agent会话。",
    "新会话从检查点继续，记录已知/未知费用。"
  ],
  "expected": [
    "null不转为0；不因用户未填金额上限阻塞。未知费用保持unknown，不能显示为免费。",
    "旧会话结束不令Goal失败/验收；新会话沿用业务ID，重读当前ContextBundle继续。",
    "并发/队列/重试/无进展限制仍有效，不因金额不限变成无限重试。"
  ],
  "assertions": [
    {
      "id": "C13-01",
      "check": "金额语义",
      "expected": "null不转为0；不因用户未填金额上限阻塞。未知费用保持unknown，不能显示为免费。"
    },
    {
      "id": "C13-02",
      "check": "会话与任务分离",
      "expected": "旧会话结束不令Goal失败/验收；新会话沿用业务ID，重读当前ContextBundle继续。"
    },
    {
      "id": "C13-03",
      "check": "运行限制保留",
      "expected": "并发/队列/重试/无进展限制仍有效，不因金额不限变成无限重试。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "预算序列化前后、两会话回执、检查点、费用ledger。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.resources",
    "test.context"
  ],
  "final_owner_task": "W12"
}
```

### C14 · 运行中收紧预算与并发预留

模式：FIXTURE；唯一最终负责人：W12；状态：NOT_RUN。

固定输入：

```json
{
  "currency": "USD",
  "parent_cap": "10.00",
  "child_cap": "20.00",
  "spent": "6.00",
  "reserved": "2.00",
  "new_requests_upper_bounds": [
    "2.00",
    "2.00"
  ],
  "unknown_cost_request": true
}
```

完整合同：

```json
{
  "id": "C14",
  "title": "运行中收紧预算与并发预留",
  "requirement_ids": [
    "R11",
    "R12"
  ],
  "wbs_ids": [
    "W12"
  ],
  "setup": [
    "父/子范围预算可叠加；费用decimal string且同一币种；已有不可取消在途费用。"
  ],
  "input": {
    "currency": "USD",
    "parent_cap": "10.00",
    "child_cap": "20.00",
    "spent": "6.00",
    "reserved": "2.00",
    "new_requests_upper_bounds": [
      "2.00",
      "2.00"
    ],
    "unknown_cost_request": true
  },
  "actions": [
    "原不限额运行时启用上述父限额，两请求并发申请费用预留。",
    "再请求未知费用上界和不同币种调用；显示在途最终结算。"
  ],
  "expected": [
    "有效cap为10.00；两个2.00请求最多一个取得预留；原子预留不超限。",
    "严格模式下无法建立可靠上界或缺显式汇率政策的请求BLOCKED；不自动换算或当零成本。",
    "收紧限额后停止不合规新调用；不可取消在途/晚到结算仍记录，不能声称消除既有外部费用。"
  ],
  "assertions": [
    {
      "id": "C14-01",
      "check": "最严格上限",
      "expected": "有效cap为10.00；两个2.00请求最多一个取得预留；原子预留不超限。"
    },
    {
      "id": "C14-02",
      "check": "未知及币种",
      "expected": "严格模式下无法建立可靠上界或缺显式汇率政策的请求BLOCKED；不自动换算或当零成本。"
    },
    {
      "id": "C14-03",
      "check": "在途透明",
      "expected": "收紧限额后停止不合规新调用；不可取消在途/晚到结算仍记录，不能声称消除既有外部费用。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "并发预留事务、策略revision、每次请求许可结果、费用对账表。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.resources"
  ],
  "final_owner_task": "W12"
}
```

### C15 · 额度耗尽后合资格替代或去重请求

模式：FIXTURE；唯一最终负责人：W12；状态：NOT_RUN。

固定输入：

```json
{
  "primary_fault": "QUOTA_EXHAUSTED",
  "replacement_cases": [
    "qualified_authorized",
    "unauthorized",
    "qualification_mismatch"
  ]
}
```

完整合同：

```json
{
  "id": "C15",
  "title": "额度耗尽后合资格替代或去重请求",
  "requirement_ids": [
    "R08",
    "R10",
    "R11"
  ],
  "wbs_ids": [
    "W12"
  ],
  "setup": [
    "主账户耗尽，提供三个子场景：等价且已授权合格替代、未授权替代、已授权但用途资格不符。"
  ],
  "input": {
    "primary_fault": "QUOTA_EXHAUSTED",
    "replacement_cases": [
      "qualified_authorized",
      "unauthorized",
      "qualification_mismatch"
    ]
  },
  "actions": [
    "分别运行阻塞任务并重复触发五次；并行运行不依赖该资源的支路。"
  ],
  "expected": [
    "仅第一个子场景自动换路；保留等价能力、用途资格、约束及原始验收标准证据。",
    "另两子场景各只生成一个未解决ResourceRequest（同去重键），包含原因/已完成/可继续部分/成本或unknown。",
    "独立支路完成不被连带阻塞；补资源后沿原检查点继续。"
  ],
  "assertions": [
    {
      "id": "C15-01",
      "check": "替代限制",
      "expected": "仅第一个子场景自动换路；保留等价能力、用途资格、约束及原始验收标准证据。"
    },
    {
      "id": "C15-02",
      "check": "资源请求",
      "expected": "另两子场景各只生成一个未解决ResourceRequest（同去重键），包含原因/已完成/可继续部分/成本或unknown。"
    },
    {
      "id": "C15-03",
      "check": "局部继续",
      "expected": "独立支路完成不被连带阻塞；补资源后沿原检查点继续。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "替代资格矩阵、账户授权引用（无密钥）、请求去重表、独立支路回执。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.resources"
  ],
  "final_owner_task": "W12"
}
```

### C16 · 有界重试与不能重置的无进展计数

模式：FIXTURE；唯一最终负责人：W12；状态：NOT_RUN。

固定输入：

```json
{
  "automatic_retry_limit": 2,
  "no_progress_iteration_limit": 3,
  "new_child_goal_attempt": true,
  "harness_replays": {
    "H04": {
      "mu_session_reopened": true,
      "host_continuation_limit_reached": true,
      "user_interrupt": true,
      "new_message_without_new_evidence": true
    }
  },
  "delivery_replays": {
    "U09": {
      "journey_document": "17_USER_JOURNEYS_AND_VALUE.md",
      "real_issue": "ISSUE-REUSE-001",
      "typed_protocol": "researchos-client/2",
      "manual_admin_commands_for_normal_use": 0,
      "old_PASS_is_new_PASS": false,
      "real_issue_selection_policy": "delivery.contract.json:first_real_coding_task_policy"
    }
  }
}
```

完整合同：

```json
{
  "id": "C16",
  "title": "有界重试与不能重置的无进展计数",
  "requirement_ids": [
    "R12",
    "R16"
  ],
  "wbs_ids": [
    "W06",
    "W12"
  ],
  "setup": [
    "固定origin_problem/candidate/input_hash，错误相同且无新证据。"
  ],
  "input": {
    "automatic_retry_limit": 2,
    "no_progress_iteration_limit": 3,
    "new_child_goal_attempt": true,
    "harness_replays": {
      "H04": {
        "mu_session_reopened": true,
        "host_continuation_limit_reached": true,
        "user_interrupt": true,
        "new_message_without_new_evidence": true
      }
    },
    "delivery_replays": {
      "U09": {
        "journey_document": "17_USER_JOURNEYS_AND_VALUE.md",
        "real_issue": "ISSUE-REUSE-001",
        "typed_protocol": "researchos-client/2",
        "manual_admin_commands_for_normal_use": 0,
        "old_PASS_is_new_PASS": false,
        "real_issue_selection_policy": "delivery.contract.json:first_real_coding_task_policy"
      }
    }
  },
  "actions": [
    "执行初次失败及两次自动重试；请求第四次同策略尝试。",
    "进行三个完整无进展迭代后创建子Goal并再请求。",
    "依次重开会话、用尽宿主续跑额度、人工取消、发送无新证据的继续消息并尝试新子Goal。",
    "按17/18/19/22运行U09具体操作与反例，保存原始输出和对应客户端/构建/数据版本。"
  ],
  "expected": [
    "初次尝试+最多两次自动重试；第四次不得继续同错误同策略自动调用，改策略有实证依据或暂停该支路。",
    "第三次无进展后DEFERRED_NO_PROGRESS，保留最好合格结果及恢复条件；不成为ACCEPTED。",
    "子Goal继承相同origin_problem/candidate/input_hash的计数，不清零；新证据/新版本恢复有显式理由记录。",
    "明确区分完成/暂停/资源阻塞/无进展；用户取消不会自动复活；重开或普通消息不清零业务origin计数；可运行独立支路继续，最终验收保持未完成。",
    "原失败/无进展计数跨会话持久不清零；连续两个交付检查点仅增加文档/fixture/框架时优先修最短用户流程并暂停非必要扩展；新候选数量不能冒充用户能力，完整必需门不降低。"
  ],
  "assertions": [
    {
      "id": "C16-01",
      "check": "同输入重试",
      "expected": "初次尝试+最多两次自动重试；第四次不得继续同错误同策略自动调用，改策略有实证依据或暂停该支路。"
    },
    {
      "id": "C16-02",
      "check": "无进展延期",
      "expected": "第三次无进展后DEFERRED_NO_PROGRESS，保留最好合格结果及恢复条件；不成为ACCEPTED。"
    },
    {
      "id": "C16-03",
      "check": "计数范围",
      "expected": "子Goal继承相同origin_problem/candidate/input_hash的计数，不清零；新证据/新版本恢复有显式理由记录。"
    },
    {
      "id": "C16-04",
      "check": "暂停续跑与持久无进展计数",
      "expected": "明确区分完成/暂停/资源阻塞/无进展；用户取消不会自动复活；重开或普通消息不清零业务origin计数；可运行独立支路继续，最终验收保持未完成。"
    },
    {
      "id": "C16-05",
      "check": "整个方向的无价值扩展停止",
      "expected": "原失败/无进展计数跨会话持久不清零；连续两个交付检查点仅增加文档/fixture/框架时优先修最短用户流程并暂停非必要扩展；新候选数量不能冒充用户能力，完整必需门不降低。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "尝试计数、无进展计数键、子Goal继承记录、暂停/恢复事件。",
    "H04重放输入、判断/执行事件、确定性检查与原始输出hash。",
    "U09当前输入/构建/文件hash、操作回执、失败分支和独立复核；fixture与live分开。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.orchestration",
    "test.resources"
  ],
  "final_owner_task": "W12"
}
```

### C17 · 成果通知去重与离线补看

模式：FIXTURE；唯一最终负责人：W13；状态：NOT_RUN。

固定输入：

```json
{
  "release_id": "fixture_release_1",
  "delivery_count": 5,
  "recipient": "user",
  "channel": "in_app"
}
```

完整合同：

```json
{
  "id": "C17",
  "title": "成果通知去重与离线补看",
  "requirement_ids": [
    "R13",
    "R14",
    "R19"
  ],
  "wbs_ids": [
    "W13"
  ],
  "setup": [
    "成果记录与通知outbox同事务提交；手机客户端离线。"
  ],
  "input": {
    "release_id": "fixture_release_1",
    "delivery_count": 5,
    "recipient": "user",
    "channel": "in_app"
  },
  "actions": [
    "同一事件发送五次，在事务提交后模拟发布worker中断。",
    "手机重连并补取快照/缺失事件，查看通知链接。"
  ],
  "expected": [
    "release_id+recipient+channel只存在一条逻辑通知；投递尝试可多次但用户不出现重复卡片。",
    "侧栏、通知、成果详情指向同release_id、artifact hash和acceptance_id。",
    "outbox待发事件可恢复，已读状态幂等；未配置外部渠道时不发邮件/社交消息，不触发Git push。"
  ],
  "assertions": [
    {
      "id": "C17-01",
      "check": "逻辑通知",
      "expected": "release_id+recipient+channel只存在一条逻辑通知；投递尝试可多次但用户不出现重复卡片。"
    },
    {
      "id": "C17-02",
      "check": "版本一致",
      "expected": "侧栏、通知、成果详情指向同release_id、artifact hash和acceptance_id。"
    },
    {
      "id": "C17-03",
      "check": "断线恢复",
      "expected": "outbox待发事件可恢复，已读状态幂等；未配置外部渠道时不发邮件/社交消息，不触发Git push。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "outbox事务/去重键、客户端事件游标、截图和链接解析结果。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.ui",
    "test.domain"
  ],
  "final_owner_task": "W13"
}
```

### C18 · 动态计划显示真实计数

模式：FIXTURE；唯一最终负责人：W13；状态：NOT_RUN。

固定输入：

```json
{
  "accepted": 4,
  "awaiting_review": 2,
  "new_ready": 3,
  "final_plan_count": 9
}
```

完整合同：

```json
{
  "id": "C18",
  "title": "动态计划显示真实计数",
  "requirement_ids": [
    "R13",
    "R14"
  ],
  "wbs_ids": [
    "W13"
  ],
  "setup": [
    "计划revision1有六项：四项ACCEPTED，两项VERIFYING；revision2再增加三项READY。"
  ],
  "input": {
    "accepted": 4,
    "awaiting_review": 2,
    "new_ready": 3,
    "final_plan_count": 9
  },
  "actions": [
    "分别展示两个revision的侧栏，逆序重放旧projection事件。"
  ],
  "expected": [
    "revision1显示已验收4/计划6、待评审2；revision2显示已验收4/计划9、待评审2、新增3。",
    "标明计划revision及分母6→9；待评审不计已完成，无总体虚假百分比。",
    "旧事件不覆盖新revision；计数可从权威任务状态重新生成。"
  ],
  "assertions": [
    {
      "id": "C18-01",
      "check": "计数",
      "expected": "revision1显示已验收4/计划6、待评审2；revision2显示已验收4/计划9、待评审2、新增3。"
    },
    {
      "id": "C18-02",
      "check": "计划变更透明",
      "expected": "标明计划revision及分母6→9；待评审不计已完成，无总体虚假百分比。"
    },
    {
      "id": "C18-03",
      "check": "投影一致",
      "expected": "旧事件不覆盖新revision；计数可从权威任务状态重新生成。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "两个revision总账和projection、桌面/移动截图、逆序事件结果。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.ui"
  ],
  "final_owner_task": "W13"
}
```

### C19 · 转载不增加独立证据数量

模式：FIXTURE；唯一最终负责人：W09；状态：NOT_RUN。

固定输入：

```json
{
  "upstream_origins": 2,
  "reposts": 4,
  "simulated_agreement_count": 20
}
```

完整合同：

```json
{
  "id": "C19",
  "title": "转载不增加独立证据数量",
  "requirement_ids": [
    "R06",
    "R09"
  ],
  "wbs_ids": [
    "W08",
    "W09"
  ],
  "setup": [
    "提供一个原始研究/仓库声明、四篇转述、一个真正独立实验；含同文不同URL和时间变更。"
  ],
  "input": {
    "upstream_origins": 2,
    "reposts": 4,
    "simulated_agreement_count": 20
  },
  "actions": [
    "归一URL/版本并建立derived_from关系。",
    "加入20个模拟Agent一致意见，再计算支持证据。"
  ],
  "expected": [
    "四个转述保留各自记录及原始来源链；同源传播不被当四个独立确认。",
    "真实独立来源为2，模拟意见计入SIMULATED且不增加OBSERVED独立支持数量。",
    "来源关系无法确认时标unknown/待核验，不凭摘要相似或数量直接提高可靠度。"
  ],
  "assertions": [
    {
      "id": "C19-01",
      "check": "传播保留",
      "expected": "四个转述保留各自记录及原始来源链；同源传播不被当四个独立确认。"
    },
    {
      "id": "C19-02",
      "check": "独立计数",
      "expected": "真实独立来源为2，模拟意见计入SIMULATED且不增加OBSERVED独立支持数量。"
    },
    {
      "id": "C19-03",
      "check": "无法定源",
      "expected": "来源关系无法确认时标unknown/待核验，不凭摘要相似或数量直接提高可靠度。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "证据关系图、来源快照hash、独立来源计算结果、模拟分类记录。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.research.fixture",
    "test.retrieval"
  ],
  "final_owner_task": "W09"
}
```

### C20 · 改评分规则不等于系统改善

模式：FIXTURE；唯一最终负责人：W16；状态：NOT_RUN。

固定输入：

```json
{
  "artifact_unchanged": true,
  "heldout_outcome_unchanged": true,
  "score_increased": true
}
```

完整合同：

```json
{
  "id": "C20",
  "title": "改评分规则不等于系统改善",
  "requirement_ids": [
    "R08",
    "R16",
    "R20"
  ],
  "wbs_ids": [
    "W11",
    "W16",
    "W21"
  ],
  "setup": [
    "稳定版产物和实际结果固定；候选只修改rubric，使旧产物分数更高。"
  ],
  "input": {
    "artifact_unchanged": true,
    "heldout_outcome_unchanged": true,
    "score_increased": true
  },
  "actions": [
    "同时保留旧rubric结果、新rubric结果并申请晋升。",
    "生成改进与项目关闭报告。"
  ],
  "expected": [
    "不能宣称系统质量/真实结果改善；无独立收益依据则不晋升该候选。",
    "评分规则、样本、模型、输入hash及实际结果版本全部保留；跨rubric分数不可直接当同尺度增量。",
    "可记录规则研究结论或INCONCLUSIVE；负/零改善结论不被改写为收益。"
  ],
  "assertions": [
    {
      "id": "C20-01",
      "check": "不虚构提升",
      "expected": "不能宣称系统质量/真实结果改善；无独立收益依据则不晋升该候选。"
    },
    {
      "id": "C20-02",
      "check": "版本可比",
      "expected": "评分规则、样本、模型、输入hash及实际结果版本全部保留；跨rubric分数不可直接当同尺度增量。"
    },
    {
      "id": "C20-03",
      "check": "结论合法",
      "expected": "可记录规则研究结论或INCONCLUSIVE；负/零改善结论不被改写为收益。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "双rubric原始回执、冻结holdout结果、晋升拒绝、最终收益表。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.jev.fixture",
    "test.evolution",
    "acceptance.audit"
  ],
  "final_owner_task": "W16"
}
```

### C21 · 评测结果完整性、硬门与适配资格

模式：FIXTURE；唯一最终负责人：W10；状态：NOT_RUN。

固定输入：

```json
{
  "fixture_file": "examples/evaluation_smoke_cases.json",
  "expected_case_count": 12,
  "harness_replays": {
    "H05": {
      "arms": [
        "full",
        "rules",
        "judge_shadow"
      ],
      "logs": [
        "vitest",
        "pytest",
        "go_test",
        "powershell",
        "unknown_format"
      ],
      "protected": [
        "failures",
        "exit_codes",
        "constraints",
        "conflicts",
        "acceptance_ids",
        "required_sources"
      ]
    }
  },
  "skill_up_report_replay": {
    "engine": "SKILL_UP",
    "variants": 3,
    "iterations": 2,
    "duplicate_and_missing": true,
    "zero_assertions": true,
    "summary_only_rejected": true
  }
}
```

完整合同：

```json
{
  "id": "C21",
  "title": "评测结果完整性、硬门与适配资格",
  "requirement_ids": [
    "R07",
    "R09",
    "R20"
  ],
  "wbs_ids": [
    "W10"
  ],
  "setup": [
    "冻结12条开发夹具、引擎版本、候选/基线/配置/数据集hash；使用真实评测运行器，外部模型可为标记明确的确定性假服务。"
  ],
  "input": {
    "fixture_file": "examples/evaluation_smoke_cases.json",
    "expected_case_count": 12,
    "harness_replays": {
      "H05": {
        "arms": [
          "full",
          "rules",
          "judge_shadow"
        ],
        "logs": [
          "vitest",
          "pytest",
          "go_test",
          "powershell",
          "unknown_format"
        ],
        "protected": [
          "failures",
          "exit_codes",
          "constraints",
          "conflicts",
          "acceptance_ids",
          "required_sources"
        ]
      }
    },
    "skill_up_report_replay": {
      "engine": "SKILL_UP",
      "variants": 3,
      "iterations": 2,
      "duplicate_and_missing": true,
      "zero_assertions": true,
      "summary_only_rejected": true
    }
  },
  "actions": [
    "运行完整夹具，导入逐条结果并与预期ID清单对账。",
    "注入零样本、漏例、重复、错误退出、阈值改动、高分硬失败；再比较稳定与故意退化候选。",
    "检查指定provider外的实际出站与分享行为，关闭未授权服务；固定当前CLI真实参数。",
    "使用固定多语言日志和任务重放三组；折叠重复输出后展开，注入解析失败、判定超时、原文对象缺失和恶意高置信删除建议。",
    "导入固定skill-up原始报告的正常与异常样例，核对variant/iteration/重复/缺例及零断言。"
  ],
  "expected": [
    "12条语义均正确处理，错误/弃权/缺失计数独立且分母不缩小；零样本与重复不能获得有效COMPLETE。",
    "配置/数据集/候选hash不符时拒收；高模型分不覆盖确定性硬失败。",
    "回归和负结果保留；退出0不等于验收，EvaluationReport只是证据产物。",
    "Promptfoo适配结论单列；若不适用，有界失败证据及等价NATIVE执行器必须仍通过同样合同；冒烟不得自动授予模型或Jev资格。",
    "规则折叠逐字节可逆，原文hash/范围可查；失败/退出码/授权/用户原话/矛盾/验收/必要来源不裁掉；未知格式或判定异常保留原文；SHADOW不改变实际输入。",
    "SKILL_UP原始结果按冻结variant×iteration分别归一化EvaluationReport并关联维度索引；未知/重复/缺例/空断言和SKIP不能被DSH汇总吞掉，工具版本、原始状态和费用未知项完整保留。"
  ],
  "assertions": [
    {
      "id": "C21-01",
      "check": "12条语义均正确处理，错误/弃权/缺失计数独立且分母不缩小",
      "expected": "12条语义均正确处理，错误/弃权/缺失计数独立且分母不缩小；零样本与重复不能获得有效COMPLETE。"
    },
    {
      "id": "C21-02",
      "check": "配置/数据集/候选hash不符时拒收",
      "expected": "配置/数据集/候选hash不符时拒收；高模型分不覆盖确定性硬失败。"
    },
    {
      "id": "C21-03",
      "check": "回归和负结果保留",
      "expected": "回归和负结果保留；退出0不等于验收，EvaluationReport只是证据产物。"
    },
    {
      "id": "C21-04",
      "check": "Promptfoo适配结论单列",
      "expected": "Promptfoo适配结论单列；若不适用，有界失败证据及等价NATIVE执行器必须仍通过同样合同；冒烟不得自动授予模型或Jev资格。"
    },
    {
      "id": "C21-05",
      "check": "原文可恢复与受保护信息",
      "expected": "规则折叠逐字节可逆，原文hash/范围可查；失败/退出码/授权/用户原话/矛盾/验收/必要来源不裁掉；未知格式或判定异常保留原文；SHADOW不改变实际输入。"
    },
    {
      "id": "C21-06",
      "check": "skill-up结果完整性",
      "expected": "SKILL_UP原始结果按冻结variant×iteration分别归一化EvaluationReport并关联维度索引；未知/重复/缺例/空断言和SKIP不能被DSH汇总吞掉，工具版本、原始状态和费用未知项完整保留。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "实际输入/输出与命令、受控证据索引、逐项断言；界面项另保存指定视口截图与操作记录。",
    "H05重放输入、判断/执行事件、确定性检查与原始输出hash。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.evaluation.fixture"
  ],
  "final_owner_task": "W10"
}
```

### C22 · 正式留出集及派生结果的权限隔离

模式：FIXTURE；唯一最终负责人：W17；状态：NOT_RUN。

固定输入：

```json
{
  "restricted_marker": "fixture_holdout_private_marker",
  "access_classes": [
    "PROJECT",
    "VERIFIER_ONLY"
  ]
}
```

完整合同：

```json
{
  "id": "C22",
  "title": "正式留出集及派生结果的权限隔离",
  "requirement_ids": [
    "R08",
    "R09",
    "R17"
  ],
  "wbs_ids": [
    "W17"
  ],
  "setup": [
    "建立普通候选Executor、Planner、独立Verifier和Owner身份；在独立受保护环境登记holdout及原始结果VERIFIER_ONLY。"
  ],
  "input": {
    "restricted_marker": "fixture_holdout_private_marker",
    "access_classes": [
      "PROJECT",
      "VERIFIER_ONLY"
    ]
  },
  "actions": [
    "候选尝试文件读取、已知ID内容下载、列表、搜索、ContextBundle、事件、日志、导出、预览和备份读取。",
    "尝试把holdout派生成PROJECT报告，或改权重、标签、基线后提交；独立Verifier运行并输出不泄题汇总。",
    "验证重启后访问控制仍生效；同目录子Agent不视为隔离。"
  ],
  "expected": [
    "候选无权取得完整题库、标签和逐例详情；API/文件/缓存/日志/事件均不泄漏测试标记。",
    "被测端只接收当次必要输入；公开汇总不包含原文、答案、逐例反馈或可还原题目的diff。",
    "执行者不能降级受限内容或篡改自身判据；明确有权Verifier/Owner可追溯完整证据。",
    "隔离不成立时资格BLOCKED/ADVISORY，不能授予BOUNDED_AUTO；重启不放宽边界。"
  ],
  "assertions": [
    {
      "id": "C22-01",
      "check": "候选无权取得完整题库、标签和逐例详情",
      "expected": "候选无权取得完整题库、标签和逐例详情；API/文件/缓存/日志/事件均不泄漏测试标记。"
    },
    {
      "id": "C22-02",
      "check": "被测端只接收当次必要输入",
      "expected": "被测端只接收当次必要输入；公开汇总不包含原文、答案、逐例反馈或可还原题目的diff。"
    },
    {
      "id": "C22-03",
      "check": "执行者不能降级受限内容或篡改自身判据",
      "expected": "执行者不能降级受限内容或篡改自身判据；明确有权Verifier/Owner可追溯完整证据。"
    },
    {
      "id": "C22-04",
      "check": "隔离不成立时资格BLOCKED/ADVISORY，不能授予BOUNDED_AUTO",
      "expected": "隔离不成立时资格BLOCKED/ADVISORY，不能授予BOUNDED_AUTO；重启不放宽边界。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "实际输入/输出与命令、受控证据索引、逐项断言；界面项另保存指定视口截图与操作记录。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.evaluation.security",
    "test.security"
  ],
  "final_owner_task": "W17"
}
```

### C23 · 工作台路由、状态与操作合同

模式：FIXTURE；唯一最终负责人：W13；状态：NOT_RUN。

固定输入：

```json
{
  "ui_contract": "contracts/ui.contract.json",
  "product_replays": {
    "P03": {
      "surface": "INSTALLED_DESKTOP",
      "flows": [
        "open_folder",
        "provider_setup",
        "chat",
        "tool_stream",
        "file_tree",
        "diff",
        "goal_control"
      ]
    }
  },
  "delivery_replays": {
    "U04": {
      "journey_document": "17_USER_JOURNEYS_AND_VALUE.md",
      "real_issue": "ISSUE-REUSE-001",
      "typed_protocol": "researchos-client/2",
      "manual_admin_commands_for_normal_use": 0,
      "old_PASS_is_new_PASS": false,
      "real_issue_selection_policy": "delivery.contract.json:first_real_coding_task_policy"
    }
  }
}
```

完整合同：

```json
{
  "id": "C23",
  "title": "工作台路由、状态与操作合同",
  "requirement_ids": [
    "R13",
    "R14",
    "R19"
  ],
  "wbs_ids": [
    "W13"
  ],
  "setup": [
    "使用真实前端与固定后端夹具，覆盖contracts/ui.contract.json中的页面及Task/Run状态。"
  ],
  "input": {
    "ui_contract": "contracts/ui.contract.json",
    "product_replays": {
      "P03": {
        "surface": "INSTALLED_DESKTOP",
        "flows": [
          "open_folder",
          "provider_setup",
          "chat",
          "tool_stream",
          "file_tree",
          "diff",
          "goal_control"
        ]
      }
    },
    "delivery_replays": {
      "U04": {
        "journey_document": "17_USER_JOURNEYS_AND_VALUE.md",
        "real_issue": "ISSUE-REUSE-001",
        "typed_protocol": "researchos-client/2",
        "manual_admin_commands_for_normal_use": 0,
        "old_PASS_is_new_PASS": false,
        "real_issue_selection_policy": "delivery.contract.json:first_real_coding_task_policy"
      }
    }
  },
  "actions": [
    "逐页进入工作台、周期、任务、成果、证据、实验、知识、团队、资源与设备设置。",
    "执行暂停/恢复/取消并观察等待与最终回执；切换项目、查看不同产物版本。",
    "检查新建想法、筛选、详情、错误恢复以及禁用动作说明。",
    "在真实Desktop壳中完成打开目录、模型配置、会话输入、工具执行流、文件/diff/成果预览和Goal控制；fixture后端与live资格分开。",
    "按17/18/19/22运行U04具体操作与反例，保存原始输出和对应客户端/构建/数据版本。"
  ],
  "expected": [
    "页面operationId与数据字段都能映射合同；未实现功能不能用静态按钮假成功。",
    "EXECUTION_REPORTED/VERIFYING与ACCEPTED清楚区分；取消请求未确认前保留等待状态。",
    "空集、加载、失败、403、限流、过期、部分来源与离线分别展示；不跨项目串数据。",
    "普通用户首屏可找到目标、当前阶段、阻塞、最近已验收成果与下一步；技术日志按需展开。",
    "11个视图属于同一Desktop；主区可操作Agent会话，不只是研究看板；各动作调用真实实现/固定测试后端且有回执，未实现不能静态假成功。",
    "researchos-client/2每项method有冻结payload/result和事件类型；目录注册、模型目录/探针/选择、文件树/读写/diff、权限处理、会话更新真实对接；错误类型可见，不返回裸object成功，不虚构handler。"
  ],
  "assertions": [
    {
      "id": "C23-01",
      "check": "页面operationId与数据字段都能映射合同",
      "expected": "页面operationId与数据字段都能映射合同；未实现功能不能用静态按钮假成功。"
    },
    {
      "id": "C23-02",
      "check": "EXECUTION_REPORTED/VERIFYING与ACCEPTED清楚区分",
      "expected": "EXECUTION_REPORTED/VERIFYING与ACCEPTED清楚区分；取消请求未确认前保留等待状态。"
    },
    {
      "id": "C23-03",
      "check": "空集、加载、失败、403、限流、过期、部分来源与离线分别展示",
      "expected": "空集、加载、失败、403、限流、过期、部分来源与离线分别展示；不跨项目串数据。"
    },
    {
      "id": "C23-04",
      "check": "普通用户首屏可找到目标、当前阶段、阻塞、最近已验收成果与下一步",
      "expected": "普通用户首屏可找到目标、当前阶段、阻塞、最近已验收成果与下一步；技术日志按需展开。"
    },
    {
      "id": "C23-05",
      "check": "Desktop可操作主流程",
      "expected": "11个视图属于同一Desktop；主区可操作Agent会话，不只是研究看板；各动作调用真实实现/固定测试后端且有回执，未实现不能静态假成功。"
    },
    {
      "id": "C23-06",
      "check": "typed客户端与可操作界面",
      "expected": "researchos-client/2每项method有冻结payload/result和事件类型；目录注册、模型目录/探针/选择、文件树/读写/diff、权限处理、会话更新真实对接；错误类型可见，不返回裸object成功，不虚构handler。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "实际输入/输出与命令、受控证据索引、逐项断言；界面项另保存指定视口截图与操作记录。",
    "P03实际客户端/项目初始化记录、输入版本、命令/事件与证据hash。",
    "U04当前输入/构建/文件hash、操作回执、失败分支和独立复核；fixture与live分开。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.ui.routes"
  ],
  "final_owner_task": "W13"
}
```

### C24 · 统一视觉、响应式与键盘可用性

模式：FIXTURE；唯一最终负责人：W13；状态：NOT_RUN。

固定输入：

```json
{
  "viewports": [
    [
      1440,
      1000
    ],
    [
      1024,
      768
    ],
    [
      768,
      1024
    ],
    [
      390,
      844
    ],
    [
      320,
      780
    ]
  ],
  "themes": [
    "light",
    "dark"
  ]
}
```

完整合同：

```json
{
  "id": "C24",
  "title": "统一视觉、响应式与键盘可用性",
  "requirement_ids": [
    "R13",
    "R19"
  ],
  "wbs_ids": [
    "W13"
  ],
  "setup": [
    "真实前端使用ui/design-tokens.json；浅色/深色各准备主要页面。"
  ],
  "input": {
    "viewports": [
      [
        1440,
        1000
      ],
      [
        1024,
        768
      ],
      [
        768,
        1024
      ],
      [
        390,
        844
      ],
      [
        320,
        780
      ]
    ],
    "themes": [
      "light",
      "dark"
    ]
  },
  "actions": [
    "在1440×1000、1024×768、768×1024、390×844及320px宽度检查；额外200%缩放与reduced-motion。",
    "键盘访问导航、标签、抽屉、筛选与关键按钮，检查焦点回归和屏幕阅读器名称。",
    "测量关键文本/控件对比度、移动触点、空态和长中文内容换行。"
  ],
  "expected": [
    "应用页面无非必要整页横向滚动；代码/大型表格仅在局部滚动，手机使用抽屉或单列。",
    "主要文本对比度≥4.5:1，大字与关键图形≥3:1；状态有文字/图标，不只依赖颜色。",
    "手机主要触点≥44×44 CSS px；可见焦点、语义标题、键盘完整操作、关闭抽屉回焦点。",
    "两主题引用同一token版本；无文本遮挡、关键操作移出屏幕或强制动画；保留截图与逐项结果。"
  ],
  "assertions": [
    {
      "id": "C24-01",
      "check": "应用页面无非必要整页横向滚动",
      "expected": "应用页面无非必要整页横向滚动；代码/大型表格仅在局部滚动，手机使用抽屉或单列。"
    },
    {
      "id": "C24-02",
      "check": "主要文本对比度≥4.5:1，大字与关键图形≥3:1",
      "expected": "主要文本对比度≥4.5:1，大字与关键图形≥3:1；状态有文字/图标，不只依赖颜色。"
    },
    {
      "id": "C24-03",
      "check": "手机主要触点≥44×44 CSS px",
      "expected": "手机主要触点≥44×44 CSS px；可见焦点、语义标题、键盘完整操作、关闭抽屉回焦点。"
    },
    {
      "id": "C24-04",
      "check": "两主题引用同一token版本",
      "expected": "两主题引用同一token版本；无文本遮挡、关键操作移出屏幕或强制动画；保留截图与逐项结果。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "实际输入/输出与命令、受控证据索引、逐项断言；界面项另保存指定视口截图与操作记录。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.ui.visual"
  ],
  "final_owner_task": "W13"
}
```

### C25 · 成果预览、版本冲突与不可信内容

模式：FIXTURE；唯一最终负责人：W13；状态：NOT_RUN。

固定输入：

```json
{
  "max_inline_bytes": 5242880
}
```

完整合同：

```json
{
  "id": "C25",
  "title": "成果预览、版本冲突与不可信内容",
  "requirement_ids": [
    "R04",
    "R09",
    "R17",
    "R19"
  ],
  "wbs_ids": [
    "W13"
  ],
  "setup": [
    "提供Markdown/HTML/图片/PDF/JSON/CSV/代码产物及两个冲突草稿；固定artifact_id+revision+content_hash。"
  ],
  "input": {
    "max_inline_bytes": 5242880
  },
  "actions": [
    "打开预览，注入HTML脚本、外链、路径越界和超大内容；查看来源与验收回执。",
    "编辑时外部更新基线，尝试提交旧草稿；先保存双方版本再走ChangeProposal/合并。",
    "访问失效产物及VERIFIER_ONLY产物并切换项目。"
  ],
  "expected": [
    "预览对应正确封存版本，失效/模拟/生成/待验收标签始终可见；未支持类型提供下载和原因。",
    "HTML默认无脚本且独立受限预览；外部网络不自动加载，渲染失败不执行宿主代码。",
    "冲突不自动取新revision重试旧草稿；已封存产物不可原地编辑，合并产生新候选版本并重验。",
    "越权返回拒绝；超大文件分块/下载，失败可恢复且不暴露宿主路径与凭据。"
  ],
  "assertions": [
    {
      "id": "C25-01",
      "check": "预览对应正确封存版本，失效/模拟/生成/待验收标签始终可见",
      "expected": "预览对应正确封存版本，失效/模拟/生成/待验收标签始终可见；未支持类型提供下载和原因。"
    },
    {
      "id": "C25-02",
      "check": "HTML默认无脚本且独立受限预览",
      "expected": "HTML默认无脚本且独立受限预览；外部网络不自动加载，渲染失败不执行宿主代码。"
    },
    {
      "id": "C25-03",
      "check": "冲突不自动取新revision重试旧草稿",
      "expected": "冲突不自动取新revision重试旧草稿；已封存产物不可原地编辑，合并产生新候选版本并重验。"
    },
    {
      "id": "C25-04",
      "check": "越权返回拒绝",
      "expected": "越权返回拒绝；超大文件分块/下载，失败可恢复且不暴露宿主路径与凭据。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "实际输入/输出与命令、受控证据索引、逐项断言；界面项另保存指定视口截图与操作记录。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.ui.preview",
    "test.contracts.security"
  ],
  "final_owner_task": "W13"
}
```

### C26 · 进度投影、断线补齐与通知一致性

模式：FIXTURE；唯一最终负责人：W13；状态：NOT_RUN。

固定输入：

```json
{
  "event_transport": "SSE",
  "expired_cursor_http_status": 410,
  "harness_replays": {
    "H09": {
      "runtime_status": "met",
      "acceptance_receipt_valid": false,
      "decision_event_replay_count": 3
    }
  }
}
```

完整合同：

```json
{
  "id": "C26",
  "title": "进度投影、断线补齐与通知一致性",
  "requirement_ids": [
    "R03",
    "R12",
    "R13",
    "R14"
  ],
  "wbs_ids": [
    "W13"
  ],
  "setup": [
    "建立六阶段ProgressProjection与相同plan_revision的事件流、成果和通知。"
  ],
  "input": {
    "event_transport": "SSE",
    "expired_cursor_http_status": 410,
    "harness_replays": {
      "H09": {
        "runtime_status": "met",
        "acceptance_receipt_valid": false,
        "decision_event_replay_count": 3
      }
    }
  },
  "actions": [
    "注入重复/乱序/缺号事件，断网重连，Last-Event-ID过期返回410。",
    "计划增加任务并产生旧事件；切换项目，通知多次重放。",
    "控制面离线、电脑休眠及恢复后比对服务器快照与界面。",
    "让运行器报告met但无有效验收，再重放判断和暂停事件、离线重连。"
  ],
  "expected": [
    "按event_id去重、按sequence补齐；410读取带水位快照，旧revision不覆盖新状态。",
    "planned/accepted/pending_review/blocked/active与服务端一致，计划变化注明；token流速不当业务进度。",
    "同release/recipient/channel仅一条通知；重放不会触发取消/采用等副作用。",
    "离线显示最后同步时间与数据可能过期，不能继续伪造采集动画或进度；跨项目响应不串入当前页。",
    "UI显示运行器声明与待验收/阻塞原因，不能显示产品已完成；账本/原文可定位；事件重放不重发判断、不重复计费或通知。"
  ],
  "assertions": [
    {
      "id": "C26-01",
      "check": "按event_id去重、按sequence补齐",
      "expected": "按event_id去重、按sequence补齐；410读取带水位快照，旧revision不覆盖新状态。"
    },
    {
      "id": "C26-02",
      "check": "planned/accepted/pending_review/blocked/active与服务端一致，计划变化注明",
      "expected": "planned/accepted/pending_review/blocked/active与服务端一致，计划变化注明；token流速不当业务进度。"
    },
    {
      "id": "C26-03",
      "check": "同release/recipient/channel仅一条通知",
      "expected": "同release/recipient/channel仅一条通知；重放不会触发取消/采用等副作用。"
    },
    {
      "id": "C26-04",
      "check": "离线显示最后同步时间与数据可能过期，不能继续伪造采集动画或进度",
      "expected": "离线显示最后同步时间与数据可能过期，不能继续伪造采集动画或进度；跨项目响应不串入当前页。"
    },
    {
      "id": "C26-05",
      "check": "判断与停止状态的真实投影",
      "expected": "UI显示运行器声明与待验收/阻塞原因，不能显示产品已完成；账本/原文可定位；事件重放不重发判断、不重复计费或通知。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "实际输入/输出与命令、受控证据索引、逐项断言；界面项另保存指定视口截图与操作记录。",
    "H09重放输入、判断/执行事件、确定性检查与原始输出hash。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.ui.recovery"
  ],
  "final_owner_task": "W13"
}
```

### A01 · 隔离工作区与规格导入完整性

模式：FIXTURE；唯一最终负责人：W04；状态：NOT_RUN。

固定输入：

```json
{
  "initial_managed_project": "researchos_self",
  "unauthorized_external_project": "quillclub_or_xiaoshuo",
  "injected_fixture_file": true,
  "product_replays": {
    "B01": {
      "new_projects": 2,
      "reuse_across_projects": true,
      "unauthorized_roots": true,
      "inaccessible_root": true
    }
  }
}
```

完整合同：

```json
{
  "id": "A01",
  "title": "隔离工作区与规格导入完整性",
  "requirement_ids": [
    "R01",
    "R02",
    "R17",
    "R20"
  ],
  "wbs_ids": [
    "W00",
    "W04"
  ],
  "setup": [
    "新建空目录/隔离repo，无既有项目绑定、无凭据；规格包manifest和reference目录只读。"
  ],
  "input": {
    "initial_managed_project": "researchos_self",
    "unauthorized_external_project": "quillclub_or_xiaoshuo",
    "injected_fixture_file": true,
    "product_replays": {
      "B01": {
        "new_projects": 2,
        "reuse_across_projects": true,
        "unauthorized_roots": true,
        "inaccessible_root": true
      }
    }
  },
  "actions": [
    "校验包内引用和hash，导入本包为ResearchOS自身初始目标。",
    "分别篡改一个包文件、提供路径穿越与伪造历史授权。",
    "连续建立两个新项目，各自查看授权目录/依赖/工具/本地源码与可共享复用记录；注入不可访问和未授权目录。"
  ],
  "expected": [
    "新project_id独立，初始ProjectProfile区分用户事实/观察/假设/提案；未继承其他项目私有资料或权限。",
    "manifest hash不符、越界路径或伪造授权导致该导入拒绝，原状态不改变。",
    "文档/schema检查只产生status=PASS、scope=SPECIFICATION_PACKAGE_ONLY、product_tests=NOT_RUN，不产生任何产品测试PASS或上线许可。",
    "每个项目有独立能力清单、扫描范围、版本/hash和已找到/未找到/未检查/不可访问结果；本地盘点先于新增外部查询，不能把另一项目私有内容自动导入。 新会话ContextBundle引用同一版本的项目开工规则；W04只验初始化和本地阶段，不伪装后续研究已实现。"
  ],
  "assertions": [
    {
      "id": "A01-01",
      "check": "身份和来源",
      "expected": "新project_id独立，初始ProjectProfile区分用户事实/观察/假设/提案；未继承其他项目私有资料或权限。"
    },
    {
      "id": "A01-02",
      "check": "篡改拒绝",
      "expected": "manifest hash不符、越界路径或伪造授权导致该导入拒绝，原状态不改变。"
    },
    {
      "id": "A01-03",
      "check": "包检验边界",
      "expected": "文档/schema检查只产生status=PASS、scope=SPECIFICATION_PACKAGE_ONLY、product_tests=NOT_RUN，不产生任何产品测试PASS或上线许可。"
    },
    {
      "id": "A01-04",
      "check": "每新项目先本地盘点",
      "expected": "每个项目有独立能力清单、扫描范围、版本/hash和已找到/未找到/未检查/不可访问结果；本地盘点先于新增外部查询，不能把另一项目私有内容自动导入。 新会话ContextBundle引用同一版本的项目开工规则；W04只验初始化和本地阶段，不伪装后续研究已实现。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "新repo/工作区身份、导入产物hash、manifest结果、负例拒绝。",
    "B01实际客户端/项目初始化记录、输入版本、命令/事件与证据hash。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "package.validate",
    "test.context"
  ],
  "final_owner_task": "W04"
}
```

### A02 · 底座资格门与唯一调度路线

模式：LIVE_WINDOWS；唯一最终负责人：W06；状态：NOT_RUN。

固定输入：

```json
{
  "preferred_route": "mu_fork",
  "reuse_alternative": "pi_compose",
  "gap_route": "gap_only_compose",
  "maximum_reuse_routes": 2,
  "repairs_per_route": 1,
  "baseline_commit": "8dfebe36508ac0c2508735bb866756dab9283e74",
  "required_order": [
    "LOCAL_INVENTORY",
    "RESEARCH",
    "REUSE_DECISION",
    "IMPLEMENTATION"
  ]
}
```

完整合同：

```json
{
  "id": "A02",
  "title": "底座资格门与唯一调度路线",
  "requirement_ids": [
    "R10",
    "R12",
    "R17",
    "R20"
  ],
  "wbs_ids": [
    "W01",
    "W06"
  ],
  "setup": [
    "Windows11 x64隔离资格环境；已完成授权本地盘点并冻结Mu/Pi复用资格清单。",
    "W01资格样机、W06当前共享核心/CLI/桌面协议测试端分别记录；最终Desktop在W13/W14/W20完成，不要求其提前存在。"
  ],
  "input": {
    "preferred_route": "mu_fork",
    "reuse_alternative": "pi_compose",
    "gap_route": "gap_only_compose",
    "maximum_reuse_routes": 2,
    "repairs_per_route": 1,
    "baseline_commit": "8dfebe36508ac0c2508735bb866756dab9283e74",
    "required_order": [
      "LOCAL_INVENTORY",
      "RESEARCH",
      "REUSE_DECISION",
      "IMPLEMENTATION"
    ]
  },
  "actions": [
    "读取本地盘点、来源与候选比较；W06核对W01资格样机和当前共享核心/CLI/桌面协议测试端证据，最终Desktop在A13/A15复验。",
    "验证多个客户端并发接入同一任务、重复命令、取消/恢复、执行者自批及无证据自研反例。"
  ],
  "expected": [
    "route.json只有一个MU_FORK、PI_COMPOSE或经具体缺口证明的GAP_ONLY_COMPOSE；CLI/Desktop共享一个核心与状态权威。",
    "所选复用路线有真实Windows命令、资格样机与当前核心/CLI/桌面协议测试端回执；README或部署命令不通过。本例不提前证明最终Desktop，安装包/真实双端操作必须在A10/A13/A15通过。",
    "本地先于新增外部调研，复用路线最多两条、各一次针对性修复；自研按能力有缺口证据，不因资源不可用自动转从零实现。",
    "同一任务同时一个有效owner；CLI与Desktop不能分别直写ACCEPTED；重复控制/恢复不重复外部副作用。"
  ],
  "assertions": [
    {
      "id": "A02-01",
      "check": "路线唯一",
      "expected": "route.json只有一个MU_FORK、PI_COMPOSE或经具体缺口证明的GAP_ONLY_COMPOSE；CLI/Desktop共享一个核心与状态权威。"
    },
    {
      "id": "A02-02",
      "check": "资格不靠阅读",
      "expected": "所选复用路线有真实Windows命令、资格样机与当前核心/CLI/桌面协议测试端回执；README或部署命令不通过。本例不提前证明最终Desktop，安装包/真实双端操作必须在A10/A13/A15通过。"
    },
    {
      "id": "A02-03",
      "check": "受控回退",
      "expected": "本地先于新增外部调研，复用路线最多两条、各一次针对性修复；自研按能力有缺口证据，不因资源不可用自动转从零实现。"
    },
    {
      "id": "A02-04",
      "check": "幂等授权边界",
      "expected": "同一任务同时一个有效owner；CLI与Desktop不能分别直写ACCEPTED；重复控制/恢复不重复外部副作用。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "精确commit/依赖锁、资格运行日志、方案尝试/修复计数、ADR-001、route.json及唯一调度检查。"
  ],
  "mode": "LIVE_WINDOWS",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "core.qualify"
  ],
  "final_owner_task": "W06"
}
```

### A03 · 数据/API约束与事务并发

模式：FIXTURE；唯一最终负责人：W06；状态：NOT_RUN。

固定输入：

```json
{
  "bad_cases": [
    "float_money",
    "cap_zero_for_unlimited",
    "naive_timestamp",
    "invalid_state_transition",
    "unknown_project",
    "stale_revision",
    "same_key_different_payload",
    "hash_mismatch"
  ]
}
```

完整合同：

```json
{
  "id": "A03",
  "title": "数据/API约束与事务并发",
  "requirement_ids": [
    "R03",
    "R04",
    "R09",
    "R11",
    "R20"
  ],
  "wbs_ids": [
    "W02",
    "W03",
    "W06"
  ],
  "setup": [
    "选定路线已提供实际数据库和/v1适配API；按domain.schema.json/openapi.json构造有效与无效负例。"
  ],
  "input": {
    "bad_cases": [
      "float_money",
      "cap_zero_for_unlimited",
      "naive_timestamp",
      "invalid_state_transition",
      "unknown_project",
      "stale_revision",
      "same_key_different_payload",
      "hash_mismatch"
    ]
  },
  "actions": [
    "验证序列化往返、状态转换、If-Match、幂等键与outbox原子事务。",
    "对同aggregate并发更新；在业务写入/outbox提交中注入崩溃并重启。"
  ],
  "expected": [
    "金额不用float，UNLIMITED_AMOUNT的cap为null，时间RFC3339 UTC，revision>=1；无效输入不写入。",
    "过期If-Match返回412；其他状态/幂等冲突409；权限失败不泄露跨项目实体。",
    "业务写入及outbox同成同败；事件有稳定ID/顺序且消费者幂等；数据库和投影最终一致。",
    "AcceptanceReceipt绑定输入/规则/产物hash；任一不符不能将任务置ACCEPTED。"
  ],
  "assertions": [
    {
      "id": "A03-01",
      "check": "合同拒绝",
      "expected": "金额不用float，UNLIMITED_AMOUNT的cap为null，时间RFC3339 UTC，revision>=1；无效输入不写入。"
    },
    {
      "id": "A03-02",
      "check": "HTTP冲突",
      "expected": "过期If-Match返回412；其他状态/幂等冲突409；权限失败不泄露跨项目实体。"
    },
    {
      "id": "A03-03",
      "check": "事务与事件",
      "expected": "业务写入及outbox同成同败；事件有稳定ID/顺序且消费者幂等；数据库和投影最终一致。"
    },
    {
      "id": "A03-04",
      "check": "验收绑定",
      "expected": "AcceptanceReceipt绑定输入/规则/产物hash；任一不符不能将任务置ACCEPTED。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "合同向量、实际HTTP请求/响应、数据库前后快照、并发与故障注入回执。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "contracts.validate",
    "test.domain"
  ],
  "final_owner_task": "W06"
}
```

### A04 · 真实执行器生命周期与取消

模式：LIVE_WINDOWS；唯一最终负责人：W05；状态：NOT_RUN。

固定输入：

```json
{
  "subcases": [
    "success",
    "tool_failed",
    "request_timeout",
    "pending_queue_cancel",
    "executor_crash"
  ],
  "harness_replays": {
    "H08": {
      "nested_tool_cancel": true,
      "candidate_runtimes": [
        "pi",
        "mu"
      ],
      "fixed_agent_model": true,
      "selected_upstream_security_patches_preserved": true
    }
  },
  "product_replays": {
    "P01": {
      "own_binary": "researchos",
      "interactive": true,
      "headless_jsonl": true,
      "actions": [
        "read",
        "edit",
        "shell",
        "goal",
        "resume",
        "cancel"
      ]
    }
  },
  "delivery_replays": {
    "U02": {
      "journey_document": "17_USER_JOURNEYS_AND_VALUE.md",
      "real_issue": "ISSUE-CONTINUITY-001",
      "typed_protocol": "researchos-client/2",
      "manual_admin_commands_for_normal_use": 0,
      "old_PASS_is_new_PASS": false,
      "real_issue_selection_policy": "delivery.contract.json:first_real_coding_task_policy"
    }
  }
}
```

完整合同：

```json
{
  "id": "A04",
  "title": "真实执行器生命周期与取消",
  "requirement_ids": [
    "R10",
    "R12",
    "R17"
  ],
  "wbs_ids": [
    "W05"
  ],
  "setup": [
    "选一个可用真实执行器并固定版本；独立任务工作目录；本地无副作用工具子进程可控。"
  ],
  "input": {
    "subcases": [
      "success",
      "tool_failed",
      "request_timeout",
      "pending_queue_cancel",
      "executor_crash"
    ],
    "harness_replays": {
      "H08": {
        "nested_tool_cancel": true,
        "candidate_runtimes": [
          "pi",
          "mu"
        ],
        "fixed_agent_model": true,
        "selected_upstream_security_patches_preserved": true
      }
    },
    "product_replays": {
      "P01": {
        "own_binary": "researchos",
        "interactive": true,
        "headless_jsonl": true,
        "actions": [
          "read",
          "edit",
          "shell",
          "goal",
          "resume",
          "cancel"
        ]
      }
    },
    "delivery_replays": {
      "U02": {
        "journey_document": "17_USER_JOURNEYS_AND_VALUE.md",
        "real_issue": "ISSUE-CONTINUITY-001",
        "typed_protocol": "researchos-client/2",
        "manual_admin_commands_for_normal_use": 0,
        "old_PASS_is_new_PASS": false,
        "real_issue_selection_policy": "delivery.contract.json:first_real_coding_task_policy"
      }
    }
  },
  "actions": [
    "执行五个子场景并观察宿主状态。",
    "如采用Pi：验证agent_end后仍未settled及队列行为，按clear_queue→abort取消当前任务；仅关闭整个runtime时关闭stdin并检查进程退出。",
    "对实际选用运行器验证嵌套事件/费用/取消、失效租约与能力探针；尝试通过路由器改变用户固定模型。",
    "通过自己的已安装CLI，分别运行交互自然语言任务与非交互JSONL模式；真实模型执行读文件、改文件、测试和Goal。",
    "按17/18/19/22运行U02具体操作与反例，保存原始输出和对应客户端/构建/数据版本。"
  ],
  "expected": [
    "模型返回/CLI exit0/agent_end均不直接等于ACCEPTED；宿主等待实际settled/完整回执后进入EXECUTION_REPORTED再独立验收。",
    "取消后当前任务工具子进程停止、其待执行请求清空；保留长驻RPC进程允许，但其不得继续取消任务工作。",
    "记录可恢复状态，工作目录与凭据不交叉；不假定原生resume已支持，不能支持时由ContextBundle重建新会话。",
    "子运行关联parent/run/tool ID并服从同一取消和预算；未实现适配器明确不可用；实际版本矩阵可查；固定模型不被静默替换，已选上游安全补丁不因升级或移植丢失。",
    "CLI独立完成真实任务，支持流式工具/结果、会话恢复和取消；stdout结构化事件不混日志，失败/阻塞/取消使用明确非成功退出码；退出0不自动接受成果。",
    "自有researchos的交互/JSONL/init/run/goal/resume/status/cancel/doctor/config及斜杠入口有真实处理器；中文输入、流式工具、读改文件和测试完成，取消结清子进程，固定模型不静默更换。"
  ],
  "assertions": [
    {
      "id": "A04-01",
      "check": "完成语义",
      "expected": "模型返回/CLI exit0/agent_end均不直接等于ACCEPTED；宿主等待实际settled/完整回执后进入EXECUTION_REPORTED再独立验收。"
    },
    {
      "id": "A04-02",
      "check": "取消",
      "expected": "取消后当前任务工具子进程停止、其待执行请求清空；保留长驻RPC进程允许，但其不得继续取消任务工作。"
    },
    {
      "id": "A04-03",
      "check": "崩溃/超时",
      "expected": "记录可恢复状态，工作目录与凭据不交叉；不假定原生resume已支持，不能支持时由ContextBundle重建新会话。"
    },
    {
      "id": "A04-04",
      "check": "嵌套执行与版本兼容",
      "expected": "子运行关联parent/run/tool ID并服从同一取消和预算；未实现适配器明确不可用；实际版本矩阵可查；固定模型不被静默替换，已选上游安全补丁不因升级或移植丢失。"
    },
    {
      "id": "A04-05",
      "check": "自有CLI交互与自动化输出",
      "expected": "CLI独立完成真实任务，支持流式工具/结果、会话恢复和取消；stdout结构化事件不混日志，失败/阻塞/取消使用明确非成功退出码；退出0不自动接受成果。"
    },
    {
      "id": "A04-06",
      "check": "完整CLI真实编码任务",
      "expected": "自有researchos的交互/JSONL/init/run/goal/resume/status/cancel/doctor/config及斜杠入口有真实处理器；中文输入、流式工具、读改文件和测试完成，取消结清子进程，固定模型不静默更换。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "执行器版本、原始协议/JSONL、进程树前后、取消队列、失败与恢复回执。",
    "H08重放输入、判断/执行事件、确定性检查与原始输出hash。",
    "P01实际客户端/项目初始化记录、输入版本、命令/事件与证据hash。",
    "U02当前输入/构建/文件hash、操作回执、失败分支和独立复核；fixture与live分开。"
  ],
  "mode": "LIVE_WINDOWS",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.runtime"
  ],
  "final_owner_task": "W05"
}
```

### A05 · GitHub/X/论文真实来源与故障探针

模式：LIVE_SERVICE；唯一最终负责人：W07；状态：NOT_RUN。

固定输入：

```json
{
  "required_sources": [
    "github",
    "x",
    "papers"
  ],
  "positive_items_per_source_min": 1,
  "faults": [
    "not_configured",
    "429",
    "401_or_revoked",
    "timeout",
    "empty_valid_result"
  ],
  "harness_replays": {
    "H07": {
      "source_exit_code": 0,
      "source_status": "ok",
      "detail_error": "page_timeout",
      "x_backend_configured": false,
      "pr_states": [
        "open",
        "closed",
        "merged"
      ]
    }
  }
}
```

完整合同：

```json
{
  "id": "A05",
  "title": "GitHub/X/论文真实来源与故障探针",
  "requirement_ids": [
    "R05",
    "R06",
    "R11"
  ],
  "wbs_ids": [
    "W07"
  ],
  "setup": [
    "三个必需来源使用真实可用接口/渠道；凭据由用户已授权配置，取最小公开查询。",
    "缺任一来源账户/配额/访问能力则对应探针BLOCKED，整体本例BLOCKED；不得用fixture替代。"
  ],
  "input": {
    "required_sources": [
      "github",
      "x",
      "papers"
    ],
    "positive_items_per_source_min": 1,
    "faults": [
      "not_configured",
      "429",
      "401_or_revoked",
      "timeout",
      "empty_valid_result"
    ],
    "harness_replays": {
      "H07": {
        "source_exit_code": 0,
        "source_status": "ok",
        "detail_error": "page_timeout",
        "x_backend_configured": false,
        "pr_states": [
          "open",
          "closed",
          "merged"
        ]
      }
    }
  },
  "actions": [
    "每来源至少执行一次真实检索并抓取可定位原始项，记录实际查询窗口。",
    "独立故障测试使用明确标记的代理注入/测试账户，不伪造服务真实故障；验证错误映射。",
    "保留三源真实正例，再注入exit0且ok但分页超时，以及X未配置、仅搜索索引和PR关闭未合并结果。"
  ],
  "expected": [
    "三来源各至少一条可复核真实回执，记录URL/来源ID、作者、发布/采集时间、版本/commit、正文快照hash及cursor。",
    "X主张需关联一手材料；缺一手证据不得直接成采用依据。适配器实际窗口与请求窗口分别记录。",
    "空有效结果≠失败，缺配置/限流/失效密钥/超时分别记录；429遵守等待，失败不推进未完成游标。",
    "任何账户/服务缺失保持BLOCKED；不记录明文cookie/token，不以未经授权渠道绕过访问。",
    "未配置映射NOT_CONFIGURED；分页缺失映射PARTIAL；有效空结果为COMPLETE且数量0；来源健康保留原因/实际窗口/可访问范围，closed不误写merged，索引摘要不伪装已读原文。"
  ],
  "assertions": [
    {
      "id": "A05-01",
      "check": "真实覆盖",
      "expected": "三来源各至少一条可复核真实回执，记录URL/来源ID、作者、发布/采集时间、版本/commit、正文快照hash及cursor。"
    },
    {
      "id": "A05-02",
      "check": "线索核查",
      "expected": "X主张需关联一手材料；缺一手证据不得直接成采用依据。适配器实际窗口与请求窗口分别记录。"
    },
    {
      "id": "A05-03",
      "check": "故障分类",
      "expected": "空有效结果≠失败，缺配置/限流/失效密钥/超时分别记录；429遵守等待，失败不推进未完成游标。"
    },
    {
      "id": "A05-04",
      "check": "访问边界",
      "expected": "任何账户/服务缺失保持BLOCKED；不记录明文cookie/token，不以未经授权渠道绕过访问。"
    },
    {
      "id": "A05-05",
      "check": "来源部分成功与窗口",
      "expected": "未配置映射NOT_CONFIGURED；分页缺失映射PARTIAL；有效空结果为COMPLETE且数量0；来源健康保留原因/实际窗口/可访问范围，closed不误写merged，索引摘要不伪装已读原文。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "三来源脱敏实际请求/响应、引用快照、游标和时间窗、故障注入与真实访问分开的回执。",
    "H07重放输入、判断/执行事件、确定性检查与原始输出hash。"
  ],
  "mode": "LIVE_SERVICE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.sources.live"
  ],
  "final_owner_task": "W07"
}
```

### A06 · 检索权限、增量更新与缓存失效

模式：FIXTURE；唯一最终负责人：W09；状态：NOT_RUN。

固定输入：

```json
{
  "index_candidates": [
    "sirchmunk_if_enabled",
    "fts_or_rg_fallback"
  ],
  "updates": [
    "modify",
    "delete",
    "revoke_access",
    "move_outside_root"
  ]
}
```

完整合同：

```json
{
  "id": "A06",
  "title": "检索权限、增量更新与缓存失效",
  "requirement_ids": [
    "R03",
    "R06",
    "R17"
  ],
  "wbs_ids": [
    "W09"
  ],
  "setup": [
    "授权根目录A和未授权B含唯一标记；A存在v1、删除项和符号链接/Windows junction指向B；缓存预热。"
  ],
  "input": {
    "index_candidates": [
      "sirchmunk_if_enabled",
      "fts_or_rg_fallback"
    ],
    "updates": [
      "modify",
      "delete",
      "revoke_access",
      "move_outside_root"
    ]
  },
  "actions": [
    "检索预热后修改/删除/撤销权限，再用旧查询和缓存重试。",
    "尝试路径穿越、链接越界；停用候选检索器验证fallback。"
  ],
  "expected": [
    "新ContextBundle不包含已删除/撤权正文；旧证据仅以STALE/REVOKED元数据保留，不作为CURRENT支持。",
    "解析后实际路径必须仍在授权根内，链接/junction不能绕过；B秘密标记泄漏为0。",
    "可选检索器失败时FTS/rg等选定fallback返回同授权范围可定位结果；缓存键绑定项目/权限/内容版本。"
  ],
  "assertions": [
    {
      "id": "A06-01",
      "check": "当前有效性",
      "expected": "新ContextBundle不包含已删除/撤权正文；旧证据仅以STALE/REVOKED元数据保留，不作为CURRENT支持。"
    },
    {
      "id": "A06-02",
      "check": "路径安全",
      "expected": "解析后实际路径必须仍在授权根内，链接/junction不能绕过；B秘密标记泄漏为0。"
    },
    {
      "id": "A06-03",
      "check": "可用回退",
      "expected": "可选检索器失败时FTS/rg等选定fallback返回同授权范围可定位结果；缓存键绑定项目/权限/内容版本。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "文件/权限版本hash、查询与缓存命中记录、越界负例、fallback真实回执。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.retrieval",
    "test.security"
  ],
  "final_owner_task": "W09"
}
```

### A07 · 冻结实验、负结果与无法确定

模式：FIXTURE；唯一最终负责人：W10；状态：NOT_RUN。

固定输入：

```json
{
  "result_variants": [
    "positive",
    "negative",
    "null",
    "inconclusive"
  ],
  "attempted_posthoc_change": true
}
```

完整合同：

```json
{
  "id": "A07",
  "title": "冻结实验、负结果与无法确定",
  "requirement_ids": [
    "R07",
    "R09",
    "R20"
  ],
  "wbs_ids": [
    "W10"
  ],
  "setup": [
    "同一数据/环境可运行基线及候选；冻结指标定义、输入、资源边界、成功/失败条件和分析方法。"
  ],
  "input": {
    "result_variants": [
      "positive",
      "negative",
      "null",
      "inconclusive"
    ],
    "attempted_posthoc_change": true
  },
  "actions": [
    "分别执行四种结果fixture；注入结果后调低门槛和删除失败样本的提案。",
    "让独立验证器重算指标并检查未执行实验。"
  ],
  "expected": [
    "执行开始时间晚于预注册冻结时间；输入/基线/规则hash都匹配；事后更改必须新实验ID，不替换本轮。",
    "四种结果分别保留实际值和结论；null/负结果可完成实验；缺必要数据标INCONCLUSIVE，不捏造收益。",
    "原始观测可重算到报告值；超预算/范围/时长按策略停止并记录；未运行状态保持NOT_RUN/BLOCKED。"
  ],
  "assertions": [
    {
      "id": "A07-01",
      "check": "事前注册",
      "expected": "执行开始时间晚于预注册冻结时间；输入/基线/规则hash都匹配；事后更改必须新实验ID，不替换本轮。"
    },
    {
      "id": "A07-02",
      "check": "结果诚实",
      "expected": "四种结果分别保留实际值和结论；null/负结果可完成实验；缺必要数据标INCONCLUSIVE，不捏造收益。"
    },
    {
      "id": "A07-03",
      "check": "重算与边界",
      "expected": "原始观测可重算到报告值；超预算/范围/时长按策略停止并记录；未运行状态保持NOT_RUN/BLOCKED。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "预注册记录、基线与候选原始输出、计算回执、四类结论及事后改规则拒绝。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.experiments"
  ],
  "final_owner_task": "W10"
}
```

### A08 · Jev中文与混合语言冻结留出评测

模式：LIVE_SERVICE；唯一最终负责人：W11；状态：NOT_RUN。

固定输入：

```json
{
  "critical_false_accepts_max": 0,
  "total_false_accept_rate_max": 0.05,
  "qualification_key": [
    "task_type",
    "language",
    "provider",
    "model_revision",
    "rubric_revision"
  ],
  "holdout_content": [
    "valid_positive",
    "missing_evidence",
    "conflicting_evidence",
    "prompt_injection",
    "numerical_or_date_hard_constraint",
    "unsafe_or_unqualified_adoption"
  ],
  "initial_evaluation_minimum_development_cases": 60,
  "initial_evaluation_minimum_total_labeled_cases": 90,
  "initial_evaluation_minimum_holdout_cases": 30,
  "initial_evaluation_minimum_holdout_per_language": 15,
  "auto_qualification_per_key": {
    "minimum_development_cases": 60,
    "minimum_disjoint_holdout_cases": 30,
    "critical_false_accepts_max": 0,
    "false_accept_count_over_holdout_count_max": 0.05
  },
  "harness_replays": {
    "H06": {
      "decision_points": [
        "tool.admission",
        "goal.continue",
        "memory.worth",
        "model.route"
      ],
      "cross_scope_transfer_attempt": true,
      "judge_cost_unknown": true
    }
  },
  "adoption_replays": {
    "J02": {
      "task_type": "reuse_selection",
      "negative_cases": [
        "platform_mismatch",
        "license_unknown",
        "no_benefit",
        "readme_injection",
        "missing_evidence"
      ],
      "cross_scope_qualification": true
    }
  }
}
```

完整合同：

```json
{
  "id": "A08",
  "title": "Jev中文与混合语言冻结留出评测",
  "requirement_ids": [
    "R08",
    "R09",
    "R20"
  ],
  "wbs_ids": [
    "W11"
  ],
  "setup": [
    "真实Jev账户可用；每个申请自动化的task_type独立评估，不把一种用途资格扩展到全部。",
    "初轮评测开发/校准集至少60条，另设独立holdout至少30条，总计至少90条；中文/中英混合均衡，holdout两种语言各至少15条，按来源族/同义改写严格隔离。这只是初轮评测规模。",
    "每个拟启用BOUNDED_AUTO的task_type×language×provider×model_revision×rubric_revision键，必须各有至少60条开发样例＋30条独立holdout，并各自满足冻结错误门槛；双语言两个键都晋升至少各90条，即至少180条。样本不足或未测键保持ADVISORY/SHADOW，聚合结果不授予资格。",
    "标签来自可重算客观结果或可追溯独立人工标注；模型共识不能单独作为真值；冻结样本、标签、rubric、阈值hash后再调用。",
    "正式留出输入、标签、逐例结果与详细日志处于Verifier隔离环境；公开目录仅有不泄题的EvaluationSummary。"
  ],
  "input": {
    "critical_false_accepts_max": 0,
    "total_false_accept_rate_max": 0.05,
    "qualification_key": [
      "task_type",
      "language",
      "provider",
      "model_revision",
      "rubric_revision"
    ],
    "holdout_content": [
      "valid_positive",
      "missing_evidence",
      "conflicting_evidence",
      "prompt_injection",
      "numerical_or_date_hard_constraint",
      "unsafe_or_unqualified_adoption"
    ],
    "initial_evaluation_minimum_development_cases": 60,
    "initial_evaluation_minimum_total_labeled_cases": 90,
    "initial_evaluation_minimum_holdout_cases": 30,
    "initial_evaluation_minimum_holdout_per_language": 15,
    "auto_qualification_per_key": {
      "minimum_development_cases": 60,
      "minimum_disjoint_holdout_cases": 30,
      "critical_false_accepts_max": 0,
      "false_accept_count_over_holdout_count_max": 0.05
    },
    "harness_replays": {
      "H06": {
        "decision_points": [
          "tool.admission",
          "goal.continue",
          "memory.worth",
          "model.route"
        ],
        "cross_scope_transfer_attempt": true,
        "judge_cost_unknown": true
      }
    },
    "adoption_replays": {
      "J02": {
        "task_type": "reuse_selection",
        "negative_cases": [
          "platform_mismatch",
          "license_unknown",
          "no_benefit",
          "readme_injection",
          "missing_evidence"
        ],
        "cross_scope_qualification": true
      }
    }
  },
  "actions": [
    "仅开发集调提示/rubric，冻结后对完整holdout真实调用Jev。",
    "计算每语言/用途及总体错误采信、漏选、弃权、延迟、费用、确定性基线对照；验证超时和模型revision改变时降级。",
    "资格不满足则保存失败结果、保持ADVISORY/SHADOW并验证确定性门和补证路径；重新调优需要新的未泄露holdout。",
    "在真实用途评测中记录每次判断及回退；尝试把上下文筛选资格转给完成判断、授权或模型路由。",
    "真实调用reuse_selection并按A08冻结留出评测；注入不兼容平台、缺许可、负收益、恶意README，尝试借用其他用途资格并模拟超时/弃权。"
  ],
  "expected": [
    "holdout内容/标签未送入调优过程；样本源族不跨集合；模型revision、rubric、语言和用途键完整。",
    "每个申请自动化的完整资格键分别满足开发>=60、独立holdout>=30、critical_false_accepts=0、false_accepts/该键holdout_count<=0.05；不得以跨语言/跨用途聚合均值授予键资格。样本不足或有严重错误的键不晋升。",
    "报告false_accepts/negative_label_count及自动动作覆盖率；全弃权/无可验证自动动作样本不获得BOUNDED_AUTO；不将低置信强制转正例。",
    "完整真实评测和安全降级可使本用例PASS，即使qualification=FAILED；qualification未通过时对应BOUNDED_AUTO必须关闭并在交付说明披露。缺真实调用/独立标签则本用例BLOCKED。",
    "即便资格通过，缺证据/程序测试失败/版本冲突仍拒绝ACCEPTED；模型输出不是现实成功概率。",
    "Artifact.access_class和实际权限隔离一致；详细结果导出不能泄题，候选无法通过共享日志/文件/预览获得留出反馈。",
    "逐条可追溯decision point/模式/输入hash/provider/model/rubric/输出/实际动作/弃权/耗时/费用；未知费用为null；资格不能跨用途继承，judge不能授权、验收或发布。",
    "reuse_selection按完整用途/语言/provider/model/rubric独立记录真实结果；未合格保持SHADOW/ADVISORY，缺调用BLOCKED；超时/弃权不伪造采纳，硬检查/独立审查可继续，其他用途资格不可迁移。"
  ],
  "assertions": [
    {
      "id": "A08-01",
      "check": "冻结和独立性",
      "expected": "holdout内容/标签未送入调优过程；样本源族不跨集合；模型revision、rubric、语言和用途键完整。"
    },
    {
      "id": "A08-02",
      "check": "资格硬门",
      "expected": "每个申请自动化的完整资格键分别满足开发>=60、独立holdout>=30、critical_false_accepts=0、false_accepts/该键holdout_count<=0.05；不得以跨语言/跨用途聚合均值授予键资格。样本不足或有严重错误的键不晋升。"
    },
    {
      "id": "A08-03",
      "check": "弃权防伪",
      "expected": "报告false_accepts/negative_label_count及自动动作覆盖率；全弃权/无可验证自动动作样本不获得BOUNDED_AUTO；不将低置信强制转正例。"
    },
    {
      "id": "A08-04",
      "check": "资格与产品验收分离",
      "expected": "完整真实评测和安全降级可使本用例PASS，即使qualification=FAILED；qualification未通过时对应BOUNDED_AUTO必须关闭并在交付说明披露。缺真实调用/独立标签则本用例BLOCKED。"
    },
    {
      "id": "A08-05",
      "check": "独立最终验收",
      "expected": "即便资格通过，缺证据/程序测试失败/版本冲突仍拒绝ACCEPTED；模型输出不是现实成功概率。"
    },
    {
      "id": "A08-06",
      "check": "留出结果隔离",
      "expected": "Artifact.access_class和实际权限隔离一致；详细结果导出不能泄题，候选无法通过共享日志/文件/预览获得留出反馈。"
    },
    {
      "id": "A08-07",
      "check": "判断账本、费用与用途资格",
      "expected": "逐条可追溯decision point/模式/输入hash/provider/model/rubric/输出/实际动作/弃权/耗时/费用；未知费用为null；资格不能跨用途继承，judge不能授权、验收或发布。"
    },
    {
      "id": "A08-08",
      "check": "Jev源码选型的独立资格",
      "expected": "reuse_selection按完整用途/语言/provider/model/rubric独立记录真实结果；未合格保持SHADOW/ADVISORY，缺调用BLOCKED；超时/弃权不伪造采纳，硬检查/独立审查可继续，其他用途资格不可迁移。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "不含凭据的真实服务回执、冻结split及标签hash、标注来源、逐条混淆表/严重性、弃权/费用/延迟和基线报告、资格及降级回执。",
    "H06重放输入、判断/执行事件、确定性检查与原始输出hash。",
    "J02冻结候选/输入/判据、来源及实际模式、原始输出、独立检查与动作回执。"
  ],
  "mode": "LIVE_SERVICE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.jev.live"
  ],
  "final_owner_task": "W11"
}
```

### A09 · 资料到技能的覆盖与晋升

模式：FIXTURE；唯一最终负责人：W15；状态：NOT_RUN。

固定输入：

```json
{
  "expected_source_count": 4,
  "extractor_success_count": 3,
  "extractor_exit_code": 0,
  "source_conflict": true,
  "prompt_injection": true,
  "adoption_replays": {
    "J04": {
      "candidate_engine": "SKILL_UP",
      "variants": [
        "without_skill",
        "stable_skill",
        "candidate_skill"
      ],
      "mutated_acceptance": true,
      "missing_duplicate_skip": true
    }
  }
}
```

完整合同：

```json
{
  "id": "A09",
  "title": "资料到技能的覆盖与晋升",
  "requirement_ids": [
    "R06",
    "R15",
    "R16"
  ],
  "wbs_ids": [
    "W15"
  ],
  "setup": [
    "源清单固定四份文档，含一份抽取失败、一组互相矛盾建议及一段提示注入。",
    "技能候选在隔离版本目录；固定已有技能回归集。"
  ],
  "input": {
    "expected_source_count": 4,
    "extractor_success_count": 3,
    "extractor_exit_code": 0,
    "source_conflict": true,
    "prompt_injection": true,
    "adoption_replays": {
      "J04": {
        "candidate_engine": "SKILL_UP",
        "variants": [
          "without_skill",
          "stable_skill",
          "candidate_skill"
        ],
        "mutated_acceptance": true,
        "missing_duplicate_skip": true
      }
    }
  },
  "actions": [
    "运行导入/提炼流程并对照expected-source manifest。",
    "生成候选技能，保留冲突和来源；尝试将生成文件直接晋升；随后修复缺口并走独立评测。",
    "有限验证固定skill-up，按W10合同导入原始报告；固定输入分别比较无技能、旧技能和候选技能，注入退化、缺例、重复、SKIP与修改测试自证。"
  ],
  "expected": [
    "即使exit0且SKILL.md存在，4份中仅3份成功必须标PARTIAL；不能省略失败来源后宣称完整。",
    "每条可操作知识可回溯来源版本；矛盾建议明确列出适用条件或未决，不覆盖项目权威事实。",
    "生成/扫描器通过不等于可信；候选需固定回归与注入负例通过，独立验收后启用；失败保持旧技能。",
    "外部文档的指令不能修改宿主权限、密钥、验收门或全局配置。",
    "skill-up通过才采用，否则有证据拒绝并用既有后端完成同一冻结验收；缺资源保持阻塞；variant/iteration完整对账，零断言或exit0不判成功，正式门/holdout不让候选修改，退化保持旧技能。"
  ],
  "assertions": [
    {
      "id": "A09-01",
      "check": "覆盖完整",
      "expected": "即使exit0且SKILL.md存在，4份中仅3份成功必须标PARTIAL；不能省略失败来源后宣称完整。"
    },
    {
      "id": "A09-02",
      "check": "来源/冲突",
      "expected": "每条可操作知识可回溯来源版本；矛盾建议明确列出适用条件或未决，不覆盖项目权威事实。"
    },
    {
      "id": "A09-03",
      "check": "晋升门",
      "expected": "生成/扫描器通过不等于可信；候选需固定回归与注入负例通过，独立验收后启用；失败保持旧技能。"
    },
    {
      "id": "A09-04",
      "check": "权限",
      "expected": "外部文档的指令不能修改宿主权限、密钥、验收门或全局配置。"
    },
    {
      "id": "A09-05",
      "check": "技能评测后端的资格及退化拒绝",
      "expected": "skill-up通过才采用，否则有证据拒绝并用既有后端完成同一冻结验收；缺资源保持阻塞；variant/iteration完整对账，零断言或exit0不判成功，正式门/holdout不让候选修改，退化保持旧技能。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "源清单hash、逐源抽取回执、缺失对账、候选diff、技能评测及启用/拒绝记录。",
    "J04冻结候选/输入/判据、来源及实际模式、原始输出、独立检查与动作回执。"
  ],
  "mode": "FIXTURE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.skills"
  ],
  "final_owner_task": "W15"
}
```

### A10 · 真实Windows Desktop与手机监督可用性

模式：LIVE_WINDOWS；唯一最终负责人：W17；状态：NOT_RUN。

固定输入：

```json
{
  "views": [
    "sidebar",
    "cycle_detail",
    "evidence",
    "resource_request",
    "milestone",
    "pause_resume_cancel"
  ],
  "zoom_percent": 200,
  "delivery_replays": {
    "U01": {
      "journey_document": "17_USER_JOURNEYS_AND_VALUE.md",
      "real_issue": "ISSUE-FIRST-USE-001",
      "typed_protocol": "researchos-client/2",
      "manual_admin_commands_for_normal_use": 0,
      "old_PASS_is_new_PASS": false,
      "real_issue_selection_policy": "delivery.contract.json:first_real_coding_task_policy"
    }
  }
}
```

完整合同：

```json
{
  "id": "A10",
  "title": "真实Windows Desktop与手机监督可用性",
  "requirement_ids": [
    "R13",
    "R14",
    "R19"
  ],
  "wbs_ids": [
    "W13",
    "W17"
  ],
  "setup": [
    "Windows11真实浏览器和一个真实手机浏览器或明确记录的远程手机监督设备；桌面1440×900、窄屏390×844为基准；不同实机尺寸记录。",
    "使用发行候选ResearchOS Desktop安装包在Windows启动真实桌面进程；浏览器只用于手机监督补充。"
  ],
  "input": {
    "views": [
      "sidebar",
      "cycle_detail",
      "evidence",
      "resource_request",
      "milestone",
      "pause_resume_cancel"
    ],
    "zoom_percent": 200,
    "delivery_replays": {
      "U01": {
        "journey_document": "17_USER_JOURNEYS_AND_VALUE.md",
        "real_issue": "ISSUE-FIRST-USE-001",
        "typed_protocol": "researchos-client/2",
        "manual_admin_commands_for_normal_use": 0,
        "old_PASS_is_new_PASS": false,
        "real_issue_selection_policy": "delivery.contract.json:first_real_coding_task_policy"
      }
    }
  },
  "actions": [
    "用键盘和屏幕阅读器可达名称检查关键操作，实际手机完成查看/暂停/恢复/取消。",
    "200%缩放、网络断线重连、长中文/空态/错误态/计划变更逐项检查。",
    "按17/18/19/22运行U01具体操作与反例，保存原始输出和对应客户端/构建/数据版本。"
  ],
  "expected": [
    "六阶段/实际计数/覆盖缺口/阻塞原因可读；手机抽屉不遮挡永久无法关闭；关键操作有名称且可键盘触达。",
    "基准窄屏关键正文及操作无必须横向滚动才能到达的遮挡；焦点可见、顺序合理、无键盘陷阱。",
    "等待/失败/只读/过期数据明确标记；点击暂停/取消显示服务端实际回执，不凭动画假成功。",
    "自动accessibility检查加人工操作回执；无高严重性访问障碍，发现的问题附定位及修复/未过门结论。",
    "干净Windows用户通过安装包选择目录、配置已有模型、进入真实会话并跨15分钟重开；不执行内部管理命令、不复制Owner token；受信本机身份及短会话续接有效，普通renderer不能创建Owner。"
  ],
  "assertions": [
    {
      "id": "A10-01",
      "check": "内容和操作",
      "expected": "六阶段/实际计数/覆盖缺口/阻塞原因可读；手机抽屉不遮挡永久无法关闭；关键操作有名称且可键盘触达。"
    },
    {
      "id": "A10-02",
      "check": "布局",
      "expected": "基准窄屏关键正文及操作无必须横向滚动才能到达的遮挡；焦点可见、顺序合理、无键盘陷阱。"
    },
    {
      "id": "A10-03",
      "check": "状态和反馈",
      "expected": "等待/失败/只读/过期数据明确标记；点击暂停/取消显示服务端实际回执，不凭动画假成功。"
    },
    {
      "id": "A10-04",
      "check": "独立检查",
      "expected": "自动accessibility检查加人工操作回执；无高严重性访问障碍，发现的问题附定位及修复/未过门结论。"
    },
    {
      "id": "A10-05",
      "check": "无需手工token的首次使用",
      "expected": "干净Windows用户通过安装包选择目录、配置已有模型、进入真实会话并跨15分钟重开；不执行内部管理命令、不复制Owner token；受信本机身份及短会话续接有效，普通renderer不能创建Owner。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "设备/浏览器版本、桌面/手机截图或录屏、键盘流程、可访问性检查原始结果和状态回执。",
    "U01当前输入/构建/文件hash、操作回执、失败分支和独立复核；fixture与live分开。"
  ],
  "mode": "LIVE_WINDOWS",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.ui",
    "test.security"
  ],
  "final_owner_task": "W17"
}
```

### A11 · 密钥保护、设备配对与撤销

模式：LIVE_WINDOWS；唯一最终负责人：W17；状态：NOT_RUN。

固定输入：

```json
{
  "attacks": [
    "expired_pairing_code",
    "reused_pairing_code",
    "unauthenticated_api",
    "cross_project_access",
    "revoked_device",
    "log_secret_leak"
  ],
  "product_replays": {
    "P04": {
      "untrusted_preview_ipc": true,
      "invalid_sender": true,
      "path_traversal": true,
      "local_port_without_auth": true
    }
  }
}
```

完整合同：

```json
{
  "id": "A11",
  "title": "密钥保护、设备配对与撤销",
  "requirement_ids": [
    "R17",
    "R19"
  ],
  "wbs_ids": [
    "W17"
  ],
  "setup": [
    "Windows主机与真实远程浏览器，使用正式选定认证/传输方式；测试密钥含可追踪假标记，真密钥不输出。"
  ],
  "input": {
    "attacks": [
      "expired_pairing_code",
      "reused_pairing_code",
      "unauthenticated_api",
      "cross_project_access",
      "revoked_device",
      "log_secret_leak"
    ],
    "product_replays": {
      "P04": {
        "untrusted_preview_ipc": true,
        "invalid_sender": true,
        "path_traversal": true,
        "local_port_without_auth": true
      }
    }
  },
  "actions": [
    "完成一次实际设备配对，检查会话权限及传输保护。",
    "执行六类负例；保持事件流在线时撤销设备，再发读写请求。",
    "从不可信预览、外部导航及伪造renderer向宿主发送命令，尝试越界路径和未认证本地服务访问。"
  ],
  "expected": [
    "配对码单次、短时有效且只授予定义范围；过期/重复/无认证请求拒绝。",
    "撤销后下一认证API请求拒绝；已连事件流在30秒内断开；敏感写每次校验撤销状态。",
    "已保存token/cookie/密码不在UI明文回显，也不进入提示词、导出、日志和产物；首次设置的受控掩码输入短时处理并清除；进程/文件权限按角色限定。",
    "远程通信必须使用已验证TLS或受认证加密通道；无明文公网管理入口；默认不扩大开放端口。",
    "宿主验证sender/frame、项目范围、协议与参数；不可信内容没有通用shell/fs/密钥API；本地传输鉴权，已保存凭据不回传renderer；首次设置仅受控掩码输入并及时清除，秘密不进日志/会话；正常CLI/Desktop可用。"
  ],
  "assertions": [
    {
      "id": "A11-01",
      "check": "配对约束",
      "expected": "配对码单次、短时有效且只授予定义范围；过期/重复/无认证请求拒绝。"
    },
    {
      "id": "A11-02",
      "check": "撤销生效",
      "expected": "撤销后下一认证API请求拒绝；已连事件流在30秒内断开；敏感写每次校验撤销状态。"
    },
    {
      "id": "A11-03",
      "check": "秘密隔离",
      "expected": "已保存token/cookie/密码不在UI明文回显，也不进入提示词、导出、日志和产物；首次设置的受控掩码输入短时处理并清除；进程/文件权限按角色限定。"
    },
    {
      "id": "A11-04",
      "check": "远程保护",
      "expected": "远程通信必须使用已验证TLS或受认证加密通道；无明文公网管理入口；默认不扩大开放端口。"
    },
    {
      "id": "A11-05",
      "check": "桌面IPC和凭据边界",
      "expected": "宿主验证sender/frame、项目范围、协议与参数；不可信内容没有通用shell/fs/密钥API；本地传输鉴权，已保存凭据不回传renderer；首次设置仅受控掩码输入并及时清除，秘密不进日志/会话；正常CLI/Desktop可用。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "脱敏配对/认证日志、撤销时间线、传输配置与验证、秘密标记扫描、授权矩阵。",
    "P04实际客户端/项目初始化记录、输入版本、命令/事件与证据hash。"
  ],
  "mode": "LIVE_WINDOWS",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.security"
  ],
  "final_owner_task": "W17"
}
```

### A12 · 备份恢复与迁移失败回退

模式：LIVE_WINDOWS；唯一最终负责人：W18；状态：NOT_RUN。

固定输入：

```json
{
  "restore_target": "clean_isolated_workspace",
  "failure_migration": true,
  "backup_consistency": "database_plus_artifact_manifest",
  "delivery_replays": {
    "U06": {
      "journey_document": "17_USER_JOURNEYS_AND_VALUE.md",
      "real_issue": "ISSUE-REUSE-001",
      "typed_protocol": "researchos-client/2",
      "manual_admin_commands_for_normal_use": 0,
      "old_PASS_is_new_PASS": false,
      "real_issue_selection_policy": "delivery.contract.json:first_real_coding_task_policy"
    }
  }
}
```

完整合同：

```json
{
  "id": "A12",
  "title": "备份恢复与迁移失败回退",
  "requirement_ids": [
    "R03",
    "R12",
    "R18"
  ],
  "wbs_ids": [
    "W18"
  ],
  "setup": [
    "实际选定数据库含两个项目、上下文、费用/预留、游标、outbox、验收和产物引用；备份保存到独立位置。",
    "迁移前保存DB版本及产物manifest，准备一个故意失败的隔离迁移。"
  ],
  "input": {
    "restore_target": "clean_isolated_workspace",
    "failure_migration": true,
    "backup_consistency": "database_plus_artifact_manifest",
    "delivery_replays": {
      "U06": {
        "journey_document": "17_USER_JOURNEYS_AND_VALUE.md",
        "real_issue": "ISSUE-REUSE-001",
        "typed_protocol": "researchos-client/2",
        "manual_admin_commands_for_normal_use": 0,
        "old_PASS_is_new_PASS": false,
        "real_issue_selection_policy": "delivery.contract.json:first_real_coding_task_policy"
      }
    }
  },
  "actions": [
    "在有活动只读/受控写任务时生成一致性备份，停止后恢复到空工作区。",
    "核验引用/hash、重放待发事件；执行失败迁移并恢复前版。",
    "按17/18/19/22运行U06具体操作与反例，保存原始输出和对应客户端/构建/数据版本。"
  ],
  "expected": [
    "项目/任务ID、revision、费用ledger、游标、验收关系与备份点一致；每个current产物hash存在且可读。",
    "恢复后不盲重放外部动作；先对账，重复通知逻辑数不增加；未完成任务从检查点恢复。",
    "失败迁移不会破坏稳定备份；不可逆迁移必须阻止自动晋升或进入明确维护方案，不能假称可热回退。",
    "记录实际备份点、恢复耗时、数据差异和恢复命令；不能仅证明备份文件存在。",
    "保留ResearchOS永久身份、旧规格/回执和用户文件；在备份副本验证旧版到目标版及失败回退；旧PASS逐断言核对，新增CLI/Desktop/协议断言不继承；原有效数据不被静默覆盖。"
  ],
  "assertions": [
    {
      "id": "A12-01",
      "check": "恢复完整",
      "expected": "项目/任务ID、revision、费用ledger、游标、验收关系与备份点一致；每个current产物hash存在且可读。"
    },
    {
      "id": "A12-02",
      "check": "副作用保护",
      "expected": "恢复后不盲重放外部动作；先对账，重复通知逻辑数不增加；未完成任务从检查点恢复。"
    },
    {
      "id": "A12-03",
      "check": "迁移策略",
      "expected": "失败迁移不会破坏稳定备份；不可逆迁移必须阻止自动晋升或进入明确维护方案，不能假称可热回退。"
    },
    {
      "id": "A12-04",
      "check": "恢复可审计",
      "expected": "记录实际备份点、恢复耗时、数据差异和恢复命令；不能仅证明备份文件存在。"
    },
    {
      "id": "A12-05",
      "check": "既有项目迁移与证据分级",
      "expected": "保留ResearchOS永久身份、旧规格/回执和用户文件；在备份副本验证旧版到目标版及失败回退；旧PASS逐断言核对，新增CLI/Desktop/协议断言不继承；原有效数据不被静默覆盖。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "备份/恢复命令及hash、前后实体计数与关键字段比对、失败迁移日志、对账和健康回执。",
    "U06当前输入/构建/文件hash、操作回执、失败分支和独立复核；fixture与live分开。"
  ],
  "mode": "LIVE_WINDOWS",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.backup"
  ],
  "final_owner_task": "W18"
}
```

### A13 · 首个真实项目完整研究周期

模式：LIVE_WINDOWS_AND_SERVICE；唯一最终负责人：W14；状态：NOT_RUN。

固定输入：

```json
{
  "managed_project": "researchos_self",
  "mandatory_sources": [
    "github",
    "x",
    "papers"
  ],
  "minimum_real_bounded_experiments": 1,
  "product_replays": {
    "P06": {
      "entry": "cli",
      "continue_in": "desktop",
      "return_to": "cli",
      "project_bootstrap_required": true
    }
  },
  "adoption_replays": {
    "J03": {
      "real_source_snapshot": true,
      "real_jev_required": true,
      "isolated_adaptation": true,
      "force_adopt": false
    }
  },
  "delivery_replays": {
    "U03": {
      "journey_document": "17_USER_JOURNEYS_AND_VALUE.md",
      "real_issue": "ISSUE-REUSE-001",
      "typed_protocol": "researchos-client/2",
      "manual_admin_commands_for_normal_use": 0,
      "old_PASS_is_new_PASS": false,
      "real_issue_selection_policy": "delivery.contract.json:first_real_coding_task_policy"
    },
    "U07": {
      "journey_document": "17_USER_JOURNEYS_AND_VALUE.md",
      "real_issue": "ISSUE-REUSE-001",
      "typed_protocol": "researchos-client/2",
      "manual_admin_commands_for_normal_use": 0,
      "old_PASS_is_new_PASS": false,
      "real_issue_selection_policy": "delivery.contract.json:first_real_coding_task_policy"
    }
  }
}
```

完整合同：

```json
{
  "id": "A13",
  "title": "首个真实项目完整研究周期",
  "requirement_ids": [
    "R01",
    "R02",
    "R05",
    "R06",
    "R07",
    "R08",
    "R09",
    "R13",
    "R14",
    "R20"
  ],
  "wbs_ids": [
    "W14"
  ],
  "setup": [
    "默认受管理项目为本包创建的ResearchOS自身；导入该新repo的实际状态和一个具体未解决问题。其他项目须独立授权导入。",
    "GitHub、X、论文来源与真实执行器/Jev可用；预先冻结问题、来源窗口、实验与处置标准。"
  ],
  "input": {
    "managed_project": "researchos_self",
    "mandatory_sources": [
      "github",
      "x",
      "papers"
    ],
    "minimum_real_bounded_experiments": 1,
    "product_replays": {
      "P06": {
        "entry": "cli",
        "continue_in": "desktop",
        "return_to": "cli",
        "project_bootstrap_required": true
      }
    },
    "adoption_replays": {
      "J03": {
        "real_source_snapshot": true,
        "real_jev_required": true,
        "isolated_adaptation": true,
        "force_adopt": false
      }
    },
    "delivery_replays": {
      "U03": {
        "journey_document": "17_USER_JOURNEYS_AND_VALUE.md",
        "real_issue": "ISSUE-REUSE-001",
        "typed_protocol": "researchos-client/2",
        "manual_admin_commands_for_normal_use": 0,
        "old_PASS_is_new_PASS": false,
        "real_issue_selection_policy": "delivery.contract.json:first_real_coding_task_policy"
      },
      "U07": {
        "journey_document": "17_USER_JOURNEYS_AND_VALUE.md",
        "real_issue": "ISSUE-REUSE-001",
        "typed_protocol": "researchos-client/2",
        "manual_admin_commands_for_normal_use": 0,
        "old_PASS_is_new_PASS": false,
        "real_issue_selection_policy": "delivery.contract.json:first_real_coding_task_policy"
      }
    }
  },
  "actions": [
    "从一句目标开始，系统生成GoalBrief并读取当前上下文，执行三来源研究、原始材料核验与至少一个实际有界实验。",
    "独立验收后形成ADOPT/REJECT/WATCH/INCONCLUSIVE，更新当前状态、后续任务、侧栏和有价值的成果版本。",
    "启动全新Agent会话接续下一步，核对无需用户补述已有背景。",
    "使用CLI建立新项目，按本地→调研→复用决策推进真实研究和有界实验；Desktop查看文件/diff并暂停，再由CLI恢复与提交验收。",
    "对真实问题完成源码候选调查、固定commit、真实Jev建议，在隔离分支改造原代码或模块并运行同输入基线/候选测试；CLI/Desktop接续查看决定和产物。",
    "按17/18/19/22运行U03具体操作与反例，保存原始输出和对应客户端/构建/数据版本。",
    "按17/18/19/22运行U07具体操作与反例，保存原始输出和对应客户端/构建/数据版本。"
  ],
  "expected": [
    "每阶段有真实输入输出与版本引用；至少一个实验有实际基线/候选输出；不能把文档读完当实验完成。",
    "请求的三来源及必需实验完成才COMPLETE；任一必需资源缺失则本例BLOCKED且周期PARTIAL/BLOCKED，不用fixture补齐。",
    "不强制ADOPT；负/零收益可合格完成；实际项目变更须独立验收，缺证据不修改项目。",
    "跨会话恢复目标/下一步一致；用户不重复转发已有材料；侧栏/成果/总账指向同版本。",
    "实测背景补述次数、错误采信、时间、费用及未知项；首轮仅建立基线，不填虚构改善百分比。",
    "真实三来源/Jev/实验条件仍满足；CLI/Desktop指向同一目标、文件和费用；项目开工证据链完整，能实际修改和验证项目成果，不能只生成调研报告。",
    "保留上游URL/HEAD/源码路径、必要适配diff、许可、Jev原始判断及实际测试；最终采用有独立证据，不合适可REJECT且稳定版不变；报告/clone数量不替代实现和测试，不强制合入。",
    "实际CLI到Desktop再回CLI接续同一session/Goal和产物；只有一名有效writer，旧epoch拒绝，事件/工具/费用收敛；用户无需重复提供已保存背景，真实研究及代码适配/拒绝证据齐全。",
    "FIRST-USE/CONTINUITY/REUSE三项真实问题有输入、产物、人工介入/重复解释、质量、时间和未知费用观察；从首切片采集且同条件比较，不以报表数量或模型高分宣称收益；无改善保留稳定方案。"
  ],
  "assertions": [
    {
      "id": "A13-01",
      "check": "纵向闭环",
      "expected": "每阶段有真实输入输出与版本引用；至少一个实验有实际基线/候选输出；不能把文档读完当实验完成。"
    },
    {
      "id": "A13-02",
      "check": "真实完成",
      "expected": "请求的三来源及必需实验完成才COMPLETE；任一必需资源缺失则本例BLOCKED且周期PARTIAL/BLOCKED，不用fixture补齐。"
    },
    {
      "id": "A13-03",
      "check": "采用与负结果",
      "expected": "不强制ADOPT；负/零收益可合格完成；实际项目变更须独立验收，缺证据不修改项目。"
    },
    {
      "id": "A13-04",
      "check": "上下文与可见性",
      "expected": "跨会话恢复目标/下一步一致；用户不重复转发已有材料；侧栏/成果/总账指向同版本。"
    },
    {
      "id": "A13-05",
      "check": "收益基线",
      "expected": "实测背景补述次数、错误采信、时间、费用及未知项；首轮仅建立基线，不填虚构改善百分比。"
    },
    {
      "id": "A13-06",
      "check": "双端真实研究到执行",
      "expected": "真实三来源/Jev/实验条件仍满足；CLI/Desktop指向同一目标、文件和费用；项目开工证据链完整，能实际修改和验证项目成果，不能只生成调研报告。"
    },
    {
      "id": "A13-07",
      "check": "真实源码判断到适配",
      "expected": "保留上游URL/HEAD/源码路径、必要适配diff、许可、Jev原始判断及实际测试；最终采用有独立证据，不合适可REJECT且稳定版不变；报告/clone数量不替代实现和测试，不强制合入。"
    },
    {
      "id": "A13-08",
      "check": "CLI Desktop CLI同任务交接",
      "expected": "实际CLI到Desktop再回CLI接续同一session/Goal和产物；只有一名有效writer，旧epoch拒绝，事件/工具/费用收敛；用户无需重复提供已保存背景，真实研究及代码适配/拒绝证据齐全。"
    },
    {
      "id": "A13-09",
      "check": "真实问题的用户价值基线",
      "expected": "FIRST-USE/CONTINUITY/REUSE三项真实问题有输入、产物、人工介入/重复解释、质量、时间和未知费用观察；从首切片采集且同条件比较，不以报表数量或模型高分宣称收益；无改善保留稳定方案。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "完整trace及各阶段回执、三来源原始引用、实际实验、独立验收、UI录屏、跨会话回执、实际指标基线。",
    "P06实际客户端/项目初始化记录、输入版本、命令/事件与证据hash。",
    "J03冻结候选/输入/判据、来源及实际模式、原始输出、独立检查与动作回执。",
    "U03当前输入/构建/文件hash、操作回执、失败分支和独立复核；fixture与live分开。",
    "U07当前输入/构建/文件hash、操作回执、失败分支和独立复核；fixture与live分开。"
  ],
  "mode": "LIVE_WINDOWS_AND_SERVICE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.cycle.live"
  ],
  "final_owner_task": "W14"
}
```

### A14 · Windows隔夜运行与真实中断恢复

模式：LIVE_WINDOWS_AND_SERVICE；唯一最终负责人：W19；状态：NOT_RUN。

固定输入：

```json
{
  "minimum_wall_clock_hours": 8,
  "faults": [
    "executor_terminated",
    "host_reboot_or_sleep_resume",
    "network_disconnected",
    "phone_offline"
  ],
  "reconciliation_slo_seconds": 120,
  "harness_replays": {
    "H10": {
      "mu_default_minutes": 180,
      "mu_default_continuations": 20,
      "minimum_observation_hours": 8,
      "persist_counters": true
    }
  },
  "product_replays": {
    "P05": {
      "close_window": true,
      "renderer_crash": true,
      "explicit_quit": true,
      "cli_detach": true,
      "reopen": true
    }
  },
  "delivery_replays": {
    "U05": {
      "journey_document": "17_USER_JOURNEYS_AND_VALUE.md",
      "real_issue": "ISSUE-REUSE-001",
      "typed_protocol": "researchos-client/2",
      "manual_admin_commands_for_normal_use": 0,
      "old_PASS_is_new_PASS": false,
      "real_issue_selection_policy": "delivery.contract.json:first_real_coding_task_policy"
    }
  }
}
```

完整合同：

```json
{
  "id": "A14",
  "title": "Windows隔夜运行与真实中断恢复",
  "requirement_ids": [
    "R03",
    "R05",
    "R11",
    "R12",
    "R18",
    "R19"
  ],
  "wbs_ids": [
    "W19"
  ],
  "setup": [
    "Windows11 x64真实主机、选定服务启动方式及已验收备份；授权资源足以运行；运行配置并发2/队列100/周期6h/每项目1活动周期。",
    "观察窗口至少8小时真实墙钟；模拟时钟的单元测试不能代替。"
  ],
  "input": {
    "minimum_wall_clock_hours": 8,
    "faults": [
      "executor_terminated",
      "host_reboot_or_sleep_resume",
      "network_disconnected",
      "phone_offline"
    ],
    "reconciliation_slo_seconds": 120,
    "harness_replays": {
      "H10": {
        "mu_default_minutes": 180,
        "mu_default_continuations": 20,
        "minimum_observation_hours": 8,
        "persist_counters": true
      }
    },
    "product_replays": {
      "P05": {
        "close_window": true,
        "renderer_crash": true,
        "explicit_quit": true,
        "cli_detach": true,
        "reopen": true
      }
    },
    "delivery_replays": {
      "U05": {
        "journey_document": "17_USER_JOURNEYS_AND_VALUE.md",
        "real_issue": "ISSUE-REUSE-001",
        "typed_protocol": "researchos-client/2",
        "manual_admin_commands_for_normal_use": 0,
        "old_PASS_is_new_PASS": false,
        "real_issue_selection_policy": "delivery.contract.json:first_real_coding_task_policy"
      }
    }
  },
  "actions": [
    "运行周期并保留时间线，在不同阶段实际中断执行器、重启或休眠恢复主机、断网并使手机离线。",
    "恢复网络/主机后从检查点续跑，合并错过窗口并回查外部未确认动作；记录实际扫描停顿。",
    "如使用Mu，记录实际续跑策略并跨越其默认180分钟限制；如用其他运行器，验证等价会话结束/重开场景，保留8小时观察。",
    "隔夜过程中关闭/重开Desktop、模拟renderer崩溃、CLI脱离与显式退出，再恢复同一业务任务。",
    "按17/18/19/22运行U05具体操作与反例，保存原始输出和对应客户端/构建/数据版本。"
  ],
  "expected": [
    "至少8小时墙钟证据，停机/睡眠/离线明确显示；不宣称休眠时持续扫描。",
    "当服务/网络/凭据均可用后120秒内完成任务/事件状态对账或明确产生可见BLOCKED原因；不以不断重启隐藏故障。",
    "同项目同时活动周期<=1；全局活动执行<=配置并发2，队列<=100；积压窗口合并，游标不丢失。",
    "业务ID/检查点保留，重复副作用为0，重复逻辑通知为0；旧会话不复活已撤销决定。",
    "费用保留估计/已结算/未知类别；实际Windows恢复通过，不用Linux或fixture截图替代。",
    "宿主额度耗尽记暂停/检查点，不记完成；已授权自动恢复先对账并保留业务无进展/重试/费用计数；人工停止不可被恢复器绕过；无持久宿主时明确阻塞。",
    "关闭窗口和退出的实际行为与设置一致；后台运行须有真实宿主/托盘状态；明确停止不会自动复活；恢复保留业务ID/计数/事件水位且没有双执行或未知动作盲重试。",
    "关闭窗口/托盘/显式退出/崩溃/休眠分别按配置生效；重开同身份与检查点，人工停止保持停止，无重复副作用；保留真实8小时墙钟和物理Windows中断证据。"
  ],
  "assertions": [
    {
      "id": "A14-01",
      "check": "真实时长与状态",
      "expected": "至少8小时墙钟证据，停机/睡眠/离线明确显示；不宣称休眠时持续扫描。"
    },
    {
      "id": "A14-02",
      "check": "恢复时效",
      "expected": "当服务/网络/凭据均可用后120秒内完成任务/事件状态对账或明确产生可见BLOCKED原因；不以不断重启隐藏故障。"
    },
    {
      "id": "A14-03",
      "check": "有界运行",
      "expected": "同项目同时活动周期<=1；全局活动执行<=配置并发2，队列<=100；积压窗口合并，游标不丢失。"
    },
    {
      "id": "A14-04",
      "check": "连续性与副作用",
      "expected": "业务ID/检查点保留，重复副作用为0，重复逻辑通知为0；旧会话不复活已撤销决定。"
    },
    {
      "id": "A14-05",
      "check": "费用/恢复实测",
      "expected": "费用保留估计/已结算/未知类别；实际Windows恢复通过，不用Linux或fixture截图替代。"
    },
    {
      "id": "A14-06",
      "check": "真实隔夜不受会话额度误判",
      "expected": "宿主额度耗尽记暂停/检查点，不记完成；已授权自动恢复先对账并保留业务无进展/重试/费用计数；人工停止不可被恢复器绕过；无持久宿主时明确阻塞。"
    },
    {
      "id": "A14-07",
      "check": "窗口与核心生命周期",
      "expected": "关闭窗口和退出的实际行为与设置一致；后台运行须有真实宿主/托盘状态；明确停止不会自动复活；恢复保留业务ID/计数/事件水位且没有双执行或未知动作盲重试。"
    },
    {
      "id": "A14-08",
      "check": "正常关闭与隔天接续",
      "expected": "关闭窗口/托盘/显式退出/崩溃/休眠分别按配置生效；重开同身份与检查点，人工停止保持停止，无重复副作用；保留真实8小时墙钟和物理Windows中断证据。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "Windows版本/电源事件、8小时带时间戳运行日志、网络/进程/手机中断记录、前后检查点、对账SLO、资源与副作用统计。",
    "H10重放输入、判断/执行事件、确定性检查与原始输出hash。",
    "P05实际客户端/项目初始化记录、输入版本、命令/事件与证据hash。",
    "U05当前输入/构建/文件hash、操作回执、失败分支和独立复核；fixture与live分开。"
  ],
  "mode": "LIVE_WINDOWS_AND_SERVICE",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.overnight"
  ],
  "final_owner_task": "W19"
}
```

### A15 · 可复现安装、交付与验收索引

模式：LIVE_WINDOWS；唯一最终负责人：W20；状态：NOT_RUN。

固定输入：

```json
{
  "clean_target": true,
  "secret_material_in_distribution": false,
  "required_cases": 42,
  "deliverables": [
    "researchos_cli",
    "researchos_desktop_windows"
  ],
  "product_replays": {
    "P07": {
      "own_cli": true,
      "desktop_installer": true,
      "desktop_requires_external_node": false,
      "qm_server_required": false
    }
  },
  "delivery_replays": {
    "U08": {
      "journey_document": "17_USER_JOURNEYS_AND_VALUE.md",
      "real_issue": "ISSUE-REUSE-001",
      "typed_protocol": "researchos-client/2",
      "manual_admin_commands_for_normal_use": 0,
      "old_PASS_is_new_PASS": false,
      "real_issue_selection_policy": "delivery.contract.json:first_real_coding_task_policy"
    }
  }
}
```

完整合同：

```json
{
  "id": "A15",
  "title": "可复现安装、交付与验收索引",
  "requirement_ids": [
    "R18",
    "R20"
  ],
  "wbs_ids": [
    "W02",
    "W20"
  ],
  "setup": [
    "使用未安装开发依赖的干净Windows11 x64用户环境/隔离VM，交付包含精确依赖锁、build_id及真实commands registry。",
    "安装/账户先决条件明确；缺服务账户只允许局部安装验证，不会使最终live gate自动通过。"
  ],
  "input": {
    "clean_target": true,
    "secret_material_in_distribution": false,
    "required_cases": 42,
    "deliverables": [
      "researchos_cli",
      "researchos_desktop_windows"
    ],
    "product_replays": {
      "P07": {
        "own_cli": true,
        "desktop_installer": true,
        "desktop_requires_external_node": false,
        "qm_server_required": false
      }
    },
    "delivery_replays": {
      "U08": {
        "journey_document": "17_USER_JOURNEYS_AND_VALUE.md",
        "real_issue": "ISSUE-REUSE-001",
        "typed_protocol": "researchos-client/2",
        "manual_admin_commands_for_normal_use": 0,
        "old_PASS_is_new_PASS": false,
        "real_issue_selection_policy": "delivery.contract.json:first_real_coding_task_policy"
      }
    }
  },
  "actions": [
    "按交付说明安装、启动、打开UI、运行合同/必要smoke并执行升级/回退演练。",
    "校验交付manifest及全部验收索引；抽取一个结果重跑并比对原始证据。",
    "干净Windows安装并启动CLI和Desktop，核对绑定核心版本、首次模型设置、离线诊断、升级回退和卸载保留数据。",
    "按17/18/19/22运行U08具体操作与反例，保存原始输出和对应客户端/构建/数据版本。"
  ],
  "expected": [
    "execution/commands.json每个已声明实现键映射真实argv/cwd/脚本；未实现命令非零NOT_IMPLEMENTED；禁止echo PASS或空测试套件。",
    "干净Windows可完成指定安装/启动与卸载或停用；平台/依赖版本固定，安装中不隐式获取其他项目资料。",
    "包hash、来源commit、依赖锁、配置模板、备份恢复、资源缺口、已知限制及每个验收回执索引齐全，分发中无密钥。",
    "其余41个required case均有匹配版本结果；本例独立验证后再纳入完整42例索引，无需本例先PASS才能执行。NOT_RUN/BLOCKED/FAIL不能总览为PASS；文档validator不能替代产品用例。",
    "11页面连接最终真实API/事件，关键读写、成果版本、权限和断线恢复有可复核证据；固定后端夹具不能成为正式成品。",
    "交付可运行CLI与Desktop安装包和各自hash；Desktop携带必要运行时，无须用户另装Node/QM/Postgres；非交互CLI失败可诊断，联网模型缺资源如实BLOCKED；升级/卸载不默默删除项目。",
    "CLI与Desktop发行件均固定版本/hash；干净Windows安装/启动/更新/卸载可复现，必要运行时随包提供；数据保留与卸载范围明确，无需Node或手动后台命令，真实操作回执与当前构建绑定。"
  ],
  "assertions": [
    {
      "id": "A15-01",
      "check": "命令真实可执行",
      "expected": "execution/commands.json每个已声明实现键映射真实argv/cwd/脚本；未实现命令非零NOT_IMPLEMENTED；禁止echo PASS或空测试套件。"
    },
    {
      "id": "A15-02",
      "check": "复现边界",
      "expected": "干净Windows可完成指定安装/启动与卸载或停用；平台/依赖版本固定，安装中不隐式获取其他项目资料。"
    },
    {
      "id": "A15-03",
      "check": "交付完整",
      "expected": "包hash、来源commit、依赖锁、配置模板、备份恢复、资源缺口、已知限制及每个验收回执索引齐全，分发中无密钥。"
    },
    {
      "id": "A15-04",
      "check": "验收诚实",
      "expected": "其余41个required case均有匹配版本结果；本例独立验证后再纳入完整42例索引，无需本例先PASS才能执行。NOT_RUN/BLOCKED/FAIL不能总览为PASS；文档validator不能替代产品用例。"
    },
    {
      "id": "A15-05",
      "check": "最终前后端集成",
      "expected": "11页面连接最终真实API/事件，关键读写、成果版本、权限和断线恢复有可复核证据；固定后端夹具不能成为正式成品。"
    },
    {
      "id": "A15-06",
      "check": "两种发行件和干净安装",
      "expected": "交付可运行CLI与Desktop安装包和各自hash；Desktop携带必要运行时，无须用户另装Node/QM/Postgres；非交互CLI失败可诊断，联网模型缺资源如实BLOCKED；升级/卸载不默默删除项目。"
    },
    {
      "id": "A15-07",
      "check": "普通Windows用户可持续安装使用",
      "expected": "CLI与Desktop发行件均固定版本/hash；干净Windows安装/启动/更新/卸载可复现，必要运行时随包提供；数据保留与卸载范围明确，无需Node或手动后台命令，真实操作回执与当前构建绑定。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "干净环境描述、真实安装/启动/卸载命令回执、build manifest、依赖锁、验收索引、重跑对账及秘密扫描。",
    "P07实际客户端/项目初始化记录、输入版本、命令/事件与证据hash。",
    "U08当前输入/构建/文件hash、操作回执、失败分支和独立复核；fixture与live分开。"
  ],
  "mode": "LIVE_WINDOWS",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "release.reproduce",
    "acceptance.audit"
  ],
  "final_owner_task": "W20"
}
```

### A16 · 系统代码候选与独立控制面回滚

模式：LIVE_WINDOWS；唯一最终负责人：W16；状态：NOT_RUN。

固定输入：

```json
{
  "required_candidate_paths": [
    "no_gain_retained",
    "canary_then_rollback"
  ],
  "bad_candidates": [
    "startup_failure",
    "required_regression",
    "gate_or_permission_tamper"
  ]
}
```

完整合同：

```json
{
  "id": "A16",
  "title": "系统代码候选与独立控制面回滚",
  "requirement_ids": [
    "R09",
    "R16",
    "R17",
    "R18",
    "R20"
  ],
  "wbs_ids": [
    "W16"
  ],
  "setup": [
    "Windows稳定控制面由独立身份运行；候选在隔离工作区/进程，发布与验收基线不可写；有已实测备份。",
    "准备可归因的候选改动与三个故障候选：启动失败、回归、试图改验收或控制面权限。",
    "成功发布的canary遵守运营默认：至少一个真实周期且至少6小时观测，最长24小时仍未满足必需观察则不扩大；负向故障分支可即时注入验证回退机制，不替代成功发布观察窗。"
  ],
  "input": {
    "required_candidate_paths": [
      "no_gain_retained",
      "canary_then_rollback"
    ],
    "bad_candidates": [
      "startup_failure",
      "required_regression",
      "gate_or_permission_tamper"
    ]
  },
  "actions": [
    "真实构建并以同一冻结数据/回归比较稳定版与候选；无收益保留原版。",
    "对通过隔离检查的受控候选进行有限canary，然后实际触发回退；另验证三个故障候选拒绝/自动恢复。",
    "杀死候选进程，检查稳定监督/恢复仍能工作；检查迁移可回退性。"
  ],
  "expected": [
    "候选不能替换稳定发布服务、改自身强制测试/标签/权限；独立服务在候选崩溃时仍可回退。",
    "从canary实际恢复到上个接受版本hash，状态与必要数据一致；记录迁移/备份和健康检查，不仅修改状态字段。",
    "同样本可比较且无严重回归才允许候选晋升；无提升保持原版；不能用自评分或升级次数证明改善。",
    "候选失败不会终止稳定版全部任务；被冻结候选不能循环晋升；本版不声称训练或更新模型权重。"
  ],
  "assertions": [
    {
      "id": "A16-01",
      "check": "独立控制",
      "expected": "候选不能替换稳定发布服务、改自身强制测试/标签/权限；独立服务在候选崩溃时仍可回退。"
    },
    {
      "id": "A16-02",
      "check": "真实回滚",
      "expected": "从canary实际恢复到上个接受版本hash，状态与必要数据一致；记录迁移/备份和健康检查，不仅修改状态字段。"
    },
    {
      "id": "A16-03",
      "check": "收益与失败",
      "expected": "同样本可比较且无严重回归才允许候选晋升；无提升保持原版；不能用自评分或升级次数证明改善。"
    },
    {
      "id": "A16-04",
      "check": "约束范围",
      "expected": "候选失败不会终止稳定版全部任务；被冻结候选不能循环晋升；本版不声称训练或更新模型权重。"
    }
  ],
  "evidence_required": [
    "GLOBAL_EVIDENCE_V1",
    "稳定/候选进程及身份、实际构建/回归命令、固定评测数据hash、canary观测、三故障回执、真实回滚hash/数据对账/健康检查。"
  ],
  "mode": "LIVE_WINDOWS",
  "mandatory_gate": true,
  "gate_scope": "V2_RELEASE",
  "status": "NOT_RUN",
  "command_keys": [
    "test.evolution"
  ],
  "final_owner_task": "W16"
}
```

