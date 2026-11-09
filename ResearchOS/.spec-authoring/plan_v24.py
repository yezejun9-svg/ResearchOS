"""Author the small execution slices from the preserved parent contracts."""
from __future__ import annotations
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "ResearchOS_Implementation_Package_v2.4"
TASKS = json.loads((OUT / "contracts/tasks.json").read_text(encoding="utf-8"))
TM = {t["task_id"]: t for t in TASKS["tasks"]}
CM = {c['id']: c for c in json.loads((OUT/'contracts/acceptance.json').read_text(encoding='utf8'))['cases']}
STEPS = []

def add(sid, title, deps, paths, actions, results, key, cases, reads=(), resources=()):
    tid = sid[:3]
    commands = [{
        "key": key, "cwd": "REPOSITORY",
        "argv_template": ["python", "execution/command_dispatcher/dispatch.py", key,
                          "--task-id", tid, "--check-id", sid],
        "binding": "W02 registers this exact selector and real handler before use; UNBOUND/zero assertions is not PASS"
    }]
    if tid == "W00":
        commands = [{"key": "package.validate", "cwd": "SPEC",
                     "argv_template": ["python", "tools/validate_package.py"],
                     "binding": "ALREADY_PRESENT_IN_PACKAGE; save stdout in external construction evidence"}]
    elif tid == "W01":
        commands[0]["argv_template"] = ["python", "qualification/v2.4/qualify.py", "--check-id", sid]
        commands[0]["binding"] = "CREATE_AND_RUN_THIS_QUALIFICATION_DRIVER; no dependency on old dispatcher; record actual upstream commands and evidence"
    elif sid == "W02-01":
        commands[0]["argv_template"] = ["python", "qualification/v2.4/qualify.py", "--check-id", sid]
        commands[0]["binding"] = "EXTEND_EXISTING_QUALIFICATION_DRIVER_FOR_LAYOUT_AND_ENVIRONMENT; dispatcher not yet bound"
    elif sid == "W02-02":
        commands[0]["argv_template"] = ["python", "tests/bootstrap/test_dispatcher.py"]
        commands[0]["binding"] = "CREATE_SELF_RUNNING_DISPATCHER_CHECK_THIS_STEP; exercise versioned registry and exact selector with nonzero failures"
    receipt_dir = "execution/v2.4/receipts/" + tid + "/" + sid
    scope = list(paths)
    if receipt_dir + "/**" not in scope: scope.append(receipt_dir + "/**")
    if tid == 'W01' or sid == 'W02-01': scope.append('qualification/v2.4/**')
    STEPS.append({
        "id": sid, "parent_task": tid, "title": title, "phase": "IMPLEMENTATION_SLICE", "card_path": "tasks/steps/" + sid + ".md",
        "status": "NOT_STARTED", "dependencies": list(deps), "priority": len(STEPS) * 10 + 100,
        "read_refs": [
            {"path": "08_AGENT_EXECUTION_GOAL.md", "selector": "full_on_first_turn_then_relevant_constraints"},
            {"path": "05_WBS.md", "selector": tid},
            {"path": "contracts/tasks.json", "selector": "tasks[task_id=" + tid + "]"},
            *[{"path": p, "selector": s} for p, s in reads]
        ],
        "write_scope": scope, "actions": list(actions), "deliverables": list(results),
        "checks": [
            {"id": sid + "-OUTPUT", "expected": results[0]},
            {"id": sid + "-NEGATIVE", "expected": results[-1]},
            {"id": sid + "-EVIDENCE", "expected": "保存实际输入/代码/产物hash、命令/退出码和未通过项；独立复核当前产物后才接受本卡。"}
        ],
        "verification_commands": commands, "affected_formal_cases": list(cases),
        "resource_requirements": list(resources),
        "limits": [
            "只改本卡登记范围；共享合同/锁/迁移序号由对应owner串行整合。",
            "模式DEVELOPMENT/FIXTURE/资格样机与正式LIVE分别记录；子卡完成不签收整个WBS或父用例。",
            "同输入同失败最多自动重试2次；无新证据3轮延期，禁止换Goal/窗口重置。",
            "不改冻结门槛、旧回执或未知费用；资源缺失只阻塞依赖该资源的步骤。"
        ],
        "rollback": "保留已知可用基线和用户修改；撤回本卡候选变更或弃用独立候选工作区，不覆盖稳定数据。",
        "handoff": {"state": "execution/v2.4/step_state.json", "checkpoint": "execution/v2.4/checkpoint.json",
                    "receipt_directory": "execution/v2.4/receipts/" + tid + "/" + sid,
                    "independent_review_required": True},
    })

add("W00-01", "核对现有身份、Git和旧证据，保护现场", [],
    ["execution/v2.4/inventory.json", "execution/v2.4/step_state.json", "execution/v2.4/checkpoint.json", "execution/v2.4/receipts/W00/**"],
    ["实读18和Repository_Baseline；重新运行git status --porcelain=v1、rev-parse HEAD、worktree list --porcelain。",
     "读取永久身份/旧AGENTS/route/path_ownership/commands/checkpoint；记录现有服务的身份线索，不启动/停止/迁移服务。",
     "盘点当前授权仓库、已装工具和所需本地源码；FOUND/NOT_FOUND/NOT_ACCESSIBLE/NOT_CHECKED分别记录，不读取秘密值。",
     "给当前修改和活动owner建立保护清单；只为真正无法确定的归属阻塞相应路径。",
     "仅不存在新版施工状态时，按examples创建本轮step_state/checkpoint以保存本卡接受；已存在就读取验证，不覆盖。此时不改旧AGENTS/spec/业务身份。"],
    ["带当前HEAD/dirty/永久身份/旧spec hash的inventory和保护清单。",
     "反例：同名路径或旧PID不能覆盖身份；无授权项目不被访问，旧文件字节不变。"],
    "package.validate", ["A01", "C02"], [("18_EXISTING_REPOSITORY_MIGRATION.md", "1-2")])
add("W00-02", "冻结v2.4与迁移ADR，建立分支和续跑记录", ["W00-01"],
    ["AGENTS.md", "spec/v2.4/**", "docs/adr/ADR-next-v24-continuation.md", "execution/v2.4/**"],
    ["在已登记范围创建隔离候选分支/worktree，保留项目ID；若无仓库才执行新建分支。",
     "复制本包到spec/v2.4并校验manifest；同名不同hash不能覆盖，spec/v2.0保持只读。",
     "按已有ADR-001/002之后的实际空编号写迁移ADR，登记保留/适配/退休和回退；独立审查后更新候选分支AGENTS入口。",
     "接续W00-01已建立的step_state/checkpoint，将同身份候选worktree路径、spec hash、输入commit和旧证据索引登记；迁移施工记录保留文件hash与旧副本，不覆盖旧ACCEPTED。"],
    ["新spec只读快照、迁移ADR、独立复核及execution/v2.4初始检查点。",
     "反例：换规格或重新打开窗口不能清除旧policy拒绝、失败计数或覆盖用户修改。"],
    "package.validate", ["A01", "A12"], [("18_EXISTING_REPOSITORY_MIGRATION.md", "2-6")])
add("W00-03", "尽早核对施工模型和产品资源，冻结第一真实任务", ["W00-01"],
    ["execution/v2.4/resource_matrix.json", "execution/v2.4/first_work.json"],
    ["按20读取Qoder版本/模型目录，固定Qwen3.8-Flash；施工宿主与产品Mu/Pi模型后端分别登记。",
     "只核对已授权凭据引用/端点可用状态，不读取或复制其他项目账号；登记产品模型、Jev、X、GitHub、论文、Windows、手机、Verifier各资源。",
     "记录17的三个ISSUE与当前复现，先冻结问题选择规则；真正产品演示前再选一项当时未解决问题，不将已修好的首次使用缺陷当待修任务。",
     "真实资源欠缺形成具体请求；本卡的盘点可完成，但受影响live卡保留资源前置，不用假请求或目录可见冒充模型调用。"],
    ["资源矩阵逐项区分DISCOVERED/CONFIGURED/PROBED/LIVE_VERIFIED与未知；三项真实工作有输入和预注册判据。",
     "反例：Qoder能选Qwen不等于ResearchOS已有模型API凭据，网页能打开不等于工具执行已验证。"],
    "package.validate", ["A04", "A08", "A13"], [("20_QODER_QWEN_EXECUTION.md", "1-7"), ("17_USER_JOURNEYS_AND_VALUE.md", "1-6")])
