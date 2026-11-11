# ResearchOS

ResearchOS 的开发仓库。产品源码、规格、测试、依赖锁文件和当前工作交接资料直接放在仓库中，可在 GitHub 阅读编辑，也可克隆后继续开发。

## 开始开发

原生开发目标为 Windows x64。安装 Git、Node.js 24 或更新版本，以及 `go.mod` 指定的 Go 1.27.1。使用下面的命令只下载开发分支，避免同时下载历史备份分支。

```powershell
git clone -c core.longpaths=true --depth 1 --single-branch --branch codex/development-20261111 https://github.com/yezejun9-svg/ResearchOS.git ResearchOS
cd ResearchOS
node scripts/dev.mjs doctor
node scripts/dev.mjs setup
node scripts/dev.mjs build
```

`setup` 根据仓库中的锁文件安装开发依赖；首次执行需要网络。无需从旧电脑复制工作树、数据库或缓存。`build` 生成前端静态资源和 Go 开发二进制，输出在被 Git 忽略的目录中。

克隆命令已为这个仓库开启 Windows 长路径支持，保留的历史审查文件名无需手动整理。

Go 不在 PATH 时，可先设置 `$env:GO_BINARY = 'C:\your-tools\go\bin\go.exe'`。编译器只需安装一次，路径由你自己的电脑决定。

```powershell
node scripts/dev.mjs check
node scripts/dev.mjs web
```

`check` 检查 Go 编译和桌面边界代码。`web` 提供前端开发服务器；需要真实后端的功能仍须连接已配置的 ResearchOS 主机。完整桌面安装包、真实模型资源和正式验收有额外前提，详见 [开发交接](docs/DEVELOPMENT_HANDOFF.md)。开发构建不更改旧验收结果。

## 目录

| 路径 | 内容 |
| --- | --- |
| `apps/web/` | React 前端 |
| `apps/desktop/` | Electron 桌面应用 |
| `apps/control/`、`apps/cli/` | Go 控制服务和 CLI |
| `internal/`、`adapters/`、`ops/` | 业务实现、适配器和运行组件 |
| `migrations/`、`contracts/` | 数据结构和接口合同 |
| `spec/v2.0/`、`spec/v2.4/` | 完整冻结规格 |
| `tests/`、`evaluation/` | 测试与评估代码 |
| `third_party/` | 固定版本的 Mu 源码及许可证 |
| `execution/product-v1/`、`execution/v2.4/` | 当前施工状态和精选续跑依据 |
| `scripts/dev.mjs` | 不绑定旧电脑路径的开发命令 |

## 当前进度与历史资料

迁移基于当前主工作区实际文件，包含尚未提交的源码修改。续跑入口为 product-v1 revision 92 与 v2.4 checkpoint 694；具体状态见 [开发交接](docs/DEVELOPMENT_HANDOFF.md)。

历史 Git 提交、旧工作树增量、详细日志和验收快照继续保留在 [固定备份版本](https://github.com/yezejun9-svg/ResearchOS/tree/55931878579daebe47af21fbc2c18a31b9f6a032)。开发分支不继承该大型备份的提交链。选择 GitHub 的 Download ZIP 同样只下载当前分支文件。

本仓库不包含用户凭据、`.env`、私人数据库、`node_modules`、Go 缓存或旧工作树的数百份副本。需要查找历史审查资料时，参阅 [归档说明](docs/migration/ARCHIVE.md)。

上游两个可选 Google OAuth 登录入口已改为本机环境变量配置，参见 [公开版本的依赖补丁](docs/migration/VENDOR_OAUTH_PATCH.md)。
