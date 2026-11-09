# Independent official test2json resource review

Verdict: APPROVE — TOOL_COMPILATION_COMPONENT only.

结论：Root指定Go1.27.1的官方cmd/test2json已由实际owned build成功产出指定二进制，实际输入、两次Go命令及三个源码/产物守卫关闭证据一致。可将该精确binary作为后续Source fixture的冻结reporter资源。本结论不接受Q2源码，不证明test2json已执行或10个目标叶通过，不提升原FULL或产品状态。

输入：D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/official-test2json-resource-build-root-3e9129c5f7c9461e/resource-build.closed.json
SHA256 bf9a9df9448be2df121455460378d895441a244684ca053bbf288f92276dbf01；24186 bytes。

产物：D:/作品集/ResearchOS/research-os/.local/official-test2json-resource-8a1fba36028c4c0b9ed30c0a7aca54cc/programs/test2json.exe
SHA256 dead8050fd4e0e0471407380898fe9642b9107048e0ad119cb652821dfe58f7c；4932608 bytes。

## Critical / Important Issues

本组件范围未发现阻断问题。

## Provenance and actual options

固定Go：D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe，SHA256 d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490；17508352 bytes。原build脚本检查该固定hash、Go VERSION=go1.27.1、与既有A5 GoRef相同，并在base SourceReadGuard内保留Go executable、VERSION、src/go.mod、8 compiler tools、Python及加载的helper/runtime依赖。

实际两步：
1. 固定Go list -deps -compiled -json cmd/test2json。
2. 同固定Go build -trimpath -buildvcs=false -o 独占scratch/programs/test2json.exe cmd/test2json。

环境显式设置GOROOT、GOTOOLCHAIN=local、GOPROXY/GOSUMDB/GOWORK/GOENV=off、CGO_ENABLED=0、GOFLAGS=-mod=readonly -p=1、GOMAXPROCS=2；PATH仅固定Go目录及Windows System32，TEMP/TMP/profile指向独占scratch。没有通过PATH寻找Go、没有自动下载toolchain或外部module。包源码来自这个已固定Go发行目录；本次不是再次联网认证发行版。

独立从210190-byte原go list stdout逐对象重算：102包全部Standard/Goroot、无Error/DepsErrors；包含cmd/test2json与cmd/internal/test2json。13类Go/compiler选中字段共759个唯一源输入，与selected-official-compiler-inputs.json精确集合与hash一致，实际EmbedFiles为0。实际选中源、compiler8、Go/Python/helpers、原IO及canonical当前refs共877个独立refs，全部当前hash/bytes一致。没有执行编译脚本或Go来取得这些结论。

## Actual closure

- 原public tool chunk2e8c88记录outer exit0与ROOT_PYTHON_EXIT=0。
- go list PID85976 / creation_time_100ns134359727356412390；build PID81596 / creation_time_100ns134359727393775988；各自actual_native_exit=0，未timeout/error。
- 两个不同unnamed exclusive Jobs均kill_on_close、assign_before_resume、primary_exit_confirmed、active_processes_last_observed=0、job_idle_confirmed、handles_closed，errors空。确认的是两次工具构建命令的Job，不是后续fixture Job。
- base101、selected760（759源+inventory）、binary1守卫entry集合与实际refs逐一一致；每项verified/final_path_match/closed；三个守卫整体verification PASSED、retained_handles_count0、failure null、errors空。
- closed回执在finally之前写入，因此独立结论同时核对finally的三份cleanup及最终outer/Python0，未只凭closed.status自证完成。

## What's Done Well / limits

- 官方cmd/test2json实现具有冻结的Go发行来源、完整选中依赖清单和精确产物hash；可以直接调用固定RESEARCHOS_TEST2JSON及固定SHA，无需把先前建议的literal go tool作为唯一实现。
- 原始命令、raw stdout/stderr、选中输入、Job实际退出/关闭和守卫关闭分开保留，full refs见input-refs.json。
- 使用现有shared GOCACHE；成功build可复用Go构建缓存，本审查不声称759个输入对应的全部依赖均本轮从零重新编译，也不声称完全独立可复现构建。
- 产物守卫已关闭。后续Root使用前须重新核对精确binary hash并持有相应guard，不能把本次已关闭guard称为持续冻结。
- test2json执行次数0；产品native fixture、provider/model、SQL、private key均无新增执行或验收证据。目标10叶、parent/child JSONL、SDK descendants/lease关闭及Q2 Source独立审查仍待后续。
- 原FULL1261/25/4 FAILED不变；CP356/OW168/SS/CM、6/22历史和0/42当前、GoalActive不因本组件审查改变。
- 本轮独立检查仅固定Python静态/文件读取；没有新机械失败，未写Main/canonical/旧receipt。首次宽details读取输出被截断并如实保存，最终判定基于完整磁盘数据的有界机械核对。

Tests reviewed: 本组件没有执行目标测试；审查官方工具构建输入和实际回执。
Build verified: yes，通过已有实际build/exit/产物/closure独立复核；未由reviewer重跑。
Security checked: 仅编译资源边界、固定toolchain/source/离线环境、守卫与Job生命周期范围；不冒充产品安全接受。

STOP。

