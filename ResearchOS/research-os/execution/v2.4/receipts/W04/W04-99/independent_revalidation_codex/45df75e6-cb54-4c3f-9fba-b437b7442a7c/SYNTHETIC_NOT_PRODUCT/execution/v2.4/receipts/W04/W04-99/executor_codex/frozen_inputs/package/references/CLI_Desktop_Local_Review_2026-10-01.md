# CLI/Desktop本地源码复核与本次范围调整

日期：2026-10-01（Asia/Shanghai）。先检查了本会话工作目录中已经存在的Mu、QM、last30days克隆及已有实施包和调研，再复用了当天有固定来源的研究结果。本次没有扫描用户Windows整机，没有安装/启动CLI或Desktop，没有调用真实模型。资产路径与实际Git HEAD见CLI_Desktop_Local_Inventory.json。

用户本次确认：产品是像Pi/Claude一样的自己的CLI Agent，同时有自己的Desktop；每个新项目先找本地、再调研现成、最后才自研。此确认使v2.1的QM平台优先路线需要调整。

## 已复核的源码事实

| 来源与固定commit | 实际阅读位置 | 观察及影响 |
|---|---|---|
| Mu `8dfebe36508ac0c2508735bb866756dab9283e74` | `kyrn/bin/mu.mjs`、`packages/coding-agent/`、`packages/kyrn-judge/` | 有CLI、Agent和判断能力；优先检查完整组合能否满足本产品 |
| 同上 | `desktop/docs/native-host.md`、`desktop/packages/desktop/src/process/services/nativeHost/` | 有本地Electron main→每session utility process宿主；旧bundle可能回退旧路径，不能只看main源码推断已发布安装包 |
| 同上 | `nativeBridge.ts`、`common/utils/nativeHost/`及已有集成/e2e测试 | 可复用桥、事件归约、会话和UI；CLI/Desktop活会话协调仍须本项目验证 |
| 同上 | 根`LICENSE`及`desktop/LICENSE` | 根MIT、桌面Apache-2.0，分别保留许可和第三方来源 |
| QM `6a01d56c8145b125301596506b7b007b9890bcf2` | `cli/README.md` | CLI主要负责部署长驻QM服务，并非用户要的本地交互Agent运行时 |
| 同上 | `desktop/README.md` | Electron客户端连接已有QM Web服务，不内置后端或离线Agent执行，因此不作为本产品本地启动前置 |

本次源码Mu的CLI npm模板为0.1.7、Desktop package为0.1.6、内嵌Pi为0.87.1；它们是仓库不同组件版本，不意味着已公开发布。独立Pi0.99.2仍是另一条兼容边界。具体选型必须固定整体源码/锁文件并实跑。

## 采用建议及其证据级别

优先有界验证Mu完整CLI/Desktop组合；备选Pi SDK/CLI和现成桌面壳/组件；QM保留为远程适配或可靠性参考。该建议来自与本次明确需求的匹配度，不是性能或稳定性实测排名。

以同会话双端交接、并发写入控制、取消/重连、真实文件操作和Windows安装为必要门。Mu共用配置/会话文件不自动等于可以同时控制一个运行会话；闭环中应同时观察客户端、核心/worker、事件和产物。源码中的测试只能作为可复用入口，不能记为本产品PASS。

原有Harness_Research与Mu_Source_Review保留当天来源与访问限制；本次不为格式重复搜索同一材料。未来实施者须先检查自己的实际本地目录，遇到新版本、平台差异、信息缺口时再定向查源。正式要求以00–15和contracts为准。

一手复核链接：

- https://github.com/qybaihe/mu/blob/8dfebe36508ac0c2508735bb866756dab9283e74/desktop/docs/native-host.md
- https://github.com/qybaihe/mu/blob/8dfebe36508ac0c2508735bb866756dab9283e74/kyrn/bin/mu.mjs
- https://github.com/yc-software/qm/blob/6a01d56c8145b125301596506b7b007b9890bcf2/cli/README.md
- https://github.com/yc-software/qm/blob/6a01d56c8145b125301596506b7b007b9890bcf2/desktop/README.md
