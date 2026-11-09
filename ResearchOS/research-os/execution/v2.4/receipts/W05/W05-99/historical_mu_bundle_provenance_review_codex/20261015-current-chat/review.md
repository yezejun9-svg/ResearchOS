# Historical Mu bundle 来源独立复核

已找到并验证具体 ResearchOS wrapper 来源：`292ad860f9e76cf2795d5a3010da1d114d01ff56:adapters/runtime/mu/worker.mjs`。Git 原始对象为 48,557 字节，SHA256 `0d50cea351f325f28ca5ee377eac36833768a28be42cf48ec0e50834c0ff6517`，与原构建回执、build metadata 完全一致，无换行转换。同一 ResearchOS commit 的 `build.mjs` 为 4,286 字节，SHA256 `9411e13e59a227abf0a4c497253ccf006c4d5962a5374c1f254c05d18cd0f575`，也精确匹配。

原始回执位于 `runtime_assets_resource_codex/20261012-current-chat`，由 CP408 的 SHA 固定引用。历史命令使用 `C:/nvm4w/nodejs/node.exe`，从 ResearchOS 根运行 `adapters/runtime/mu/build.mjs`，在 2026-10-12 07:34:38–07:34:54 UTC 完成，native exit0。stdout、原始 build metadata、原资产文件以及七个后续包中的 bundle/metadata 均一致：bundle SHA256 `2a8e70132a914affc6122c1f1db29cfa315b655c93d4200145852ebbc853d441`；metadata SHA256 `ce85112575850403492a0d00a26100ff678d64f21e852af2f7530bb7a6b7613a`。

`8dfebe36508ac0c2508735bb866756dab9283e74` 是 `third_party/mu` 的上游 SDK commit，不是 ResearchOS wrapper 的 commit。`build.mjs` 明确从本仓库 `worker.mjs` 取得 entryPoint/source_sha256，另从常量和 component lock 取得 mu_commit。Root 在 ResearchOS 仓库查询该 SDK commit 的 native128 失败保留，但不再作为 wrapper 来源缺失的依据。

已逐项重新核对历史 Git 中的 vendor manifest 与当前清单字节一致，5083 个文件大小/hash 全部匹配。历史 builder 在打包前检查这些文件、SDK/AI `0.87.1` 和 esbuild `0.28.2`。两个链内的后续构建 worktree 也保留了相同 wrapper 字节。包复制链中 attach composition 缺少 `old_composition` 字段，但 `assemble-attach.py` 的 `OLD_COMP` 明确指向 readlane；readlane 的 `OLD_HERE` 明确指向 combined；combined 从原 runtime-assets 目录复制固定三文件。七个现存包中包括当前 installed `normal-verifier-replacement-4f4023-20261015`。

仍为 **NOT_PROVABLE_FROM_REVIEWED_RECEIPTS** 的部分：原 runtime asset receipt 未记录完整 node_modules、esbuild 二进制及生成 dist 的历史输入闭包，也未保存 esbuild metafile。5083 清单只包含三个上游跟踪的 dist 文件，包含零个 node_modules 文件。当前版本与 vendor 文件匹配不能倒推出这些未记录依赖在历史构建时的全部字节，故不能宣称整个 bundle 已获可逐字节重建证明。本次没有重新构建 bundle。

历史构建 stderr 的 ignored-bare-import 警告保留；本审查一次 `git log` 遍历因缺失旧 tree 失败也保留。已知292ad的五个精确 Git blob读取均成功，没有恢复 Git 对象。没有修改源码、共享续跑文件、实际 DB，没有运行 Core/model、网络请求或读取私密配置。

本结论仅验证历史 wrapper/构建/资产复制链并声明输入闭包限制。F01 整体由 Root 合并 Core、staged binding 与本证据后判断；不构成 C/actual、STOP、模型资格、Main/package 或正式接受，formal increment0。
