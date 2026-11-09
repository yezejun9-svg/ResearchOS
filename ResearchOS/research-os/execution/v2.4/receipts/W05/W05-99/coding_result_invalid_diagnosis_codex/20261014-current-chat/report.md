# 本次 CODING_RESULT_INVALID 独立只读诊断

结论：**配置已经提交；确定的结果校验错误是 profile_ref 类型不一致。** Core 返回 Artifact VersionRef 对象，已安装 Desktop 却要求字符串。当前 UNRESOLVED 不能解释为配置未写入，也不能再次确认。

## 本次精确提交

只读 SQLite 使用 `file URI mode=ro`、`PRAGMA query_only=ON`、BEGIN/ROLLBACK。选择同时约束 project、session、owner、旧 model ref、原生确认精确 expiry=`2026-10-13T18:35:59.7266606Z` 与 issued 窗口 `[18:34,18:36)`，只有一个 confirmation；后续 installation/authorization/config/runtime 全按该 request/ref 连接，未使用 latest 或按时间取第一条。

- coding request：`c671505efdffbb538c998cb7ca0265e1`
- request hash：`sha256:d74bce143f174592c9d36041048e8850c8e8ffa5a11d3162da037698cd98933b`
- 新 model ref：`mc-3f9329b391eaca14d82e7c4d3b9b6f34`
- runtime：`db26746ff0420ca156d315f0de00fb53`，当前 `REGISTERED`，qualification_ids 为空，未获资格。
- configuration command：`d62febd91bc5aff9e724a8a279637b5d`；配置 revision=2，创建于 `2026-10-13T18:35:22.9386059Z`。
- 当前 session 已绑定新 model ref，session revision=4、writer_epoch=2。
- profile_ref：`{entity_type:"Artifact", id:"d234b69ff0a8dcf907678d0e2c6e5373", revision:1, content_hash:"sha256:32e7bc0fb3730254e21bd2cc7991d751f9065f5dda61b6072eced69bcb45d9e0"}`。

细节、元数据连接和结果条件见 `exact-coding-commit-observation.json`。安装结果、配置行、授权行和 session 新引用同时存在；Core 在同一事务中保存 installation 后 commit，以上是 durable committed 状态证据。没有输出 canonical_config_json、credentials、prompt、模型正文或整个数据库。

## 根因证据

实际包 `normal-coding-any-a7ec7ebf-20261014` 的 `apps/desktop/main/lib/desktop-management.js:719-730`，要求 `typeof value.profile_ref === 'string'`。Core `client_runtime_setup_windows.go:17-20` 把 ProfileRef 定义为 Object；`client_runtime_coding_windows.go:360` 原样返回 `prepared.ProfileRef`。这与本次实际 installation 的 VersionRef 对象吻合。三个来源绑定到 Main `a7ec7ebf2d53848ea163b6115667b3e3761a6bd2` 的确切字节，Desktop 源码与安装包字节一致。

只读查询比较本次 installation 与原确认的 request/hash/project/session/oldref、scope、frozen_checks、model 0 与 8/1/0 限制、revision 等条件，只有 profile_ref_string 为 false。新 model ID 的实际校验进一步由生产函数探针通过。这里没有声称拿到了当时私有管道原帧；没有管道截取或进程注入。

直接 require **已安装生产模块**、调用 `DesktopManagement.prototype.acceptCodingResult` 的本地探针，真实 profile 对象得到 CODING_RESULT_INVALID；仅将 profile 值改为旧测试字符串则得到 CODING_CONFIGURED，native exit=0。未抽取/改写校验实现，也未调用 constructor、API、GUI 或启动 Core。为隔离类型条件，probe 中 scope/checks 使用双方相等的空对象/数组；完整真实 scope/checks 相等由独立 SQLite 对照证明。原测试 `coding-authorization-boundary.test.mjs:42` 使用 `'profile-1'` 字符串，所以遗漏真实生产类型。

## 产品恢复与修复边界

不再 CONFIRM，不删除 installation，不把 session 改回旧 ref，不清除历史 UNKNOWN/null。新配置已提交，下一阶段只能围绕该已提交 ref 继续；配置成功本身不等于模型/工具资格或正式接受。

`RuntimeCodingStatus` 是只读，按原 request 读取已提交 installation；Desktop codingStatus 又调用同一个 acceptCodingResult，所以当前包重复查询预计仍出现相同校验错误。没有必要用重复 STATUS 证明已明确的类型错配。

最小源码修复应按真实 VersionRef 合同验证对象（严格 entity_type=Artifact、合法 id、正的安全整数 revision、合法 content_hash，拒绝缺键/错类型/不合法引用），并保留 scope/frozen/request/owner/context 和次数限制校验。修复应包含真实 producer 形状的 fixture、错误引用负面用例，以及 CONFIRM 后 STATUS 读取同一结果的用例；不把对象强制转字符串或只放宽为 truthy。

**重启后的原请求恢复不可假定自动成立。** Core STATUS 要求原 Owner/root/Host/parent_hash，Desktop 需要原内存 codingIntent。新父进程或丢失 intent 可能拒绝原请求 STATUS。因此修复与后续产品流程应明确如何重新打开已提交的当前配置/资格入口；不能通过再确认产生另一条配置来掩盖本次已提交事实，也不应为恢复而削弱原 parent 绑定。本次未修改任何源文件或改变产品状态。

初始 observer 漏写 `uri=True`，在打开连接时即失败；原脚本和错误保留，修正后才成功只读查询。生产故障与此 observer setup 错误分开记录。

本报告只接受上述诊断事实；没有接受修复、模型调用、工具运行或新 runtime 资格。正式增量 0，22 父任务仍 OPEN，0/42 正式接受。

## 正常重开现存配置：静态路径核实

Root 明确选择修复包正常重开，从原 session 已提交 newref 进入资格，不恢复旧内存 STATUS、不热补丁、不后台重建 intent、不再次 CONFIRM。这个路径有源码依据：

- `main.js:198-228` 的 prepareQualificationScope 从正常已选 session 发 `session.get`，取当前 `snapshot.model_config_ref`，再以同一 Host 的 host.status 精确匹配配置记录；不依赖 coding commit_key。它要求有效 desktop-shell writer lease、selection generation、revision/epoch 和 Host origin 一致。
- `ipc.js` 的普通 openSession 路径和页面 session 列表允许打开原会话；重开后必须取得/刷新合法写 lease，再点准备资格。UI 创建新会话表单默认配置不能代替原 session snapshot 的精确引用。
- `desktop-management.js` 新实例初始 codingIntent=null；prepare 仅在存在未完成 codingIntent 时拒绝，因此旧进程 UNRESOLVED 不成为新实例的持久配置障碍。Core 的已提交 session/config/runtime 仍是事实来源。

这只是静态可达性，不是重启/资格成功的替代证据。新进程必须由 Root 在真实 GUI 观察原 session、newref、writer lease 和新 PREPARE 请求绑定；不得据本报告直接宣布已资格。Root 报告已在收到诊断前点击一次只读 codingStatus，仍为相同校验错误；本 reviewer 未点击。另有 Root 正式只读 observer 按精确 request 绑定成功，引用与 hash 见补充绑定记录。

Finalizer 首次因 Windows 默认编码误读 UTF-8 JSON 而停止，尚未生成 FINAL；原脚本/错误保留，改成显式 UTF-8后冻结。未改动原观察证据。