add("W01-01", "固定Mu源码与许可，划出最小复用范围", ["W00-02", "W00-03"],
    ["qualification/v2.4/mu/**", "execution/v2.4/source_candidates.json"],
    ["优先读本地固定源码，没有才在资格目录clone官方Mu并checkout 8dfebe36508ac0c2508735bb866756dab9283e74；记remote/HEAD/hash。",
     "创建qualification/v2.4/qualify.py真实驱动，支持--check-id选择当前资格检查，未知/未实现非零失败；直接调用已核查上游构建/运行命令并存原始输出，不依赖旧dispatcher。",
     "核查根MIT、desktop Apache-2.0及AionUi来源；读取19列出的CLI、NativeClientContext、RPC和NativeHost入口。",
     "记录Go控制面保留范围与上游模型/工具/UI复用范围，不把研究clone作为正式依赖。",
     "检查package scripts和锁文件后，仅在授权隔离目录安装该固定组合的必要依赖；保存原版构建结果。"],
    ["固定源码/许可/入口清单与原版构建回执；需要的适配能定位到实际文件。",
     "反例：源码获取或模型资源失败保持资源原因，不解释为没有现成实现而转全自研。"],
    "core.qualify", ["A02"], [("19_DESKTOP_IMPLEMENTATION_BLUEPRINT.md", "2-4"), ("16_ADOPTION_JUDGMENT.md", "G01-G07")])
add("W01-02", "先验证同一宿主的双端会话、工具和取消", ["W01-01"],
    ["qualification/v2.4/mu/shared-session/**", "qualification/v2.4/mu/results.json"],
    ["在资格沙箱以一名宿主监督Mu RPC worker；用最窄适配注入桌面NativeClientContext，同时保留CLI协议客户端。",
     "以授权临时工作区和一个已有模型执行读文件、候选修改、一个真实测试；桌面与CLI指向同一session。",
     "验证写入权交接、旧epoch拒绝、重复命令、事件补齐及clear_queue/abort/settled/子进程终止。",
     "固定失败输入；仅一次针对已观察失败的修复。不能把资格stub或两个独立会话冒充完整产品。"],
    ["资格矩阵含原版/适配版实际命令、双端身份、产物及取消证据；缺live明确BLOCKED。",
     "反例：父进程退出但子进程存活、两端各改一份代码或共享配置而未共享session均失败。"],
    "core.qualify", ["A02", "A04", "C01"], [("14_CLI_DESKTOP_PRODUCT.md", "2-3"), ("19_DESKTOP_IMPLEMENTATION_BLUEPRINT.md", "4-9")],
    ["Windows", "authorized_product_model_backend"])
add("W01-03", "接受唯一复用路线并固定维护退出成本", ["W01-02"],
    ["docs/adr/ADR-next-v24-route.md", "execution/v2.4/route.json", "execution/v2.4/reuse_decisions.json"],
    ["把保留现状、Mu适配的需求覆盖、补丁范围、构建/运行证据提交独立bootstrap审查；Jev可用仅ADVISORY。",
     "Mu具体能力失败时才验证Pi+已核实Craft桌面备选；固定实际版本，沿用同一输入，每条路线最多一次修复。",
     "保存ADOPT/REJECT/WATCH/INCONCLUSIVE和G01-G07依据；选定MU_FORK或PI_COMPOSE及唯一业务权威。",
     "确有证据的单能力缺口才能CUSTOM_GAP；缺账户/网络不能批准自研；W01不得依赖未来W11。",
     "仅缺live资源时可独立接受标为PROVISIONAL_DEVELOPMENT的路线用于已定义开发切片；W01-99仍须实际资格通过，后续正式门不得使用临时路线通过。"],
    ["独立接受的路线ADR、component来源范围、升级/回退计划；后续按此路线实施。",
     "反例：没有可验证路线就保留阻塞/独立开发，不以假兼容或偷换为旧THIN_CORE结案。"],
    "core.qualify", ["A02", "C05"], [("15_NEW_PROJECT_WORKFLOW.md", "3-6"), ("18_EXISTING_REPOSITORY_MIGRATION.md", "3")])
add("W02-01", "把复用源码放进可维护构建结构", ["W01-03"],
    ["third_party/mu/**", "execution/v2.4/path_ownership.json", "execution/v2.4/component_lock.json", "execution/v2.4/patch_inventory.json"],
    ["按选定路线导入固定源码/依赖；推荐third_party/mu保留上游workspace结构，若现有合法fork有更好位置则映射实际路径。",
     "根Go业务目录不移动重写；Mu原始源码和ResearchOS适配补丁分别登记，保留LICENSE/NOTICE/来源。",
     "锁定现有Go及选定Node/package manager，按上游已有锁构建；避免无理由升级内嵌Pi或追加整套框架。",
     "登记CORE/DOMAIN/CLI/DESKTOP/ADAPTERS/UI等实际路径与唯一整合owner；禁止两个工作者同时改锁文件。"],
    ["能复现的源码布局、依赖锁、许可与补丁清单；实际路径供所有后续卡读取。",
     "反例：空目录占位、嵌套.git导致源码未进入交付、源码与声明commit不同均不能通过。"],
    "environment.verify", ["A02", "A15"], [("18_EXISTING_REPOSITORY_MIGRATION.md", "3"), ("19_DESKTOP_IMPLEMENTATION_BLUEPRINT.md", "3-5")])
add("W02-02", "绑定真实命令、客户端协议和步骤检查选择器", ["W02-01"],
    ["execution/command_dispatcher/dispatch.py", "execution/v2.4/commands.json", "execution/v2.4/client_mapping.json", "tests/bootstrap/test_dispatcher.py"],
    ["复用现有dispatcher，注册当前spec验证、所选fork构建/启动/停止及后续检查键；本卡ID作为明确check-id选择器。",
     "已实现项登记实际argv/cwd/env名称/超时/产物；未实现项保持UNBOUND并非零退出，不写echo PASS。",
     "逐method映射researchos-client/2到Go领域操作或受控workspace工具、逐event映射上游RPC到本协议。",
     "测试未知键/无handler/零断言/错误JSON/超时均失败；旧spec/v2.0命令仍保留为历史，不静默测试错版本。"],
    ["可执行注册与dispatcher、完整client_mapping及真实错误路径回执。",
     "反例：共享父测试键不代表所有后置检查通过；新命令未实现时不能吞错误并返回0。"],
    "build.check", ["A03", "A15"], [("22_CLIENT_INTERFACE_DETAILS.md", "full"), ("12_IMPLEMENTATION_AND_HANDOFF.md", "2")])
add("W02-03", "形成自己的CLI和Desktop最薄可启动入口", ["W02-02"],
    ["CLI/**", "DESKTOP/main/**", "DESKTOP/preload/**", "execution/v2.4/receipts/W02/**"],
    ["用上游已有CLI启动器和Electron主进程建立ResearchOS名称/图标/构建入口，不从零写TUI或Electron框架。",
     "Electron不另起独立scheduler；明确启动/发现Go宿主与单worker链；Node IPC不能直接假当stdin JSONL。",
     "Desktop最早只要能显示宿主状态和协议版本；CLI help/version/doctor真实反馈；未实现能力显示未实现。",
     "实际构建并启动两个入口，记录版本、进程和日志位置；验证关闭测试实例不误停旧服务。"],
    ["真实可启动CLI/Desktop壳、共享宿主连接和版本握手回执。",
     "反例：仅浏览器页面、仅外部Mu/Qoder窗口或改名截图不计自有入口通过。"],
    "build.check", ["A04", "C23"], [("19_DESKTOP_IMPLEMENTATION_BLUEPRINT.md", "4-6"), ("22_CLIENT_INTERFACE_DETAILS.md", "handshake")])
add("W03-01", "对照现有领域schema，实施最小兼容迁移", ["W02-02"],
    ["internal/domain/**", "internal/store/**", "migrations/sqlite/next_v24_sessions.sql", "tests/domain/**"],
    ["对比目标domain与已实现Go实体/约束，复用已有代码；只列实际字段/状态/索引差异。",
     "加入Session与project/goal/run、上游日志ID/hash及事件水位的持久映射，业务状态仍在Go唯一事务。",
     "只在空库和旧库备份副本运行连续迁移；保存迁移前后身份、行数、引用和对象一致性。",
     "检查未知enum、金额null、陈旧revision、跨项目引用与迁移失败；不修坏数据后静默继续。"],
    ["目标字段/迁移/映射的真实可复现实现，旧project_id及已有成果关系保持。",
     "反例：重复Session业务真值、迁移失败仍升版本、直接覆盖稳定原库均失败。"],
    "test.domain", ["A03", "A12"], [("03_DATA_CONTRACTS.md", "v2.4"), ("22_CLIENT_INTERFACE_DETAILS.md", "SessionSnapshot")])
