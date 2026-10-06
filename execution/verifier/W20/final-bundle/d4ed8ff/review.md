# W20 最终文档包独立审查

结论：**PASS_BOUNDED_STATIC_DOCUMENT_PACKAGE_WITH_HISTORICAL_NATIVE_REUSE**。当前文档包唯一一次既有静态检查实际退出码 **0**，**16 项断言 PASS**；本次产品 native 启动执行为 **0**。旧包 a418 的 **28 项已执行检查**只作为历史有限机制证据复用。当前包未被实际启动，本结论不接受 A15、完整 W20、W21 或整个 Goal。

冻结源码：`d4ed8ff90b198b1853eb9af803030b818f03591a`。两个构建记录实际退出码 0 / 0；两份 ZIP 逐字节相同，SHA256 为 `2689666c9738e0073edfd7148efce71830d466267bc79f5b070d113769b4b31a`。独立检查全部 515 项 ZIP entry、514 项 manifest 文件，路径集合、每文件大小及 SHA256 均符合清单。源码树摘要和 build_id 按冻结 builder 规则独立计算相符。

## 执行与证据边界

唯一检查为锁定 Python 执行 `-B -X utf8 tests/release/check.py --archive <d4ed8ff-a.zip>`，没有 `--run-fixture`。标准输出、标准错误和实际 OS 退出码先落盘，再解析结果。输出 SHA256 为 `fa4e01cd1b28f401369147bd6370ae226a261b009397cfefcdde5a3257f4b5f0`；标准错误为空。`check-result.json` 保留所有断言名称，`command.json` 和 `exit.json` 保留命令及时间。

16 项覆盖 ZIP 唯一/排序/路径、完整允许清单、每文件 hash、升级机制与激活未资格声明、既有 release_host 入包、施工专用检查排除、UNBOUND 声明、PowerShell verify、篡改/缺失/额外文件/路径逃逸拒绝，以及未绑定命令真实返回非零。静态检查确实启动 PowerShell verify 子进程并调用临时解包中的 dispatcher；没有启动 control/runtime/release_host 产品进程，也没有旧 native、provider、private helper、数据库激活或已拒绝分支执行。

检查前后 461 项源码/检查输入、锁定工具及 PowerShell、三份新旧 ZIP、manifest、SBOM 与受保护旧审查文件的快照完全相同。现有 check.py 的 hash 同 a418 时点一致。

## 与 a418 的机械差异

相对 `a418d503f29646f62010905f9dc9338630aa0108`、ZIP `dc90caedd5287bcd718c76bc8e0e2189cf3b33c92a547b6d9fe71d3564f8a193`：仅新增 `docs/installation/user-guide.md`；仅修改 `docs/installation/README.md` 与 `release/outcome_report.json`。没有删除文件，其余 **511 项载荷逐字节相同**。四个 EXE、web/dist、start/stop/verify、规格合同、迁移、配置/锁和命令登记/dispatcher 均包含在独立清单中。

Manifest 仅 `source_commit`、`source_tree_sha256`、`build_id`、`files` 发生语义变化，其余字段完全相等。新 manifest 是 start 执行 verify 的前置输入，不能宣称所有执行依赖未变；本次 16 项检查重新验证了这一前置。普通启动的未改机制可引用旧包 28 项历史结果，不能外推成新路径、新环境或新 ZIP 已实际运行。control.exe 仍为 `b667c45bef91508df9c02f16ad91138762bcb0cbf30a481c998e71cc8194c8eb`，没有生成新的 current-control 权威证明。

## 文档与旧记录保留

指南 SHA256 `c3aea987e0bcd0527d82b1b460e16b79edcb93dc91cd825220f6cfbb72d3bcb0` 与已独立审查版本完全一致；其 21 项事实来源在当前源码中逐一 hash 相等。11 页入口、权限、操作、状态及恢复边界沿用该已核验事实。独立重核 51 个相对链接全部存在，其中 45 张历史截图 hash 同原审查一致；指南指向 README 的 hash 因本次合法段落新增而更新。项目入口四格和工作台深色桌面一格仍缺图。

README 仅新增中文指南链接及使用前置说明；Outcome 仅新增 user_guide 对象，其他字段语义不变。截图和完整执行证据在源码仓库中解析，ZIP 不包含这些文件；指南和 README 明确说明这一限制。没有新增截图、浏览器或真实手机验证，没有增加凭据签发、激活或越权操作说明。费用未知、稳定版本未知、C26 失败史、服务/恢复未资格等事实没有被文档改变。

原 a418 审查及其 manifest、W21 原 8 文件及原 manifest、a418 final-supplement 与其 manifest 全部逐项 hash/size 保留。本次仅向 W21 添加 doc-package-supplement.json 与独立 doc-package-supplement-manifest.json。当前许可缺口仍为 2；clean Windows A15 为 NOT_RUN；W20、W21_G01、W21_G02 仍 NOT_ACCEPTED，whole_goal_complete=false。

详细逐项证据见 archive-audit.json、document-audit.json、reuse-binding.json、before.json、after.json、check-result.json；本目录完整性由 manifest.json 固定。
