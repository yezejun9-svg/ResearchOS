"""One-off authoring helper. This is not a product implementation or runtime."""
from __future__ import annotations
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess

WORK = Path(__file__).resolve().parents[1]
SRC = WORK / "ResearchOS_Implementation_Package_v2.3" / "ResearchOS_Implementation_Package_v2.3"
OUT = WORK / "ResearchOS_Implementation_Package_v2.4"
REPO = WORK / "research-os"

def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def put(rel, text):
    target = OUT / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text.rstrip() + "\n", encoding="utf-8")

def putj(rel, value):
    put(rel, json.dumps(value, ensure_ascii=False, indent=2))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO, encoding="utf-8").strip()

def lift(text):
    return text.replace("2.3.0", "2.4.0").replace("v2.3", "v2.4").replace("包2.3", "包2.4")

def seed_owned_files():
    # The protocol and new research/blueprint documents have separate owners.
    owned = list(SRC.glob("[0-1][0-9]_*.md"))
    owned += [p for p in (SRC / "contracts").glob("*.json") if p.name != "client.protocol.schema.json"]
    owned += list((SRC / "examples").glob("*"))
    owned += [SRC / "tools/validate_package.py", SRC / "ui/design-tokens.json"]
    for path in owned:
        if path.is_file():
            put(path.relative_to(SRC).as_posix(), lift(path.read_text(encoding="utf-8")))

def baseline():
    rels = ["AGENTS.md", "execution/project_identity.json", "execution/route.json",
            "execution/path_ownership.json", "execution/commands.json", "execution/checkpoint.json",
            "docs/handoff/current-construction.md", "go.mod", "go.sum", "apps/web/package.json",
            "apps/web/src/main.jsx", "apps/control/main.go"]
    identity = load(REPO / "execution/project_identity.json")
    route = load(REPO / "execution/route.json")
    evidence = {
        "scope": "READ_ONLY_REPOSITORY_OBSERVATION_NOT_PRODUCT_ACCEPTANCE",
        "observed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "repository_root": str(REPO), "head": git("rev-parse", "HEAD"),
        "branch": git("branch", "--show-current"),
        "git_status_porcelain": git("status", "--porcelain=v1", "--untracked-files=normal").splitlines(),
        "project_id": identity["project_id"], "old_spec": "spec/v2.0",
        "selected_route": route["selected_route"],
        "old_spec_manifest_sha256": identity["spec_manifest_sha256"],
        "source_package_manifest_sha256": digest(SRC / "PACKAGE_MANIFEST.json"),
        "file_hashes": {p: digest(REPO / p) for p in rels},
        "observed_capabilities": [
            "Go domain/control + SQLite + React web; existing product code and evidence",
            "Explicit --bootstrap-owner administrative command exists",
            "Current web AuthGate requires a manually supplied in-memory bearer token",
            "Initial Owner token TTL is 900 seconds; no native Desktop onboarding proof",
            "Historical acceptance and current v2.4 acceptance are different scopes"
        ],
        "not_run": ["No product tests", "No database or service actions", "No credential reads",
                    "No claim that old PASS satisfies new CLI/Desktop assertions"],
    }
    putj("references/Repository_Baseline_2026-10-01.json", evidence)

