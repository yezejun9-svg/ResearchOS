# 安装设计独立审查：P1 可收敛，原多阶段提案尚不可整体开工

结论：`P1_CONDITIONALLY_DESIGN_READY_NOT_AUTHORIZED_NOT_IMPLEMENTED`。把 P1 收紧为“已冻结 payload → 固定信任输入 → 新 owned 空目录的最终路径定稿”后可实现，现有产品 ID 公式和消费者可保持不变。原提案涉及的修改构建器/条件修改消费者、NSIS、升级/回退/卸载不属于这个 P1；没有任何阶段因此成为已交付。最终仍以 exact14 主任务冻结及后续 Root 精确施工范围为前置。

本次只读核查 INSTALLER-DESIGN.md、EXACT-PATH-PROPOSAL.json、盘点报告及候选源码；INPUTS.json 记录实读 hash/bytes。未改源码，未运行构建、finalizer、Core、Electron、NSIS、安装或数据操作。后续建议已按 Root 明确要求固定，不产生施工授权。

## 影响和必须收敛的点

| ID | 影响与源码/设计依据 | 收敛决定 |
|---|---|---|
| I01 / P1 | 若 payload manifest 含 finalizer，而 finalizer 又固化 manifest hash，形成无法按普通构建顺序求解的字节自引用；manifest 若纳入自身也相同。设计只说“同时嵌入”，未定义两者在清单中的归属。 | product payload 不含 manifest 自身、finalizer、NSIS installer/uninstaller、回执和日志。控制材料全部放产品根外。先冻结纯 payload manifest 的原始字节及 SHA-256，再编译 finalizer 固化该 hash；外部 sidecar 必须逐字节匹配。安装介质/外部发布回执随后绑定 finalizer 和 sidecar，依赖图不回指。 |
| I02 / P1→P2 | 现 ID 把完整 inventory_digest 纳入计算（Python install_id、JS installationIdentity、Go productIdentity）。即使双介质业务 payload 一致，只要各自生成的 uninstaller 字节不同且入库存，ID 就不同，第二介质不再是同身份。 | 两媒体不得把不同 uninstall 字节计入产品库存；优先把共同维护/卸载工具放产品根外，单独记录 hash、安装记录与所有权。P1 根内完全没有 uninstaller。只验证 payload 相同不足以证明双媒体 ID 相同，P2 必须对同最终根实际定稿结果比对。 |
| I03 / P1 | 现 JS loadProductLayout 与 Go loadProductLayout 只遍历 marker.files 核对列出的文件，没有重新枚举整树排除未列出项；它们不能担任“无额外项”检查器。 | finalizer 自行完整枚举目标树。允许文件集合仅为 frozen payload + final verifier manifest + 最后生成的 marker；目录只能是这些文件的父目录闭包。拒绝未知文件/目录、大小写别名和所有 reparse。消费者交叉校验是补充，不能替代 finalizer 的负向检查。 |
| I04 / P1 | 路径 ID 使用 install_root 原始字符串字节，而消费者用大小写不敏感路径比较；“规范绝对路径”与“原样保留用户输入”不能含糊混用。Windows 路径还存在相对段、设备路径、ADS、尾点/空格和不同名字指向同一物理文件。 | P1 只接受明确 fresh owned 根，建立一套最终真实路径的规范表示并冻结为 marker/verifier 的共同输入；不从 cwd 或用户数据推断。拒绝相对/UNC/设备前缀/ADS/保留设备名/尾点空格/重定向路径，检查每级 ancestor 与全树 reparse、case alias；使用文件身份防止别名/硬链接被当独立 payload。先验证再生成，关键打开/提交期间防止检查后替换。当前 payload 相对文件名均可限于 ASCII，Unicode/空格测试放最终根，从而不误称 JS UTF-16 与 Go/Python 对任意 Unicode 相对名排序已经一致。 |
| I05 / P3 | 非空 data 的 product-binding.json 固定旧 ID；新版本或根变化必产生新 ID。claimProductData / prepareProductData 明确拒绝异 ID。仅换程序不能升级，卸载后旧数据也不能默认为 fresh。 | P1 不查看/修改用户 data/config/profile/binding，不接受已有非空程序根。旧绑定、数据迁移、重装恢复只能在 P3 的 stopped/snapshot/transaction 流程处理；未知进程、缺失/不符见证及任何不确定性均拒绝，不改 binding、不清 discovery、不破锁。 |
| I06 / P3 | createProductSafeExit 是 Electron 进程内闭包，依赖私有 management 对象；main 仅从窗口关闭/托盘/before-quit调用。设计尚未给出 installer 可认证调用它的入口。 | 现 closure 不得描述为已可复用的 installer API。P3 需另定受控请求入口和身份核验，或要求用户通过产品 UI 安全退出后，安装事务只验证确切进程已经退出；任何自动调用实现需单独范围和审查。不得通过强杀补齐。 |
| I07 / P3 | 程序根与数据根交换不构成一个原子事务；崩溃可能发生在旧根移走、新根尚未就位、binding改变或首次检查途中。旧根改名后其中绝对 verifier 路径与 ID 本身也不适合直接启动。 | P3 必须有 create-new 事务日志、阶段和恢复表；旧程序只在回到原规范根并重新验证旧身份后启动。数据快照必须包括旧 DB/artifact/config/必要profile并绑定旧ID，确认新进程停止后才回退；不确定时保留材料并报告，不递归删除、不自动覆盖新写入。此项不扩入 P1。 |
| I08 / P1 | 当前消费者固定 mode=OWNED_PRODUCT_LAYOUT_NOT_INSTALLER、version=2.4.0、schema=24，且现 builder 把输出限制在其 worktree .local。直接要求其产出真实安装根，或把 mode 叫 INSTALLED，会扩大 exact14 并破坏现消费者。 | P1 用全新的 producer 消费经批准、只读的 frozen layout/receipt，在新的 fixture 根定稿；保留现 marker schema/mode/version，明确这是非安装夹具。不修改原 builder/消费者/validator/锁。P2 真正发行 mode/品牌/共享工具锁问题另立契约与范围。 |

