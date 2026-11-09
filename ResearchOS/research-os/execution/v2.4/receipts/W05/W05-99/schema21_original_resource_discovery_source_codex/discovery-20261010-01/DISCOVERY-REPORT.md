# schema21 原始 Source 资源发现

本包完成 Source 资源发现，可交 Root 审查后在新目录独立构建。推荐历史提交 `f6e4a0ed54d697c7214a75743cd1b83dc3685ddb`，tree `9696c3a456a4786cbb5518c75ead66e6d8120a83`。本轮没有编译或启动程序，没有获得 old21 程序资格、正式 old21 Case、Runtime grant 或活动 TP。

## 两个真实历史快照

| 输入 | a3816cd36322fdf554b629e780d07bb23fcaf355 | f6e4a0ed54d697c7214a75743cd1b83dc3685ddb |
|---|---|---|
| Git tree | 53d5270608a7e26c817b285172355da092822013 | 9696c3a456a4786cbb5518c75ead66e6d8120a83 |
| 编号 migrations | 原始连续 1..21 | 原始连续 1..21 |
| public control / domain.New 安装 session addon | 不安装；仅文件存在 | 同一事务执行 next_v24_sessions.sql，并安装 session fence |
| 适用来源 | schema21 基础数据库来源候选 | schema21 加真实公开客户端 session 初始化来源候选 |
| Go 要求 | go.mod: Go 1.27.1 | go.mod: Go 1.27.1 |

所有检查都是源代码与 Git 对象检查，没有以 SQLite 模拟执行替代真实程序。`source-object-inventory.json` 每个源对象保留 Git blob、SHA-256、字节数及原路径，`git-io` 保留真实 `git ls-tree` 和 `git cat-file --batch` 输出；selected excerpts 是原 blob 字节副本。没有读原业务数据库、凭据、owner 输出或恢复私钥。

`f6e4a0e…` 的24份 runtime 输入（21 SQL、旧 session addon、两个 spec contracts）与现存已资格 old22 SourceRoot 中相应文件逐字节相等。它自身历史 tree 没有 SQL22。这个比较支持重用已核实的资源边界；真实 bootstrap 的最终数据库 schema、schema hash 及21→22迁移兼容性仍须后续实际验证。

## 原始公开入口

历史 `apps/control/main.go:42–122` 的 `--bootstrap-owner` 分支依次获取新 data-root lease、打开 SQLite、运行 `store.Bootstrap`、`domain.New`，随后生成新的本地 Owner 并返回。`internal/domain/store.go:39–104` 决定原始编号 SQL 与 session addon/fence 的安装；两个提交在这一点有实质区别。

未来 Root 的独立 Native scope 可以把工作目录设为完全来自 `f6e4a0e…` 的新 SourceRoot，再设置 `RESEARCHOS_DATA_DIR=<全新隔离目录>`，调用：

```text
<old21-control.exe> --bootstrap-owner --credential-file <新scope私有输出目录>/owner.json
```

该 admin 分支不要求 web/dist，也在启动 HTTP listener / runtime coordinator 前返回。它生成的是新的 synthetic Owner；本次没有执行这条命令，也没有读取任何现存 Owner。凭据路径只作为将来的受控程序输出，不应被当前 discovery 读取或收入公开 Source manifest。普通 `apps/cli init` 需要已启动 host，不是上述独立 bootstrap 的替代入口。

历史 `ops/backup/main.go` 公开暴露以下精确命令形态，均须后续独立 Native scope：

```text
<old21-backup.exe> keygen --key-file <新scope私有目录>/recovery.key
<old21-backup.exe> create --db <新data-root>/researchos.sqlite --root <精确old21-SourceRoot> --key-file <新scope私有目录>/recovery.key --out <不存在的backup目录>
<old21-backup.exe> restore --backup <上述backup目录> --root <同一精确old21-SourceRoot> --key-file <新scope私有目录>/recovery.key --out <不存在的restore目录>
```

key 必须在 backup/restore 目录之外。历史 restore 使用 SourceRoot 的编号 migration 列表，不注入手写迁移。这里列出原始命令接口，不授予执行权限；实际备份、恢复、进程 PID/创建时间/IO/退出与 SourceGuard 闭合须由 Root 后续 scope 记录。`--fixture-control-replay` 是单独受限制的 fixture replay 协议，不能当作通用无凭据 bootstrap。发现任务不要求启用它。

## 后续独立构建的范围

