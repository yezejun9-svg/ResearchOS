# Host stored final_path 有限诊断

结论：Source 4f4023c956f84d65743f39ce77d6c8899a21ada1 存在已重现的 UTF-16 长度误用于 UTF-8 字节截取缺陷。冻结 actual 元数据里的尾部 20261012 → 20 恰好符合该缺陷（3 个中文字符造成 6 字节差额）。Source53 + fixture 6802628826dcc4b79a16ced20a8e26f7e5494a1b 的相关生产文件完全相同，未修复。

SnapshotWorkspace 不比较 stored FinalPath，也不比较重新计算的 final：它只将 volume/fileID 用于 pin 身份比较，其他 owner/access/status/RealPath/reparse/范围检查仍独立执行。故单独这个 stored-final-path 差异不是当前备份代码的拒绝条件；也不是“同样的坏 final 值相等而通过”。本轮没有执行实际备份、没有接触原始 Root/DB/registry/API/Core/Desktop/model/keys/worker。

## 范围与证据等级

- 只读 Source worktree：D:\作品集\ResearchOS\research-os\.local\worktrees\online-backup-fixture-qualification-20261015，HEAD 已核对为 4f4023c956f84d65743f39ce77d6c8899a21ada1。
- scope SHA256：6fb724a908f1fce71185855de9be5075e29c14d524693a082f5c1c3695eade2d；五个 frozen input 全部核对 SHA256 相符。
- actual 事实仅来自 frozen resource-map.json（SHA256 9609d05ad7afdfabf4cf9c635066c1f7df1fb71b21d580f23419a361fe31ec88）。本轮没有重新读取实际 registry，也没有证明当时写入所用 binary/版本；这些具体历史出处仍 UNKNOWN。
- 5 个有界 source/test groups（01–05），加 00 intake；未超过 8 组。Microsoft 官方文档为辅助外部只读取证。
- Source bug/native fresh fixture 已证实；consumer 为 Source 控制流证据；实际备份资格、same-handle 128-bit identity/ancestor continuity、安全全面验收均未获得。
- formal_increment=0，self_acceptance=false；Root 另行采用。本诊断没有修改 Source/Git/共享 ledger/原始数据。

## 生产、持久化、读取与消费的精确定位

所有下面路径均相对上述只读 worktree：

| 阶段 | 文件与函数/行号 | 证据 |
|---|---|---|
| 原生选择入口 | internal/host/native.go nativeWorkspaceChoose:262–330，特别是 305–313 | nextRef 后 Register，随后 Issue selection；选择由 Host chooser 参与 |
| 生产 identity/final | internal/host/roots_windows.go fileIdentity:17–44，API 35，错误 39–42 | 返回 n 为 UTF-16 单位，转 Go string 后 len/final[:n] 按 UTF-8 字节 |
| 保存 binding | internal/host/roots.go RootRegistry.Register:90–130，特别是 113、122–125 | 将 fileIdentity 返回的 final 原样放进 RootBinding.FinalPath |
| JSON 字段/索引 | internal/host/roots.go RootBinding:24–34，rootIndex:36–39，save:68–76 | final_path 字段无独立编码版本；index Version:1 |
| 实际序列化函数 | internal/host/host.go writePrivate:198–226 | json.MarshalIndent，临时文件 Sync/privateFile 后 Rename；无截断/格式迁移 |
| 加载路径 | internal/host/roots.go openRootRegistry:47–65；internal/host/host.go readPrivate:229–237 | JSON Unmarshal 后直接放入 roots；无 FinalPath 重算或版本迁移 |
| 通用解析 | internal/host/roots.go Resolve:135–172，特别是 151–170 | verifyStillPinned 仅 Stat；fileIdentity 的第三返回值丢弃，只比 volume/fileID，再由完整 RealPath 拼接及检查 reparse/范围 |
| 备份选择/pin 校验 | internal/host/backup_windows.go SnapshotWorkspace:17–63，特别是 29–54 | 根通过完整 RealPath 及权限匹配；第三返回值丢弃，52–54 只比 volume/fileID |
| 备份文件读取 | 同文件 67–139，特别是 77–88、108–135 | WalkDir 使用完整 pinned.RealPath；每项调用 Resolve，os.Root 打开 relative path，读前后身份/大小/mtime 校验 |
| 备份输出 | internal/domain/backup_workspace.go backupWorkspaceFiles:166–226，特别是 190、197–198、211–225 | index.SourcePath 来自 binding.RealPath；blob 路径来自 AuthorizedRef 和相对路径；未传递 FinalPath |
| 恢复重新 pin | internal/host/backup_windows.go PinRestoredWorkspace:175–207 | 新路径由 Register 重新生成 Host root；不继承旧 roots 文件，因此当前 bug 也会作用于新 Unicode restore 路径 |
| 其他身份消费者 | internal/host/workspace_files_windows.go:83–95；internal/host/workspace_write_windows.go:365–393 | 同样丢弃 final，只以 volume/fileID 校验或构造 rootIdentity |

