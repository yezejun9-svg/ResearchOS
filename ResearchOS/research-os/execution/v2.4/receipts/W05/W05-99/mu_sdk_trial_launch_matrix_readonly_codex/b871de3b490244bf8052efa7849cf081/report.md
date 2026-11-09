只读结论：SDK v7 的输入和 authority 引用可排成无环 DAG，但当前不能据此声称实际 trial 可启动。本次仅解析原文 AST、抽取契约和文件依赖，没有导入或执行候选脚本，没有运行 SQL/native/product/model/provider，没有写 Root authority、Main、Git 或 canonical checkpoint。

源码固定为 mu_sdk_trial.v7.final.proposed.py，SHA-256 d527eaf03d83208751c046d024747cb42bdc2f806474f8dda7f8ae70c2716a98，84032 bytes。源码 SOURCE_COMMIT 为 e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7；父任务报告当前 HEAD 已到 adc460...，本提取任务未重新执行 Git 验证。当前 Source 更新仍须另行审查。

启动契约

同一个 phase 的 precheck 与实际执行都会先验证完整 Root registration/review/grant/lease、真实 canonical checkpoint、当前 Python PID 的 Job/probe/heartbeat/controller review。precheck 不是脱离 authority 的静态检查。main 一次只接受一个 command；普通两个 Python 进程不能复用同一 PID authority。可行的同 PID 双阶段运行机制须在真实 controller/runner 源码中明确并审查，本次没有实现或证实该机制。

PHASE_BASIS_KEYS 所有字段在 bootstrap 和 execute 都必须出现。basis 只绑定消费输入、脚本本身、child argv/cwd/env，不引用后续 registration/review/grant/checkpoint，避免输入 hash 自循环。权威字段和全部原文函数行号已写 launch-matrix.json；原文 read-tool-io.json 与完整 Source snapshot 可复查。

Bootstrap 需要已初始化且 ProjectProfile 数为零的隔离 DB、已存在 discovery 和缺失的 CLI config；它不创建 Host，不初始化数据库。CLI init 和 goal --draft 产出真实 Project、恰好一个 DRAFT Goal、config 原文；bootstrap.result.json 必须证明零 Task/Run/BudgetLedger/resource effects。所有合法 config 变化均由原始 CLI JSONL 与产品上下文证明，不允许手工改写后只更新 hash。

Execute 需要 post-bootstrap config 原文、当前 route/profile/cancel fixture/bootstrap receipt，以及被冻结的 qualification task/run/epoch/profile/owner_root。候选只等待资格，并不创建或发起资格。资格必须由产品可信路径产生，Run.created_at >= registration.started_at_utc，具有独立 LIVE PASS receipt、当前 trusted observation/Artifact/plan/profile/approval binding，恰好一个 CONFIRMED MODEL effect。资格不能借用 bootstrap DRAFT Goal。普通 CLI turn 再创建新的 Goal，完成 MODEL→TOOL→MODEL，合计三次 MODEL 请求、一条 TOOL read；每次输出上限2730，总请求上限8192而三次实际请求上限8190；金额与实际计费 tokens 保持 UNKNOWN/null。

最小文件矩阵

机器可读 launch-matrix.json 包括27项最小文件/目录状态、逐字段 authority 契约、引用 DAG、4种 command 模式、源函数定位，以及待完成启动序列。所有路径/pin 都要求绝对、canonical、原文 sha256/bytes；消费 discovery/config 还要求隔离 root 内的单硬链接普通文件。heartbeat 是动态活性文件，不作固定 hash；路径在 data_root/trial-control，tick 必须0至5秒内。一次性标志位于 data_root/trial-once/<uuid>.json；父目录存在、文件缺失。实际 phase 成功校验后才消耗 once 并创建 outcome_dir；precheck 不消费 once。

无环封存顺序为：source与静态phase输入→basis→registration→source/scope review；独立lease与registration→canonical checkpoint；真实 suspended PID + controller→Job contract→OS probe→controller lifecycle review；前述review/Job/basis→Root grant→完整 executable input。controller review 先于 grant，不能先给需要事后PID或Job的通用 grant 再补字段。

未解决的实际启动事项

1. Source/current commit 与 cancel receipt 重新绑定，不能用旧 commit Source 或伪装 canonical checkpoint.head。
2. 同一 PID 内 precheck→phase 的真实实现与独立审查；若选择两个进程，必须分别提供真实 PID authority，并确保没有违反一次性授权和整体预算。
3. 资格 ID 冻结与产品 admission 次序。若 admission 会立即向 provider 发请求，就不能在 Root grant/Job/预算之前用它取得 ID；需真实 prepare/reserve 路径，或受审查的最小协议调整。这里没有查证产品是否提供该路径。
4. 实际 controller 必须证明 suspended→assigned→probe/review/grant→resume、kill-on-close、全子树和绝对 deadline。候选只用 IsProcessInJob(current,None) 确认在某个 Job 中，并消费 expected-Job probe；源码没有直接验证 assignedBeforeResume 字段，也不独立查询所有Job限制。
5. Bootstrap 消耗自己的 once，execute不能重用该标志。源码对每个phase验证<=300秒，没有自行累计两阶段wall time；Root须按实际授权范围维持总时限和计数，不能隐式重置。
6. 资格 Host/worker 若在runner CLI子树之外，必须证明也由真实受控生命周期覆盖。

最终 trial.result.json 只允许 OBSERVED_NOT_INDEPENDENTLY_ACCEPTED，formal_acceptance=null。本只读提取不批准运行、不授予任何新权限、不提升 formal acceptance/主线计数，不把推荐启动序列当作已经实现。没有新增工具失败；先前失败计数未重计。