`root-build-input-scope.json` 给出每个入口的静态传递 import 集合及完整源对象清单。它保留相关包的全部非测试 OS/tag 变体，并包含所有四处 embed 的原始 JSON，不能冒称已经经过真实 Go 编译器依赖枚举。

| 用途 | 静态输入文件 | 原始字节 |
|---|---:|---:|
| `./apps/control` | 247 | 2,474,761 |
| `./ops/backup` | 197 | 1,868,127 |
| 可选 `./apps/cli` | 243 | 2,134,134 |
| control + backup + runtime 去重 | 272 | 3,105,007 |

Root 可以按清单从本仓库 Git object database 逐 blob 提取到新的单一构建 SourceRoot，逐项检查 Git blob ID、SHA-256、字节数。无需 clone 仓库、复制 receipt 历史、Go toolchain 或 module cache。若需要编译 CLI，再合入其清单。不要裁掉 Main/old22 的 migrations 来伪造 old21 根，也不要编辑现存缓存工作树。当前注册 Git worktree 没有精确停在这两个候选提交；这是一项有限枚举结果，不宣称磁盘上不存在其他 Source 副本。

先在 Root 的独立构建 scope 对上述实际提取 Source 运行真实 `go list -deps -json`，封存 compiler/tag/embed/runtime 闭合，再使用锁定工具运行如下构建形态：

```text
<locked-go.exe> build -mod=readonly -trimpath -o <新scope>/old21-control.exe ./apps/control
<locked-go.exe> build -mod=readonly -trimpath -o <新scope>/old21-backup.exe ./ops/backup
```

若只是无 .git 的精确 blob 提取目录，应明确记录 `-buildvcs=false`，由 Source manifest 绑定 commit/tree，不把缺失的 embedded VCS revision 假报为存在。若采用 detached checkout 则按该 checkout 的真实 buildinfo 记录；不要靠设置假的 revision 掩盖来源。构建必须保存真实调用/原始 stdout/stderr/退出、构建输入前后 pins、程序完整 ref 与可审查的 buildinfo，并交非作者独立验证。编译成功也不自动证明历史正式发布资格或 old21 Case 成功。

## 已存在工具和模块

已实际读取 `execution/toolchains/locked.json`，重新哈希 Go / Git / Python 可执行文件，与 lock 一致。Go 是 `.local/tools/go1.27.1/go/bin/go.exe`，SHA-256 `d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490`，17,508,352 bytes。本轮没有运行 Go，包括 version、list、build、test。

19 个 go.mod 直接/间接模块的 expanded 目录均在 `.local/gopath/pkg/mod`。`tool-module-resources.json` 列出每个版本、go.sum 对应行、expanded go.mod ref、缓存 .mod/.info/.ziphash 的实测 refs，以及 zip 是否存在。目录与 hash 文本存在不等于内容完整性或真实编译闭合；Root 后续需在同一模块缓存上验证实际需求。保留现存 cache，独立指定新的 GOCACHE，避免在 D 盘额外复制数 GB。

建议后续构建环境精确限定 `GOTOOLCHAIN=local`、`GOPROXY=off`、`GOSUMDB=off`、`GOWORK=off`、`GOOS=windows`、`GOARCH=amd64`、`CGO_ENABLED=0`、`GOFLAGS=-mod=readonly`，GOPATH/GOMODCACHE 采用清单里的绝对路径。关闭联网不能替代模块完整性验证；如真实构建发现缓存缺项，只记录 old21 分支的具体 OPEN 输入，不修改锁文件、切换版本或重跑其他已成功 Development 任务。

## 原资格记录与本分支 OPEN

`existing-qualification-refs.json` 精确引用既有 release-resource 发现记录、已资格 old22 的独立 decision/HDF/MF、历史资源调查和 backup resource report。`selected-prior-metadata-checks.json` 只复核直接引用元数据的当前 pins 和对应 MF 成员；没有递归遍历旧 business JSON 依赖，也没有重跑 old22 或 Development13。

本分支尚未完成：真实 Go 依赖枚举/模块内容闭合、old21 两个新二进制构建与非作者程序资格、公开 bootstrap/backup/restore 实际运行、目标 schema 与21→22对接实证、正式历史 release/old21 Case。它们均只标 old21 分支 OPEN，不扩散到其他工作。

本轮输出仅在本包目录内。Main/Canon/现存缓存 Source 未修改；无 active TP、Runtime grant、SQL query、产品 Native 子进程、模型请求、dispatcher 或正式 Case 增量。只读 Git/Python 收集有真实日志回执，原始 console 截断如实保留；已封存完整 Git 原始输出，不把截断 console 冒称为完整日志。
