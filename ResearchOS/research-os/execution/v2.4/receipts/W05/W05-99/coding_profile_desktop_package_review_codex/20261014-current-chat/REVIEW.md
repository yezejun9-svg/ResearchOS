# Desktop Profile 修复包独立审查

结论：**APPROVE_FOR_ROOT_NORMAL_REOPEN**。冻结的包可由 Root 按既定范围正常重开；本审查未发现阻塞项。

审查对象是 `normal-coding-profile-c8b7adab-20261014`，固定 source `c8b7adab9f0c15eb33f235f8d0d9eb205794e376` / tree `cd951533206a6a4545a6e55fec374e62289d2dd4`。作者 FINAL-manifest 的 SHA256 为 `0bedb06fbb120c69c2224f0102c2be0c0aeed158d0f62322d7a9406a83351466`，与委派输入一致。

独立重算 6,444 个构建输入，摘要为 `819e8a98f8b678928a6354663747ea2d0b7adab21bc220fe6720edf7dc20c8ce`。58 个包成员完整；14 个 Main/preload 文件与固定源码逐字节相同，3 个 React 资产与新构建输出相同。descriptor、编译 argv、binary Go buildinfo 中的输入绑定一致，validator 的 VCS 为 c8b7adab / modified=false。11,362 个独立输入路径、16,198 次引用校验通过，测试后再读全部输入，无漂移。

正式构建证据有 32 份 raw、1,844 份 WORK 与 680 份 archive，已逐一校验。作者 71 个 Go PASS 标记及退出 0 的回执被保留，本轮未重复此源码套件。作者 3 次失败（2 次 ACL 设置、1 次读取路径）仍完整保留。

独立新跑实际包的 **214/214** 个非 GUI 用例，native exit 0，fail/skip/cancel 均 0。固定源码中的 Main 模块与包字节一致；validator 从包绝对路径运行，其生产 spawn cwd 为包的 apps/desktop。原始回执记录 456 个实际包 validator child，均 exit 0 且所有句柄关闭；另有隔离副本运行负例。原始 stdout 包含 474 份携带新输入绑定的 child 输出。

安装 manifest 指向新包的 verifier 绝对路径，哈希正确。独立 Get-Acl 读取确认当前 SID owner、受保护 DACL、单条显式 FullControl ACE。Core/control 与 runtime-verifier 的 binary buildinfo 仍为 `a7ec7ebf`，Mu bundle 仍为 `8dfebe36`；迁移严格为 1–24。此包没有纳入 Native25/storage25/bridgecompat/Core17。

授权边界：本次只接受包的组成、来源、绑定和夹具测试。未启动正常 GUI，未访问真实产品 API/数据库/provider，未进行 CONFIRM，formal 增量 0。Root 后续应在原授权 data location 正常重开，验证已有保存状态 `c671505` / 新 Profile `mc3f932` 保留，不重复 coding CONFIRM。W05/Main24 及正式用例仍按原验收流程处理。

本轮 20 个负例临时目录已在检查绝对路径与唯一 alias 目标后清理；正式 raw 留存。测试与审查证据详见 FINAL-report.json、audit.json、fresh-package-cases.process.json、runtime-evidence-summary.json、fresh-acl.json、inputs.after.json、cleanup-result.json。审查读取截止 2026-10-13T19:23:38.229128+00:00。
