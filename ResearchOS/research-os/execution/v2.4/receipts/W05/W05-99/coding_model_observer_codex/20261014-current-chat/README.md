# 新 coding model-ref 的只读观察 helper

本 helper 已通过 19 项合成 SQLite 自测，并核对当前 live 数据库的 9 张表结构和对应源码。新的 coding PREPARE 尚未产生有效 request，因此没有进行新配置或新资格 Run 的 live 验证。它不构成资格通过、native 验证器完成或任何 22/42 正式增量。

## 文件及边界

- `observe_coding_model.py`：可单独复制的标准库 Python helper，Python 3.9+（本轮 Python 3.14.3）。
- `selftest_observer.py`：19 个合成 SQLite 自测，临时 fixture 仅在本目录创建并自动清理。
- `selftest-final-output.txt`：最终源码的自测输出，native exit 0。
- `schema-source-evidence.json`：只读 live 表结构与本轮引用源码的 SHA256；没有复制产品行。
- `FINAL-report.json` 与 `manifest.json`：范围、限制、文件哈希。

只读取显式的 `project_id`、`session_id`、`owner_principal`，再要求 `coding_request_id` 或 `model_config_ref`。没有默认数据库、项目、Task、Run 或旧 model-ref。`qualification_request_id` 缺省时只列候选，不自动挑选 latest；显式传入后，只按该 request 的 consumption 推导 Run。可选 `run_id` 仅用来核对，不替代 request 绑定。未匹配的旧 request/ref/Run 会失败。

连接使用 SQLite URI `mode=ro`、`PRAGMA query_only=ON`、`BEGIN`/`ROLLBACK`，附表/敏感 config 列和写语句受 authorizer 拒绝；查询用参数绑定，1000 行、JSON 2 MiB、输出 2 MiB、8 秒 SQLite 查询预算。没有 API、GUI、subprocess 或模型调用。输出须处于 helper 所在目录，采用 exclusive create，已有输出不会覆盖。

新 model-ref 的链为：coding confirmation → installation（表 request_hash 和 body request_hash 都检查）→ coding authorization → configuration metadata → runtime_bindings/profile_ref → plan → exact qualification request → consumed Run → effect/ledger/acceptance。保留 UNKNOWN/null 费用；effect 数按不同 journal key 计数，PREPARED/STARTED/CONFIRMED 不视为三次调用。原生 stdout frames、verifier stderr、numeric native process wait 未取得时明确 NOT_OBSERVED。数据库里的 Run.exit_code 不代替外部进程的 wait 证据。

完整 coding frozen/assets、配置 credential JSON、dispatch manifest 与 MODEL prompt/response body 不输出。coding nested request/authorization 的完整哈希未重算，仅检查已存 request hash 和身份链接；qualification 的 17 字段请求与 plan/profile 的受限 canonical hash 会重算。BudgetPolicy 是当前存储链的观察，不重演 effective-version 或 current admission。历史已消耗 request 的 session 后续变化只记录，不冒充当前授权。

## 精确运行命令

下面是本工作区的数据库/Project/Session/Owner 参数。必须将 `GUI_CODING_REQUEST_ID`、两个已批准文件路径以及（第二步）`GUI_QUALIFICATION_REQUEST_ID` 换成当前 GUI 的精确值。不能填旧资格 request，也不能选择列表中最新一条代替。每次换一个尚不存在的输出名。

```powershell
$helper = 'C:/Users/yqyyds/.codex/researchos-build-worktrees/coding-model-observer-review-20261014/observe_coding_model.py'
$common = @(
  '--database', 'D:/作品集/ResearchOS/research-os/.local/live/current-chat-normal-desktop-first-use-20261012/data/researchos.sqlite',
  '--project-id', 'a7ebcf2a322c6abcf87e043f601ee804',
  '--session-id', 'a09d4435036b2b32a0d7076bfc53fd93',
  '--owner-principal', 'owner-95f641f393696f7d1439dc36ae99935d',
  '--coding-request-id', 'GUI_CODING_REQUEST_ID',
  '--expected-write-path', 'APPROVED_FIRST_PATH',
  '--expected-write-path', 'APPROVED_SECOND_PATH'
)
python -B $helper @common --out 'C:/Users/yqyyds/.codex/researchos-build-worktrees/coding-model-observer-review-20261014/observation-coding-001.json'
# 新资格 PREPARE/CONFIRM 后，使用其精确 request_id：
python -B $helper @common --qualification-request-id 'GUI_QUALIFICATION_REQUEST_ID' --out 'C:/Users/yqyyds/.codex/researchos-build-worktrees/coding-model-observer-review-20261014/observation-qualification-001.json'
```

若已知精确新 model-ref，可以用 `--model-config-ref 'GUI_NEW_MODEL_REF'` 代替 `--coding-request-id`，或两者一起传入以检查一致性。只能在 coding installation 已完成后这样使用。输出目录跟随 helper 文件的位置；复制到正式 receipt 目录后将 `--out` 指向该目录内新文件。

```powershell
python -B 'C:/Users/yqyyds/.codex/researchos-build-worktrees/coding-model-observer-review-20261014/selftest_observer.py'
```

退出 0 表示观察绑定成立（阶段仍可能是 PREPARE/待消耗），退出 2 表示 schema/read/binding 失败，详细安全错误码在新输出文件中。输出路径或重复输出等 CLI 前置错误也会非零退出。不能把 observation_bound、退出 0 或 fixture 通过解读为执行验收通过。
