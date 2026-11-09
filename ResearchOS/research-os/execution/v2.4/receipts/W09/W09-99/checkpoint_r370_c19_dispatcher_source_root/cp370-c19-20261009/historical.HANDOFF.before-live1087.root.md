# Current Root continuation: CP373 / OW177 / CM39

Goal remains ACTIVE; 0 of 42 formal cases accepted. Main23 actual build completed with 5 Go exits0; candidate awaits independent final delivery and Root qualification binding. All original failures retained; canonical next1067, live next1076; pending1067..1073 sealed, Source captures1074..1075 await sealing. Original API stdout truncation is preserved, complete durable state independently read back.

Current resume: D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W09\W09-99\checkpoint_r370_c19_dispatcher_source_root\cp370-c19-20261009\RESUME.cp373-main23-built-pending-review.live1074.root.json
SHA256 21bf7e56694c94a50e08d9a07419e985e8bc6f5f5ef53be99c2eee98eb170e24 bytes 4149

Pending diagnostics: D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W09\W09-99\checkpoint_r370_c19_dispatcher_source_root\cp370-c19-20261009\pending-diagnostics.cp373.live1074.root.json
SHA256 5f7296e7d25a53bed378a21687ef07d544ce56b8c9609851dd5ca515fdb8d019 bytes 9899

# 当前续跑入口：CP372 / OW176 / CM39 / live next1065

读取 D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W09\W09-99\checkpoint_r370_c19_dispatcher_source_root\cp370-c19-20261009\RESUME.cp372-public22-readonly-actual.live1065.root.json。Root已完成public22既有产物只读真实复核：83表，零新Native，原1025失败保留；独立actual复核Task64进行中。41个原始诊断1024至1064已封待登记，失败计数未重置。M4 Source修正37项有限控通过待独立复核。正式接受0/42，目标ACTIVE。

# 当前续跑入口：Root live1064 / Canon CP371-OW175-CM39

读取 D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W09\W09-99\checkpoint_r370_c19_dispatcher_source_root\cp370-c19-20261009\RESUME_POINTER.live1064.root.json 与 D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W09\W09-99\checkpoint_r370_c19_dispatcher_source_root\cp370-c19-20261009\RESUME.cp371-time-contract-live1059.root.json。35个待登记原件已封至1058，1059至1063待完整IO关联。正式接受0/42，目标ACTIVE；旧失败和完整交接正文保留。

<!-- R371 continuation: read HANDOFF_RESUME_PACK_R371.md and its exact pinned live1042 Root resume. Older continuation/body content below is historical; current Canon is authoritative. -->

<!-- R370 continuation: read HANDOFF_RESUME_PACK_R370.md and the exact pinned live1013 Root resume. The R156 content below is retained as historical evidence and must not override current Canon. -->

# ResearchOS v2.4 resume pack (rewritten 2026-10-05 from disk at HEAD b6ac2d69)

Read this first, then re-verify it. Every figure below was produced by `.local/rewrite_resume_pack.py`
reading `execution/v2.4/step_state.json`, `checkpoint.json` and `commands.json` at run time; nothing here
is carried over from the previous pack's numbers. If this file and the state files disagree, the state
files are right and this file is the bug.

## 1. Where the build stands (measured)

- checkpoint revision **156** (expected_previous 155); `next_step_id` = **W10-01**; failure counters
  and integrity events carried forward, never reset: 17
- cards accepted: **28 of 71**; statuses {'ACCEPTED': 28, 'BLOCKED': 2, 'IN_PROGRESS': 1}
- parent gates: accepted **1 of 22** (['W00-99']); BLOCKED: ['W01-99']
- formal cases accepted: **none of 42**
- registry: revision **22**, 24 keys, **16 BOUND**; the plan declares 33
  distinct keys, of which **20 are absent from the v2.4 registry**: ['acceptance.audit', 'core.qualify', 'environment.verify', 'package.validate', 'release.reproduce', 'test.backup', 'test.contracts.security', 'test.cycle.live', 'test.evaluation.fixture', 'test.evaluation.security', 'test.evolution', 'test.experiments', 'test.jev.fixture', 'test.jev.live', 'test.overnight', 'test.skills', 'test.sources.fixture', 'test.ui', 'test.ui.preview', 'test.ui.visual']