def amend_docs():
    prepend = {
        "01_PRD.md": """## v2.4 接续与交付优先级

本版针对实际已经存在的 ResearchOS v2.0 仓库继续建设。文中 NOT_STARTED/NOT_RUN 是 v2.4 合同初值，不能抹掉旧代码和历史证据。先按18核对现场与迁移，后按17的三个真实问题交付；完整范围仍为所有R01–R20。

产品定位默认是可长期接续项目的自有研发 Agent。优先顺序为：真实 CLI/桌面任务与首次使用→研究到复用→经过评测的自我改进。所有完整门仍须通过，阶段顺序不构成删减。用户本轮授权由执行者补齐工程默认，不再要求Founder先补数据库、端口或工具选型表。

体验与价值基线从首个可用切片采集；W21汇总已有证据。JRN-01–04、ISSUE-FIRST-USE-001/CONTINUITY-001/REUSE-001、U01–U09见17及delivery.contract.json。零重复索取已有背景、零手工管理命令完成正常首次使用、真实文件/测试和接续是硬条件；改善百分比仍须实测。
""",
        "02_TECHNICAL_DESIGN.md": """## v2.4 现场接续架构与客户端边界

默认继续复用现有 Go/SQLite 业务权威，Mu CLI/Agent worker/Desktop 作为经过资格的执行与客户端源码。共享核心是一处逻辑权威而非强制单一语言或单进程。Go 调度与接受，Mu/Pi worker 只运行一次已委派 Agent 循环；上游独立 /goal 调度必须映射或关闭。19给出真实NativeClientContext/RPC接合点，18给出现有目录迁移；W01仍须验证，不能凭本文宣布兼容通过。

本地协议升级为 researchos-client/2，typed请求、结果、SessionSnapshot和事件见22及client.protocol.schema.json。凭据明文只走瞬态受限native桥，不进入CommandEnvelope、journal或事件。受信宿主完成本地身份鉴别/Owner引导/短会话续接；普通网页renderer不获得公开Owner创建权。目录注册、文件树/读写/diff、模型目录/探针、会话更新与批准处理都有具体方法，不交给UI猜接口。

现有HTTP领域API继续用于业务事务；本地协议是它们和授权工作区工具的同一边界适配。文件写入校验内容hash、session revision、writer_epoch及任务授权；禁止以任意绝对路径开放fs。API字段版本与上游原生事件映射由W02/03串行整合。
""",
        "03_DATA_CONTRACTS.md": """## v2.4 客户端与接续数据补充

领域实体保持本文件及domain.schema.json；新增客户端消息/SessionSnapshot/原生瞬态桥定义由22与client.protocol.schema.json权威管理，不再另写不一致的字段表。Session索引关联现有project/goal/task/run及上游会话日志；索引和事件写入经唯一宿主。

SourceCandidate/AdoptionDecision仍是Artifact内容。施工execution.plan/step_state/checkpoint不进入产品业务数据库，也不授予ACCEPTED；规格模板NOT_RUN与真实施工状态分开。每个reference必须有真实生产者、范围、生命周期及回收规则，见22。明文凭据不是持久字段，不写入协议回放样本；样例仅用虚构值。

协议 /2 握手失败给出明确版本错误，不降级为裸 object。旧库/新字段迁移先在备份副本验证，旧证据按18逐项映射。
""",
        "04_API_CONTRACTS.md": """## v2.4 本地客户端操作对接

本HTTP OpenAPI与22的本地协议并存：HTTP承载领域操作；CLI/Desktop经同一宿主适配调用。不能把新增本地method当作上游Mu现成API或另建一套领域HTTP真值。client.protocol.schema.json定义researchos-client/2请求、按method约束的返回、SessionSnapshot和按type约束的事件。product.contract.json提供methods/payload/result映射；ui.contract.json将控件绑定到这些方法。

凭据输入与系统目录选择为受限native桥，检查sender/frame和本机身份；密钥不会通过普通CommandEnvelope、Artifact、事件或日志。host.configure只接受脱敏引用和已验证配置。普通permission.respond仅处理当前作用域待决请求，不能清除系统policy拒绝或提升调用者权限。

同一command_id不同请求拒绝；写入校验revision/epoch和文件hash。请求接受、工具完成、独立验收分别返回/投影；所有缺失handler非零NOT_IMPLEMENTED，不允许空成功响应。接口与错误的逐项详情及生产者见22。
""",
        "07_OPERATIONS_AND_EVOLUTION.md": """## v2.4 可用性交付与方向检查

正常本地首次使用不要求复制Owner token、手工启动数据库或编辑运行配置JSON。受保护宿主完成本机身份引导与短会话续接；服务身份/旧数据切换仍遵循18，不因新规格自动重新尝试被拒绝动作。

在原origin key无进展规则之外，每三张实施卡或两个无用户能力输出的回合采集value_checkpoint。连续两个检查点只有基础设施变化时优先打通最短真实用户流程，暂缓非阻塞性扩展；这不是删除完整验收要求。W18未验证前禁止W16晋升；稳定版本可保持不变。正式来源/Jev/手机/8小时门仍需要实际资源与独立证据。
""",
        "09_COMPONENT_DECISIONS.md": """## v2.4 已核实的具体复用入口

新核实见references/Desktop_Reuse_Verification_2026-10-01.md和19。Mu固定commit仍是优先候选；保留现有Go/SQLite业务权威，优先注入Mu NativeClientContext并经受控RPC委派worker。备选仅在Mu具体能力失败后考虑Pi及已核实的Craft Agents壳；不安装三个调度器或三套主UI。Craft仓库当前规范URL及固定commit以本轮证据为准。

Claude/Qoder是体验对照。本轮未取得其官方Desktop前端可直接fork的开源依据；Claude Code公开仓库不等于Claude Desktop前端。禁止将受版权限制的官方客户端解包复制。用户允许clone适合的开源前端，实际采用仍遵守15/16的固定源码、许可、验证和独立接受。
""",
        "10_UI_UX_DESIGN.md": """## v2.4 桌面工作区优先

19是本版具体施工蓝图，22是控件调用合同；本文件的11视图、token、可访问性和状态要求保留。主入口是S01真实会话工作区，不以研究统计卡片占据首屏。左侧项目/会话，中央会话/工具/固定输入，右侧文件/diff/Goal；研究/知识/团队/资源在同一导航的次级视图。

新交互设计预览为ui/workbench-prototype.html；旧ui/reference.html保留全部视图参考。两者均为FIXTURE示例，不能计为真实Desktop或视觉验收。必须验证中文输入法、streaming、取消/排队、错误重试、模型选择、权限请求、文件CAS保存与双端交接。首用必须从系统目录选择和已有资源配置直接进会话，不让用户手工取得token。
""",
        "11_EVALUATION_AND_INTEGRATION.md": """## v2.4 真实工作基线前置

17定义首个真实任务和用户介入指标。W05/13早期切片即采集输入、人工补步骤、重复解释、工具正确性与耗时；W14同条件比较并保存有来源Outcome，W21汇总。Qoder+Qwen3.8-Flash是施工宿主选择，不自动等同ResearchOS产品provider/Jev资格；一个无工具读取探针不能计入A04/A08/A13。

新typed client正负例属于协议fixture；完整live门及正式留出不变。小模型同一会话的自评不作为独立验收，必须按既有身份、冻结输入及权限分离要求检查实际产物。
""",
        "12_IMPLEMENTATION_AND_HANDOFF.md": """## v2.4 可直接交接的执行入口

先读00、08、20、18。使用tools/start_qoder.ps1启动本机已核实的Qoder及固定Qwen3.8-Flash，再将GOAL_START.txt一行交给TUI；不把/goal当未验证的shell子命令。完整计划contracts/execution.plan.json由tools/task_packet.py读取，任务卡是其可重建投影。只读选择器不执行任务、不签发验收。

逐卡运行、保存真实证据、独立审查、再取下一卡。早期纵向切片按step依赖实现和演示；父WBS及正式用例的完成仍受tasks.json完整依赖和最终owner约束。缺live资源只阻塞相应卡；没有可继续卡时保存具体恢复入口。所有新施工状态写execution/v2.4，原仓库和旧spec/回执保留。
""",
        "13_HARNESS_DESIGN.md": """## v2.4 施工宿主与产品Harness分开

本轮施工首选Qoder 1.1.64及目录名Qwen3.8-Flash，真实/goal语法和恢复见20。Mu仍是产品CLI/Agent/Desktop复用候选。Qoder的Goal状态不替代ResearchOS AcceptanceReceipt；turn上限不清除业务重试计数，也不证明关闭终端后仍有持久进程。

单卡上下文由tools/task_packet.py生成，包含父任务、输入、依赖、受影响路径、具体动作与断言。不得只读取任务标题或checker截取后的目标。当前代码hash与完整必需ID集合一起判定，H01–H10和reuse_selection资格仍完整保留。数据/取消/权限/事件的客户端边界按22。
""",
        "14_CLI_DESKTOP_PRODUCT.md": """## v2.4 可用性与接口闭合补充

17定义必须亲自操作的首日/CLI/双端/研究流程，19给出复用源码和控件施工步骤，22给出researchos-client/2全部请求、typed结果和事件。新包按18接续已有Go/SQLite/React，不从空库假设开工。保留本文件P01–P07/B01–B02，另外U01–U09落入原42例，完整范围不缩减。

自有CLI要覆盖真实交互、JSONL、模型/工具、修改测试、目标续跑、诊断、取消恢复。Desktop有安装包、自己的品牌、首次引导、聊天与文件工作区、可操作设置和同会话接续。只修改窗口标题、套壳旧网页、能打开Mu、只连接外部CLI，均未达到这些要求。成熟源码复用后仍须以自己的发行件完成真实流程。
""",
        "15_NEW_PROJECT_WORKFLOW.md": """## v2.4 当前仓库与普通任务的适用范围

新项目和既有项目新增大能力执行完整流程；当前ResearchOS走18的EXISTING_CONTINUATION，保留永久身份及已有资产。普通小修复复核已有本地记录和受影响代码，不为每条聊天重新跑三来源全量选型。研究由当前问题驱动；没有候选优势时保持现状。Jev reuse_selection及整仓/模块/依赖的真实采用要求继续完整生效。
""",
        "16_ADOPTION_JUDGMENT.md": """## v2.4 采用后的实际用户能力

除G01–G07外，候选适配报告关联17中的当前真实问题与delivery能力；减少源码量只是观察，不替代真实CLI/Desktop效果。Mu/Craft等前端候选通过19的固定来源和接口比较，合同以22为准，不让UI自行扩展协议。Qoder模型目录可见只证明施工资源候选，不证明Jev或产品provider通过资格。负结果、保持现状和明确阻塞均继续合法。
"""
    }
    for rel, section in prepend.items():
        path = OUT / rel
        text = path.read_text(encoding="utf-8")
        first, rest = text.split("\n", 1)
        put(rel, first + "\n\n" + section.strip() + "\n\n" + rest.lstrip())
    # Remove factual statements that described a greenfield package, not this continuation.
    replacements = {
        "完整产品尚未开始；当前交付是实施规格。": "当前交付为v2.4实施规格；既有v2.0代码与证据按18接续，新版产品门尚未验收。",
        "本版v2.4仍定义尚未开工的首版产品。": "本版v2.4定义接续既有仓库后的目标产品。",
        "本包v2.4仍定义尚未开工的首版产品。": "本包v2.4定义接续既有仓库后的目标产品。",
        "本次用户表示尚未开工；仍以现场实际证据为准。": "本次已确认存在ResearchOS仓库；按18实读并保护现场。",
        "先创建全新": "仅无合法既有仓库时创建全新",
    }
    for path in OUT.glob("[0-1][0-9]_*.md"):
        if int(path.name[:2]) > 16:
            continue
        text = path.read_text(encoding="utf-8")
        for old, new in replacements.items():
            text = text.replace(old, new)
        put(path.name, text)