生产目录搜索未发现以 FinalPath 进行路径打开、相等比较或授权判断的代码；tests/security/check/phases.go:341 仅检查其非空。roots_windows.go:15–16 的注释宣称 resolved final 有助于后来检测替换，但上述实际消费者不使用此字段；不能以注释替代实现。

## API 语义与缺陷

Microsoft GetFinalPathNameByHandleW 文档说明，buffer 长度和返回长度以 TCHAR 计；W 版本使用宽字符，当前 Go 调用 buffer 是 []uint16。成功时 n 不含末尾 NUL，buffer 不足时返回所需容量（包含 NUL）。当前 fileIdentity 先 UTF16PtrToString，随后把 n 作为 Go string 的字节上限，错误混用了 UTF-16 code unit 与 UTF-8 byte。不是 rune 数差异。

官方来源：https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfinalpathnamebyhandlew （本轮成功读取；请求及原始返回保存为 03-microsoft-doc-*）。

冻结字段的完整路径含“作品集”三个 BMP 中文字符：UTF-8 每字 3 bytes，UTF-16 每字 1 unit，差额 6。API 返回带 \\?\ 前缀；Source 先按 n 截掉末尾 6 bytes，再移除前缀，准确得到冻结的 ...agent-20。普通 ASCII-only 路径没有这种长度差；非 BMP 字符是 4 UTF-8 bytes 对 2 UTF-16 units，也会累加差额。

另外 API n>=len(buf) 的 buffer-too-small 分支当前未显式处理；最小修复应一并定义容量失败行为。该分支本轮仅由 Source + API 契约识别，没有执行超长实际路径测试。

这不是有证据支持的“历史格式约定”：index version 1 不包含此种转换规则/迁移，生产代码仍实时制造截断。鲜活 fixture 证明现象无需任何报告层截断即可发生；冻结记录与其逐字吻合。因未重读原 registry/历史 binary，本报告不把原记录的精确写入来源认定为已证实，也不声称独立审计了 collector 的所有转换。

## 本轮 native fixture

05-native-unicode-fixture.raw.txt 保存 2 个 Go test 的原始输出与 PASS；PASS 含义是“当前 bug 如预期重现”，不是修复已通过。

通过 Go 1.27.1、GOTOOLCHAIN=local、GOPROXY=off、GOSUMDB=off 运行既有 roots_windows.go 的逐字副本（SHA256 49da785d1531314a9b74ecd5ad5a378b5203dad7d239f8e9f7860433364ad6a8）；test 通过 Go overlay 加入，所有 fresh directories/build/cache/temp 仅位于 own temporary root。没有新 C#/PInvoke/native reader，没有调用原始 root、Host.New、worker、provider 或备份。

| fresh case | 结果 |
|---|---|
| own CJK parent + ascii-tail-20261012 | 末尾只剩 ascii-tail-20，丢 6 bytes |
| 同父目录 + 工作区 | 丢 12 bytes，精确符合编码差额 |
| 同父目录 + 😀 | 丢 8 bytes，精确符合 surrogate-pair 差额 |
| collision-000001 与 collision-000002 | 相同 truncated final 字符串；现有生产函数返回的 native fileID 不同 |
| 冻结 metadata 纯字符串算术 | 精确得到 ...agent-20；没有打开该路径 |

因此截断 final 不能当作唯一 canonical identity；现有 volume/fileID 校验在上述鲜目录中仍区分两个对象。此结果没有证明实际根的 pin 连续性、重解析竞争防御或完整安全性。

## 680 是否已修

03 的 scoped git diff 为空；04 的两个 revision 的 blob ID 完全一致：

| 文件 | 共同 Git blob |
|---|---|
| internal/host/roots_windows.go | 9057ffb989e5f03a50d39ca2c7eef79ada47612d |
| internal/host/roots.go | 49e26a66909ac9c71019b978e16e39d841983387 |
| internal/host/backup_windows.go | 68cbb1d1a33b763031ec26f2c8cb99c7f6560b85 |
| internal/host/host.go | 4c231c79e5cf77c52bb0cecaf2f9a86e00aeaa15 |
| internal/host/native.go | bbe1bea8a82f6c6b55f3e49432d78e7c66fc04de |

