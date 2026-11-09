## Review Summary

**Verdict:** REQUEST CHANGES

**Overview:** 固定 snapshot 上的 driver 两处改动没有发现源码正确性问题，完整候选可以交 Root 作为下一受控 fork 准备的输入。整个准备包还需要修正一条测试观测口径：PRAGMA function_list 的 flags 不含 SQLITE_UTF8，现18项计划的统一预期容易把正确结果判失败。本结论不批准 source adoption、安装 SQL24 或执行任何验证。

受审 input namespace 为 da3c883ec6684c4487dbe36ff45affe4，writer 按 Root 输入 STOPPED。handoff cf24eb27c506f0e4fb524ab39cf29459433452326bf1e625df86f275fd503f57 /1754 bytes；manifest 7c0d979f80472e3035a9d4c267fe9d42f933870e72e9ed26fd5553c8c41aec4d /9647 bytes，31 listed members + manifest 32物理文件。全部成员 SHA/size 已独立核对并复制到本 receipt；读的是冻结 snapshots，没有读取或更改 Main、module cache、运行中的 writer 或旧包。

完整固定原 sqlite.go：095b77ed583de9b845814210debf6ca0a4e3b23d0134006db9e577e81db709d9 /44703 bytes。完整候选：0eea393caed04ad05ff9a8ca2a1e81d6dc3ad519728ebfcd62fec66b1101e2cb /45071 bytes /1383 lines。整个文件的逆差异字节相等，847-byte 历史 patch 4d409061e130d8908849ded09a0bc2cd0035c75ddbfd092614756d75b4d90679 与 inputs/15 的原件完全一致，按原 line/context 两个 hunk 独立应用恰好生成该完整候选。候选新增6行字段说明/字段和4行 conditional OR；没有其他差异。

### Critical Issues

没有在这两处 driver 改动中确认 Critical issue。

### Important Issues

- **V01 — future function_list 预期混合了 encoding 与 flags。** `inputs/future-tests.proposed.json:98` 写 “flags mask” 要等于 UTF8 | optional DETERMINISTIC | optional INNOCUOUS，而 I10/I11 明确用 function_list（52/57行）。固定 engine 的 `inputs/inputs/14-sqlite_g_0000000000060000.go:103566` 构造 mask 时没有 encoding；103589行把 _azEnc[funcFlags & SQLITE_FUNC_ENCMASK] 单独作为 enc 列输出，flags 则使用另一表达式。若将当前 methods 的式子用到 PRAGMA flags，会给正确 driver 的四组输出平白增加值1，导致假失败。

  **具体修复：** 明确区分内部 sqlite3_create_* 的 eTextRep 与公开 PRAGMA function_list 两个口径。后者分别断言 enc 为 utf8、flags 只等于可选 DETERMINISTIC | 可选 INNOCUOUS，并检查 builtin/name/type/narg，不能修改 engine 或宽松忽略未知 bits 来迁就错误 oracle。若内部 eTextRep 也记录，那里才是 UTF8 | 两个 opt-in bits。I10/I11 的2×2最小预期如下，所有数字是冻结源码推导，NOT_RUN：

  | Deterministic | Innocuous | internal eTextRep | function_list enc | function_list flags |
  |---|---|---:|---|---:|
  | false | false | 1 | utf8 | 0 |
  | true | false | 2049 | utf8 | 2048 |
  | false | true | 2097153 | utf8 | 2097152 |
  | true | true | 2099201 | utf8 | 2099200 |

  engine constants 在 `inputs/inputs/12-sqlite.go:3444`、3708、3782、4552行。engine 使用 INNOCUOUS/内部 UNSAFE 同 bit 的反转；不得直接拿内部 UNSAFE 位作为公开 flags。只需修正 future-tests 的 oracle/措辞，18项仍保持 NOT_RUN；本 finding 不要求更改正确的 driver candidate。

### Suggestions

没有必要再扩大 driver patch。下一步只要在 Root 的受控 source/resource lease 下构造完整、可锁定的 fork，保留本候选唯一文件变化，并让修正后的测试 oracle 进入独立复核。

### What's Done Well

- `inputs/candidate/sqlite.go:528` 添加默认 false 的 Innocuous 字段；847行仅在显式 true 时 OR SQLITE_INNOCUOUS，与843行 Deterministic 的条件独立。没有对默认、deterministic 或便利注册做自动提升。
- 原便利 wrappers 保持 keyed literals，767/818行均省略 Innocuous，继续 false。RegisterFunction 735–739行仍走同一个 default Driver 的 registerFunction，未新增全局 registry 或自定义连接绕路。
- 851–855行在 scalar/aggregate 分支之前构造同一个 eTextRep。冻结 conn.go 1089/1094行 scalar create_function 和1101/1106行 aggregate/window create_window_function 都使用该字段；driver.go 298–302行仍为新连接安装 descriptors，并在 error 时关闭连接。新 flag 未改变 callback lifetimes、VolatileArgs、trampoline、IDs、mutex 或 hook 顺序。
- 许可证与交付方案保留了真实限制：driver LICENSE 为 BSD-3-Clause 条款，SQLite public-domain 文件、sqlite-vec MIT 和完整 LICENSE-3RD-PARTY.md 保留原 bytes。local replace 明确不受根 go.sum 的 upstream h1 认证。