def mutate_base_contracts():
    tasks = load(OUT / "contracts/tasks.json")
    cases = load(OUT / "contracts/acceptance.json")
    tm = {t["task_id"]: t for t in tasks["tasks"]}
    cm = {c["id"]: c for c in cases["cases"]}
    w00 = tm["W00"]
    w00["title"] = "既有仓库接续、本地盘点与v2.4规格冻结"
    w00["input"] = ["完整v2.4实施包及当前合法ResearchOS仓库；旧规格、身份、Git/worktree和未提交成果；本次接续授权。"]
    w00["deliverable"][0] = "保持既有ResearchOS永久身份；在隔离候选分支冻结spec/v2.4；真实现场/迁移影响清单；execution/v2.4施工命名空间。无合法仓库时才新建独立research-os。"
    w00["deliverable"][1] = "execution/v2.4/step_state.json及checkpoint.json；原bootstrap_ledger保持历史；由独立Verifier接受当前输入下的子门。"
    w00["integration_strategy"]["workspace"] = "已有仓库优先隔离分支/worktree，保留永久project_id；W01用资格沙箱；不得删除旧仓库重建。"
    for gate in w00["task_gate_checks"]:
        if gate["check_id"] == "W00-G02":
            gate["check"] = "实读既有仓库身份/Git/worktree/修改；仅无合法仓库时新建；核对v2.4接续范围。"
            gate["expected"] = "永久身份保留，用户改动与旧规格不覆盖，新旧施工记录可追溯；未导入项目不访问。"
        if gate["check_id"] == "W00-G04":
            gate["check"] = "冻结spec/v2.4和迁移ADR，建立execution/v2.4施工状态；由外部Verifier按当前证据复核。"
            gate["expected"] = "旧台账及回执不改，旧PASS不整批追认；新子步骤可在产品服务建成前独立取证。"
    w00["allowed_paths"] += ["WORKSPACE/AGENTS.md", "SPEC/v2.4/**", "EXECUTION/v2.4/**", "ADR/**"]
    tasks["continuation_policy"] = {
        "default_mode": "EXISTING_CONTINUATION", "authority": "18_EXISTING_REPOSITORY_MIGRATION.md",
        "keep_project_identity": True, "keep_old_spec_and_receipts": True,
        "new_construction_namespace": "execution/v2.4", "bulk_copy_old_PASS": False,
        "step_plan": "execution.plan.json", "parent_dependencies_remain_binding": True,
        "early_slice_completion_is_whole_task_acceptance": False
    }
    for t in tasks["tasks"]:
        t["continuation_notes"] = "先核对当前实现与旧证据，按18只补受影响缺口；状态初值是v2.4目标，不表示旧成果不存在。"
        t["allowed_paths"] = list(dict.fromkeys(t["allowed_paths"] + [f"EXECUTION/v2.4/receipts/{t['task_id']}/**"]))
    delivery = {
        "package_version": "2.4.0", "product_status": "NOT_STARTED",
        "authority": "17_USER_JOURNEYS_AND_VALUE.md",
        "priority": ["USABLE_OWN_CLI_AND_DESKTOP", "PROJECT_DRIVEN_RESEARCH_AND_REUSE", "EVALUATED_SELF_IMPROVEMENT"],
        "all_original_requirements_remain_required": True,
        "first_real_issues": ["ISSUE-FIRST-USE-001", "ISSUE-CONTINUITY-001", "ISSUE-REUSE-001"],
        "capabilities": [],
        "value_checkpoint": {"after_step_count": 3, "no_user_capability_rounds": 2,
                             "no_value_checkpoints_before_replan": 2,
                             "new_candidates_alone_count_as_value": False,
                             "amount_cap": None,
                             "does_not_lower_product_acceptance": True}
    }
    caps = [
      ("U01", "无需手工token的首次使用", "W17", "A10", "test.security",
       "干净Windows用户通过安装包选择目录、配置已有模型、进入真实会话并跨15分钟重开；不执行内部管理命令、不复制Owner token；受信本机身份及短会话续接有效，普通renderer不能创建Owner。"),
      ("U02", "完整CLI真实编码任务", "W05", "A04", "test.runtime",
       "自有researchos的交互/JSONL/init/run/goal/resume/status/cancel/doctor/config及斜杠入口有真实处理器；中文输入、流式工具、读改文件和测试完成，取消结清子进程，固定模型不静默更换。"),
      ("U03", "CLI Desktop CLI同任务交接", "W14", "A13", "test.cycle.live",
       "实际CLI到Desktop再回CLI接续同一session/Goal和产物；只有一名有效writer，旧epoch拒绝，事件/工具/费用收敛；用户无需重复提供已保存背景，真实研究及代码适配/拒绝证据齐全。"),
      ("U04", "typed客户端与可操作界面", "W13", "C23", "test.ui.routes",
       "researchos-client/2每项method有冻结payload/result和事件类型；目录注册、模型目录/探针/选择、文件树/读写/diff、权限处理、会话更新真实对接；错误类型可见，不返回裸object成功，不虚构handler。"),
      ("U05", "正常关闭与隔天接续", "W19", "A14", "test.overnight",
       "关闭窗口/托盘/显式退出/崩溃/休眠分别按配置生效；重开同身份与检查点，人工停止保持停止，无重复副作用；保留真实8小时墙钟和物理Windows中断证据。"),
      ("U06", "既有项目迁移与证据分级", "W18", "A12", "test.backup",
       "保留ResearchOS永久身份、旧规格/回执和用户文件；在备份副本验证旧版到目标版及失败回退；旧PASS逐断言核对，新增CLI/Desktop/协议断言不继承；原有效数据不被静默覆盖。"),
      ("U07", "真实问题的用户价值基线", "W14", "A13", "test.cycle.live",
       "FIRST-USE/CONTINUITY/REUSE三项真实问题有输入、产物、人工介入/重复解释、质量、时间和未知费用观察；从首切片采集且同条件比较，不以报表数量或模型高分宣称收益；无改善保留稳定方案。"),
      ("U08", "普通Windows用户可持续安装使用", "W20", "A15", "release.reproduce",
       "CLI与Desktop发行件均固定版本/hash；干净Windows安装/启动/更新/卸载可复现，必要运行时随包提供；数据保留与卸载范围明确，无需Node或手动后台命令，真实操作回执与当前构建绑定。"),
      ("U09", "整个方向的无价值扩展停止", "W12", "C16", "test.resources",
       "原失败/无进展计数跨会话持久不清零；连续两个交付检查点仅增加文档/fixture/框架时优先修最短用户流程并暂停非必要扩展；新候选数量不能冒充用户能力，完整必需门不降低。")
    ]
    for uid, title, tid, cid, key, expected in caps:
        task, case = tm[tid], cm[cid]
        aid = f"{cid}-{len(case['assertions']) + 1:02d}"
        gid = f"{tid}-{uid}"
        capability = dict(id=uid, title=title, task_id=tid, case_id=cid, check_id=gid,
                          assertion_id=aid, command_key=key, mode=case["mode"], status="NOT_RUN")
        delivery["capabilities"].append(capability)
        task["task_gate_checks"].append(dict(check_id=gid, mode=case["mode"], check=title,
                                             expected=expected, status="NOT_RUN"))
        case["assertions"].append(dict(id=aid, check=title, expected=expected))
        case["expected"].append(expected)
        case["actions"].append("按17/18/19/22运行" + uid + "具体操作与反例，保存原始输出和对应客户端/构建/数据版本。")
        case["input"].setdefault("delivery_replays", {})[uid] = {
            "journey_document": "17_USER_JOURNEYS_AND_VALUE.md",
            "real_issue": delivery["first_real_issues"][min(int(uid[1:]) - 1, 2)],
            "typed_protocol": "researchos-client/2", "manual_admin_commands_for_normal_use": 0,
            "old_PASS_is_new_PASS": False
        }
        case["evidence_required"].append(uid + "当前输入/构建/文件hash、操作回执、失败分支和独立复核；fixture与live分开。")
    # A10 is finalized by W17; its command keys are shared with that final owner.
    for t in tasks["tasks"]:
        t["verification_command_keys"] = list(dict.fromkeys(t["verification_command_keys"]))
    product = load(OUT / "contracts/product.contract.json")
    product["local_protocol"]["version"] = "researchos-client/2"
    product["delivery_contract"] = "delivery.contract.json"
    product["desktop"]["blueprint"] = "19_DESKTOP_IMPLEMENTATION_BLUEPRINT.md"
    product["desktop"]["normal_onboarding_requires_manual_owner_token"] = False
    product["desktop"]["workbench_design_preview"] = "ui/workbench-prototype.html"
    product["construction_host"] = {"tool": "Qoder CLI", "observed_version": "1.1.64",
                                    "requested_model_name": "Qwen3.8-Flash",
                                    "goal_entry": "GOAL_START.txt", "instructions": "20_QODER_QWEN_EXECUTION.md",
                                    "model_catalog_verified": True, "inference_or_goal_verified_by_this_field": False}
    ui = load(OUT / "contracts/ui.contract.json")
    ui["workbench_blueprint"] = "19_DESKTOP_IMPLEMENTATION_BLUEPRINT.md"
    ui["preview_only"] = "ui/workbench-prototype.html"
    ui["primary_screen"] = "S01"
    ui["startup"] = {"native_local_identity": True, "manual_owner_token": False,
                     "bundled_runtime": True, "offline_history_readable": True}
    for screen in ui["screens"]:
        screen["presentation_priority"] = "PRIMARY" if screen["id"] in {"S00", "S01", "S04", "S10"} else "SECONDARY"
    putj("contracts/tasks.json", tasks)
    putj("contracts/acceptance.json", cases)
    putj("contracts/delivery.contract.json", delivery)
    putj("contracts/product.contract.json", product)
    putj("contracts/ui.contract.json", ui)
    old_fixture = load(OUT / "examples/client_protocol_fixtures.json")
    putj("examples/client_protocol_fixtures.json",
         json.loads(json.dumps(old_fixture, ensure_ascii=False).replace("researchos-client/1", "researchos-client/2")))

def main():
    seed_owned_files()
    baseline()
    amend_docs()
    mutate_base_contracts()
    print("v2.4 owned baseline/doc/contract draft generated; NOT a validation or product PASS")

if __name__ == "__main__":
    main()
