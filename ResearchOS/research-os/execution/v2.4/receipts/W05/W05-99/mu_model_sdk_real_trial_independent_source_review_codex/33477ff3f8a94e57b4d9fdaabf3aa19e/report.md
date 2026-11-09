## Review Summary

**Verdict:** REQUEST CHANGES

**Overview:** 四份 Go 产品补丁和 Mu SDK 试验 runner 尚有四项阻断。新路径保留了 UNLIMITED 金额语义与原 CAPPED/STRICT 储备约束，但实际 Root 准入、资格证据闭包、总时限和初始化前隔离还未完整实现。

### Critical Issues

- 未确认 Critical 项。

### Important Issues

- **R01** — Root finite authority is pinned without validating or consuming its meaning。D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_executable_source_codex/1b8bc13521764e508f540dc2399ac33d/mu_sdk_trial.proposed.py，行 148, 169, 206, 219。Registration and grant are only pin_file inputs. Their actor, decision, scope/input/current-source/phase/lease/budget and once-consumption bindings are not read. Hash-valid {} or authorization-false files can pass this admission. Outer-job claims are three asserted JSON values. Isolation only checks absolute roots and inequality with intake private root. 修复：Before output allocation, database access, spawn or product effects, consume an independently reviewed Root finite grant: exact registration/grant/input/source/binary/profile/route and actual argv/cwd/env/owned-root bindings, current lease, phase and once consumption, 3 requests (qualification 1 plus ordinary 2), requested tokens 8190 <= 8192, and real owned-job deadline/tree evidence. Canonical disjoint roots must reject aliases/reparse/subtree overlaps. NULL, false, foreign, consumed or mismatched authority must fail closed. New schema and actual Root producer remain proposals/OPEN until separately adopted.

- **R02** — Qualification, profile and provider facts do not close the causal graph of this trial。D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_executable_source_codex/1b8bc13521764e508f540dc2399ac33d/mu_sdk_trial.proposed.py，行 105, 128, 171, 200, 276, 313, 380, 397。AVAILABLE is read from RuntimeRegistration, but the trial never associates the selected qualification run with runtime_qualification_runs and runtime_bindings sealed profile bytes, project, task, Goal, epoch, plan or actual qualification authority. Effects use run_id without project. UNKNOWN ledger validation is a minimum count; fact_refs hashes files and permits missing model_transport, and SSE completion is a substring check. Ordinary counting/witness does not independently bind the exact runtime/profile/read result to the selected qualification. 修复：Read and bind the real qualification/binding rows and sealed artifact raw bytes to this project/Goal/runtime/qualification run/profile/plan/epoch and current validity. Require project+run effect queries, exact provider-request/effect/ledger/fact associations, strict complete raw SSE/hash binding, and exact ordinary dispatch runtime/profile plus read1 path/body. Do not release the ordinary branch from a supplied AVAILABLE label or unrelated qualification. Missing actual evidence remains NOT_RUN and unknown billing remains NULL.

- **R03** — The next child is launched before checking the total deadline。D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_executable_source_codex/1b8bc13521764e508f540dc2399ac33d/mu_sdk_trial.proposed.py，行 239, 261。command_once calls Popen before checking deadline in the polling loop. A qualification wait or previous stage can exhaust the 300-second budget and the next config/run child still launches. Fixed 2+2-second waits and final receipt/hash IO have no remaining-budget reserve. Spawn/drain failures can bypass a fully closed first-cause/raw invocation receipt. 修复：Check the real Root absolute monotonic deadline and remaining cleanup/evidence reserves before every spawn/side effect; bound waits and cleanup by remaining time and prohibit a later launch after exhaustion. Preserve one immutable first cause, original command/output and nullable exits for spawn/wait/parse/hash failures, with separate secondary failures and no retry. Actual outer owned-job evidence must prove the full Control/worker/CLI tree stopped within the authorized bound.

- **R04** — Trial isolation is checked after mutable lease/database/host setup。D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_executable_source_codex/1b8bc13521764e508f540dc2399ac33d/apps_control_main.go.proposed.go；D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_executable_source_codex/1b8bc13521764e508f540dc2399ac33d/internal_host_host.go.proposed.go，行 {"control":[49,51,63,90,178,182],"host":[126,154]}。Control acquires the data-root lease, opens/bootstrap/migrates the store and creates CurrentMu before the new partial/equal-vault rejection. Host.New creates host/private directories before selecting the readonly vault and its public Config entrypoint has no equivalent root-isolation rejection. filepath.Clean equality is case-sensitive and does not prove Windows alias/subtree separation. 修复：Validate the complete trial tuple and canonical Windows root separation before AcquireDataRootLease/store.Open/Bootstrap/NewCurrentMu and before Host.New mkdir/ACL/mutable-host setup. Apply the same guard to both Control flags and the Config entrypoint. Reject equality/case/reparse aliases and ancestor/descendant overlaps; preserve the original nontrial startup behavior and the sealed readonly old vault.

### Suggestions

- 本轮不增加非必要功能或通用框架；按 review.json 的最小反例修复并交独立复审。

### What's Done Well

- 27 个 Source 成员和 3 个 correction 成员全部实读哈希；四份完整 Go 正反变换均成立，Main 原件无漂移。
- all-active-scope UNLIMITED/cap-null/non-BLOCK 门禁保留，正金额路径仍使用原 RESERVE；真实 MODEL UNKNOWN 不伪造价格或重复责任账。
- 实际接线保持 CLI→Mu SDK→protocol.model→Go broker，重试关闭。2730×3=8190 是 requested-output 界限，实际费用和未知计费维度保持 NULL。

### Verification Story

- Tests reviewed: yes。读了现有 fixture、资格和严格预算断言；本轮所有新增实际测试均 NOT_RUN。
- Build verified: no。仅四个 Python Source 的 AST 与 Go 完整字节正反变换，无 Go AST/compile/gofmt/build。
- Security checked: yes。公开源码边界已审；R01/R04 为具体阻断；未解封/读取密钥。
- candidate/SDK/provider/product/canonical 操作均 0；Source/42formal 接受增量 0。Root 实际 authority、qualification、owned runtime 和后续 LIVE 资格仍 OPEN。
- 新增元数据 origin 共两次：failure-origin.js-unbound-ns.json（Root623）及 failure-origin.command-length.json（Windows os error 206，创建 Python 进程前拒绝）。两者真实 outer/Python/native 数值全部 NULL，原输入未重跑，旧 origin 不重计。

本结论仅为 SOURCE 独审 REQUEST；修复作者应保留原包，以新不可变 namespace 修 R01–R04 后再独立复核。