680 的 schema22 queue fixture 不构成此缺陷修复。有限 fixture acceptance 也不等于 original actual 资格。

## 最小 Source/test 修复方案（未实施）

必需生产变更只落 internal/host/roots_windows.go:fileIdentity:34–43：先验证 n 对 buffer 的有效范围；以 UTF-16 buffer[:n] 做有界转换，再按现有约定处理前缀；删除以 n 截取 UTF-8 string 的步骤。超出容量可以明确拒绝，或采用有界增长重试；需在该小卡上选定一种行为，不能将不足容量当成功或读取未定边界。不要顺便改变 volume/fileID 格式、注册授权或备份策略。

必要测试 cuts：

1. 新增 internal/host/roots_windows_test.go：调用真实 fileIdentity，ASCII control、CJK ancestor/CJK basename、non-BMP、同前缀不同 suffix；断言完整 final、不损坏 UTF-8、不同目录 native IDs 保持区别。长度边界测试必须覆盖 n=0 和 n>=buffer capacity，选择 helper/unit seam 或有界 native long-path fixture。
2. 在 internal/host 的 root registry 测试新增 Unicode Register → save → reopen 断言，保证完整 FinalPath/RealPath 无损；若采用 roots_windows_test.go 同包测试即可使用既有 registry 入口。复用真实生产函数，避免仅复述修复表达式。
3. 本卡恰好只修改上述两个路径。备份行为用已有 internal/host/backup_integration_windows_test.go 中相关用例回归即可，不为此另改第三个源文件；旧字段与 producer 修复之间的边界由本报告 Source 控制流证据明确。如果后续改变 consumer 才另立旧记录兼容测试。
4. 此次无需修改 backup_windows.go 或 roots.go 的校验语义。若产品另行要求把 final 纳入安全校验，应另立 consumer/legacy-compatibility cut：届时旧记录可能被新比较拒绝，必须先定义可信迁移/拒绝策略，不能顺便接受旧的错误字符串。

最小施工文件集合恰好 2 个：internal/host/roots_windows.go（现有）和 internal/host/roots_windows_test.go（新增）。不需要新增 C 原生实现、重写 backup 架构或泛化路径清理。

## actual legacy 刷新仅方案与未知

修复 fileIdentity 只影响以后计算的返回值；既有 roots.json 在 openRootRegistry 中直接反序列化，不会自动重写已有 FinalPath。当前 SnapshotWorkspace/Resolve 不读该字段做比较，所以旧字段本身不会因 producer 修复而自动阻断当前控制流；这不等于实际 backup 已获准。

当前 Source 没有专用 FinalPath refresh/migration 方法。可见正常能力是 RevokeWorkspace/RootRegistry.Revoke（surface.go:16；roots.go:210–218）以及经 chooser 的 nativeWorkspaceChoose → 新 ref → Register。不能直接对同一个未撤销 ref 再 Register（roots.go:119–120 会拒绝），不能只额外创建相同 RealPath 的 live record，否则 SnapshotWorkspace:36–37 会拒绝 ambiguous root。

实际刷新应在另行授权的维护/重新授予流程中选择：
- 元数据修复路线：需要一个明确的受控 migration 契约，验证当前 principal、完整 RealPath、volume/fileID、reparse/可信祖先，并保留旧值与原因；本轮没有实现或验证这种工具。
- 正常重新授予路线：先确定旧 Host ref 与 domain AuthorizedRef 的 crosswalk、旧授权撤销及 domain workspace 更新/替换的正式入口，再经用户 chooser 重新授权并核验全链。不能推定只调用 Host revoke/rechoose 就更新了 domain binding。
- 仅凭截断后缀不能“补字符串”；也不能把 fileIdentity 取得的任何新对象默认为旧授权对象。实际 same-handle identity/ancestor continuity、授权契约、执行顺序和维护窗口仍 UNKNOWN，Root 需单独决定范围。

本轮未执行上述任一路线。

## 命令偏差与保留

01 首次 rg 扫描范围包含 worktree 中的已提交 source snapshots，输出较多；02 后收紧到生产目录。03 有一条 rg 使用 Windows 不展开的 internal/host/*test.go glob，native exit=2，随后 04 用 -g '*test.go' 修正；失败原文仍保留，没有把它抹成 0。准备 04 时发生一次 JavaScript orchestration SyntaxError（未启动 shell），重发后成功。command-index/ledger 如实记录 1 个 native query failure 与 1 个 orchestration failure；Go fixture native exit=0。不是零失败声明。
