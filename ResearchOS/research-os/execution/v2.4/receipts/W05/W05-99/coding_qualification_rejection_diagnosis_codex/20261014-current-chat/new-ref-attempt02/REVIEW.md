# 第二次新配置确认：确定的 verifier 注册阻塞

结论：**DEFINITE_INSTALLED_VERIFIER_REGISTRATION_MISMATCH；停止重复准备/确认。** 前次“正常重开后新请求可恢复”仅解决 Main 易失状态，遗漏持久 verifier 注册门；本追加报告据新证据收紧该结论，原 35-member 报告逐字节保留。

## 确定事实

`bb0cb22142a08e1cc63a722739c1f069` 在 19:39:58.333Z 确认，19:40:47.475113Z 到期，剩 49.142113 秒。19:40:23.517007Z observer 仍在期限内，记录没有消费、没有 Run。当前 Task/Run 分支及全库持久未决计数仍为零；不能再用临近到期解释本次快速拒绝。

生产 Core a7ec7ebf 的 `internal/host/runtime_qualification_windows.go:79–92` 构造完整 registration，并与 data/host/runtime-verifier-installation.json 做 domain.Hash 比较。以下三项不同：

| 字段 | 持久注册 | 当前包 |
|---|---|---|
| executable 包目录 | normal-attach-combined-c465d135-20261014 | normal-coding-profile-c8b7adab-20261014 |
| executable_hash | 42c7802cc5d0c3dce21e997c3e82798d14f0b0b137dbf7eb021dace48a18e5ed | 921947553cc0f0df0d6a5061b5441a7f115ace5bdcbb65158ba7f6f884fba183 |
| source_commit | b955c8665281193d5cbf90a146f936c9212c7940 | a7ec7ebf2d53848ea163b6115667b3e3761a6bd2 |

旧 record hash 为 af1f1dbf15074cb94fbea524d52d93c00c0cdaf8305a642998666d77b0ccfc33，新候选为 58bc1cb105f958946a123f57a935c6c371afb5072070a482696113ad724a7e30。旧安装摘要重算与保存值完全相同；当前新 installation 摘要为 3e6a4bcf21551cbf3ada1d9a5307a00a0a660ebcb8fc02457120a991a4ae8c91。Owner、Host、service root 其余身份相同。

因此只要执行到 ensureRuntimeVerifier，此状态必定返回 `registered verifier installation changed; explicit administrator replacement required`。该门在 verifier 启动之后、RecordLocalRuntimeAdministration/ExecuteLocalQualification/Run claim 之前，符合零消费结果。但未读取或捕获私有响应，仍不能把该确定门推断写成已捕获本次实际 ERROR，也不能断言没有 verifier 启动。

新旧 sealed Profile 内容哈希正确，qualification model_config_hash 均匹配。旧 ref 普通限额 1 次模型、无工具；新 ref 普通限额 8 次模型、read/write/edit/run_check，独立 qualification 仍限 1 次。新 authorization session/ref、tool policy 哈希在只读数据中匹配。PREPARE 本身会调用 localQualification/profile/workspace 门，但这些事实不替代完整当前 admission/工具实测。不是根据新工具存在就判定它们被拒绝。

## 现有通路与较小备选

固定 a7ec7ebf 的生产源码检索、CLI flags、private operation 枚举与注册文件所有读写引用中，没有正式 replacement 入口。`--runtime-verifier-manifest` 只加载安装描述；ensureRuntimeVerifier 拒绝更改已保存 record。旧记录不能删除、直接编辑或由普通启动自动覆盖。

Desktop 存在 `RESEARCHOS_DESKTOP_VERIFIER_MANIFEST` 配置入口，理论上能继续选用原已注册 manifest。这属于保留原安装，绝不是 old→new replacement。原 manifest/exe 仍存在，字节/声明与持久 record 完全匹配；历史独立包审查与原 ref 的单模型资格报告已核对哈希。当前 manifest ACL 是 current SID owner、protected、单显式 FullControl；旧 exe 则为继承 ACL（非 protected），原始完整权限已留档，不能宣称二者都是单 ACE 保护。

这个备选**尚未接受**。仅 apps/runtime-verifier、internal/verifier 无源码差异不够：旧 verifier 引入 internal/domain，后者的编译依赖可能涉及已改变的 bridge 等文件。完整旧 binary 编译输入/生成文件/归档与协议/合同哈希、新 Core→旧 verifier 的实际合同、新 coding Profile 的一模型零工具 qualification 及普通工具权限边界尚未验证。旧 ref 的 PASS 不能转授新 ref。Root 必须先登记固定组合 scope、确认原 manifest/exe 路径和 ACL 接受标准，独立核完整构建来源并运行隔离合同/负例验证，才能另行决定正常启动；不得临时改环境绕过当前包 scope。若这些条件无法充分证明，正式 replacement Source 入口优先。

## 正式 replacement 的最小建议范围（未实现）

建议新增独立本地管理命令，不扩展普通 CONFIRM 自动替换：`apps/control/main.go` 增加单一管理 action 及互斥检查；新 `apps/control/runtime_verifier_replacement_windows.go` 负责参数/输出，必要时配 non-Windows stub；新 `internal/host/runtime_verifier_replacement_windows.go` 实现显式 preflight/commit 与持久审计。对应控制入口与 Host 替换测试分开。原 ensureRuntimeVerifier 的拒绝逻辑保持有效；无须修改 Profile/Run/qualification 或模型工具策略。最终确切文件集由 Root 登记后交作者，当前未派作者。

流程必须可审查：

1. 正常退出原 Desktop/Core，取得同一 data-root 的唯一 lease；复核没有消费后未结算 Run/effect/dispatch、没有正在运行的 verifier。保留现有 Host/Owner、service root 和 project verifier lineage，不清资格历史。
2. preflight 显式绑定预期旧完整 record hash 和新安装 manifest/hash；校验当前 OS-bound Owner/Host、非重解析路径、候选 binary、协议/来源、权限、独立包接受。输出精确旧→新差异和不会触碰的业务状态，不产生新资格请求/模型调用。
3. commit 重新读旧 hash 做 compare-and-swap；先持久保存旧原始记录及新描述和唯一操作 ID，以 append-only journal 标记阶段，再原子替换受保护注册文件并读回；任何不明或失败状态须可恢复且拒绝正常使用。不能只写新文件而丢失旧记录，也不能把新的 installer 事实当作资格通过。
4. 单独固定并审查新 Core/新 verifier 的实际组合，然后正常启动、保留原配置，只准备全新请求。两次失败请求及原 coding c671505 绝不重发。

回退边界：提交前失败保持原 record；提交后若要返回旧安装，执行新的显式反向替换，绑定当前新 hash、旧 binary/manifest 和新操作 ID，保留两次历史。崩溃按 journal 与实际文件一致性恢复，不能重置计数或通过删除注册“重新初始化”。原数据有未决消费/执行时，先走原状态协调，不以替换处理。上述为设计要求，并非已存在命令。

本轮只读 SQL/source/file/ACL，无私钥、token 或 raw private frame 读取，无 GUI/API/产品进程/模型/替换/DB 写入。原 35 个文件无漂移；新证据都在此子目录，formal 增量 0。
