# ResearchOS 产品 V1：可输入、可看见、可审阅的本地 AI 工作台

状态：**产品V1规划基线；实施状态以`execution/product-v1/state.json`为准，所有产品验收均为NOT_RUN。** 正式方案位于`docs/product-v1/PLAN.md`；DAG、验收、旧规格映射与证据分别位于`execution/product-v1/plan.json`、`execution/product-v1/acceptance.json`、`execution/product-v1/legacy_mapping.json`、`execution/product-v1/evidence.json`。本规划不清除旧工作树、旧数据库、旧22/42验收或失败台账；后续按Root登记的新scope实施，不再请求用户重复批准。

## 产品结果

用户打开自己的项目，在一个干净的桌面端输入有界coding任务，看到真实回复、工具调用、检查和成果。一个Harness串行实现一次，固定候选后交给另一个Harness只读评审；用户看到diff和证据后决定接受或拒绝。接受只对当前hash对应的候选有效。V1不自动进入自我迭代、不自动commit/push、不让模型完成或另一模型认可变成产品接受。

首个开发里程碑只打通单Harness。完整V1还需双Harness和Windows交付两层证据，不能用第一个里程碑宣称全部完成。

## 默认页面

默认使用现有React技术栈和三栏信息结构，不把用户带回11页配置后台：

- 左栏：项目、最近情况、会话、当前任务；项目路径与状态可辨认。
- 中栏：会话画布、Markdown回复、可展开工具过程；底部始终有可输入的CLI风格composer、附件/范围、发送/停止。
- 右栏：有界任务步骤、当前工具/检查、候选成果和diff、评审与用户接受状态。细节按需展开，原始回执可查。

视觉采用干净留白、深绿/暖白与深色主题，克制的黑客感；不堆原始日志，也不把装饰光线当进度。窄屏折叠边栏但输入与停止始终可达。必须验证IME、键盘、焦点、文字可读性和reduced-motion。

## 唯一执行权威与复用边界

Go Host是权限、任务上限、单执行锁、会话身份、持久事件、候选和用户接受的唯一外层权威，接同既有Coordinator/Run/lease/events/receipt。fresh数据root仍用现store，扩字段由Root先版本化，不另造productv1 journal、调度DB或第二调度器。CLI/Desktop都是薄客户端。Codex/Pi adapter只做实际受支持协议的进程/stdio/请求/事件/错误/取消映射；Harness内的模型与工具循环继续由Harness负责，不在Go里重造第二套。

一期固定本机已通过exec help确认的Codex0.166.0 `exec --json`薄driver，再打通单任务；第二阶段适配Pi0.99.2 RPC做只读评审。app-server/RPC只在后续确实需要per-tool permission bridge时单独评估，不是一期前置研究。两者的版本、登录、协议和真实执行分别记录。若Codex实际事件或权限能力不满足，仅阻塞该支路并报告；不静默换实现、不复活旧Mu/Codex资格会话。普通shell终端可作为按需面板，不能成为唯一用户交互或任意命令授权绕道。

本机已安装Pi0.99.2、ResearchOS vendor0.87.1、Lancer SDK声明/锁1.4.0是三套不同版本。Lancer多模型Pi SDK并不等于多个CLI Harness；不能将其事件接口直接套到0.99.2 RPC。

Codex权限按`default_permissions`自定义filesystem profile：`:root deny`、`:minimal read`、`:workspace_roots read`；候选写入只可另由Root授权确切owned路径并实测。不得同时传`--sandbox`覆盖profile。实际Windows allow/deny enforcement未验证前capability不得READY。V1不把事件显示伪装成exec无法强制的逐工具审批。

UI沿既有`apps/web/src/workbench.jsx`、`activity.js`、`components/activity-rail.jsx`实施；Desktop沿`preload/preload.js`、`main/lib/ipc.js`、`main/main.js`窄链，不另建productv1独立页面。

## 一次有限闭环

1. 用户选择项目，Host记录HEAD、dirty、输入、允许路径、检查和上限。
2. 用户确认有界任务。Host只启动一个实施Harness，修改进入owned隔离候选，不覆盖旧工作树。
3. 接受命令ACK、流式消息、工具事件、检查exit分别入账。未知费用/状态如实显示；ACK不是完成。
4. 实施终止后固定baseline/candidate/check hashes。真实检查失败保留，不被模型总结洗白。
5. 另一Harness只读评审该固定候选与证据，输出带Harness版本和输入hash的评审产物；不自动修复或自签。
6. 用户看diff/检查/评审后接受或拒绝。应用前CAS核当前基线与候选；漂移拒绝，拒绝则保留候选。随后停止，下一轮由用户启动。

## 停止、失败与恢复

