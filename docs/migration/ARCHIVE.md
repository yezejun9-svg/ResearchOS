# 开发目录与历史归档

开发目录从原主工作区 `research-os` 的当前文件建立。代码保持原文件内容；新增开发脚本和说明文档另行登记。固定的 v2.4 规格从 `v24-continuation` 工作树完整复制到 `spec/v2.4/`，无需复制原工作树才能阅读。

源码清单记录在 `source-manifest.json`，包含相对路径、长度与 SHA-256。它记录迁移时的原文件，不用于阻止后续正常开发修改。

历史备份固定版本是 [55931878579daebe47af21fbc2c18a31b9f6a032](https://github.com/yezejun9-svg/ResearchOS/tree/55931878579daebe47af21fbc2c18a31b9f6a032)。

| 资料 | 归档位置 |
| --- | --- |
| 主工作区的历史资料 | [ResearchOS/research-os](https://github.com/yezejun9-svg/ResearchOS/tree/55931878579daebe47af21fbc2c18a31b9f6a032/ResearchOS/research-os) |
| v2.4 详细施工证据 | [execution/v2.4](https://github.com/yezejun9-svg/ResearchOS/tree/55931878579daebe47af21fbc2c18a31b9f6a032/ResearchOS/research-os/execution/v2.4) |
| product-v1 详细证据 | [execution/product-v1](https://github.com/yezejun9-svg/ResearchOS/tree/55931878579daebe47af21fbc2c18a31b9f6a032/ResearchOS/research-os/execution/product-v1) |
| 独立 task 工作资料 | 备份版本的 `Codex-task/` 目录，按原相对路径查找 |
| 历史提交映射、工作树状态和迁移排除记录 | 备份版本的 `_backup/` 目录 |

旧工作树是不同时间或任务的分支，不能将同名文件互相覆盖后称为整合。本次开发目录使用主工作区的已整合源码；未整合分支和审查中间稿留在历史归档。原机器中尚未公开备份的文件继续保留在原位置及本地迁移清单中。

未进入日常 checkout 的内容包括旧源码副本、完整历史 receipts/verifier/invocation 目录、构建产物、安装包和运行缓存。公开备份本来就排除了秘密、私人数据库、部分大型或未能确认安全的文件，因此归档链接不代表这些排除项已经上传。查证旧资料时以备份中的具体文件和原迁移排除记录为准。

开发构建可重新获取 Go/npm 依赖。旧机器上的凭据、业务数据库、受保护留出材料和原始大型安装包不可从代码仓库恢复；需要相关运行环境时单独配置。
