## Review Summary

**Verdict: REQUEST CHANGES**

两份 adapter 保持 source preparation 边界，但实际授权链的三个静态缺口应先修正。本次没有运行 adapter、controller、helper、Go、SQL、HTTP、CAS 或任何目标。

### Critical Issues

无已确认 Critical。

### Important Issues

- **R01 — authority_adapter.proposed.py:177 / scope**：保护旧 SQLite 子树的比较区分大小写，Windows 上 `MODERNC.ORG/SQLITE@V1.60.1/new.go` 可绕过。controller 在 offline copy 前检查 1899 成员，`xb` 只拒绝已存在文件。用 `casefold()` 比较完整受保护前缀，且真实 prepared 闭包必须证明复制后 pristine inventory 仍等于原锁。原 controller 是冻结输入，需独立审批其变更，不能静默改 pin。
- **R02 — authority_adapter.proposed.py:307 / prepared_evidence**：`all(...)` 接受空、缺项、重复 roster；prepared files 也可为空。请求、Job、原始 stdout/stderr、实际 outer invocation 和完成结果尚未形成同一 prepare 的绑定。严格核对 I01–I18 完整 roster、非空闭合文件集、固定输出目录及原始 request/invocation/raw/manifest/outer 配对；缺任一实际事实仍 OPEN。
- **R03 — authority_adapter.proposed.py:245 / registration**：注册独审缺当前 scope/draft/desired refs 的关系核对；实际 argv 仅核前 6 项，忽略选择 draft/binding、review、output 的尾参和 cwd。owned helper 的结果不含 argv，不能由 `job(result)` 补齐。注册独审应绑定当前 scope/draft 与四份 desired，完整 invocation/request 应绑定已审 argv、cwd 和注册 namespace。预执行 audit 输入与最终 audit 回执必须分开，避免哈希循环。

全部反例均为静态推导，未执行。精确字段与最小 NOT_RUN 控制集见 review.json。

### Suggestions

- **authority_adapter.proposed.py:167**：资源重复检测也宜采用 Windows 大小写一致的比较键，原 path/hash/bytes 继续完整保留。

### What's Done Well

完整旧 failure prefix、原 payload、去重、四份 canonical 原件/目标件和 ST/commands 原始字节得到保护。JSON 重复键拒绝和 immutable ref 检查明确。作者诚实保留全部 A01–A07 OPEN，partial17 排除 I17，未声称实际 grant 或用例接受。

### Verification Story

- Tests reviewed：只读 NOT_RUN 控制与已冻结 driver/I16/I18 独审来源；没有运行测试。
- Build verified：否。仅两份 Python source AST 解析，未 import/execute，也没有 Go AST/compile。
- Security checked：静态检查路径、raw/hash、独审/CAS/grant/prepare 数据关系与过程边界。
- 实际重哈希作者 15 个成员和全部 46 refs；`after.refs` 与 before 精确相同。没有重新核验 catalogs 下 1899 或其他大树成员。
- 本轮新增失败 0；旧 origin、canonical、失败计数、正式接受数均未写。

Root 后续最小实现是有限实际资源 catalog、明确 phase/tuple/cut/lease、两阶段完整 scope 独审、真实 CAS/wrapper/sealer 和单次 grant producer，以及真实 prepared/raw 链。上述修正与这些 OPEN 闭合前，不授执行资格。所有目标仍 NOT_RUN，I17 与全 18、SQL24、完整 callbacks 保持 OPEN。

