# 文档包复用 a418 机制证据的只读建议

结论：`CONDITIONAL_REUSE_OF_PRIOR_FIXTURE_MECHANISM`。在最终包满足下列精确比较且新包静态 16 项通过时，可以引用 a418 已执行的启动/停止机制证据。不能称“执行依赖全部相同”，不能将 a418 的 28 项报告改写为新 ZIP 的新执行 PASS。最终 ZIP 尚未在本审查中检查；本建议没有执行任何测试或启动产品进程。

## 真实读取链

| 入口 | 实际读取/使用 | 与文档包的关系 |
| --- | --- | --- |
| `scripts/start.ps1`（源 `ops/release/start.ps1:9`） | 首先执行 verify；随后设置 DATA_DIR/WEB_DIR/LISTEN，生成 instance 与 root/data path hash，启动 bin/control.exe，并核对 OS 命令行、EXE 路径和创建时间 | 新 manifest 是启动前置的变化输入；不能从旧包验证直接推定新前置通过 |
| `scripts/verify.ps1:5-40` | 读取 release-manifest.json；校验 format、每个 files 的安全路径/size/hash、reparse 与完整清单；build_id 只随验证结果输出 | 新文档及 manifest 必须重新验证；它不把 source_commit/build_id 当运行权限或独立签名 |
| `scripts/stop.ps1:9-33` | 读取数据目录的 fixture-control.pid；核对 schema、instance、root/data、PID、进程创建时间、EXE 路径和 OS command line | 不读取 release-manifest、source_commit 或 build_id；新包路径仍是动态身份输入，旧执行不证明任意未来路径/环境 |
| `apps/control/main.go:60-85` | 普通启动取得新 data-root lease、打开 SQLite，读取 bootstrap/migration SQL 与 domain/OpenAPI contracts；使用 webDir；loopback health 不执行 provider | 普通启动链未读取 release-manifest/source_commit/build_id；必须保持 binary、迁移、合同与 web 字节不变 |
| `apps/control/main.go:39,137` | `--manifest-sha256` 只用于显式 `--import-spec` 管理路径 | 不是普通 fixture 启动的 release manifest 身份参数，不能混同 |
| `ops/release/build.py:300-323` | Go 用 `-trimpath -buildvcs=false -ldflags=-buildid=`；manifest source_commit 来自 Git，source_tree_sha256 由入包源/文档算出，build_id 是其前 20 字符 | 文档变化足以改变 manifest 身份字段；四个 EXE 是否不变必须机械核对，不凭编译参数推定 |
| `tests/release/check.py:92-136` | 仅 `--run-fixture` 分支启动两套临时 control；没有该参数则跳过这 12 个启动/停止相关检查 | 新包只运行静态 16 项；仍会运行 PowerShell verify 子进程，但不启动 control/runtime/release_host 产品进程 |

普通 control 另有显式 runtime coordinator 配置、import-Jev、fixture replay 与继承 drain pipe 路径；既有 start 不传这些管理参数。本建议不认证这些路径，不读环境凭证或旧受保护 payload。默认赋值 FrozenProvider 不是实际 provider 资格证明。

## 最终机械复用条件

1. 冻结新源码与两个新 ZIP。相对 a418 ZIP，新增/修改仅限明确列出的 `docs/`、`release/outcome_report.json` 和 `release-manifest.json`，不得默许其他文件变化、删除或改名。
2. 对全部非上述允许变化的 ZIP entries 验证路径集合、原始字节、SHA-256、大小一致；单列四个 `bin/*.exe`、全部 `web/dist/`、start/stop/verify、contracts/spec、全部 migrations、fixture config、locks、命令 registry/dispatcher 和现有 check.py。变化的文档必须核对内容没有增授权限、改变配置/数据路径/启动模式或伪造资格。
3. manifest 只允许正确的文档 files 清单差异与 source_commit/source_tree_sha256/build_id 推导变化。format、platform、tools、build_flags、locks、API/domain schema hash、migrations、database、commands、sbom、runtime_profile、rollback、evidence_index、acceptance 等语义字段保持一致；新增字段或其他差异须显式判明，不能自动归类为文档变化。
4. 新包使用未变的 existing check.py，不带 `--run-fixture`，只执行一次；保存实际退出码和完整 raw 后解析。预期 16 个静态检查，包含当前 manifest/allowlist/hash 及篡改、缺文件、额外文件、路径逃逸拒绝，未绑定命令继续非零。
5. 新报告明确三组数据：`historical_checks=28 at a418`、`current_static_checks=16`、`current_native_fixture_runs=0`。只复用旧包实际执行过的有限机制，不声称新 ZIP 已实际启动、在新环境运行、完成 A15 或完成当前 42 例。

源与包摘要均发生变化。即使新包 control.exe 与 a418 的 `b667c45bef91508df9c02f16ad91138762bcb0cbf30a481c998e71cc8194c8eb` 相同，也没有产生新的 current-control now-current proof。a418 自身与早期 `203fe4...` 证明不同，原权限关闭和全部未接受门继续保留。

若任何非文档执行材料或权限/DB/mode 语义变化，本建议的复用前提不成立；报告应标出变化并停止本次复用判断，不自行扩大执行。原 a418 报告、W21 原快照和 supplement 全部保持不变。