add("W03-02", "实现typed本地协议及幂等事件边界", ["W03-01"],
    ["internal/api/**", "internal/domain/client_protocol*.go", "tests/contracts/**"],
    ["按client.protocol.schema.json验证23方法请求和逐method结果；实现握手、错误、空值与typed SessionSnapshot。",
     "使用command_id内容hash去重；same key/different request拒绝；所有写入检查身份/project/session/revision/epoch。",
     "事务中写业务状态和事件，序号/缺口/快照恢复规则统一；敏感字段不进入普通payload。",
     "使用全部v2协议正负fixtures并加实际业务不变量检查；schema通过不替代路径/CAS/OS身份验证。"],
    ["CLI和Desktop可使用同一typed服务；请求/响应/事件均有正负回放。",
     "反例：裸object成功、跨method结果、旧协议降级、错误payload吞掉或重复副作用均失败。"],
    "contracts.validate", ["A03", "C23", "C26"], [("22_CLIENT_INTERFACE_DETAILS.md", "full"), ("examples/client_protocol_v2_fixtures.json", "fixtures")])
add("W04-01", "本地目录注册、项目接续和首用最小导入", ["W03-02", "W00-02"],
    ["internal/domain/context*.go", "internal/domain/project*.go", "ADAPTERS/local_workspace/**", "tests/context/**"],
    ["通过受限native目录选择和workspace.register生产authorized_workspace_ref；验证路径/junction/范围后才发引用。",
     "project.bootstrap创建或接续ResearchOS身份；重复导入幂等，导入失败按文件记录。",
     "先保存身份/元数据/LOCAL_INVENTORY，完整研究和采用状态由W08接入；允许授权资格工作，不虚构完成初始化。",
     "验证同名项目、取消选择、路径越界、未授权旧项目和部分解析失败。"],
    ["首次选择目录能创建/接续真实项目，引用有生产者和生命周期。",
     "反例：把绝对路径当已授权引用、无权限目录当空目录、重复创建永久身份均失败。"],
    "test.context", ["A01", "C02"], [("22_CLIENT_INTERFACE_DETAILS.md", "workspace/project"), ("18_EXISTING_REPOSITORY_MIGRATION.md", "1-3")])
add("W04-02", "冻结上下文并将变更影响传给真实任务", ["W04-01"],
    ["internal/domain/context*.go", "internal/domain/change*.go", "tests/context/**"],
    ["从实际ProjectState生成带hash/revision的ContextBundle，保存用户原话、有效/废弃决定、失败、权限和未完成下一步。",
     "worker在空任务工作区接收必要文件manifest并核对字节，不假定继承父cwd。",
     "变更记录显式影响关系，旧输入提交拒绝；冲突保留双方，不重取最新revision后覆盖旧草稿。",
     "测试必需上下文缺失阻塞、可选检索失败降级、无关事件不让所有任务失效。"],
    ["新会话/worker能恢复准确下一步，依赖变更与冲突有可重放处理。",
     "反例：压缩丢授权/失败、私有记忆覆盖项目真值、未注入文件却自报读取均失败。"],
    "test.context", ["C01", "C03", "C04"], [("13_HARNESS_DESIGN.md", "H01/H05"), ("03_DATA_CONTRACTS.md", "ContextBundle/ChangeProposal")])
add("W05-01", "对接实际模型和一次受控Agent循环", ["W03-02", "W04-02", "W17-01", "W12-01"],
    ["ADAPTERS/runtime/**", "ADAPTERS/model/**", "CLI/**", "tests/runtime/**"],
    ["通过provider.models/configure/probe获取模型目录并验证连接/认证/真实推理；工具能力由后续真实read/write/command Run验证，未运行显示NOT_RUN；产品provider不借用Qoder内部账号假设。",
     "Go委派一个有Task/Run/lease的Mu/Pi worker；已有SDK提供模型/工具循环，ResearchOS限制作用域并接收事件。",
     "实际调用一个已授权模型执行读取临时文件，记录真实provider/model revision及费用已知/未知。",
     "测试鉴权/限流/模型不支持tool-calling/格式错与明确错误；固定模型不能偷偷换别的模型。"],
    ["自有CLI能经唯一宿主完成真实模型和文件读取，事件/费用与Run关联。",
     "反例：只返回文本或目录能列模型不等于真实工具能力；缺账户保持对应live BLOCKED。"],
    "test.runtime", ["A04"], [("22_CLIENT_INTERFACE_DETAILS.md", "provider/session"), ("20_QODER_QWEN_EXECUTION.md", "模型身份区分")],
    ["authorized_product_model_backend"])
add("W05-02", "完成CLI读改文件、diff、测试和真实中断", ["W05-01"],
    ["CLI/**", "ADAPTERS/runtime/**", "ADAPTERS/workspace/**", "tests/runtime/**"],
    ["复用成熟TUI实现中文多行/IME、流式消息/工具、错误输出、长日志展开；不只打印一段最终答案。",
     "按17的真实首次登录问题读取现有代码、提出修改、写候选文件并跑相关检查。",
     "工具写与workspace.write走同一授权/hash/CAS处理器；文件命令和测试都留下真实输出。",
     "Ctrl+C与cancel执行clear_queue→abort→settled→子进程确认；忙时steer/follow_up有队列语义。"],
    ["CLI可执行完整编码任务并展示真实diff/检查；至少一次失败检查驱动有限修复。",
     "反例：只有计划未落盘、父进程退出但子进程仍写、取消后Goal继续重启均失败。"],
    "test.runtime", ["A04", "C11"], [("17_USER_JOURNEYS_AND_VALUE.md", "JRN-02"), ("19_DESKTOP_IMPLEMENTATION_BLUEPRINT.md", "CLI/tool lifecycle")],
    ["authorized_product_model_backend", "Windows"])
add("W05-03", "补齐CLI命令、JSONL与安装入口", ["W05-02", "W06-02"],
    ["CLI/**", "OPS/cli_distribution/**", "tests/runtime/cli_contract*"],
    ["逐项实现product.contract列出的交互/init/run/goal/resume/status/cancel/doctor/config和slash命令。",
     "非交互stdout仅JSONL，stderr诊断；验证0/1/2/3/130退出码与执行报告/独立验收语义。",
     "resume同一session并检查writer；model切换经配置版本与settled确认；未知命令非零失败。",
     "生成可在Windows路径含空格/中文时安装启动的CLI分发候选，W20再做最终发行复验。"],
    ["全命令有对应处理器、帮助和检查；中文路径/长输出/headless可复现。",
     "反例：空stub、shell别名调用外部品牌CLI充数、stdout混日志或静默模型切换均失败。"],
    "test.runtime", ["A04", "A15"], [("14_CLI_DESKTOP_PRODUCT.md", "4"), ("contracts/product.contract.json", "cli")])
add("W06-01", "复用并补足独立接受服务", ["W03-02", "W04-02"],
    ["internal/domain/orchestration*.go", "internal/domain/acceptance*.go", "tests/orchestration/**"],
    ["执行者只提交EXECUTION_REPORTED；独立Verifier重读实际产物、检查输入/代码/测试hash及完整必需ID。",
     "最终接受事务再检查任务归属、revision/epoch、权限、未决冲突/副作用和用途资格。",
     "同事务写ACCEPTED、后继放行与outbox；运行器done/met/最后lint不自动完成。",
     "测试自批、旧输入、缺一个硬门、评分高但失败和对账间状态变化。"],
    ["接受链使用真实服务事务，假完成和自批反例全部被拒绝。",
     "反例：仅换模型名字、解析到met、最后一条命令exit0均不能掩盖必需失败。"],
    "test.orchestration", ["A03", "C07", "C10"], [("02_TECHNICAL_DESIGN.md", "5"), ("13_HARNESS_DESIGN.md", "H02")])
