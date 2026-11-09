# 独立包审查：LIMITED_PACKAGE_ACCEPTED

接受 `C:/Users/yqyyds/.codex/researchos-resource-cache/normal-verifier-replacement-4f4023-20261015` 的限定包组合、固定来源及离线加载行为。未发现包范围阻断问题。本报告不接受实际产品注册替换、Desktop/Core 正常启动、原 DataRoot、真实 provider/模型 qualification、父任务或正式用例。formal increment=0，formal 0/42，22 个父任务保持 open。

审查者 `codex:/root/verifier_revision_review`，gpt-6-astra/high。Source 与包均只读，仅写本独立 evidence 目录和隔离测试临时目录；未访问产品 data、registry、GUI、凭据、网络模型，未启动实际 Desktop 或 Core 服务。

## 固定范围与组合

- scope SHA256 `491def288f03df983b227f1b647f74f77a98362187c9dc99f444d6fdc34dd4ad`。
- Main 与候选 worktree HEAD 均 `4f4023c956f84d65743f39ce77d6c8899a21ada1`，tree `3db13a15cc52b2b0bd75cae3452c66509a9f55c9`；候选前后 clean。没有在 Main 或 Source 写入。
- 新包实际 58 文件，路径集合、每项 SHA256/bytes 和记录的 CRLF/LF/NUL 计数均与 inventory 一致；与旧 `normal-coding-profile-c8b7adab-20261014` 同路径比较，精确仅 3 文件改变，其余 55 文件逐字节保持。
- 3 个变更：`researchos-control.exe` SHA256 `c4a3b498fc15120828427b237b8176710acfd7a9333cd24e9911fded9cd63e24`；`runtime-verifier.exe` SHA256 `f255f4d49c5b217462bb38a8ec2292e9d62889d8506488569ff3638237708a43`；`runtime-verifier-installation.json` SHA256 `74ca846daf8f6ad82692b43dcd3b664fe2970247072546495d05519b01358609`。
- manifest 的 executable 是新包内 verifier 的规范绝对路径，executable_hash 对应其实际字节，source_commit 是 4f；除 executable/executable_hash/source_commit 外，其余字段与旧 manifest 相同。包内 Desktop 默认 core、manifest、runtime 解析路径仍与该布局相符。

作者 FINAL-manifest SHA256 `97e828ce312b7ddcf76c2cef32b5c4848c860e85208bdc99bc18e1c101865396` 及 SUPPLEMENT 引用均核验。独立校验全部 2231 项冻结作者 evidence 文件；2294 个 compiler/module 输入的 before/after/current SHA256 全部相同。control 还与本 reviewer 前一轮独立 clean 构建的字节 hash 相同。

## 独立新鲜证据

`02-native-package-probes` 通过 Go overlay 调用当前冻结 Source，而未改 Source；native exit 0，3 个 top-level 测试、含子例 7 PASS，0 FAIL/0 SKIP。

1. 直接对包内真实 verifier exe 和 manifest 调用 Windows GetNamedSecurityInfo，确认 owner=current SID、DACL protected、恰好一个 allow ACE、ACE SID=current SID、flags=0、mask=0x001f01ff。随后分别通过冻结 `replacementRead`，验证同一实际文件的路径身份、单硬链接、无 reparse、严格 ACL 和精确 SHA256；详细 SID/owner/ACE 信息保存在原始日志。
2. 实际调用 `LoadRuntimeVerifierInstallation`，成功解析并验证新 manifest/exe；实际调用 `LoadRuntimeSetupAssets`，成功消费包内保留的 Node、Mu bundle 和 build metadata。确认 Mu commit `8dfebe36508ac0c2508735bb866756dab9283e74`、5083 vendored files，bundle SHA256 `2a8e70132a914affc6122c1f1db29cfa315b655c93d4200145852ebbc853d441`，返回路径均在当前包内。这是本地离线 loader 兼容性证明，不是模型执行证明。
3. 从两个包内 PE 二进制直接读取 Go buildinfo，核对真实 main package、go1.27.1、windows/amd64、`vcs.revision=4f4023c956f84d65743f39ce77d6c8899a21ada1` 和 `vcs.modified=false`。

另在 reviewer 空临时目录中使用只有 SystemRoot/WINDIR/TEMP/TMP 的环境运行两个有界负例：实际 packaged control 仅传 `--runtime-verifier-replacement`，返回 native exit 2、REPLACEMENT_ARGUMENTS；实际 verifier 以非 pipe stdio 启动，返回 native exit 2。二者均为预期拒绝，没有进入正常产品服务。执行后该隔离临时目录为空。

作者 214/214、0 fail/skip 的 package wire 测试在本轮复用，已经验证原始 stdout、实际调用记录、test source 和对应全部冻结 case 证据哈希。没有把它表述为本轮重新执行。包内 55 个未变旧资产与已接受 baseline 完全一致，本轮变化的原生 executable、manifest、ACL、loader 另行获得上述独立新鲜证据。

## 保留历史与验收边界

所有独立命令的实际 argv、cwd、完整传入 allowlist environment、数值 native exit、原始 stdout/stderr 及 hash 均保存在本目录；两个 exit 2 是预期负例，不计失败。独立测试无失败。最初只读查找的日期路径、rg wildcard、sparse Desktop 路径和 verifier 文件名误猜保留在 reviewer-diagnostics.json。

作者旧失败 ledger 保持原字节，包括 ACL PowerShell/临时 checker 的先前失败。作者已披露一次临时 checker 编译失败没有单独保留 raw tool output；本轮不补造该历史输出，也不宣称该缺口已恢复。实际包 ACL 现在有本轮独立原生读取与冻结 replacementRead 的直接证据，因此这一历史记录缺口未构成本次包接受阻断。

本轮没有尝试删除此前被自动审批拒绝的 `control-clean.exe` 或作者 pyc；没有改包 ACL。前后 58+58 包文件和候选现存 tracked 源码/构建输入一致，冻结作者证据引用无漂移。本次新建临时测试目录为空，无遗留临时文件。

本限定接受只绑定上述 Source、scope 和全包 inventory。Root 后续实际产品 preflight/commit、正常重开和新 qualification 仍须单独留证，不能由此次 package 接受推导通过。
