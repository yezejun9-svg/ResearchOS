## Security Audit Report

### Summary

- Critical: 0
- High: 0
- Medium: 1
- Low: 0

### Findings

#### [MEDIUM] 公共 JSON 尚未写完就对并发读端可见

- **Location:** `root_native_migration_controller.py:97`、`:303`、`:633`、`:667`；已封存 harness 的 `nativeHarnessWait:159`。
- **Description:** `write_new` 先以 `xb` 创建最终路径，再写入、flush、fsync。读端把文件存在当作内容已完成。
- **Impact:** 正常 `poll` 请求可被 `serve` 读成空/半份 JSON，进入异常清理并取消正在保留的 Job；审批文件也可能让 Go harness 误报 `t.Fatal`。
- **Proof of concept:** 写端在 `open("xb")` 后、`write(raw)` 前被调度挂起；读端发现最终路径并解析。空或半份 JSON 解析失败，Source 已明确连接到取消路径。本次仅验证静态时序和普通 JSON 解析，未运行 controller/native。
- **Recommendation:** 在同目录唯一临时文件中完成 write/flush/fsync/close，再以 Windows 原子、目标存在即失败的方式提交；不得覆盖最终路径，只清理本次临时文件。用公开的受控延迟写入测试验证读端只见不存在或完整 JSON。

### Positive Observations

- 观察 helper 可逆向逐字恢复原实现，创建、handle allowlist、先分配 Job 后 resume 和清理主体未变。
- snapshot、具体签署批准、签署产物审查、publish、fixture 独立检查和 release 分步处理；未自动批准。
- 私密路径仅由签署 API 在运行时传入，原生 signer 输出丢弃到 NUL；未在公开回执保留私密 argv。

### Recommendations

仅接受观察 helper 的 Source 用于 Root 三项公开 dummy：normal、cancel、timeout；后两项需真实 grandchild 和 Job 实测 active count >=2。实际结果仍需独立复核，authority NONE。

controller 整体等待原子发布修订。Owner-bearing/native 九项流程、签署、原库和真实模型均未验收。Root 实际 FrozenInputs 还必须补足并核验 compiler tools、Python 源依赖及 native runtime 闭包。