- protected-work audit just now: **585 registered evidence rows across 585 distinct files,
  0 drifted, 0 missing**, and neither state file is registered as evidence
- obligation register: **237 entries**, append-only; it is a queue to triage, not a list of failures

## 2. What is in flight, and what can be started

**W10-01** (see its row note and receipt directory)

**Dependency-eligible now (3):** W12-02 (用途等价资源切换与用户可操作请求, prio 1390), W17-02 (数据出口与独立holdout权限隔离, prio 1500), W18-01 (一致性备份和迁移前快照, prio 1520). `task_packet next` selects by DAG then priority,
so compare against its output rather than assuming the lowest card number.

## 3. Route feasibility — the check that was missing until 2026-10-05

A card is executable only if all three hold: its declared key is BOUND, the key's selectors resolve that
card's `--task-id/--check-id/--case-id`, **and the program behind the key is inside that card's own
`write_scope`.** The third was never checked before. Measured over the open slices: 1_key_absent_or_unbound: 20, 2_selector_not_routed: 3.

**Nobody may write `migrations/sqlite/**`** — no card's write_scope covers it — so anything needing a new
column or table must derive from existing tables.

## 4. Corrections to earlier handoffs, so they are not re-inherited

- **`cli.entry_run` is not the parent-gate neck.** No card's `verification_commands` names it. The gate
  chain runs through `W01-99`, and `W01-99`'s blocker is not a missing dependency: all four deps are
  ACCEPTED and the row's own reason is that **A02 and C10 have no registered selector at all**, nothing
  emits `A02-02`/`A02-03`, `C11-04` has no emitter (it belongs to `W12-02`, which is eligible), `C04` is
  already covered, and the LIVE dual-end run needs the resource `Windows_desktop_session`.
- **`test.retrieval` is bound** (rev 21) and `test.retrieval.revocation` (rev 22) exists. The older note
  "no Go key runs the domain suite" is false: `tests/evidence/check/main.py` runs
  `go test -json -run '^TestW0901' ./internal/domain`.
- **The product's own CLI builds and runs** (`go build -o .local/bin/researchos.exe ./apps/cli`, then
  `version` → `researchos 0.2.4-w0203 protocol=researchos-client/2`, exit 0). `W01-G03`'s
  `own_cli_entry_present` is false only because `qualification/v2.4/qualify.py:218` scans filenames under
  `apps/cli`, while the accepted build step deliberately emits the binary to `.local/bin/`.
- **`test.security` and `test.experiments` answer gate ids, not slice ids**, so W09-02 and W10-01 each had
  to bind a new key to a handler in their own scope. Those two deviations are disclosed in their receipts;
  `W09-99` still declares the dead `test.security` pair.

## 5. How to re-verify every number in section 1

    python -B .local/rewrite_resume_pack.py            # re-derives this file
    python -B .local/protected_evidence_audit.py       # recomputes all registered digests
    python -B .local/measure_route_feasibility.py      # the three-condition route audit
    cd "D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4" && python tools/task_packet.py next --state "D:/作品集/ResearchOS/research-os/execution/v2.4/step_state.json"

## 6. Constraints that are easy to break by accident

- A registered receipt is byte-frozen. Corrections land in a **new** file (`claim_corrections_*`,
  `post_review_actions_*`, `prerequisite_inventory_correction_*`), and the superseded sentence is struck
  through in the row note rather than deleted.
- Read acceptance from `step_state.json`, never from a receipt's `status` field.
- `commands.json` is a shared append point: appending a key can silently re-route an existing selector.
  Regress every selector accepted cards actually dispatch, and assert the pre-existing entries are
  byte-identical before `os.replace`.
- **Never append a selector to a key whose handler emits another card's roster** — that manufactures a PASS.
- Hash raw bytes; a re-encoded or newline-normalised read hides drift in exactly the files that are empty.
- Resolve toolchains from `execution/toolchains/locked.json`; set `RESEARCHOS_GO` or legacy domain reds are
  misattributed (this has happened repeatedly, including while writing this pack).
- Running a project's own verification driver is a **write**: `qualify.py` rewrites its own evidence file.
- Mutation discipline: one mutant per operand, never one per condition; and a guard written to enforce that
  must itself be exercised against a violating input before it is cited as evidence.
- No push, no deploy, no purchases, no reading secret values, no second construction session, never
  `git reset/clean/checkout .` against the tree, explicit paths only in `git add`.