add("W06-02", "落实会话单写者和双客户端协议交接", ["W05-02", "W06-01"],
    ["internal/domain/session*.go", "internal/api/client*.go", "tests/context/**"],
    ["session.attach/handoff在同一权威存储取得或转移writer_epoch，忙时先取得可中断点的真实停止确认。",
     "实现session.get/list/events及snapshot-watermark重连；新客户端不另起第二个可写Agent。",
     "用真实CLI和协议测试客户端双向交接、并发发消息、重复命令、断线和旧epoch写入。",
     "W13/W14还要真实Desktop复验，本卡协议客户端不冒充产品UI。"],
    ["一个session最多一个有效writer，重复/乱序/恢复事件与费用收敛。",
     "反例：共用配置但不同会话、旧端覆盖新端、断线重连丢事件仍报最新均失败。"],
    "test.context", ["C01", "C04", "C26"], [("22_CLIENT_INTERFACE_DETAILS.md", "session"), ("14_CLI_DESKTOP_PRODUCT.md", "3")])
add("W07-01", "接通GitHub与论文来源并固定原文", ["W03-02", "W01-03"],
    ["adapters/sources/**", "internal/domain/sources*.go", "tests/sources/**"],
    ["复用已实现SourceAdapter和已有last30days组件中合格部分，不运行其第二watchlist scheduler。",
     "实际GitHub/论文查询固定问题和时间窗口，分别记录元数据/原文、revision/日期/hash/locator。",
     "游标在该页落库后推进；重试/转载/重复页面去重不丢来源。",
     "验证真实空集与认证/限流/超时/格式失败区分；外部文本不作为工具执行指令。"],
    ["两类真实来源和原文证据可追溯，失败不推进成功游标。",
     "反例：模型记忆、README宣传或转载计数代替实际原文均失败。"],
    "test.sources.live", ["A05", "C19"], [("02_TECHNICAL_DESIGN.md", "SourceAdapter"), ("06_ACCEPTANCE_TESTS.md", "A05")],
    ["GitHub_read", "paper_source"])
add("W07-02", "接通X并完整记录来源健康", ["W07-01"],
    ["adapters/sources/**", "internal/domain/sources*.go", "tests/sources/**"],
    ["只用已授权X后端或官方可用入口；查询与当前问题关联，不绕过登录/限额。",
     "真实取得页面/结果并记录来源窗口、后端、游标和健康；无结果也是实际成功访问后的结果。",
     "注入X失败并验证GitHub/论文继续、整体PARTIAL而非COMPLETE；恢复从游标补齐。",
     "保存三源探针和错误分类，不将网络/账号失败解释为产品研究无价值。"],
    ["三类来源各有真实成功或明确阻塞，健康/覆盖与UI一致。",
     "反例：X未配置却写空结果或完整覆盖、引用一年旧文当近7天均失败。"],
    "test.sources.live", ["A05", "C06"], [("06_ACCEPTANCE_TESTS.md", "A05/C06")], ["authorized_X_backend"])
add("W08-01", "把源码采用与初始化状态做进产品", ["W04-01", "W07-01", "W06-01"],
    ["internal/domain/research*.go", "internal/domain/adoption*.go", "tests/research/**"],
    ["让init/Desktop新项目使用LOCAL_INVENTORY→RESEARCH→REUSE_DECISION→IMPLEMENTATION同一状态投影。",
     "封存SourceCandidate/AdoptionDecision Artifact，绑定来源revision、许可、G01-G07、基线及独立接受。",
     "先实现明确FIXTURE的Jev建议协议和拒绝路径，真实用途等W11；W08不依赖W14或W11。",
     "测试本地已足够/高分硬失败/无许可证/候选不合适/无候选/确有缺口以及调查clone未正式采用。"],
    ["B01/B02/J01对应产品路径有真实处理器和负例；已有小修复不重复全量选型。",
     "反例：clone后默认ADOPT、未调用Jev却显示分数、缺网络跳过复用门自研均失败。"],
    "test.research.fixture", ["C05", "C06"], [("15_NEW_PROJECT_WORKFLOW.md", "full"), ("16_ADOPTION_JUDGMENT.md", "J01")])
add("W08-02", "研究周期闭合与问题驱动调度", ["W08-01", "W09-01", "W12-02"],
    ["internal/domain/research*.go", "internal/domain/monitor*.go", "tests/research/**"],
    ["将每轮研究绑定有效问题/用户明确监控意图，持久保存窗口、覆盖、候选、实验、处置与下次条件。",
     "最多一个活动周期，6小时触发与错过窗口有限合并；未形成问题不能无限扩展框架清单。",
     "完整必需来源/实验/处置后接受COMPLETE；REJECT/WATCH/INCONCLUSIVE合法，缺源PARTIAL。",
     "测试重复触发/恢复/无候选/手动周期与自动周期不同关闭门；候选不能绕过接受直接写稳定代码。"],
    ["周期可真实推进且有界关闭，长期监控不阻止已完成单轮交付。",
     "反例：资料多或高star自动推进采用、反复新候选逃避无进展或手动关闭自动工作均失败。"],
    "test.research.fixture", ["C05", "C06", "C11"], [("01_PRD.md", "R05/R07"), ("07_OPERATIONS_AND_EVOLUTION.md", "研究周期")])

add("W09-01", "统一证据谱系与真实原文定位", ["W03-02", "W07-01"],
    ["internal/domain/evidence*.go", "adapters/retrieval/**", "tests/evidence/**"],
    ["封存原文Artifact与Evidence：source URL/revision/hash/locator/type/observed_at，不将摘要替代原文。",
     "让同源转载合并但保留引用链；源更新/撤销使下游证据STALE/REVOKED，传播到依赖判定。",
     "实现本地检索与引用返回，命中必须通过项目权限和当前source hash重验。",
     "基线使用本地现有索引；Sirchmunk只在固定源码资格合格后替代适配器。"],
    ["回答和候选的每项依据可回到具体原文片段与当前权限。", "反例：SIMULATED伪装OBSERVED、同名文件跨项目泄露、撤销后缓存继续命中均失败。"],
    "test.retrieval", ["A06", "C02", "C19"], [("03_DATA_CONTRACTS.md", "Evidence"), ("09_COMPONENT_DECISIONS.md", "Sirchmunk")])
add("W09-02", "撤销和权限变化清除检索缓存", ["W09-01", "W17-01"],
    ["adapters/retrieval/**", "internal/domain/evidence*.go", "tests/evidence/**"],
    ["缓存键绑定project/source/index/permission版本，权限或内容改变立即失效。",
     "执行删源、改权、路径越界、软链接、过期引用五类负例；事件重放不重新授权。",
     "把来源覆盖和证据类型显示在CLI/Desktop同一投影。"],
    ["新旧客户端与搜索缓存同时遵守撤销结果。", "反例：只隐藏前端但API/附件/事件仍返回被撤销内容失败。"],
    "test.security", ["A06", "C02", "C19"], [("06_ACCEPTANCE_TESTS.md", "A06")])
add("W10-01", "冻结实验输入并公平执行基线和候选", ["W06-02", "W09-01", "W12-01"],
    ["internal/domain/experiment*.go", "adapters/evaluation/**", "tests/experiments/**"],
    ["在任何候选运行前固定问题、基线、版本、指标、预算/停止条件和样本hash。",
     "相同输入分别运行基线与候选，保留stdout/stderr/exit/原始测量；候选只能改隔离工作区。",
     "区分PASS/FAIL/ABSTAIN/ERROR/INVALID/MISSING，支持REJECT/WATCH/INCONCLUSIVE。",
     "运行12条冻结smoke及零样本/改hash/越权负例；统计实现接入实际持久化报告。"],
    ["实验报告包含可复算计数、版本和所有失败样本。", "反例：删除失败样本、补造缺失指标或运行后更改通过门均失败。"],
    "test.experiments", ["A07", "C05", "C07"], [("11_EVALUATION_AND_INTEGRATION.md", "full"), ("examples/evaluation_smoke_cases.json", "full")])
add("W10-02", "对接固定skill-up并验证外部评测适配", ["W10-01"],
    ["adapters/evaluation/**", "tests/evaluation/**"],
    ["读取当前选定skill-up固定源码/真实CLI帮助，保存输入输出接口和版本，先跑最小真实样本。",
     "将外部报告转换EvaluationReport且保持原始计数，SKIP/缺失/重复不能变PASS。",
     "注入未知用例、修改被测配置和未授权外发；正式标签只给独立Verifier。"],
    ["真实skill-up执行及报告可追溯，适配器拒绝畸形结果。", "反例：只做内部DSH替身或生成报告JSON不足通过C21。"],
    "test.evaluation.fixture", ["C21", "A07"], [("06_ACCEPTANCE_TESTS.md", "C21"), ("11_EVALUATION_AND_INTEGRATION.md", "评测接口")], ["skill_up_runtime"])