### Compatibility and delivery boundaries

新增 exported struct field 会让外部 unkeyed FunctionImpl literals 在重新编译时失效，反射的字段索引也有变化；不能承诺 Go struct 的二进制 layout/ABI。当前给出的 wrappers 与冻结测试注册使用 keyed literals，支持默认 false 的源码路径，但完整消费者编译和布局验证都没运行。旧二进制不会因文件复制获得新注册或 flag。这个风险在作者 compatibility 文档已经明确，不是新隐瞒问题，也不能用静态读源码替代未来完整消费者检查。

项目 snapshot 的 require 为 modernc.org/sqlite v1.60.1，root go 为1.27.1；driver snapshot module directive 为 modernc.org/sqlite，go 为1.26.0。根 go.sum 含 upstream module 与 go.mod 两个 h1。这里只确认冻结文本和 SHA，未对 module zip/dirhash、完整 upstream tree 或这些 h1 的来源完成独立认证，不能把目录名 v1.60.1 当认证结果。

建议的 version-qualified local replace 与原 module/go.mod 保留方案可以作为 Root 下一受控 fork 方案：

`replace modernc.org/sqlite v1.60.1 => ./third_party/modernc_sqlite_v1_60_1_researchos_innocuous`

它仍需完整 upstream inventory/origin 认证、完整 fork inventory、恰好唯一 sqlite.go delta、patch/candidate hash、原 licenses、精确 Root lease 和实际 build/backup/import/export closure 锁。version-qualified replace 只覆盖所写版本，未来实际 selected module version 与 replacement directory 必须由真实 module/build evidence确认；不能默认为任意升级仍使用这个 fork。go.sum 保留 upstream 校验值，另外的全文件锁才描述本地 replacement；现准备包没有创建完整 module fork 或锁文件。

给出的 conn.go、driver.go、三份 engine snapshot 全部保持冻结原 SHA；candidate 目录只有 sqlite.go，整个 sqlite.go 逆差异表明 wrappers 和所有未变源码字节相同。这不等于“完整未来 fork 已证明只有一个文件变化”：完整 module inventory 尚未生成，是明确 OPEN gate。source-evidence 的12段引用已与真实 frozen snapshot 对上，不把 author 的 before/after metadata 当 fresh Main/cache 复核。

### Verification Story

- Tests reviewed: **yes, static proposal/baseline only**。先读18项计划；默认 false、四组 flags、scalar/aggregate/window 的 view/trigger/CHECK、两新连接、duplicate error、NULL/error、旧 driver 与 F08 registration、旧 TestRegisteredFunctions 的意图覆盖清楚。V01 需修正。聚合直接放 CHECK 本就非法，作者没有把它列为正例。全部18项 NOT_RUN，没有 native test、Go AST、编译或 SQLite/UDF执行。
- Build verified: **no**。完整1383行候选及两 hunk读过，byte inverse/context application 是文本验证，不是 Go parse/compile。只有自己的 readonly metadata/hash/copy 脚本执行。根 module/cache/安装/SQL/SDK/Node/HTTP/模型调用均0。
- Security checked: **static flag binding only**。Innocuous 是 caller 断言，不是 runtime purity enforcement。这个 patch 不证明每个 F08 callback 能安全 opt-in；冻结输入17仍是旧部分 callback proposal，未来注册源、完整 transitive DB/Host/Clock/外部状态访问复核与错误/strict frozen shape/hash 验证仍 OPEN。未 blanket-enable callbacks，未改 trusted_schema，也未触碰生成 engine。
- Supply chain: **OPEN**。完整 upstream module origin、完整 source inventory、完整 fork lock、transitive build/runtime/stdlib inputs、全消费者编译及全部 driver tests 尚未产生或执行。新 candidate 仅具备向 Root 受控 fork 准备传递的资格，本 review 不自授 implementation/adoption lease。
- SQL24、三 callback 完成、旧22/23真实 binary/startup/backup/rollback compatibility、F08其他 source proof、正式用例接受均未由这次 driver 修订解决。Source acceptance=false，SQL24 adoption=false，formal increment=0。
- Origins: 作者本包新 failure origins=[]；本 review 迄今所有实际 outer exit 为0，native 无明确桥仍 NULL。一次 rg 命中 generated string 长行而导致可见结果截断；已保留实际输出，仅换用精确有界行段查看 engine，未推断这是 process failure或重置计数。所有历史 origins/旧 receipt 均不写入、不重计。

reviewer 非作者；封包后 writer STOPPED。Root 可用精确候选继续受控 fork 准备，但应先修正 V01 oracle；没有 SQLite SQL24 可安装的结论。

