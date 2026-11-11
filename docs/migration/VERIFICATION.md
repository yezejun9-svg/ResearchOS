# 开发迁移验证

2026-11-11，在独立新目录、Windows x64、Node.js 24.9.0 和 Go 1.27.1 下完成以下检查。Go/npm 依赖由锁文件重新下载，没有复制旧工作树的依赖目录或业务数据。

| 检查 | 结果 |
| --- | --- |
| `node scripts/dev.mjs doctor` | 工具检查通过 |
| `node scripts/dev.mjs setup` | Go modules 下载、web npm ci 成功 |
| `node scripts/dev.mjs check` | 模块完整性通过；4 个 Go 入口编译通过；canonical/store 单元测试通过；43 项 Node 边界测试通过 |
| `node scripts/dev.mjs build` | Core、CLI、runtime-verifier 和 React 静态资源构建成功 |
| `python -B spec/v2.4/tools/validate_package.py` | 规格包 PASS，manifest SHA-256 与冻结包一致 |
| Mu `packages/ai/scripts/check-model-data.ts` | 公开模型目录及其哈希校验通过 |
| `node --experimental-vm-modules --test tests/development/google-oauth-config.test.mjs` | 12 项 OAuth 配置测试通过，未调用真实供应商 |

本次未执行完整 Electron 桌面装配、真实模型请求、安装器或产品正式验收。旧验收状态保留原值。`check` 中入口编译步骤使用 `-run ^$`，不代表执行了该入口的运行时测试。

首次上传被 GitHub 发现的上游编码 OAuth 配置已移除，修改和来源清单见 [VENDOR_OAUTH_PATCH.md](VENDOR_OAUTH_PATCH.md)。上游 Mu 的完整 npm 类型检查未运行，所需依赖未安装；该变更执行了上述 12 项隔离测试。Go/React 源码未因这个补丁改变。

重新编码时使用 `README.md` 中的命令。上述结果描述迁移时的源码；后续修改需要运行与改动相关的检查。