add("W11-01", "接通Jev建议并限制决策权", ["W09-01", "W10-01"],
    ["adapters/judge/**", "internal/domain/judgment*.go", "tests/jev/**"],
    ["固定Mu/Jev复用模块或已选模型接口，记录decision point、输入hash和原始建议。",
     "实现SHADOW/ADVISORY/BOUNDED_AUTO和用途资格键；默认SHADOW，建议不直接创建Acceptance。",
     "比较原始判断与Jev建议，重放硬失败高分、超时、越权和旧版本意见。"],
    ["同一决策有原始判断/Jev建议/最终独立接受的可追溯链。", "反例：改名Verifier后执行者自签、建议分数覆盖硬失败或全用途放权均失败。"],
    "test.jev.fixture", ["A08", "C07", "C08", "C20"], [("16_ADOPTION_JUDGMENT.md", "full")])
add("W11-02", "隔离真实标签并完成逐用途资格", ["W11-01", "W17-02"],
    ["adapters/judge/**", "tests/jev/**", "execution/v2.4/qualification/**"],
    ["每个申请授权的用途按A08固定至少60开发/校准+30独立holdout；取得可追溯人工/事实标签。",
     "真实provider运行，保留task_type/language/provider/model_revision/rubric_revision独立统计。",
     "关键误放行0、分歧不超过5%，同时报告拒绝/弃权/成本/延迟；不足继续SHADOW。",
     "对reuse_selection单独验证许可/平台/接入/README不足等反例，不借其他用途资格。"],
    ["每用途独立资格报告与holdout访问审计；缺标签/凭据明确BLOCKED。", "反例：12smoke、模型投票或开发样本冒充独立holdout通过A08失败。"],
    "test.jev.live", ["A08", "C08", "C20"], [("06_ACCEPTANCE_TESTS.md", "A08"), ("11_EVALUATION_AND_INTEGRATION.md", "holdout")], ["authorized_provider", "independent_labeled_cases"])
add("W12-01", "费用预占、对账与有限重试", ["W03-02"],
    ["internal/domain/budget*.go", "internal/domain/resource*.go", "tests/resources/**"],
    ["默认cap=null并发2，但保留最大重试2及同源连续3轮无进展停止。",
     "预占/未知费用/已结算费用分列；严格cap时未可证明上限的运行拒绝启动。",
     "迟到usage按原run原幂等键对账；断连/重启不重计也不清空预占。",
     "持久记录失败指纹和origin，改Goal/会话/窗口不能逃避失败预算。"],
    ["正常、迟到和重复usage均可复算；有限重试跨重启延续。", "反例：null无限金额被解释为无限重试，或超时后未知账单当0失败。"],
    "test.resources", ["C11", "C13", "C14", "C15"], [("03_DATA_CONTRACTS.md", "Budget"), ("06_ACCEPTANCE_TESTS.md", "C13-C15")])
add("W12-02", "用途等价资源切换与用户可操作请求", ["W12-01", "W06-01"],
    ["internal/domain/resource*.go", "adapters/runtime/**", "tests/resources/**"],
    ["只在已授权且同用途资格有效的资源之间切换；保持原任务、run关联和版本。",
     "资源不足聚合同源ResourceRequest，包含影响、用户下一步与恢复条件。",
     "证明未受影响分支继续，受影响支路恢复后不重复副作用；告警不每轮重复。",
     "接入U09：连续两个检查点只有文档/fixture时转回最短真实用户流程，不降低正式门。"],
    ["故障切换、缺资源和恢复状态在两端一致且可操作。", "反例：静默换模型/越权账户/无限收费或停掉全部独立分支失败。"],
    "test.resources", ["C16", "C11", "C13"], [("17_USER_JOURNEYS_AND_VALUE.md", "U09"), ("07_OPERATIONS_AND_EVOLUTION.md", "资源")])
add("W13-01", "装好就能配置的原生桌面工作台", ["W02-03", "W03-02", "W04-01", "W17-01", "W05-01"],
    ["DESKTOP/**", "UI/**", "tests/ui/**"],
    ["按19固定Mu渲染器入口接入已有Go核心；先替换workspace/session/provider/status原生客户端。",
     "安装启动即能自动发现/启动本地核心，OS主体bootstrap/安全续期不要求复制token或手动开服务。",
     "实现目录选择、模型列表/凭据保存/真实probe、首个session、空状态/失败重试。",
     "在Windows实际安装并从开始菜单打开；运行U01首次使用门，当前卡不接受整个W13。"],
    ["真实桌面首次使用可完成目录/模型/首个会话配置。", "反例：浏览器壳要求终端启动、手抄owner token、provider失败却显示成功均失败。"],
    "test.ui.routes", ["C23", "A10"], [("19_DESKTOP_IMPLEMENTATION_BLUEPRINT.md", "1-7"), ("22_CLIENT_INTERFACE_DETAILS.md", "full")], ["Windows_desktop_session"])
add("W13-02", "打通对话、工具、文件Diff与双端接续", ["W13-01", "W05-02", "W06-02"],
    ["DESKTOP/**", "UI/**", "tests/ui/**"],
    ["绑定23方法：流式输出/工具执行/队列/暂停取消/权限响应/附件和文件树Diff，所有按钮有生产者。",
     "文件保存使用base hash冲突校验；未保存草稿在切会话/刷新前提示；封存内容只能建候选。",
     "CLI创建session，Desktop接入同一个session查看、暂停、handoff，再CLI接续；双端抢写冲突明确。",
     "断网/崩溃/重开通过事件游标+快照恢复，不重放副作用、不丢Goal/费用/失败计数。"],
    ["真实CLI/Desktop操作同一任务、文件和事件，无第二调度器。", "反例：复制聊天记录假接续、按钮只变样式、冲突静默覆盖或取消残留worker失败。"],
    "test.ui.recovery", ["C23", "C24", "C25", "A04"], [("22_CLIENT_INTERFACE_DETAILS.md", "按钮与状态"), ("17_USER_JOURNEYS_AND_VALUE.md", "JRN-02")], ["Windows_desktop_session", "authorized_provider"])
add("W13-03", "完成11页前端交互与视觉可访问性", ["W13-02", "W08-02", "W12-02"],
    ["DESKTOP/**", "UI/**", "ui/design_tokens/**", "tests/ui/**"],
    ["按ui.contract逐页实现真正可操作的前端/API客户端；已实现服务用真实数据，尚未完成的实验/Jev/技能页用明确标FIXTURE的合同后端验证交互，W20-02再全部接最终真实服务。",
     "实现所有loading/empty/ready/error/forbidden/partial/stale/offline状态和可操作恢复。",
     "两主题五视口、200%缩放、键盘/焦点/读屏基础实际检查；320px无横溢出。",
     "HTML预览禁脚本和远程加载，超限附件下载或外部打开前明确提示；用原始截图与DOM证明。"],
    ["11页实际Desktop前端的交互、失败恢复和视觉矩阵有记录；固定后端与真实服务证据逐页区分，不提前声称W20全量集成。", "反例：离线reference/prototype截图或静态卡片不能证明真实前端；将固定后端当最终产品数据通过W20失败。"],
    "test.ui.visual", ["C17", "C18", "C23", "C24", "C25", "C26"], [("10_UI_UX_DESIGN.md", "full"), ("contracts/ui.contract.json", "full")], ["Windows_desktop_session"])
add("W14-01", "先用自己的CLI完成一件真实编码工作", ["W05-03", "W06-02", "W13-02"],
    ["execution/v2.4/live/**", "tests/e2e/**", "REAL_ISSUE_SCOPE/**"],
    ["按17候选问题池在当前版本复现一项尚未完成真实问题，冻结输入/允许文件/原始失败/独立判据。",
     "若免token问题已修好，则选当前缺失doctor --json等已要求能力；不回退修复或人为植入bug。",
     "通过已安装ResearchOS CLI实际让Agent读、改、执行检查，产生非空可审查diff和产物。",
     "独立Verifier重放冻结判据；Desktop打开同session审查，再恢复原任务，记录真实时间/成本/人工干预。"],
    ["实际用户问题被产品Agent完成且有可复核diff；只接受U02/U03切片。", "反例：施工Qoder直接改文件充当ResearchOS能力、手工先修或无diff假完成均失败。"],
    "test.cycle.live", ["A13", "A04", "C23"], [("17_USER_JOURNEYS_AND_VALUE.md", "JRN-01/JRN-02"), ("06_ACCEPTANCE_TESTS.md", "A13")], ["authorized_provider", "Windows_desktop_session"])