## 可供下一轮登记的 exact source 建议

仅新增下列五个文件，独立 worktree；这只是建议路径，不是写入许可：

- `apps/desktop/installer/build.py`：读取已批准 frozen source/build receipts 和 layout，验证其实际库存/闭包；复制到新的 path-independent payload，排除且只排除原两个位置绑定生成文件；生成 sidecar，随后构建固定 sidecar hash 的 Go finalizer。不得删改源候选。
- `apps/desktop/installer/payload.schema.json`：冻结相对路径、size/hash、五 executable 引用、source commit/digest、版本/protocol/schema 与依赖摘要；不含最终 root/ID，不列自身、finalizer 或维护工具。
- `apps/desktop/installer/finalize/main.go`：仅 Windows owned fixture 的新空目标；先核验固化 hash 的 sidecar，再自主验证全 payload、目标路径和全集，写最终 verifier manifest，按现算法生成 inventory 与 ID，原子写 marker，最后只读复核。无 host/data/registry/PATH/shortcut/NSIS 功能。
- `apps/desktop/installer/finalize/main_windows_test.go`：文件系统/身份算法与拒绝分支的定向测试；不 import/启动产品 host。
- `tests/ui/desktop/product-installer-layout.test.py`：以真实 frozen payload 和编译 finalizer 测试中文空格/ASCII两个新 owned 根、字节篡改/缺项/额外项/路径与别名，独立 Python 重算和现 JS/Go 消费者交叉验证。

`modify=[]`、`conditional_modify=[]`。原提案将 apps/desktop/build-product-layout.py 列为修改并允许 conditional consumers，均不纳入这个收敛 P1。若实现证明新增文件不足，先以具体接口缺口提出新范围，不能自行转为修改已冻结 exact14。

信任顺序：冻结产品 source/build和工具 → 只读核对布局 → manifest M → finalizer F 内嵌 SHA256(M) → 控制 envelope 绑定 M/F。M 不含 F，F 不在 payload，envelope 不纳入 M；无循环。P1 的信任根是外部已批准输入回执和固定 digest，不宣称数字签名或发布者资格。构建 finalizer 自身的 Go compiled closure/tool hash 同样入证据，但留在根外。

## P1 完成门（本轮均 NOT_RUN）

1. 原 frozen layout/receipts 前后 hash 不变；源 commit、完整 inventory、Go/Mu/client-wire闭包均可追溯。移除原 marker/verifier 只发生在新复制物，payload sidecar字节冻结后再编 finalizer；全部控制材料在根外。
2. 目标必须是登记 owned 新空目录；目标含任何既有文件或无法确定所有权就拒绝，不删除、不覆盖、不采用原安装。输入payload是分离只读根。数据根/用户配置路径不进入API。
3. 自主拒绝 manifest hash变动、size/hash变动、漏项、额外常规文件/空目录、case duplicate、路径穿越、ADS/设备名/尾点空格、文件与目录reparse、ancestor reparse、文件identity alias、提交前替换；失败不能留下可被识别为成功的marker，所有诊断保留。
4. 以同一个明确规范最终根字符串，在 finalizer/独立Python/现JS/现Go得相同 inventory_digest 与 installation_id。Go可用冻结产品CLI的 `version` 入口做只读 loader检查，JS用 bundled Node 调纯 layout helper；不启动Core/Electron，隔离 LOCALAPPDATA。
5. verifier manifest先生成，executable绝对指向该最终根内的 verifier，hash准确，arguments=[]；marker最后提交且自身不入inventory。未更改的已定稿树可只读验证；未经显式新范围不允许重新finalize覆盖它。
6. 复制定稿树到第二根、保留旧marker/verifier必须拒绝；从同一payload在另一个新根重新finalize得到该根正确的新ID。该路径差异是现公式要求，不能为了“可移动”删除root绑定。
7. 所有构建/调用保留实际argv、input/source/tool/compiled closure、stdout/stderr/exit、前后库存；声明 `P1_PAYLOAD_FINALIZER_FIXTURE_ONLY`。不能称两个安装介质完成、升级/卸载完成、真实产品已验证或W20/A15/U08接受。

P2以后仍保留：两介质真实一致payload与单一维护登记、根外维护工具的来源与删除边界、品牌和工具锁、安装/卸载、受控旧ID迁移、未知进程拒绝、崩溃恢复、干净Windows普通用户和正式独立验收。设计认可不等于这些能力已交付。