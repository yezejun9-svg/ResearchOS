# W01 CORE-01 资格证据

唯一决定为 THIN_CORE。完整 Paperclip 门：16 BLOCKED；直接调用上游策略函数的两个有限观察：普通完成进入 review PASS、清策略保持必需 reviewer FAIL。这些不是产品测试或 HTTP 漏洞完整证明。

- `source.json`、`source-excerpts.json`：固定版本与实际读取源码的 hash/定位/节选。
- `evidence/*/command.json`：真实 argv、cwd、UTC 时间、退出码及 stdout/stderr SHA256；同目录保存未经改写的原始输出。
- `attempts.json`：A1 1 轮实际环境修复；准备阶段错误命令也保留。A2 未开始，未打核心补丁。
- `cases.json`、`results.json`：逐个门、输入场景、前置条件、结果和原始阻塞依据。
- `probe-policy.ts`：导入固定上游真实函数，无重写实现、无 DB/HTTP 模拟器。
- `verify_evidence.py`：检查输出 hash、source/tag、源码节选、全部门清单、尝试界限和唯一路线。

在本 worktree 根目录复核（不安装、不启动、不改证据）：

```powershell
python -X utf8 qualification/core/verify_evidence.py
```

保留的局部依赖还在时，可在独立证据目录复跑函数探针：

```powershell
python -X utf8 qualification/core/qualify.py policy --evidence-dir .local/verification-policy
```

复跑完整环境必须在新资格 worktree 内、经重新开立资格授权；本轮已停止，不自动清零计数。按需依次运行 `qualify.py fetch`、`install`、`start`、`probe`、`repair`（仅准备固定 Node）、`repair-execute`（同一轮短路径/固定工具安装修复）、`policy`、`documented-start`、`final-state`，每次用独立 `--evidence-dir`。source 已存在时 fetch 拒绝覆盖。依赖均从固定 tag 的 pnpm-lock.yaml 安装；pnpm 9.15.4 由上游 packageManager 固定，局部 Node archive 的官方 SHA256 在下载日志。初始公共 pnpm/Corepack 缓存副作用已在 ADR 披露；有效修复的 store 位于 .local/store。

脚本退出 0 表示命令捕获完成，具体子命令退出码和语义结果以记录为准。初始脚本准备参数错误保留在 repair-install/repair-start；最终脚本已修正，不伪装这些历史失败为成功。健康探针只访问专用 13179 端口，上游进程未成功监听。没有创建第二套调度器、部署 verifier 或运行故障注入；无法执行的业务反例明确 BLOCKED。

`.local/paperclip`、`.local/v`、`.local/store`、`.local/tools` 暂留供独立 Verifier；审查后可清理，它们不是正式唯一证据。上游节选属于 MIT 许可，LICENSE 节选和完整源文件 hash 收录在 source-excerpts.json。