add("W14-02", "三来源研究、真实Jev和实验端到端闭环", ["W14-01", "W08-02", "W09-02", "W10-02", "W11-02", "W12-02"],
    ["execution/v2.4/live/**", "tests/e2e/**", "adapters/integration/**"],
    ["针对真实工作里的明确缺口启动研究，获取GitHub/X/论文三源真实记录和证据定位。",
     "对有依据的源码候选运行真实Jev建议，固定commit并在隔离工作区接入/实验。",
     "按同输入比较结果作采用/拒绝/观察/证据不足处置；无价值候选不强行采用。",
     "CLI/Desktop显示一致周期、实验、产物和接受链；缺源/缺标签仍PARTIAL并聚合资源请求。"],
    ["A13完整真实链可按版本和原始证据重放。", "反例：fixture改名LIVE、抓到材料当采用收益、缺来源显示COMPLETE均失败。"],
    "test.cycle.live", ["A13", "C05", "C06", "C07", "C19"], [("06_ACCEPTANCE_TESTS.md", "A13"), ("16_ADOPTION_JUDGMENT.md", "J03")], ["GitHub_read", "paper_source", "authorized_X_backend", "authorized_provider"])
add("W15-01", "研究证据编译候选技能并记录完整来源", ["W09-01", "W10-02", "W11-01", "W14-02"],
    ["adapters/skills/**", "internal/domain/skill*.go", "tests/skills/**"],
    ["按固定book-to-skill或现有提取器输入，记录实际覆盖/失败页/来源manifest，不凭exit0判完整。",
     "候选包含适用条件/操作/验证/反例/限制/负证据，提示注入只作为被分析文本。",
     "Fold-in生成新版本并保留旧版本与冲突选择；只写候选不自动发给所有项目。"],
    ["每个技能动作能追溯原文与证据，覆盖缺口真实显示。", "反例：只有SKILL文件、正文没读完却全覆盖或文中指令升级权限失败。"],
    "test.skills", ["A09", "C03", "C07", "C20"], [("06_ACCEPTANCE_TESTS.md", "A09"), ("11_EVALUATION_AND_INTEGRATION.md", "技能")])
add("W15-02", "以真实skill-up比较并有限启用技能", ["W15-01"],
    ["adapters/skills/**", "internal/domain/skill*.go", "tests/skills/**"],
    ["复用W10唯一评测适配器，冻结同输入比较无技能/旧技能/候选技能。",
     "注入退化、缺样本、SKIP、改测试等负例，保存原始报告并拒绝不合格候选。",
     "用途资格和独立接受通过才为选定项目启用，记录版本/回滚和客户端展示。"],
    ["技能收益或拒绝依据可重放，项目仍可回退旧版。", "反例：自行给候选评分、修改公共评测门、共享给未授权项目失败。"],
    "test.skills", ["A09", "C20", "C21"], [("16_ADOPTION_JUDGMENT.md", "J04")], ["skill_up_runtime", "authorized_provider"])
add("W16-01", "自我改进候选保持监督器和门槛隔离", ["W12-02", "W14-02", "W15-02"],
    ["internal/evolution/**", "adapters/evolution/**", "tests/evolution/**"],
    ["稳定supervisor与candidate隔离目录、凭据和发布权；候选只提议允许范围的路由/配置/流程改动。",
     "冻结问题、输入、基线和收益判据；复用现有实验/评测，不增加平行真相库。",
     "候选尝试改评测阈值/自身Acceptance/安全策略时拒绝并记录；合法失败保留证据。"],
    ["候选能迭代但不能修改自己的胜出规则或稳定监督器。", "反例：同Agent自评自批、以新Goal重置失败或直接改稳定分支失败。"],
    "test.evolution", ["A16", "C09", "C10", "C12", "C20"], [("07_OPERATIONS_AND_EVOLUTION.md", "演进"), ("06_ACCEPTANCE_TESTS.md", "A16")])
add("W16-02", "备份后小范围试用并验证自动回滚", ["W16-01", "W18-99"],
    ["internal/evolution/**", "tests/evolution/**", "execution/v2.4/evolution/**"],
    ["在已验证备份/恢复基础上跑基线和候选回归，独立Verifier只接受当前hash结果。",
     "canary限制范围并测正确性/延迟/成本，退化时回到已知稳定版本。",
     "保留失败候选、回滚原因和证据，禁止故障循环自动重新发布同一输入。"],
    ["真实候选试用、退化和回滚链可复现。", "反例：仅改模型自评分数或手写rollback日志，未恢复实际运行版本失败。"],
    "test.evolution", ["A16", "C09", "C10", "C12"], [("06_ACCEPTANCE_TESTS.md", "A16"), ("07_OPERATIONS_AND_EVOLUTION.md", "canary")])
add("W17-01", "首次本地主体引导与权限边界", ["W03-02"],
    ["internal/auth/**", "internal/host/**", "tests/security/**"],
    ["按22实现受OS用户保护的NativeBridge一次性OWNER初始化、重复引导保护及短期会话自动续期。",
     "provider凭据只经受保护原生入口入系统凭据库，普通CommandEnvelope/日志/事件中不出现秘密。",
     "绑定workspace根目录/项目身份，对读写/导入/工具执行统一校验路径、重解析点和权限。",
     "验证无凭据/过期/错项目/撤销用户无法利用HTTP、IPC、回放或文件读取。"],
    ["首次本地用户无需手抄后台token，后续访问和文件操作仍鉴权。", "反例：公开OWNER注册、另一OS用户接管、secret进argv或越界读写失败。"],
    "test.security", ["A10", "A11", "C02", "C22"], [("22_CLIENT_INTERFACE_DETAILS.md", "NativeBridge"), ("04_API_CONTRACTS.md", "鉴权")])
add("W17-02", "数据出口与独立holdout权限隔离", ["W17-01", "W06-01", "W09-01"],
    ["internal/auth/**", "internal/domain/artifact*.go", "tests/security/**"],
    ["在API/文件/日志/搜索/事件/备份全部出口执行PROJECT与VERIFIER_ONLY访问分级。",
     "独立Verifier持有自身身份；施工执行者无权读取正式标签、写入Acceptance或替换冻结门。",
     "用C22逐出口负例和凭据撤销测试，不把前端隐藏当隔离。"],
    ["正式holdout和评测标签仅授权Verifier可用，普通执行者无法绕过出口。", "反例：备份/全文检索/事件或异常堆栈泄露受限内容失败。"],
    "test.evaluation.security", ["C22", "A11", "C07"], [("06_ACCEPTANCE_TESTS.md", "C22"), ("11_EVALUATION_AND_INTEGRATION.md", "权限")])
add("W17-03", "手机安全接入、撤销与真实监督", ["W17-02", "W13-03", "W12-02"],
    ["internal/auth/**", "UI/**", "tests/mobile/**"],
    ["默认仅本地；使用用户已授权安全通道发布可认证的手机监督入口，不新建付费服务。",
     "设备配对短时单次、防重放；设备撤销即不能重连/回放/提交控制。",
     "实际手机完成查看、暂停、响应资源和恢复，验证项目/费用/通知一致与离线恢复。"],
    ["真实手机监督流程和撤销回执完整。", "反例：响应式截图冒充手机使用、匿名公网控制面或撤销后仍可控制失败。"],
    "test.ui", ["A10", "A11", "C17"], [("06_ACCEPTANCE_TESTS.md", "A10/A11")], ["real_mobile_device", "authorized_remote_channel"])
add("W18-01", "一致性备份和迁移前快照", ["W03-02", "W12-01"],
    ["internal/backup/**", "scripts/backup/**", "tests/backup/**"],
    ["备份唯一状态/接受/资源配置/技能和必要续跑信息，SQLite在线备份保持一致。",
     "记录文件manifest/hash/revision、事件游标及可重建索引；凭据按受控导入策略处理。",
     "迁移前检查旧数据与schema版本，先备份、在副本试迁移再切换，失败保留原库。"],
    ["备份可校验且保留目标、任务、费用/失败计数及权限版本。", "反例：复制写入中的db漏WAL、把密钥明文打包或迁移直接破坏原库失败。"],
    "test.backup", ["A12", "C11"], [("07_OPERATIONS_AND_EVOLUTION.md", "备份"), ("18_EXISTING_REPOSITORY_MIGRATION.md", "迁移")])