停止先关闭Host新增dispatch；Pi的完全停止需clear_queue后abort，并核对终态/实际队列。prompt的started/queued/handled只是处理结果，handled可能根本没有run，不能一律等agent_settled。其他Harness按自己固定版本合同核验。子进程未证停止只能显示STOPPING/UNKNOWN。

断线或重启后先对账，UNKNOWN不自动重发。用户STOP持续有效。失败来源、输入、候选和次数持久保留，不因新名字/新会话/新Goal清零。V1默认不自动重新发起模型任务或评审；旧规则的同源最多2次、连续3轮无进展是不得放宽的上限，不是自动重发许可。只有明确NOT_SENT或幂等本地操作才可在已登记范围内定向修复；接受后/未知结果必须先对账并由用户决定下一步。资源缺口只阻塞相关adapter/验收层。所有旧UNKNOWN和已消费模型scope保持，不重放。

## Lancer可复用范围

优先局部引入MIT LightUI0.1.0：`light-layer.ts`、`geometry.ts`、`svg.ts`、`running-border.css`，保留LICENSE/NOTICE。它无运行时依赖，不需Lancer账号、Electron或模型SDK。参考`live-emissions.ts`的历史基线抑制、会话切换清理，以及timeline viewport和工具折叠布局。

借用`SessionDriverEvent`的会话/工具事件形状作为映射参考，另由Host补稳定事件ID、任务/运行/输入hash及真实接受依据。不得直接把Lancer的window.piApp、账号、~/.pi/agent、会话owner或整个DesktopAppStore移成新主控。任务图中的commit是显示事件，不必是Git提交；branch-return的worker-reported只是报告，不是独立接受。LightUI发光只由真实离散事件驱动，历史加载不发光、缺anchor不接邻居，不显示模型私有思维链。

## 验收与旧规格

`execution/product-v1/acceptance.json`固定13条用户旅程：J01–J09单Harness、J10–J11双Harness、J12 Windows包交付、J13默认React工作台真实可用性与图谱事实（IME、窄屏、reduced-motion、历史不发光及节点回执关联）。任务导出/新目录恢复属于POST_V1_OPTIONAL，不是V1发布门；重启/断线恢复仍是J07必需。每条目前NOT_RUN，REAL证据需绑定实际source/build/adapter版本、task/run/session、输入/基线/候选/检查/评审hash。静态检查、单元、fixture Electron、真实Harness、真实Windows UI、安装分别报告；fixture/build成功不能替代REAL。

`execution/product-v1/legacy_mapping.json`完整读取并逐项映射外部v2.4的22父任务及42正式用例为保留、改写成V1用户结果或后置。映射不是修改旧合同，也不是给旧门签PASS。旧PASS不自动继承；旧失败/重试/UNKNOWN不删不清，旧全量ResearchOS目标仍未完成。V1只是用户新授权的首版范围。

## 实施顺序与续跑

`execution/product-v1/plan.json`必需DAG只有10个小切片：S01合同/现store新root→S02 Codex exec --json→S03既有Coordinator单任务接点→S04既有CLI/React三栏→S05候选diff→S06停止/恢复/LightUI→S07 Pi RPC→S08另一Harness评审→S09用户接受→S10 Windows包与真实UI。S11记录导出/新目录恢复保存在POST_V1_OPTIONAL，不进入首版必需DAG。路径为建议，不是写入lease；Root登记实际worktree、source pins和共享文件owner后才施工。

每片实施、窄测、独立复核、保存检查点再续跑。每次只证明本层实际结果。新V1 root默认不碰旧DB；schema扩展由Root在单Host/store中定案，不创建第二调度器、私自编号migration或采用prepared addon。当前旧施工保持CP602暂停；这份规划不恢复它。

## 首版明确后置

研究源采集/通用检索/正式实验/Jev留出评测、资料到技能晋升、系统自动自我迭代/灰度、手机远程监督、隔夜无人执行、旧DB迁移及Native prepared addon生产采用、任务导出/新目录恢复、并行实施者集群。它们保留历史映射和证据，不能靠缩小首版宣称已接受。

## 当前证据界限

本规划作者只读公共manifest、源码、规格和Root已完成的脱敏探测报告。Root已实际观测Codex0.166.0版本、exec help及logged_in/chatgpt凭据状态，均exit0、0prompt/0模型请求、未保存原始认证输出；没有进行登录动作。这不证明模型、额度、取消/恢复或真实任务资格。Pi运行完全未测。未构建安装、未验证真实UI。Lancer文档明确macOS为主验目标，Windows本轮只有配置/打包路径而无native接受；不能照搬支持结论。详见`execution/product-v1/evidence.json`的逐文件hash与版本/未验证矩阵。
