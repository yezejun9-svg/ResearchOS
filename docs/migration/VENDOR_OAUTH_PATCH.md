# Mu Google OAuth 配置调整

迁移时发现固定 Mu 上游源码中的 `packages/kyrn-judge/src/google-login/oauth.ts` 含有以 Base64 编码的 Google OAuth client ID 与 client secret。GitHub 的推送保护阻止了第一份候选提交。该候选未创建远端分支；公开开发分支的提交历史重新从原 main 构建，不包含被拒绝的候选提交。

开发版本移除内嵌值，使用以下进程环境变量。仓库不保存其值，也不提供可用的默认值。

- `MU_GEMINI_CLI_CLIENT_ID`
- `MU_GEMINI_CLI_CLIENT_SECRET`
- `MU_ANTIGRAVITY_CLIENT_ID`
- `MU_ANTIGRAVITY_CLIENT_SECRET`

未配置时模块仍可加载；发起该 OAuth 登录或刷新时会在网络操作前给出配置错误。这只影响上游两个可选的 Google OAuth 登录路径，普通 ResearchOS 源码编辑与 Go/React 构建无需这些变量。

来源记录如下：

- `third_party/mu.UPSTREAM_MANIFEST.json` 保存原固定上游的 5083 文件哈希清单；只含哈希和长度。
- `third_party/mu.MANIFEST.json` 记录开发版本的当前文件哈希，并明确记录本补丁。
- `execution/v2.4/patch_inventory.json` 登记修改前后哈希及本说明；原补丁台账保存在 `docs/migration/original-vendor-patch-inventory.json`。

这不是对旧正式验收的重新签发。完整 Mu/Desktop 构建和正式资格验证需要核对这项来源变更，旧 PRISTINE 状态仅适用于原固定上游。产品检查点、历史失败计数和旧回执仍按原文保留。

公开前的补充审查同时检查源码中可打印的 Base64 常量及解码包装器。单纯的公共 OAuth client ID 与账户密钥、OAuth client secret 分别记录。测试夹具使用不可用的假凭据；不连接真实供应商验证任何值。
