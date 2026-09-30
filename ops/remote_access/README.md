# W17 远程监督：开发实现与待验证入口

本目录提供可审查的本地 gateway，尚未启用公网入口。电脑控制面仍只监听 `127.0.0.1`。本轮只读取已安装 `cloudflared 2026.8.3` 的版本/help；未读取其他项目配置、未创建账户、未使用 VPS。

## 已实现范围

- 正式 migration `0014_remote_access.sql` 和原合同六个设备 API。256 bit 一次性令牌、30–300 秒期限、默认 READER、非空明确项目列表。设备管理仅发起配对的本地 OWNER 可用。
- 访问令牌 10 分钟；刷新凭据 24 小时且一次轮换，旧 access 在轮换时失效。每次认证读取设备/Owner 当前撤销状态，设备项目权限与发起者当前项目权限求交；paired OWNER 仍无全局管理、再配对、创建项目和 VERIFIER_ONLY 权限。
- 凭据、refresh 和 challenge 仅保存 SHA-256 验证材料。秘密响应在 handler 内 AES-GCM 加密缓存至多 5 分钟；重启或过期后拒绝重发。DB 保留不可逆消费/重放指纹；普通授权/撤销响应可幂等重放 7 天。审计仅含主体/操作/对象标识，不记录输入正文、令牌、cookie、标签或 reason。
- 当前手机会话只存在页面内存，支持页面存活期间离线恢复/自动续期；刷新或关闭页面需重新配对。没有 cookie 鉴权或 localStorage/sessionStorage 凭据。
- 本机 SSE 每 250 ms 重新认证，撤销测试实测约 250 ms 断开。Quick Tunnel 不支持 SSE，因此 gateway 声明 `events=poll`，手机按既有 listEvents/snapshot 进行两秒增量轮询；写入不会因重连自动重发。官方限制：[Quick Tunnels](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/)。这只是临时跨网试用路径，不作为持久远程部署。

## 信任边界

`手机 HTTPS → Cloudflare edge / 加密 tunnel → cloudflared → 127.0.0.1:8790 gateway → 127.0.0.1:8787 control`。

gateway 仅接受 loopback 来客、精确配置的公开 Host 和单一 `X-Forwarded-Proto: https`，写入要求精确 Origin 与 JSON；拒绝 cross-site、表单、混合 forwarded scheme。只转发已构建 UI、设备 redeem/refresh、项目 API；不暴露 device administration、全局 policy、health、SSE、数据库或工作目录。它清除 cookie 和所有客户端 forwarded/Cloudflare headers，注入只允许设备身份的标记；即使用户在远程页面粘贴本地 Owner token，API 也拒绝。

边缘到 gateway 的 HTTPS 标记依赖 **已核验 cloudflared 实际覆写行为**；单元测试只能证明 gateway 的拒绝规则。实际开放前必须验证 HTTP 明文请求、伪造 `X-Forwarded-Proto`、伪造 Host/Origin 不能到达控制面。此项、证书验证及真实跨网手机目前均 `NOT_RUN`。本机同 OS 身份不作为安全隔离边界。

## 复现开发验证

在仓库根目录使用锁定工具链：

```powershell
$env:RESEARCHOS_GO = (Get-Content execution/toolchains/locked.json -Raw | ConvertFrom-Json).tools.go.path
& $env:RESEARCHOS_GO test ./internal/domain ./ops/remote_access/gateway -run 'TestW17|TestGateway' -count=1 -v
$env:PYTHONUTF8 = '1'
python tests/security/remote_browser.py
```

浏览器 runner 使用新建临时 SQLite、真实 control.exe 与两个 Chromium context。只注入 polling 元信息，不 mock 业务 API。临时实例、credentials 和进程在收尾删除，回执保留脱敏 HTTP 状态、截图、构建/service 日志和源哈希。浏览器夹具不代表实体手机、独立验收或 C22 主机边界通过。

## 待主 Agent 审查并获授权后的启动命令

以下是准备好的命令，**本轮未执行**。先构建 gateway。tunnel 初次运行时 gateway 端口保持关闭；获取动态 HTTPS 域名并将精确 origin 交 gateway 后才开始转发。不要直接 tunnel 到控制服务端口。

```powershell
& $env:RESEARCHOS_GO build -o .local/remote-gateway.exe ./ops/remote_access/gateway
& 'C:\Program Files (x86)\cloudflared\cloudflared.exe' tunnel --config ops/remote_access/quick-tunnel.yml --no-autoupdate --metrics 127.0.0.1:0 --url http://127.0.0.1:8790
# 使用这一次实际输出且审核过的 URL；不得使用通配 Host。
$remoteOrigin = 'https://REPLACE-WITH-ACTUAL.trycloudflare.com'
& .local/remote-gateway.exe -listen 127.0.0.1:8790 -upstream http://127.0.0.1:8787 -public-origin $remoteOrigin
```

若由自动化后台启动，使用 `Start-Process -WindowStyle Hidden` 并捕获本任务 PID；仅停止本次创建的进程。配置明确指定本项目空 YAML，禁止借用其他项目 Cloudflare 登录/配置。实际版本是否接受该空配置及 Quick Tunnel 必须在授权后的首次运行核验；失败不改用户原配置，也不创建账户/域名。CLI 参数已用已安装二进制 `tunnel --help` 核对。上游快速隧道路由逻辑参考：[cloudflared source](https://github.com/cloudflare/cloudflared/blob/master/cmd/cloudflared/tunnel/cmd.go)。

入口可达后先完成无认证 API 拒绝、Host/Origin/HTTP 负例和证书检查，再由本机设置页填写精确 HTTPS origin、生成一次性链接，在手机浏览器打开。令牌仅在 URL fragment 中传递，页面立即清除 fragment，HTTP 请求和 Referer 不含它。不要把包含 fragment 的完整配对链接写入日志、回执、截图或聊天。

## 验收状态

W17 开发施工可复验；A10/A11 正式 LIVE_WINDOWS、C02 完整跨项目检索/共享资料矩阵、C22 独立主机文件/缓存/备份/进程隔离仍待独立验证。当前 C22 测试只使用公开假 canary 的受限元数据，覆盖 paired OWNER 的列表/已知 ID/正文/事件拒绝；没有读取正式 holdout，也没有放宽 W11 资格或 frozen service。
