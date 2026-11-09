# W05 Desktop 模型配置 UI 候选

候选源码位于独立 worktree `D:\作品集\ResearchOS\research-os\.local\worktrees\w05-normal-model-ui-20261012`，基线 `292ad860f9e76cf2795d5a3010da1d114d01ff56`，候选提交 `c12847d7ee7b37a15d875929738fe84fd7ba6964`。此收据是候选验证，不是 Main 合并、真实 Desktop 用户流或 W05 正式接受。

Desktop 首次进入项目工作台且主机无模型配置时显示表单；设置页一直提供同一入口。表单先调用 `desktop.selectProject` 和 `host.status`，再以状态修订加一提交且仅提交 `config_revision`、`provider_id`、`base_url`、`model_id`、`credential_ref`。空凭据引用发送 `null`。对于已接收但未完成的命令，输入锁定且用相同 payload 显式重试。成功后刷新 `host.status` 并核对模型引用；后端拒绝时显示错误且保留输入。页面说明配置记录不等于运行时资格。

IPC 修正了“已选项目、尚无会话”的 `host.configure`：发往主机的四个作用域字段全部为 `null`。已有会话仍使用项目、会话、修订和写入者 epoch 的完整作用域，不绕过写入权限。对应 `v2client.js` 的本地约束与 shell 一致。

验证结果：锁定 Node `C:\nvm4w\nodejs\node.exe`、现行 SHA256 `5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6` 下，`vite-build-final.log` 构建成功；source-bound validator 生成成功，`validator-result.json` 的 drift 为 0，input digest 为 `e15bfac51bd84f2de8b1a505eefef4039e8d5acd8408d9a6b62800dfff0a4664`。`desktop-model-boundary-final.log` 是 source-bound HTTP/validator 用例 3/3；`w13-react-test.log` 是既有用例 5/5。`browser-config-test.json` 是 Playwright Chromium 加合成 preload bridge 的实际 DOM 操作 4/4，外部调用与模型调用均为 0；截图和可复现脚本在本目录。浏览器 fixture 不证明真实 Core、凭据服务或 Electron 启动成功。

`renderer-shell-parity.json` 的运行自身 errors 为 0，但 legal envelopes 只一致 66/69；三行分歧均为未改动的 `goal.start` 与 `project.bootstrap`。因此不将这份全量脚本称为通过。首次构建误用 `C:\Program Files\nodejs\node.exe`，被工具锁拒绝；原始工具清单保留在 `validator-first-attempt-tools.json`。没有改锁或重置失败记录。

用于后续真实 Electron 试验的 source-bound 树位于此 worktree 的 `.local\w05-validator-final`。它含 `apps/desktop/resources/client-wire`、桌面源码和 web dist；启动仍需按原始哈希提供 `spec/v2.0/contracts/openapi.json`，因为 `build-validator.py` 当前只复制 `spec/v2.0/ui`。不能用原始源码树直接当有 validator 的启动树，也不能用浏览器合成 bridge 代替 native/Core 资格。候选未调用模型，未改默认模型、Canon、CLI 或产品 Core。

本目录关键校验：`browser-config-test.json` SHA256 `43ed80957daad3e71783cb9c1284c3c2b419ec2ed3a528115ec1eed37957cc4d`；`vite-build-final.log` SHA256 `ae8a6c34e3bbe42de84d00280d13efea53122b943002f3d87fd51dcc1e5b98d1`；`desktop-model-boundary-final.log` SHA256 `c5384c939901c45ad184cd4d433fe7ba09e7187aa3e4e0b0943b041c1fa43a20`；`validator-result.json` SHA256 `3466ff22f64c03c3299911ca5a2308f4b2965c222ebafb0fb4e2f304c2dd745a`；`validator-descriptor.json` SHA256 `1164e5702087a8a0003aa10d61853bae6de7f1b4ee398b54bf25356f2c0fb729`。

工作树的 `apps/web/.local` 为本次 Vite 临时构建与浏览器 harness；其等价 harness 源码已复制进本目录。该临时目录的递归清理被自动命令审查拒绝，未纳入提交，需在允许的清理环境删除。
