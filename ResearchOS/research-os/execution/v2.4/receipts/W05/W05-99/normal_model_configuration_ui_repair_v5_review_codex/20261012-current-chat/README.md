# W05 UI repair-v5 独立审查

结论：**ACCEPT — SOURCE + FIXTURE ONLY**。冻结候选 `1c761174cabdd5be6fc95218eeaa502cd8c6c3f1` 修复 `W05-UI-V4-001`，本轮未发现新增阻断项。

原 v4 三条触发时序已独立复跑：状态 HTTP 在途切换、状态凭据获取期间切换、最终编译 UI 的状态在途切换。三者均保持原配置意图和锁定输入；在 B 再核对仍不解锁，回到 A 并更换 PID 后才确认保存。每个完整场景仅发出一次 `host.configure`。原样最终编译 UI 的前后 DOM、截图、HTTP/validator 原始字节见 `status-race-results.json`、`status-race-http/` 及 `compiled-ui-status-response-switch*.png`。

绑定核对 7439/7439，通过项包含作者959成员、完整构建6424输入、累计7个源码 Git 对象、最终 IPC/validator/编译 UI 资源。构建输入摘要 `055b84beaf269fcc8b9a4e055e93196e9ff62f8b44203a9922d146554533dfae`，validator SHA256 `ba25b1dc569e6d3be910eeab1d4beaebd55db6c8b5e2dbce4b172e927338999a`。这是独立核对作者构建，没有声称重新编译。

必要回归：边界23/23、独立 ACK 屏障保留2/2、原 v4 反例3/3、组件生命周期5/5、v3 跨 Host 变体6/6。状态读取失败不会清除其他已 ACK 的配置命令，不降低 `possiblySent`，回原主机使用原 command ID 与 envelope；同逻辑主机变更端口/PID 仍允许核对。测试命令、环境、时间、exit、stdout/stderr 及 raw evidence 均在本目录。

既有 whole continuity parity 的66/69、三条 goal.start/project.bootstrap 不一致保留为遗留边界；本轮未重复执行，也没有改写为整体通过。此次接受不等于与 Main 新 Core 集成后的验证，不是 Electron/native/Core 真实用户流、模型运行时资格、W05 父任务或正式用例接受。0 actual model / external / tunnel，formal 与 parent acceptance 均 +0。

Main 核对基线 `dfefe326dd7f4ae528caaf311ae388f40b8f0841`，CP413 / OW202 / CM40。只写本独审目录，未修改候选、Main、Canon、合同、冻结作者收据或旧独审记录。作者旧失败保留。两处新独审缓存定向删除被自动审批审查以 `blocked by policy` 拒绝，保留但排除于证据清单，未换工具绕过。