add("W18-02", "新目录恢复并核对双端上下文", ["W18-01", "W05-02", "W06-02", "W13-02"],
    ["internal/backup/**", "scripts/backup/**", "tests/backup/**"],
    ["恢复到新空目录，验证manifest、引用、事件游标及资源重新绑定。",
     "已发生外部副作用不重放，未知费用先对账；旧活动lease不得误复用新PID。",
     "CLI/Desktop恢复同一session/Goal/下一步，U06要求用户只补确实不可迁移的凭据。"],
    ["从备份恢复实际可续跑的任务和文件，旧现场不变。", "反例：只有文件齐全却无法继续，重复外部写入、把恢复当新项目或清零失败失败。"],
    "test.backup", ["A12", "C11"], [("17_USER_JOURNEYS_AND_VALUE.md", "U06"), ("06_ACCEPTANCE_TESTS.md", "A12")])
add("W19-01", "冻结隔夜故障计划并启动真实运行", ["W14-02", "W17-03", "W18-02"],
    ["tests/recovery/**", "execution/v2.4/overnight/**"],
    ["按A14固定实际时长、起止时间、故障时点、成功条件和受控测试工作区。",
     "使用真实产品CLI/Desktop/provider启动，记录host/process identity和初始Goal/计数。",
     "在授权测试环境注入断网/杀受管进程/休眠等，保留前后快照和系统日志。",
     "长时等待用检查点续跑；不能压缩时钟、伪造睡眠或以fixture替代真实隔夜。"],
    ["真实隔夜运行有原始时间线和故障计划执行证据。", "反例：到时长前宣布通过、误杀无关用户进程或人为重置会话失败。"],
    "test.overnight", ["A14", "C11", "C13"], [("06_ACCEPTANCE_TESTS.md", "A14"), ("07_OPERATIONS_AND_EVOLUTION.md", "Windows")], ["Windows_desktop_session", "authorized_provider", "real_elapsed_time"])
add("W19-02", "次日从两端恢复并独立核验", ["W19-01"],
    ["tests/recovery/**", "execution/v2.4/overnight/**"],
    ["次日打开桌面显示昨夜真实结果/未完事项/资源问题和下一步，CLI读取相同状态。",
     "核对无孤儿进程、无重复副作用、游标去重、未知费用对账及有限合并研究窗口。",
     "重放U05，独立Verifier核算全时段证据后才接受A14。"],
    ["用户无需重新解释目标即可继续，错误和实际未完成项可见。", "反例：恢复后全显示成功却遗漏工作、计数重置或残留provider任务失败。"],
    "test.overnight", ["A14", "C11", "C13"], [("17_USER_JOURNEYS_AND_VALUE.md", "U05"), ("06_ACCEPTANCE_TESTS.md", "A14")])
add("W20-01", "制作Windows CLI和Desktop安装产物", ["W13-03", "W17-03", "W18-02"],
    ["scripts/release/**", "DESKTOP/**", "docs/release/**", "tests/install/**"],
    ["固定core/CLI/Desktop/protocol/schema版本和hash，复用选定壳打包机制生成可安装产物。",
     "携带实际依赖或明确合法安装前提；无签名如实说明，不申请账号或假称可信签名。",
     "实现升级前备份/版本兼容检查，回退/卸载保留用户数据，明确目录。",
     "在干净Windows用户或VM按文档安装，从开始菜单和新终端分别运行，验证U08。"],
    ["两个真实安装入口无需开发者命令，首次使用和升级路径可复现。", "反例：只在源码目录npm dev、缺运行时或卸载删除用户数据失败。"],
    "release.reproduce", ["A15", "A01"], [("19_DESKTOP_IMPLEMENTATION_BLUEPRINT.md", "安装"), ("06_ACCEPTANCE_TESTS.md", "A15")], ["clean_Windows_target"])
add("W20-02", "全量发布门和真实证据覆盖复现", ["W20-01", "W16-99", "W19-99"],
    ["scripts/release/**", "docs/release/**", "execution/v2.4/release/**"],
    ["按22父任务/42用例唯一final owner检查当前代码/spec/数据hash与有效接受；旧PASS按影响重验。",
     "确认H/P/B/J/U能力、Jev源码采用、真实skill-up、11页真实API和所有LIVE门无空洞。",
     "在干净目标运行完整发行复现，产物清单、原始报告、限制和恢复命令封存。",
     "只做已有授权的发布动作；缺外部发布授权保留本地候选，不能伪称已发布。"],
    ["全部正式门由独立Verifier接受，发行产物与证据版本一致。", "反例：fixture覆盖LIVE、waiver降门、只做哈希审计不做干净安装均失败。"],
    "release.reproduce", ["A15", "A13", "A14", "A16"], [("06_ACCEPTANCE_TESTS.md", "A15"), ("12_IMPLEMENTATION_AND_HANDOFF.md", "发布")], ["clean_Windows_target"])
add("W21-01", "交付实际价值、操作手册与剩余边界", ["W20-99"],
    ["docs/handoff/**", "execution/v2.4/handoff/**"],
    ["汇总真实完成任务、未采用候选、时间/成本/人工干预/可靠性与未知项，分离模型分数和用户收益。",
     "交付CLI/Desktop安装、首次配置、日常任务、暂停续跑、备份恢复与诊断手册。",
     "审计R01-R20/42用例/22任务/H-P-B-J-U覆盖；输出当前版本、下一步、资源状态与回滚入口。",
     "下一轮只来自真实未解决缺口；不将无限演进设成当前交付永不结束的条件。"],
    ["用户可安装、使用、隔夜恢复且知道还缺什么，最终完成有独立接受。", "反例：只有文档数量/框架数量或一份未验证完成声明失败。"],
    "acceptance.audit", ["C05", "C20", "A15"], [("17_USER_JOURNEYS_AND_VALUE.md", "价值记录"), ("12_IMPLEMENTATION_AND_HANDOFF.md", "交付")])

def render(step):
    lines = [f"# {step['id']} · {step['title']}", "", f"父任务：{step['parent_task']}；类型：{step['phase']}；初始状态：NOT_STARTED。", "",
             "本文件是 contracts/execution.plan.json 的生成视图，不单独修改；接受本卡不自动接受父任务。", "",
             "## 前置与输入", "", "依赖卡：" + ("、".join(step['dependencies']) or "无") + "。", ""]
    lines += [f"- [{r['path']}](../../{r['path']})：{r['selector']}" for r in step['read_refs']]
    for title, key in [("允许修改范围", "write_scope"), ("具体步骤", "actions"), ("预期交付", "deliverables")]:
        lines += ["", "## " + title, ""] + [f"{i}. {v}" for i, v in enumerate(step[key], 1)]
    paths_note = ("W00/W01及W02-01/02属于引导步骤：上列小写路径是已确认仓库根下的直接相对路径，不等待W02注册；仅创建本卡列出的新版施工/资格文件，旧spec/身份/登记不变。" if step['parent_task'] in {'W00','W01'} or step['id'] in {'W02-01','W02-02'}
                  else "路径是W02登记的仓库相对映射；缺映射先修W02注册，不按名字凭空新建架构。REAL_ISSUE_SCOPE只在冻结问题时展开成具体文件。")
    lines += ["", paths_note, "", "## 检查与回执", ""]
    for check in step['checks']:
        lines.append(f"- `{check['id']}`：{check['expected']}")
    for cmd in step['verification_commands']:
        lines += ["", f"cwd={cmd['cwd']}；binding={cmd['binding']}", "", "```text", " ".join(cmd['argv_template']), "```"]
    lines += ["", "正式用例：" + "、".join(step['affected_formal_cases']) + "；本卡只检查所列增量，正式终验见父任务-99。",
              "资源前提：" + ("、".join(step['resource_requirements']) or "本地开发资源；正式资源以父用例为准") + "。", "", "## 失败与恢复", ""]
    lines += ["- " + v for v in step['limits']] + ["", step['rollback'], "", "## 下一步", "",
        "保存证据到 `" + step['handoff']['receipt_directory'] + "`，由不同身份独立复核后登记step_state。更新checkpoint记录next_step_id、失败计数、输入版本和下一条命令。",
        "执行 `python <SPEC>/tools/task_packet.py next --state <REPOSITORY>/execution/v2.4/step_state.json` 选择下一张可做卡；没有READY卡时报告具体依赖/资源，不能写DONE。", ""]
    if step.get('formal_final_cases') is not None:
        lines += ['本卡唯一最终负责用例：'+('、'.join(step['formal_final_cases']) or '无；只接受父任务自身门，关联用例由其final owner终验')+'。', '']
    return "\n".join(lines)

def main():
    primary={
      'W00':'package.validate','W01':'core.qualify','W02':'build.check','W03':'test.domain','W04':'test.context',
      'W05':'test.runtime','W06':'test.orchestration','W07':'test.sources.live','W08':'test.research.fixture','W09':'test.retrieval',
      'W10':'test.experiments','W11':'test.jev.live','W12':'test.resources','W13':'test.ui','W14':'test.cycle.live',
      'W15':'test.skills','W16':'test.evolution','W17':'test.security','W18':'test.backup','W19':'test.overnight',
      'W20':'release.reproduce','W21':'acceptance.audit'}
    overrides={'W03-G01':'contracts.validate','W03-G03':'contracts.validate','W06-G02':'test.context','W06-P02':'test.context',
      'W07-G01':'test.sources.fixture','W10-G03':'test.evaluation.fixture','W10-H05':'test.evaluation.fixture','W10-SKILLUP':'test.evaluation.fixture',
      'W11-G01':'test.jev.fixture','W11-H02':'test.orchestration','W12-G02':'test.runtime','W12-H03':'test.orchestration',
      'W12-H04':'test.runtime','W13-G02':'test.ui.visual','W13-G03':'test.ui.routes','W13-P03':'test.ui.routes','W13-U04':'test.ui.routes',
      'W16-G01':'acceptance.audit','W17-G02':'test.ui','W17-G03':'test.evaluation.security','W20-G01':'acceptance.audit'}
    # Capability contracts already freeze their precise check-to-command binding.
    for name in ['harness.contract.json','product.contract.json','adoption.contract.json','delivery.contract.json']:
        for cap in json.loads((OUT/'contracts'/name).read_text(encoding='utf8')).get('capabilities',[]):
            if cap.get('check_id') and cap.get('command_key'): overrides[cap['check_id']]=cap['command_key']
    gate_bindings=[];case_bindings=[]
    early=['W00-01','W00-02','W00-03','W01-01','W01-02','W01-03','W02-01','W02-02','W02-03','W03-01','W03-02',
           'W17-01','W04-01','W13-01','W04-02','W12-01','W05-01','W05-02','W05-03','W06-01','W06-02','W13-02','W14-01']
    for step in STEPS:
        step['priority']=(early.index(step['id'])*10+10) if step['id'] in early else step['priority']+1000
    for t in TASKS['tasks']:
        tid=t['task_id']; own=[s['id'] for s in STEPS if s['parent_task']==tid]
        final_priority=max(s['priority'] for s in STEPS if s['id'] in own)+1
        add(tid+'-99', '父任务正式验收：'+t['title'], own+[d+'-99' for d in t['depends_on']],
            ['execution/v2.4/receipts/'+tid+'/**', 'execution/v2.4/step_state.json', 'execution/v2.4/checkpoint.json'],
            ['逐项核对父任务development_checklist/task_gate_checks，所有必须项有当前输入和原始证据。',
             '只运行该父任务拥有的正式用例；引用其他用例作为中间集成检查，不夺取其final owner。',
             '依verification_command_selection绑定每个check/case真实处理器，FIXTURE/DEVELOPMENT/LIVE独立记录。',
             '由独立Verifier重放并签收；资源缺失保留BLOCKED/PARTIAL，不缩减42用例最终门。'],
            ['父任务所有门和本父任务final_owner用例被独立接受，证据版本一致。', '反例：仅子卡完成、文档/fixture或旧PASS代替当前正式验收失败。'],
            t['verification_command_keys'][0], t['acceptance_ids'], [('06_ACCEPTANCE_TESTS.md', ','.join(t['acceptance_ids']))])
        step=STEPS[-1]; step['phase']='PARENT_FINAL_GATE'
        step['priority']=final_priority
        step['formal_final_cases']=[c for c, owner in TASKS['acceptance_final_owners'].items() if owner==tid]
        commands=[]
        for gate in t['task_gate_checks']:
            gid=gate['check_id'];key=overrides.get(gid,primary[tid])
            assert key in t['verification_command_keys'],(gid,key)
            argv=['python','execution/command_dispatcher/dispatch.py',key,'--task-id',tid,'--check-id',gid]
            if tid=='W01':argv=['python','qualification/v2.4/qualify.py','--check-id',gid]
            if tid=='W00':argv=['python','tools/validate_package.py']
            binding={'key':key,'cwd':'SPEC' if tid=='W00' else 'REPOSITORY','argv_template':argv,
                     'binding':'Exact parent check selector; W00 additionally requires independent inventory/migration evidence review. Reuse a still-current verified receipt instead of repeating unchanged checks.',
                     'task_id':tid,'check_id':gid,'expected_assertion_ids':[gid]}
            commands.append(binding);gate_bindings.append(binding)
        for cid in step['formal_final_cases']:
            for key in CM[cid]['command_keys']:
                binding={'key':key,'cwd':'REPOSITORY','argv_template':['python','execution/command_dispatcher/dispatch.py',key,'--task-id',tid,'--case-id',cid],
                  'binding':'Exact formal case selector. Must report its frozen assertion IDs at the required mode, not an aggregate empty PASS.',
                  'task_id':tid,'case_id':cid,'expected_assertion_ids':[a['id'] for a in CM[cid]['assertions']]}
                commands.append(binding);case_bindings.append(binding)
        step['verification_commands']=commands
        if tid=='W00': step['verification_commands']=[{'key':'package.validate','cwd':'SPEC','argv_template':['python','tools/validate_package.py'],'binding':'ALREADY_PRESENT; plus manually verified inventory/migration evidence'}]
        t['execution_steps']=[s['id'] for s in STEPS if s['parent_task']==tid]
        t['final_step_id']=tid+'-99'
        scope=[p.replace('EXECUTION/v2.4/','EXECUTION/').replace('SPEC/v2.4/','SPEC/').replace('ADR/ADR-001.md','ADR/**').replace('EXECUTION/command_dispatcher/','WORKSPACE/execution/command_dispatcher/') for p in t['allowed_paths']]
        if tid=='W00':scope=[p for p in scope if p!='EXECUTION/project_identity.json']
        for s in STEPS:
            if s['parent_task']==tid:scope.extend(s['write_scope'])
        t['allowed_paths']=list(dict.fromkeys(scope))
    TASKS['path_aliases']['SPEC']='当前只读快照的精确目录 spec/v2.4；SPEC/**不会再次拼接v2.4。升级写新版本目录，不覆盖已有快照。'
    TASKS['path_aliases']['QUALIFICATION']='候选worktree内 qualification；v2.4子目录存本轮隔离资格驱动/源码/证据，不作产品权威库。'
    TASKS['verification_command_selection']['parent_check_bindings']=gate_bindings
    TASKS['verification_command_selection']['formal_case_bindings']=case_bindings
    TASKS['verification_command_selection']['slice_bindings']='execution.plan.json steps[].verification_commands; W00/W01 and W02-01/02 use direct bootstrap commands before the dispatcher is bound.'
    plan={'package_version':'2.4.0','artifact_kind':'bounded_execution_plan','product_status':'NOT_STARTED',
          'canonical_source':'contracts/execution.plan.json','generated_views':'tasks/steps/{id}.md',
          'scope':'Construction routing only; parent WBS and 42 formal acceptance gates remain authoritative.',
          'state_file':'execution/v2.4/step_state.json','steps':STEPS}
    (OUT/'contracts/execution.plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    (OUT/'contracts/tasks.json').write_text(json.dumps(TASKS,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    folder=OUT/'tasks/steps'; folder.mkdir(parents=True,exist_ok=True)
    for step in STEPS: (folder/(step['id']+'.md')).write_text(render(step),encoding='utf8')
    print('Authored',len(STEPS),'execution cards; formal product gates NOT_RUN.')

if __name__=='__main__': main()

